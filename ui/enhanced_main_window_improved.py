#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Main Window for AI Waheeb Pro Desktop Application
النافذة الرئيسية المحسنة لتطبيق AI Waheeb Pro
"""

from multiprocessing import Process
import os
import sys
import logging
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QTabWidget, QTextEdit,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QFrame,
    QMessageBox, QInputDialog, QProgressBar, QDockWidget,QApplication,  QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap, QKeySequence
from functools import partial # Import partial for recent files menu

# Import custom widgets
from .widgets.code_editor import CodeEditor
from .widgets.voice_control import VoiceControlWidget
from .widgets.file_tree import VSCodeFileTree
from .widgets.output_panel import OutputPanel
from .widgets.ai_assistant import AIAssistantWidget
from .widgets.settings_dialog import SettingsDialog
from .widgets.about_dialog import AboutDialog
from .widgets.collapsible_widget import CollapsibleDockWidget
from .widgets.dropdown_panel import DropdownPanel

# Import services
from core.unified_file_manager import UnifiedFileManager # Using the original name
from core.voice_service import VoiceService # Assuming VoiceService exists and is functional

logger = logging.getLogger(__name__)

class EnhancedMainWindow(QMainWindow):
    """Enhanced main application window with improved UI"""
    
    # Signals
    file_content_changed = pyqtSignal(str, str)  # file_path, content
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config, gemini_service):
        super().__init__()
        try:

          logger.info("EnhancedMainWindow: Initializing main window.")
        
          screen = QApplication.primaryScreen()
          size = screen.availableGeometry()
          self._is_applying_ai_response = False 
          self.setMinimumSize(1200, 800)
          self.resize(1200, 800)
          self.center_window()
          self.setWindowTitle("AI cyber Pro - مساعد البرمجة الذكي المتقدم")
          self.config = config
          self.gemini_service = gemini_service

        # Initialize services
          self.file_manager = gemini_service.file_manager
          self.voice_service = VoiceService(config) # Assuming VoiceService is properly defined

        # UI components
          self.central_widget = None
          self.code_editor = None
          self.voice_control = None
          self.file_tree = None
          self.output_panel = None
          self.ai_assistant = None
          self.status_bar = None
          self.progress_bar = None
          self.status_label = None
          self.connection_label = None
          self.file_info_label = None
          self.dropdown_panel = None  # New dropdown panel

        # State
          self.current_file = None
          self.open_tabs = {}
          self.tab_widget = None

        # Auto-save timer
          self.autosave_timer = QTimer(self)
          self.autosave_timer.timeout.connect(self.autosave_files)
          self.autosave_timer.start(5 * 60 * 1000) # Auto-save every 5 minutes

        # Initialize UI components
          self.create_menu_bar()
          self.create_tool_bars()
          self.create_dropdown_panel()  # New dropdown panel
          self.create_status_bar()
          self.create_dock_widgets()
          self.create_central_widget()

          self.setCentralWidget(self.central_widget)

          self.setup_connections()
          self.restore_window_state()
          self.start_services()
          self.apply_theme()
        
          last_folder = self.config.get_recent_folders() # افترض أن لديك دالة كهذه في config
          if last_folder:
            last_folder_path = last_folder[0] # خذ آخر مجلد تم فتحه
            if os.path.isdir(last_folder_path):
                logger.info(f"EnhancedMainWindow: Loading last opened folder: {last_folder_path}")
                # استدعاء الدالة مباشرة عبر مدير الملفات لتشغيل الإشارة
                self.file_manager.open_folder(last_folder_path)
          logger.info("EnhancedMainWindow: Main window initialized successfully.")
          
        except Exception as e:
             logger.critical(f"Unhandled exception during EnhancedMainWindow initialization: {e}", exc_info=True)
             QMessageBox.critical(self, "خطأ فادح", f"حدث خطأ غير متوقع أثناء بدء التشغيل: {e}\nالرجاء مراجعة السجلات.")
             sys.exit(1) # إغلاق التطبيق بعد عرض الخطأ
    def create_dropdown_panel(self):
        """Create dropdown panel for voice control and AI assistant"""
        self.dropdown_panel = DropdownPanel(self)
        
        # Create a dock widget for the dropdown panel
        self.dropdown_dock = QDockWidget("", self)
        self.dropdown_dock.setWidget(self.dropdown_panel)
        self.dropdown_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.dropdown_dock.setTitleBarWidget(QWidget())  # Hide title bar
        
        # Add to top of the window
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.dropdown_dock)
        
        # Connect signals
        self.dropdown_panel.voice_control_requested.connect(self.show_voice_control_dock)
        self.dropdown_panel.ai_assistant_requested.connect(self.show_ai_assistant_dock)
        self.dropdown_panel.voice_toggle_requested.connect(self.toggle_voice_control)
        logger.info("EnhancedMainWindow: Dropdown panel created.")
    
    def show_voice_control_dock(self):
        """Show voice control dock widget"""
        if hasattr(self, 'voice_dock'):
            self.voice_dock.setVisible(True)
            self.voice_dock.raise_()
            logger.info("EnhancedMainWindow: Voice control dock shown.")
    
    def show_ai_assistant_dock(self):
        """Show AI assistant dock widget"""
        if hasattr(self, 'ai_dock'):
            self.ai_dock.setVisible(True)
            self.ai_dock.raise_()
            logger.info("EnhancedMainWindow: AI assistant dock shown.")
    
    def handle_ai_action(self, action):
        """Handle AI action from dropdown"""
        logger.info(f"EnhancedMainWindow: Handling AI action: {action}")
        if action == "شرح الكود المحدد":
            self.explain_code()
        elif action == "تحسين الكود":
            self.optimize_code()
        elif action == "تصحيح الأخطاء":
            self.debug_code()
        elif action == "إنشاء كود جديد":
            self.create_new_code()
    
    def create_new_code(self):
        """Create new code with AI assistance"""
        text, ok = QInputDialog.getText(self, 'إنشاء كود جديد', 'صف الكود الذي تريد إنشاءه:')
        if ok and text:
            logger.info(f"EnhancedMainWindow: Requesting AI to generate code: {text[:50]}...")
            # Assuming gemini_service has a method to generate code based on a description
            # This might map to process_general_query or a specific generate_code method
            self.gemini_service.process_general_query(f"أنشئ كود بايثون لـ: {text}")
            self.update_status("جاري إنشاء الكود...")
    
    
    def autosave_files(self):
        """Auto-save all modified open files"""
        logger.info("EnhancedMainWindow: Initiating auto-save.")
        for file_path, tab_index in self.open_tabs.items():
            editor = self.tab_widget.widget(tab_index)
            if isinstance(editor, CodeEditor):
                # Check if file is modified according to file_manager's internal state
                if self.file_manager.is_file_modified(file_path):
                    content = editor.toPlainText() # Get current content from editor
                    self.file_manager.save_file(file_path, content)
                    self.output_panel.add_program_output(f"📁 تم حفظ {os.path.basename(file_path)} تلقائيًا")
                    logger.info(f"EnhancedMainWindow: Auto-saved: {file_path}")
        self.update_status("✅ تم تنفيذ الحفظ التلقائي")
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("ملف")
        
        # New file
        new_action = QAction("ملف جديد", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        # Open file
        open_action = QAction("فتح ملف", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Open folder
        open_folder_action = QAction("فتح مجلد", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # Save
        save_action = QAction("حفظ", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # Save as
        save_as_action = QAction("حفظ باسم", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Recent files
        recent_menu = file_menu.addMenu("الملفات الأخيرة")
        self.update_recent_files_menu(recent_menu)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("خروج", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("عرض")
        
        # Toggle panels
        toggle_dropdown = QAction("شريط القوائم المنسدلة", self)
        toggle_dropdown.setCheckable(True)
        toggle_dropdown.setChecked(True)
        toggle_dropdown.triggered.connect(lambda checked: self.dropdown_dock.setVisible(checked))
        view_menu.addAction(toggle_dropdown)
        
        toggle_file_tree = QAction("شجرة الملفات", self)
        toggle_file_tree.setCheckable(True)
        toggle_file_tree.setChecked(True)
        toggle_file_tree.triggered.connect(lambda checked: self.file_tree_dock.setVisible(checked))
        view_menu.addAction(toggle_file_tree)
        
        toggle_output = QAction("لوحة الإخراج", self)
        toggle_output.setCheckable(True)
        toggle_output.setChecked(True)
        toggle_output.triggered.connect(lambda checked: self.output_dock.setVisible(checked))
        view_menu.addAction(toggle_output)
        
        toggle_ai_assistant = QAction("المساعد الذكي", self)
        toggle_ai_assistant.setCheckable(True)
        toggle_ai_assistant.setChecked(True)
        toggle_ai_assistant.triggered.connect(lambda checked: self.ai_dock.setVisible(checked))
        view_menu.addAction(toggle_ai_assistant)
        
        toggle_voice_control = QAction("التحكم الصوتي", self)
        toggle_voice_control.setCheckable(True)
        toggle_voice_control.setChecked(True)
        toggle_voice_control.triggered.connect(lambda checked: self.voice_dock.setVisible(checked))
        view_menu.addAction(toggle_voice_control)
        
        # Tools menu with backup buttons
        tools_menu = menubar.addMenu("أدوات")
        
        # Backup voice control button
        voice_backup_action = QAction("🎤 التحكم الصوتي", self)
        voice_backup_action.triggered.connect(self.show_voice_control_dock)
        tools_menu.addAction(voice_backup_action)
        
        # Backup AI assistant button
        ai_backup_action = QAction("🤖 المساعد الذكي", self)
        ai_backup_action.triggered.connect(self.show_ai_assistant_dock)
        tools_menu.addAction(ai_backup_action)
        
        tools_menu.addSeparator()
        
        # Settings
        settings_action = QAction("الإعدادات", self)
        settings_action.setShortcut(QKeySequence.StandardKey.Preferences)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu("مساعدة")
        
        # About
        about_action = QAction("حول البرنامج", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        logger.info("EnhancedMainWindow: Menu bar created.")
    
    def create_tool_bars(self):
        """Create tool bars with enhanced functionality"""
        # Main toolbar
        main_toolbar = self.addToolBar("الأدوات الرئيسية")
        main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # File operations
        new_btn = QPushButton("جديد")
        new_btn.clicked.connect(self.new_file)
        main_toolbar.addWidget(new_btn)
        
        open_btn = QPushButton("فتح")
        open_btn.clicked.connect(self.open_file)
        main_toolbar.addWidget(open_btn)
        
        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self.save_file)
        main_toolbar.addWidget(save_btn)
        
        main_toolbar.addSeparator()
        
        # Run button
        run_btn = QPushButton("تشغيل")
        run_btn.clicked.connect(self.run_current_file)
        run_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        main_toolbar.addWidget(run_btn)
        
        main_toolbar.addSeparator()
        terminal_btn = QPushButton("💻 الترمنال")
        terminal_btn.clicked.connect(lambda: self.output_panel.show_tab("terminal"))
        terminal_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E293B;
            }
            QPushButton:pressed {
                background-color: #0F172A;
            }
        """)
        main_toolbar.addWidget(terminal_btn)
        
        main_toolbar.addSeparator()
        # Backup buttons for voice control and AI assistant
        voice_backup_btn = QPushButton("🎤 صوت")
        voice_backup_btn.setCheckable(True)
        voice_backup_btn.clicked.connect(self.toggle_voice_control)
        voice_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
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
        main_toolbar.addWidget(voice_backup_btn)
        self.voice_backup_btn = voice_backup_btn
        
        ai_backup_btn = QPushButton("🤖 مساعد")
        ai_backup_btn.clicked.connect(self.show_ai_assistant_dock)
        ai_backup_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        main_toolbar.addWidget(ai_backup_btn)
        logger.info("EnhancedMainWindow: Toolbars created.")
    
    def create_central_widget(self):
        """Create central widget with code editor"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget for multiple files
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        
        layout.addWidget(self.tab_widget)
        
        # Create welcome tab
        self.create_welcome_tab()
        logger.info("EnhancedMainWindow: Central widget and tab widget created.")
    
    
    def on_folder_changed(self, folder_path: str):
        """
        Slot to handle when the project folder is opened.
        Updates the file tree with the new root path.
        """
        logger.info(f"EnhancedMainWindow: Received folder opened signal for: {folder_path}")
        if self.file_tree and os.path.isdir(folder_path):
            
            self.file_tree.set_root_path(folder_path)
            
            self.output_panel.add_program_output(f"📂 تم فتح المجلد: {folder_path}")
            self.update_status(f"تم تحميل المشروع: {os.path.basename(folder_path)}")
        else:
            logger.warning("File tree not available or path is not a directory.")
    def create_welcome_tab(self):
        """Create welcome tab"""
        welcome_widget = QWidget()
        layout = QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo and title
        title_label = QLabel("AI Waheeb Pro")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #2563EB;
                margin: 20px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("مساعد البرمجة الذكي المتقدم")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #6B7280;
                margin-bottom: 40px;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Quick actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # New file button
        new_file_btn = QPushButton("إنشاء ملف جديد")
        new_file_btn.clicked.connect(self.new_file)
        new_file_btn.setStyleSheet(self.get_button_style())
        actions_layout.addWidget(new_file_btn)
        
        # Open file button
        open_file_btn = QPushButton("فتح ملف")
        open_file_btn.clicked.connect(self.open_file)
        open_file_btn.setStyleSheet(self.get_button_style())
        actions_layout.addWidget(open_file_btn)
        
        # Open folder button
        open_folder_btn = QPushButton("فتح مجلد")
        open_folder_btn.clicked.connect(self.open_folder)
        open_folder_btn.setStyleSheet(self.get_button_style())
        actions_layout.addWidget(open_folder_btn)
        
        layout.addWidget(actions_widget)
        
        # Recent files
        recent_label = QLabel("الملفات الأخيرة:")
        recent_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(recent_label)
        
        recent_files = self.file_manager.get_recent_files()[:5]
        for file_path in recent_files:
            file_btn = QPushButton(os.path.basename(file_path))
            file_btn.clicked.connect(lambda checked, path=file_path: self.open_file(path))
            file_btn.setStyleSheet("text-align: left; padding: 5px;")
            layout.addWidget(file_btn)
        
        self.tab_widget.addTab(welcome_widget, "مرحباً")
        logger.info("EnhancedMainWindow: Welcome tab created.")
    
    def create_dock_widgets(self):
        """Create dock widgets"""
        # File tree dock
        self.file_tree_dock = QDockWidget("شجرة الملفات", self)
   
        self.file_tree = VSCodeFileTree(self)
        self.file_tree.set_file_manager(self.file_manager)
        self.file_tree_dock.setWidget(self.file_tree) 
       
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.file_tree_dock)
        logger.info("EnhancedMainWindow: File tree dock created.")
        
        # AI Assistant dock with collapsible widget
        self.ai_dock = QDockWidget("المساعد الذكي", self)
        self.ai_assistant = AIAssistantWidget(self.gemini_service)
        self.ai_collapsible = CollapsibleDockWidget("المساعد الذكي", self.ai_assistant)
        self.ai_dock.setWidget(self.ai_collapsible)
        self.ai_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_dock)
        logger.info("EnhancedMainWindow: AI Assistant dock created.")
        
        # Voice control dock with collapsible widget
        self.voice_dock = QDockWidget("التحكم الصوتي", self)
        self.voice_control = VoiceControlWidget(self.voice_service, self.gemini_service)
        self.voice_collapsible = CollapsibleDockWidget("التحكم الصوتي", self.voice_control)
        self.voice_dock.setWidget(self.voice_collapsible)
        self.voice_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.voice_dock)
        logger.info("EnhancedMainWindow: Voice control dock created.")
        
        # Output panel dock
        self.output_dock = QDockWidget("لوحة الإخراج", self)
        self.output_panel = OutputPanel()
        self.output_dock.setWidget(self.output_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)
        logger.info("EnhancedMainWindow: Output panel dock created.")
        
        # Tabify right docks
        self.tabifyDockWidget(self.ai_dock, self.voice_dock)
        self.ai_dock.raise_()
        logger.info("EnhancedMainWindow: Docks tabified.")
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        
        # Status label
        self.status_label = QLabel("جاهز")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Connection status
        self.connection_label = QLabel("غير متصل")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # File info
        self.file_info_label = QLabel("")
        self.status_bar.addPermanentWidget(self.file_info_label)
        logger.info("EnhancedMainWindow: Status bar created.")
    
    def setup_connections(self):
        """Setup signal connections"""
        logger.info("EnhancedMainWindow: Setting up all service connections.")
        # File manager connections
        self.file_manager.file_opened.connect(self.on_file_opened)
        self.file_manager.file_saved.connect(self.on_file_saved)
        self.file_manager.error_occurred.connect(self.show_error)
        self.file_manager.file_output_ready.connect(self.output_panel.add_program_output)
        self.file_manager.folder_opened.connect(self.on_folder_changed)
        self.file_manager.file_output_ready.connect(self.output_panel.add_program_output) 
        
        # Connect folder_opened to set terminal's working directory
        self.file_manager.folder_opened.connect(self.output_panel.set_terminal_working_directory)

        logger.info("EnhancedMainWindow: File manager connections established.")
        
        # Voice service connections
        self.voice_service.text_recognized.connect(self.on_voice_recognized)
        self.voice_service.error_occurred.connect(self.show_error)
        self.voice_service.listening_started.connect(self.on_voice_started)
        self.voice_service.listening_stopped.connect(self.on_voice_stopped)
        logger.info("EnhancedMainWindow: Voice service connections established.")
        
        # Gemini service connections
        self.gemini_service.response_ready.connect(self.output_panel.add_ai_response_display) # For general AI responses, if desired
        self.gemini_service.response_ready.connect(self.on_ai_response)
        self.gemini_service.error_occurred.connect(self.show_error)
        self.gemini_service.progress_updated.connect(self.update_status)
        self.gemini_service.connection_status_changed.connect(self.on_connection_changed)
        logger.info("EnhancedMainWindow: Gemini service connections established.")
     
        # File tree connections
        if self.file_tree:
            self.file_tree.file_selected.connect(self.open_file)
            logger.info("EnhancedMainWindow: File tree connections established.")
        
        # AI Assistant connections - Fix the text sending issue
        if self.ai_assistant:
            self.ai_assistant.command_requested.connect(self.process_ai_command)
            logger.info("EnhancedMainWindow: AI Assistant connections established.")
        
        # Voice Control Widget's voice_command_ready signal to Gemini service
        # This is the crucial connection for voice commands to reach the AI processor
        if self.voice_control:
            self.voice_control.voice_command_ready.connect(self.gemini_service.process_general_query)
            logger.info("EnhancedMainWindow: VoiceControlWidget command_ready connected to gemini_service.process_general_query.")

        logger.info("EnhancedMainWindow: All connections setup complete.")
    
    
  # In EnhancedMainWindow.process_ai_command
    def process_ai_command(self, command):
        logger.info(f"EnhancedMainWindow: Processing AI command from assistant: '{command[:50]}...'")
        if self._is_applying_ai_response:
            logger.warning("EnhancedMainWindow: Ignoring new AI command as AI response is currently being applied.")
            self.update_status("جاري تطبيق استجابة AI سابقة. تم تجاهل الأمر الجديد.")
            return
        current_editor = self.get_current_editor()
        context = current_editor.toPlainText() if current_editor else ""
        file_path = self.current_file if self.current_file else ""

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor) # Set busy cursor
        try:
          self.gemini_service.process_user_input(
             user_input=command,
            current_code=context,
            file_path=file_path,
            project_files=self.file_manager.get_all_project_files()
         )
          
          self.update_status(f"جاري معالجة: {command[:50]}...")
          
          self.output_panel.add_ai_response_display(f"💬 سؤال: {command}")
        except Exception as e:
           logger.error(f"Error in process_ai_command: {e}", exc_info=True)
           self.show_error(f"حدث خطأ أثناء معالجة الأمر: {e}")
        finally:
          QApplication.restoreOverrideCursor() # Restore cursor          
    def start_services(self):
        """Start background services"""
        logger.info("EnhancedMainWindow: Starting services.")
        # Update connection status
        self.on_connection_changed(self.gemini_service.is_available())
        
        # Update status
        self.update_status("جاهز للاستخدام")
        logger.info("EnhancedMainWindow: Services started.")
    
    def apply_theme(self):
        """Apply dark theme"""
        logger.info("EnhancedMainWindow: Applying theme.")
        theme = self.config.get('ui.theme', 'dark')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #0A0A0B;
                    color: #F8FAFC;
                }
                QMenuBar {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border-bottom: 1px solid #334155;
                }
                QMenuBar::item {
                    background-color: transparent;
                    padding: 8px 12px;
                }
                QMenuBar::item:selected {
                    background-color: #2563EB;
                }
                QMenu {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border: 1px solid #334155;
                }
                QMenu::item {
                    padding: 8px 20px;
                }
                QMenu::item:selected {
                    background-color: #2563EB;
                }
                QToolBar {
                    background-color: #1E293B;
                    border: none;
                    spacing: 4px;
                    padding: 4px;
                }
                QTabWidget::pane {
                    border: 1px solid #334155;
                    background-color: #0F172A;
                }
                QTabBar::tab {
                    background-color: #1E293B;
                    color: #94A3B8;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    min-width: 80px;
                }
                QTabBar::tab:selected {
                    background-color: #0F172A;
                    color: #F8FAFC;
                }
                QTabBar::tab:hover {
                    background-color: #334155;
                }
                QDockWidget {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border: 1px solid #334155;
                    border-radius: 6px;
                }
                QDockWidget::title {
                    background-color: #334155;
                    padding: 8px;
                    text-align: center;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    font-weight: bold;
                }
                QStatusBar {
                    background-color: #1E293B;
                    color: #94A3B8;
                    border-top: 1px solid #334155;
                    padding: 4px;
                }
            """
            )
        logger.info("EnhancedMainWindow: Theme applied.")
    
    def get_button_style(self) -> str:
        """Get button style"""
        return """
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                margin: 4px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
        """
    
    # File operations
    def new_file(self):
        """Create new file"""
        logger.info("EnhancedMainWindow: Creating new file.")
        file_path = self.file_manager.create_new_file()
        if file_path:
            self.add_editor_tab(file_path, "")
            logger.info(f"EnhancedMainWindow: New file created: {file_path}")
    
    def open_file(self, file_path: str = None):
        """Open file"""
        logger.info(f"EnhancedMainWindow: Opening file: {file_path}")
        if not file_path:
            file_path = self.file_manager.open_file()
        else:
            file_path = self.file_manager.open_file(file_path)
        
        if file_path and file_path not in self.open_tabs:
            # File will be opened via signal (on_file_opened)
            logger.info(f"EnhancedMainWindow: File open request sent to file manager: {file_path}")
            pass
        elif file_path and file_path in self.open_tabs:
            self.tab_widget.setCurrentIndex(self.open_tabs[file_path])
            logger.info(f"EnhancedMainWindow: Switched to already open file: {file_path}")
    
    def save_file(self):
        """Save current file"""
        logger.info("EnhancedMainWindow: Saving current file.")
        current_editor = self.get_current_editor()
        if current_editor and self.current_file:
            content = current_editor.toPlainText()
            self.file_manager.save_file(self.current_file, content)
            logger.info(f"EnhancedMainWindow: File save request sent for: {self.current_file}")
        else:
            logger.warning("EnhancedMainWindow: No current file or editor to save.")
            self.show_error("لا يوجد ملف حالي للحفظ.")
    
    def save_file_as(self):
        """Save file as"""
        logger.info("EnhancedMainWindow: Saving file as...")
        current_editor = self.get_current_editor()
        if current_editor:
            content = current_editor.toPlainText()
            new_path = self.file_manager.save_file_as(self.current_file, content)
            if new_path:
                self.current_file = new_path
                self.update_tab_title()
                logger.info(f"EnhancedMainWindow: File saved as: {new_path}")
        else:
            logger.warning("EnhancedMainWindow: No editor content to save as.")
            self.show_error("لا يوجد محتوى للحفظ باسم.")
    
    
    def open_folder(self):
        """
        يطلب من مدير الملفات فتح مجلد.
        مدير الملفات (UnifiedFileManager) هو المسؤول عن عرض مربع الحوار.
        """
        logger.info("EnhancedMainWindow: Opening folder.")
      
        success = self.file_manager.open_folder() 
        
        if not success:
            logger.warning("EnhancedMainWindow: عملية فتح المجلد لم تكن ناجحة أو تم إلغاؤها.")
            self.update_status("فتح المجلد ألغي أو فشل.")
    
    def run_current_file(self):
        """Run current file"""
        logger.info("EnhancedMainWindow: Attempting to run current file.")
        if self.current_file:
            self.update_status(f"جاري تشغيل {os.path.basename(self.current_file)}...")
            success = self.file_manager.run_file(self.current_file)
            if success:
                
                self.output_panel.add_program_output(f"✅ تم تشغيل {os.path.basename(self.current_file)}")
                self.update_status("تم التشغيل بنجاح")
                logger.info(f"EnhancedMainWindow: Successfully ran file: {self.current_file}")
            else:
                self.update_status("فشل في التشغيل")
                logger.error(f"EnhancedMainWindow: Failed to run file: {self.current_file}")
        else:
            logger.warning("EnhancedMainWindow: No current file to run.")
            self.show_error("لا يوجد ملف حالي للتشغيل.")
    
    # AI operations
    def explain_code(self):
        """Explain current code"""
        logger.info("EnhancedMainWindow: Requesting AI to explain code.")
        current_editor = self.get_current_editor()
        if current_editor:
            selected_text = current_editor.textCursor().selectedText()
            code = selected_text if selected_text else current_editor.toPlainText()
            
            if code.strip():
                # Use process_user_input to send context
                self.gemini_service.process_user_input(
                    user_input="اشرح هذا الكود بالتفصيل:",
                    current_code=code,
                    file_path=self.current_file
                )
                self.update_status("جاري شرح الكود...")
                logger.info("EnhancedMainWindow: Sent explain code request to Gemini service.")
            else:
                logger.warning("EnhancedMainWindow: No code to explain.")
                self.show_error("لا يوجد كود لشرحه.")
        else:
            logger.warning("EnhancedMainWindow: No active editor for code explanation.")
            self.show_error("لا يوجد محرر كود نشط لشرحه.")
    
    def optimize_code(self):
        """Optimize current code"""
        logger.info("EnhancedMainWindow: Requesting AI to optimize code.")
        current_editor = self.get_current_editor()
        if current_editor:
            code = current_editor.toPlainText()
            if code.strip():
                # Use process_user_input to send context
                self.gemini_service.process_user_input(
                    user_input="حسن هذا الكود لجعله أكثر كفاءة:",
                    current_code=code,
                    file_path=self.current_file
                )
                self.update_status("جاري تحسين الكود...")
                logger.info("EnhancedMainWindow: Sent optimize code request to Gemini service.")
            else:
                logger.warning("EnhancedMainWindow: No code to optimize.")
                self.show_error("لا يوجد كود لتحسينه.")
        else:
            logger.warning("EnhancedMainWindow: No active editor for code optimization.")
            self.show_error("لا يوجد محرر كود نشط لتحسينه.")
    
    def debug_code(self):
        """Debug current code"""
        logger.info("EnhancedMainWindow: Requesting AI to debug code.")
        current_editor = self.get_current_editor()
        if current_editor:
            code = current_editor.toPlainText()
            if code.strip():
                # Use process_user_input to send context
                self.gemini_service.process_user_input(
                    user_input="ابحث عن الأخطاء المحتملة في هذا الكود واقترح حلولاً:",
                    current_code=code,
                    file_path=self.current_file
                )
                self.update_status("جاري تصحيح الأخطاء...")
                logger.info("EnhancedMainWindow: Sent debug code request to Gemini service.")
            else:
                logger.warning("EnhancedMainWindow: No code to debug.")
                self.show_error("لا يوجد كود لتصحيحه.")
        else:
            logger.warning("EnhancedMainWindow: No active editor for code debugging.")
            self.show_error("لا يوجد محرر كود نشط لتصحيحه.")
    
    # Voice control
    def toggle_voice_control(self):
        """Toggle voice control"""
        logger.info("EnhancedMainWindow: Toggling voice control.")
        if self.voice_service.is_listening:
            self.voice_service.stop_listening()
            logger.info("EnhancedMainWindow: Voice service stopped listening.")
        else:
            self.voice_service.start_listening()
            logger.info("EnhancedMainWindow: Voice service started listening.")
    
    # Tab management
    def add_editor_tab(self, file_path: str, content: str):
        """Add new editor tab"""
        logger.info(f"EnhancedMainWindow: Adding editor tab for: {file_path}")
        if file_path in self.open_tabs:
            # Switch to existing tab
            self.tab_widget.setCurrentIndex(self.open_tabs[file_path])
            logger.info(f"EnhancedMainWindow: Switched to existing tab for: {file_path}")
            return
        
        # Create new code editor
        editor = CodeEditor()
        editor.setPlainText(content)
        # Connect textChanged to update tab title with '*' for unsaved changes
        editor.textChanged.connect(lambda: self.on_editor_changed(file_path)) 
        
        # Add tab
        file_name = os.path.basename(file_path) if file_path else "بدون عنوان"
        tab_index = self.tab_widget.addTab(editor, file_name)
        self.open_tabs[file_path] = tab_index
        
        # Switch to new tab
        self.tab_widget.setCurrentIndex(tab_index)
        self.current_file = file_path
        
        # Update file info in status bar
        self.update_file_info()
        logger.info(f"EnhancedMainWindow: Editor tab added for {file_path} at index {tab_index}.")
    
    def close_tab(self, index: int):
        """Close tab"""
        logger.info(f"EnhancedMainWindow: Closing tab at index: {index}")
        widget = self.tab_widget.widget(index)
        if widget:
            # Find file path associated with the tab
            file_path = None
            for path, tab_index in self.open_tabs.items():
                if tab_index == index:
                    file_path = path
                    break
            
            # Remove from open tabs dictionary
            if file_path:
                del self.open_tabs[file_path]
                self.file_manager.close_file(file_path) # Notify file manager
                logger.info(f"EnhancedMainWindow: Closed file: {file_path}")
            
            # Remove tab from QTabWidget
            self.tab_widget.removeTab(index)
            
            # Update indices of remaining tabs in open_tabs dictionary
            for path in self.open_tabs:
                if self.open_tabs[path] > index:
                    self.open_tabs[path] -= 1
            
            # Update current file if the closed tab was active
            if self.tab_widget.count() > 0:
                self.tab_changed(self.tab_widget.currentIndex())
            else:
                self.current_file = None
                self.update_file_info()
            logger.info(f"EnhancedMainWindow: Tab at index {index} closed.")
    
    def tab_changed(self, index: int):
        """Handle tab change"""
        logger.info(f"EnhancedMainWindow: Tab changed to index: {index}")
        if index >= 0:
         
            for file_path, tab_index in self.open_tabs.items():
                if tab_index == index:
                    self.current_file = file_path
                    break
            else:
                self.current_file = None 
            
            self.update_file_info()
            
            current_editor = self.get_current_editor()
            if current_editor:
                self.gemini_service.set_context(current_editor.toPlainText(), self.current_file)
            else:
                self.gemini_service.set_context("", "") 
            logger.info(f"EnhancedMainWindow: Current file set to: {self.current_file}")
    
   
    def get_current_editor(self, _=None) -> Optional[CodeEditor]: 
        """الحصول على محرر الكود الحالي."""
        current_widget = self.tab_widget.currentWidget()
        
        if isinstance(current_widget, CodeEditor):
            return current_widget
        return None
    def update_tab_title(self):
        """Update current tab title"""
        if self.current_file:
            file_name = os.path.basename(self.current_file)
            current_index = self.tab_widget.currentIndex()
            self.tab_widget.setTabText(current_index, file_name)
            logger.debug(f"EnhancedMainWindow: Tab title updated to: {file_name}")
    
  
    def on_file_opened(self, file_path: str, content: str):
        """Handle file opened"""
        logger.info(f"EnhancedMainWindow: Received file opened signal for: {file_path}")
        self.add_editor_tab(file_path, content)
        self.update_status(f"تم فتح {os.path.basename(file_path)}")
    
    def on_file_saved(self, file_path: str):
        """Handle file saved"""
        logger.info(f"EnhancedMainWindow: Received file saved signal for: {file_path}")
        self.update_status(f"تم حفظ {os.path.basename(file_path)}")
        index = self.open_tabs.get(file_path)
        if index is not None:
            title = self.tab_widget.tabText(index)
            if title.endswith("*"):
                self.tab_widget.setTabText(index, title.rstrip("*"))
       
        current_editor = self.get_current_editor()
        if current_editor and self.current_file == file_path:
            
            self.file_manager.mark_file_modified(file_path, current_editor.toPlainText(), modified=False) 
            logger.info(f"EnhancedMainWindow: File {file_path} marked as saved in UI and internal state.")
        else:
            
            logger.info(f"EnhancedMainWindow: File {file_path} marked as saved in UI, but editor state not updated internally (might be closed or not active).")
   
    def on_editor_changed(self, file_path: str):
        """Handle editor content changed"""
        current_editor = self.get_current_editor()
        if current_editor and self.current_file == file_path:
            content = current_editor.toPlainText()
            self.file_content_changed.emit(file_path, content)

          
            self.file_manager.mark_file_modified(file_path, content) 

            index = self.open_tabs.get(file_path)
            if index is not None:
                title = self.tab_widget.tabText(index)
                if not title.endswith("*"):
                    self.tab_widget.setTabText(index, f"{title}*")
    def on_voice_recognized(self, text: str):
        """Handle voice recognition"""
        logger.info(f"EnhancedMainWindow: Voice recognized: '{text}'")
        if self.voice_control:
            self.voice_control.set_recognized_text(text)
        
    
        if self.dropdown_panel:
            self.dropdown_panel.update_ai_status("جاري معالجة الأمر الصوتي...")
        
        self.update_status("تم التعرف على الأمر الصوتي، جاري المعالجة...")
    
    def on_voice_started(self):
        """Handle voice listening started"""
        logger.info("EnhancedMainWindow: Voice listening started.")
        if hasattr(self, 'voice_backup_btn'):
            self.voice_backup_btn.setChecked(True)
            self.voice_backup_btn.setText("🔴 جاري الاستماع...")
        
        if self.dropdown_panel:
            self.dropdown_panel.update_voice_status(True)
        
        self.update_status("جاري الاستماع للأوامر الصوتية...")
    
    def on_voice_stopped(self):
        """Handle voice listening stopped"""
        logger.info("EnhancedMainWindow: Voice listening stopped.")
        if hasattr(self, 'voice_backup_btn'):
            self.voice_backup_btn.setChecked(False)
            self.voice_backup_btn.setText("🎤 صوت")
        
        if self.dropdown_panel:
            self.dropdown_panel.update_voice_status(False)
        
        self.update_status("تم إيقاف الاستماع")
    
    
    def on_ai_response(self, response: Dict[str, Any]):
        """Handle AI response with improved routing"""
        logger.info(f"EnhancedMainWindow: Received AI response. Action: {response.get('action')}")
        current_editor = self.get_current_editor()
        
        action = response.get('action', '')
        content = response.get('content', '')
        description = response.get('explanation', 'تم تنفيذ العملية')
        
        if self.ai_assistant:
            self.ai_assistant.add_message("المساعد الذكي", content, is_user=False)
            logger.info(f"EnhancedMainWindow: AI response sent to AI Assistant widget.")

        self.output_panel.add_ai_response_display(content)
        self._is_applying_ai_response = True 
        
        logger.info(f"EnhancedMainWindow: AI response sent to AI Assistant widget and OutputPanel's AI Response tab.")

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor) 

        try:
          
            if action in ['add_code', 'replace_code', 'optimize_code', 'add_comment']:
                if current_editor and self.current_file:
                    reply_message = "الذكاء الاصطناعي اقترح تحديث الكود. هل تريد تحديث المحرر الحالي؟"
                    if action == 'add_comment':
                        reply_message = "الذكاء الاصطناعي اقترح إضافة تعليقات إلى الكود. هل تريد تحديث المحرر الحالي؟"
                    elif action == 'optimize_code':
                        reply_message = "الذكاء الاصطلاعي اقترح تحسين الكود. هل تريد تحديث المحرر الحالي؟"
                    
                    dialog_title = "تحديث الكود"
                    full_message = f"{reply_message}\n\nملحوظة: هذا سيكتب فوق المحتوى الحالي أو يضيف إليه. \n\n {content[:1000]}..."
                    
                    reply = QMessageBox.question(
                        self, dialog_title, full_message,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        current_editor.setPlainText(content)
                        
                        self.file_manager.mark_file_modified(self.current_file, content) 
                        
                        self.output_panel.add_ai_response_display(description)
                        self.update_status("الكود محدث في المحرر.")
                        logger.info(f"EnhancedMainWindow: Code applied to current editor for action: {action}.")
                    else:
                        self.output_panel.add_program_output(f"ℹ️ تم رفض تحديث الكود من قبل المستخدم.")
                        self.update_status("تحديث الكود مرفوض.")
                        logger.info("EnhancedMainWindow: User rejected code update.")
                else:
                    self.output_panel.add_program_output(f"❌ لا يوجد محرر نشط لتطبيق التغييرات. المحتوى المقترح:\n{content}")
                    self.show_error(f"لا يوجد محرر كود نشط لتطبيق التغييرات.")
                    logger.error(f"EnhancedMainWindow: No active editor for code modification action: {action}.")
            
            elif action == 'create_file':
                file_name = response.get('file_name', 'generated_file.txt')
                file_type = response.get('file_type', 'text')
                
                target_directory = self.file_manager.current_folder 
                if not target_directory or not os.path.isdir(target_directory):
                    target_directory = os.path.expanduser("~")
                    logger.warning(f"No valid current folder. Defaulting file creation to: {target_directory}")

                full_path_to_create = os.path.join(target_directory, file_name)

                if os.path.exists(full_path_to_create):
                    overwrite_reply = QMessageBox.question(
                        self, 'الملف موجود',
                        f"الملف '{os.path.basename(full_path_to_create)}' موجود بالفعل. هل تريد الكتابة فوقه؟ (إلا فسيتم إنشاء نسخة جديدة).",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                        QMessageBox.StandardButton.No
                    )
                    if overwrite_reply == QMessageBox.StandardButton.Cancel:
                        self.output_panel.add_program_output(f"ℹ️ تم إلغاء إنشاء الملف: {file_name}")
                        self.update_status(f"إنشاء الملف {file_name} ألغي.")
                        logger.info(f"EnhancedMainWindow: User cancelled file creation for {file_name}.")
                        return
                    elif overwrite_reply == QMessageBox.StandardButton.No:
                        base_name, ext = os.path.splitext(file_name)
                        counter = 1
                        new_file_name = f"{base_name}_copy{ext}"
                        new_full_path_to_create = os.path.join(target_directory, new_file_name)
                        while os.path.exists(new_full_path_to_create):
                            counter += 1
                            new_file_name = f"{base_name}_copy{counter}{ext}"
                            new_full_path_to_create = os.path.join(target_directory, new_file_name)
                        full_path_to_create = new_full_path_to_create
                        file_name = new_file_name 

                created_path = self.file_manager.create_file_with_content(full_path_to_create, content, file_type)
                
                if created_path:
                    self.open_file(created_path) 
                    self.output_panel.add_program_output(f"✅ تم إنشاء ملف جديد بواسطة الذكاء الاصطناعي: {os.path.basename(created_path)}")
                    self.update_status(f"ملف {os.path.basename(created_path)} تم إنشاؤه.")
                    logger.info(f"EnhancedMainWindow: AI requested file creation: {os.path.basename(created_path)}. Opening in UI.")
                else:
                    self.output_panel.add_program_output(f"❌ فشل في إنشاء ملف بواسطة الذكاء الاصطناعي: {file_name}")
                    self.show_error(f"فشل في إنشاء ملف بواسطة الذكاء الاصطناعي: {file_name}")
                    logger.error(f"EnhancedMainWindow: AI requested file creation but failed for {file_name}.")
            
            else:
                self.update_status(description)
                logger.info(f"EnhancedMainWindow: Non-code action '{action}' processed (output only).")

        finally:
         
            self._is_applying_ai_response = False
            QApplication.restoreOverrideCursor()


    def on_connection_changed(self, connected: bool):
        """Handle connection status change"""
        logger.info(f"EnhancedMainWindow: Connection status changed to: {connected}")
        if connected:
            self.connection_label.setText("🟢 متصل بـ Gemini AI")
            self.connection_label.setStyleSheet("color: #10B981;")
        else:
            self.connection_label.setText("🔴 غير متصل")
            self.connection_label.setStyleSheet("color: #EF4444;")
        
      
        if self.ai_assistant:
         
            pass # Placeholder, implement if needed in AIAssistantWidget
        if self.voice_control:
           
            pass 
    
    # UI updates
    def update_status(self, message: str):
        """Update status bar message"""
        logger.debug(f"EnhancedMainWindow: Updating status bar: {message}")
        self.status_label.setText(message)
        
        # Auto-clear after 5 seconds
        QTimer.singleShot(5000, lambda: self.status_label.setText("جاهز"))
    
    def update_file_info(self):
        """Update file info in status bar"""
        if self.current_file:
            file_name = os.path.basename(self.current_file)
            current_editor = self.get_current_editor()
            if current_editor:
                text = current_editor.toPlainText()
                lines = len(text.split('\n'))
                chars = len(text)
                self.file_info_label.setText(f"{file_name} | {lines} سطر | {chars} حرف")
            else:
                self.file_info_label.setText(file_name)
            logger.debug(f"EnhancedMainWindow: File info updated: {self.file_info_label.text()}")
        else:
            self.file_info_label.setText("")
            logger.debug("EnhancedMainWindow: File info cleared.")
    
    def update_recent_files_menu(self, menu):
        """Update recent files menu"""
        menu.clear()
        recent_files = self.file_manager.get_recent_files()
        
        for file_path in recent_files[:10]:
            action = menu.addAction(os.path.basename(file_path))
            
            action.triggered.connect(partial(self.open_file, file_path))
        logger.info("EnhancedMainWindow: Recent files menu updated.")
    
    def show_error(self, message: str):
        """Show error message"""
        logger.error(f"EnhancedMainWindow: Displaying error: {message}")
        QMessageBox.critical(self, "خطأ", message)
        self.update_status(f"خطأ: {message}")

        self.output_panel.add_error_display(f"❌ {message}")
        
    
    def show_settings(self):
        """Show settings dialog"""
        logger.info("EnhancedMainWindow: Showing settings dialog.")
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            
            self.apply_theme()
            logger.info("EnhancedMainWindow: Settings applied after dialog close.")
    
    def show_about(self):
        """Show about dialog"""
        logger.info("EnhancedMainWindow: Showing about dialog.")
        dialog = AboutDialog(self)
        dialog.exec()
    
 
    def restore_window_state(self):
        """Restore window state"""
        logger.info("EnhancedMainWindow: Restoring window state.")
        geometry = self.config.get_window_geometry()
        
       
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
      
        x = max(screen_geometry.x(), min(geometry['x'], screen_geometry.x() + screen_geometry.width() - 400))
        y = max(screen_geometry.y(), min(geometry['y'], screen_geometry.y() + screen_geometry.height() - 300))
        
      
        width = max(800, min(geometry['width'], screen_geometry.width()))
        height = max(600, min(geometry['height'], screen_geometry.height()))
        
        self.resize(width, height)
        self.move(x, y)
        
        if geometry['maximized'] and screen_geometry.width() > 800:
            self.showMaximized()
            logger.info("EnhancedMainWindow: Window restored to maximized state.")
        else:
            self.showNormal()
            logger.info("EnhancedMainWindow: Window restored to normal state.")
    
    def save_window_state(self):
        """Save window state"""
        logger.info("EnhancedMainWindow: Saving window state.")
        geometry = self.geometry()
        self.config.set_window_geometry(
            geometry.x(),
            geometry.y(),
            geometry.width(),
            geometry.height(),
            self.isMaximized()
        )
    
   
    
    def closeEvent(self, event):
        """Handle window close event"""
        logger.info("EnhancedMainWindow: Handling close event.")
        self.save_window_state()
        
       
        if self.voice_service.is_listening:
            self.voice_service.stop_listening()
            logger.info("EnhancedMainWindow: Voice service stopped on close.")
        
        # إيقاف FileWatcherThread
        if hasattr(self.file_manager, 'file_watcher') and self.file_manager.file_watcher:
            if self.file_manager.file_watcher.isRunning():
                self.file_manager.file_watcher.stop_watching()
                logger.info("EnhancedMainWindow: File watcher stopped on close.")
        
        # Terminate the terminal process when closing
        if self.output_panel and self.output_panel.terminal_process and \
           self.output_panel.terminal_process.state() != Process.ProcessState.NotRunning:
            self.output_panel.terminal_process.terminate() 
            self.output_panel.terminal_process.waitForFinished(2000) 
            logger.info("EnhancedMainWindow: Terminal process terminated on close.")

      

        event.accept()
        logger.info("EnhancedMainWindow: Main window closed.")
    
    def center_window(self):
        """Center the main window on the screen"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.geometry()
        
        x = screen_geometry.x() + (screen_geometry.width() - window_geometry.width()) // 2
        y = screen_geometry.y() + (screen_geometry.height() - window_geometry.height()) // 2
        
        self.move(x, y)
        logger.info("EnhancedMainWindow: Window centered.")
