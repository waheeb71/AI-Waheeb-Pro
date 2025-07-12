#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Dialog
نافذة الإعدادات
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QCheckBox,
    QSpinBox, QComboBox, QTextEdit, QGroupBox, QSlider,
    QFileDialog, QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Settings dialog"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("الإعدادات")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # General tab
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, "عام")
        
        # Editor tab
        editor_tab = self.create_editor_tab()
        tab_widget.addTab(editor_tab, "المحرر")
        
        # AI tab
        ai_tab = self.create_ai_tab()
        tab_widget.addTab(ai_tab, "الذكاء الاصطناعي")
        
        # Voice tab
        voice_tab = self.create_voice_tab()
        tab_widget.addTab(voice_tab, "الصوت")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        
        layout.addWidget(button_box)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #0A0A0B;
                color: #F8FAFC; /* هذا اللون هو لون النص الافتراضي لأغلب العناصر */
            }
            
            /* أضف هذه القاعدة لضمان أن الـ QLabel والـ QCheckBox تظهر نصوصها بلون فاتح */
            QLabel, QCheckBox {
                color: #F8FAFC; /* لون أبيض تقريباً لضمان الوضوح */
            }

            QTabWidget::pane {
                border: 1px solid #334155;
                background-color: #0F172A;
            }
            QTabBar::tab {
                background-color: #1E293B;
                color: #94A3B8; /* لون أفتح قليلاً لأزرار التبويبات غير المختارة */
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0F172A;
                color: #F8FAFC; /* لون أبيض لأزرار التبويبات المختارة */
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #334155;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #F8FAFC; /* تأكد من أن لون عنوان المجموعة فاتح */
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background-color: #1E293B;
                color: #F8FAFC; /* لون النص في خانات الإدخال وصناديق الاختيار والقوائم المنسدلة */
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
    
    def create_general_tab(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Appearance group
        appearance_group = QGroupBox("المظهر")
        appearance_layout = QVBoxLayout(appearance_group)
        
        # Theme
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("السمة:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["مظلم", "فاتح", "تلقائي"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        # Font size
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("حجم الخط:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()
        appearance_layout.addLayout(font_layout)
        
        layout.addWidget(appearance_group)
        
        # Language group
        language_group = QGroupBox("اللغة")
        language_layout = QVBoxLayout(language_group)
        
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("لغة الواجهة:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["العربية", "English"])
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        language_layout.addLayout(lang_layout)
        
        layout.addWidget(language_group)
        
        # Startup group
        startup_group = QGroupBox("بدء التشغيل")
        startup_layout = QVBoxLayout(startup_group)
        
        self.restore_session_check = QCheckBox("استعادة الجلسة السابقة")
        startup_layout.addWidget(self.restore_session_check)
        
        self.auto_save_check = QCheckBox("الحفظ التلقائي")
        startup_layout.addWidget(self.auto_save_check)
        
        layout.addWidget(startup_group)
        
        layout.addStretch()
        return widget
    
    def create_editor_tab(self):
        """Create editor settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Editor behavior group
        behavior_group = QGroupBox("سلوك المحرر")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.line_numbers_check = QCheckBox("إظهار أرقام الأسطر")
        behavior_layout.addWidget(self.line_numbers_check)
        
        self.word_wrap_check = QCheckBox("التفاف النص")
        behavior_layout.addWidget(self.word_wrap_check)
        
        self.auto_indent_check = QCheckBox("المسافة البادئة التلقائية")
        behavior_layout.addWidget(self.auto_indent_check)
        
        self.auto_complete_check = QCheckBox("الإكمال التلقائي")
        behavior_layout.addWidget(self.auto_complete_check)
        
        self.syntax_highlight_check = QCheckBox("تمييز الصيغة")
        behavior_layout.addWidget(self.syntax_highlight_check)
        
        layout.addWidget(behavior_group)
        
        # Tab settings group
        tab_group = QGroupBox("إعدادات التبويب")
        tab_layout = QVBoxLayout(tab_group)
        
        tab_size_layout = QHBoxLayout()
        tab_size_layout.addWidget(QLabel("حجم التبويب:"))
        self.tab_size_spin = QSpinBox()
        self.tab_size_spin.setRange(2, 8)
        self.tab_size_spin.setValue(4)
        tab_size_layout.addWidget(self.tab_size_spin)
        tab_size_layout.addStretch()
        tab_layout.addLayout(tab_size_layout)
        
        self.spaces_for_tabs_check = QCheckBox("استخدام المسافات بدلاً من التبويب")
        tab_layout.addWidget(self.spaces_for_tabs_check)
        
        layout.addWidget(tab_group)
        
        layout.addStretch()
        return widget
    
    def create_ai_tab(self):
        """Create AI settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # API settings group
        api_group = QGroupBox("إعدادات API")
        api_layout = QVBoxLayout(api_group)
        
        # Gemini API key
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("مفتاح Gemini API:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_layout.addWidget(self.api_key_edit)
        
        show_key_btn = QPushButton("إظهار")
        show_key_btn.setCheckable(True)
        show_key_btn.toggled.connect(self.toggle_api_key_visibility)
        api_key_layout.addWidget(show_key_btn)
        
        api_layout.addLayout(api_key_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("النموذج:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
            "gemini-2.0-flash"
        ])
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        api_layout.addLayout(model_layout)
        
        layout.addWidget(api_group)
        
        # AI behavior group
        behavior_group = QGroupBox("سلوك الذكاء الاصطناعي")
        behavior_layout = QVBoxLayout(behavior_group)
        
        # Response length
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("طول الاستجابة:"))
        self.response_length_combo = QComboBox()
        self.response_length_combo.addItems(["قصير", "متوسط", "طويل"])
        length_layout.addWidget(self.response_length_combo)
        length_layout.addStretch()
        behavior_layout.addLayout(length_layout)
        
        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("الإبداع (Temperature):"))
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(70)
        temp_layout.addWidget(self.temperature_slider)
        self.temp_value_label = QLabel("0.7")
        temp_layout.addWidget(self.temp_value_label)
        behavior_layout.addLayout(temp_layout)
        
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temp_value_label.setText(f"{v/100:.1f}")
        )
        
        # Auto suggestions
        self.auto_suggestions_check = QCheckBox("الاقتراحات التلقائية")
        behavior_layout.addWidget(self.auto_suggestions_check)
        
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        return widget
    
    def create_voice_tab(self):
        """Create voice settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Voice recognition group
        recognition_group = QGroupBox("التعرف على الصوت")
        recognition_layout = QVBoxLayout(recognition_group)
        
        # Language
        voice_lang_layout = QHBoxLayout()
        voice_lang_layout.addWidget(QLabel("لغة التعرف:"))
        self.voice_language_combo = QComboBox()
        self.voice_language_combo.addItems([
            "العربية (ar-SA)",
            "English (en-US)",
            "تلقائي"
        ])
        voice_lang_layout.addWidget(self.voice_language_combo)
        voice_lang_layout.addStretch()
        recognition_layout.addLayout(voice_lang_layout)
        
        # Sensitivity
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("الحساسية:"))
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(5)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        self.sensitivity_value_label = QLabel("5")
        sensitivity_layout.addWidget(self.sensitivity_value_label)
        recognition_layout.addLayout(sensitivity_layout)
        
        self.sensitivity_slider.valueChanged.connect(
            lambda v: self.sensitivity_value_label.setText(str(v))
        )
        
        # Timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("مهلة التسجيل (ثانية):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 60)
        self.timeout_spin.setValue(10)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        recognition_layout.addLayout(timeout_layout)
        
        layout.addWidget(recognition_group)
        
        # Voice commands group
        commands_group = QGroupBox("الأوامر الصوتية")
        commands_layout = QVBoxLayout(commands_group)
        
        self.voice_commands_check = QCheckBox("تفعيل الأوامر الصوتية")
        commands_layout.addWidget(self.voice_commands_check)
        
        self.continuous_listening_check = QCheckBox("الاستماع المستمر")
        commands_layout.addWidget(self.continuous_listening_check)
        
        # Wake word
        wake_word_layout = QHBoxLayout()
        wake_word_layout.addWidget(QLabel("كلمة التنشيط:"))
        self.wake_word_edit = QLineEdit()
        self.wake_word_edit.setPlaceholderText("مثال: يا وهيب")
        wake_word_layout.addWidget(self.wake_word_edit)
        commands_layout.addLayout(wake_word_layout)
        
        layout.addWidget(commands_group)
        
        layout.addStretch()
        return widget
    
    def toggle_api_key_visibility(self, visible):
        """Toggle API key visibility"""
        if visible:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
   
    def load_settings(self):
        """Load settings from config"""
        # General settings
        def str_to_bool(value):
            return str(value).strip().lower() == 'true'

        theme = self.config.get('ui.theme', 'dark')
        theme_index = {'dark': 0, 'light': 1, 'auto': 2}.get(theme, 0)
        self.theme_combo.setCurrentIndex(theme_index)
        
        self.font_size_spin.setValue(self.config.get('ui.font_size', 12))
        
        language = self.config.get('ui.language', 'ar')
        lang_index = {'ar': 0, 'en': 1}.get(language, 0)
        self.language_combo.setCurrentIndex(lang_index)
        
        
      
        self.restore_session_check.setChecked(str_to_bool(self.config.get('general.restore_session', True)))

        
        self.auto_save_check.setChecked(str_to_bool(self.config.get('files.auto_save', True)))

        # Editor settings
        self.line_numbers_check.setChecked(str_to_bool(self.config.get('editor.line_numbers', True)))
        self.word_wrap_check.setChecked(str_to_bool(self.config.get('editor.word_wrap', False)))
        self.auto_indent_check.setChecked(str_to_bool(self.config.get('editor.auto_indent', True)))
        self.auto_complete_check.setChecked(str_to_bool(self.config.get('editor.auto_complete', True)))
        self.syntax_highlight_check.setChecked(str_to_bool(self.config.get('editor.syntax_highlight', True)))
        self.tab_size_spin.setValue(self.config.get('editor.tab_size', 4))
        self.spaces_for_tabs_check.setChecked(str_to_bool(self.config.get('editor.spaces_for_tabs', True)))

        # AI settings
        self.api_key_edit.setText(self.config.get('ai.gemini_api_key', ''))
        self.model_combo.setCurrentText(self.config.get('ai.model', 'gemini-2.0-flash'))
        
        response_length = self.config.get('ai.response_length', 'medium')
        length_index = {'short': 0, 'medium': 1, 'long': 2}.get(response_length, 1)
        self.response_length_combo.setCurrentIndex(length_index)
        
       
        try:
    # تأكد من أن القيمة المحفوظة في ai.temperature هي float (مثل 0.7)
          temperature = float(self.config.get('ai.temperature', 0.7))
          self.temperature_slider.setValue(int(temperature * 100)) # اضبط شريط التمرير (مثلاً 0.7 * 100 = 70)
        except (ValueError, TypeError): # أضف TypeError
          logger.warning("Invalid temperature value in config, setting to default.")
          self.temperature_slider.setValue(70) # 0.7 * 100

        
        self.auto_suggestions_check.setChecked(str_to_bool(self.config.get('ai.auto_suggestions', True)))

        # Voice settings
        voice_lang = self.config.get('voice.language', 'ar-SA')
        voice_lang_index = {'ar-SA': 0, 'en-US': 1, 'auto': 2}.get(voice_lang, 0)
        self.voice_language_combo.setCurrentIndex(voice_lang_index)
        
        self.sensitivity_slider.setValue(self.config.get('voice.sensitivity', 5))
        self.timeout_spin.setValue(self.config.get('voice.timeout', 10))
        self.voice_commands_check.setChecked(str_to_bool(self.config.get('voice.commands_enabled', True)))

        self.continuous_listening_check.setChecked(str_to_bool(self.config.get('voice.continuous_listening', False)))
        self.wake_word_edit.setText(self.config.get('voice.wake_word', ''))
    
    def apply_settings(self):
        """Apply settings to config"""
        # General settings
        theme_map = {0: 'dark', 1: 'light', 2: 'auto'}
        self.config.set('ui.theme', theme_map[self.theme_combo.currentIndex()])
        self.config.set('ui.font_size', self.font_size_spin.value())
        
        lang_map = {0: 'ar', 1: 'en'}
        self.config.set('ui.language', lang_map[self.language_combo.currentIndex()])
        
        self.config.set('general.restore_session', self.restore_session_check.isChecked())
        self.config.set('files.auto_save', self.auto_save_check.isChecked())
        
        # Editor settings
        self.config.set('editor.line_numbers', self.line_numbers_check.isChecked())
        self.config.set('editor.word_wrap', self.word_wrap_check.isChecked())
        self.config.set('editor.auto_indent', self.auto_indent_check.isChecked())
        self.config.set('editor.auto_complete', self.auto_complete_check.isChecked())
        self.config.set('editor.syntax_highlight', self.syntax_highlight_check.isChecked())
        self.config.set('editor.tab_size', self.tab_size_spin.value())
        self.config.set('editor.spaces_for_tabs', self.spaces_for_tabs_check.isChecked())
        
        # AI settings
        self.config.set('ai.gemini_api_key', self.api_key_edit.text())
        self.config.set('ai.model', self.model_combo.currentText())
        
        length_map = {0: 'short', 1: 'medium', 2: 'long'}
        self.config.set('ai.response_length', length_map[self.response_length_combo.currentIndex()])
        
        temperature_value = self.temperature_slider.value() / 100
        self.config.set('ai.temperature', temperature_value)

        self.config.set('ai.auto_suggestions', self.auto_suggestions_check.isChecked())
        
        # Voice settings
        voice_lang_map = {0: 'ar-SA', 1: 'en-US', 2: 'auto'}
        self.config.set('voice.language', voice_lang_map[self.voice_language_combo.currentIndex()])
        self.config.set('voice.sensitivity', self.sensitivity_slider.value())
        self.config.set('voice.timeout', self.timeout_spin.value())
        self.config.set('voice.commands_enabled', self.voice_commands_check.isChecked())
        self.config.set('voice.continuous_listening', self.continuous_listening_check.isChecked())
        self.config.set('voice.wake_word', self.wake_word_edit.text())
        
        # Save config
        
        try:
            self.config.save()
            QMessageBox.information(self, "الإعدادات", "تم حفظ الإعدادات بنجاح")
            logger.info("Settings saved successfully.")
        except Exception as e:
            error_msg = f"فشل في حفظ الإعدادات: {e}"
            QMessageBox.critical(self, "خطأ في الحفظ", error_msg)
            logger.error(error_msg)

        QMessageBox.information(self, "الإعدادات", "تم حفظ الإعدادات بنجاح")
    
    def accept(self):
        """Accept dialog and apply settings"""
        self.apply_settings()
        super().accept()

