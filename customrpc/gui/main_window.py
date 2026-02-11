"""
Main application window for CustomRPC Manager.

Provides the primary GUI interface with menu bar, profile selector,
RPC form, and controls.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QStatusBar, QMessageBox,
    QMenuBar, QMenu, QScrollArea
)
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtCore import Qt, pyqtSignal
import logging
from pathlib import Path

from customrpc.gui.rpc_form import RPCForm
from customrpc.gui.log_viewer import LogViewer
from customrpc.gui.settings_dialog import SettingsDialog
from customrpc.gui import profile_dialog


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    connect_requested = pyqtSignal()
    disconnect_requested = pyqtSignal()
    window_closed = pyqtSignal()
    
    def __init__(self, config_manager, profile_manager, rpc_manager, startup_manager, logger_manager):
        """
        Initialize main window.
        
        Args:
            config_manager: Configuration manager instance
            profile_manager: Profile manager instance
            rpc_manager: RPC manager instance
            startup_manager: Startup manager instance
            logger_manager: Logger manager instance
        """
        super().__init__()
        self.config = config_manager
        self.profiles = profile_manager
        self.rpc = rpc_manager
        self.startup = startup_manager
        self.logger_manager = logger_manager
        self.logger = logging.getLogger("customrpc.gui")
        
        self.log_viewer = None
        self.unsaved_changes = False
        
        self.setup_ui()
        self.load_profiles()
        self.load_last_profile()
        self.apply_theme()
    
    def setup_ui(self) -> None:
        """Setup UI components."""
        self.setWindowTitle("CustomRPC Manager")
        self.resize(600, 800)
        
        # Setup menu bar
        self.setup_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Profile selector
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Profile:"))
        
        self.profile_combo = QComboBox()
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)
        profile_layout.addWidget(self.profile_combo, 1)
        
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._load_selected_profile)
        profile_layout.addWidget(load_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_current_profile)
        profile_layout.addWidget(save_btn)
        
        layout.addLayout(profile_layout)
        
        # RPC Form (in scroll area)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.rpc_form = RPCForm()
        self.rpc_form.data_changed.connect(self._on_form_changed)
        scroll.setWidget(self.rpc_form)
        
        layout.addWidget(scroll, 1)
        
        # Controls
        control_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        self.connect_btn.setStyleSheet("QPushButton { font-weight: bold; min-height: 30px; }")
        control_layout.addWidget(self.connect_btn)
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("QLabel { padding: 5px; }")
        control_layout.addWidget(self.status_label)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def setup_menu_bar(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_profile_action = QAction("New Profile", self)
        new_profile_action.triggered.connect(self._create_new_profile)
        file_menu.addAction(new_profile_action)
        
        file_menu.addSeparator()
        
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.window_closed.emit)
        file_menu.addAction(quit_action)

        # Profiles menu
        profiles_menu = menubar.addMenu("Profiles")
        
        rename_action = QAction("Rename Current Profile", self)
        rename_action.triggered.connect(self._rename_current_profile)
        profiles_menu.addAction(rename_action)
        
        duplicate_action = QAction("Duplicate Current Profile", self)
        duplicate_action.triggered.connect(self._duplicate_current_profile)
        profiles_menu.addAction(duplicate_action)
        
        delete_action = QAction("Delete Current Profile", self)
        delete_action.triggered.connect(self._delete_current_profile)
        profiles_menu.addAction(delete_action)
        
        profiles_menu.addSeparator()
        
        export_action = QAction("Export Current Profile", self)
        export_action.triggered.connect(self._export_current_profile)
        profiles_menu.addAction(export_action)
        
        import_action = QAction("Import Profile", self)
        import_action.triggered.connect(self._import_profile)
        profiles_menu.addAction(import_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        logs_action = QAction("View Logs", self)
        logs_action.triggered.connect(self._show_logs)
        view_menu.addAction(logs_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self._show_settings)
        settings_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def load_profiles(self) -> None:
        """Load all profiles into combo box."""
        current = self.profile_combo.currentText()
        self.profile_combo.clear()
        
        profiles = self.profiles.list_profiles()
        if profiles:
            self.profile_combo.addItems(profiles)
            
            # Restore selection if possible
            if current in profiles:
                self.profile_combo.setCurrentText(current)
    
    def load_last_profile(self) -> None:
        """Load the last used profile."""
        last_profile = self.config.get('last_profile')
        if last_profile:
            profiles = self.profiles.list_profiles()
            if last_profile in profiles:
                self.profile_combo.setCurrentText(last_profile)
                self._load_selected_profile()
    
    def _on_profile_changed(self, profile_name: str) -> None:
        """Handle profile selection change."""
        if profile_name:
            self.status_bar.showMessage(f"Selected profile: {profile_name}")
    
    def _on_form_changed(self) -> None:
        """Handle form data change."""
        self.unsaved_changes = True
        self.status_bar.showMessage("Unsaved changes")
    
    def _load_selected_profile(self) -> None:
        """Load selected profile into form."""
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return
        
        profile_data = self.profiles.load_profile(profile_name)
        if profile_data:
            self.rpc_form.set_data(profile_data)
            self.config.set('last_profile', profile_name)
            self.unsaved_changes = False
            self.status_bar.showMessage(f"Loaded profile: {profile_name}")
            self.logger.info(f"Loaded profile: {profile_name}")
    
    def _save_current_profile(self) -> None:
        """Save current form data to profile."""
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            QMessageBox.warning(self, "No Profile", "Please create or select a profile first.")
            return
        
        # Validate form
        valid, error = self.rpc_form.validate()
        if not valid:
            QMessageBox.warning(self, "Validation Error", error)
            return
        
        # Get form data
        data = self.rpc_form.get_data()
        
        # Update profile
        if self.profiles.update_profile(profile_name, data):
            self.unsaved_changes = False
            self.status_bar.showMessage(f"Saved profile: {profile_name}")
            QMessageBox.information(self, "Success", f"Profile '{profile_name}' saved successfully.")
        else:
            QMessageBox.critical(self, "Error", f"Failed to save profile '{profile_name}'.")
    
    def _create_new_profile(self) -> None:
        """Create a new profile."""
        name = profile_dialog.show_create_profile_dialog(self)
        if name:
            # Create with current form data or empty
            data = self.rpc_form.get_data() if self.rpc_form.get_data()['app_id'] else {}
            
            if self.profiles.create_profile(name, data):
                self.load_profiles()
                self.profile_combo.setCurrentText(name)
                QMessageBox.information(self, "Success", f"Profile '{name}' created successfully.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to create profile '{name}'.")
    
    def _rename_current_profile(self) -> None:
        """Rename current profile."""
        old_name = self.profile_combo.currentText()
        if not old_name:
            return
        
        new_name = profile_dialog.show_rename_profile_dialog(old_name, self)
        if new_name and new_name != old_name:
            if self.profiles.rename_profile(old_name, new_name):
                self.load_profiles()
                self.profile_combo.setCurrentText(new_name)
                self.config.set('last_profile', new_name)
                QMessageBox.information(self, "Success", f"Profile renamed to '{new_name}'.")
            else:
                QMessageBox.critical(self, "Error", "Failed to rename profile.")
    
    def _duplicate_current_profile(self) -> None:
        """Duplicate current profile."""
        source_name = self.profile_combo.currentText()
        if not source_name:
            return
        
        new_name = profile_dialog.show_duplicate_profile_dialog(source_name, self)
        if new_name:
            if self.profiles.duplicate_profile(source_name, new_name):
                self.load_profiles()
                self.profile_combo.setCurrentText(new_name)
                QMessageBox.information(self, "Success", f"Profile duplicated as '{new_name}'.")
            else:
                QMessageBox.critical(self, "Error", "Failed to duplicate profile.")
    
    def _delete_current_profile(self) -> None:
        """Delete current profile."""
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return
        
        if profile_dialog.show_delete_profile_dialog(profile_name, self):
            if self.profiles.delete_profile(profile_name):
                self.load_profiles()
                self.rpc_form.clear()
                QMessageBox.information(self, "Success", f"Profile '{profile_name}' deleted.")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete profile.")
    
    def _export_current_profile(self) -> None:
        """Export current profile."""
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            return
        
        export_path = profile_dialog.show_export_profile_dialog(profile_name, self)
        if export_path:
            if self.profiles.export_profile(profile_name, Path(export_path)):
                QMessageBox.information(self, "Success", f"Profile exported to {export_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export profile.")
    
    def _import_profile(self) -> None:
        """Import a profile."""
        import_path = profile_dialog.show_import_profile_dialog(self)
        if import_path:
            if self.profiles.import_profile(Path(import_path)):
                self.load_profiles()
                QMessageBox.information(self, "Success", "Profile imported successfully.")
            else:
                QMessageBox.critical(self, "Error", "Failed to import profile.")
    
    def _on_connect_clicked(self) -> None:
        """Handle connect/disconnect button click."""
        if self.rpc.is_connected():
            self.disconnect_requested.emit()
        else:
            # Validate form first
            valid, error = self.rpc_form.validate()
            if not valid:
                QMessageBox.warning(self, "Validation Error", error)
                return
            
            self.connect_requested.emit()
    
    def update_connection_status(self, connected: bool, status_text: str = "") -> None:
        """
        Update UI based on connection status.
        
        Args:
            connected: Whether RPC is connected
            status_text: Optional status text
        """
        if connected:
            self.connect_btn.setText("Disconnect")
            self.status_label.setText(status_text or "Connected")
            self.status_label.setStyleSheet("QLabel { background-color: #4CAF50; color: white; padding: 5px; border-radius: 3px; }")
        else:
            self.connect_btn.setText("Connect")
            self.status_label.setText(status_text or "Disconnected")
            self.status_label.setStyleSheet("QLabel { background-color: #f44336; color: white; padding: 5px; border-radius: 3px; }")
    
    def _show_logs(self) -> None:
        """Show log viewer window."""
        if self.log_viewer is None:
            self.log_viewer = LogViewer(self.logger_manager, self)
        
        self.log_viewer.show()
        self.log_viewer.raise_()
        self.log_viewer.activateWindow()
    
    def _show_settings(self) -> None:
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self.startup, self.profiles, self)
        dialog.settings_changed.connect(self.apply_theme)
        dialog.exec()
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About CustomRPC Manager",
            "<h3>CustomRPC Manager 1.0</h3>"
            "<p>A simple custom Discord Rich Presence manager.</p>"
            "<p>A tool to help managing custom RPC to your Discord status.</p>"
            "<p><b>Technologies:</b> Python, PyQt6, pypresence</p>"
        )
    
    def apply_theme(self) -> None:
        """Apply theme from config."""
        theme = self.config.get('theme', 'dark')
        
        # Load theme file
        theme_file = Path(__file__).parent.parent / "resources" / "themes" / f"{theme}.qss"
        
        if theme_file.exists():
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                self.logger.info(f"Applied {theme} theme from {theme_file}")
            except Exception as e:
                self.logger.error(f"Failed to load theme file: {e}")
        else:
            self.logger.warning(f"Theme file not found: {theme_file}")
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close event.
        
        Args:
            event: Close event
        """
        # Check if should minimize to tray
        if self.config.get('minimize_to_tray', True):
            event.ignore()
            self.hide()
            self.logger.info("Window minimized to tray")
        else:
            # Confirm if unsaved changes
            if self.unsaved_changes:
                reply = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    "You have unsaved changes. Are you sure you want to quit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    event.ignore()
                    return
            
            self.window_closed.emit()
            event.accept()
