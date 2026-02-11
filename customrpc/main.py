"""
CustomRPC Manager - Main Application Entry Point

A cross-platform Discord Rich Presence manager with GUI and CLI support.
"""

import sys
import signal
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer, QSocketNotifier

# Import core modules
from customrpc.core.config_manager import ConfigManager
from customrpc.core.profile_manager import ProfileManager
from customrpc.core.rpc_manager import RPCManager
from customrpc.core.startup_manager import StartupManager

# Import utilities
from customrpc.utils.logger import LoggerManager
from customrpc.utils.ipc import SingleInstanceManager, IPCServer, IPCClient
from customrpc.utils.assets import get_icon_path

# Import CLI
from customrpc.cli.cli_parser import CLIParser
from customrpc.cli.cli_controller import CLIController

# Import GUI
from customrpc.gui.main_window import MainWindow
from customrpc.tray.tray_manager import TrayManager


class CustomRPCApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize application."""
        # Initialize configuration
        self.config = ConfigManager()
        
        # Initialize logger
        self.logger_manager = LoggerManager(
            self.config.logs_dir,
            "customrpc"
        )
        self.logger = self.logger_manager.get_logger()
        
        # Initialize managers
        self.profiles = ProfileManager(self.config.profiles_dir)
        self.rpc = RPCManager()
        self.startup = StartupManager("CustomRPC")
        
        # Single instance management
        lock_file = self.config.config_dir / ".lock"
        port_file = self.config.config_dir / ".port"
        self.instance_manager = SingleInstanceManager(lock_file, port_file)
        
        # GUI components
        self.app: QApplication = None
        self.main_window: MainWindow = None
        self.tray: TrayManager = None
        
        # IPC server for receiving commands
        self.ipc_server: IPCServer = None
        
        # CLI controller
        self.cli = None
        
        self.logger.info("CustomRPC Manager initialized")
    
    def run(self):
        """Run the application."""
        # Parse CLI arguments
        parser = CLIParser()
        args, is_headless = parser.parse()

        # Set debug logging if requested
        if args.debug:
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("Debug logging enabled")

        # Try to acquire single instance lock
        # if another instance is already running, check if we have CLI commands
        if not self.instance_manager.acquire_lock():
            self.logger.info("Another instance is already running")
            
            # If we have CLI commands, send them to the running instance
            if is_headless:
                port = self.instance_manager.get_port()
                if port:
                    self.logger.info(f"Sending commands to running instance on port {port}")
                    ipc_client = IPCClient(port)
                    
                    # Build command from CLI args
                    command = self._build_command_from_args(args)
                    if command:
                        response = ipc_client.send_command(command)
                        if response.get('success'):
                            # Print output if available
                            if 'output' in response:
                                print(response['output'], end='')
                            return 0
                        else:
                            error = response.get('error', 'Unknown error')
                            self.logger.error(f"Failed to send command: {error}")
                            return 1
                    else:
                        self.logger.error("Failed to build command")
                        return 1
                else:
                    self.logger.error("Cannot communicate with running instance.")
                    return 1
            else:
                # no cli commands, exit
                self.logger.error("CustomRPC Manager is already running.")
                self.logger.error("Check your system tray or use the running instance.")
                return 0
        
        # No other instance is running, continue

        # Create QApplication
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("CustomRPC Manager")
        self.app.setQuitOnLastWindowClosed(False)  # Don't quit when window closes
        
        # Set application icon
        icon_path = get_icon_path()
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))
        else:
            self.logger.warning(f"Icon not found at {icon_path}")
        
        # Initialize CLI controller
        self.cli = CLIController(self.config, self.profiles, self.rpc)
        
        # Start IPC server for receiving commands
        self.ipc_server = IPCServer(response_callback=self._handle_ipc_command)
        port = self.ipc_server.start()
        self.instance_manager.save_port(port)
        
        # Setup socket notifier for non-blocking IPC command handling
        # QSocketNotifier triggers only when data is available on the socket
        socket_fd = self.ipc_server.socket.fileno()
        self.socket_notifier = QSocketNotifier(
            socket_fd,
            QSocketNotifier.Type.Read,
            self.app
        )
        self.socket_notifier.activated.connect(self._check_ipc_commands)
        
        # Create system tray
        self.tray = TrayManager(self.app)
        self.tray.show_window.connect(self._show_main_window)
        self.tray.connect_requested.connect(self._handle_connect)
        self.tray.disconnect_requested.connect(self._handle_disconnect)
        self.tray.show_logs.connect(self._show_logs)
        self.tray.quit_signal.connect(self._quit_application)
        
        # Handle CLI commands if in headless mode
        if is_headless:
            self._handle_cli_commands(args)
            # Don't show main window, but keep tray running
        else:
            # Create and show main window
            self._create_main_window()
            
            # Show window unless starting minimized
            if not (args.minimized or self.config.get('start_minimized', False)):
                self.main_window.show()
            
            # Handle auto-connect
            if self.config.get('auto_connect', False):
                profile_name = self.config.get('auto_connect_profile')
                if profile_name:
                    self.logger.info(f"Auto-connecting with profile: {profile_name}")
                    self._auto_connect(profile_name)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, lambda sig, frame: self._quit_application())
        signal.signal(signal.SIGTERM, lambda sig, frame: self._quit_application())
        signal.signal(signal.SIGINT, signal.SIG_DFL) 
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        
        # Run application
        self.logger.info("Application started")
        return self.app.exec()
    
    def _create_main_window(self):
        """Create main window."""
        if not self.main_window:
            self.main_window = MainWindow(
                self.app,
                self.config,
                self.profiles,
                self.rpc,
                self.startup,
                self.logger_manager
            )
            self.main_window.connect_requested.connect(self._handle_connect)
            self.main_window.disconnect_requested.connect(self._handle_disconnect)
            self.main_window.window_closed.connect(self._quit_application)
    
    def _show_main_window(self):
        """Show main window."""
        if not self.main_window:
            self._create_main_window()
        
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
    
    def _show_logs(self):
        """Show log viewer."""
        self._show_main_window()
        self.main_window._show_logs()
    
    def _handle_connect(self):
        """Handle connect request."""
        if not self.main_window:
            return
        
        # Get form data
        data = self.main_window.rpc_form.get_data()
        app_id = data.get('app_id')
        
        if not app_id:
            return
        
        # Connect
        if self.rpc.connect(app_id):
            # Update activity
            activity = self._build_activity(data)
            self.rpc.update_activity(activity)
            
            # Update UI
            profile_name = self.main_window.profile_combo.currentText()
            self.main_window.update_connection_status(True, f"Connected - {profile_name}")
            self.tray.update_status(True)
            self.tray.show_message("CustomRPC", "Connected to Discord")
        else:
            self.main_window.update_connection_status(False, "Connection Failed")
            self.tray.update_status(False)
    
    def _handle_disconnect(self):
        """Handle disconnect request."""
        self.rpc.disconnect()
        
        if self.main_window:
            self.main_window.update_connection_status(False)
        
        self.tray.update_status(False)
        self.tray.show_message("CustomRPC", "Disconnected from Discord")
    
    def _auto_connect(self, profile_name: str):
        """Auto-connect with profile."""
        profile = self.profiles.load_profile(profile_name)
        if not profile:
            self.logger.error(f"Auto-connect profile '{profile_name}' not found")
            return
        
        app_id = profile.get('app_id')
        if not app_id:
            self.logger.error(f"Profile '{profile_name}' missing app_id")
            return
        
        if self.rpc.connect(app_id):
            activity = self._build_activity(profile)
            self.rpc.update_activity(activity)
            
            if self.main_window:
                self.main_window.update_connection_status(True, f"Connected - {profile_name}")
            
            self.tray.update_status(True)
            self.logger.info(f"Auto-connected with profile '{profile_name}'")
    
    def _build_activity(self, data: dict) -> dict:
        """Build activity dict from profile data."""
        activity = {}

        if data.get('name'):
            activity['name'] = data['name']
        if data.get('details'):
            activity['details'] = data['details']
        if data.get('state'):
            activity['state'] = data['state']
        
        if data.get('start_timestamp'):
            activity['start'] = data['start_timestamp']
        if data.get('end_timestamp'):
            activity['end'] = data['end_timestamp']
        
        if data.get('large_image_key'):
            activity['large_image'] = data['large_image_key']
        if data.get('large_image_text'):
            activity['large_text'] = data['large_image_text']
        if data.get('small_image_key'):
            activity['small_image'] = data['small_image_key']
        if data.get('small_image_text'):
            activity['small_text'] = data['small_image_text']
        
        if data.get('party_size') and data.get('party_max'):
            activity['party_size'] = [data['party_size'], data['party_max']]
        
        buttons = data.get('buttons', [])
        if buttons:
            activity['buttons'] = buttons
        
        if data.get('instance') is not None:
            activity['instance'] = data['instance']
        
        return activity
    
    def _build_command_from_args(self, args) -> dict:
        """Build IPC command from CLI arguments.
        
        Args:
            args: Parsed CLI arguments
            
        Returns:
            Command dictionary
        """
        command = {}
        
        if args.list_profiles:
            command['action'] = 'list_profiles'
        elif args.quit:
            command['action'] = 'quit'
        elif args.disconnect:
            command['action'] = 'disconnect'
        elif args.connect:
            command['action'] = 'connect'
            if args.profile:
                command['profile'] = args.profile
        elif args.profile:
            command['action'] = 'load_profile'
            command['profile'] = args.profile
        
        return command
    
    def _handle_cli_commands(self, args):
        """Handle CLI commands in headless mode.
        
        Args:
            args: Parsed CLI arguments
        """
        # Execute commands but don't exit - keep app running in tray
        if args.list_profiles:
            self.cli.execute_list_profiles()
        elif args.quit:
            self._quit_application()
        elif args.disconnect:
            self._handle_disconnect()
        elif args.connect:
            profile_name = args.profile if args.profile else None
            if profile_name:
                # Load profile and connect
                profile = self.profiles.load_profile(profile_name)
                if profile:
                    app_id = profile.get('app_id')
                    if app_id and self.rpc.connect(app_id):
                        activity = self._build_activity(profile)
                        self.rpc.update_activity(activity)
                        self.tray.update_status(True)
                        self.logger.info(f"Connected with profile: {profile_name}")
            else:
                self.logger.warning("No profile specified for connect command")
        elif args.profile:
            self.cli.execute_load_profile(args.profile)
    
    def _check_ipc_commands(self):
        """Check and process IPC commands from CLI."""
        if not self.ipc_server:
            return
        
        # Note: The command is handled by the response_callback set in IPC server
        # We just need to accept the connection
        command = self.ipc_server.accept_connection()
    
    def _handle_ipc_command(self, command: dict) -> dict:
        """Handle an IPC command and return response.
        
        Args:
            command: Command dictionary
            
        Returns:
            Response dictionary with output
        """
        import io
        import sys
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            output = self._process_ipc_command(command)
            captured = sys.stdout.getvalue()
            
            # Combine explicitly returned output with captured stdout
            if output:
                full_output = output + captured
            else:
                full_output = captured
            
            return {
                'success': True,
                'output': full_output
            }
        except Exception as e:
            captured = sys.stdout.getvalue()
            self.logger.error(f"Error processing IPC command: {e}")
            return {
                'success': False,
                'error': str(e),
                'output': captured
            }
        finally:
            sys.stdout = old_stdout
    
    def _process_ipc_command(self, command: dict) -> str:
        """Process an IPC command.
        
        Args:
            command: Command dictionary
            
        Returns:
            Output string from command execution
        """
        action = command.get('action')
        self.logger.info(f"Processing IPC command: {action}")
        output = ""
        
        if action == 'list_profiles':
            # Capture output from list_profiles
            self.cli.execute_list_profiles()
        elif action == 'quit':
            output = "Quitting application...\n"
            # Use QTimer to quit after response is sent
            QTimer.singleShot(100, self._quit_application)
        elif action == 'disconnect':
            self._handle_disconnect()
            output = "Disconnected from Discord RPC\n"
            self.tray.show_message("CustomRPC", "Disconnected via CLI")
        elif action == 'connect':
            profile_name = command.get('profile')
            if profile_name:
                # Load profile and connect
                profile = self.profiles.load_profile(profile_name)
                if profile:
                    app_id = profile.get('app_id')
                    if app_id and self.rpc.connect(app_id):
                        activity = self._build_activity(profile)
                        self.rpc.update_activity(activity)
                        self.tray.update_status(True)
                        output = f"Connected to Discord RPC with profile: {profile_name}\n"
                        self.tray.show_message("CustomRPC", f"Connected with profile: {profile_name}")
                        if self.main_window:
                            self.main_window.update_connection_status(True, f"Connected - {profile_name}")
                    else:
                        output = "Failed to connect to Discord RPC\n"
                else:
                    output = f"Profile '{profile_name}' not found\n"
            else:
                # Connect with current settings if main_window exists
                if self.main_window:
                    self._handle_connect()
                    output = "Connected to Discord RPC\n"
                else:
                    output = "Cannot connect without profile in headless mode\n"
                    self.logger.warning("Cannot connect without profile in headless mode")
        elif action == 'load_profile':
            profile_name = command.get('profile')
            if profile_name:
                exit_code = self.cli.execute_load_profile(profile_name)
                if exit_code == 0:
                    if self.main_window:
                        # Update UI if window exists
                        if profile_name in self.profiles.list_profiles():
                            self.main_window.profile_combo.setCurrentText(profile_name)
                            self.main_window._load_selected_profile()
                else:
                    output = f"Failed to load profile '{profile_name}'\n"
        
        return output
    

    def _quit_application(self):
        """Quit application."""
        self.logger.info("Quitting application")
        
        # Stop socket notifier
        if hasattr(self, 'socket_notifier') and self.socket_notifier:
            self.socket_notifier.setEnabled(False)
        
        # Stop IPC server
        if self.ipc_server:
            self.ipc_server.stop()
        
        # Disconnect RPC
        if self.rpc.is_connected():
            self.rpc.disconnect()
        
        # Cleanup instance manager
        self.instance_manager.cleanup()
        
        # Quit app
        if self.app:
            self.app.quit()


def main():
    """Main entry point."""
    app = CustomRPCApp()
    sys.exit(app.run())

if __name__ == "__main__":
    main()
