"""
System tray manager for CustomRPC.

Provides system tray icon and menu integration.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal
from customrpc.utils.assets import get_icon_path
import logging


class TrayManager(QObject):
    """Manages system tray icon and menu."""
    
    # Signals
    show_window = pyqtSignal()
    connect_requested = pyqtSignal()
    disconnect_requested = pyqtSignal()
    show_logs = pyqtSignal()
    quit_signal = pyqtSignal()
    
    def __init__(self, app):
        """
        Initialize tray manager.
        
        Args:
            app: QApplication instance
        """
        super().__init__()
        self.app = app
        self.logger = logging.getLogger("customrpc.tray")
        self.tray_icon = None
        self.setup_tray()
    
    def setup_tray(self) -> None:
        """Setup system tray icon and menu."""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # Set tray icon
        icon_path = get_icon_path()
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            # Fallback to default icon
            icon = self.app.style().standardIcon(self.app.style().StandardPixmap.SP_ComputerIcon)
            self.logger.warning(f"Icon not found at {icon_path}, using default")
            
        self.tray_icon.setIcon(icon)
        
        # Create context menu
        menu = QMenu()
        
        # Show/Hide action
        self.show_action = QAction("Open CustomRPC", menu)
        self.show_action.triggered.connect(self.show_window.emit)
        menu.addAction(self.show_action)
        
        menu.addSeparator()
        
        # Connect action
        self.connect_action = QAction("Connect", menu)
        self.connect_action.triggered.connect(self.connect_requested.emit)
        menu.addAction(self.connect_action)
        
        # Disconnect action
        self.disconnect_action = QAction("Disconnect", menu)
        self.disconnect_action.triggered.connect(self.disconnect_requested.emit)
        self.disconnect_action.setEnabled(False)
        menu.addAction(self.disconnect_action)
        
        menu.addSeparator()
        
        # View logs action
        logs_action = QAction("View Logs", menu)
        logs_action.triggered.connect(self.show_logs.emit)
        menu.addAction(logs_action)
        
        menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit_signal.emit)
        menu.addAction(quit_action)
        
        # Set menu
        self.tray_icon.setContextMenu(menu)
        
        # Double-click to show window
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # Show tray icon
        self.tray_icon.show()
        self.logger.info("System tray icon initialized")
    
    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        Handle tray icon activation.
        
        Args:
            reason: Activation reason
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window.emit()
    
    def update_status(self, connected: bool) -> None:
        """
        Update tray icon status.
        
        Args:
            connected: Whether RPC is connected
        """
        if connected:
            self.tray_icon.setToolTip("CustomRPC - Connected")
            self.connect_action.setEnabled(False)
            self.disconnect_action.setEnabled(True)
        else:
            self.tray_icon.setToolTip("CustomRPC - Disconnected")
            self.connect_action.setEnabled(True)
            self.disconnect_action.setEnabled(False)
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information) -> None:
        """
        Show tray notification.
        
        Args:
            title: Notification title
            message: Notification message
            icon: Notification icon
        """
        if self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(title, message, icon, 3000)
    
    def hide(self) -> None:
        """Hide tray icon."""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def show(self) -> None:
        """Show tray icon."""
        if self.tray_icon:
            self.tray_icon.show()
