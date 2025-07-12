#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced File Manager with VS Code-like Features
مدير الملفات المحسن مع ميزات مشابهة لـ VS Code
"""

import os
import shutil
import json
import logging
import subprocess
import sys
import platform
import mimetypes
import hashlib
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QFileSystemWatcher, QTimer, QThread
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog

logger = logging.getLogger(__name__)

class FileOperation:
    """عملية ملف"""
    
    def __init__(self, operation_type: str, source: str, destination: str = None, 
                 callback: Callable = None, metadata: Dict = None):
        self.operation_type = operation_type  # copy, move, delete, create
        self.source = source
        self.destination = destination
        self.callback = callback
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.status = 'pending'  # pending, running, completed, failed
        self.error = None
        self.progress = 0.0

class FileWatcherThread(QThread):
    """خيط مراقبة الملفات المحسن"""
    
    file_changed = pyqtSignal(str, dict)  # file_path, change_info
    file_added = pyqtSignal(str, dict)
    file_removed = pyqtSignal(str, dict)
    directory_changed = pyqtSignal(str, dict)
    
    def __init__(self, watch_paths: List[str]):
        super().__init__()
        self.watch_paths = watch_paths
        self.is_watching = False
        self.file_states = {}
        self.check_interval = 1.0  # ثانية
        self.ignore_patterns = {'.git', '__pycache__', 'node_modules', '.DS_Store'}
        
    def run(self):
        """تشغيل مراقب الملفات"""
        self.is_watching = True
        self.scan_initial_state()
        
        while self.is_watching:
            self.check_changes()
            self.msleep(int(self.check_interval * 1000))
    
    def stop_watching(self):
        """إيقاف المراقبة"""
        self.is_watching = False
        self.quit()
        self.wait()
    
    def add_watch_path(self, path: str):
        """إضافة مسار للمراقبة"""
        if path not in self.watch_paths:
            self.watch_paths.append(path)
            if self.is_watching:
                self.scan_path_initial_state(path)
    
    def remove_watch_path(self, path: str):
        """إزالة مسار من المراقبة"""
        if path in self.watch_paths:
            self.watch_paths.remove(path)
            # إزالة حالات الملفات المرتبطة بهذا المسار
            to_remove = [fp for fp in self.file_states.keys() if fp.startswith(path)]
            for fp in to_remove:
                del self.file_states[fp]
    
    def scan_initial_state(self):
        """فحص الحالة الأولية لجميع المسارات"""
        for path in self.watch_paths:
            self.scan_path_initial_state(path)
    
    def scan_path_initial_state(self, path: str):
        """فحص الحالة الأولية لمسار معين"""
        if not os.path.exists(path):
            return
        
        try:
            if os.path.isfile(path):
                self._scan_file(path)
            else:
                for root, dirs, files in os.walk(path):
                    # تصفية المجلدات المتجاهلة
                    dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
                    
                    for file in files:
                        if not file.startswith('.') or file in ['.gitignore', '.env']:
                            file_path = os.path.join(root, file)
                            self._scan_file(file_path)
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot scan path {path}: {e}")
    
    def _scan_file(self, file_path: str):
        """فحص ملف واحد"""
        try:
            stat = os.stat(file_path)
            self.file_states[file_path] = {
                'mtime': stat.st_mtime,
                'size': stat.st_size,
                'mode': stat.st_mode,
                'exists': True
            }
        except (OSError, PermissionError):
            pass
    
    def check_changes(self):
        """فحص التغييرات في الملفات"""
        current_files = set()
        
        for watch_path in self.watch_paths:
            if not os.path.exists(watch_path):
                continue
            
            try:
                if os.path.isfile(watch_path):
                    current_files.add(watch_path)
                    self._check_file_changes(watch_path)
                else:
                    for root, dirs, files in os.walk(watch_path):
                        # تصفية المجلدات المتجاهلة
                        dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
                        
                        for file in files:
                            if not file.startswith('.') or file in ['.gitignore', '.env']:
                                file_path = os.path.join(root, file)
                                current_files.add(file_path)
                                self._check_file_changes(file_path)
            except (OSError, PermissionError):
                continue
        
        # فحص الملفات المحذوفة
        removed_files = set(self.file_states.keys()) - current_files
        for file_path in removed_files:
            if self.file_states[file_path]['exists']:
                self.file_states[file_path]['exists'] = False
                change_info = {
                    'type': 'removed',
                    'timestamp': time.time(),
                    'previous_state': self.file_states[file_path].copy()
                }
                self.file_removed.emit(file_path, change_info)
                logger.debug(f"File removed: {file_path}")
    
    def _check_file_changes(self, file_path: str):
        """فحص تغييرات ملف معين"""
        try:
            stat = os.stat(file_path)
            current_state = {
                'mtime': stat.st_mtime,
                'size': stat.st_size,
                'mode': stat.st_mode,
                'exists': True
            }
            
            if file_path not in self.file_states:
                # ملف جديد
                self.file_states[file_path] = current_state
                change_info = {
                    'type': 'added',
                    'timestamp': time.time(),
                    'current_state': current_state
                }
                self.file_added.emit(file_path, change_info)
                logger.debug(f"File added: {file_path}")
                
            elif self.file_states[file_path] != current_state:
                # ملف متغير
                previous_state = self.file_states[file_path].copy()
                self.file_states[file_path] = current_state
                
                change_info = {
                    'type': 'modified',
                    'timestamp': time.time(),
                    'previous_state': previous_state,
                    'current_state': current_state,
                    'size_changed': previous_state['size'] != current_state['size'],
                    'time_changed': previous_state['mtime'] != current_state['mtime'],
                    'mode_changed': previous_state['mode'] != current_state['mode']
                }
                self.file_changed.emit(file_path, change_info)
                logger.debug(f"File modified: {file_path}")
                
        except (OSError, PermissionError):
            pass

class FileHistoryManager:
    """مدير تاريخ الملفات"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history = []
        self.current_index = -1
    
    def add_operation(self, operation: FileOperation):
        """إضافة عملية إلى التاريخ"""
        # إزالة العمليات التي تأتي بعد الفهرس الحالي (للتراجع)
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        self.history.append(operation)
        self.current_index = len(self.history) - 1
        
        # الحفاظ على الحد الأقصى للتاريخ
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
    
    def can_undo(self) -> bool:
        """فحص إمكانية التراجع"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """فحص إمكانية الإعادة"""
        return self.current_index < len(self.history) - 1
    
    def undo(self) -> Optional[FileOperation]:
        """التراجع عن العملية الأخيرة"""
        if not self.can_undo():
            return None
        
        operation = self.history[self.current_index]
        self.current_index -= 1
        return operation
    
    def redo(self) -> Optional[FileOperation]:
        """إعادة العملية التالية"""
        if not self.can_redo():
            return None
        
        self.current_index += 1
        operation = self.history[self.current_index]
        return operation
    
    def get_history(self) -> List[FileOperation]:
        """الحصول على التاريخ الكامل"""
        return self.history.copy()
    
    def clear_history(self):
        """مسح التاريخ"""
        self.history.clear()
        self.current_index = -1

class FileSearchEngine:
    """محرك البحث في الملفات"""
    
    def __init__(self):
        self.search_cache = {}
        self.cache_timeout = 300  # 5 دقائق
    
    def search_files(self, root_path: str, pattern: str, 
                    include_content: bool = False,
                    file_extensions: List[str] = None,
                    max_results: int = 1000) -> List[Dict[str, Any]]:
        """البحث في الملفات"""
        results = []
        pattern_lower = pattern.lower()
        
        try:
            for root, dirs, files in os.walk(root_path):
                # تصفية المجلدات المتجاهلة
                dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules'}]
                
                for file in files:
                    if len(results) >= max_results:
                        break
                    
                    file_path = os.path.join(root, file)
                    file_name_lower = file.lower()
                    
                    # فحص الامتداد
                    if file_extensions:
                        _, ext = os.path.splitext(file)
                        if ext.lower() not in file_extensions:
                            continue
                    
                    # البحث في اسم الملف
                    name_match = pattern_lower in file_name_lower
                    content_matches = []
                    
                    # البحث في المحتوى
                    if include_content and self._is_text_file(file_path):
                        content_matches = self._search_in_file_content(file_path, pattern)
                    
                    if name_match or content_matches:
                        try:
                            stat = os.stat(file_path)
                            result = {
                                'path': file_path,
                                'name': file,
                                'size': stat.st_size,
                                'modified': stat.st_mtime,
                                'name_match': name_match,
                                'content_matches': content_matches,
                                'match_count': len(content_matches)
                            }
                            results.append(result)
                        except OSError:
                            continue
                
                if len(results) >= max_results:
                    break
        
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        return results
    
    def _is_text_file(self, file_path: str) -> bool:
        """فحص ما إذا كان الملف نصياً"""
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith('text/'):
                return True
            
            # فحص الامتدادات المعروفة
            text_extensions = {
                '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
                '.txt', '.md', '.rst', '.log', '.cfg', '.ini', '.conf'
            }
            _, ext = os.path.splitext(file_path)
            return ext.lower() in text_extensions
        except:
            return False
    
    def _search_in_file_content(self, file_path: str, pattern: str) -> List[Dict[str, Any]]:
        """البحث في محتوى الملف"""
        matches = []
        pattern_lower = pattern.lower()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_lower = line.lower()
                    if pattern_lower in line_lower:
                        # العثور على جميع المواضع في السطر
                        start = 0
                        while True:
                            pos = line_lower.find(pattern_lower, start)
                            if pos == -1:
                                break
                            
                            matches.append({
                                'line_number': line_num,
                                'line_content': line.strip(),
                                'match_position': pos,
                                'match_length': len(pattern)
                            })
                            start = pos + 1
                    
                    # حد أقصى للمطابقات لكل ملف
                    if len(matches) >= 50:
                        break
        
        except Exception as e:
            logger.debug(f"Cannot search in file {file_path}: {e}")
        
        return matches

class FileComparisonEngine:
    """محرك مقارنة الملفات"""
    
    def __init__(self):
        self.hash_cache = {}
    
    def compare_files(self, file1: str, file2: str) -> Dict[str, Any]:
        """مقارنة ملفين"""
        result = {
            'files': [file1, file2],
            'identical': False,
            'size_match': False,
            'hash_match': False,
            'content_diff': None,
            'error': None
        }
        
        try:
            # فحص وجود الملفات
            if not os.path.exists(file1) or not os.path.exists(file2):
                result['error'] = 'أحد الملفات غير موجود'
                return result
            
            # مقارنة الأحجام
            size1 = os.path.getsize(file1)
            size2 = os.path.getsize(file2)
            result['size_match'] = size1 == size2
            
            if not result['size_match']:
                return result
            
            # مقارنة الهاش
            hash1 = self._get_file_hash(file1)
            hash2 = self._get_file_hash(file2)
            result['hash_match'] = hash1 == hash2
            result['identical'] = result['hash_match']
            
            # إذا كانت الملفات نصية ومختلفة، احسب الفروق
            if not result['identical'] and self._is_text_file(file1) and self._is_text_file(file2):
                result['content_diff'] = self._get_text_diff(file1, file2)
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _get_file_hash(self, file_path: str) -> str:
        """حساب هاش الملف"""
        if file_path in self.hash_cache:
            cached_hash, cached_mtime = self.hash_cache[file_path]
            current_mtime = os.path.getmtime(file_path)
            if current_mtime == cached_mtime:
                return cached_hash
        
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            
            file_hash = hash_md5.hexdigest()
            self.hash_cache[file_path] = (file_hash, os.path.getmtime(file_path))
            return file_hash
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def _is_text_file(self, file_path: str) -> bool:
        """فحص ما إذا كان الملف نصياً"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' not in chunk
        except:
            return False
    
    def _get_text_diff(self, file1: str, file2: str) -> List[str]:
        """حساب الفروق النصية بين ملفين"""
        try:
            import difflib
            
            with open(file1, 'r', encoding='utf-8') as f1:
                lines1 = f1.readlines()
            
            with open(file2, 'r', encoding='utf-8') as f2:
                lines2 = f2.readlines()
            
            diff = list(difflib.unified_diff(
                lines1, lines2,
                fromfile=os.path.basename(file1),
                tofile=os.path.basename(file2),
                lineterm=''
            ))
            
            return diff
        except Exception as e:
            logger.error(f"Error calculating text diff: {e}")
            return []

class EnhancedFileManager(QObject):
    """مدير الملفات المحسن مع ميزات متقدمة"""
    
    # الإشارات
    file_opened = pyqtSignal(str, str)  # file_path, content
    file_saved = pyqtSignal(str)  # file_path
    file_created = pyqtSignal(str, str)  # file_path, file_type
    file_deleted = pyqtSignal(str)  # file_path
    file_renamed = pyqtSignal(str, str)  # old_path, new_path
    file_copied = pyqtSignal(str, str)  # source_path, dest_path
    file_moved = pyqtSignal(str, str)  # source_path, dest_path
    folder_opened = pyqtSignal(str)  # folder_path
    folder_created = pyqtSignal(str)  # folder_path
    project_opened = pyqtSignal(str, dict)  # project_path, project_info
    error_occurred = pyqtSignal(str)  # error_message
    file_changed_externally = pyqtSignal(str, dict)  # file_path, change_info
    operation_progress = pyqtSignal(str, float)  # operation_id, progress
    operation_completed = pyqtSignal(str, bool, str)  # operation_id, success, message
    search_completed = pyqtSignal(str, list)  # search_id, results
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_project = None
        self.current_folder = None
        self.open_files = {}  # file_path -> {'content': str, 'modified': bool, 'encoding': str}
        self.recent_files = []
        self.recent_folders = []
        self.bookmarks = []
        
        # المكونات المحسنة
        self.file_watcher = None
        self.history_manager = FileHistoryManager()
        self.search_engine = FileSearchEngine()
        self.comparison_engine = FileComparisonEngine()
        
        # إعدادات متقدمة
        self.auto_save_enabled = True
        self.auto_save_interval = 30  # ثانية
        self.backup_enabled = True
        self.max_backup_files = 10
        self.file_encoding = 'utf-8'
        self.line_ending = 'auto'  # auto, lf, crlf, cr
        
        # عمليات الملفات
        self.pending_operations = {}
        self.operation_counter = 0
        
        # مؤقت الحفظ التلقائي
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_all)
        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval * 1000)
        
        # تحميل الإعدادات
        self.load_settings()
        
        logger.info("Enhanced File Manager initialized")
    
    def load_settings(self):
        """تحميل الإعدادات"""
        try:
            # تحميل الملفات الأخيرة
            self.recent_files = self.config.get('recent_files', [])
            self.recent_folders = self.config.get('recent_folders', [])
            self.bookmarks = self.config.get('bookmarks', [])
            
            # تحميل إعدادات الملفات
            self.auto_save_enabled = self.config.get('auto_save_enabled', True)
            self.auto_save_interval = self.config.get('auto_save_interval', 30)
            self.backup_enabled = self.config.get('backup_enabled', True)
            self.max_backup_files = self.config.get('max_backup_files', 10)
            self.file_encoding = self.config.get('file_encoding', 'utf-8')
            self.line_ending = self.config.get('line_ending', 'auto')
            
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
    
    def save_settings(self):
        """حفظ الإعدادات"""
        try:
            self.config.set('recent_files', self.recent_files)
            self.config.set('recent_folders', self.recent_folders)
            self.config.set('bookmarks', self.bookmarks)
            self.config.set('auto_save_enabled', self.auto_save_enabled)
            self.config.set('auto_save_interval', self.auto_save_interval)
            self.config.set('backup_enabled', self.backup_enabled)
            self.config.set('max_backup_files', self.max_backup_files)
            self.config.set('file_encoding', self.file_encoding)
            self.config.set('line_ending', self.line_ending)
        except Exception as e:
            logger.warning(f"Failed to save settings: {e}")
    
    def set_current_folder(self, folder_path: str):
        """تعيين المجلد الحالي"""
        if not os.path.isdir(folder_path):
            self.error_occurred.emit(f"المجلد غير صالح: {folder_path}")
            return False
        
        self.current_folder = folder_path
        self.add_recent_folder(folder_path)
        
        # بدء مراقبة الملفات
        self.start_file_watching([folder_path])
        
        self.folder_opened.emit(folder_path)
        logger.info(f"Current folder set to: {folder_path}")
        return True
    
    def start_file_watching(self, paths: List[str]):
        """بدء مراقبة الملفات"""
        if self.file_watcher:
            self.file_watcher.stop_watching()
        
        self.file_watcher = FileWatcherThread(paths)
        self.file_watcher.file_changed.connect(self._on_file_changed_externally)
        self.file_watcher.file_added.connect(self._on_file_added_externally)
        self.file_watcher.file_removed.connect(self._on_file_removed_externally)
        self.file_watcher.start()
    
    def stop_file_watching(self):
        """إيقاف مراقبة الملفات"""
        if self.file_watcher:
            self.file_watcher.stop_watching()
            self.file_watcher = None
    
    def _on_file_changed_externally(self, file_path: str, change_info: dict):
        """التعامل مع تغيير ملف خارجياً"""
        self.file_changed_externally.emit(file_path, change_info)
        
        # إذا كان الملف مفتوحاً، تحديث حالته
        if file_path in self.open_files:
            self.open_files[file_path]['externally_modified'] = True
    
    def _on_file_added_externally(self, file_path: str, change_info: dict):
        """التعامل مع إضافة ملف خارجياً"""
        logger.info(f"File added externally: {file_path}")
    
    def _on_file_removed_externally(self, file_path: str, change_info: dict):
        """التعامل مع حذف ملف خارجياً"""
        logger.info(f"File removed externally: {file_path}")
        
        # إذا كان الملف مفتوحاً، تحديث حالته
        if file_path in self.open_files:
            self.open_files[file_path]['externally_deleted'] = True
    
    def create_file(self, file_path: str, content: str = "", file_type: str = None) -> str:
        """إنشاء ملف جديد"""
        operation_id = self._generate_operation_id()
        
        try:
            # التأكد من وجود المجلد الأب
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # كتابة الملف
            encoding = self._detect_encoding(content) if content else self.file_encoding
            with open(file_path, 'w', encoding=encoding, newline='') as f:
                f.write(content)
            
            # إضافة إلى الملفات المفتوحة
            self.open_files[file_path] = {
                'content': content,
                'modified': False,
                'encoding': encoding,
                'line_ending': self._detect_line_ending(content),
                'externally_modified': False,
                'externally_deleted': False
            }
            
            # إضافة إلى التاريخ
            operation = FileOperation('create', file_path, metadata={'content': content})
            self.history_manager.add_operation(operation)
            
            # إضافة إلى الملفات الأخيرة
            self.add_recent_file(file_path)
            
            # إرسال الإشارات
            self.file_created.emit(file_path, file_type or self._detect_file_type(file_path))
            self.operation_completed.emit(operation_id, True, f"تم إنشاء الملف: {os.path.basename(file_path)}")
            
            logger.info(f"File created: {file_path}")
            return operation_id
            
        except Exception as e:
            error_msg = f"فشل في إنشاء الملف: {e}"
            self.error_occurred.emit(error_msg)
            self.operation_completed.emit(operation_id, False, error_msg)
            logger.error(error_msg)
            return operation_id
    
    def open_file(self, file_path: str = None) -> Optional[str]:
        """فتح ملف"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                None,
                "فتح ملف",
                self.current_folder or os.path.expanduser("~"),
                "جميع الملفات (*.*)"
            )
            
            if not file_path:
                return None
        
        try:
            if not os.path.exists(file_path):
                self.error_occurred.emit(f"الملف غير موجود: {file_path}")
                return None
            
            # قراءة الملف
            encoding = self._detect_file_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # إضافة إلى الملفات المفتوحة
            self.open_files[file_path] = {
                'content': content,
                'modified': False,
                'encoding': encoding,
                'line_ending': self._detect_line_ending(content),
                'externally_modified': False,
                'externally_deleted': False
            }
            
            # إضافة إلى الملفات الأخيرة
            self.add_recent_file(file_path)
            
            # إرسال الإشارة
            self.file_opened.emit(file_path, content)
            
            logger.info(f"File opened: {file_path}")
            return file_path
            
        except Exception as e:
            error_msg = f"فشل في فتح الملف: {e}"
            self.error_occurred.emit(error_msg)
            logger.error(error_msg)
            return None
    
    def save_file(self, file_path: str, content: str, encoding: str = None) -> bool:
        """حفظ ملف"""
        try:
            # إنشاء نسخة احتياطية إذا كانت مفعلة
            if self.backup_enabled and os.path.exists(file_path):
                self._create_backup(file_path)
            
            # تحديد الترميز
            if not encoding:
                if file_path in self.open_files:
                    encoding = self.open_files[file_path]['encoding']
                else:
                    encoding = self.file_encoding
            
            # التأكد من وجود المجلد الأب
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # كتابة الملف
            with open(file_path, 'w', encoding=encoding, newline='') as f:
                f.write(content)
            
            # تحديث الملفات المفتوحة
            if file_path in self.open_files:
                self.open_files[file_path].update({
                    'content': content,
                    'modified': False,
                    'encoding': encoding,
                    'externally_modified': False
                })
            else:
                self.open_files[file_path] = {
                    'content': content,
                    'modified': False,
                    'encoding': encoding,
                    'line_ending': self._detect_line_ending(content),
                    'externally_modified': False,
                    'externally_deleted': False
                }
            
            # إضافة إلى التاريخ
            operation = FileOperation('save', file_path, metadata={'content': content})
            self.history_manager.add_operation(operation)
            
            # إضافة إلى الملفات الأخيرة
            self.add_recent_file(file_path)
            
            # إرسال الإشارة
            self.file_saved.emit(file_path)
            
            logger.info(f"File saved: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"فشل في حفظ الملف: {e}"
            self.error_occurred.emit(error_msg)
            logger.error(error_msg)
            return False
    
    def save_file_as(self, current_path: str, content: str, new_path: str = None) -> Optional[str]:
        """حفظ ملف باسم جديد"""
        if not new_path:
            new_path, _ = QFileDialog.getSaveFileName(
                None,
                "حفظ باسم",
                current_path or self.current_folder or os.path.expanduser("~"),
                "جميع الملفات (*.*)"
            )
            
            if not new_path:
                return None
        
        if self.save_file(new_path, content):
            return new_path
        return None
    
    def close_file(self, file_path: str, save_if_modified: bool = True) -> bool:
        """إغلاق ملف"""
        if file_path not in self.open_files:
            return True
        
        file_info = self.open_files[file_path]
        
        # فحص التعديلات
        if file_info['modified'] and save_if_modified:
            reply = QMessageBox.question(
                None, 'حفظ التغييرات',
                f'هل تريد حفظ التغييرات في "{os.path.basename(file_path)}"؟',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return False
            elif reply == QMessageBox.StandardButton.Yes:
                if not self.save_file(file_path, file_info['content']):
                    return False
        
        # إزالة من الملفات المفتوحة
        del self.open_files[file_path]
        
        logger.info(f"File closed: {file_path}")
        return True
    
    def delete_file(self, file_path: str) -> bool:
        """حذف ملف"""
        operation_id = self._generate_operation_id()
        
        try:
            if not os.path.exists(file_path):
                self.error_occurred.emit(f"الملف غير موجود: {file_path}")
                return False
            
            # إنشاء نسخة احتياطية
            if self.backup_enabled:
                self._create_backup(file_path)
            
            # إغلاق الملف إذا كان مفتوحاً
            if file_path in self.open_files:
                self.close_file(file_path, save_if_modified=False)
            
            # حذف الملف
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            
            # إضافة إلى التاريخ
            operation = FileOperation('delete', file_path)
            self.history_manager.add_operation(operation)
            
            # إرسال الإشارات
            self.file_deleted.emit(file_path)
            self.operation_completed.emit(operation_id, True, f"تم حذف: {os.path.basename(file_path)}")
            
            logger.info(f"File deleted: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"فشل في حذف الملف: {e}"
            self.error_occurred.emit(error_msg)
            self.operation_completed.emit(operation_id, False, error_msg)
            logger.error(error_msg)
            return False
    
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """إعادة تسمية ملف"""
        operation_id = self._generate_operation_id()
        
        try:
            if not os.path.exists(old_path):
                self.error_occurred.emit(f"الملف غير موجود: {old_path}")
                return False
            
            if os.path.exists(new_path):
                self.error_occurred.emit(f"الملف موجود بالفعل: {new_path}")
                return False
            
            # إعادة التسمية
            os.rename(old_path, new_path)
            
            # تحديث الملفات المفتوحة
            if old_path in self.open_files:
                self.open_files[new_path] = self.open_files.pop(old_path)
            
            # تحديث الملفات الأخيرة
            if old_path in self.recent_files:
                index = self.recent_files.index(old_path)
                self.recent_files[index] = new_path
            
            # إضافة إلى التاريخ
            operation = FileOperation('rename', old_path, new_path)
            self.history_manager.add_operation(operation)
            
            # إرسال الإشارات
            self.file_renamed.emit(old_path, new_path)
            self.operation_completed.emit(operation_id, True, f"تم إعادة تسمية: {os.path.basename(new_path)}")
            
            logger.info(f"File renamed: {old_path} -> {new_path}")
            return True
            
        except Exception as e:
            error_msg = f"فشل في إعادة التسمية: {e}"
            self.error_occurred.emit(error_msg)
            self.operation_completed.emit(operation_id, False, error_msg)
            logger.error(error_msg)
            return False
    
    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """نسخ ملف"""
        operation_id = self._generate_operation_id()
        
        try:
            if not os.path.exists(source_path):
                self.error_occurred.emit(f"الملف المصدر غير موجود: {source_path}")
                return False
            
            # التأكد من وجود المجلد الهدف
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            # نسخ الملف أو المجلد
            if os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path)
            else:
                shutil.copy2(source_path, dest_path)
            
            # إضافة إلى التاريخ
            operation = FileOperation('copy', source_path, dest_path)
            self.history_manager.add_operation(operation)
            
            # إرسال الإشارات
            self.file_copied.emit(source_path, dest_path)
            self.operation_completed.emit(operation_id, True, f"تم نسخ: {os.path.basename(dest_path)}")
            
            logger.info(f"File copied: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            error_msg = f"فشل في نسخ الملف: {e}"
            self.error_occurred.emit(error_msg)
            self.operation_completed.emit(operation_id, False, error_msg)
            logger.error(error_msg)
            return False
    
    def move_file(self, source_path: str, dest_path: str) -> bool:
        """نقل ملف"""
        operation_id = self._generate_operation_id()
        
        try:
            if not os.path.exists(source_path):
                self.error_occurred.emit(f"الملف المصدر غير موجود: {source_path}")
                return False
            
            # التأكد من وجود المجلد الهدف
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            # نقل الملف
            shutil.move(source_path, dest_path)
            
            # تحديث الملفات المفتوحة
            if source_path in self.open_files:
                self.open_files[dest_path] = self.open_files.pop(source_path)
            
            # تحديث الملفات الأخيرة
            if source_path in self.recent_files:
                index = self.recent_files.index(source_path)
                self.recent_files[index] = dest_path
            
            # إضافة إلى التاريخ
            operation = FileOperation('move', source_path, dest_path)
            self.history_manager.add_operation(operation)
            
            # إرسال الإشارات
            self.file_moved.emit(source_path, dest_path)
            self.operation_completed.emit(operation_id, True, f"تم نقل: {os.path.basename(dest_path)}")
            
            logger.info(f"File moved: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            error_msg = f"فشل في نقل الملف: {e}"
            self.error_occurred.emit(error_msg)
            self.operation_completed.emit(operation_id, False, error_msg)
            logger.error(error_msg)
            return False
    
    def create_folder(self, folder_path: str) -> bool:
        """إنشاء مجلد"""
        operation_id = self._generate_operation_id()
        
        try:
            if os.path.exists(folder_path):
                self.error_occurred.emit(f"المجلد موجود بالفعل: {folder_path}")
                return False
            
            os.makedirs(folder_path, exist_ok=True)
            
            # إضافة إلى التاريخ
            operation = FileOperation('create_folder', folder_path)
            self.history_manager.add_operation(operation)
            
            # إرسال الإشارات
            self.folder_created.emit(folder_path)
            self.operation_completed.emit(operation_id, True, f"تم إنشاء المجلد: {os.path.basename(folder_path)}")
            
            logger.info(f"Folder created: {folder_path}")
            return True
            
        except Exception as e:
            error_msg = f"فشل في إنشاء المجلد: {e}"
            self.error_occurred.emit(error_msg)
            self.operation_completed.emit(operation_id, False, error_msg)
            logger.error(error_msg)
            return False
    
    def search_files(self, pattern: str, root_path: str = None, 
                    include_content: bool = False,
                    file_extensions: List[str] = None) -> str:
        """البحث في الملفات"""
        search_id = self._generate_operation_id()
        
        if not root_path:
            root_path = self.current_folder or os.path.expanduser("~")
        
        # تشغيل البحث في خيط منفصل
        def search_thread():
            try:
                results = self.search_engine.search_files(
                    root_path, pattern, include_content, file_extensions
                )
                self.search_completed.emit(search_id, results)
            except Exception as e:
                logger.error(f"Search error: {e}")
                self.search_completed.emit(search_id, [])
        
        threading.Thread(target=search_thread, daemon=True).start()
        return search_id
    
    def compare_files(self, file1: str, file2: str) -> Dict[str, Any]:
        """مقارنة ملفين"""
        return self.comparison_engine.compare_files(file1, file2)
    
    def add_recent_file(self, file_path: str):
        """إضافة ملف إلى القائمة الأخيرة"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        self.recent_files.insert(0, file_path)
        
        # الحفاظ على حد أقصى 20 ملف
        if len(self.recent_files) > 20:
            self.recent_files = self.recent_files[:20]
    
    def add_recent_folder(self, folder_path: str):
        """إضافة مجلد إلى القائمة الأخيرة"""
        if folder_path in self.recent_folders:
            self.recent_folders.remove(folder_path)
        
        self.recent_folders.insert(0, folder_path)
        
        # الحفاظ على حد أقصى 10 مجلدات
        if len(self.recent_folders) > 10:
            self.recent_folders = self.recent_folders[:10]
    
    def add_bookmark(self, path: str, name: str = None):
        """إضافة إشارة مرجعية"""
        if not name:
            name = os.path.basename(path)
        
        bookmark = {'path': path, 'name': name, 'timestamp': time.time()}
        
        # إزالة الإشارة إذا كانت موجودة
        self.bookmarks = [b for b in self.bookmarks if b['path'] != path]
        
        self.bookmarks.append(bookmark)
    
    def remove_bookmark(self, path: str):
        """إزالة إشارة مرجعية"""
        self.bookmarks = [b for b in self.bookmarks if b['path'] != path]
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """الحصول على معلومات الملف"""
        try:
            if not os.path.exists(file_path):
                return {'error': 'الملف غير موجود'}
            
            stat = os.stat(file_path)
            info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'accessed': stat.st_atime,
                'is_file': os.path.isfile(file_path),
                'is_dir': os.path.isdir(file_path),
                'extension': os.path.splitext(file_path)[1],
                'permissions': oct(stat.st_mode)[-3:],
                'mime_type': mimetypes.guess_type(file_path)[0],
                'is_open': file_path in self.open_files
            }
            
            if file_path in self.open_files:
                file_data = self.open_files[file_path]
                info.update({
                    'encoding': file_data['encoding'],
                    'line_ending': file_data['line_ending'],
                    'modified_in_editor': file_data['modified'],
                    'externally_modified': file_data['externally_modified'],
                    'externally_deleted': file_data['externally_deleted']
                })
            
            return info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_folder_contents(self, folder_path: str, 
                           show_hidden: bool = False,
                           sort_by: str = 'name') -> Dict[str, List[Dict]]:
        """الحصول على محتويات المجلد"""
        try:
            if not os.path.isdir(folder_path):
                return {'files': [], 'folders': [], 'error': 'المجلد غير صالح'}
            
            items = os.listdir(folder_path)
            files = []
            folders = []
            
            for item in items:
                if not show_hidden and item.startswith('.'):
                    continue
                
                item_path = os.path.join(folder_path, item)
                
                try:
                    stat = os.stat(item_path)
                    item_info = {
                        'name': item,
                        'path': item_path,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'is_file': os.path.isfile(item_path),
                        'is_dir': os.path.isdir(item_path),
                        'extension': os.path.splitext(item)[1] if os.path.isfile(item_path) else '',
                        'mime_type': mimetypes.guess_type(item_path)[0] if os.path.isfile(item_path) else None
                    }
                    
                    if item_info['is_file']:
                        files.append(item_info)
                    else:
                        folders.append(item_info)
                        
                except OSError:
                    continue
            
            # ترتيب العناصر
            sort_key = lambda x: x[sort_by] if sort_by in x else x['name']
            files.sort(key=sort_key)
            folders.sort(key=sort_key)
            
            return {'files': files, 'folders': folders}
            
        except Exception as e:
            return {'files': [], 'folders': [], 'error': str(e)}
    
    def undo_last_operation(self) -> bool:
        """التراجع عن العملية الأخيرة"""
        operation = self.history_manager.undo()
        if not operation:
            return False
        
        try:
            # تنفيذ التراجع حسب نوع العملية
            if operation.operation_type == 'delete':
                # لا يمكن التراجع عن الحذف بدون نسخة احتياطية
                logger.warning("Cannot undo delete operation without backup")
                return False
            
            elif operation.operation_type == 'rename':
                # إعادة التسمية إلى الاسم القديم
                if os.path.exists(operation.destination):
                    os.rename(operation.destination, operation.source)
                    return True
            
            elif operation.operation_type == 'move':
                # إعادة النقل
                if os.path.exists(operation.destination):
                    shutil.move(operation.destination, operation.source)
                    return True
            
            elif operation.operation_type == 'copy':
                # حذف النسخة
                if os.path.exists(operation.destination):
                    if os.path.isdir(operation.destination):
                        shutil.rmtree(operation.destination)
                    else:
                        os.remove(operation.destination)
                    return True
            
            elif operation.operation_type == 'create':
                # حذف الملف المنشأ
                if os.path.exists(operation.source):
                    os.remove(operation.source)
                    return True
            
        except Exception as e:
            logger.error(f"Undo operation failed: {e}")
            return False
        
        return False
    
    def redo_last_operation(self) -> bool:
        """إعادة العملية التالية"""
        operation = self.history_manager.redo()
        if not operation:
            return False
        
        try:
            # تنفيذ الإعادة حسب نوع العملية
            if operation.operation_type == 'create':
                content = operation.metadata.get('content', '')
                with open(operation.source, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            elif operation.operation_type == 'rename':
                if os.path.exists(operation.source):
                    os.rename(operation.source, operation.destination)
                    return True
            
            elif operation.operation_type == 'move':
                if os.path.exists(operation.source):
                    shutil.move(operation.source, operation.destination)
                    return True
            
            elif operation.operation_type == 'copy':
                if os.path.exists(operation.source):
                    if os.path.isdir(operation.source):
                        shutil.copytree(operation.source, operation.destination)
                    else:
                        shutil.copy2(operation.source, operation.destination)
                    return True
            
        except Exception as e:
            logger.error(f"Redo operation failed: {e}")
            return False
        
        return False
    
    def _auto_save_all(self):
        """حفظ تلقائي لجميع الملفات المعدلة"""
        if not self.auto_save_enabled:
            return
        
        for file_path, file_info in self.open_files.items():
            if file_info['modified'] and not file_info['externally_modified']:
                try:
                    self.save_file(file_path, file_info['content'], file_info['encoding'])
                    logger.debug(f"Auto-saved: {file_path}")
                except Exception as e:
                    logger.error(f"Auto-save failed for {file_path}: {e}")
    
    def _create_backup(self, file_path: str):
        """إنشاء نسخة احتياطية"""
        try:
            if not os.path.exists(file_path):
                return
            
            # إنشاء مجلد النسخ الاحتياطية
            backup_dir = os.path.join(os.path.dirname(file_path), '.backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # اسم النسخة الاحتياطية مع الطابع الزمني
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            file_name = os.path.basename(file_path)
            backup_name = f"{file_name}.{timestamp}.backup"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # نسخ الملف
            shutil.copy2(file_path, backup_path)
            
            # تنظيف النسخ الاحتياطية القديمة
            self._cleanup_old_backups(backup_dir, file_name)
            
            logger.debug(f"Backup created: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
    
    def _cleanup_old_backups(self, backup_dir: str, file_name: str):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            # البحث عن النسخ الاحتياطية لهذا الملف
            backup_files = []
            for item in os.listdir(backup_dir):
                if item.startswith(file_name + '.') and item.endswith('.backup'):
                    backup_path = os.path.join(backup_dir, item)
                    backup_files.append((backup_path, os.path.getmtime(backup_path)))
            
            # ترتيب حسب التاريخ (الأحدث أولاً)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # حذف النسخ الزائدة
            if len(backup_files) > self.max_backup_files:
                for backup_path, _ in backup_files[self.max_backup_files:]:
                    os.remove(backup_path)
                    logger.debug(f"Removed old backup: {backup_path}")
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def _detect_file_encoding(self, file_path: str) -> str:
        """اكتشاف ترميز الملف"""
        try:
            import chardet
            
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # قراءة أول 10KB
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                
                if encoding and result['confidence'] > 0.7:
                    return encoding
                    
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Encoding detection failed for {file_path}: {e}")
        
        # الافتراضي
        return self.file_encoding
    
    def _detect_encoding(self, content: str) -> str:
        """اكتشاف ترميز المحتوى"""
        try:
            # محاولة ترميزات مختلفة
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1256']
            
            for encoding in encodings:
                try:
                    content.encode(encoding)
                    return encoding
                except UnicodeEncodeError:
                    continue
                    
        except Exception:
            pass
        
        return self.file_encoding
    
    def _detect_line_ending(self, content: str) -> str:
        """اكتشاف نوع نهاية السطر"""
        if '\r\n' in content:
            return 'crlf'
        elif '\r' in content:
            return 'cr'
        elif '\n' in content:
            return 'lf'
        else:
            return 'lf'  # افتراضي
    
    def _detect_file_type(self, file_path: str) -> str:
        """اكتشاف نوع الملف"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        type_mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.md': 'markdown',
            '.txt': 'text',
            '.sql': 'sql',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        
        return type_mapping.get(ext, 'unknown')
    
    def _generate_operation_id(self) -> str:
        """توليد معرف عملية"""
        self.operation_counter += 1
        return f"op_{self.operation_counter}_{int(time.time())}"
    
    def get_recent_files(self) -> List[str]:
        """الحصول على الملفات الأخيرة"""
        # تصفية الملفات غير الموجودة
        self.recent_files = [f for f in self.recent_files if os.path.exists(f)]
        return self.recent_files.copy()
    
    def get_recent_folders(self) -> List[str]:
        """الحصول على المجلدات الأخيرة"""
        # تصفية المجلدات غير الموجودة
        self.recent_folders = [f for f in self.recent_folders if os.path.exists(f)]
        return self.recent_folders.copy()
    
    def get_bookmarks(self) -> List[Dict[str, Any]]:
        """الحصول على الإشارات المرجعية"""
        # تصفية الإشارات غير الموجودة
        self.bookmarks = [b for b in self.bookmarks if os.path.exists(b['path'])]
        return self.bookmarks.copy()
    
    def get_open_files(self) -> Dict[str, Dict[str, Any]]:
        """الحصول على الملفات المفتوحة"""
        return self.open_files.copy()
    
    def is_file_modified(self, file_path: str) -> bool:
        """فحص ما إذا كان الملف معدلاً"""
        if file_path not in self.open_files:
            return False
        return self.open_files[file_path]['modified']
    
    def mark_file_modified(self, file_path: str, modified: bool = True):
        """تحديد حالة تعديل الملف"""
        if file_path in self.open_files:
            self.open_files[file_path]['modified'] = modified
    
    def get_operation_history(self) -> List[FileOperation]:
        """الحصول على تاريخ العمليات"""
        return self.history_manager.get_history()
    
    def can_undo(self) -> bool:
        """فحص إمكانية التراجع"""
        return self.history_manager.can_undo()
    
    def can_redo(self) -> bool:
        """فحص إمكانية الإعادة"""
        return self.history_manager.can_redo()
    
    def cleanup(self):
        """تنظيف الموارد"""
        # إيقاف مراقبة الملفات
        self.stop_file_watching()
        
        # إيقاف مؤقت الحفظ التلقائي
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
        
        # حفظ الإعدادات
        self.save_settings()
        
        logger.info("Enhanced File Manager cleaned up")
    
    def __del__(self):
        """مدمر الكائن"""
        self.cleanup()

