"""
RPC Manager for Discord Rich Presence.

Handles connection and updates to Discord RPC using pypresence.
"""

import time
import logging
from typing import Optional, Dict, Any
from threading import Thread, Event
from pypresence import Presence, InvalidID, InvalidPipe


class RPCStatus:
    """RPC connection status constants."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class RPCManager:
    """Manages Discord Rich Presence connection."""
    
    def __init__(self):
        """Initialize RPC manager."""
        self.logger = logging.getLogger("customrpcmanager.rpc")
        self.client: Optional[Presence] = None
        self.client_id: Optional[str] = None
        self.status = RPCStatus.DISCONNECTED
        self.current_activity: Optional[Dict[str, Any]] = None
        
        # Auto-reconnect thread
        self._reconnect_thread: Optional[Thread] = None
        self._reconnect_event = Event()
        self._should_reconnect = False
    
    def connect(self, client_id: str) -> bool:
        """
        Connect to Discord RPC.
        
        Args:
            client_id: Discord Application ID
            
        Returns:
            True if connected successfully
        """
        if self.status == RPCStatus.CONNECTED and self.client_id == client_id:
            self.logger.info("Already connected with same client ID")
            return True
        
        # Disconnect existing connection
        if self.client:
            self.disconnect()
        
        self.status = RPCStatus.CONNECTING
        self.client_id = client_id
        
        try:
            self.client = Presence(client_id)
            self.client.connect()
            self.status = RPCStatus.CONNECTED
            self.logger.info(f"Connected to Discord RPC with client ID: {client_id}")
            
            # Start auto-reconnect thread
            self._should_reconnect = True
            if not self._reconnect_thread or not self._reconnect_thread.is_alive():
                self._reconnect_event.clear()
                self._reconnect_thread = Thread(target=self._auto_reconnect_loop, daemon=True)
                self._reconnect_thread.start()
            
            return True
            
        except InvalidID:
            self.logger.error(f"Invalid Discord Application ID: {client_id}")
            self.status = RPCStatus.ERROR
            return False
        except InvalidPipe:
            self.logger.error("Discord is not running or RPC is not available")
            self.status = RPCStatus.ERROR
            return False
        except Exception as e:
            self.logger.error(f"Failed to connect to Discord RPC: {e}")
            self.status = RPCStatus.ERROR
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Discord RPC."""
        self._should_reconnect = False
        
        if self.client:
            try:
                self.client.close()
                self.logger.info("Disconnected from Discord RPC")
            except Exception as e:
                self.logger.error(f"Error disconnecting: {e}")
            finally:
                self.client = None
                self.status = RPCStatus.DISCONNECTED
                self.current_activity = None
        
        # Stop reconnect thread
        if self._reconnect_thread:
            self._reconnect_event.set()
    
    def update_activity(self, activity: Dict[str, Any], log_args: bool = True) -> bool:
        """
        Update Discord activity.
        
        Args:
            activity: Activity data dictionary
            
        Returns:
            True if updated successfully
        """
        if not self.client or self.status != RPCStatus.CONNECTED:
            self.logger.error("Not connected to Discord RPC")
            return False
        
        try:
            # Prepare activity data (remove None values)
            rpc_data = {k: v for k, v in activity.items() if v is not None}
            
            # Update presence
            self.logger.info(f"Updating Discord activity: {rpc_data}")
            self.client.update(**rpc_data)
            self.current_activity = activity
            self.logger.info("Updated Discord activity")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update activity: {e}")
            return False
    
    def clear_activity(self) -> bool:
        """
        Clear Discord activity.
        
        Returns:
            True if cleared successfully
        """
        if not self.client or self.status != RPCStatus.CONNECTED:
            self.logger.error("Not connected to Discord RPC")
            return False
        
        try:
            self.client.clear()
            self.current_activity = None
            self.logger.info("Cleared Discord activity")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear activity: {e}")
            return False
    
    def _auto_reconnect_loop(self) -> None:
        """Auto-reconnect loop running in background thread."""
        while self._should_reconnect:
            # Check connection status
            if self.status == RPCStatus.CONNECTED and self.client:
                try:
                    # Try to update with current activity to check connection
                    if self.current_activity:
                        self.update_activity(self.current_activity, log_args=False)
                except Exception as e:
                    self.logger.warning(f"Connection lost, attempting reconnect: {e}")
                    self.status = RPCStatus.DISCONNECTED
                    
                    # Try to reconnect
                    if self.client_id:
                        self.logger.info("Attempting to reconnect...")
                        self.connect(self.client_id)
                        
                        # Restore activity if reconnected
                        if self.status == RPCStatus.CONNECTED and self.current_activity:
                            self.update_activity(self.current_activity, log_args=False)
            
            # Wait before next check (with early exit on event)
            if self._reconnect_event.wait(timeout=10):
                self._reconnect_thread = None # clear the thread
                break
    
    def get_status(self) -> str:
        """Get current connection status."""
        return self.status
    
    def is_connected(self) -> bool:
        """Check if connected to Discord RPC."""
        return self.status == RPCStatus.CONNECTED
