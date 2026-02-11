"""
Log viewer window for displaying application logs.

Provides search, filtering, and export functionality.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLineEdit, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QTextCursor, QFont
from PyQt6.QtCore import Qt, pyqtSlot
from pathlib import Path


class LogViewer(QDialog):
    """Dialog for viewing application logs."""
    
    def __init__(self, logger_manager, parent=None):
        """
        Initialize log viewer.
        
        Args:
            logger_manager: Logger manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger_manager = logger_manager
        self.setup_ui()
        
        # Connect to log handler
        gui_handler = self.logger_manager.add_gui_handler()
        gui_handler.log_emitted.connect(self.append_log)
    
    def setup_ui(self) -> None:
        """Setup UI components."""
        self.setWindowTitle("Log Viewer")
        self.setModal(False)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term...")
        self.search_input.returnPressed.connect(self.search_logs)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Find")
        search_btn.clicked.connect(self.search_logs)
        search_layout.addWidget(search_btn)
        
        layout.addLayout(search_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Monospace", 9))
        layout.addWidget(self.log_display)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Display")
        clear_btn.clicked.connect(self.clear_display)
        btn_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("Export Logs")
        export_btn.clicked.connect(self.export_logs)
        btn_layout.addWidget(export_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Load existing logs
        self.load_existing_logs()
    
    def load_existing_logs(self) -> None:
        """Load existing log file contents."""
        try:
            log_file = self.logger_manager.get_log_file_path()
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    self.log_display.setPlainText(f.read())
                
                # Scroll to bottom
                cursor = self.log_display.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.log_display.setTextCursor(cursor)
        except Exception as e:
            self.log_display.setPlainText(f"Error loading logs: {e}")
    
    @pyqtSlot(str)
    def append_log(self, message: str) -> None:
        """
        Append log message to display.
        
        Args:
            message: Log message
        """
        self.log_display.append(message)
    
    def search_logs(self) -> None:
        """Search for text in logs."""
        search_term = self.search_input.text()
        if not search_term:
            return
        
        # Find text
        found = self.log_display.find(search_term)
        
        if not found:
            # Try from beginning
            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.log_display.setTextCursor(cursor)
            
            found = self.log_display.find(search_term)
            
            if not found:
                QMessageBox.information(self, "Search", f"'{search_term}' not found in logs.")
    
    def clear_display(self) -> None:
        """Clear log display."""
        self.log_display.clear()
    
    def export_logs(self) -> None:
        """Export logs to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            str(Path.home() / "customrpc_logs.txt"),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_display.toPlainText())
                
                QMessageBox.information(self, "Success", f"Logs exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export logs: {e}")
