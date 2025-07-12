#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON AI Processor for Enhanced Code Editor
معالج الذكاء الاصطناعي المحسن للـ JSON
"""

import json
import logging
import os
import re
from typing import Dict, Any, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import google.generativeai as genai
from .ai_prompts import AIPrompts
from .unified_file_manager import UnifiedFileManager
logger = logging.getLogger(__name__)
class JSONAIProcessor(QObject):
    """معالج الذكاء الاصطناعي المحسن للـ JSON"""

    # الإشارات
    response_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(str)
    file_creation_requested = pyqtSignal(str, str, str)  # اسم الملف، المحتوى، النوع
    connection_status_changed = pyqtSignal(bool) # تُصدر True عند الاتصال، False عند الفشل

    def __init__(self, config, file_manager: UnifiedFileManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.file_manager = file_manager
        self.model = None
        self.chat = None
        self.is_connected = False
        self.current_worker = None
        # إضافة متغيرات لتخزين سياق الكود الحالي والمسار
        self.current_code = ""
        self.current_file_path = ""
        
        # تهيئة الاتصال
        self.initialize_connection()
    def shutdown(self):
        """إيقاف أي عامل AI نشط بشكل سلس عند إغلاق التطبيق."""
        if self.current_worker and self.current_worker.isRunning():
            logger.info("JSONAIProcessor: Shutting down active AI worker.")
            self.current_worker.cancel() # اطلب من العامل إلغاء عمله
            # *** هذا السطر هو الأهم لحل مشكلة التحذير ***
            # انتظر حتى ينهي الخيط عمله تماماً قبل أن يتم تدميره.
            # هذا يمنع رسالة "Destroyed while thread is still running"
            self.current_worker.wait()
            logger.info("JSONAIProcessor: AI worker thread has finished.")
        else:
            logger.info("JSONAIProcessor: No active AI worker to shut down.")
    
    def initialize_connection(self):
        """تهيئة الاتصال مع Gemini AI"""
        try:
            api_key = self.config.get_gemini_api_key()
            if not api_key or api_key == "your_api_key_here":
                logger.warning("Gemini API key not configured")
                self.is_connected = False
                self.connection_status_changed.emit(False) # إصدار الإشارة: فشل الاتصال
                return False
            
            genai.configure(api_key=api_key)
            
            # إعداد النموذج
            model_name = self.config.get('ai.model', 'gemini-2.0-flash')
            
            # التأكد من تحويل القيم إلى أرقام حقيقية (float/int)
            temperature = float(self.config.get('ai.temperature', 0.7))
            top_p = float(self.config.get('ai.top_p', 0.95))
            top_k = int(self.config.get('ai.top_k', 40))
            max_output_tokens = int(self.config.get('ai.max_tokens', 2048))

            generation_config = {
                'temperature': temperature,
                'top_p': top_p,
                'top_k': top_k,
                'max_output_tokens': max_output_tokens,
            }
            logger.info(f"JSONAIProcessor: Initializing Gemini model with config: {generation_config}")
            
            # الحصول على الـ system prompt
            system_prompt_text = AIPrompts.get_system_prompt()

            # تهيئة GenerativeModel مع system_instruction
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                system_instruction=system_prompt_text # تم نقل system_prompt إلى هنا
            )
            
            # بدء محادثة جديدة بدون system prompt في history
            self.chat = self.model.start_chat(history=[]) # تم إزالة system_prompt من history
            
            self.is_connected = True
            logger.info("JSON AI Processor connected successfully")
            self.connection_status_changed.emit(True) # إصدار الإشارة: تم الاتصال بنجاح
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize JSON AI Processor: {e}", exc_info=True) # Log full traceback
            self.is_connected = False
            self.connection_status_changed.emit(False) # إصدار الإشارة: فشل الاتصال
            return False
    
    def process_user_input(self, user_input: str, current_code: str = "", file_path: str = "", project_files: List[str] = None):
        """معالجة مدخلات المستخدم وإرجاع استجابة JSON"""
        logger.info(f"JSONAIProcessor: Received user input for processing. Input length: {len(user_input)}")
        if not self.is_connected:
            self.error_occurred.emit("الذكاء الاصطناعي غير متصل")
            logger.error("JSONAIProcessor: AI is not connected, cannot process input.")
            return
        
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.wait()
            logger.info("JSONAIProcessor: Cancelled previous worker.")
        
        # استخدام السياق المخزن إذا لم يتم توفيره مباشرة في الاستدعاء
        if not current_code:
            current_code = self.current_code
        if not file_path:
            file_path = self.current_file_path

        # تنسيق المدخلات
        formatted_input = AIPrompts.format_user_input(user_input, current_code, file_path)
        logger.debug(f"JSONAIProcessor: Formatted input length: {len(formatted_input)}")
        
        # إضافة سياق المشروع إذا كان متوفراً
        if project_files:
            context = AIPrompts.get_context_prompt(project_files)
            formatted_input = context + "\n" + formatted_input
            logger.debug(f"JSONAIProcessor: Added project context. New input length: {len(formatted_input)}")
        
        # بدء المعالجة في خيط منفصل
        self.current_worker = JSONAIWorker(self.chat, formatted_input, self.file_manager)
        self.current_worker.response_ready.connect(self._handle_ai_response)
        self.current_worker.error_occurred.connect(self.error_occurred.emit)
        self.current_worker.progress_updated.connect(self.progress_updated.emit)
        self.current_worker.file_creation_requested.connect(self.file_creation_requested.emit)
        self.current_worker.finished.connect(self._worker_finished)
        self.current_worker.start()
        logger.info("JSONAIProcessor: JSONAIWorker started.")
    
    def process_general_query(self, query: str):
        """
        معالجة استعلام عام من المستخدم.
        هذه الدالة تُستخدم كواجهة بسيطة للاستعلامات العامة التي لا تتطلب سياق كود محدد.
        """
        logger.info(f"JSONAIProcessor: Received general query: '{query}'")
        # استدعاء الدالة الأساسية process_user_input مع قيم افتراضية للكود والمسار
        # هنا سيتم استخدام current_code و current_file_path المخزنة إذا لم يتم تمريرها
        self.process_user_input(user_input=query)

   
    def set_context(self, current_code: str, file_path: str, project_files: Optional[List[str]] = None):
        self.current_code = current_code
        self.current_file_path = file_path
        self.project_files_context = project_files
        logger.debug(f"JSONAIProcessor: Context updated. File: {file_path}, Code length: {len(current_code)}")
        # Make absolutely sure there is NO call to self.process_user_input() or starting a worker here.
        # This method should be passive.
    def _handle_ai_response(self, response: Dict[str, Any]):
        """معالجة استجابة الذكاء الاصطناعي"""
        logger.info(f"JSONAIProcessor: Handling AI response. Action: {response.get('action')}")
        try:
            action = response.get('action', '')
            
            # معالجة الإجراءات الخاصة
            if action == 'create_file' and response.get('auto_create', False):
                file_name = response.get('file_name', 'new_file.txt')
                content = response.get('content', '')
                file_type = response.get('file_type', 'text')
                
                # إنشاء الملف تلقائياً
                success = self.file_manager.create_file_with_content(file_name, content, file_type)
                if success:
                    response['file_created'] = True
                    response['file_path'] = file_name
                    self.file_creation_requested.emit(file_name, content, file_type)
                    logger.info(f"JSONAIProcessor: Auto-created file: {file_name}")
                else:
                    response['error'] = f"فشل في إنشاء الملف: {file_name}"
                    logger.error(f"JSONAIProcessor: Failed to auto-create file: {file_name}")
            elif action in ["add_code", "replace_code", "optimize_code", "add_comment"]:
                content = response.get("content", "") # Ensure content is always defined here
                if self.current_file_path:
                    current_content = self.file_manager.open_file(self.current_file_path)
                    if current_content is not None:
                        if action == 'add_code':
                            new_content = current_content + '\n\n' + content
                        elif action == 'add_comment':
                            new_content = current_content + '\n' + content
                        else: # replace_code, optimize_code
                            new_content = content
                        
                        success = self.file_manager.save_file(self.current_file_path, new_content)
                        if success:
                            response['file_updated'] = True
                            response['file_path'] = self.current_file_path
                            logger.info(f"JSONAIProcessor: File updated in-place: {self.current_file_path}")
                        else:
                            response['error'] = f"فشل في تحديث الملف: {self.current_file_path}"
                            logger.error(f"JSONAIProcessor: Failed to update file in-place: {self.current_file_path}")
                    else:
                        response['error'] = f"فشل في قراءة الملف الحالي: {self.current_file_path}"
                        logger.error(f"JSONAIProcessor: Failed to read current file for in-place update: {self.current_file_path}")
                else:
                    response['error'] = "لا يوجد ملف حالي لتحديثه."
                    logger.error("JSONAIProcessor: No current file path for in-place update.")
            
            self.response_ready.emit(response)
            logger.info("JSONAIProcessor: Emitted response_ready signal.")
            
        except Exception as e:
            logger.error(f"JSONAIProcessor: Error handling AI response: {e}", exc_info=True)
            self.error_occurred.emit(f"خطأ في معالجة الاستجابة: {str(e)}")
    
    def _worker_finished(self):
        """التعامل مع انتهاء العامل"""
        logger.info("JSONAIProcessor: JSONAIWorker finished.")
        if self.current_worker:
            if self.current_worker.isRunning():
               logger.debug("JSONAIProcessor: Waiting for worker to finish before deleting.")
               self.current_worker.wait()
            self.current_worker.deleteLater()
            self.current_worker = None

    
    def is_busy(self):
        """فحص ما إذا كان المعالج مشغولاً"""
        return self.current_worker is not None and self.current_worker.isRunning()
    
    def cancel_current_operation(self):
        """إلغاء العملية الحالية"""
        if self.current_worker and self.current_worker.isRunning():
            logger.info("JSONAIProcessor: Cancelling current operation.")
            self.current_worker.cancel()
            self.current_worker.wait()

    def is_available(self) -> bool:
        """
        فحص ما إذا كان معالج الذكاء الاصطناعي متاحاً (متصلاً).
        هذه الدالة تُستخدم بواسطة EnhancedMainWindow للتحقق من حالة الاتصال.
        """
        return self.is_connected

class JSONAIWorker(QThread):
    """عامل معالجة الذكاء الاصطناعي في خيط منفصل"""
    
    response_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(str)
    file_creation_requested = pyqtSignal(str, str, str)
    
    def __init__(self, chat, user_input: str, file_manager: UnifiedFileManager):
        super().__init__()
        self.chat = chat
        self.user_input = user_input
        self.file_manager = file_manager
        self.is_cancelled = False
        logger.debug("JSONAIWorker: Initialized.")
    
    def run(self):
        """تشغيل المعالجة"""
        try:
            self.progress_updated.emit("جاري معالجة الطلب...")
            logger.info("JSONAIWorker: Sending message to Gemini AI.")
            
            # إرسال الطلب إلى Gemini
            response = self.chat.send_message(self.user_input)
            logger.info(f"JSONAIWorker: Received raw AI response. Text length: {len(response.text) if response.text else 0}")
            logger.debug(f"JSONAIWorker: Raw AI response text: \n{response.text}") # Log raw response for debugging
            
            if self.is_cancelled:
                logger.info("JSONAIWorker: Operation cancelled during AI response.")
                return
            
            self.progress_updated.emit("جاري تحليل الاستجابة...")
            
            # تحليل الاستجابة
            parsed_response = self._parse_ai_response(response.text)
            logger.info(f"JSONAIWorker: Parsed AI response. Action: {parsed_response.get('action')}, Content length: {len(parsed_response.get('content', ''))}")
            logger.debug(f"JSONAIWorker: Parsed AI response: {parsed_response}") # Log parsed response for debugging
            
            if not self.is_cancelled:
                self.response_ready.emit(parsed_response)
                logger.info("JSONAIWorker: Emitted response_ready from worker.")
                
        except Exception as e:
            if not self.is_cancelled:
                logger.error(f"JSONAIWorker: Error in JSON AI Worker: {e}", exc_info=True)
                self.error_occurred.emit(f"خطأ في معالجة الطلب: {str(e)}")
            else:
                logger.info("JSONAIWorker: Error occurred but operation was cancelled.")
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """تحليل استجابة الذكاء الاصطناعي وتحويلها إلى JSON"""
        logger.debug(f"JSONAIWorker: Parsing AI response text:\n{response_text}")
        try:
            # محاولة استخراج JSON من النص
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group()
                logger.debug(f"JSONAIWorker: Extracted JSON string: {json_str}")
                # تنظيف النص
                json_str = self._clean_json_string(json_str)
                logger.debug(f"JSONAIWorker: Cleaned JSON string: {json_str}")
                parsed = json.loads(json_str)
                logger.debug(f"JSONAIWorker: Successfully parsed JSON: {parsed}")
                
                # التحقق من وجود الحقول المطلوبة
                if 'action' not in parsed:
                    parsed['action'] = 'add_comment'
                    logger.warning("JSONAIWorker: 'action' key missing in parsed JSON, defaulting to 'add_comment'.")
                if 'content' not in parsed:
                    parsed['content'] = response_text
                    logger.warning("JSONAIWorker: 'content' key missing in parsed JSON, defaulting to raw response text.")
                if 'explanation' not in parsed:
                    parsed['explanation'] = 'تم معالجة الطلب'
                    logger.warning("JSONAIWorker: 'explanation' key missing in parsed JSON, defaulting to 'تم معالجة الطلب'.")
                
                return parsed
            else:
                logger.warning("JSONAIWorker: No JSON object found in AI response. Creating fallback response.")
                # إذا لم يتم العثور على JSON، إنشاء استجابة افتراضية
                return self._create_fallback_response(response_text)
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSONAIWorker: Failed to parse JSON response: {e}. Creating fallback response.", exc_info=True)
            return self._create_fallback_response(response_text)
        except Exception as e:
            logger.error(f"JSONAIWorker: Unexpected error parsing AI response: {e}. Creating error response.", exc_info=True)
            return {
                'action': 'error',
                'content': f'خطأ في تحليل الاستجابة: {str(e)}',
                'explanation': 'فشل في تحليل استجابة الذكاء الاصطناعي'
            }
    
    def _clean_json_string(self, json_str: str) -> str:
        """تنظيف نص JSON من الأخطاء الشائعة والمعقدة."""
        logger.debug(f"JSONAIWorker: Attempting to clean JSON string:\n{json_str}")
        
        # 1. إزالة أي نص قبل أول قوس مفتوح { وبعد آخر قوس مغلق }
        # هذا يزيل أي نص زائد قد يرسله AI خارج كائن JSON.
        json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            logger.debug(f"JSONAIWorker: Extracted main JSON block: {json_str[:200]}...") # Log start of block
        else:
            logger.warning("JSONAIWorker: No complete JSON object found in string during cleaning.")
            return json_str # Return as is if no JSON block is found

        # 2. إزالة التعليقات بأسلوب JavaScript (//) أو Python (#)
        # تأكد من عدم إزالة // التي قد تكون جزءًا من URL داخل قيمة نصية
        json_str = re.sub(r'(?<![:"\w])//.*', '', json_str) # يزيل // إلا إذا سبقتها : " أو حرف
        json_str = re.sub(r'(?<![:"\w])#.*', '', json_str) # يزيل # إلا إذا سبقتها : " أو حرف
        
        # 3. إزالة الأسطر الجديدة غير المهربة داخل النصوص، واستبدالها بـ \n مهربة
        # هذا يمنع الأسطر الجديدة في القيم النصية من كسر JSON
        # (؟ <!) \ "تطابق حرف السطر الجديد فقط إذا لم يسبقه خط مائل عكسي (\)
        json_str = re.sub(r'(?<!\\)\n', '\\n', json_str)
        
        # 4. إصلاح الفواصل المفقودة بين الأزواج (key-value)
        # يبحث عن علامة اقتباس متبوعة بمسافات وأسطر جديدة ثم علامة اقتباس أخرى، ويضيف فاصلة
        # قد يحتاج هذا إلى تعديل دقيق بناءً على الأخطاء الفعلية
        json_str = re.sub(r'("\s*?\n?\s*?")\s*(")', r'\1,\2', json_str)
        
        # 5. التعامل مع الفواصل الزائدة في النهاية (ليس بالضرورة هنا ولكن مفيد)
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # 6. إزالة أي أسطر فارغة إضافية قد تكون ناتجة عن التنظيف
        json_str = os.linesep.join([s for s in json_str.splitlines() if s.strip()])

        logger.debug(f"JSONAIWorker: Finished cleaning JSON string.")
        return json_str

    
    def _create_fallback_response(self, response_text: str) -> Dict[str, Any]:
        """إنشاء استجابة احتياطية إذا فشل تحليل JSON"""
        logger.info(f"JSONAIWorker: Creating fallback response for text length: {len(response_text)}")

    # 🆕 هذا الجزء سيتم إزالته أو تعديله ليتجنب التخمين التلقائي لإنشاء الملف.
    # لا تحاول تخمين "إنشاء ملف" من كلمات مفتاحية عامة.
    # إذا كنت تريد هذا السلوك، اجعله أكثر دقة أو مرتبطاً بسياق الطلب الأصلي.

    # استجابة افتراضية (افترض أن الغالبية العظمى من الاستجابات التي لا تُفهم
    # يمكن أن تُضاف كتعليقات أو استجابات عامة).
        logger.info("JSONAIWorker: Fallback: Defaulting to general_response action (or add_comment).")
        return {
        'action': 'general_response', # أو 'add_comment' حسب تفضيلك
        'content': response_text, # هنا يمكنك إرجاع النص الخام كاملاً
        'explanation': 'لم يتمكن AI من تقديم استجابة منظمة، تم إظهار النص الخام.'
    }
    
    def cancel(self):
       """إلغاء العملية"""
       logger.info("JSONAIWorker: Cancel flag set to True.")
       self.is_cancelled = True