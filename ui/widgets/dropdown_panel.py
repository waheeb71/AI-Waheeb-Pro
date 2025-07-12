#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dropdown Panel Widget for AI Waheeb Pro
لوحة القوائم المنسدلة لـ AI Waheeb Pro
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton,
    QFrame, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class DropdownPanel(QWidget):
    """Panel with dropdown menus for voice control and AI assistant"""
    
    # Signals
    voice_control_requested = pyqtSignal()
    ai_assistant_requested = pyqtSignal()
    voice_toggle_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E293B;
                border-bottom: 1px solid #334155;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        # Voice Control Dropdown
        voice_label = QLabel("التحكم الصوتي:")
        voice_label.setStyleSheet("color: #F8FAFC; font-weight: bold;")
        layout.addWidget(voice_label)
        
        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "إيقاف التحكم الصوتي",
            "تشغيل التحكم الصوتي",
            "فتح نافذة التحكم الصوتي"
        ])
        self.voice_combo.setStyleSheet("""
            QComboBox {
                background-color: #334155;
                color: #F8FAFC;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 180px;
            }
            QComboBox:hover {
                border-color: #2563EB;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #F8FAFC;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #334155;
                color: #F8FAFC;
                border: 1px solid #475569;
                selection-background-color: #2563EB;
            }
        """)
        self.voice_combo.currentTextChanged.connect(self.on_voice_selection_changed)
        layout.addWidget(self.voice_combo)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setStyleSheet("color: #475569;")
        layout.addWidget(separator1)
        
        # AI Assistant Dropdown
        ai_label = QLabel("المساعد الذكي:")
        ai_label.setStyleSheet("color: #F8FAFC; font-weight: bold;")
        layout.addWidget(ai_label)
        
        self.ai_combo = QComboBox()
        self.ai_combo.addItems([
            "اختر عملية...",
            "فتح نافذة المساعد الذكي",
            "شرح الكود المحدد",
            "تحسين الكود",
            "تصحيح الأخطاء",
            "إنشاء كود جديد"
        ])
        self.ai_combo.setStyleSheet("""
            QComboBox {
                background-color: #334155;
                color: #F8FAFC;
                border: 1px solid #475569;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 180px;
            }
            QComboBox:hover {
                border-color: #10B981;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #F8FAFC;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #334155;
                color: #F8FAFC;
                border: 1px solid #475569;
                selection-background-color: #10B981;
            }
        """)
        self.ai_combo.currentTextChanged.connect(self.on_ai_selection_changed)
        layout.addWidget(self.ai_combo)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setStyleSheet("color: #475569;")
        layout.addWidget(separator2)
        
        # Quick Voice Button
        self.quick_voice_btn = QPushButton("🎤")
        self.quick_voice_btn.setCheckable(True)
        self.quick_voice_btn.setToolTip("تشغيل/إيقاف التحكم الصوتي السريع")
        self.quick_voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 20px;
                width: 40px;
                height: 40px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:checked {
                background-color: #DC2626;
            }
            QPushButton:checked:hover {
                background-color: #B91C1C;
            }
        """)
        self.quick_voice_btn.clicked.connect(self.voice_toggle_requested.emit)
        layout.addWidget(self.quick_voice_btn)
        
        # Spacer
        layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("جاهز")
        self.status_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(self.status_label)
        
    def on_voice_selection_changed(self, text):
        """Handle voice control selection change"""
        if text == "تشغيل التحكم الصوتي":
            self.voice_toggle_requested.emit()
            self.quick_voice_btn.setChecked(True)
        elif text == "إيقاف التحكم الصوتي":
            self.voice_toggle_requested.emit()
            self.quick_voice_btn.setChecked(False)
        elif text == "فتح نافذة التحكم الصوتي":
            self.voice_control_requested.emit()
        
        # Reset to default
        self.voice_combo.setCurrentIndex(0)
        
    def on_ai_selection_changed(self, text):
        """Handle AI assistant selection change"""
        if text == "فتح نافذة المساعد الذكي":
            self.ai_assistant_requested.emit()
        elif text != "اختر عملية...":
            # Emit signal with the selected action
            self.ai_action_requested(text)
        
        # Reset to default
        self.ai_combo.setCurrentIndex(0)
        
    def ai_action_requested(self, action):
        """Handle AI action request"""
        # This will be connected to the main window's AI functions
        if hasattr(self.parent(), 'handle_ai_action'):
            self.parent().handle_ai_action(action)
            
    def update_voice_status(self, is_listening):
        """Update voice control status"""
        self.quick_voice_btn.setChecked(is_listening)
        if is_listening:
            self.status_label.setText("🔴 جاري الاستماع...")
            self.status_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        else:
            self.status_label.setText("جاهز")
            self.status_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
            
    def update_ai_status(self, status):
        """Update AI status"""
        self.status_label.setText(status)
        if "جاري" in status:
            self.status_label.setStyleSheet("color: #F59E0B; font-size: 12px;")
        else:
            self.status_label.setStyleSheet("color: #94A3B8; font-size: 12px;")

