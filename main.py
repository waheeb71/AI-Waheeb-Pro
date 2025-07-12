#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced AI Waheeb Pro Desktop Application
تطبيق AI Waheeb Pro المحسن لسطح المكتب
A professional AI-powered coding assistant with improved voice control,
file management, and direct Gemini AI integration.
مساعد برمجة ذكي احترافي محسن مع التحكم الصوتي وإدارة الملفات
ودمج مباشر مع Gemini AI.
"""
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

# Add current directory to path to ensure modules can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary core components and UI elements
from ui.enhanced_main_window_improved import EnhancedMainWindow
from core.app_config import AppConfig
from core.json_ai_processor import JSONAIProcessor
from core.unified_file_manager import UnifiedFileManager # Using the enhanced version

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO, # Set logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", # Define log message format
    handlers=[
        logging.FileHandler("ai_waheeb_pro_enhanced.log", encoding="utf-8"), # Log to a file
        logging.StreamHandler() # Log to console
    ]
)

logger = logging.getLogger(__name__) # Get a logger instance for this module

class EnhancedAIWaheebProApp(QApplication):
    """Enhanced main application class for AI Waheeb Pro."""
    
    def __init__(self, argv):
        """
        Initializes the application.

        Args:
            argv (list): Command line arguments.
        """
        super().__init__(argv)
        
        # Set application metadata
        self.setApplicationName("AI Waheeb Pro Enhanced")
        self.setApplicationVersion("2.1.0")
        self.setOrganizationName("AI Waheeb Pro Team")
        self.setOrganizationDomain("aiwaheebpro.com")
       
        # Set application icon if available
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"Application icon not found at: {icon_path}")
        
        # Set a default font for the application
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        # Initialize core services
        self.config = AppConfig() # Configuration manager for application settings
       
        self.file_manager = UnifiedFileManager(self.config) # Initialize with config
        # Initialize the AI processor, passing both config and file_manager
        # JSONAIProcessor requires both config and file_manager objects.
        self.gemini_service = JSONAIProcessor(self.config, self.file_manager) 
        default_folder = self.config.get_last_opened_folder() or os.path.expanduser("~")
        # Create the main application window, passing necessary services
        self.main_window = EnhancedMainWindow(self.config, self.gemini_service)
        self.aboutToQuit.connect(self._cleanup_threads)
        logger.info("Enhanced AI Waheeb Pro Desktop Application initialized successfully.")
    def _cleanup_threads(self):
        """دالة مساعدة لإدارة إغلاق الخيوط."""
        logger.info("EnhancedAIWaheebProApp: Application is about to quit. Initiating thread cleanup.")
        # استدعاء دالة الإغلاق في خدمة Gemini
        if self.gemini_service:
            self.gemini_service.shutdown()
        
    
    def show_main_window(self):
        """Displays the main application window."""
        self.main_window.show()
        # Bring the window to the front and make it active
        self.main_window.raise_()
        self.main_window.activateWindow()

def main():
    """
    Main entry point for the Enhanced AI Waheeb Pro application.
    This function initializes the QApplication and starts the event loop.
    """
    try:
        # Create an instance of the custom QApplication
        app = EnhancedAIWaheebProApp(sys.argv)
        
        # Display the main application window
        app.show_main_window()
        
        # Start the Qt event loop, which handles user interactions and events
        sys.exit(app.exec())
        
    except Exception as e:
        # Log any exceptions that occur during application startup
        logger.error(f"Failed to start enhanced application: {e}", exc_info=True)
        sys.exit(1) # Exit with an error code

if __name__ == "__main__":
    main()

