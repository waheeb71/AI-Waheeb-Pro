#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Code Editor Widget
محرر الكود المتقدم
"""

import re
import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, 
    QScrollBar, QFrame, QLabel, QCompleter, QTextBrowser
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QStringListModel, QTimer
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QFont, QFontMetrics,
    QTextCursor, QTextCharFormat, QSyntaxHighlighter,
    QTextDocument, QPalette, QKeySequence
)
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter
from PyQt6.QtWidgets import QPlainTextEdit
logger = logging.getLogger(__name__)

class LineNumberArea(QWidget):
    """Line number area widget"""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
    
    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Python syntax highlighter"""
    
    def __init__(self, document):
        super().__init__(document)
        
        # Define highlighting rules
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Blue
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
            'while', 'with', 'yield', 'True', 'False', 'None'
        ]
        
        for keyword in keywords:
            pattern = f'\\b{keyword}\\b'
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
        
        # Built-in functions
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#DCDCAA"))  # Yellow
        
        builtins = [
            'abs', 'all', 'any', 'bin', 'bool', 'chr', 'dict', 'dir',
            'enumerate', 'eval', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id',
            'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
            'list', 'locals', 'map', 'max', 'min', 'next', 'object',
            'oct', 'open', 'ord', 'pow', 'property', 'range', 'repr',
            'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
            'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        ]
        
        for builtin in builtins:
            pattern = f'\\b{builtin}\\b'
            self.highlighting_rules.append((re.compile(pattern), builtin_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange
        
        # Single quoted strings
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        # Double quoted strings
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        # Triple quoted strings
        self.highlighting_rules.append((re.compile(r'""".*?"""', re.DOTALL), string_format))
        self.highlighting_rules.append((re.compile(r"'''.*?'''", re.DOTALL), string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile(r'#[^\n]*'), comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))  # Light green
        self.highlighting_rules.append((re.compile(r'\b\d+\.?\d*\b'), number_format))
        
        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))  # Yellow
        self.highlighting_rules.append((re.compile(r'\bdef\s+(\w+)'), function_format))
        
        # Classes
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4EC9B0"))  # Cyan
        class_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((re.compile(r'\bclass\s+(\w+)'), class_format))
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text"""
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)

class CodeEditor(QPlainTextEdit):
    """Advanced code editor with syntax highlighting and line numbers"""
    
    # Signals
    line_number_clicked = pyqtSignal(int)
    text_changed_delayed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        
        # Editor settings
        self.line_number_area = LineNumberArea(self)
        self.syntax_highlighter = None
        self.completer = None
        self.auto_indent_enabled = True
        self.auto_complete_enabled = True
        self.word_wrap_enabled = False
        self.line_numbers_enabled = True
        
        # Delayed text change timer
        self.text_change_timer = QTimer()
        self.text_change_timer.setSingleShot(True)
        self.text_change_timer.timeout.connect(self.text_changed_delayed.emit)
        
        # Setup editor
        self.setup_editor()
        self.setup_syntax_highlighting()
        self.setup_auto_completion()
        self.setup_connections()
        
        logger.info("Code editor initialized")
    
    def setup_editor(self):
        """Setup editor appearance and behavior"""
        # Font
        font = QFont("Consolas", 12)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Colors and theme
        self.setStyleSheet("""
    background-color: #0D1117;
    color: #F0F6FC;
    border: 1px solid #30363D;
    selection-background-color: #264F78;
    selection-color: #F0F6FC;
""")


        
        # Tab settings
        tab_width = 4
        font_metrics = QFontMetrics(self.font())
        tab_stop_width = tab_width * font_metrics.horizontalAdvance(' ')
        self.setTabStopDistance(tab_stop_width)
        
        # Line wrap
       
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Cursor
        self.setCursorWidth(2)
        
        # Update line number area
        self.update_line_number_area_width()
        self.highlight_current_line()
    
    def setup_syntax_highlighting(self):
        """Setup syntax highlighting"""
        self.syntax_highlighter = PythonSyntaxHighlighter(self.document())
    
    def setup_auto_completion(self):
        """Setup auto-completion"""
        # Python keywords and built-ins for completion
        completions = [
            # Keywords
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
            'while', 'with', 'yield', 'True', 'False', 'None',
            
            # Built-in functions
            'abs', 'all', 'any', 'bin', 'bool', 'chr', 'dict', 'dir',
            'enumerate', 'eval', 'filter', 'float', 'format', 'frozenset',
            'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id',
            'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
            'list', 'locals', 'map', 'max', 'min', 'next', 'object',
            'oct', 'open', 'ord', 'pow', 'property', 'range', 'repr',
            'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
            'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip',
            
            # Common modules
            'os', 'sys', 'json', 'time', 'datetime', 'random', 'math',
            'collections', 'itertools', 'functools', 'operator',
            
            # Common patterns
            'if __name__ == "__main__":',
            'def __init__(self):',
            'def __str__(self):',
            'def __repr__(self):',
            'try:\n    \nexcept Exception as e:\n    ',
            'with open() as f:\n    ',
            'for i in range():\n    ',
            'while True:\n    ',
            'class ClassName:\n    def __init__(self):\n        pass'
        ]
        
        self.completer = QCompleter(completions)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)
    
    def setup_connections(self):
        """Setup signal connections"""
        
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self.on_text_changed)
    
    def on_text_changed(self):
        """Handle text change with delay"""
        self.text_change_timer.start(500)  # 500ms delay
    
    def line_number_area_width(self):
        """Calculate line number area width"""
        if not self.line_numbers_enabled:
            return 0
        
    
        digits = len(str(max(1, self.document().blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def update_line_number_area_width(self):
        """Update line number area width"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        """Update line number area"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), 
                                       self.line_number_area.width(), 
                                       rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()
    
    def resizeEvent(self, event):
        """Handle resize event"""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), 
                  self.line_number_area_width(), cr.height())
        )
    
    def line_number_area_paint_event(self, event):
        """Paint line numbers"""
        if not self.line_numbers_enabled:
            return
        
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#161B22"))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        height = self.fontMetrics().height()
        
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(block_number + 1)
                painter.setPen(QColor("#7D8590"))
                painter.drawText(0, int(top), self.line_number_area.width() - 3, 
                               height, Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
    
    def highlight_current_line(self):
        """Highlight current line"""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            
            line_color = QColor("#21262D")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Auto-completion
        key = event.key()
        text = event.text()
        cursor = self.textCursor()
        if self.auto_complete_enabled and self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                event.ignore()
                return
        
        # Auto-indentation
        if self.auto_indent_enabled and event.key() == Qt.Key.Key_Return:
            cursor = self.textCursor()
            current_line = cursor.block().text()
            
            # Calculate indentation
            indent = 0
            for char in current_line:
                if char == ' ':
                    indent += 1
                elif char == '\t':
                    indent += 4
                else:
                    break
            
            # Add extra indent for certain keywords
            stripped_line = current_line.strip()
            if stripped_line.endswith(':'):
                indent += 4
            
            super().keyPressEvent(event)
            
            # Insert indentation
            if indent > 0:
                cursor = self.textCursor()
                cursor.insertText(' ' * indent)
            
            return
        closing = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        if text in closing:
           cursor.insertText(text + closing[text])
           cursor.movePosition(cursor.MoveOperation.PreviousCharacter)
           self.setTextCursor(cursor)
           return
       
        # Tab handling
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                # Indent selected lines
                self.indent_selection()
            else:
                # Insert spaces instead of tab
                cursor.insertText('    ')
            return
        
        # Shift+Tab handling
        if event.key() == Qt.Key.Key_Backtab:
            self.unindent_selection()
            return
        
        # Auto-completion trigger
        if self.auto_complete_enabled and event.text().isalnum():
            super().keyPressEvent(event)
            self.show_completion()
            return
        
        super().keyPressEvent(event)
    
    def indent_selection(self):
        """Indent selected lines"""
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        
        while cursor.position() < end:
            cursor.insertText('    ')
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
            end += 4
    
    def unindent_selection(self):
        """Unindent selected lines"""
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        
        while cursor.position() < end:
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            text = cursor.selectedText()
            
            if text.startswith('    '):
                cursor.insertText(text[4:])
                end -= 4
            elif text.startswith('\t'):
                cursor.insertText(text[1:])
                end -= 1
            
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
    
    def show_completion(self):
        """Show auto-completion popup"""
        if not self.completer:
            return
        
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        completion_prefix = cursor.selectedText()
        
        if len(completion_prefix) < 2:
            self.completer.popup().hide()
            return
        
        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            self.completer.popup().setCurrentIndex(
                self.completer.completionModel().index(0, 0)
            )
        
        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) + 
                   self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)
    
    def insert_completion(self, completion):
        """Insert completion text"""
        if not self.completer:
            return
        
        cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
        cursor.insertText(completion[-extra:])
        self.setTextCursor(cursor)
    
    def get_current_line_number(self):
        """Get current line number"""
        return self.textCursor().blockNumber() + 1
    
    def get_current_column_number(self):
        """Get current column number"""
        return self.textCursor().columnNumber() + 1
    
    def goto_line(self, line_number: int):
        """Go to specific line"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, 
                          QTextCursor.MoveMode.MoveAnchor, line_number - 1)
        self.setTextCursor(cursor)
        self.centerCursor()
    
    def find_text(self, text: str, case_sensitive: bool = False, whole_words: bool = False):
        """Find text in editor"""
        flags = QTextDocument.FindFlag(0)
        
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        
        if whole_words:
            flags |= QTextDocument.FindFlag.FindWholeWords
        
        return self.find(text, flags)
    
    def replace_text(self, find_text: str, replace_text: str, replace_all: bool = False):
        """Replace text in editor"""
        if replace_all:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
            
            count = 0
            while self.find_text(find_text):
                cursor = self.textCursor()
                cursor.insertText(replace_text)
                count += 1
            
            return count
        else:
            cursor = self.textCursor()
            if cursor.hasSelection() and cursor.selectedText() == find_text:
                cursor.insertText(replace_text)
                return 1
            
            return 0
    
    def comment_selection(self):
        """Comment selected lines"""
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        
        while cursor.position() < end:
            cursor.insertText('# ')
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
            end += 2
    
    def uncomment_selection(self):
        """Uncomment selected lines"""
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        
        while cursor.position() < end:
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            text = cursor.selectedText()
            
            if text.startswith('# '):
                cursor.insertText(text[2:])
                end -= 2
            elif text.startswith('#'):
                cursor.insertText(text[1:])
                end -= 1
            
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
    
    def get_selected_text(self) -> str:
        """Get selected text"""
        return self.textCursor().selectedText()
    
    def get_word_under_cursor(self) -> str:
        """Get word under cursor"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()
    
    def set_line_numbers_enabled(self, enabled: bool):
        """Enable/disable line numbers"""
        self.line_numbers_enabled = enabled
        self.update_line_number_area_width()
        self.line_number_area.setVisible(enabled)
    
    def set_word_wrap_enabled(self, enabled: bool):
        """Enable/disable word wrap"""
        self.word_wrap_enabled = enabled
        if enabled:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            
    
    def set_auto_indent_enabled(self, enabled: bool):
        """Enable/disable auto-indentation"""
        self.auto_indent_enabled = enabled
    
    def set_auto_complete_enabled(self, enabled: bool):
        """Enable/disable auto-completion"""
        self.auto_complete_enabled = enabled
        if self.completer:
            self.completer.popup().setVisible(False)
    
    def get_editor_info(self) -> Dict[str, Any]:
        """Get editor information"""
        text = self.toPlainText()
        cursor = self.textCursor()
        
        return {
            'line_count': self.blockCount(),
            'character_count': len(text),
            'word_count': len(text.split()),
            'current_line': cursor.blockNumber() + 1,
            'current_column': cursor.columnNumber() + 1,
            'selection_start': cursor.selectionStart(),
            'selection_end': cursor.selectionEnd(),
            'has_selection': cursor.hasSelection(),
            'selected_text': cursor.selectedText() if cursor.hasSelection() else '',
            'is_modified': self.document().isModified()
        }

