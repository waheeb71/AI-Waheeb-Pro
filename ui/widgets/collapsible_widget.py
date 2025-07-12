#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collapsible Widget for AI Code Editor
ويدجت قابل للطي لمحرر الأكواد الذكي
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, 
    QLabel, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QIcon, QPainter, QPen, QColor

class CollapsibleWidget(QWidget):
    """Widget قابل للطي مع تأثيرات بصرية جميلة"""
    
    # إشارات
    toggled = pyqtSignal(bool)  # عند تغيير حالة الطي
    
    def __init__(self, title: str, content_widget: QWidget, parent=None):
        super().__init__(parent)
        
        self.title = title
        self.content_widget = content_widget
        self.is_collapsed = False
        
        self.setup_ui()
        self.setup_animations()
        self.apply_styles()
        
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("CollapsibleWidget")
        
        # التخطيط الرئيسي
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # إنشاء شريط العنوان
        self.create_title_bar()
        
        # إنشاء منطقة المحتوى
        self.create_content_area()
        
    def create_title_bar(self):
        """إنشاء شريط العنوان القابل للنقر"""
        self.title_frame = QFrame()
        self.title_frame.setObjectName("TitleFrame")
        self.title_frame.setFixedHeight(40)
        self.title_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # تخطيط شريط العنوان
        title_layout = QHBoxLayout(self.title_frame)
        title_layout.setContentsMargins(12, 8, 12, 8)
        
        # أيقونة الطي/التوسيع
        self.toggle_icon = QPushButton()
        self.toggle_icon.setObjectName("ToggleIcon")
        self.toggle_icon.setFixedSize(24, 24)
        self.toggle_icon.setText("▼")
        self.toggle_icon.clicked.connect(self.toggle)
        title_layout.addWidget(self.toggle_icon)
        
        # عنوان النافذة
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("TitleLabel")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.title_label.setFont(font)
        title_layout.addWidget(self.title_label)
        
        # مساحة فارغة لدفع العناصر لليسار
        title_layout.addStretch()
        
        # إضافة تأثير الظل
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.title_frame.setGraphicsEffect(shadow)
        
        # ربط النقر على شريط العنوان
        self.title_frame.mousePressEvent = self.on_title_clicked
        
        self.main_layout.addWidget(self.title_frame)
        
    def create_content_area(self):
        """إنشاء منطقة المحتوى"""
        self.content_frame = QFrame()
        self.content_frame.setObjectName("ContentFrame")
        
        # تخطيط المحتوى
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.addWidget(self.content_widget)
        
        self.main_layout.addWidget(self.content_frame)
        
    def setup_animations(self):
        """إعداد الرسوم المتحركة"""
        # رسوم متحركة لتغيير الحجم
        self.size_animation = QPropertyAnimation(self.content_frame, b"maximumHeight")
        self.size_animation.setDuration(300)
        self.size_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # رسوم متحركة لدوران الأيقونة
        self.icon_animation = QPropertyAnimation(self.toggle_icon, b"rotation")
        self.icon_animation.setDuration(300)
        self.icon_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
    def apply_styles(self):
        """تطبيق الأنماط"""
        self.setStyleSheet("""
            CollapsibleWidget {
                background-color: transparent;
                border: none;
            }
            
            #TitleFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3B82F6, stop: 1 #2563EB);
                border: none;
                border-radius: 8px;
                color: white;
            }
            
            #TitleFrame:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2563EB, stop: 1 #1D4ED8);
            }
            
            #TitleLabel {
                color: white;
                background: transparent;
                border: none;
            }
            
            #ToggleIcon {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            
            #ToggleIcon:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            #ToggleIcon:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
            
            #ContentFrame {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-top: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }
        """)
        
    def toggle(self):
        """تبديل حالة الطي/التوسيع"""
        if self.is_collapsed:
            self.expand()
        else:
            self.collapse()
            
    def collapse(self):
        """طي النافذة"""
        if self.is_collapsed:
            return
            
        self.is_collapsed = True
        
        # حفظ الارتفاع الحالي
        current_height = self.content_frame.height()
        
        # بدء الرسوم المتحركة
        self.size_animation.setStartValue(current_height)
        self.size_animation.setEndValue(0)
        self.size_animation.start()
        
        # تغيير الأيقونة
        self.toggle_icon.setText("▶")
        
        # إخفاء المحتوى
        self.content_frame.setMaximumHeight(0)
        
        # إرسال إشارة
        self.toggled.emit(False)
        
    def expand(self):
        """توسيع النافذة"""
        if not self.is_collapsed:
            return
            
        self.is_collapsed = False
        
        # الحصول على الارتفاع المطلوب
        self.content_frame.setMaximumHeight(16777215)  # إزالة القيد المؤقت
        target_height = self.content_widget.sizeHint().height() + 16  # مع الهوامش
        
        # بدء الرسوم المتحركة
        self.size_animation.setStartValue(0)
        self.size_animation.setEndValue(target_height)
        self.size_animation.start()
        
        # تغيير الأيقونة
        self.toggle_icon.setText("▼")
        
        # إرسال إشارة
        self.toggled.emit(True)
        
    def on_title_clicked(self, event):
        """معالج النقر على شريط العنوان"""
        self.toggle()
        
    def set_title(self, title: str):
        """تعيين عنوان جديد"""
        self.title = title
        self.title_label.setText(title)
        
    def is_expanded(self) -> bool:
        """التحقق من حالة التوسيع"""
        return not self.is_collapsed
        
    def set_expanded(self, expanded: bool):
        """تعيين حالة التوسيع"""
        if expanded and self.is_collapsed:
            self.expand()
        elif not expanded and not self.is_collapsed:
            self.collapse()


class CollapsibleDockWidget(QWidget):
    """نافذة dock قابلة للطي"""
    
    def __init__(self, title: str, content_widget: QWidget, parent=None):
        super().__init__(parent)
        
        # إعداد التخطيط
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # إنشاء الويدجت القابل للطي
        self.collapsible = CollapsibleWidget(title, content_widget)
        layout.addWidget(self.collapsible)
        
        # إضافة مساحة فارغة في الأسفل
        layout.addStretch()
        
    def toggle(self):
        """تبديل حالة الطي"""
        self.collapsible.toggle()
        
    def set_expanded(self, expanded: bool):
        """تعيين حالة التوسيع"""
        self.collapsible.set_expanded(expanded)
        
    def is_expanded(self) -> bool:
        """التحقق من حالة التوسيع"""
        return self.collapsible.is_expanded()

