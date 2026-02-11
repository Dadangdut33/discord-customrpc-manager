"""
Profile management dialogs.

Provides dialogs for creating, renaming, and deleting profiles.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QFileDialog
)
from pathlib import Path


class ProfileNameDialog(QDialog):
    """Dialog for entering/editing profile name."""
    
    def __init__(self, title: str, label: str, initial_value: str = "", parent=None):
        """
        Initialize profile name dialog.
        
        Args:
            title: Dialog title
            label: Label text
            initial_value: Initial name value
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(label))
        
        self.name_input = QLineEdit()
        self.name_input.setText(initial_value)
        self.name_input.selectAll()
        layout.addWidget(self.name_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def get_name(self) -> str:
        """Get entered name."""
        return self.name_input.text().strip()


def show_create_profile_dialog(parent=None) -> str:
    """
    Show create profile dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        Profile name or empty string if cancelled
    """
    dialog = ProfileNameDialog(
        "Create Profile",
        "Enter profile name:",
        parent=parent
    )
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_name()
    return ""


def show_rename_profile_dialog(current_name: str, parent=None) -> str:
    """
    Show rename profile dialog.
    
    Args:
        current_name: Current profile name
        parent: Parent widget
        
    Returns:
        New profile name or empty string if cancelled
    """
    dialog = ProfileNameDialog(
        "Rename Profile",
        "Enter new profile name:",
        initial_value=current_name,
        parent=parent
    )
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_name()
    return ""


def show_delete_profile_dialog(profile_name: str, parent=None) -> bool:
    """
    Show delete profile confirmation dialog.
    
    Args:
        profile_name: Name of profile to delete
        parent: Parent widget
        
    Returns:
        True if confirmed
    """
    result = QMessageBox.question(
        parent,
        "Delete Profile",
        f"Are you sure you want to delete profile '{profile_name}'?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    
    return result == QMessageBox.StandardButton.Yes


def show_duplicate_profile_dialog(source_name: str, parent=None) -> str:
    """
    Show duplicate profile dialog.
    
    Args:
        source_name: Name of profile to duplicate
        parent: Parent widget
        
    Returns:
        New profile name or empty string if cancelled
    """
    dialog = ProfileNameDialog(
        "Duplicate Profile",
        f"Enter name for duplicate of '{source_name}':",
        initial_value=f"{source_name} (Copy)",
        parent=parent
    )
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_name()
    return ""


def show_export_profile_dialog(profile_name: str, parent=None) -> str:
    """
    Show export profile file dialog.
    
    Args:
        profile_name: Name of profile to export
        parent: Parent widget
        
    Returns:
        Export file path or empty string if cancelled
    """
    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Export Profile",
        str(Path.home() / f"{profile_name}.json"),
        "JSON Files (*.json);;All Files (*)"
    )
    
    return file_path


def show_import_profile_dialog(parent=None) -> str:
    """
    Show import profile file dialog.
    
    Args:
        parent: Parent widget
        
    Returns:
        Import file path or empty string if cancelled
    """
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Import Profile",
        str(Path.home()),
        "JSON Files (*.json);;All Files (*)"
    )
    
    return file_path
