# في ui/widgets/output_panel.py

import logging
from datetime import datetime
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QTabWidget, QLabel, QFrame,
    QLineEdit, QMessageBox # Added QLineEdit and QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QProcess # Added QProcess for terminal
from PyQt6.QtGui import QFont, QTextCursor

logger = logging.getLogger(__name__)

class OutputPanel(QWidget):
    """Output panel for displaying results, logs, errors, and integrated terminal"""
    
    terminal_output_ready = pyqtSignal(str) 

    def __init__(self):
        super().__init__()
        
        # UI components
        self.tab_widget = None
        self.output_text = None         # For program execution output
        self.ai_response_text = None    # For general AI responses
        self.error_text = None          # For application errors
        self.log_text = None            # For application logs
        self.terminal_output_display = None # For terminal output
        self.terminal_input_field = None # For terminal input
        self.terminal_process = None    # QProcess for running shell
        
        self.init_ui()
        self.setup_terminal()
        
        logger.info("Output panel initialized")
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("لوحة الإخراج")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #F8FAFC;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("مسح الكل")
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155;
                background-color: #0F172A;
            }
            QTabBar::tab {
                background-color: #1E293B;
                color: #94A3B8;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0F172A;
                color: #F8FAFC;
            }
            QTabBar::tab:hover { /* 🆕 Hover effect for tabs */
                background-color: #334155;
            }
        """)
        
        # Output tab (for program execution output)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #0D1117;
                color: #F0F6FC;
                border: none;
                padding: 8px;
            }
        """)
        self.tab_widget.addTab(self.output_text, "إخراج البرنامج")
        
        # AI Response tab (for raw AI textual responses to general queries)
        self.ai_response_text = QTextEdit()
        self.ai_response_text.setReadOnly(True)
        self.ai_response_text.setFont(QFont("Arial", 11))
        self.ai_response_text.setStyleSheet("""
            QTextEdit {
                background-color: #0D1117;
                color: #F0F6FC;
                border: none;
                padding: 8px;
            }
        """)
        self.tab_widget.addTab(self.ai_response_text, "استجابة الذكاء الاصطناعي")
        
        # Error tab
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setFont(QFont("Consolas", 10))
        self.error_text.setStyleSheet("""
            QTextEdit {
                background-color: #0D1117;
                color: #FCA5A5; /* Softer red for errors */
                border: none;
                padding: 8px;
            }
        """)
        self.tab_widget.addTab(self.error_text, "الأخطاء")
        
        # Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0D1117;
                color: #9CA3AF;
                border: none;
                padding: 8px;
            }
        """)
        self.tab_widget.addTab(self.log_text, "السجل")

        # Terminal Tab
        self.terminal_tab_widget = QWidget()
        terminal_layout = QVBoxLayout(self.terminal_tab_widget)
        terminal_layout.setContentsMargins(0,0,0,0)

        self.terminal_output_display = QTextEdit()
        self.terminal_output_display.setReadOnly(True)
        self.terminal_output_display.setFont(QFont("Consolas", 10))
        self.terminal_output_display.setStyleSheet("""
            QTextEdit {
                background-color: #0D1117;
                color: #F0F6FC;
                border: none;
                padding: 8px;
            }
        """)
        terminal_layout.addWidget(self.terminal_output_display)

        self.terminal_input_field = QLineEdit()
        self.terminal_input_field.setPlaceholderText("اكتب الأمر هنا...")
        self.terminal_input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1E293B;
                color: #F0F6FC;
                border: 1px solid #334155;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus { /* 🆕 Focus style */
                border: 1px solid #2563EB;
            }
        """)
        self.terminal_input_field.returnPressed.connect(self.execute_terminal_command)
        terminal_layout.addWidget(self.terminal_input_field)

        self.tab_widget.addTab(self.terminal_tab_widget, "الترمنال")
        
        layout.addWidget(self.tab_widget)
    
    def _format_timestamp(self):
        """Helper to get formatted timestamp"""
        return f"<span style='color:#6B7280;'>[{datetime.now().strftime('%H:%M:%S')}]</span>"

    def add_program_output(self, text: str):
        """Add program execution output text to 'إخراج البرنامج' tab"""
        # Ensure output is treated as plain text to prevent HTML injection from program output
        formatted_text = f"{self._format_timestamp()} <span style='color:#F0F6FC;'>{text}</span>"
        self.output_text.append(formatted_text.rstrip())
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)
        self.tab_widget.setCurrentIndex(0) # Switch to Program Output tab

    def add_ai_response_display(self, text: str):
        """Add AI response text to 'استجابة الذكاء الاصطناعي' tab"""
        # AI responses might contain code blocks or markdown, so append as HTML for rich display
        formatted_text = f"{self._format_timestamp()} <span style='color:#A78BFA;'>AI:</span> {text}"
        self.ai_response_text.append(formatted_text.rstrip())
        self.ai_response_text.moveCursor(QTextCursor.MoveOperation.End)
        self.tab_widget.setCurrentIndex(1) # Switch to AI Response tab
        
    def add_error_display(self, error: str):
        """Add error text to 'الأخطاء' tab"""
        # Errors should be clearly visible
        formatted_text = f"{self._format_timestamp()} <span style='color:#EF4444; font-weight:bold;'>❌ خطأ:</span> <span style='color:#FCA5A5;'>{error}</span>"
        self.error_text.append(formatted_text.rstrip())
        self.error_text.moveCursor(QTextCursor.MoveOperation.End)
        self.tab_widget.setCurrentIndex(2) # Switch to Error tab
        self.tab_widget.setTabText(2, "⚠️ الأخطاء") # Highlight tab with warning icon
    
    def add_log_display(self, message: str, level: str = "INFO"):
        """Add log message to 'السجل' tab"""
        # Log messages for debugging, different colors for different levels
        color = {
            "DEBUG": "#6B7280",   # Gray
            "INFO": "#9CA3AF",    # Light gray
            "WARNING": "#FBBF24", # Yellow
            "ERROR": "#EF4444",   # Red
            "CRITICAL": "#DC2626" # Darker Red
        }.get(level.upper(), "#9CA3AF")

        formatted_text = f"{self._format_timestamp()} <span style='color:{color};'>[{level.upper()}]</span> <span style='color:#9CA3AF;'>{message}</span>"
        self.log_text.append(formatted_text.rstrip())
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
    
    # Terminal Methods
    def setup_terminal(self):
        self.terminal_process = QProcess(self)
        self.terminal_process.readyReadStandardOutput.connect(self._handle_terminal_stdout)
        self.terminal_process.readyReadStandardError.connect(self._handle_terminal_stderr)
        self.terminal_process.stateChanged.connect(self._handle_terminal_state_change)
        self.terminal_process.finished.connect(self._handle_terminal_finished)

        # Determine the shell based on OS
        import platform
        if platform.system() == "Windows":
            # For Windows, cmd.exe is standard. For better compatibility/features, consider using WSL bash or PowerShell.
            # Using ["cmd.exe", "/K", "echo Terminal started..."] to keep window open and interactive
            self.shell_command = ["cmd.exe", "/K"] # /K runs command and keeps cmd window open
            # Note: /K might not be ideal for redirection within QProcess.
            # A more robust solution might require a PTY or specific shell flags.
            # For basic functionality, simple start("cmd.exe") and write might work.
            # Let's try just "cmd.exe" first and write commands.
            self.shell_args = []
            self.shell_prompt = "> "
        else: # Linux or macOS
            self.shell_command = ["bash", "-i"] # -i for interactive shell, better for prompts etc.
            self.shell_args = []
            self.shell_prompt = "$ " # Typical Linux/macOS prompt
        
        # Start the shell process
        try:
            self.terminal_process.start(self.shell_command[0], self.shell_args)
            self.terminal_output_display.append(f"<span style='color:#10B981; font-weight:bold;'>مرحباً بك في الترمنال ({self.shell_command[0]})!</span>")
            self.terminal_output_display.append("<span style='color:#9CA3AF;'>لإدخال الأوامر، اكتب في الأسفل واضغط Enter.</span>")
            self.terminal_output_display.append("<span style='color:#6B7280;'>-" * 50 + "</span>")
            self.terminal_output_display.append(f"<span style='color:#F0F6FC;'>{self.terminal_process.workingDirectory()}{self.shell_prompt}</span>")
        except Exception as e:
            self.add_error_display(f"فشل في بدء الترمنال: {e}")
            logger.error(f"Failed to start terminal process: {e}", exc_info=True)

    def execute_terminal_command(self):
        command = self.terminal_input_field.text().strip()
        if not command:
            return
        
        # Display command in a distinct color for user clarity
        self.terminal_output_display.append(f"<span style='color:#60A5FA;'>{self.terminal_process.workingDirectory()}{self.shell_prompt} {command}</span>") 
        self.terminal_input_field.clear()

        # Send command to the process
        if self.terminal_process.state() == QProcess.ProcessState.Running:
            # Need to write the command AND a newline to simulate pressing Enter
            self.terminal_process.write((command + '\n').encode())
        else:
            self.add_error_display("الترمنال غير نشط. حاول إعادة تشغيله أو فتح مجلد.")
            logger.warning("Attempted to write to a non-running terminal process.")
    
    def _handle_terminal_stdout(self):
        output = self.terminal_process.readAllStandardOutput().data().decode(errors='ignore')
        # Display output directly, preserving newlines
        self.terminal_output_display.append(f"<span style='color:#F0F6FC;'>{output}</span>")
        self.terminal_output_display.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal_output_ready.emit(output)

    def _handle_terminal_stderr(self):
        error_output = self.terminal_process.readAllStandardError().data().decode(errors='ignore')
        # Display errors in a distinct red color
        self.terminal_output_display.append(f"<span style='color:#FF6347;'>{error_output}</span>")
        self.terminal_output_display.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal_output_ready.emit(error_output)

    def _handle_terminal_state_change(self, state: QProcess.ProcessState):
        state_map = {
            QProcess.ProcessState.NotRunning: "غير نشط",
            QProcess.ProcessState.Starting: "جاري البدء",
            QProcess.ProcessState.Running: "نشط"
        }
        logger.info(f"Terminal state changed to: {state_map.get(state, str(state))}")
        if state == QProcess.ProcessState.Running:
            self.terminal_input_field.setEnabled(True)
            self.terminal_input_field.setFocus()
        else:
            self.terminal_input_field.setEnabled(False)
            self.terminal_output_display.append(f"\n<span style='color:#EF4444;'>--- الترمنال {state_map.get(state, str(state))} ---</span>")

    def _handle_terminal_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        logger.info(f"Terminal process finished. Exit code: {exit_code}, Exit status: {exit_status}")
        self.terminal_output_display.append(f"\n<span style='color:#6B7280;'>--- انتهى الترمنال (رمز الخروج: {exit_code}) ---</span>")
        if exit_code != 0:
            self.add_error_display(f"خطأ في الترمنال: رمز الخروج {exit_code}")
        
    def clear_output(self):
        """Clear program output text"""
        self.output_text.clear()
    
    def clear_ai_response(self):
        """Clear AI response text"""
        self.ai_response_text.clear()
    
    def clear_errors(self):
        """Clear error text"""
        self.error_text.clear()
        self.tab_widget.setTabText(2, "الأخطاء")
    
    def clear_log(self):
        """Clear log text"""
        self.log_text.clear()
    
    def clear_terminal(self):
        """Clear terminal output"""
        self.terminal_output_display.clear()

    def clear_all(self):
        """Clear all tabs"""
        self.clear_output()
        self.clear_ai_response()
        self.clear_errors()
        self.clear_log()
        self.clear_terminal()
    
    def show_tab(self, tab_name: str):
        """Show specific tab"""
        tab_map = {
            "program_output": 0,
            "ai_response": 1,
            "error": 2,
            "log": 3,
            "terminal": 4
        }
        
        if tab_name in tab_map:
            self.tab_widget.setCurrentIndex(tab_map[tab_name])

    def set_terminal_working_directory(self, path: str):
        """Set current working directory for terminal"""
        if os.path.isdir(path):
            self.terminal_process.setWorkingDirectory(path)
            self.terminal_output_display.append(f"\n<span style='color:#60A5FA; font-weight:bold;'>--- تم تغيير مسار الترمنال إلى: {path} ---</span>\n")
            self.terminal_output_display.append(f"<span style='color:#F0F6FC;'>{self.terminal_process.workingDirectory()}{self.shell_prompt}</span>")
            logger.info(f"Terminal working directory set to: {path}")
        else:
            logger.warning(f"Attempted to set non-existent directory as terminal WD: {path}")