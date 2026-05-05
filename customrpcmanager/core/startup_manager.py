"""
Startup manager for OS-specific autostart functionality.

Handles run-on-startup configuration for Linux, Windows, and macOS.
"""

import sys
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import logging

from customrpcmanager.utils.assets import get_icon_path


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
        self.python_path = Path(sys.executable).resolve()
        self.logger = logging.getLogger("customrpcmanager.startup")

    def get_launch_command(self, minimized: bool = False, gui: bool = False) -> list[str]:
        """
        Build the command used to launch the app in the current environment.

        Args:
            minimized: Whether to add the minimized flag
            gui: Whether to prefer GUI-friendly launchers when possible

        Returns:
            Launch command as a list of arguments
        """
        if getattr(sys, "frozen", False):
            command = [str(self.python_path)]
        elif self.app_path.suffix.lower() == ".py":
            python_path = self._get_windows_gui_python() if gui else self.python_path
            command = [str(python_path), str(self.app_path)]
        else:
            command = [str(self.app_path)]

        if minimized:
            command.append("--minimized")

        return command

    def get_launcher_path(self) -> Path:
        """Get the OS-specific launcher/shortcut path."""
        if sys.platform == "win32":
            programs_dir = Path(
                os.environ.get(
                    "APPDATA",
                    Path.home() / "AppData" / "Roaming"
                )
            ) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            programs_dir.mkdir(parents=True, exist_ok=True)
            return programs_dir / f"{self.app_name}.lnk"
        if sys.platform == "darwin":
            applications_dir = Path.home() / "Applications"
            applications_dir.mkdir(parents=True, exist_ok=True)

            bundle_path = self._get_macos_app_bundle_path()
            if bundle_path is not None:
                return applications_dir / bundle_path.name

            return applications_dir / f"{self.app_name}.command"

        applications_dir = Path.home() / ".local" / "share" / "applications"
        applications_dir.mkdir(parents=True, exist_ok=True)
        return applications_dir / f"{self.app_name.lower()}.desktop"

    def launcher_exists(self) -> bool:
        """Check whether a launcher/shortcut currently exists."""
        return self.get_launcher_path().exists()

    def create_launcher(self) -> bool:
        """Create or update the OS-specific launcher/shortcut entry."""
        if sys.platform == "win32":
            return self._create_launcher_windows()
        if sys.platform == "darwin":
            return self._create_launcher_macos()
        return self._create_launcher_linux()

    def remove_launcher(self) -> bool:
        """Remove the OS-specific launcher/shortcut entry."""
        try:
            launcher_path = self.get_launcher_path()
            if launcher_path.is_symlink() or launcher_path.is_file():
                launcher_path.unlink()
                self.logger.info(f"Removed launcher entry: {launcher_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove launcher entry: {e}")
            return False
    
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

    def _build_linux_desktop_entry(self, launch_command: list[str], autostart: bool) -> str:
        """Build the contents of a Linux .desktop entry."""
        icon_path = get_icon_path()
        icon_line = f"Icon={icon_path}\n" if icon_path.exists() else ""
        autostart_line = "X-GNOME-Autostart-enabled=true\n" if autostart else ""

        return (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={self.app_name}\n"
            "Comment=Discord Rich Presence Manager\n"
            f"Exec={shlex.join(launch_command)}\n"
            f"{icon_line}"
            "Terminal=false\n"
            "Categories=Utility;\n"
            f"{autostart_line}"
        )
    
    def _is_enabled_linux(self) -> bool:
        """Check if autostart is enabled on Linux."""
        return self._get_desktop_file_path().exists()
    
    def _enable_linux(self) -> bool:
        """Enable autostart on Linux using .desktop file."""
        try:
            desktop_file = self._get_desktop_file_path()

            content = self._build_linux_desktop_entry(
                self.get_launch_command(gui=True),
                autostart=True
            )
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

            winreg.SetValueEx(
                key,
                self.app_name,
                0,
                winreg.REG_SZ,
                subprocess.list2cmdline(self.get_launch_command(gui=True))
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
            program_arguments = "\n".join(
                f"        <string>{self._xml_escape(arg)}</string>"
                for arg in self.get_launch_command(gui=True)
            )

            content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
{program_arguments}
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

    def _create_launcher_linux(self) -> bool:
        """Create a launcher entry in the Linux applications directory."""
        try:
            launcher_path = self.get_launcher_path()
            launcher_path.write_text(
                self._build_linux_desktop_entry(
                    self.get_launch_command(gui=True),
                    autostart=False
                )
            )
            launcher_path.chmod(0o755)
            self.logger.info(f"Created launcher entry: {launcher_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create Linux launcher entry: {e}")
            return False

    def _create_launcher_windows(self) -> bool:
        """Create a Start Menu shortcut on Windows."""
        try:
            launcher_path = self.get_launcher_path()
            launch_command = self.get_launch_command(gui=True)
            target_path = launch_command[0]
            arguments = subprocess.list2cmdline(launch_command[1:]) if len(launch_command) > 1 else ""
            working_directory = str(self.app_path.parent)

            icon_location = ""
            if Path(target_path).suffix.lower() == ".exe":
                icon_location = target_path

            powershell = shutil.which("powershell") or shutil.which("pwsh")
            if not powershell:
                raise RuntimeError("PowerShell was not found on this system.")

            script_lines = [
                "$WshShell = New-Object -ComObject WScript.Shell",
                f"$Shortcut = $WshShell.CreateShortcut('{self._powershell_escape(str(launcher_path))}')",
                f"$Shortcut.TargetPath = '{self._powershell_escape(target_path)}'",
                f"$Shortcut.Arguments = '{self._powershell_escape(arguments)}'",
                f"$Shortcut.WorkingDirectory = '{self._powershell_escape(working_directory)}'",
                f"$Shortcut.Description = '{self._powershell_escape('Discord Rich Presence Manager')}'",
            ]
            if icon_location:
                script_lines.append(
                    f"$Shortcut.IconLocation = '{self._powershell_escape(icon_location)}'"
                )
            script_lines.extend(["$Shortcut.Save()", ""])

            subprocess.run(
                [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "\n".join(script_lines)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.logger.info(f"Created launcher entry: {launcher_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create Windows launcher entry: {e}")
            return False

    def _create_launcher_macos(self) -> bool:
        """Create a launcher entry in ~/Applications on macOS."""
        try:
            launcher_path = self.get_launcher_path()
            bundle_path = self._get_macos_app_bundle_path()

            if launcher_path.exists() or launcher_path.is_symlink():
                if launcher_path.is_symlink() or launcher_path.is_file():
                    launcher_path.unlink()
                else:
                    raise RuntimeError(
                        f"Launcher path already exists and is not safely replaceable: {launcher_path}"
                    )

            if bundle_path is not None:
                launcher_path.symlink_to(bundle_path, target_is_directory=True)
            else:
                script = (
                    "#!/bin/bash\n"
                    f"exec {shlex.join(self.get_launch_command(gui=True))} \"$@\"\n"
                )
                launcher_path.write_text(script)
                launcher_path.chmod(0o755)

            self.logger.info(f"Created launcher entry: {launcher_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create macOS launcher entry: {e}")
            return False

    def _get_macos_app_bundle_path(self) -> Optional[Path]:
        """Return the enclosing .app bundle when running from a macOS app."""
        for path in [self.python_path, self.app_path]:
            if path.suffix == ".app":
                return path

            for parent in path.parents:
                if parent.suffix == ".app":
                    return parent

        return None

    def _get_windows_gui_python(self) -> Path:
        """Prefer pythonw.exe for Windows GUI launch contexts."""
        if sys.platform != "win32":
            return self.python_path

        if self.python_path.name.lower() == "python.exe":
            pythonw_path = self.python_path.with_name("pythonw.exe")
            if pythonw_path.exists():
                return pythonw_path

        return self.python_path

    @staticmethod
    def _xml_escape(value: str) -> str:
        """Escape a string for XML/plist output."""
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    @staticmethod
    def _powershell_escape(value: str) -> str:
        """Escape a string for a single-quoted PowerShell string literal."""
        return value.replace("'", "''")
