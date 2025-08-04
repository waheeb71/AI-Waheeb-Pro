#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Configuration
إعدادات التطبيق
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List # أضف List هنا
from PyQt6.QtCore import QSettings, QStandardPaths
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AppConfig:
    """Application configuration manager"""
    
    def __init__(self):
        """Initialize configuration"""
        # تهيئة QSettings
        self.settings = QSettings("AI Waheeb Pro Team", "AI Waheeb Pro Enhanced") # اسم المؤسسة واسم التطبيق مهمان لـ QSettings

        self.app_data_dir = self._get_app_data_dir()
        self.ensure_directories()
        
      
        self.config_file_path = os.path.join(self.app_data_dir, 'config.json')
        self._config_data_json = {} 
        self.load_json_config() 

        # Default configuration values
        self.defaults = {
            'window': {
                'width': 1400,
                'height': 900,
                'maximized': False,
                'x': 100,
                'y': 100
            },
            'editor': {
                'font_family': 'Consolas',
                'font_size': 12,
                'theme': 'dark',
                'tab_size': 4,
                'word_wrap': False,
                'line_numbers': True,
                'syntax_highlighting': True,
                'auto_indent': True,
                'auto_complete': True
            },
            'ai': {
                'model': 'gemini-2.0-flash',
                'temperature': 0.7,
                'max_tokens': 2048,
                'timeout': 30,
                'api_key': 'your_api_key_here' # أضف مفتاح API هنا كقيمة افتراضية
            },
            'voice': {
                'enabled': True,
                'language': 'ar-SA',
                'recognition_timeout': 5,
                'phrase_timeout': 1
            },
            'files': {
                'recent_files': [],
                'recent_folders': [],
                'auto_save': True,
                'auto_save_interval': 300,  # 5 minutes
                'backup_enabled': True,
                'max_recent_files': 10,
                # *** أضف هذا الإعداد الافتراضي الجديد هنا ***
                'last_opened_folder': os.path.expanduser("~") # القيمة الافتراضية هي المجلد الرئيسي للمستخدم
            },
            'ui': {
                'theme': 'dark',
                'language': 'ar',
                'show_welcome': True,
                'show_minimap': True,
                'show_file_tree': True,
                'show_output_panel': True
            }
        }
        
        logger.info(f"Configuration initialized. App data directory: {self.app_data_dir}")
    
    def load_json_config(self):
        """Loads configuration specific to JSON file (e.g., recent lists)."""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    self._config_data_json = json.load(f)
                logger.info(f"JSON configuration loaded from: {self.config_file_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding config file {self.config_file_path}: {e}. Starting with empty JSON config.")
                self._config_data_json = {}
            except Exception as e:
                logger.error(f"Error loading JSON config file {self.config_file_path}: {e}. Starting with empty JSON config.")
                self._config_data_json = {}
        else:
            logger.info("No JSON config file found. Starting with default JSON configuration.")
    
    def save_json_config(self):
        """Saves configuration specific to JSON file (e.g., recent lists)."""
        try:
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(self._config_data_json, f, indent=4, ensure_ascii=False)
            logger.info(f"JSON configuration saved to: {self.config_file_path}")
        except Exception as e:
            logger.error(f"Error saving JSON config file {self.config_file_path}: {e}")

    def _get_app_data_dir(self) -> str:
        """Get application data directory"""
        app_data = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        return os.path.join(app_data, "AI Waheeb Pro Enhanced") # تأكد من أن هذا يتطابق مع اسم التطبيق
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            self.app_data_dir,
            os.path.join(self.app_data_dir, 'projects'),
            os.path.join(self.app_data_dir, 'backups'),
            os.path.join(self.app_data_dir, 'logs'),
            os.path.join(self.app_data_dir, 'cache')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        # أولاً، حاول الحصول على القيمة من QSettings
        settings_value = self.settings.value(key)
        
        if settings_value is not None:
            return settings_value
        
        # إذا لم تكن موجودة في QSettings، حاول الحصول عليها من القاموس الافتراضي
        keys = key.split('.')
        value = self.defaults
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default # إذا لم يتم العثور على المفتاح في الافتراضيات
            return value
        except Exception as e:
            logger.warning(f"Failed to get default value for '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        try:
            self.settings.setValue(key, value)
            self.settings.sync() # حفظ التغييرات فوراً إلى QSettings
            
            # تحديث قاموس الافتراضيات لتجنب تناقض البيانات في حال تم الوصول إليها بشكل مباشر
            # هذا يحافظ على التناسق بين القاموس الافتراضي و QSettings
            keys = key.split('.')
            current = self.defaults
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
            
        except Exception as e:
            logger.error(f"Failed to set config value for '{key}': {e}")
    
    def get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key"""
        # Try environment variable first
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            return api_key
        
        # Try QSettings (which gets from default if not set)
        return self.get('ai.api_key')
    
    def set_gemini_api_key(self, api_key: str):
        """Set Gemini API key"""
        self.set('ai.api_key', api_key)
    
    def get_recent_files(self) -> List[str]:
        """Get recent files list (from JSON config)"""
        recent = self._config_data_json.get('files', {}).get('recent_files', [])
        return [f for f in recent if os.path.exists(f)] if isinstance(recent, list) else [] 

    def add_recent_file(self, file_path: str):
        """Add file to recent files (and save to JSON config)"""
        recent = self.get_recent_files() 
        
        # Remove if already exists
        if file_path in recent:
            recent.remove(file_path)
        
        # Add to beginning
        recent.insert(0, file_path)
        
        # Limit to max recent files
        max_files = self.get('files.max_recent_files', 10)
        recent = recent[:max_files]
        
        # تحديث في قاموس JSON وحفظه
        if 'files' not in self._config_data_json:
            self._config_data_json['files'] = {}
        self._config_data_json['files']['recent_files'] = recent
        self.save_json_config()
    
    def get_recent_folders(self) -> List[str]:
        """Get recent folders list (from JSON config)"""
        recent = self._config_data_json.get('files', {}).get('recent_folders', [])
        return [f for f in recent if os.path.isdir(f)] if isinstance(recent, list) else [] 
    
    def add_recent_folder(self, folder_path: str):
        """Add folder to recent folders (and save to JSON config, also update last_opened_folder)"""
        recent = self.get_recent_folders() # استخدم الدالة الحالية للحصول على القائمة المفلتَرة
        
        # Remove if already exists
        if folder_path in recent:
            recent.remove(folder_path)
        
        # Add to beginning
        recent.insert(0, folder_path)
        
        # Limit to max recent folders
        max_folders = self.get('files.max_recent_files', 10) 
        recent = recent[:max_folders]
        
        # تحديث في قاموس JSON وحفظه
        if 'files' not in self._config_data_json:
            self._config_data_json['files'] = {}
        self._config_data_json['files']['recent_folders'] = recent
        self.save_json_config()
        
        # *** أضف هذا السطر لتعيين آخر مجلد مفتوح ***
        self.set_last_opened_folder(folder_path)

    # *** أضف الدوال الجديدة هنا ***
    def get_last_opened_folder(self) -> Optional[str]:
        """Retrieves the path of the last opened folder."""
   
        folder = self.get('files.last_opened_folder', None)
        
        # التحقق مما إذا كان المسار صالحًا كدليل
        if folder and os.path.isdir(folder):
            return folder
        
        # القيمة الافتراضية النهائية إذا لم تكن موجودة أو غير صالحة
        return os.path.expanduser("~")

    def set_last_opened_folder(self, folder_path: str):
        """Saves the path of the last opened folder."""
        # تأكد من أن المسار هو دليل صالح قبل حفظه
        if os.path.isdir(folder_path):
            self.set('files.last_opened_folder', folder_path)
        else:
            logger.warning(f"Attempted to set invalid last_opened_folder: {folder_path}. Not saving.")

    def get_window_geometry(self) -> Dict[str, Any]: # تغيير int إلى Any لأن maximized هو bool
        """Get window geometry"""
        return {
            'x': self.get('window.x', self.defaults['window']['x']),
            'y': self.get('window.y', self.defaults['window']['y']),
            'width': self.get('window.width', self.defaults['window']['width']),
            'height': self.get('window.height', self.defaults['window']['height']),
            'maximized': self.get('window.maximized', self.defaults['window']['maximized'])
        }
    
    def set_window_geometry(self, x: int, y: int, width: int, height: int, maximized: bool = False):
        """Set window geometry"""
        self.set('window.x', x)
        self.set('window.y', y)
        self.set('window.width', width)
        self.set('window.height', height)
        self.set('window.maximized', maximized)
    
    def get_editor_settings(self) -> Dict[str, Any]:
        """Get editor settings"""
        # يمكنك جعل هذا أكثر ديناميكية بدلاً من تكرار المفاتيح
        settings = {}
        for key_part, default_val in self.defaults['editor'].items():
            settings[key_part] = self.get(f'editor.{key_part}', default_val)
        return settings
    
    def get_projects_dir(self) -> str:
        """Get projects directory"""
        return os.path.join(self.app_data_dir, 'projects')
    
    def get_backups_dir(self) -> str:
        """Get backups directory"""
        return os.path.join(self.app_data_dir, 'backups')
    
    def get_logs_dir(self) -> str:
        """Get logs directory"""
        return os.path.join(self.app_data_dir, 'logs')
    
    def get_cache_dir(self) -> str:
        """Get cache directory"""
        return os.path.join(self.app_data_dir, 'cache')
    
    def export_settings(self, file_path: str):
        """Export settings to file (both QSettings and JSON parts)"""
        try:
            settings_to_export = {}
            
            # 1. Export from QSettings
            for key in self.settings.allKeys():
                settings_to_export[key] = self.settings.value(key)
            
            # 2. Add JSON specific data (like recent_files/folders)
            # يجب أن يتم دمج هذا بشكل أذكى لتجنب التكرار إذا كانت QSettings تحفظها أيضاً
            # أو التأكد من أن QSettings لا تحفظها وأنها فقط في JSON
            # في حالتك الحالية، يبدو أن get_recent_files/folders تقرأ من _config_data_json،
            # لذا يجب حفظها بشكل منفصل.
            settings_to_export['files.recent_files'] = self.get_recent_files()
            settings_to_export['files.recent_folders'] = self.get_recent_folders()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_to_export, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Settings exported to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export settings: {e}", exc_info=True)
            raise
    
    def import_settings(self, file_path: str):
        """Import settings from file (to both QSettings and JSON parts)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_dict = json.load(f)
            
            for key, value in settings_dict.items():
                if key == 'files.recent_files':
                    if 'files' not in self._config_data_json: self._config_data_json['files'] = {}
                    self._config_data_json['files']['recent_files'] = value
                elif key == 'files.recent_folders':
                    if 'files' not in self._config_data_json: self._config_data_json['files'] = {}
                    self._config_data_json['files']['recent_folders'] = value
                else:
                    self.settings.setValue(key, value) # يتم الحفظ إلى QSettings
            
            self.settings.sync()
            self.save_json_config() # حفظ إعدادات JSON المستوردة
            logger.info(f"Settings imported from: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to import settings: {e}", exc_info=True)
            raise
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        try:
            self.settings.clear()
            self.settings.sync()
            
            # إعادة تهيئة _config_data_json
            self._config_data_json = {}
            self.save_json_config() # حفظ ملف JSON فارغ
            
            logger.info("Settings reset to defaults")
            
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}", exc_info=True)
            raise
