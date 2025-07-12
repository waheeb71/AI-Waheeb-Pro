#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class UIFileOperations:
    """
    فئة مساعدة لعمليات الملفات المتعلقة بواجهة المستخدم.
    تقوم بتنسيق الإجراءات بين الواجهة (MainWindow) ومدير الملفات (UnifiedFileManager)
    وخدمة الذكاء الاصطناعي (JSONAIProcessor).
    """
    
    def __init__(self, main_window):
      
        self.main_window = main_window
       
        self.file_manager = main_window.file_manager
        self.output_panel = main_window.output_panel
        self.gemini_service = main_window.gemini_service
        
        logger.info("UIFileOperations: Initialized.")
    
    def create_file_and_write_content(self, file_name: str, content: str, file_type: str) -> bool:
      
        logger.info(f"UIFileOperations: Requesting file creation and content write for: {file_name}")
        try:
          
            success = self.file_manager.create_file_with_content(file_name, content, file_type)
            
            if success:
              
                self.main_window.open_file(file_name) 
                self.output_panel.add_log(f"✅ تم إنشاء الملف وكتابة الكود وفتحه: {file_name}")
                return True
            else:
                self.output_panel.add_error(f"❌ فشل في إنشاء الملف على القرص: {file_name}")
                return False
                
        except Exception as e:
            logger.error(f"UIFileOperations: Error creating file and writing content: {e}", exc_info=True)
            self.output_panel.add_error(f"خطأ في إنشاء الملف: {str(e)}")
            return False
    
    def open_and_write_file(self, file_name: str, content: str):
       
        logger.info(f"UIFileOperations: Opening and ensuring content for file: {file_name}")
        try:
           
            self.main_window.open_file(file_name)
            
          
            current_editor = self.main_window.get_current_editor()
            
            if current_editor:
                current_content = current_editor.toPlainText()
               
                if current_content.strip() != content.strip():
                    current_editor.setPlainText(content)
                    self.output_panel.add_log(f"✍️ تم تحديث الكود في المحرر: {file_name}")
                   
                else:
                    self.output_panel.add_log(f"✅ الكود موجود بالفعل في المحرر: {file_name}")
            else:
                self.output_panel.add_error("❌ لم يتم العثور على محرر نشط بعد فتح الملف.")
                logger.error(f"UIFileOperations: No active editor found after opening file: {file_name}")
                
        except Exception as e:
            logger.error(f"UIFileOperations: Error opening and writing file: {e}", exc_info=True)
            self.output_panel.add_error(f"خطأ في فتح الملف وكتابة المحتوى: {str(e)}")
    
  
    
    def insert_code_in_editor(self, code: str):
       
        logger.info(f"UIFileOperations: Inserting code into editor. Code length: {len(code)}")
        try:
            current_editor = self.main_window.get_current_editor()
            if current_editor:
                cursor = current_editor.textCursor()
                cursor.insertText(code)
                current_editor.setTextCursor(cursor)
                self.output_panel.add_log("✅ تم إدراج الكود في المحرر")
            else:
              
                self.main_window.new_file() 
                new_editor = self.main_window.get_current_editor()
                if new_editor:
                    new_editor.setPlainText(code)
                    self.output_panel.add_log("✅ تم إنشاء تبويب جديد وإدراج الكود")
                else:
                    self.output_panel.add_error("❌ فشل في إدراج الكود: لا يوجد محرر نشط")
                    logger.error("UIFileOperations: Failed to get new editor after new_file() for insert_code.")
                
        except Exception as e:
            logger.error(f"UIFileOperations: Error inserting code: {e}", exc_info=True)
            self.output_panel.add_error(f"خطأ في إدراج الكود: {str(e)}")
    
    def replace_code_in_editor(self, code: str):
      
        logger.info(f"UIFileOperations: Replacing code in editor. Code length: {len(code)}")
        try:
            current_editor = self.main_window.get_current_editor()
            if current_editor:
                current_editor.setPlainText(code)
                self.output_panel.add_log("✅ تم استبدال الكود في المحرر")
               
            else:
              
                self.main_window.new_file() # هذا سيضيف تبويباً جديداً
                new_editor = self.main_window.get_current_editor()
                if new_editor:
                    new_editor.setPlainText(code)
                    self.output_panel.add_log("✅ تم إنشاء تبويب جديد واستبدال الكود")
                else:
                    self.output_panel.add_error("❌ فشل في استبدال الكود: لا يوجد محرر نشط")
                    logger.error("UIFileOperations: Failed to get new editor after new_file() for replace_code.")
                
        except Exception as e:
            logger.error(f"UIFileOperations: Error replacing code: {e}", exc_info=True)
            self.output_panel.add_error(f"خطأ في استبدال الكود: {str(e)}")
    
    def handle_ai_file_creation(self, response: Dict[str, Any]) -> bool:
       
        file_name = response.get('file_name', 'new_file.txt')
        content = response.get('content', '')
        file_type = response.get('file_type', 'text')
        
        logger.info(f"UIFileOperations: Handling AI file creation request for: {file_name}")
        
        try:
       
            self.main_window.open_file(file_name)
            self.output_panel.add_log(f"✅ تم فتح الملف الذي أنشأه الذكاء الاصطناعي: {file_name}")
            
           
            self.open_and_write_file(file_name, content) 
            
            return True
                
        except Exception as e:
            logger.error(f"UIFileOperations: Error handling AI file creation: {e}", exc_info=True)
            self.output_panel.add_error(f"خطأ في معالجة إنشاء الملف من الذكاء الاصطناعي: {str(e)}")
            return False
    
    def verify_file_content(self, file_path: str, expected_content: str) -> bool:
       
        logger.debug(f"UIFileOperations: Verifying content for: {file_path}")
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    actual_content = f.read()
                return actual_content.strip() == expected_content.strip()
            return False
        except Exception as e:
            logger.error(f"UIFileOperations: Error verifying file content: {e}", exc_info=True)
            self.output_panel.add_error(f"خطأ في التحقق من محتوى الملف: {str(e)}")
            return False
    
    def ensure_file_in_editor(self, file_name: str, content: str) -> bool:
        
        logger.info(f"UIFileOperations: Ensuring file '{file_name}' is in editor with correct content.")
        try:
          
            self.main_window.open_file(file_name)
            
          
            current_editor = self.main_window.get_current_editor()
            
            if current_editor:
                current_content = current_editor.toPlainText()
                if current_content.strip() != content.strip():
                    current_editor.setPlainText(content)
                    self.output_panel.add_log(f"🔄 تم تحديث محتوى الملف في المحرر: {file_name}")
                else:
                    self.output_panel.add_log(f"✅ الملف '{file_name}' موجود في المحرر ومحتواه صحيح.")
                return True
            else:
                self.output_panel.add_error(f"❌ فشل في التأكد من الملف '{file_name}': لا يوجد محرر نشط.")
                logger.error(f"UIFileOperations: No active editor found for ensure_file_in_editor for file: {file_name}")
                return False
                
        except Exception as e:
            logger.error(f"UIFileOperations: Error ensuring file in editor: {e}", exc_info=True)
            self.output_panel.add_error(f"خطأ في التأكد من الملف في المحرر: {str(e)}")
            return False