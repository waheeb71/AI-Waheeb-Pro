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
        self.operation_type = operation_type  # copy, move, delete, create, create_folder, save, undo, redo
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
    error_occurred_in_thread = pyqtSignal(str)
    file_changed = pyqtSignal(str, dict)  # file_path, change_info
    file_added = pyqtSignal(str, dict)
    file_removed = pyqtSignal(str, dict)
    directory_changed = pyqtSignal(str, dict)
    
    def __init__(self, watch_paths: List[str]):
        super().__init__()
        self.watch_paths = watch_paths
        self.is_watching = False
        self.file_states = {} # {file_path: {'mtime': float, 'size': int, 'mode': int, 'exists': bool}}
        self.check_interval = 1.0  # ثانية
        self.ignore_patterns = {'.git', '__pycache__', 'node_modules', '.DS_Store', '.pytest_cache', '.venv', '.idea'}
        
    def run(self):
        """تشغيل مراقب الملفات"""
        self.is_watching = True
        try:
            logger.info("FileWatcherThread: Starting initial scan...")
            self.scan_initial_state()
            logger.info("FileWatcherThread: Initial scan complete. Starting periodic checks.")
            while self.is_watching:
                self.check_changes()
                self.msleep(int(self.check_interval * 1000))
        except Exception as e:
            error_msg = f"خطأ فادح غير مُعالج في مراقب الملفات (FileWatcherThread): {e}"
            logger.critical(error_msg, exc_info=True)
            self.error_occurred_in_thread.emit(error_msg)
        finally:
            self.is_watching = False
            logger.info("FileWatcherThread: توقف الخيط بسبب خطأ أو إيقاف عادي.")

    def stop_watching(self):
        """إيقاف المراقبة"""
        self.is_watching = False
        self.quit()
        self.wait() # انتظر حتى ينتهي الخيط بشكل صحيح
        logger.info("FileWatcherThread: Watching stopped.")
        
    def add_watch_path(self, path: str):
        """إضافة مسار للمراقبة"""
        if path not in self.watch_paths:
            self.watch_paths.append(path)
            if self.is_watching: # إذا كان المراقب يعمل بالفعل، قم بمسح الحالة الأولية لهذا المسار
                self.scan_path_initial_state(path)
                logger.debug(f"FileWatcherThread: Added path '{path}' for live watching.")
            else:
                logger.debug(f"FileWatcherThread: Added path '{path}' to watch list (watcher not active yet).")
        
    def remove_watch_path(self, path: str):
        """إزالة مسار من المراقبة"""
        if path in self.watch_paths:
            self.watch_paths.remove(path)
            # إزالة حالات الملفات المرتبطة بهذا المسار
            to_remove = [fp for fp in self.file_states.keys() if fp.startswith(path)]
            for fp in to_remove:
                del self.file_states[fp]
            logger.debug(f"FileWatcherThread: Removed path '{path}' from watching.")
            
    def scan_initial_state(self):
        """فحص الحالة الأولية لجميع المسارات"""
        self.file_states.clear() # مسح الحالات القديمة قبل الفحص الجديد
        for path in self.watch_paths:
            self.scan_path_initial_state(path)
            
    def scan_path_initial_state(self, path: str):
        """فحص الحالة الأولية لمسار معين"""
        if not os.path.exists(path):
            logger.warning(f"FileWatcherThread: Initial scan target '{path}' does not exist.")
            return
        
        try:
            if os.path.isfile(path):
                self._scan_file(path)
            else: # إذا كان مجلد
                # استخدام os.walk لتغطية جميع الملفات والمجلدات الفرعية
                for root, dirs, files in os.walk(path):
                    # تصفية المجلدات المتجاهلة في مكانها
                    dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
                    
                    for file_name in files:
                        # تصفية الملفات المخفية أو الملفات الخاصة التي يجب تجاهلها
                        if file_name.startswith('.') and file_name not in ['.gitignore', '.env']:
                            continue
                        
                        file_path = os.path.join(root, file_name)
                        self._scan_file(file_path)
        except (OSError, PermissionError) as e:
            logger.warning(f"FileWatcherThread: Cannot scan path '{path}' due to permission or OS error: {e}")
            
    def _scan_file(self, file_path: str):
        """فحص ملف واحد وتحديث حالته المخزنة"""
        try:
            # التحقق من وجود المسار قبل محاولة stat
            if not os.path.exists(file_path):
                # إذا كان الملف غير موجود، تأكد من إزالته من الحالات المخزنة
                if file_path in self.file_states:
                    del self.file_states[file_path]
                return

            stat = os.stat(file_path)
            self.file_states[file_path] = {
                'mtime': stat.st_mtime,
                'size': stat.st_size,
                'mode': stat.st_mode,
                'exists': True # دائماً True عند إضافة أو تحديث
            }
        except (OSError, PermissionError) as e:
            logger.warning(f"FileWatcherThread: Could not get state for file '{file_path}': {e}")
            # إذا لم نتمكن من قراءة الملف، نعتبره غير موجود لحالات التتبع
            if file_path in self.file_states:
                del self.file_states[file_path]
            
    def check_changes(self):
        """فحص التغييرات في الملفات والمجلدات"""
        current_files_and_dirs = set()
        
        # جمع الحالات الحالية وإطلاق إشارات التعديل
        for watch_path in self.watch_paths:
            if not os.path.exists(watch_path):
                # إذا اختفى مسار المراقبة بالكامل (مجلد الجذر)
                if watch_path in self.file_states: # تحقق إذا كان المجلد الجذر نفسه تمت إزالته
                    self.file_removed.emit(watch_path, {'type': 'removed', 'is_dir': True, 'timestamp': time.time()})
                    del self.file_states[watch_path]
                continue
                
            try:
                if os.path.isfile(watch_path):
                    current_files_and_dirs.add(watch_path)
                    self._check_file_changes_and_emit(watch_path)
                else:
                    for root, dirs, files in os.walk(watch_path):
                        # أضف المجلد نفسه للمراقبة (للتأكد من التغييرات في محتواه)
                        current_files_and_dirs.add(root)
                        # تصفية المجلدات المتجاهلة
                        dirs[:] = [d for d in dirs if d not in self.ignore_patterns]
                        
                        for file_name in files:
                            # تصفية الملفات المخفية أو الخاصة
                            if file_name.startswith('.') and file_name not in ['.gitignore', '.env']:
                                continue
                            file_path = os.path.join(root, file_name)
                            current_files_and_dirs.add(file_path)
                            self._check_file_changes_and_emit(file_path)
            except (OSError, PermissionError) as e:
                logger.warning(f"FileWatcherThread: Cannot check path '{watch_path}' due to permission or OS error during change check: {e}")
                continue # تخطى هذا المسار
        
        # فحص الملفات/المجلدات التي تم حذفها
        removed_paths = set(self.file_states.keys()) - current_files_and_dirs
        for path in removed_paths:
            if path in self.file_states: # تأكد أنها لم تُحذف بالفعل في إطار زمني ضيق
                change_info = {
                    'type': 'removed',
                    'timestamp': time.time(),
                    'is_dir': os.path.isdir(path) if Path(path).exists() else self.file_states[path].get('is_dir_before_delete', False), # حاول التخمين إذا كان مجلد
                    'previous_state': self.file_states[path].copy()
                }
                self.file_removed.emit(path, change_info)
                logger.debug(f"File/Dir removed: {path}")
                del self.file_states[path] # أزلها من الحالات المخزنة
                
        # فحص الملفات/المجلدات التي تم إضافتها أو تعديلها
        for path in current_files_and_dirs:
            if path not in self.file_states:
                # إذا كان مسارًا جديدًا
                try:
                    stat = os.stat(path)
                    is_dir = os.path.isdir(path)
                    current_state = {
                        'mtime': stat.st_mtime,
                        'size': stat.st_size if not is_dir else 0, # لا حجم للمجلدات
                        'mode': stat.st_mode,
                        'exists': True,
                        'is_dir_before_delete': is_dir # لتخمين النوع عند الحذف
                    }
                    self.file_states[path] = current_state
                    change_info = {
                        'type': 'added',
                        'timestamp': time.time(),
                        'is_dir': is_dir,
                        'current_state': current_state
                    }
                    self.file_added.emit(path, change_info)
                    logger.debug(f"File/Dir added: {path}")
                except (OSError, PermissionError):
                    continue # قد يكون الملف قد اختفى للتو
            else:
                self._check_file_changes_and_emit(path) # تحقق من التعديلات للملفات الموجودة
                
    def _check_file_changes_and_emit(self, path: str):
        """فحص تغييرات ملف/مجلد معين وإطلاق الإشارة المناسبة"""
        try:
            current_stat = os.stat(path)
            is_dir = os.path.isdir(path)
            current_state = {
                'mtime': current_stat.st_mtime,
                'size': current_stat.st_size if not is_dir else 0,
                'mode': current_stat.st_mode,
                'exists': True,
                'is_dir_before_delete': is_dir
            }
            
            if path not in self.file_states:
                # هذا السيناريو يجب أن يُعالج بواسطة جزء إضافة الملفات في `check_changes`،
                # ولكن كتدبير وقائي، إذا وجدناه هنا ولم يكن في `file_states`
                self.file_states[path] = current_state
                change_info = {'type': 'added', 'timestamp': time.time(), 'is_dir': is_dir, 'current_state': current_state}
                self.file_added.emit(path, change_info)
                logger.debug(f"File/Dir added (late detection): {path}")
                return

            previous_state = self.file_states[path]
            
            # تحقق من التغييرات: الحجم أو وقت التعديل
            if (current_state['mtime'] != previous_state['mtime'] or 
                (not is_dir and current_state['size'] != previous_state['size']) or # فقط للملفات
                current_state['mode'] != previous_state['mode']):
                
                self.file_states[path] = current_state # تحديث الحالة المخزنة
                
                change_info = {
                    'type': 'modified',
                    'timestamp': time.time(),
                    'is_dir': is_dir,
                    'previous_state': previous_state,
                    'current_state': current_state,
                    'size_changed': (not is_dir and current_state['size'] != previous_state['size']),
                    'time_changed': current_state['mtime'] != previous_state['mtime'],
                    'mode_changed': current_state['mode'] != previous_state['mode']
                }
                
                if is_dir:
                    self.directory_changed.emit(path, change_info)
                    logger.debug(f"Directory changed: {path}")
                else:
                    self.file_changed.emit(path, change_info)
                    logger.debug(f"File modified: {path}")

        except (OSError, PermissionError) as e:
            # إذا كان هناك خطأ في الوصول، قد يكون الملف محذوفًا أو غير متاح
            if path in self.file_states:
                change_info = {
                    'type': 'removed',
                    'timestamp': time.time(),
                    'is_dir': self.file_states[path].get('is_dir_before_delete', False),
                    'previous_state': self.file_states[path].copy()
                }
                self.file_removed.emit(path, change_info)
                logger.debug(f"File/Dir removed (via OSError): {path}")
                del self.file_states[path]
            logger.warning(f"FileWatcherThread: Error accessing '{path}' during change check: {e}")


# ---
# FileHistoryManager
# ---
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

# ---
# FileSearchEngine
# ---
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

# ---
# FileComparisonEngine
# ---
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

# ---
# UnifiedFileManager
# ---
class UnifiedFileManager(QObject):
    """مدير الملفات المحسن مع ميزات متقدمة"""
    
    # الإشارات
    # إشارات العمليات الأساسية على الملفات والمجلدات
    file_opened = pyqtSignal(str, str)  # file_path, content
    file_saved = pyqtSignal(str)  # file_path
    file_created = pyqtSignal(str, str)  # file_path, file_type
    file_deleted = pyqtSignal(str)  # file_path
    file_renamed = pyqtSignal(str, str)  # old_path, new_path
    file_copied = pyqtSignal(str, str)  # source_path, dest_path
    file_moved = pyqtSignal(str, str)  # source_path, dest_path
    folder_opened = pyqtSignal(str)  # folder_path
    folder_created = pyqtSignal(str)  # folder_path
    
    # إشارات التغييرات الخارجية (المكتشفة بواسطة FileWatcherThread)
    file_added = pyqtSignal(str, dict)       # path, change_info
    file_removed = pyqtSignal(str, dict)     # path, change_info
    file_changed_externally = pyqtSignal(str, dict) # path, change_info (for modifications)
    directory_changed = pyqtSignal(str, dict) # path, change_info (for folder contents changing)
    
    # إشارات أخرى متعلقة بالعمليات وحالة التطبيق
    error_occurred = pyqtSignal(str) # إشارة الخطأ
    project_opened = pyqtSignal(str, dict)  # project_path, project_info (قد تكون متطابقة مع folder_opened ولكن مع معلومات إضافية)
    operation_progress = pyqtSignal(str, float)  # operation_id, progress
    operation_completed = pyqtSignal(str, bool, str)  # operation_id, success, message
    search_completed = pyqtSignal(str, list)  # search_id, results
    file_output_ready = pyqtSignal(str) # لإخراج نتائج تشغيل الملفات مثلاً

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_project = None
        self.current_folder = None # سيتم تعيينه عند فتح مجلد
        self.open_files = {}  # file_path -> {'content': str, 'modified': bool, 'encoding': str, 'last_known_disk_content_hash': str}
        self.recent_files = []
        self.recent_folders = []
        self.output_process = None # لعمليات subprocess الجارية (مثل تشغيل ملف بايثون)
        self.bookmarks = []
        self.current_project_path = None # عادة ما يكون هو نفسه current_folder للمشاريع البسيطة
        
        # علامة لمنع إطلاق أحداث مراقب الملفات ذاتياً عند إجراء عمليات داخلية
        self._ignore_watcher_events = False 
        
        self.folder_history: List[str] = [] # لتتبع تاريخ المجلدات المفتوحة
        self.history_index: int = -1 # مؤشر للموقع الحالي في تاريخ المجلدات
        
        # المكونات المحسنة
        self.file_watcher_thread = None # سيتم تهيئة خيط المراقبة عند الحاجة
        self.history_manager = FileHistoryManager()
        self.search_engine = FileSearchEngine()
        self.comparison_engine = FileComparisonEngine()
        
        # إعدادات متقدمة
        self.auto_save_enabled = True
        self.auto_save_interval = 30  # ثانية
        self.backup_enabled = True
        self.max_backup_files = 10
        self.file_encoding = 'utf-8' # الترميز الافتراضي للملفات
        self.line_ending = 'auto'  # auto, lf, crlf, cr
        
        # عمليات الملفات الجارية (لتتبع التقدم والإشعارات)
        self.pending_operations = {}
        self.operation_counter = 0
        
        # مؤقت الحفظ التلقائي
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_all)
        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval * 1000)
        
        # تحميل الإعدادات من كائن التهيئة
        self.load_settings()
        
        logger.info("Enhanced File Manager initialized")
        
    def load_settings(self):
        """تحميل الإعدادات"""
        try:
            # تحميل الملفات والمجلدات الأخيرة والإشارات المرجعية
            self.recent_files = self.config.get('recent_files', [])
            self.recent_folders = self.config.get('recent_folders', [])
            self.bookmarks = self.config.get('bookmarks', [])
            
            # تحميل إعدادات إدارة الملفات
            self.auto_save_enabled = self.config.get('file_management.auto_save_enabled', True)
            self.auto_save_interval = self.config.get('file_management.auto_save_interval', 30)
            self.backup_enabled = self.config.get('file_management.backup_enabled', True)
            self.max_backup_files = self.config.get('file_management.max_backup_files', 10)
            self.file_encoding = self.config.get('file_management.file_encoding', 'utf-8')
            self.line_ending = self.config.get('file_management.line_ending', 'auto')
            
        except Exception as e:
            logger.warning(f"Failed to load settings in UnifiedFileManager: {e}")
            
    def save_settings(self):
        """حفظ الإعدادات"""
        try:
            self.config.set('recent_files', self.recent_files)
            self.config.set('recent_folders', self.recent_folders)
            self.config.set('bookmarks', self.bookmarks)
            self.config.set('file_management.auto_save_enabled', self.auto_save_enabled)
            self.config.set('file_management.auto_save_interval', self.auto_save_interval)
            self.config.set('file_management.backup_enabled', self.backup_enabled)
            self.config.set('file_management.max_backup_files', self.max_backup_files)
            self.config.set('file_management.file_encoding', self.file_encoding)
            self.config.set('file_management.line_ending', self.line_ending)
            # يجب عليك أيضاً استدعاء self.config.save() في مكان ما في التطبيق الرئيسي
            # لضمان حفظ هذه الإعدادات على القرص.
        except Exception as e:
            logger.warning(f"Failed to save settings in UnifiedFileManager: {e}")
            
    def _reset_ignore_watcher_flag(self):
        """إعادة تعيين علامة تجاهل أحداث المراقبة بعد فترة قصيرة."""
        self._ignore_watcher_events = False
        logger.debug("UnifiedFileManager: Watcher events are now being processed again.")

    def create_file_with_content(self, file_path: str, content: str = "", file_type: str = None) -> Optional[str]:
        """
        Creates a new file at the specified path with the given content.
        This is typically used for AI-generated content or programmatic file creation.
        Returns the file_path if successful, None otherwise.
        """
        operation_id = self._generate_operation_id()
        
        try:
            self._ignore_watcher_events = True # تجاهل حدث المراقبة الناتج عن هذه العملية
            # Ensure parent directory exists
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                
            # Write the file
            # Use 'file_encoding' from config if not provided, otherwise utf-8 as fallback
            encoding = self.file_encoding or 'utf-8'  
            with open(file_path, 'w', encoding=encoding, newline='') as f:
                f.write(content)
            
            # Add to open files (if the UI is expected to open it, or for internal tracking)
            file_hash = hashlib.md5(content.encode(encoding, errors='ignore')).hexdigest()
            self.open_files[file_path] = {
                'content': content,
                'modified': False,
                'encoding': encoding,
                'line_ending': self._detect_line_ending(content),
                'externally_modified': False,
                'externally_deleted': False,
                'last_known_editor_content': content,
                'last_known_disk_content_hash': file_hash
            }
            
            # Add to history
            operation = FileOperation('create', file_path, metadata={'content': content, 'ai_generated': True})
            self.history_manager.add_operation(operation)
            
            # Add to recent files
            self.add_recent_file(file_path)
            
            # Emit signals (important for UI update)
            self.file_created.emit(file_path, file_type or self._detect_file_type(file_path))
            self.operation_completed.emit(operation_id, True, f"تم إنشاء الملف بواسطة الذكاء الاصطناعي: {os.path.basename(file_path)}")
            
            logger.info(f"AI-generated file created: {file_path}")
            return file_path # Return the path on success
            
        except Exception as e:
            error_msg = f"فشل الذكاء الاصطناعي في إنشاء الملف: {e}"
            self.error_occurred.emit(error_msg)
            self.operation_completed.emit(operation_id, False, error_msg)
            logger.error(error_msg, exc_info=True)
            return None # Return None on failure
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag) # إعادة تعيين العلامة بعد فترة قصيرة
            
    def get_all_project_files(self) -> List[str]:
        """
        Returns a list of all file paths within the current project folder,
        excluding commonly ignored directories and files.
        """
        if not self.current_folder or not os.path.isdir(self.current_folder):
            logger.warning("UnifiedFileManager: No current project folder set or it does not exist.")
            return []

        all_files = []
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.vscode', '.idea', '.venv', 'build', 'dist', 'temp', '.DS_Store', 'bin', 'obj'} # تم إضافة 'bin', 'obj'
        ignore_files = {'.gitignore', '.env', 'Thumbs.db', '.gitattributes', 'LICENSE', 'README.md'} # تم إضافة بعض الملفات
        
        # يمكن إضافة منطق Git ignore هنا لاحقاً إذا كان مطلوباً
        
        try:
            for root, dirs, files in os.walk(self.current_folder, topdown=True):
                # Exclude directories that match ignore_dirs
                dirs[:] = [d for d in dirs if d not in ignore_dirs]

                for file_name in files:
                    if file_name in ignore_files:
                        continue
                    # Optionally, add a check for hidden files (starting with '.') if not already handled by ignore_files
                    if file_name.startswith('.') and file_name not in ignore_files:
                        continue

                    file_path = os.path.join(root, file_name)
                    all_files.append(file_path)
            logger.info(f"UnifiedFileManager: Retrieved {len(all_files)} project files from {self.current_folder}.")
            return all_files
        except PermissionError as e:
            logger.error(f"UnifiedFileManager: Permission denied while accessing {self.current_folder}: {e}")
            self.error_occurred.emit(f"Permission denied to access project files: {e}")
            return []
        except Exception as e:
            logger.critical(f"UnifiedFileManager: An unexpected error occurred while getting project files: {e}", exc_info=True)
            self.error_occurred.emit(f"Failed to retrieve project files: {e}")
            return []
            
    def open_folder(self, folder_path: str = None) -> bool:
        """
        يفتح مجلد المشروع، إما من مسار معين أو من خلال مربع حوار (إذا لم يُحدد مسار).
        يضيف المجلد إلى سجل المجلدات ويُحدث شجرة الملفات.
        """
        if not folder_path:
            # هذا هو المكان الصحيح لعرض QFileDialog.
            # هنا نستخدم self.current_folder الخاص بـ EnhancedFileManager كمسار بدء افتراضي.
            selected_folder = QFileDialog.getExistingDirectory(
                None, "اختر مجلد المشروع", self.current_folder or os.path.expanduser("~")
            )
            if selected_folder:
                folder_path = selected_folder
            else:
                logger.info("EnhancedFileManager: تم إلغاء اختيار المجلد من قبل المستخدم.")
                return False # المستخدم ألغى العملية

        if os.path.isdir(folder_path):
            self.current_folder = folder_path 
            self.current_project_path = folder_path  # Project path is often the same as the folder
            self.add_recent_folder(folder_path)  
            
            # بدء مراقبة الملفات للمجلد الجديد.
            # ستقوم FileWatcherThread بمراقبة هذا المجلد ومحتوياته.
            self.start_file_watching([folder_path])  

            self.folder_opened.emit(folder_path) # إطلاق الإشارة لتحديث UI
            logger.info(f"EnhancedFileManager: تم فتح المجلد: {folder_path}")
            return True
        else:
            error_msg = f"فشل في فتح المجلد: المسار غير صالح أو لا يوجد: {folder_path}"
            self.error_occurred.emit(error_msg) # UnifiedFileManager يطلق إشارة الخطأ
            logger.error(f"EnhancedFileManager: {error_msg}")
            return False
            
    def set_current_folder(self, folder_path: str) -> bool:
        """تعيين المجلد الحالي"""
        if not os.path.isdir(folder_path):
            self.error_occurred.emit(f"المجلد غير صالح: {folder_path}")
            return False
            
        self.current_folder = folder_path
        self.current_project_path = folder_path # تحديث مسار المشروع أيضاً
        self.add_recent_folder(folder_path)
        
        # بدء مراقبة الملفات
        self.start_file_watching([folder_path])
        
        self.folder_opened.emit(folder_path)
        logger.info(f"Current folder set to: {folder_path}")
        return True
        
    def run_file(self, file_path: str) -> bool:
        """
        يقوم بتشغيل ملف معين باستخدام مترجم مناسب (مثل Python).
        يعالج الإخراج والأخطاء.
        """
        if not os.path.exists(file_path):
            self.error_occurred.emit(f"الملف غير موجود للتشغيل: {file_path}")
            return False

        if not os.path.isfile(file_path):
            self.error_occurred.emit(f"المسار ليس ملفًا قابلاً للتشغيل: {file_path}")
            return False

        # تحديد المترجم بناءً على امتداد الملف
        _, ext = os.path.splitext(file_path)
        interpreter = None
        if ext.lower() == '.py':
            interpreter = sys.executable  # يستخدم مترجم بايثون الحالي
        elif ext.lower() == '.js':
            # ستحتاج إلى التأكد من أن Node.js مثبت ومتاح في PATH
            interpreter = 'node'
        elif ext.lower() in ('.sh', '.bash'):
            if platform.system() == "Windows":
                self.error_occurred.emit("لا يمكن تشغيل ملفات Bash/Shell مباشرة على Windows بشكل افتراضي.")
                return False
            interpreter = 'bash' # أو 'sh'
        elif ext.lower() == '.html':
            # لا يمكن "تشغيل" ملف HTML مباشرة كبرنامج تنفيذي. يمكن فتحه بمتصفح.
            self.error_occurred.emit(f"الملف {file_path} هو ملف HTML. لفتحه، استخدم 'فتح في مستكشف الملفات' ثم المتصفح الافتراضي.")
            return False
        # أضف المزيد من المترجمات حسب الحاجة (C++, Java, etc.)

        if not interpreter:
            self.error_occurred.emit(f"لا يوجد مترجم معروف للملف من النوع: {ext}")
            return False

        try:
            # لإدارة العمليات الطويلة ومنع التعليق
            if self.output_process and self.output_process.poll() is None:
                # إذا كانت هناك عملية سابقة لا تزال قيد التشغيل
                self.error_occurred.emit("عملية تشغيل أخرى لا تزال قيد التنفيذ. الرجاء الانتظار أو إيقافها.")
                return False

            
            logger.info(f"UnifiedFileManager: Running file: {file_path}")

            # تشغيل العملية في الخلفية والتقاط الإخراج
            # Popen يسمح بالتشغيل غير المتزامن
            self.output_process = subprocess.Popen(
                [interpreter, file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # يعامل الإخراج كنص، وليس بايت
                encoding='utf-8',
                errors='replace', # لاستبدال الأحرف التي لا يمكن فك ترميزها
                cwd=os.path.dirname(file_path) # تشغيل من مجلد الملف
            )

            # بدء مؤقت لقراءة الإخراج بشكل دوري
            QTimer.singleShot(100, self._read_process_output)
            
            return True

        except FileNotFoundError:
            self.error_occurred.emit(f"المترجم '{interpreter}' غير موجود. تأكد من تثبيته وإضافته إلى متغير PATH.")
            logger.error(f"UnifiedFileManager: Interpreter not found: {interpreter}")
            return False
        except Exception as e:
            self.error_occurred.emit(f"فشل تشغيل الملف: {str(e)}")
            logger.error(f"UnifiedFileManager: Error running file {file_path}: {e}", exc_info=True)
            return False

    def _read_process_output(self):
        """
        يقرأ إخراج العملية ويطلقه كإشارات.
        """
        if self.output_process and self.output_process.poll() is None: # العملية لا تزال تعمل
            stdout_line = self.output_process.stdout.readline()
            stderr_line = self.output_process.stderr.readline()

            if stdout_line:
                self.file_output_ready.emit(stdout_line.strip())
            if stderr_line:
                self.file_output_ready.emit(f"خطأ: {stderr_line.strip()}")

            # استدعاء هذه الدالة مرة أخرى حتى تنتهي العملية
            QTimer.singleShot(100, self._read_process_output)
        elif self.output_process: # العملية انتهت
            # قراءة أي إخراج متبقي بعد انتهاء العملية
            remaining_stdout = self.output_process.stdout.read()
            remaining_stderr = self.output_process.stderr.read()

            if remaining_stdout:
                self.file_output_ready.emit(remaining_stdout.strip())
            if remaining_stderr:
                self.file_output_ready.emit(f"خطأ: {remaining_stderr.strip()}")

            return_code = self.output_process.returncode
            if return_code == 0:
              
                logger.info(f"UnifiedFileManager: File ran successfully. Exit code: {return_code}")
            else:
               
                logger.error(f"UnifiedFileManager: File failed to run. Exit code: {return_code}")
            self.output_process = None # إعادة تعيين العملية
            
    def start_file_watching(self, paths: List[str]):
        """
        يبدأ خيط مراقبة الملفات للمسارات المحددة.
        يتم إنشاء خيط جديد إذا لم يكن موجوداً أو يتم تحديث مسارات المراقبة.
        """
        try:
            if self.file_watcher_thread and self.file_watcher_thread.isRunning():
                # إذا كان الخيط موجودًا، قم بإيقافه أولاً
                self.file_watcher_thread.stop_watching()
                self.file_watcher_thread.wait() # انتظر حتى ينتهي الخيط القديم
                self.file_watcher_thread = None # إزالة المرجع القديم

            # إنشاء خيط مراقبة جديد
            self.file_watcher_thread = FileWatcherThread(paths)
            
            # توصيل إشارات المراقب الداخلية إلى دوال المعالجة الوسيطة في UnifiedFileManager
            self.file_watcher_thread.file_changed.connect(self._handle_internal_file_changed)
            self.file_watcher_thread.file_added.connect(self._handle_internal_file_added)
            self.file_watcher_thread.file_removed.connect(self._handle_internal_file_removed)
            self.file_watcher_thread.directory_changed.connect(self._handle_internal_directory_changed)
            self.file_watcher_thread.error_occurred_in_thread.connect(self.error_occurred.emit) # لإطلاق أخطاء المراقب إلى UI
            
            self.file_watcher_thread.start() # بدء الخيط، مما سيؤدي إلى استدعاء run()
            logger.info(f"UnifiedFileManager: File watcher started for paths: {paths}")
        except Exception as e:
            error_msg = f"Error starting file watcher: {e}"
            logger.critical(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)
            
    def _handle_internal_file_changed(self, file_path: str, change_info: dict):
        """وسيط للتعامل مع إشارة تغيير ملف من المراقب الداخلي."""
        if self._ignore_watcher_events:
            logger.debug(f"UnifiedFileManager: Ignoring self-initiated file_changed event for: {file_path}")
            return
        # أعد إطلاق الإشارة للمستمعين الخارجيين (مثل FileTree)
        self.file_changed_externally.emit(file_path, change_info)
        
        # إذا كان الملف مفتوحاً في المحرر، قم بتحديث حالته لتنبيه UI
        if file_path in self.open_files:
            # يمكن هنا مقارنة محتوى الملف على القرص مع محرر لتحديد ما إذا كان "معدلاً خارجياً"
            # ومعالجة التعارضات. حالياً، نكتفي بتحديد العلامة.
            self.open_files[file_path]['externally_modified'] = True
            logger.info(f"UnifiedFileManager: File '{file_path}' externally modified. Marked for refresh.")

    def _handle_internal_file_added(self, file_path: str, change_info: dict):
        """وسيط للتعامل مع إشارة إضافة ملف من المراقب الداخلي."""
        if self._ignore_watcher_events:
            logger.debug(f"UnifiedFileManager: Ignoring self-initiated file_added event for: {file_path}")
            return
        # أعد إطلاق الإشارة للمستمعين الخارجيين (مثل FileTree)
        self.file_added.emit(file_path, change_info)
        logger.info(f"UnifiedFileManager: File added externally: {file_path}")

    def _handle_internal_file_removed(self, file_path: str, change_info: dict):
        """وسيط للتعامل مع إشارة حذف ملف من المراقب الداخلي."""
        if self._ignore_watcher_events:
            logger.debug(f"UnifiedFileManager: Ignoring self-initiated file_removed event for: {file_path}")
            return
        # أعد إطلاق الإشارة للمستمعين الخارجيين (مثل FileTree)
        self.file_removed.emit(file_path, change_info)
        logger.info(f"UnifiedFileManager: File removed externally: {file_path}")
        
        # إذا كان الملف مفتوحاً، قم بتحديث حالته (لا داعي لإغلاقه هنا، بل في UI)
        if file_path in self.open_files:
            self.open_files[file_path]['externally_deleted'] = True
            logger.info(f"UnifiedFileManager: File '{file_path}' opened in editor, but deleted externally.")
            # يمكنك هنا إضافة منطق لتنبيه المستخدم بوجود ملف مفتوح تم حذفه

    def _handle_internal_directory_changed(self, path: str, change_info: dict):
        """وسيط للتعامل مع إشارة تغيير مجلد من المراقب الداخلي."""
        if self._ignore_watcher_events:
            logger.debug(f"UnifiedFileManager: Ignoring self-initiated directory_changed event for: {path}")
            return
        # أعد إطلاق الإشارة للمستمعين الخارجيين (مثل FileTree)
        self.directory_changed.emit(path, change_info)
        logger.info(f"UnifiedFileManager: Directory changed externally: {path}")

    def stop_file_watching(self):
        """إيقاف مراقبة الملفات"""
        if self.file_watcher_thread:
            self.file_watcher_thread.stop_watching()
            self.file_watcher_thread.wait() # انتظر حتى ينتهي الخيط
            self.file_watcher_thread = None
            logger.info("UnifiedFileManager: File watcher stopped.")
        
    def create_file(self, file_path: str, content: str = "", file_type: str = None) -> str:
        """إنشاء ملف جديد (واجهة عامة)"""
        operation_id = self._generate_operation_id()
        try:
            self._ignore_watcher_events = True
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
            return operation_id # نرجع الـ ID لتتبع العملية
            
        except Exception as e:
            error_msg = f"فشل في إنشاء الملف: {e}"
            self.error_occurred.emit(error_msg)
            self.operation_completed.emit(operation_id, False, error_msg)
            logger.error(error_msg)
            return operation_id
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag)
            
    def open_file(self, file_path: str = None) -> Optional[str]:
        """فتح ملف"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                None, # يجب استبدال None هنا بمرجع للـ parent Widget
                "فتح ملف",
                self.current_folder or os.path.expanduser("~"),
                "جميع الملفات (*.*)"
            )
            
            if not file_path:
                return None # المستخدم ألغى
                
        try:
            if not os.path.exists(file_path):
                self.error_occurred.emit(f"الملف غير موجود: {file_path}")
                return None
                
            # قراءة الملف
            encoding = self._detect_file_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            file_hash = hashlib.md5(content.encode(encoding, errors='ignore')).hexdigest() # حساب الهاش عند الفتح
            
            # إضافة إلى الملفات المفتوحة
            self.open_files[file_path] = {
                'content': content,
                'modified': False, # ليس معدلاً عند الفتح
                'encoding': encoding,
                'line_ending': self._detect_line_ending(content),
                'externally_modified': False,
                'externally_deleted': False,
                'last_known_editor_content': content, # تخزين محتوى المحرر عند الفتح
                'last_known_disk_content_hash': file_hash # تخزين هاش محتوى القرص عند الفتح
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
            self._ignore_watcher_events = True # تجاهل حدث المراقب
            # إنشاء نسخة احتياطية إذا كانت مفعلة
            encoding = encoding or self.file_encoding or 'utf-8'
            if self.backup_enabled and os.path.exists(file_path):
                self._create_backup(file_path)
                
          
            
            # التأكد من وجود المجلد الأب
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # كتابة الملف
            with open(file_path, 'w', encoding=encoding, newline='') as f:
                f.write(content)
            file_hash = hashlib.md5(content.encode(encoding, errors='ignore')).hexdigest() # حساب الهاش عند الحفظ
            
            # تحديث الملفات المفتوحة
            if file_path in self.open_files:
                self.open_files[file_path].update({
                    'content': content, 
                    'modified': False, # لم يعد معدلاً بعد الحفظ
                    'encoding': encoding,
                    'externally_modified': False, # لا يوجد تعديل خارجي بعد الحفظ
                    'last_known_editor_content': content, # تحديث آخر محتوى للمحرر
                    'last_known_disk_content_hash': file_hash # تحديث هاش محتوى القرص بعد الحفظ
                })
            else: # إذا لم يكن الملف مفتوحاً من قبل، أضفه (قد يحدث عند save_file_as)
                self.open_files[file_path] = {
                    'content': content,
                    'modified': False,
                    'encoding': encoding,
                    'line_ending': self._detect_line_ending(content),
                    'externally_modified': False,
                    'externally_deleted': False,
                    'last_known_editor_content': content,
                    'last_known_disk_content_hash': file_hash
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
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag) # إعادة تعيين العلامة بعد فترة قصيرة

    def save_file_as(self, current_path: str, content: str, new_path: str = None) -> Optional[str]:
        """حفظ ملف باسم جديد"""
        if not new_path:
            new_path, _ = QFileDialog.getSaveFileName(
                None, # يجب استبدال None هنا بمرجع للـ parent Widget
                "حفظ باسم",
                current_path or self.current_folder or os.path.expanduser("~"),
                "جميع الملفات (*.*)"
            )
            
            if not new_path:
                return None
        
        # عند الحفظ باسم، إذا كان الملف القديم مفتوحاً، أغلقه من open_files
        if current_path and current_path in self.open_files:
            del self.open_files[current_path] # إزالة الإدخال القديم

        if self.save_file(new_path, content):
            # إذا نجح الحفظ باسم، أضف الملف الجديد إلى الملفات المفتوحة
            # (تمت إضافته بالفعل بواسطة save_file)
            return new_path
        return None
        
    def close_file(self, file_path: str, save_if_modified: bool = True) -> bool:
        """إغلاق ملف"""
        if file_path not in self.open_files:
            return True # الملف ليس مفتوحاً بالفعل
            
        file_info = self.open_files[file_path]
        
        # فحص التعديلات
        if file_info['modified'] and save_if_modified:
            reply = QMessageBox.question(
                None, # يجب استبدال None هنا بمرجع للـ parent Widget
                'حفظ التغييرات',
                f'هل تريد حفظ التغييرات في "{os.path.basename(file_path)}"؟',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return False
            elif reply == QMessageBox.StandardButton.Yes:
                if not self.save_file(file_path, file_info['content']):
                    return False # فشل الحفظ
        
        # إزالة من الملفات المفتوحة
        del self.open_files[file_path]
        
        logger.info(f"File closed: {file_path}")
        return True
        
    def delete_file(self, file_path: str) -> bool:
        """حذف ملف أو مجلد"""
        operation_id = self._generate_operation_id()
        
        try:
            if not os.path.exists(file_path):
                self.error_occurred.emit(f"الملف غير موجود: {file_path}")
                return False
                
            # إغلاق الملف إذا كان مفتوحاً في المحرر (دون حفظ)
            if file_path in self.open_files:
                self.close_file(file_path, save_if_modified=False)
                # يجب إزالة الملف من open_files في close_file، لذا لا داعي لحذفه هنا مرة أخرى.
            
            self._ignore_watcher_events = True # تجاهل حدث المراقب
            # إنشاء نسخة احتياطية (إذا كان ملفاً)
            if self.backup_enabled and os.path.isfile(file_path): # Backup only for files
                self._create_backup(file_path)
            
            # حذف الملف أو المجلد
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
                logger.debug(f"Directory removed: {file_path}")
            else:
                os.remove(file_path)
                logger.debug(f"File removed: {file_path}")
            
            # إضافة إلى التاريخ (فقط لتتبع العملية، لا يمكن التراجع عن الحذف بدون سلة مهملات)
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
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag)
            
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """إعادة تسمية ملف أو مجلد"""
        operation_id = self._generate_operation_id()
        
        try:
            if not os.path.exists(old_path):
                self.error_occurred.emit(f"الملف غير موجود: {old_path}")
                return False
                
            if os.path.exists(new_path):
                self.error_occurred.emit(f"الملف موجود بالفعل: {new_path}")
                return False
            
            self._ignore_watcher_events = True # تجاهل حدث المراقب
            # إعادة التسمية
            os.rename(old_path, new_path)
            
            # تحديث الملفات المفتوحة
            if old_path in self.open_files:
                self.open_files[new_path] = self.open_files.pop(old_path)
                # تحديث مسار الملف المحفوظ في القاموس الداخلي
                self.open_files[new_path]['content'] = self.open_files[new_path]['content'] # المحتوى لا يتغير
                self.open_files[new_path]['modified'] = True # قد يحتاج المستخدم لحفظه بالاسم الجديد
            
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
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag)
            
    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """نسخ ملف أو مجلد"""
        operation_id = self._generate_operation_id()
        
        try:
            if not os.path.exists(source_path):
                self.error_occurred.emit(f"الملف المصدر غير موجود: {source_path}")
                return False
            
            # التأكد من وجود المجلد الهدف
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            self._ignore_watcher_events = True # تجاهل حدث المراقب
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
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag)
            
    def move_file(self, source_path: str, dest_path: str) -> bool:
        """نقل ملف أو مجلد"""
        operation_id = self._generate_operation_id()
        
        try:
            if not os.path.exists(source_path):
                self.error_occurred.emit(f"الملف المصدر غير موجود: {source_path}")
                return False
                
            # التأكد من وجود المجلد الهدف
            dest_dir = os.path.dirname(dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            self._ignore_watcher_events = True # تجاهل حدث المراقب
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
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag)
            
    def create_folder(self, folder_path: str) -> bool:
        """إنشاء مجلد"""
        operation_id = self._generate_operation_id()
        
        try:
            if os.path.exists(folder_path):
                self.error_occurred.emit(f"المجلد موجود بالفعل: {folder_path}")
                return False
            
            self._ignore_watcher_events = True # تجاهل حدث المراقب
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
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag)
            
    def search_files(self, pattern: str, root_path: str = None, 
                     include_content: bool = False,
                     file_extensions: List[str] = None) -> str:
        """البحث في الملفات"""
        search_id = self._generate_operation_id()
        
        if not root_path:
            root_path = self.current_folder or os.path.expanduser("~")
            
        # تشغيل البحث في خيط منفصل لتجنب تجميد UI
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
                # تجاهل بعض المجلدات الخاصة التي لا ينبغي أن تظهر في شجرة الملفات
                if item in ['.git', '__pycache__', 'node_modules', '.vscode', '.idea', '.venv', 'build', 'dist', 'temp', '.DS_Store', '.backups']:
                    continue

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
                        
                except OSError: # Permission denied or file disappeared
                    continue
                    
            # ترتيب العناصر
            # ترتيب المجلدات أولاً، ثم الملفات. ثم ترتيب أبجدي.
            files.sort(key=lambda x: x[sort_by] if sort_by in x else x['name'])
            folders.sort(key=lambda x: x[sort_by] if sort_by in x else x['name'])
            
            return {'files': files, 'folders': folders}
            
        except Exception as e:
            return {'files': [], 'folders': [], 'error': str(e)}
            
    def undo_last_operation(self) -> bool:
        """التراجع عن العملية الأخيرة (تحتاج إلى تنفيذ حقيقي للتراجع في هذا الكود)"""
        operation = self.history_manager.undo()
        if not operation:
            logger.info("No operation to undo.")
            return False
            
        try:
            # هنا يجب تنفيذ منطق التراجع الفعلي لكل نوع عملية
            self._ignore_watcher_events = True # تجاهل أحداث المراقب أثناء التراجع
            success = False
            if operation.operation_type == 'create': # إذا كانت عملية إنشاء ملف، قم بحذفه
                if os.path.exists(operation.source):
                    os.remove(operation.source)
                    logger.info(f"Undo: Removed created file {operation.source}")
                    success = True
            elif operation.operation_type == 'delete': # إذا كانت عملية حذف، حاول استعادة الملف من النسخة الاحتياطية (أو من سلة المهملات)
                # هذا يتطلب منطقًا معقدًا لاستعادة النسخ الاحتياطية
                logger.warning(f"Undo: Cannot automatically undo delete operation for {operation.source} without full backup/trash integration.")
                self.error_occurred.emit(f"لا يمكن التراجع عن عملية الحذف للملف {os.path.basename(operation.source)}")
                return False # فشل التراجع
            elif operation.operation_type == 'rename': # إذا كانت إعادة تسمية، أعد التسمية إلى الاسم القديم
                if os.path.exists(operation.destination):
                    os.rename(operation.destination, operation.source)
                    logger.info(f"Undo: Renamed {operation.destination} back to {operation.source}")
                    success = True
            elif operation.operation_type == 'move': # إذا كانت نقل، أعد النقل
                if os.path.exists(operation.destination):
                    shutil.move(operation.destination, operation.source)
                    logger.info(f"Undo: Moved {operation.destination} back to {operation.source}")
                    success = True
            elif operation.operation_type == 'copy': # إذا كانت نسخ، احذف النسخة
                if os.path.exists(operation.destination):
                    if os.path.isdir(operation.destination):
                        shutil.rmtree(operation.destination)
                    else:
                        os.remove(operation.destination)
                    logger.info(f"Undo: Removed copied item {operation.destination}")
                    success = True
            elif operation.operation_type == 'save': # إذا كانت حفظ، يمكن التراجع عنها إذا كان هناك تاريخ للمحتوى السابق
                # هذا يتطلب تخزين محتوى الملف قبل الحفظ في الـ history_manager
                logger.warning(f"Undo: Cannot automatically undo save operation for {operation.source}. Requires content history.")
                self.error_occurred.emit(f"لا يمكن التراجع عن عملية الحفظ للملف {os.path.basename(operation.source)}")
                return False # فشل التراجع
            
            if success:
                self.operation_completed.emit(operation.timestamp, True, f"تم التراجع عن العملية: {operation.operation_type}")
                return True
            else:
                logger.error(f"Undo operation type '{operation.operation_type}' not fully implemented or failed.")
                self.operation_completed.emit(operation.timestamp, False, f"فشل التراجع عن العملية: {operation.operation_type}")
                return False
                
        except Exception as e:
            logger.error(f"Undo operation failed: {e}", exc_info=True)
            self.error_occurred.emit(f"فشل التراجع عن العملية: {str(e)}")
            self.operation_completed.emit(operation.timestamp, False, f"فشل التراجع: {str(e)}")
            return False
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag) # إعادة تعيين العلامة بعد فترة قصيرة
            
    def redo_last_operation(self) -> bool:
        """إعادة العملية التالية (تحتاج إلى تنفيذ حقيقي للإعادة في هذا الكود)"""
        operation = self.history_manager.redo()
        if not operation:
            logger.info("No operation to redo.")
            return False
            
        try:
            self._ignore_watcher_events = True # تجاهل أحداث المراقب أثناء الإعادة
            success = False
            if operation.operation_type == 'create': # إذا كانت عملية إنشاء ملف، أعد إنشاءه
                content = operation.metadata.get('content', '')
                if not os.path.exists(operation.source): # أعد إنشائه فقط إذا لم يكن موجودًا
                    with open(operation.source, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Redo: Re-created file {operation.source}")
                    success = True
            elif operation.operation_type == 'delete': # لا يمكن إعادة الحذف (يجب أن تكون قد استعدت من التراجع أولاً)
                logger.warning(f"Redo: Cannot automatically redo delete operation for {operation.source}. Not supported.")
                return False # فشل الإعادة
            elif operation.operation_type == 'rename': # إذا كانت إعادة تسمية، أعد التسمية إلى الاسم الجديد
                if os.path.exists(operation.source):
                    os.rename(operation.source, operation.destination)
                    logger.info(f"Redo: Renamed {operation.source} to {operation.destination}")
                    success = True
            elif operation.operation_type == 'move': # إذا كانت نقل، أعد النقل
                if os.path.exists(operation.source):
                    shutil.move(operation.source, operation.destination)
                    logger.info(f"Redo: Moved {operation.source} to {operation.destination}")
                    success = True
            elif operation.operation_type == 'copy': # إذا كانت نسخ، أعد النسخ
                if os.path.exists(operation.source):
                    if os.path.isdir(operation.source):
                        shutil.copytree(operation.source, operation.destination)
                    else:
                        shutil.copy2(operation.source, operation.destination)
                    logger.info(f"Redo: Re-copied item {operation.source} to {operation.destination}")
                    success = True
            elif operation.operation_type == 'save': # إعادة الحفظ تعني تطبيق نفس المحتوى مرة أخرى
                if os.path.exists(operation.source):
                    content = operation.metadata.get('content', '')
                    self.save_file(operation.source, content)
                    logger.info(f"Redo: Re-saved file {operation.source}")
                    success = True
                
            if success:
                self.operation_completed.emit(operation.timestamp, True, f"تمت إعادة العملية: {operation.operation_type}")
                return True
            else:
                logger.error(f"Redo operation type '{operation.operation_type}' not fully implemented or failed.")
                self.operation_completed.emit(operation.timestamp, False, f"فشل الإعادة عن العملية: {operation.operation_type}")
                return False
                
        except Exception as e:
            logger.error(f"Redo operation failed: {e}", exc_info=True)
            self.error_occurred.emit(f"فشل الإعادة عن العملية: {str(e)}")
            self.operation_completed.emit(operation.timestamp, False, f"فشل الإعادة: {str(e)}")
            return False
        finally:
            QTimer.singleShot(500, self._reset_ignore_watcher_flag) # إعادة تعيين العلامة بعد فترة قصيرة
            
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
                
            # إنشاء مجلد النسخ الاحتياطية داخل مجلد الملف
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
        """اكتشاف ترميز الملف باستخدام chardet إذا كان متاحاً"""
        try:
            import chardet
            
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # قراءة أول 10KB
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                
                # استخدام الترميز المكتشف إذا كانت الثقة عالية
                if encoding and result['confidence'] > 0.7:
                    return encoding
                    
        except ImportError:
            logger.debug("chardet not installed. Falling back to default encoding.")
        except Exception as e:
            logger.debug(f"Encoding detection failed for {file_path}: {e}")
            
        # الافتراضي إذا لم يتم الكشف أو الثقة منخفضة
        return self.file_encoding
        
    def _detect_encoding(self, content: str) -> str:
        """اكتشاف ترميز المحتوى (للسلاسل النصية)"""
        try:
            # محاولة ترميزات مختلفة
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1256'] # أضف cp1256 للعربية
            
            for encoding in encodings:
                try:
                    content.encode(encoding)
                    return encoding # إذا نجح الترميز، استخدمه
                except UnicodeEncodeError:
                    continue # حاول الترميز التالي
                    
        except Exception:
            pass # تجاهل أي أخطاء هنا
            
        return self.file_encoding # الافتراضي
        
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
        """اكتشاف نوع الملف بناءً على الامتداد"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        type_mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascriptreact',
            '.ts': 'typescript',
            '.tsx': 'typescriptreact',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text',
            '.sql': 'sql',
            '.sh': 'shellscript',
            '.bash': 'shellscript',
            '.php': 'php',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.rb': 'ruby',
            '.pl': 'perl',
            '.lua': 'lua',
            '.r': 'r',
            '.vue': 'vue',
            '.svelte': 'svelte',
            '.csv': 'csv',
            '.log': 'log',
            '.cfg': 'ini',
            '.ini': 'ini',
            '.conf': 'ini',
            '.env': 'dotenv',
            'dockerfile': 'dockerfile',
            'makefile': 'makefile',
        }
        
        # بعض الملفات لا تحتوي على امتداد ولكن يمكن التعرف عليها بالاسم الكامل
        if os.path.basename(file_path).lower() == 'dockerfile':
            return 'dockerfile'
        if os.path.basename(file_path).lower() == 'makefile':
            return 'makefile'

        return type_mapping.get(ext, 'unknown')
        
    def _generate_operation_id(self) -> str:
        """توليد معرف عملية فريد"""
        self.operation_counter += 1
        return f"op_{self.operation_counter}_{int(time.time())}"
        
    def get_recent_files(self) -> List[str]:
        """الحصول على الملفات الأخيرة"""
        # تصفية الملفات غير الموجودة لضمان قائمة نظيفة
        self.recent_files = [f for f in self.recent_files if os.path.exists(f)]
        return self.recent_files.copy()
        
    def get_recent_folders(self) -> List[str]:
        """الحصول على المجلدات الأخيرة"""
        # تصفية المجلدات غير الموجودة لضمان قائمة نظيفة
        self.recent_folders = [f for f in self.recent_folders if os.path.exists(f)]
        return self.recent_folders.copy()
        
    def get_bookmarks(self) -> List[Dict[str, Any]]:
        """الحصول على الإشارات المرجعية"""
        # تصفية الإشارات غير الموجودة لضمان قائمة نظيفة
        self.bookmarks = [b for b in self.bookmarks if os.path.exists(b['path'])]
        return self.bookmarks.copy()
        
    def get_open_files(self) -> Dict[str, Dict[str, Any]]:
        """الحصول على الملفات المفتوحة حالياً"""
        return self.open_files.copy()
        
    def is_file_modified(self, file_path: str) -> bool:
        """فحص ما إذا كان الملف معدلاً في المحرر (مقارنة بالقرص)"""
        if file_path not in self.open_files:
            return False
            
        # تحديث حالة 'modified' بناءً على آخر محتوى من المحرر وهاش القرص
        # هذا يضمن أن 'modified' تعكس الحالة الحقيقية (إذا تم تحديثها بواسطة mark_file_modified)
        return self.open_files[file_path]['modified']
        
    def mark_file_modified(self, file_path: str, current_editor_content: str, modified: Optional[bool] = None):
        """
        تحديد حالة تعديل الملف ومقارنة المحتوى.
        هذه الدالة تستقبل المحتوى الحالي من المحرر.
        
        Args:
            file_path (str): مسار الملف.
            current_editor_content (str): المحتوى الحالي للملف من المحرر.
            modified (Optional[bool]): حالة التعديل المراد فرضها (True/False).
                                       إذا كانت None، فسيتم تحديد الحالة بناءً على مقارنة المحتوى.
        """
        if file_path not in self.open_files:
            logger.warning(f"UnifiedFileManager: Attempted to mark non-open file '{file_path}' as modified.")
            return

        file_info = self.open_files[file_path]
        
        # Determine the encoding to use for hashing
        encoding = file_info.get('encoding', self.file_encoding or 'utf-8')

        # Calculate hash of the current editor content
        current_content_hash = hashlib.md5(current_editor_content.encode(encoding, errors='ignore')).hexdigest()

        # Compare with the last known hash of content from disk or last save
        # إذا لم يكن هناك هاش مخزن بعد (مثلاً ملف تم إنشاؤه حديثاً ولم يتم حفظه بعد)، نعتبره معدلاً
        if 'last_known_disk_content_hash' not in file_info or file_info['last_known_disk_content_hash'] is None:
            file_info['modified'] = True
            logger.debug(f"UnifiedFileManager: '{file_path}' marked modified (no previous disk hash).")
        elif current_content_hash != file_info['last_known_disk_content_hash']:
            file_info['modified'] = True
            logger.debug(f"UnifiedFileManager: '{file_path}' content hash changed, marked modified.")
        else:
            file_info['modified'] = False
            logger.debug(f"UnifiedFileManager: '{file_path}' content hash unchanged, marked NOT modified.")

        # Override with 'modified' argument if explicitly set (e.g., after saving, set to False)
        if modified is not None:
            file_info['modified'] = modified
            logger.debug(f"UnifiedFileManager: '{file_path}' modification state explicitly set to: {file_info['modified']}.")

        # تحديث المحتوى المخزن في الذاكرة ليمثل أحدث محتوى للمحرر
        file_info['content'] = current_editor_content
        
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
        """تنظيف الموارد وإيقاف الخيوط لضمان إغلاق نظيف للتطبيق"""
        # إيقاف مراقبة الملفات
        self.stop_file_watching()
        
        # إيقاف مؤقت الحفظ التلقائي
        if self.auto_save_timer.isActive():
            self.auto_save_timer.stop()
            
        # حفظ الإعدادات النهائية
        self.save_settings()
        
        logger.info("Enhanced File Manager cleaned up successfully.")
        
    def __del__(self):
        """مدمر الكائن، يضمن استدعاء التنظيف عند حذف الكائن"""
        # يتم استدعاء هذا عند إزالة الكائن من الذاكرة
        # يمكن أن يكون متأخراً جداً لإيقاف الخيوط بشكل صحيح، لذا يفضل استخدام cleanup() يدوياً
        # قبل إغلاق التطبيق.
        self.cleanup()