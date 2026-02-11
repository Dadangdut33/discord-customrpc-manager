"""
Inter-Process Communication for single instance management.

Ensures only one instance of the application runs at a time and
allows CLI to communicate with running instances.
"""

import json
import socket
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Platform-specific imports
if sys.platform == "win32":
    import msvcrt
    import os
else:
    import fcntl


class IPCServer:
    """IPC server for receiving commands from CLI."""
    
    def __init__(self, port: int = 0, response_callback=None):
        """
        Initialize IPC server.
        
        Args:
            port: Port to bind to (0 for automatic assignment)
            response_callback: Optional callback function that takes a command dict
                             and returns a response dict to send back to client
        """
        self.socket: Optional[socket.socket] = None
        self.port = port
        self.response_callback = response_callback
        self.logger = logging.getLogger("customrpc.ipc")
        
    def start(self) -> int:
        """
        Start IPC server.
        
        Returns:
            Port number the server is listening on
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('127.0.0.1', self.port))
            self.socket.listen(1)
            self.socket.setblocking(False)  # Non-blocking mode
            
            # Get actual port if auto-assigned
            self.port = self.socket.getsockname()[1]
            self.logger.info(f"IPC server started on port {self.port}")
            return self.port
            
        except Exception as e:
            self.logger.error(f"Failed to start IPC server: {e}")
            raise
    
    def accept_connection(self) -> Optional[Dict[str, Any]]:
        """
        Accept and process one connection.
        
        Returns:
            Command dictionary if received, None if no connection available
        """
        try:
            conn, addr = self.socket.accept()
            with conn:
                data = conn.recv(4096)
                if data:
                    command = json.loads(data.decode('utf-8'))
                    self.logger.info(f"Received command: {command}")
                    
                    # If callback is set, get response and send it
                    if self.response_callback:
                        response = self.response_callback(command)
                        response_data = json.dumps(response).encode('utf-8')
                        conn.sendall(response_data)
                    else:
                        # Send simple acknowledgment
                        conn.sendall(b'OK')
                    
                    return command
        except BlockingIOError:
            # No connection available in non-blocking mode
            return None
        except Exception as e:
            self.logger.error(f"Error accepting connection: {e}")
            return None
    
    def stop(self) -> None:
        """Stop IPC server."""
        if self.socket:
            try:
                self.socket.close()
                self.logger.info("IPC server stopped")
            except Exception as e:
                self.logger.error(f"Error stopping IPC server: {e}")


class IPCClient:
    """IPC client for sending commands to running instance."""
    
    def __init__(self, port: int):
        """
        Initialize IPC client.
        
        Args:
            port: Port to connect to
        """
        self.port = port
        self.logger = logging.getLogger("customrpc.ipc")
    
    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send command to running instance.
        
        Args:
            command: Command dictionary
            
        Returns:
            Response dictionary from server
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)  # Increased timeout for response
                s.connect(('127.0.0.1', self.port))
                s.sendall(json.dumps(command).encode('utf-8'))
                
                # Receive response
                response_data = s.recv(4096)
                if response_data:
                    try:
                        # Try to parse as JSON (new protocol)
                        response = json.loads(response_data.decode('utf-8'))
                        return response
                    except json.JSONDecodeError:
                        # Legacy "OK" response
                        if response_data == b'OK':
                            return {'success': True}
                        return {'success': False, 'error': 'Invalid response'}
                return {'success': False, 'error': 'No response'}
        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
            return {'success': False, 'error': str(e)}


class SingleInstanceManager:
    """Manages single instance lock using file locking."""
    
    def __init__(self, lock_file: Path, port_file: Path):
        """
        Initialize single instance manager.
        
        Args:
            lock_file: Path to lock file
            port_file: Path to file storing IPC port
        """
        self.lock_file = lock_file
        self.port_file = port_file
        self.lock_fd: Optional[Any] = None
        self.logger = logging.getLogger("customrpc.ipc")
        
        # Ensure parent directory exists
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
    
    def acquire_lock(self) -> bool:
        """
        Try to acquire single instance lock.
        
        Returns:
            True if lock acquired, False if another instance is running
        """
        try:
            # Open or create lock file
            self.lock_fd = open(self.lock_file, 'w')
            
            if sys.platform == "win32":
                # Windows file locking
                try:
                    msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
                    # Write PID to lock file
                    self.lock_fd.write(str(os.getpid()))
                    self.lock_fd.flush()
                    self.logger.info(f"Lock acquired (PID: {os.getpid()})")
                    return True
                except OSError:
                    self.logger.info("Another instance is running")
                    return False
            else:
                # Unix file locking
                try:
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    # Write PID to lock file
                    self.lock_fd.write(str(os.getpid()))
                    self.lock_fd.flush()
                    self.logger.info(f"Lock acquired (PID: {os.getpid()})")
                    return True
                except IOError:
                    self.logger.info("Another instance is running")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error acquiring lock: {e}")
            return False
    
    def release_lock(self) -> None:
        """Release single instance lock."""
        if self.lock_fd:
            try:
                if sys.platform == "win32":
                    msvcrt.locking(self.lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                self.lock_file.unlink(missing_ok=True)
                self.logger.info("Lock released")
            except Exception as e:
                self.logger.error(f"Error releasing lock: {e}")
    
    def save_port(self, port: int) -> None:
        """
        Save IPC port to file.
        
        Args:
            port: Port number to save
        """
        try:
            self.port_file.write_text(str(port))
        except Exception as e:
            self.logger.error(f"Error saving port: {e}")
    
    def get_port(self) -> Optional[int]:
        """
        Get IPC port from file.
        
        Returns:
            Port number or None if not found
        """
        try:
            if self.port_file.exists():
                return int(self.port_file.read_text().strip())
        except Exception as e:
            self.logger.error(f"Error reading port: {e}")
        return None
    
    def get_pid(self) -> Optional[int]:
        """
        Get PID from lock file.
        
        Returns:
            PID number or None if not found
        """
        try:
            if self.lock_file.exists():
                pid_str = self.lock_file.read_text().strip()
                if pid_str:
                    return int(pid_str)
        except Exception as e:
            self.logger.error(f"Error reading PID: {e}")
        return None
    
    def is_process_running(self, pid: int) -> bool:
        """
        Check if a process with given PID is running.
        
        Args:
            pid: Process ID to check
            
        Returns:
            True if process is running
        """
        try:
            if sys.platform == "win32":
                # Windows: try to open the process
                import ctypes
                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_INFORMATION = 0x0400
                handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                # Unix: send signal 0 (doesn't actually send a signal, just checks)
                os.kill(pid, 0)
                return True
        except (OSError, ProcessLookupError):
            return False
        except Exception as e:
            self.logger.error(f"Error checking if process is running: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up lock and port files."""
        self.release_lock()
        self.port_file.unlink(missing_ok=True)
