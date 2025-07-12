#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Assistant Widget
مكون المساعد الذكي
"""

import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QScrollArea, QFrame, QDialog, QApplication,
    QTextBrowser # Import QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor

logger = logging.getLogger(__name__)

class EnlargedResponseDialog(QDialog):
    """
    A dialog to display the full AI response for easier reading.
    """
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400) # Set a reasonable default size

        layout = QVBoxLayout(self)

        response_text_edit = QTextBrowser() # Changed to QTextBrowser
        response_text_edit.setReadOnly(True)
        response_text_edit.setHtml(content) # Use setHtml to preserve formatting
        response_text_edit.setFont(QFont("Arial", 11))
        response_text_edit.setStyleSheet("""
            QTextBrowser { /* Changed selector to QTextBrowser */
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Arial';
            }
        """)
        layout.addWidget(response_text_edit)

        close_button = QPushButton("إغلاق")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

class AIAssistantWidget(QWidget):
    """AI Assistant widget for code help and suggestions"""
    
    # Signals
    command_requested = pyqtSignal(str)
    
    def __init__(self, gemini_service):
        super().__init__()
        self.gemini_service = gemini_service
        
        # Store full responses for enlargement
        self.full_ai_responses = []

        # UI components
        self.chat_area = None
        self.input_text = None
        self.send_button = None
        self.quick_actions = None
        
        self.init_ui()
        self.setup_connections()
        
        logger.info("AI Assistant widget initialized")
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8) # Reduced spacing

        # Title
        title_label = QLabel("المساعد الذكي 🤖") # Added an emoji for visual appeal
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #F8FAFC; margin-bottom: 5px;") # Reduced margin
        layout.addWidget(title_label)
        
        # Chat area
        self.chat_area = QTextBrowser() # Changed to QTextBrowser
        self.chat_area.setReadOnly(True) # QTextBrowser is read-only by default, but good to be explicit
        self.chat_area.setMinimumHeight(150) # Set a minimum height
        self.chat_area.setMaximumHeight(250) # Reduced maximum height for compactness
        self.chat_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_area.setStyleSheet("""
            QTextBrowser { /* Changed selector to QTextBrowser */
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px; /* Slightly more rounded corners */
                padding: 8px;
                font-family: 'Arial';
                font-size: 11px;
                selection-background-color: #2563EB; /* Highlight selected text */
            }
            QScrollBar:vertical {
                border: none;
                background: #1E293B;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4B5563;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.chat_area.setPlaceholderText("ستظهر هنا استجابات المساعد الذكي...")
        layout.addWidget(self.chat_area)
        
        # Input area
        input_layout = QVBoxLayout()
        input_layout.setSpacing(5) # Reduced spacing

        input_label = QLabel("اسأل المساعد الذكي:")
        input_label.setStyleSheet("color: #F8FAFC; font-weight: bold;")
        input_layout.addWidget(input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setMinimumHeight(40) # Minimum height for input
        self.input_text.setMaximumHeight(70) # Max height for compactness
        self.input_text.setPlaceholderText("اكتب سؤالك أو طلبك هنا...")
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Arial';
                font-size: 11px;
            }
        """)
        input_layout.addWidget(self.input_text)
        
        # Send button
        self.send_button = QPushButton("إرسال 🚀") # Added emoji
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6B7280;
            }
        """)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #334155; margin-top: 5px; margin-bottom: 5px;") # Adjusted margins
        layout.addWidget(separator)
        
        # Quick actions
        quick_label = QLabel("إجراءات سريعة:")
        quick_label.setStyleSheet("color: #F8FAFC; font-weight: bold; margin-top: 5px;")
        layout.addWidget(quick_label)
        
        # Scroll area for quick actions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150) # Reduced height for compactness
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #1E293B;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4B5563;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        self.quick_actions = QWidget()
        quick_layout = QVBoxLayout(self.quick_actions)
        quick_layout.setSpacing(4) # Reduced spacing
        quick_layout.setContentsMargins(0, 0, 0, 0) # Remove margins around quick action buttons
        
        # Quick action buttons
        quick_actions_data = [
            ("🔍 شرح الكود المحدد", "explain_selected"),
            ("⚡ تحسين الكود", "optimize_code"),
            ("🐛 العثور على الأخطاء", "find_bugs"),
            ("📝 إضافة تعليقات", "add_comments"),
            ("🔄 إعادة هيكلة الكود", "refactor_code"),
            ("📚 إنشاء وثائق", "generate_docs"),
            ("🧪 إنشاء اختبارات", "generate_tests"),
            ("💡 اقتراح تحسينات", "suggest_improvements"),
            ("🎯 تحليل الأداء", "analyze_performance"),
            ("🔒 فحص الأمان", "security_check")
        ]
        
        for text, action in quick_actions_data:
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, a=action: self.quick_action(a))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    color: #D1D5DB;
                    border: 1px solid #4B5563;
                    padding: 6px 10px; /* Smaller padding */
                    border-radius: 4px;
                    text-align: left;
                    font-size: 11px; /* Slightly smaller font */
                }
                QPushButton:hover {
                    background-color: #4B5563;
                    color: #F9FAFB;
                }
            """)
            quick_layout.addWidget(btn)
        quick_layout.addStretch() # Push buttons to the top

        scroll_area.setWidget(self.quick_actions)
        layout.addWidget(scroll_area)
        
        # Status
        self.status_label = QLabel("جاهز للمساعدة ✨") # Added emoji
        self.status_label.setStyleSheet("color: #94A3B8; font-style: italic; margin-top: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch() # Pushes all content to the top
    
    def setup_connections(self):
        """Setup signal connections"""
        if self.gemini_service:
            self.gemini_service.response_ready.connect(self.on_ai_response)
            self.gemini_service.error_occurred.connect(self.on_error)
            self.gemini_service.progress_updated.connect(self.on_progress)
        
        # IMPORTANT: Connect anchorClicked here, once.
        self.chat_area.anchorClicked.connect(self._handle_anchor_click)

    def send_message(self):
        """Send message to AI"""
        message = self.input_text.toPlainText().strip()
        if not message:
            return
        
        # Add user message to chat
        self.add_message("أنت", message, is_user=True, full_content=message) # Pass full content
        
        # Clear input
        self.input_text.clear()
        
        # Send to AI
        self.status_label.setText("جاري المعالجة... ⏳")
        self.send_button.setEnabled(False)
        
        # Process with Gemini
        if self.gemini_service:
            self.gemini_service.process_general_query(message)
    
    def quick_action(self, action: str):
        """Execute quick action"""
        action_messages = {
            "explain_selected": "اشرح الكود المحدد حالياً",
            "optimize_code": "حسن الكود الحالي لجعله أكثر كفاءة",
            "find_bugs": "ابحث عن الأخطاء المحتملة في الكود",
            "add_comments": "أضف تعليقات توضيحية للكود",
            "refactor_code": "أعد هيكلة الكود لجعله أكثر وضوحاً",
            "generate_docs": "أنشئ وثائق للكود الحالي",
            "generate_tests": "أنشئ اختبارات للكود الحالي",
            "suggest_improvements": "اقترح تحسينات للكود",
            "analyze_performance": "حلل أداء الكود واقترح تحسينات",
            "security_check": "افحص الكود للثغرات الأمنية المحتملة"
        }
        
        message = action_messages.get(action, action)
        self.input_text.setPlainText(message)
        self.send_message()
    
    def add_message(self, sender: str, message_snippet: str, is_user: bool = False, full_content: str = ""):
        """Add message to chat area, with optional full content for AI responses."""
        from datetime import datetime
        
        time_str = datetime.now().strftime("%H:%M")
        
        if is_user:
            formatted_message = f"""
<div style="margin: 8px 0; padding: 10px 12px; background-color: #2563EB; border-radius: 12px; color: white; max-width: 90%; float: right; clear: both;">
    <strong style="font-size: 12px;">{sender}</strong> <span style="font-size: 9px; opacity: 0.8;">{time_str}</span><br>
    <p style="margin-top: 5px; margin-bottom: 0; font-size: 11px;">{message_snippet}</p>
</div>
"""
        else:
            # Store the full AI response
            self.full_ai_responses.append(full_content)
            response_index = len(self.full_ai_responses) - 1 

            #
            display_message = message_snippet
            if len(message_snippet) > 150: # Adjust threshold as needed
                display_message = message_snippet[:150] + "..."

            
            enlarge_button_html = f"""
            <a href="pyqt_signal://enlargeResponse/{response_index}" style="color: #60A5FA; text-decoration: underline; font-size: 10px; margin-left: 5px;">[تكبير]</a>
            """ if len(message_snippet) > 150 else "" 

            formatted_message = f"""
<div style="margin: 8px 0; padding: 10px 12px; background-color: #374151; border-radius: 12px; color: #F9FAFB; max-width: 90%; float: left; clear: both;">
    <strong style="font-size: 12px;">{sender}</strong> <span style="font-size: 9px; opacity: 0.8;">{time_str}</span><br>
    <p style="margin-top: 5px; margin-bottom: 0; font-size: 11px;">{display_message}{enlarge_button_html}</p>
</div>
"""
        
        self.chat_area.append(formatted_message)
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())

    def _handle_anchor_click(self, url):
        """Handle clicks on custom anchors, specifically for enlarge buttons."""
        if url.scheme() == 'pyqt_signal' and url.host() == 'enlargeResponse':
            try:
                index = int(url.path().lstrip('/'))
                self.enlarge_ai_response(index)
            except ValueError:
                logger.error(f"Invalid index in enlargeResponse URL: {url.path()}")

    def enlarge_ai_response(self, index: int):
        """Opens a new dialog to show the full AI response."""
        if 0 <= index < len(self.full_ai_responses):
            full_content = self.full_ai_responses[index]
            dialog = EnlargedResponseDialog("استجابة المساعد الذكي الكاملة", full_content, self)
            dialog.exec() # Show as a modal dialog
        else:
            logger.warning(f"Attempted to enlarge non-existent AI response at index: {index}")

    def on_ai_response(self, response: Dict[str, Any]):
        """Handle AI response"""
        content = response.get('content', 'لا توجد استجابة')
        action = response.get('action', '')
        
        # Add AI response to chat, passing the full content
        self.add_message("المساعد الذكي", content, is_user=False, full_content=content) 
        
        # Reset status
        self.status_label.setText("جاهز للمساعدة ✨")
        self.send_button.setEnabled(True)
        
       
        if action in ['add_code', 'replace_code', 'add_comment']:
            self.command_requested.emit(content)
    
    def on_error(self, error: str):
        """Handle error"""
        self.add_message("النظام", f"حدث خطأ: {error}", is_user=False)
        self.status_label.setText("حدث خطأ ❌")
        self.send_button.setEnabled(True)
    
    def on_progress(self, message: str):
        """Handle progress update"""
        self.status_label.setText(message + "...") 
    
    def clear_chat(self):
        """Clear chat area"""
        self.chat_area.clear()
        self.full_ai_responses = [] 
        self.status_label.setText("تم مسح المحادثة ✅")
    
    def set_context(self, code: str, file_path: str = None):
        """Set current code context for AI"""
        context_message = "السياق الحالي:\n"
        if file_path:
            context_message += f"الملف: {file_path}\n"
        context_message += f"الكود:\n```python\n{code}\n```"
        
      
        if self.gemini_service:
            self.gemini_service.set_context(code, file_path)
    
    def get_suggestions(self, code: str) -> list:
        """Get AI suggestions for code"""
       
        suggestions = [
            "إضافة معالجة للأخطاء",
            "تحسين أسماء المتغيرات",
            "إضافة تعليقات توضيحية",
            "تحسين الأداء"
        ]
        return suggestions


if __name__ == '__main__':
    import sys
    from PyQt6.QtCore import QTimer

    class MockGeminiService(QWidget):
        """A mock service to simulate Gemini AI responses."""
        response_ready = pyqtSignal(dict)
        error_occurred = pyqtSignal(str)
        progress_updated = pyqtSignal(str)

        def __init__(self):
            super().__init__()
            self.context_code = ""
            self.context_file = ""

        def process_general_query(self, query: str):
            self.progress_updated.emit("جاري التفكير...")
            QTimer.singleShot(1000, lambda: self._simulate_response(query))

        def _simulate_response(self, query: str):
            if "error" in query.lower():
                self.error_occurred.emit("حدث خطأ في معالجة طلبك.")
            elif "code" in query.lower():
                response_content = f"بالتأكيد، إليك بعض الأفكار حول طلبك المتعلق بالكود '{query}':\n\n```python\n# This is a suggested code snippet based on your query.\ndef example_function():\n    print('Hello from AI!')\n```\n\nهذا مجرد مثال توضيحي. إذا كنت بحاجة إلى مزيد من المساعدة، فلا تتردد في السؤال!"
                self.response_ready.emit({'content': response_content, 'action': 'add_code'})
            else:
                long_response = "هذه استجابة طويلة جداً من المساعد الذكي لتوضيح وظيفة زر التكبير. تخيل أن هنا الكثير من المعلومات التقنية المفيدة والنصائح البرمجية التفصيلية التي لا يمكن عرضها بالكامل في النافذة الصغيرة. يمكنك استخدام زر 'تكبير' لقراءة كل التفاصيل بسهولة في نافذة منفصلة أكبر. على سبيل المثال، قد تحتوي هذه الاستجابة على شرح مفصل لخوارزمية معينة، أو تحليل معمق لأداء قطعة من الكود، أو حتى قائمة طويلة من الحلول المقترحة لمشكلة برمجية معقدة. إن الهدف من هذا الزر هو تحسين تجربة المستخدم عندما تكون الاستجابات طويلة وغنية بالمعلومات، مما يضمن سهولة الوصول إلى المحتوى الكامل دون الحاجة إلى التمرير المستمر في نافذة صغيرة. نتمنى أن يكون هذا مفيداً!"
                short_response = "مرحباً! كيف يمكنني مساعدتك اليوم؟ هذه استجابة قصيرة."
                if "long" in query.lower():
                    self.response_ready.emit({'content': long_response, 'action': ''})
                else:
                    self.response_ready.emit({'content': short_response, 'action': ''})

        def set_context(self, code: str, file_path: str = None):
            self.context_code = code
            self.context_file = file_path
            logger.info(f"Mock Gemini Service: Context set for file '{file_path}' with code snippet.")


    app = QApplication(sys.argv)
    app.setApplicationName("AI Assistant Demo")

  
    app.setStyleSheet("""
        QWidget {
            background-color: #020617; /* Dark background for the main window */
            color: #F8FAFC;
            font-family: 'Arial';
        }
        QPushButton {
            background-color: #2563EB;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1D4ED8;
        }
    """)

    gemini_mock = MockGeminiService()
    assistant_widget = AIAssistantWidget(gemini_mock)
    assistant_widget.setWindowTitle("مساعد الذكاء الاصطناعي التجريبي")
    assistant_widget.setMinimumWidth(350) 
    assistant_widget.show()

    sys.exit(app.exec())