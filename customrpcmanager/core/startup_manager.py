"""
Startup manager for OS-specific autostart functionality.

Handles run-on-startup configuration for Linux, Windows, and macOS.
"""

import sys
import os
from pathlib import Path
from typing import Optional
import logging


class StartupManager:
    """Manages application autostart across different operating systems."""
    
    def __init__(self, app_name: str = "CustomRPCManager", app_path: Optional[Path] = None):
        """
        Initialize startup manager.
        
        Args:
            app_name: Application name
            app_path: Path to application executable
        """
        self.app_name = app_name
        self.app_path = app_path or Path(sys.argv[0]).resolve()
        self.logger = logging.getLogger("customrpcmanager.startup")
    
    def is_enabled(self) -> bool:
        """
        Check if autostart is enabled.
        
        Returns:
            True if autostart is enabled
        """
        if sys.platform == "win32":
            return self._is_enabled_windows()
        elif sys.platform == "darwin":
            return self._is_enabled_macos()
        else:
            return self._is_enabled_linux()
    
    def enable(self) -> bool:
        """
        Enable autostart.
        
        Returns:
            True if successful
        """
        if sys.platform == "win32":
            return self._enable_windows()
        elif sys.platform == "darwin":
            return self._enable_macos()
        else:
            return self._enable_linux()
    
    def disable(self) -> bool:
        """
        Disable autostart.
        
        Returns:
            True if successful
        """
        if sys.platform == "win32":
            return self._disable_windows()
        elif sys.platform == "darwin":
            return self._disable_macos()
        else:
            return self._disable_linux()
    
    # Linux implementation
    def _get_desktop_file_path(self) -> Path:
        """Get path to .desktop file."""
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        return autostart_dir / f"{self.app_name.lower()}.desktop"
    
    def _is_enabled_linux(self) -> bool:
        """Check if autostart is enabled on Linux."""
        return self._get_desktop_file_path().exists()
    
    def _enable_linux(self) -> bool:
        """Enable autostart on Linux using .desktop file."""
        try:
            desktop_file = self._get_desktop_file_path()
            
            # Create .desktop file content
            content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Discord Rich Presence Manager
Exec=python3 {self.app_path}
Icon=discord
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""
            
            desktop_file.write_text(content)
            desktop_file.chmod(0o755)
            
            self.logger.info(f"Enabled autostart on Linux: {desktop_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable autostart on Linux: {e}")
            return False
    
    def _disable_linux(self) -> bool:
        """Disable autostart on Linux."""
        try:
            desktop_file = self._get_desktop_file_path()
            if desktop_file.exists():
                desktop_file.unlink()
                self.logger.info("Disabled autostart on Linux")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable autostart on Linux: {e}")
            return False
    
    # Windows implementation
    def _get_startup_registry_key(self) -> str:
        """Get Windows registry key path for startup."""
        return r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    def _is_enabled_windows(self) -> bool:
        """Check if autostart is enabled on Windows."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self._get_startup_registry_key(),
                0,
                winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception as e:
            self.logger.error(f"Error checking Windows autostart: {e}")
            return False
    
    def _enable_windows(self) -> bool:
        """Enable autostart on Windows using registry."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self._get_startup_registry_key(),
                0,
                winreg.KEY_SET_VALUE
            )
            
            # Set registry value
            winreg.SetValueEx(
                key,
                self.app_name,
                0,
                winreg.REG_SZ,
                f'pythonw "{self.app_path}"'
            )
            winreg.CloseKey(key)
            
            self.logger.info("Enabled autostart on Windows")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable autostart on Windows: {e}")
            return False
    
    def _disable_windows(self) -> bool:
        """Disable autostart on Windows."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self._get_startup_registry_key(),
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, self.app_name)
                self.logger.info("Disabled autostart on Windows")
            except FileNotFoundError:
                pass  # Already disabled
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disable autostart on Windows: {e}")
            return False
    
    # macOS implementation
    def _get_launchagent_path(self) -> Path:
        """Get path to LaunchAgent plist file."""
        agents_dir = Path.home() / "Library" / "LaunchAgents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        return agents_dir / f"com.{self.app_name.lower()}.plist"
    
    def _is_enabled_macos(self) -> bool:
        """Check if autostart is enabled on macOS."""
        return self._get_launchagent_path().exists()
    
    def _enable_macos(self) -> bool:
        """Enable autostart on macOS using LaunchAgent."""
        try:
            plist_file = self._get_launchagent_path()
            
            # Create plist content
            content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{self.app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""
            plist_file.write_text(content)
            self.logger.info(f"Enabled autostart on macOS: {plist_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable autostart on macOS: {e}")
            return False
    
    def _disable_macos(self) -> bool:
        """Disable autostart on macOS."""
        try:
            plist_file = self._get_launchagent_path()
            if plist_file.exists():
                plist_file.unlink()
                self.logger.info("Disabled autostart on macOS")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disable autostart on macOS: {e}")
            return False
