#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
About Dialog
نافذة حول البرنامج
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

class AboutDialog(QDialog):
    """About dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("حول AI Waheeb Pro")
        self.setModal(True)
        self.setFixedSize(500, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Logo and title
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo (if available)
        logo_label = QLabel("🤖")
        logo_label.setFont(QFont("Arial", 48))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("AI Waheeb Pro")
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2563EB; margin: 10px;")
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("مساعد البرمجة الذكي المتقدم")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #6B7280; margin-bottom: 20px;")
        header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # Version info
        version_frame = QFrame()
        version_frame.setFrameStyle(QFrame.Shape.Box)
        version_frame.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        version_layout = QVBoxLayout(version_frame)
        
        version_info = [
            ("الإصدار:", "2.0.0"),
            ("تاريخ الإصدار:", "2025-01-08"),
            ("نوع الترخيص:", "MIT License"),
            ("المطور:", "AI Waheeb Team"),
            ("نموذج الذكاء الاصطناعي:", "Google Gemini AI")
        ]
        
        for label, value in version_info:
            info_layout = QHBoxLayout()
            info_layout.addWidget(QLabel(label))
            info_layout.addStretch()
            value_label = QLabel(value)
            value_label.setStyleSheet("font-weight: bold; color: #10B981;")
            info_layout.addWidget(value_label)
            version_layout.addLayout(info_layout)
        
        layout.addWidget(version_frame)
        
        # Description
        desc_label = QLabel("الوصف:")
        desc_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(desc_label)
        
        description = QTextEdit()
        description.setReadOnly(True)
        description.setMaximumHeight(150)
        description.setPlainText("""AI Waheeb Pro هو مساعد برمجة ذكي متقدم يستخدم تقنيات الذكاء الاصطناعي من Google Gemini لمساعدة المطورين في كتابة وتحسين الكود.

الميزات الرئيسية:
• محرر كود متقدم مع تمييز الصيغة
• التحكم الصوتي والتعرف على الأوامر
• شرح وتحسين الكود تلقائياً
• إدارة المشاريع والملفات
• واجهة مستخدم احترافية ومظلمة
• دعم اللغة العربية والإنجليزية""")
        
        description.setStyleSheet("""
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
        layout.addWidget(description)
        
        # Features
        features_label = QLabel("التقنيات المستخدمة:")
        features_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(features_label)
        
        features_frame = QFrame()
        features_frame.setFrameStyle(QFrame.Shape.Box)
        features_frame.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        features_layout = QVBoxLayout(features_frame)
        
        technologies = [
            "🐍 Python 3.11+",
            "🖼️ PyQt6 للواجهة الرسومية",
            "🤖 Google Gemini AI API",
            "🎤 Speech Recognition",
            "🎨 Pygments لتمييز الصيغة",
            "📁 نظام إدارة ملفات متقدم"
        ]
        
        for tech in technologies:
            tech_label = QLabel(tech)
            tech_label.setStyleSheet("margin: 2px; color: #D1D5DB;")
            features_layout.addWidget(tech_label)
        
        layout.addWidget(features_frame)
        
        # Contact info
        contact_label = QLabel("للدعم والتواصل:")
        contact_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(contact_label)
        
       # Contact Info - Updated to Telegram
        telegram_account_link = "<a href='https://t.me/WAT4F' style='color:#60A5FA; text-decoration:none;'>👤 حسابي على التليجرام</a>"
        telegram_channel_link = "<a href='https://t.me/cyber_code1' style='color:#60A5FA; text-decoration:none;'>📢 قناتي على التليجرام</a>"
        
        contact_info = QLabel(f"{telegram_account_link} | {telegram_channel_link}")
        contact_info.setFont(QFont("Arial", 10))
        contact_info.setStyleSheet("color: #94A3B8;") # هذا اللون للخلفية، الروابط لها لونها الخاص في الـ HTML
        contact_info.setOpenExternalLinks(True) # مهم جداً لفتح الروابط في المتصفح الافتراضي
        layout.addWidget(contact_info)
        
        # Close button
        close_button = QPushButton("إغلاق")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0A0B;
                color: #F8FAFC;
            }
            QLabel {
                color: #F8FAFC;
            }
        """)

