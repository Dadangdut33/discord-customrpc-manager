"""
Settings dialog for application configuration.

Allows users to configure theme, autostart, and other preferences.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox,
    QCheckBox, QPushButton, QHBoxLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    # Signal emitted when settings change
    settings_changed = pyqtSignal()
    
    def __init__(self, config_manager, startup_manager, profile_manager, parent=None):
        """
        Initialize settings dialog.
        
        Args:
            config_manager: Configuration manager instance
            startup_manager: Startup manager instance
            profile_manager: Profile manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config_manager
        self.startup = startup_manager
        self.profiles = profile_manager
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self) -> None:
        """Setup UI components."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Appearance
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Startup
        startup_group = QGroupBox("Startup")
        startup_layout = QVBoxLayout()
        
        self.run_on_startup_check = QCheckBox("Run on system startup")
        startup_layout.addWidget(self.run_on_startup_check)
        
        self.start_minimized_check = QCheckBox("Start minimized to tray")
        startup_layout.addWidget(self.start_minimized_check)
        
        self.auto_connect_check = QCheckBox("Auto-connect on startup")
        self.auto_connect_check.toggled.connect(self._on_auto_connect_toggled)
        startup_layout.addWidget(self.auto_connect_check)
        
        # Auto-connect profile
        profile_layout = QFormLayout()
        self.auto_connect_profile = QComboBox()
        self.auto_connect_profile.setEnabled(False)
        profile_layout.addRow("Auto-connect profile:", self.auto_connect_profile)
        startup_layout.addLayout(profile_layout)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # Behavior
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout()
        
        self.minimize_to_tray_check = QCheckBox("Minimize to tray")
        behavior_layout.addWidget(self.minimize_to_tray_check)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_auto_connect_toggled(self, checked: bool) -> None:
        """Handle auto-connect checkbox toggle."""
        self.auto_connect_profile.setEnabled(checked)
    
    def load_settings(self) -> None:
        """Load settings from config."""
        # Theme
        theme = self.config.get('theme', 'dark')
        self.theme_combo.setCurrentText(theme.title())
        
        # Startup
        self.run_on_startup_check.setChecked(self.config.get('run_on_startup', False))
        self.start_minimized_check.setChecked(self.config.get('start_minimized', False))
        self.auto_connect_check.setChecked(self.config.get('auto_connect', False))
        
        # Load profiles
        profiles = self.profiles.list_profiles()
        self.auto_connect_profile.clear()
        self.auto_connect_profile.addItems(profiles)
        
        # Set current auto-connect profile
        auto_profile = self.config.get('auto_connect_profile')
        if auto_profile and auto_profile in profiles:
            self.auto_connect_profile.setCurrentText(auto_profile)
        
        # Behavior
        self.minimize_to_tray_check.setChecked(self.config.get('minimize_to_tray', True))

    def save_settings(self) -> None:
        """Save settings to config."""
        # Theme
        theme = self.theme_combo.currentText().lower()
        self.config.set('theme', theme)
        
        # Startup - run on startup
        run_on_startup = self.run_on_startup_check.isChecked()
        self.config.set('run_on_startup', run_on_startup)
        
        # Apply startup setting
        if run_on_startup:
            success = self.startup.enable()
            if not success:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Failed to enable run on startup. Check logs for details."
                )
        else:
            self.startup.disable()
        
        # Other startup settings
        self.config.set('start_minimized', self.start_minimized_check.isChecked())
        self.config.set('auto_connect', self.auto_connect_check.isChecked())
        
        # Auto-connect profile
        if self.auto_connect_check.isChecked():
            profile = self.auto_connect_profile.currentText()
            self.config.set('auto_connect_profile', profile)
        else:
            self.config.set('auto_connect_profile', None)
        
        # Behavior
        self.config.set('minimize_to_tray', self.minimize_to_tray_check.isChecked())
        
        # Emit signal
        self.settings_changed.emit()
        
        QMessageBox.information(self, "Success", "Settings saved successfully.")
        self.accept()
