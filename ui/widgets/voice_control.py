#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Control Widget
مكون التحكم الصوتي
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QProgressBar, QFrame, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette

# تهيئة المسجل لهذا الملف
logger = logging.getLogger(__name__)

class VoiceVisualizerWidget(QWidget):
    """Voice level visualizer"""
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self.volume_level = 0.0
        self.is_active = False
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        
    def set_volume(self, level: float):
        """Set volume level (0.0 to 1.0)"""
        self.volume_level = max(0.0, min(1.0, level))
        self.update()
    
    def set_active(self, active: bool):
        """Set active state"""
        self.is_active = active
        if active:
            self.animation_timer.start(50)  # 20 FPS
        else:
            self.animation_timer.stop()
        self.update()
    
    def paintEvent(self, event):
        """Paint the visualizer"""
        from PyQt6.QtGui import QPainter, QColor, QBrush
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#1E293B"))
        
        if not self.is_active:
            # Draw inactive state
            painter.setPen(QColor("#64748B"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🎤 غير نشط")
            return
        
        # Draw volume bars
        bar_count = 20
        bar_width = self.width() // bar_count - 2
        max_height = self.height() - 10
        
        for i in range(bar_count):
            x = i * (bar_width + 2) + 5
            
            # Calculate bar height based on volume and position
            base_height = max_height * 0.1
            volume_height = max_height * self.volume_level * (0.5 + 0.5 * (i / bar_count))
            bar_height = base_height + volume_height
            
            y = self.height() - bar_height - 5
            
            # Color based on volume level
            if self.volume_level > 0.8:
                color = QColor("#EF4444")  # Red
            elif self.volume_level > 0.5:
                color = QColor("#F59E0B")  # Orange
            else:
                color = QColor("#10B981")  # Green
            
            # Fade color based on position
            alpha = int(255 * (0.3 + 0.7 * (i / bar_count)))
            color.setAlpha(alpha)
            
            painter.fillRect(int(x), int(y), bar_width, int(bar_height), color)

class VoiceControlWidget(QWidget):
    """Voice control widget"""
    
    # Signals
    voice_command_ready = pyqtSignal(str)
    
    def __init__(self, voice_service, gemini_service):
        super().__init__()
        self.voice_service = voice_service
        self.gemini_service = gemini_service
        
        # State
        self.is_listening = False
        self.recognized_text = ""
        
        # UI components
        self.record_button = None
        self.text_display = None
        self.status_label = None
        self.volume_visualizer = None
        self.send_button = None
        self.clear_button = None
        
        self.init_ui()
        self.setup_connections()
        
        logger.info("VoiceControlWidget: Voice control widget initialized.")
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel("التحكم الصوتي")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #F8FAFC; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Record button
        self.record_button = QPushButton("🎤 ابدأ التسجيل")
        self.record_button.setFixedHeight(60)
        self.record_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
            QPushButton:checked {
                background-color: #DC2626;
            }
        """)
        self.record_button.setCheckable(True)
        layout.addWidget(self.record_button)
        
        # Volume visualizer
        self.volume_visualizer = VoiceVisualizerWidget()
        layout.addWidget(self.volume_visualizer)
        
        # Status label
        self.status_label = QLabel("اضغط للبدء في التسجيل")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #94A3B8; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #334155;")
        layout.addWidget(separator)
        
        # Text display
        text_label = QLabel("النص المحول:")
        text_label.setStyleSheet("color: #F8FAFC; font-weight: bold;")
        layout.addWidget(text_label)
        
        self.text_display = QTextEdit()
        self.text_display.setMaximumHeight(120)
        self.text_display.setPlaceholderText("سيظهر النص المحول من الصوت هنا...")
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Arial';
                font-size: 11px;
            }
        """)
        self.text_display.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_display)
        
        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton("📤 إرسال")
        self.send_button.clicked.connect(self.send_command)
        self.send_button.setEnabled(False)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #374151;
                color: #6B7280;
            }
        """)
        buttons_layout.addWidget(self.send_button)
        
        self.clear_button = QPushButton("🗑️ مسح")
        self.clear_button.clicked.connect(self.clear_text)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        buttons_layout.addWidget(self.clear_button)
        
        layout.addLayout(buttons_layout)
        
        # Voice settings
        settings_label = QLabel("إعدادات الصوت:")
        settings_label.setStyleSheet("color: #F8FAFC; font-weight: bold; margin-top: 10px;")
        layout.addWidget(settings_label)
        
        # Sensitivity slider
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("الحساسية:"))
        
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(5)
        self.sensitivity_slider.valueChanged.connect(self.on_sensitivity_changed)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        
        self.sensitivity_value = QLabel("5")
        sensitivity_layout.addWidget(self.sensitivity_value)
        
        layout.addLayout(sensitivity_layout)
        
        # Language selection
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("اللغة:"))
        
        self.arabic_button = QPushButton("العربية")
        self.arabic_button.setCheckable(True)
        self.arabic_button.setChecked(True)
        self.arabic_button.clicked.connect(lambda: self.set_language("ar-SA"))
        language_layout.addWidget(self.arabic_button)
        
        self.english_button = QPushButton("English")
        self.english_button.setCheckable(True)
        self.english_button.clicked.connect(lambda: self.set_language("en-US"))
        language_layout.addWidget(self.english_button)
        
        layout.addLayout(language_layout)
        
        # Quick commands
        quick_label = QLabel("أوامر سريعة:")
        quick_label.setStyleSheet("color: #F8FAFC; font-weight: bold; margin-top: 10px;")
        layout.addWidget(quick_label)
        
        quick_commands = [
            "اكتب دالة لحساب مضروب العدد",
            "أضف تعليق يشرح هذا الكود",
            "أنشئ حلقة تكرار",
            "اشرح هذا الكود"
        ]
        
        for command in quick_commands:
            btn = QPushButton(command)
            btn.clicked.connect(lambda checked, cmd=command: self.set_quick_command(cmd))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    color: #D1D5DB;
                    border: 1px solid #4B5563;
                    padding: 6px 12px;
                    border-radius: 4px;
                    text-align: left;
                    margin: 2px;
                }
                QPushButton:hover {
                    background-color: #4B5563;
                }
            """)
            layout.addWidget(btn)
        
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        logger.info("VoiceControlWidget: Setting up connections for voice service.")
        if self.voice_service:
            self.voice_service.text_recognized.connect(self.on_text_recognized)
            self.voice_service.listening_started.connect(self.on_listening_started)
            self.voice_service.listening_stopped.connect(self.on_listening_stopped)
            self.voice_service.volume_changed.connect(self.on_volume_changed)
            self.voice_service.error_occurred.connect(self.on_error) # هذا هو الربط المهم
            logger.info("VoiceControlWidget: Voice service connections established.")
        else:
            logger.warning("VoiceControlWidget: Voice service is None, cannot setup connections.")
        
        # ربط إشارة gemini_service.error_occurred بـ on_error في VoiceControlWidget
        # هذا الربط قد يكون مكررًا إذا كان EnhancedMainWindow يقوم بذلك بالفعل
        # ولكن للتأكد من استقبال الأخطاء من معالج الذكاء الاصطناعي هنا:
        if self.gemini_service:
            self.gemini_service.error_occurred.connect(self.on_error)
            logger.info("VoiceControlWidget: Connected to gemini_service.error_occurred.")


    def toggle_recording(self):
        """Toggle voice recording"""
        logger.info(f"VoiceControlWidget: Toggle recording. Current state: is_listening={self.is_listening}")
        if self.is_listening:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start voice recording"""
        logger.info("VoiceControlWidget: Attempting to start recording.")
        if self.voice_service and self.voice_service.is_available():
            self.voice_service.start_listening()
            logger.info("VoiceControlWidget: Voice service start_listening called.")
        else:
            self.status_label.setText("خدمة التعرف على الصوت غير متاحة")
            self.record_button.setChecked(False)
            logger.error("VoiceControlWidget: Voice service not available or not initialized.")
            self.on_error("خدمة التعرف على الصوت غير متاحة.") # عرض الخطأ في الواجهة والسجل
    
    def stop_recording(self):
        """Stop voice recording"""
        logger.info("VoiceControlWidget: Attempting to stop recording.")
        if self.voice_service:
            self.voice_service.stop_listening()
            logger.info("VoiceControlWidget: Voice service stop_listening called.")
        else:
            logger.warning("VoiceControlWidget: Voice service is None, cannot stop recording.")
            
    def on_listening_started(self):
        """Handle listening started"""
        self.is_listening = True
        self.record_button.setText("� جاري التسجيل...")
        self.record_button.setChecked(True)
        self.status_label.setText("جاري الاستماع... تحدث الآن")
        self.volume_visualizer.set_active(True)
        logger.info("VoiceControlWidget: Listening started.")
    
    def on_listening_stopped(self):
        """Handle listening stopped"""
        self.is_listening = False
        self.record_button.setText("🎤 ابدأ التسجيل")
        self.record_button.setChecked(False)
        self.status_label.setText("تم إيقاف التسجيل")
        self.volume_visualizer.set_active(False)
        logger.info("VoiceControlWidget: Listening stopped.")
    
    def on_text_recognized(self, text: str):
        """Handle text recognition"""
        logger.info(f"VoiceControlWidget: Text recognized: '{text}'")
        self.recognized_text = text
        self.text_display.setPlainText(text)
        self.status_label.setText(f"تم التعرف على: {text[:30]}...")
        self.send_button.setEnabled(True)
    
    def on_volume_changed(self, volume: float):
        """Handle volume change"""
        # logger.debug(f"VoiceControlWidget: Volume changed to: {volume}") # قد يكون مزعجًا، استخدم debug
        self.volume_visualizer.set_volume(volume)
    
    def on_error(self, error: str):
        """Handle error and display it"""
        logger.error(f"VoiceControlWidget: An error occurred: {error}") # إضافة تسجيل الخطأ
        self.status_label.setText(f"خطأ: {error}")
        self.record_button.setChecked(False)
        self.volume_visualizer.set_active(False)
    
    def on_text_changed(self):
        """Handle text change in display"""
        text = self.text_display.toPlainText().strip()
        self.send_button.setEnabled(bool(text))
        # logger.debug(f"VoiceControlWidget: Text changed, send button enabled: {bool(text)}")
    
    def send_command(self):
        """Send voice command"""
        text = self.text_display.toPlainText().strip()
        logger.info(f"VoiceControlWidget: Send command button clicked. Text to send: '{text}'")
        if text:
            self.voice_command_ready.emit(text)
            self.status_label.setText("تم إرسال الأمر للمعالجة...")
            logger.info("VoiceControlWidget: voice_command_ready signal emitted.")
        else:
            logger.warning("VoiceControlWidget: Attempted to send empty command.")
            self.status_label.setText("لا يوجد نص لإرساله.")
    
    def clear_text(self):
        """Clear text display"""
        self.text_display.clear()
        self.recognized_text = ""
        self.send_button.setEnabled(False)
        self.status_label.setText("تم مسح النص")
        logger.info("VoiceControlWidget: Text display cleared.")
    
    def set_recognized_text(self, text: str):
        """Set recognized text"""
        logger.info(f"VoiceControlWidget: Manually setting recognized text: '{text}'")
        self.recognized_text = text
        self.text_display.setPlainText(text)
        self.send_button.setEnabled(bool(text.strip()))
    
    def set_quick_command(self, command: str):
        """Set quick command"""
        logger.info(f"VoiceControlWidget: Setting quick command: '{command}'")
        self.text_display.setPlainText(command)
        self.send_button.setEnabled(True)
        # Assuming quick commands are immediately sent, trigger send_command
        self.send_command() 
    
    def on_sensitivity_changed(self, value: int):
        """Handle sensitivity change"""
        self.sensitivity_value.setText(str(value))
        logger.info(f"VoiceControlWidget: Sensitivity changed to: {value}")
        # Update voice service sensitivity if available
        if self.voice_service:
            # This would update the voice recognition sensitivity
            logger.debug("VoiceControlWidget: Placeholder for updating voice service sensitivity.")
            pass
    
    def set_language(self, language: str):
        """Set recognition language"""
        logger.info(f"VoiceControlWidget: Setting language to: {language}")
        if language == "ar-SA":
            self.arabic_button.setChecked(True)
            self.english_button.setChecked(False)
        else:
            self.arabic_button.setChecked(False)
            self.english_button.setChecked(True)
        
        # Update voice service language
        if self.voice_service:
            settings = {'language': language}
            self.voice_service.update_settings(settings)
            logger.info("VoiceControlWidget: Voice service language updated.")
        else:
            logger.warning("VoiceControlWidget: Voice service is None, cannot update language.")
    
    def get_status(self) -> dict:
        """Get widget status"""
        status = {
            'is_listening': self.is_listening,
            'recognized_text': self.recognized_text,
            'is_available': self.voice_service.is_available() if self.voice_service else False
        }
        logger.debug(f"VoiceControlWidget: Getting status: {status}")
        return status

