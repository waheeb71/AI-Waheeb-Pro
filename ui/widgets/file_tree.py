#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced File Tree Widget with VS Code-like Features
شجرة الملفات المحسنة مع ميزات مشابهة لـ VS Code
"""

import os
import json
import logging
import shutil
import mimetypes
import datetime 
from typing import Optional, List, Dict, Any, Set
from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout,
    QMenu, QMessageBox, QInputDialog, QFileDialog, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QSplitter, QTextEdit, QTabWidget,
    QProgressBar, QStatusBar, QToolBar, QFrame, QApplication, QHeaderView,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem, QTreeWidgetItemIterator # Added for _find_item_by_path
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QMimeData, QUrl, QModelIndex,
    QSettings, QSize, QRect, QPoint # Removed QThread, QFileSystemWatcher as they are now in UnifiedFileManager
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QDrag, QAction, QFont, QColor, QPalette, QPainter,
    QFontMetrics, QPen, QBrush, QKeySequence, QShortcut
)

logger = logging.getLogger(__name__)

class VSCodeFileIcons:
    """أيقونات الملفات بنمط VS Code"""
    

    FOLDER_ICONS = {
        'default': '📁',
        'open': '📂',
        'src': '📦',
        'lib': '📚',
        'bin': '⚙️',
        'docs': '📖',
        'test': '🧪',
        'tests': '🧪',
        'assets': '🎨',
        'images': '🖼️',
        'css': '🎨',
        'js': '📜',
        'node_modules': '📦',
        '__pycache__': '🗂️',
        '.git': '🔀',
        '.vscode': '💻',
        '.idea': '💡',
        'config': '⚙️',
        'configs': '⚙️',
        'public': '🌐',
        'static': '🌐',
        'templates': '📄',
        'components': '🧩',
        'utils': '🔧',
        'helpers': '🔧',
        'services': '🔧',
        'models': '📊',
        'views': '👁️',
        'controllers': '🎮',
        'middleware': '🔗',
        'routes': '🛣️',
        'api': '🔌',
        'database': '🗄️',
        'migrations': '🔄',
        'seeds': '🌱',
        'logs': '📋',
        'cache': '💾',
        'temp': '🗂️',
        'tmp': '🗂️',
        'build': '🏗️',
        'dist': '📦',
        'output': '📤',
        'backup': '💾',
        'scripts': '📜',
        'tools': '🔧',
        'vendor': '📦',
        'external': '🔗',
        'third_party': '🔗',
        'plugins': '🔌',
        'extensions': '🔌',
        'modules': '📦',
        'packages': '📦',
        'resources': '📦',
        'locales': '🌍',
        'i18n': '🌍',
        'translations': '🌍',
        'fonts': '🔤',
        'icons': '🎨',
        'media': '🎬',
        'audio': '🎵',
        'video': '🎬',
        'downloads': '⬇️',
        'uploads': '⬆️',
        'shared': '🤝',
        'common': '🤝',
        'core': '⚡',
        'base': '🏗️',
        'framework': '🏗️',
        'engine': '⚙️',
        'system': '💻',
        'admin': '👑',
        'user': '👤',
        'client': '👤',
        'server': '🖥️',
        'frontend': '🎨',
        'backend': '⚙️',
        'ui': '🎨',
        'ux': '🎨',
        'design': '🎨',
        'layout': '📐',
        'style': '🎨',
        'theme': '🎨',
        'skin': '🎨'
    }
    
    FILE_ICONS = {
        # ملفات البرمجة
        '.py': '🐍',
        '.pyw': '🐍',
        '.pyc': '🐍',
        '.pyo': '🐍',
        '.pyd': '🐍',
        '.js': '📜',
        '.jsx': '⚛️',
        '.ts': '📘',
        '.tsx': '⚛️',
        '.vue': '💚',
        '.svelte': '🧡',
        '.angular': '🔴',
        '.react': '⚛️',
        '.html': '🌐',
        '.htm': '🌐',
        '.xhtml': '🌐',
        '.css': '🎨',
        '.scss': '🎨',
        '.sass': '🎨',
        '.less': '🎨',
        '.stylus': '🎨',
        '.php': '🐘',
        '.java': '☕',
        '.class': '☕',
        '.jar': '☕',
        '.c': '🔧',
        '.cpp': '🔧',
        '.cxx': '🔧',
        '.cc': '🔧',
        '.h': '🔧',
        '.hpp': '🔧',
        '.cs': '🔷',
        '.vb': '🔷',
        '.go': '🐹',
        '.rs': '🦀',
        '.swift': '🐦',
        '.kt': '🟣',
        '.scala': '🔴',
        '.rb': '💎',
        '.perl': '🐪',
        '.pl': '🐪',
        '.r': '📊',
        '.matlab': '📊',
        '.m': '📊',
        '.lua': '🌙',
        '.sh': '🐚',
        '.bash': '🐚',
        '.zsh': '🐚',
        '.fish': '🐚',
        '.ps1': '💙',
        '.bat': '⚫',
        '.cmd': '⚫',
        
        # ملفات التكوين والبيانات
        '.json': '📋',
        '.xml': '📄',
        '.yaml': '📄',
        '.yml': '📄',
        '.toml': '📄',
        '.ini': '⚙️',
        '.cfg': '⚙️',
        '.conf': '⚙️',
        '.config': '⚙️',
        '.env': '🔐',
        '.properties': '⚙️',
        '.settings': '⚙️',
        '.plist': '📄',
        '.manifest': '📄',
        
        # ملفات قواعد البيانات
        '.sql': '🗄️',
        '.db': '🗄️',
        '.sqlite': '🗄️',
        '.sqlite3': '🗄️',
        '.mdb': '🗄️',
        '.accdb': '🗄️',
        '.dbf': '🗄️',
        
        # ملفات التوثيق
        '.md': '📝',
        '.markdown': '📝',
        '.txt': '📄',
        '.rtf': '📄',
        '.doc': '📄',
        '.docx': '📄',
        '.odt': '📄',
        '.pdf': '📕',
        '.tex': '📄',
        '.latex': '📄',
        '.rst': '📄',
        '.asciidoc': '📄',
        '.org': '📄',
        
        # ملفات الصور
        '.png': '🖼️',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.gif': '🖼️',
        '.bmp': '🖼️',
        '.tiff': '🖼️',
        '.tif': '🖼️',
        '.svg': '🖼️',
        '.ico': '🖼️',
        '.webp': '🖼️',
        '.avif': '🖼️',
        '.heic': '🖼️',
        '.raw': '🖼️',
        '.psd': '🎨',
        '.ai': '🎨',
        '.sketch': '🎨',
        '.figma': '🎨',
        '.xd': '🎨',
        
        # ملفات الصوت والفيديو
        '.mp3': '🎵',
        '.wav': '🎵',
        '.flac': '🎵',
        '.ogg': '🎵',
        '.aac': '🎵',
        '.wma': '🎵',
        '.m4a': '🎵',
        '.opus': '🎵',
        '.mp4': '🎬',
        '.avi': '🎬',
        '.mkv': '🎬',
        '.mov': '🎬',
        '.wmv': '🎬',
        '.flv': '🎬',
        '.webm': '🎬',
        '.m4v': '🎬',
        '.3gp': '🎬',
        
        # ملفات الأرشيف
        '.zip': '📦',
        '.rar': '📦',
        '.7z': '📦',
        '.tar': '📦',
        '.gz': '📦',
        '.bz2': '📦',
        '.xz': '📦',
        '.lz': '📦',
        '.lzma': '📦',
        '.cab': '📦',
        '.iso': '💿',
        '.dmg': '💿',
        '.img': '💿',
        
        # ملفات التنفيذ
        '.exe': '⚙️',
        '.msi': '⚙️',
        '.app': '📱',
        '.deb': '📦',
        '.rpm': '📦',
        '.pkg': '📦',
        '.snap': '📦',
        '.flatpak': '📦',
        '.appimage': '📱',
        
        # ملفات الخطوط
        '.ttf': '🔤',
        '.otf': '🔤',
        '.woff': '🔤',
        '.woff2': '🔤',
        '.eot': '🔤',
        
        # ملفات أخرى
        '.log': '📋',
        '.tmp': '🗂️',
        '.temp': '🗂️',
        '.bak': '💾',
        '.backup': '💾',
        '.old': '💾',
        '.orig': '💾',
        '.cache': '💾',
        '.lock': '🔒',
        '.pid': '🔒',
        '.key': '🔐',
        '.pem': '🔐',
        '.crt': '🔐',
        '.cert': '🔐',
        '.p12': '🔐',
        '.pfx': '🔐',
        '.jks': '🔐',
        
        # ملفات خاصة
        'readme': '📖',
        'license': '📜',
        'changelog': '📋',
        'todo': '✅',
        'makefile': '🔨',
        'dockerfile': '🐳',
        'vagrantfile': '📦',
        'gemfile': '💎',
        'package.json': '📦',
        'composer.json': '🎼',
        'requirements.txt': '📋',
        'pipfile': '🐍',
        'poetry.lock': '🔒',
        'yarn.lock': '🔒',
        'package-lock.json': '🔒',
        'pnpm-lock.yaml': '🔒',
        '.gitignore': '🔀',
        '.gitattributes': '🔀',
        '.editorconfig': '⚙️',
        '.eslintrc': '🔍',
        '.prettierrc': '🎨',
        '.babelrc': '🔄',
        'webpack.config.js': '📦',
        'rollup.config.js': '📦',
        'vite.config.js': '⚡',
        'tsconfig.json': '📘',
        'jsconfig.json': '📜',
        'tslint.json': '🔍',
        'jest.config.js': '🧪',
        'karma.conf.js': '🧪',
        'protractor.conf.js': '🧪',
        'cypress.json': '🧪',
        'playwright.config.js': '🧪',
        '.travis.yml': '🔄',
        '.github': '🔀',
        'appveyor.yml': '🔄',
        'circle.yml': '🔄',
        'jenkins': '🔄',
        'azure-pipelines.yml': '🔄'
    }
    
    @classmethod
    def get_folder_icon(cls, folder_name: str, is_open: bool = False) -> str:
        """الحصول على أيقونة المجلد"""
        folder_name_lower = folder_name.lower()
        
        if is_open:
            return cls.FOLDER_ICONS.get('open', '📂')
        
        return cls.FOLDER_ICONS.get(folder_name_lower, cls.FOLDER_ICONS['default'])
    
    @classmethod
    def get_file_icon(cls, file_name: str) -> str:
        """الحصول على أيقونة الملف"""
        file_name_lower = file_name.lower()
        
        # فحص الأسماء الخاصة أولاً
        if file_name_lower in cls.FILE_ICONS:
            return cls.FILE_ICONS[file_name_lower]
        
        # فحص الامتداد
        _, ext = os.path.splitext(file_name_lower)
        return cls.FILE_ICONS.get(ext, '📄')

class FileTreeItemDelegate(QStyledItemDelegate):
    """مفوض رسم عناصر شجرة الملفات بنمط VS Code"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_item = None
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        """رسم العنصر"""
      
        if not index.isValid():
            super().paint(painter, option, index)
            return

        item = self.parent().itemFromIndex(index) # Get the QTreeWidgetItem from the index
        if not isinstance(item, VSCodeFileTreeItem):
            super().paint(painter, option, index)
            return

        # إعداد الرسام
        painter.save()
        
        # رسم الخلفية
        if option.state & QStyle.StateFlag.State_Selected:
          
            painter.fillRect(option.rect, QColor(66, 153, 225, 100))
        elif option.state & QStyle.StateFlag.State_MouseOver:
        
            painter.fillRect(option.rect, QColor(45, 55, 72, 50))
        
       
        super().paint(painter, option, index)
        
        painter.restore()
    
    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """حجم العنصر"""
        size = super().sizeHint(option, index)
        return QSize(size.width(), max(size.height(), 24))

class VSCodeFileTreeItem(QTreeWidgetItem):
    """عنصر شجرة الملفات بنمط VS Code"""
    
    def __init__(self, parent, file_path: str, is_folder: bool = False):
        super().__init__(parent)
        self.file_path = file_path
        self.is_folder = is_folder
        self.is_expanded_state = False
        self.children_loaded = False
        self.file_size = 0
        self.last_modified = 0
        self.is_git_ignored = False
        self.git_status = None
        
        self.setup_item()
    
    def setup_item(self):
        """إعداد العنصر"""
        file_name = os.path.basename(self.file_path)
        
        # الحصول على الأيقونة
        if self.is_folder:
            icon = VSCodeFileIcons.get_folder_icon(file_name, self.isExpanded())
        else:
            icon = VSCodeFileIcons.get_file_icon(file_name)
        
        # تعيين النص مع الأيقونة
        self.setText(0, f"{icon} {file_name}")
        self.setToolTip(0, self.file_path)
        
        # تعيين البيانات
        self.setData(0, Qt.ItemDataRole.UserRole, {
            'path': self.file_path,
            'is_folder': self.is_folder,
            'name': file_name,
            'icon': icon
        })
        
        # إعداد الخصائص
        if self.is_folder:
            self.setFlags(self.flags() | Qt.ItemFlag.ItemIsDropEnabled)
            self.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
        else:
            self.setFlags(self.flags() | Qt.ItemFlag.ItemIsDragEnabled)
        
        # تحديث معلومات الملف
        self.update_file_info()
    
    def update_file_info(self):
        """تحديث معلومات الملف"""
        try:
            if os.path.exists(self.file_path):
                stat = os.stat(self.file_path)
                self.file_size = stat.st_size
                self.last_modified = stat.st_mtime
                
                # تحديث لون النص حسب حالة الملف
                if self.is_git_ignored:
                    self.setForeground(0, QColor(128, 128, 128))  
                elif self.git_status == 'modified':
                    self.setForeground(0, QColor(255, 165, 0))  
                elif self.git_status == 'added':
                    self.setForeground(0, QColor(0, 255, 0)) 
                elif self.git_status == 'deleted':
                    self.setForeground(0, QColor(255, 0, 0)) 
                else:
                    self.setForeground(0, QColor(226, 232, 240)) 
            else:
               
                self.setForeground(0, QColor(255, 0, 0, 150)) 
        except OSError:
            pass
    
    def get_file_info(self) -> Dict[str, Any]:
        """الحصول على معلومات الملف"""
        try:
            stat = os.stat(self.file_path)
            return {
                'path': self.file_path,
                'name': os.path.basename(self.file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_folder': self.is_folder,
                'extension': os.path.splitext(self.file_path)[1] if not self.is_folder else '',
                'permissions': oct(stat.st_mode)[-3:],
                'mime_type': mimetypes.guess_type(self.file_path)[0] if not self.is_folder else None,
                'git_status': self.git_status,
                'is_git_ignored': self.is_git_ignored
            }
        except OSError as e:
            return {
                'path': self.file_path,
                'name': os.path.basename(self.file_path),
                'is_folder': self.is_folder,
                'error': str(e)
            }
            
    def update_icon(self, is_expanded: bool = None):
        """تحديث الأيقونة"""
        if self.is_folder:
            if is_expanded is None:
                is_expanded = self.isExpanded()
            
            file_name = os.path.basename(self.file_path)
            icon = VSCodeFileIcons.get_folder_icon(file_name, is_expanded)
            
            
            current_text = self.text(0)
            if current_text:
               
                parts = current_text.split(' ', 1)
                if len(parts) > 1:
                    file_name = parts[1]
                else:
                    file_name = os.path.basename(self.file_path)
                
                self.setText(0, f"{icon} {file_name}")

class VSCodeFileTree(QTreeWidget):
    """شجرة الملفات بنمط VS Code"""
    
    # الإشارات
    file_selected = pyqtSignal(str)
    file_opened = pyqtSignal(str)
    file_created = pyqtSignal(str, str)
    file_deleted = pyqtSignal(str)
    file_renamed = pyqtSignal(str, str)
    folder_changed = pyqtSignal(str) 
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.root_path = None
        # self.file_watcher = QFileSystemWatcher() # Removed as per previous discussion, handled by UnifiedFileManager
        
        self.expanded_folders = set()
        self.selected_files = set()
        self.search_filter = ""
        self.show_hidden_files = False
        self.sort_folders_first = True
        self.git_repo_path = None
        self.git_ignored_patterns = set()
        
        
        self.settings = QSettings('VSCodeFileTree', 'Settings')
        
        self.setup_ui()
        self.setup_context_menu()
        self.setup_connections() 
        self.setup_shortcuts()
        self.load_settings()
        
        logger.info("VS Code-style file tree initialized")
    
    # --- New method to set file_manager dependency ---
    def set_file_manager(self, file_manager_instance):
        self.file_manager = file_manager_instance
        # Re-establish connections related to file_manager if called after init
        self.file_manager.file_changed_externally.connect(self.on_external_file_change)
        self.file_manager.file_added.connect(self.on_external_file_add)
        self.file_manager.file_removed.connect(self.on_external_file_remove)
        self.file_manager.directory_changed.connect(self.on_external_directory_change)
        logger.info("VSCodeFileTree: Connected to UnifiedFileManager signals.")

    def setup_ui(self):
        """إعداد واجهة شجرة الملفات"""
        # إعدادات الشجرة
        self.setHeaderLabel("مستكشف الملفات")
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(False)
        self.setDragDropMode(QTreeWidget.DragDropMode.DragDrop)
        self.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setExpandsOnDoubleClick(False)
        
        # إخفاء الرأس
        self.header().hide()
        
        # تعيين المفوض المخصص
        self.setItemDelegate(FileTreeItemDelegate(self))
        
        # الأنماط بنمط VS Code
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                border: none;
                font-family: 'Segoe UI', 'Consolas', monospace;
                font-size: 13px;
                outline: none;
            }
            
            QTreeWidget::item {
                padding: 2px 4px;
                border: none;
                min-height: 22px;
            }
            
            QTreeWidget::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
            
            QTreeWidget::item:selected:hover {
                background-color: #0e639c;
            }
            
            QTreeWidget::branch {
                background: transparent;
            }
            
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            
            QTreeWidget::branch:has-children:!has-siblings:closed:hover,
            QTreeWidget::branch:closed:has-children:has-siblings:hover {
                background-color: #2a2d2e;
            }
            
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 14px;
                border: none;
            }
            
            QScrollBar::handle:vertical {
                background-color: #424242;
                border-radius: 7px;
                min-height: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #4f4f4f;
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            QScrollBar:horizontal {
                background-color: #1e1e1e;
                height: 14px;
                border: none;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #424242;
                border-radius: 7px;
                min-width: 20px;
                margin: 2px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #4f4f4f;
            }
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            
            QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover,
            QScrollBar::add-line:horizontal:hover, QScrollBar::sub-line:horizontal:hover {
                background: transparent;
            }
        """)
    
    def setup_context_menu(self):
        """إعداد القائمة السياقية"""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        self.itemClicked.connect(self.on_item_clicked)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.itemExpanded.connect(self.on_item_expanded)
        self.itemCollapsed.connect(self.on_item_collapsed)
        self.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Removed QFileSystemWatcher connections from here as they will be handled by set_file_manager
        # self.file_watcher.directoryChanged.connect(self.on_directory_changed)
        # self.file_watcher.fileChanged.connect(self.on_file_changed)
    
    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        # F2 لإعادة التسمية
        rename_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F2), self)
        rename_shortcut.activated.connect(self.rename_selected_item)
        
        # Delete للحذف
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self.delete_selected_items)
        
        # Ctrl+C للنسخ
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self)
        copy_shortcut.activated.connect(self.copy_selected_items)
        
        # Ctrl+X للقص
        cut_shortcut = QShortcut(QKeySequence.StandardKey.Cut, self)
        cut_shortcut.activated.connect(self.cut_selected_items)
        
        # Ctrl+V للصق
        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_shortcut.activated.connect(self.paste_items)
        
        # Ctrl+N لملف جديد
        new_file_shortcut = QShortcut(QKeySequence.StandardKey.New, self)
        new_file_shortcut.activated.connect(self.create_new_file_shortcut)
        
        # Ctrl+Shift+N لمجلد جديد
        new_folder_shortcut = QShortcut(QKeySequence("Ctrl+Shift+N"), self)
        new_folder_shortcut.activated.connect(self.create_new_folder_shortcut)
        
        # F5 للتحديث
        refresh_shortcut = QShortcut(QKeySequence(Qt.Key.Key_F5), self)
        refresh_shortcut.activated.connect(self.refresh_tree)
    
    def load_settings(self):
        """تحميل الإعدادات"""
        self.show_hidden_files = self.settings.value('show_hidden_files', False, type=bool)
        self.sort_folders_first = self.settings.value('sort_folders_first', True, type=bool)
        
        # تحميل المجلدات المفتوحة
        expanded_folders = self.settings.value('expanded_folders', [], type=list)
        self.expanded_folders = set(expanded_folders)
    
    def save_settings(self):
        """حفظ الإعدادات"""
        self.settings.setValue('show_hidden_files', self.show_hidden_files)
        self.settings.setValue('sort_folders_first', self.sort_folders_first)
        self.settings.setValue('expanded_folders', list(self.expanded_folders))
    
    def set_root_path(self, path: str):
        """تعيين المسار الجذر وتحديث عنوان الشجرة."""
        if not os.path.isdir(path):
            self.clear()
            self.setHeaderLabel("لم يتم فتح مجلد") # تحديث العنوان في حالة الخطأ
            self.root_path = None
            return
        
        self.root_path = path
        
        # ===> هذا هو المكان الصحيح لتغيير العنوان <===
        folder_name = os.path.basename(path)
        self.setHeaderLabel(folder_name.upper()) # تغيير عنوان العمود هنا
        
        self.refresh_tree()
        # self.start_file_watching() # Removed: file watching is now handled by UnifiedFileManager
        
        logger.info(f"Root path set to: {path}")
        
    def detect_git_repository(self):
        """اكتشاف مستودع Git"""
        if not self.root_path:
            return
        
        current_path = self.root_path
        while current_path and current_path != os.path.dirname(current_path):
            git_path = os.path.join(current_path, '.git')
            if os.path.exists(git_path):
                self.git_repo_path = current_path
                self.load_git_ignore_patterns()
                logger.info(f"Git repository detected at: {current_path}")
                return
            current_path = os.path.dirname(current_path)
        
        self.git_repo_path = None
        self.git_ignored_patterns.clear()
    
    def load_git_ignore_patterns(self):
        """تحميل أنماط .gitignore"""
        if not self.git_repo_path:
            return
        
        gitignore_path = os.path.join(self.git_repo_path, '.gitignore')
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.git_ignored_patterns.add(line)
            except Exception as e:
                logger.warning(f"Failed to load .gitignore: {e}")
    
    def is_git_ignored(self, file_path: str) -> bool:
        """فحص ما إذا كان الملف متجاهلاً في Git"""
        if not self.git_repo_path or not self.git_ignored_patterns:
            return False
        
        relative_path = os.path.relpath(file_path, self.git_repo_path)
        file_name = os.path.basename(file_path)
        
        for pattern in self.git_ignored_patterns:
            # Basic pattern matching (can be improved with fnmatch or regex)
            if pattern in relative_path or pattern == file_name:
                return True
        
        return False
        
    def refresh_tree(self):
        """تحديث الشجرة"""
        if not self.root_path:
            return
        
        # حفظ حالة التوسيع والتحديد
        self.save_expansion_state()
        selected_paths = [item.file_path for item in self.get_selected_items()]
        
        # مسح الشجرة وإعادة تحميلها
        self.clear()
        self.load_directory(self.root_path, None)
        
        # استعادة حالة التوسيع والتحديد
        self.restore_expansion_state()
        self.restore_selection(selected_paths)
        
    def load_directory(self, dir_path: str, parent_item: Optional[QTreeWidgetItem]):
        """تحميل مجلد"""
        try:
            items = os.listdir(dir_path)
            
            # تصفية الملفات المخفية والمجلدات الخاصة
            filtered_items = []
            for item_name in items:
                if not self.show_hidden_files and item_name.startswith('.'):
                    # Always show .gitignore, .env, .vscode, even if hidden
                    if item_name not in ['.gitignore', '.env', '.vscode']:
                        continue
                if item_name in ['node_modules', '__pycache__', '.git', '$RECYCLE.BIN', 'System Volume Information']: # Added system folders
                    continue
                filtered_items.append(item_name)
            
            items = filtered_items

            # تطبيق فلتر البحث
            if self.search_filter:
                items = [item for item in items if self.search_filter.lower() in item.lower()]
            
            # ترتيب العناصر
            if self.sort_folders_first:
                items.sort(key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
            else:
                items.sort(key=lambda x: x.lower())
            
            for item_name in items:
                item_path = os.path.join(dir_path, item_name)
                is_folder = os.path.isdir(item_path)
                
                # إنشاء عنصر الشجرة
                if parent_item:
                    tree_item = VSCodeFileTreeItem(parent_item, item_path, is_folder)
                else:
                    tree_item = VSCodeFileTreeItem(self, item_path, is_folder)
                
                # تحديث حالة Git
                tree_item.is_git_ignored = self.is_git_ignored(item_path)
                tree_item.update_file_info()
                
                # للمجلدات، إضافة عنصر وهمي لإظهار السهم
                if is_folder:
                    try:
                        # Only add a dummy item if the folder is not empty
                        if any(True for _ in os.scandir(item_path) if not _.name.startswith('.')):
                             dummy_item = QTreeWidgetItem(tree_item)
                             dummy_item.setText(0, "") # Empty text for a cleaner look, the arrow will still show
                             tree_item.children_loaded = False
                        else:
                            tree_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.NoIndicator) # No arrow for empty folders
                    except PermissionError:
                        dummy_item = QTreeWidgetItem(tree_item)
                        dummy_item.setText(0, "❌") # Indicator for no access
                        tree_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator) # Still show arrow
                        tree_item.children_loaded = False
                    except StopIteration: # Folder is empty
                        tree_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.NoIndicator) # No arrow for empty folders
                        tree_item.children_loaded = True # Consider it loaded if empty
                
        except PermissionError:
            error_item = QTreeWidgetItem(parent_item or self)
            error_item.setText(0, "❌ ليس لديك صلاحية للوصول")
            error_item.setForeground(0, QColor(255, 100, 100))
        except Exception as e:
            logger.error(f"Error loading directory {dir_path}: {e}", exc_info=True) # Log full traceback
    
    def save_expansion_state(self):
        """حفظ حالة التوسيع"""
        self.expanded_folders.clear()
        
        def collect_expanded(item):
            if isinstance(item, VSCodeFileTreeItem) and item.isExpanded():
                self.expanded_folders.add(item.file_path)
            
            for i in range(item.childCount()):
                collect_expanded(item.child(i))
        
        for i in range(self.topLevelItemCount()):
            collect_expanded(self.topLevelItem(i))
    
    def restore_expansion_state(self):
        """استعادة حالة التوسيع"""
        def expand_items(item):
            if isinstance(item, VSCodeFileTreeItem) and item.file_path in self.expanded_folders:
                # To prevent loading children again if already loaded by on_item_expanded
                if not item.children_loaded:
                    # Clear dummy and load children if expanded, otherwise the dummy will just stay
                    for i in range(item.childCount()):
                        child = item.child(i)
                        if child.text(0) == "": # Check for dummy item
                            item.removeChild(child)
                            break
                    self.load_directory(item.file_path, item)
                    item.children_loaded = True
                self.expandItem(item) # Expand even if already loaded to ensure UI state
            
            for i in range(item.childCount()):
                expand_items(item.child(i))
        
        for i in range(self.topLevelItemCount()):
            expand_items(self.topLevelItem(i))
    
    def restore_selection(self, selected_paths: List[str]):
        """استعادة التحديد"""
        if not selected_paths:
            return
        
        # Ensure that items are actually in the tree after refresh
        for path_to_select in selected_paths:
            item = self._find_item_by_path(path_to_select)
            if item:
                item.setSelected(True)
                self.setCurrentItem(item) # Optional: set as current item
                self.scrollToItem(item) # Optional: scroll to it
                break # Only select and scroll to the first one for simplicity
    
    def get_selected_items(self) -> List[VSCodeFileTreeItem]:
        """الحصول على العناصر المحددة"""
        return [item for item in self.selectedItems() if isinstance(item, VSCodeFileTreeItem)]
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """التعامل مع النقر على عنصر"""
        if isinstance(item, VSCodeFileTreeItem):
            if not item.is_folder: # Only emit for files on single click
                self.file_selected.emit(item.file_path)
    
    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """التعامل مع النقر المزدوج على عنصر"""
        if isinstance(item, VSCodeFileTreeItem):
            if not item.is_folder:
                self.file_opened.emit(item.file_path)
            else:
                # توسيع/طي المجلد
                if item.isExpanded():
                    self.collapseItem(item)
                else:
                    self.expandItem(item)
    
    def on_item_expanded(self, item: QTreeWidgetItem):
        """التعامل مع توسيع عنصر"""
        if isinstance(item, VSCodeFileTreeItem) and item.is_folder:
            # تحديث الأيقونة
            item.update_icon(True)
            
            # تحميل المحتوى إذا لم يتم تحميله من قبل
            if not item.children_loaded:
                # إزالة العناصر الوهمية
                for i in range(item.childCount()):
                    child = item.child(i)
                    # Check if it's a dummy item or if we need to clear and reload
                    # For simplicity, if it's a dummy or empty text, remove it.
                    if child.text(0) == "" or child.text(0) == "..." or child.text(0) == "❌": 
                        item.removeChild(child)
                        break # Assume only one dummy item
                
                # تحميل المحتوى الفعلي
                self.load_directory(item.file_path, item)
                item.children_loaded = True
            
            self.expanded_folders.add(item.file_path)
    
    def on_item_collapsed(self, item: QTreeWidgetItem):
        """التعامل مع طي عنصر"""
        if isinstance(item, VSCodeFileTreeItem) and item.is_folder:
            # تحديث الأيقونة
            item.update_icon(False)
            self.expanded_folders.discard(item.file_path)
    
    def on_selection_changed(self):
        """التعامل مع تغيير التحديد"""
        selected_items = self.get_selected_items()
        if selected_items:
            # إرسال إشارة للعنصر الأول المحدد
            # self.file_selected.emit(selected_items[0].file_path) # Already done on single click
            pass # Avoid redundant signals if on_item_clicked is used
    
    # --- New slots for external file system changes from UnifiedFileManager ---
    def on_external_file_change(self, file_path: str, change_info: dict):
        """معالجة تغيير ملف خارجيًا (معدل)"""
        logger.info(f"VSCodeFileTree: External file modified: {file_path}")
        item = self._find_item_by_path(file_path)
        if item:
            item.update_file_info() # Update color/metadata if needed
            # No need to refresh tree for a single file modification

    def on_external_file_add(self, file_path: str, change_info: dict):
        """معالجة إضافة ملف خارجيًا"""
        logger.info(f"VSCodeFileTree: External file added: {file_path}")
        parent_dir = os.path.dirname(file_path)
        parent_item = self._find_item_by_path(parent_dir)
        if parent_item and parent_item.isExpanded():
            # If parent is expanded, add the new item directly
            new_item = VSCodeFileTreeItem(parent_item, file_path, is_folder=os.path.isdir(file_path))
            parent_item.sortChildren(0, Qt.SortOrder.AscendingOrder) # Re-sort children
            logger.info(f"VSCodeFileTree: Added new item '{os.path.basename(file_path)}' to tree.")
        elif parent_item:
           
            parent_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
            parent_item.children_loaded = False # Mark as not loaded if a new child might need to be shown on expand
            logger.info(f"VSCodeFileTree: Updated parent folder '{os.path.basename(parent_dir)}' indicator for new file.")
        else:
          
            self.refresh_tree()
            logger.warning(f"VSCodeFileTree: Parent item for '{file_path}' not found or not expanded, forcing full refresh.")

    def on_external_file_remove(self, file_path: str, change_info: dict):
        """معالجة حذف ملف خارجيًا"""
        logger.info(f"VSCodeFileTree: External file removed: {file_path}")
        item = self._find_item_by_path(file_path) # Find the QTreeWidgetItem corresponding to the path

        if item: # If the item is found in the tree
            parent_item = item.parent()
            if parent_item:
             # If the item has a parent (it's inside a folder), remove it from the parent
               parent_item.removeChild(item)
               logger.info(f"VSCodeFileTree: Removed child item '{os.path.basename(file_path)}' from tree.")
            # If removing the last child, hide the parent's indicator
               if parent_item.childCount() == 0:
                  parent_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.NoIndicator)
                  parent_item.children_loaded = True # No children to load now
            else:
            # If it's a top-level item (no parent in the QTreeWidget structure)
            # Find its index among top-level items and remove it directly
              index = self.indexOfTopLevelItem(item)
              if index != -1: # Ensure it's a valid top-level item
                self.takeTopLevelItem(index)
                logger.info(f"VSCodeFileTree: Removed top-level item '{os.path.basename(file_path)}' from tree.")
              else:
                # Fallback if somehow it's a non-parented item but not found by indexOfTopLevelItem
                self.refresh_tree()
                logger.warning(f"VSCodeFileTree: Top-level item '{file_path}' not found by index, forcing full refresh.")
        else:
        # If the item was not found in the tree at all (e.g., path not currently loaded/expanded)
          self.refresh_tree() # A full refresh is the safest fallback to synchronize
          logger.warning(f"VSCodeFileTree: Item for '{file_path}' not found in tree, forcing full refresh.")
    def on_external_directory_change(self, path: str, change_info: dict):
        """معالجة تغيير مجلد خارجيًا (مثل إضافة/حذف محتويات)"""
        logger.info(f"VSCodeFileTree: External directory change detected: {path}")
        # For simplicity, a full refresh of the affected part of the tree is safest.
        # Find the item corresponding to the changed directory.
        item = self._find_item_by_path(path)
        if item and item.isExpanded():
            # If the directory is expanded, clear its children and reload it
            item.takeChildren() # Removes all children
            item.children_loaded = False # Mark for re-loading
            self.on_item_expanded(item) # This will re-load children
            logger.info(f"VSCodeFileTree: Reloaded expanded directory '{os.path.basename(path)}'.")
        else:
            # If the directory is not expanded, or if it's the root, a full refresh might be necessary.
            # Or just update its icon if it changes from empty to not empty.
            if item:
                # Update its icon to show or hide the expand arrow
                try:
                    has_children = any(True for _ in os.scandir(path) if not _.name.startswith('.'))
                    if has_children:
                        item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
                        item.children_loaded = False
                    else:
                        item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.NoIndicator)
                        item.children_loaded = True
                except (PermissionError, StopIteration):
                    item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator) # Assume has children or error
                    item.children_loaded = False
            self.refresh_tree() # Fallback for complex changes or if root changed
            logger.warning(f"VSCodeFileTree: Directory '{path}' not expanded or complex change, forcing full refresh.")
            
    # Helper method to find a QTreeWidgetItem by its file_path
    def _find_item_by_path(self, target_path: str) -> Optional[VSCodeFileTreeItem]:
        """يبحث عن عنصر في الشجرة بناءً على مساره."""
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            if isinstance(item, VSCodeFileTreeItem) and item.file_path == target_path:
                return item
            iterator += 1
        return None
    # --- End of new slots ---
    
    def show_context_menu(self, position):
        """عرض القائمة السياقية"""
        item = self.itemAt(position)
        menu = QMenu(self)
        
        # تطبيق نمط VS Code على القائمة
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #454545;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QMenu::separator {
                height: 1px;
                background-color: #454545;
                margin: 4px 0;
            }
        """)
        
        if item and isinstance(item, VSCodeFileTreeItem):
            selected_items = self.get_selected_items()
            
            if item.is_folder:
                # قائمة المجلدات
                new_file_action = menu.addAction("📄 ملف جديد")
                new_file_action.triggered.connect(lambda: self.create_new_file(item.file_path))
                
                new_folder_action = menu.addAction("📁 مجلد جديد")
                new_folder_action.triggered.connect(lambda: self.create_new_folder(item.file_path))
                
                menu.addSeparator()
                
                open_in_explorer_action = menu.addAction("🗂️ فتح في مستكشف الملفات")
                open_in_explorer_action.triggered.connect(lambda: self.open_in_file_explorer(item.file_path))
                
                menu.addSeparator()
            else:
                # قائمة الملفات
                open_action = menu.addAction("📖 فتح")
                open_action.triggered.connect(lambda: self.file_opened.emit(item.file_path))
                
                open_with_action = menu.addAction("🔧 فتح بواسطة...")
                open_with_action.triggered.connect(lambda: self.open_with_dialog(item.file_path))
                
                menu.addSeparator()
                
                reveal_action = menu.addAction("👁️ إظهار في مستكشف الملفات")
                reveal_action.triggered.connect(lambda: self.reveal_in_file_explorer(item.file_path))
                
                menu.addSeparator()
            
            # إجراءات مشتركة
            if len(selected_items) == 1:
                rename_action = menu.addAction("✏️ إعادة تسمية")
                rename_action.triggered.connect(lambda: self.rename_item(item))
            
            copy_action = menu.addAction("📋 نسخ")
            copy_action.triggered.connect(self.copy_selected_items)
            
            cut_action = menu.addAction("✂️ قص")
            cut_action.triggered.connect(self.cut_selected_items)
            
            # إضافة خيار اللصق إذا كان هناك شيء في الحافظة
            clipboard = QApplication.clipboard()
            if clipboard.mimeData().hasUrls():
                paste_action = menu.addAction("📌 لصق")
                paste_action.triggered.connect(self.paste_items)
            
            menu.addSeparator()
            
            delete_action = menu.addAction("🗑️ حذف")
            delete_action.triggered.connect(self.delete_selected_items)
            
            menu.addSeparator()
            
            properties_action = menu.addAction("ℹ️ خصائص")
            properties_action.triggered.connect(lambda: self.show_properties(item))
        
        else:
            # قائمة للمساحة الفارغة
            if self.root_path:
                new_file_action = menu.addAction("📄 ملف جديد")
                new_file_action.triggered.connect(lambda: self.create_new_file(self.root_path))
                
                new_folder_action = menu.addAction("📁 مجلد جديد")
                new_folder_action.triggered.connect(lambda: self.create_new_folder(self.root_path))
                
                menu.addSeparator()
                
                paste_action = menu.addAction("📌 لصق")
                paste_action.triggered.connect(self.paste_items)
                
                menu.addSeparator()
                
                refresh_action = menu.addAction("🔄 تحديث")
                refresh_action.triggered.connect(self.refresh_tree)
                
                menu.addSeparator()
                
                # خيارات العرض
                view_menu = menu.addMenu("👁️ عرض")
                
                hidden_files_action = view_menu.addAction("إظهار الملفات المخفية")
                hidden_files_action.setCheckable(True)
                hidden_files_action.setChecked(self.show_hidden_files)
                hidden_files_action.triggered.connect(self.toggle_hidden_files)
                
                sort_folders_action = view_menu.addAction("ترتيب المجلدات أولاً")
                sort_folders_action.setCheckable(True)
                sort_folders_action.setChecked(self.sort_folders_first)
                sort_folders_action.triggered.connect(self.toggle_sort_folders_first)
        
        if not menu.isEmpty():
            menu.exec(self.mapToGlobal(position))
    
    def create_new_file(self, parent_path: str):
        """إنشاء ملف جديد"""
      
        file_templates = {
            'Python Script (*.py)': {
                'extension': '.py',
                'template': '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{filename}
"""

def main():
    """الدالة الرئيسية"""
    print("مرحباً بك!")

if __name__ == "__main__":
    main()
'''
            },
            'JavaScript (*.js)': {
                'extension': '.js',
                'template': '''// {filename}

/**
 * الدالة الرئيسية
 */
function main() {
    console.log("مرحباً بك!");
}

main();
'''
            },
            'HTML Document (*.html)': {
                'extension': '.html',
                'template': '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
</head>
<body>
    <h1>مرحباً بك!</h1>
</body>
</html>
'''
            },
            'CSS Stylesheet (*.css)': {
                'extension': '.css',
                'template': '''/* {filename} */

body {
    font-family: Arial, sans-serif;
    direction: rtl;
    margin: 0;
    padding: 20px;
}

h1 {
    color: #333;
    text-align: center;
}
'''
            },
            'JSON File (*.json)': {
                'extension': '.json',
                'template': '''{
    "name": "{filename}",
    "version": "1.0.0",
    "description": "وصف الملف"
}
'''
            },
            'Markdown Document (*.md)': {
                'extension': '.md',
                'template': '''# {filename}

## الوصف

اكتب وصف المستند هنا.

## المحتوى

- عنصر 1
- عنصر 2
- عنصر 3
'''
            },
            'Text File (*.txt)': {
                'extension': '.txt',
                'template': 'ملف نصي جديد\n'
            },
            'Empty File': {
                'extension': '',
                'template': ''
            }
        }
        
        # اختيار نوع الملف
        file_type, ok = QInputDialog.getItem(
            self, 'نوع الملف', 'اختر نوع الملف:', 
            list(file_templates.keys()), 0, False
        )
        
        if not ok:
            return
        
        # إدخال اسم الملف
        file_name, ok = QInputDialog.getText(
            self, 'اسم الملف', 'أدخل اسم الملف:'
        )
        
        if not ok or not file_name.strip():
            return
        
        # إضافة الامتداد إذا لم يكن موجوداً
        template_info = file_templates[file_type]
        extension = template_info['extension']
        
        if extension and not file_name.endswith(extension):
            file_name += extension
        
        file_path = os.path.join(parent_path, file_name.strip())
        
        if os.path.exists(file_path):
            QMessageBox.warning(self, "خطأ", "الملف موجود بالفعل!")
            return
        
        try:
            # إنشاء الملف مع المحتوى
            template_content = template_info['template']
            if '{filename}' in template_content:
                filename_without_ext = os.path.splitext(file_name)[0]
                template_content = template_content.format(filename=filename_without_ext)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # self.refresh_tree() # This might be redundant if on_external_file_add is called
            self.file_created.emit(file_path, extension[1:] if extension else 'txt')
            
            # فتح الملف تلقائياً
            self.file_opened.emit(file_path)
            
            logger.info(f"Created new file: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء الملف: {str(e)}")
    
    def create_new_folder(self, parent_path: str):
        """إنشاء مجلد جديد"""
        folder_name, ok = QInputDialog.getText(
            self, 'مجلد جديد', 'أدخل اسم المجلد:'
        )
        
        if not ok or not folder_name.strip():
            return
        
        folder_path = os.path.join(parent_path, folder_name.strip())
        
        if os.path.exists(folder_path):
            QMessageBox.warning(self, "خطأ", "المجلد موجود بالفعل!")
            return
        
        try:
            os.makedirs(folder_path)
            # self.refresh_tree() # This might be redundant if on_external_file_add (for folders) is called
            
            logger.info(f"Created new folder: {folder_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء المجلد: {str(e)}")
    
    def create_new_file_shortcut(self):
        """إنشاء ملف جديد باستخدام اختصار لوحة المفاتيح"""
        if self.root_path:
            selected_items = self.get_selected_items()
            if selected_items and selected_items[0].is_folder:
                self.create_new_file(selected_items[0].file_path)
            else:
                self.create_new_file(self.root_path)
    
    def create_new_folder_shortcut(self):
        """إنشاء مجلد جديد باستخدام اختصار لوحة المفاتيح"""
        if self.root_path:
            selected_items = self.get_selected_items()
            if selected_items and selected_items[0].is_folder:
                self.create_new_folder(selected_items[0].file_path)
            else:
                self.create_new_folder(self.root_path)
    
    def rename_selected_item(self):
        """إعادة تسمية العنصر المحدد"""
        selected_items = self.get_selected_items()
        if len(selected_items) == 1:
            self.rename_item(selected_items[0])
    
    def rename_item(self, item: VSCodeFileTreeItem):
        """إعادة تسمية عنصر"""
        old_name = os.path.basename(item.file_path)
        new_name, ok = QInputDialog.getText(
            self, 'إعادة تسمية', 'الاسم الجديد:', text=old_name
        )
        
        if not ok or not new_name.strip() or new_name == old_name:
            return
        
        old_path = item.file_path
        new_path = os.path.join(os.path.dirname(old_path), new_name.strip())
        
        if os.path.exists(new_path):
            QMessageBox.warning(self, "خطأ", "اسم موجود بالفعل!")
            return
        
        try:
            os.rename(old_path, new_path)
            # self.refresh_tree() # Handled by on_external_file_remove then on_external_file_add
            self.file_renamed.emit(old_path, new_path)
            
            logger.info(f"Renamed {old_path} to {new_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في إعادة التسمية: {str(e)}")
    
    def copy_selected_items(self):
        """نسخ العناصر المحددة"""
        selected_items = self.get_selected_items()
        if not selected_items:
            return
        
        # إنشاء بيانات MIME للحافظة
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(item.file_path) for item in selected_items]
        mime_data.setUrls(urls)
        
        # إضافة معلومات إضافية
        paths = [item.file_path for item in selected_items]
        mime_data.setText('\n'.join(paths))
        mime_data.setData('application/x-file-operation', b'copy')
        
        # نسخ إلى الحافظة
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)
        
        logger.info(f"Copied {len(selected_items)} items to clipboard")
    
    def cut_selected_items(self):
        """قص العناصر المحددة"""
        selected_items = self.get_selected_items()
        if not selected_items:
            return
        
        # إنشاء بيانات MIME للحافظة
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(item.file_path) for item in selected_items]
        mime_data.setUrls(urls)
        
        # إضافة معلومات إضافية
        paths = [item.file_path for item in selected_items]
        mime_data.setText('\n'.join(paths))
        mime_data.setData('application/x-file-operation', b'cut')
        
        # نسخ إلى الحافظة
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)
        
        # تغيير مظهر العناصر المقصوصة
        for item in selected_items:
            item.setForeground(0, QColor(128, 128, 128))
        
        logger.info(f"Cut {len(selected_items)} items to clipboard")
    
    def paste_items(self):
        """لصق العناصر"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if not mime_data.hasUrls():
            return
        
        # تحديد المجلد الهدف
        selected_items = self.get_selected_items()
        if selected_items and selected_items[0].is_folder:
            target_folder = selected_items[0].file_path
        else:
            target_folder = self.root_path
        
        if not target_folder:
            return
        
        # تحديد نوع العملية
        operation_data = mime_data.data('application/x-file-operation')
        is_cut = operation_data == b'cut'
        
        try:
            for url in mime_data.urls():
                source_path = url.toLocalFile()
                if not os.path.exists(source_path):
                    continue
                
                file_name = os.path.basename(source_path)
                target_path = os.path.join(target_folder, file_name)
                
                # التعامل مع الأسماء المكررة
                counter = 1
                original_target = target_path
                while os.path.exists(target_path):
                    name, ext = os.path.splitext(file_name)
                    new_name = f"{name} ({counter}){ext}"
                    target_path = os.path.join(target_folder, new_name)
                    counter += 1
                
                # تنفيذ العملية
                if is_cut:
                    shutil.move(source_path, target_path)
                    logger.info(f"Moved {source_path} to {target_path}")
                else:
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, target_path)
                    else:
                        shutil.copy2(source_path, target_path)
                    logger.info(f"Copied {source_path} to {target_path}")
                
            # Note: The on_external_file_add/remove should handle updates
            # However, for robustness, if those are not perfectly synchronized,
            # a refresh_tree here after a paste operation might be acceptable,
            # especially for complex multi-file pastes.
            # self.refresh_tree() # Might be called automatically by file manager signals

            # مسح الحافظة إذا كانت عملية قص
            if is_cut:
                clipboard.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في لصق الملفات: {str(e)}")
    
    def delete_selected_items(self):
        """حذف العناصر المحددة"""
        selected_items = self.get_selected_items()
        if not selected_items:
            return
        
        # تأكيد الحذف
        if len(selected_items) == 1:
            message = f'هل أنت متأكد من حذف "{os.path.basename(selected_items[0].file_path)}"؟'
        else:
            message = f'هل أنت متأكد من حذف {len(selected_items)} عنصر؟'
        
        reply = QMessageBox.question(
            self, 'تأكيد الحذف', message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            for item in selected_items:
                if item.is_folder:
                    shutil.rmtree(item.file_path)
                else:
                    os.remove(item.file_path)
                
                self.file_deleted.emit(item.file_path)
                logger.info(f"Deleted: {item.file_path}")
            
            # self.refresh_tree() # Handled by on_external_file_remove
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في الحذف: {str(e)}")
    
    def open_in_file_explorer(self, path: str):
        """فتح في مستكشف الملفات"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(['explorer', path])
            elif system == "Darwin":  # macOS
                subprocess.run(['open', path])
            else:  # Linux
                subprocess.run(['xdg-open', path])
                
        except Exception as e:
            logger.error(f"Failed to open in file explorer: {e}")
    
    def reveal_in_file_explorer(self, file_path: str):
        """إظهار الملف في مستكشف الملفات"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(['explorer', '/select,', file_path])
            elif system == "Darwin":  # macOS
                subprocess.run(['open', '-R', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', os.path.dirname(file_path)])
                
        except Exception as e:
            logger.error(f"Failed to reveal in file explorer: {e}")
    
    def open_with_dialog(self, file_path: str):
        """فتح الملف بواسطة تطبيق آخر"""
        # TODO: تنفيذ حوار "فتح بواسطة"
        QMessageBox.information(self, "معلومات", "ميزة 'فتح بواسطة' قيد التطوير")
    
    def show_properties(self, item: VSCodeFileTreeItem):
        """عرض خصائص العنصر"""
        info = item.get_file_info()
        
        properties_text = f"""
📁 مسار الملف: {info['path']}
📝 الاسم: {info['name']}
🏷️ النوع: {'مجلد' if info['is_folder'] else 'ملف'}
"""
        
        if not info['is_folder']:
            properties_text += f"📎 الامتداد: {info.get('extension', 'بدون امتداد')}\n"
            if info.get('mime_type'):
                properties_text += f"🔍 نوع MIME: {info['mime_type']}\n"
        
        if 'size' in info:
            properties_text += f"📏 الحجم: {self.format_size(info['size'])}\n"
        
        if 'modified' in info:
            modified_time = datetime.datetime.fromtimestamp(info['modified'])
            properties_text += f"📅 آخر تعديل: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if 'created' in info:
            created_time = datetime.datetime.fromtimestamp(info['created'])
            properties_text += f"📅 تاريخ الإنشاء: {created_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if 'permissions' in info:
            properties_text += f"🔐 الصلاحيات: {info['permissions']}\n"
        
        if info.get('git_status'):
            properties_text += f"🔀 حالة Git: {info['git_status']}\n"
        
        if info.get('is_git_ignored'):
            properties_text += "🚫 متجاهل في Git: نعم\n"
        
        QMessageBox.information(self, "خصائص", properties_text)
    
    def toggle_hidden_files(self):
        """تبديل إظهار الملفات المخفية"""
        self.show_hidden_files = not self.show_hidden_files
        self.save_settings()
        self.refresh_tree()
    
    def toggle_sort_folders_first(self):
        """تبديل ترتيب المجلدات أولاً"""
        self.sort_folders_first = not self.sort_folders_first
        self.save_settings()
        self.refresh_tree()
    
    def set_search_filter(self, filter_text: str):
        """تعيين فلتر البحث"""
        self.search_filter = filter_text
        self.refresh_tree()
    
    def clear_search_filter(self):
        """مسح فلتر البحث"""
        self.search_filter = ""
        self.refresh_tree()
    
    def format_size(self, size: int) -> str:
        """تنسيق حجم الملف"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    def expand_to_file(self, file_path: str):
        """توسيع الشجرة للوصول إلى ملف معين"""
        if not os.path.exists(file_path):
            return False
        
        # الحصول على مسار المجلد الأب
        parent_path = os.path.dirname(file_path)
        
        # توسيع جميع المجلدات في المسار
        def expand_path(item, target_path):
            if isinstance(item, VSCodeFileTreeItem):
                if item.file_path == target_path:
                    if not item.isExpanded():
                        self.expandItem(item)
                    return True
                elif target_path.startswith(item.file_path + os.sep):
                    if not item.isExpanded():
                        self.expandItem(item)
                    
                    for i in range(item.childCount()):
                        if expand_path(item.child(i), target_path):
                            return True
            return False
        
        # البحث في العناصر العلوية
        for i in range(self.topLevelItemCount()):
            if expand_path(self.topLevelItem(i), parent_path):
                break
        
        # البحث عن الملف وتحديده
        def select_file(item, target_file):
            if isinstance(item, VSCodeFileTreeItem):
                if item.file_path == target_file:
                    self.setCurrentItem(item)
                    self.scrollToItem(item)
                    return True
                
                for i in range(item.childCount()):
                    if select_file(item.child(i), target_file):
                        return True
            return False
        
        for i in range(self.topLevelItemCount()):
            if select_file(self.topLevelItem(i), file_path):
                return True
        
        return False
    
    def get_all_files(self, extensions: List[str] = None) -> List[str]:
        """الحصول على جميع الملفات في الشجرة"""
        files = []
        
        def collect_files(item):
            if isinstance(item, VSCodeFileTreeItem):
                if not item.is_folder:
                    if not extensions:
                        files.append(item.file_path)
                    else:
                        ext = os.path.splitext(item.file_path)[1].lower()
                        if ext in extensions:
                            files.append(item.file_path)
                
                for i in range(item.childCount()):
                    collect_files(item.child(i))
        
        for i in range(self.topLevelItemCount()):
            collect_files(self.topLevelItem(i))
        
        return files
    
    def closeEvent(self, event):
        """التعامل مع إغلاق الويدجت"""
        self.save_settings()
        super().closeEvent(event)

    # دعم السحب والإفلات
    def dragEnterEvent(self, event):
        """التعامل مع دخول السحب"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """التعامل مع حركة السحب"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        """التعامل مع الإفلات"""
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            self.files_dropped.emit(files)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)