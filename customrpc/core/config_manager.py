"""
Configuration manager for CustomRPCManager.

Handles application settings and OS-specific paths.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import logging


class ConfigManager:
    """Manages application configuration and settings."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.logger = logging.getLogger("customrpcmanager.config")
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.profiles_dir = self.config_dir / "profiles"
        self.logs_dir = self.config_dir / "logs"
        
        # Create directories
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create config
        self.config = self._load_config()
    
    def _get_config_dir(self) -> Path:
        """
        Get OS-specific configuration directory.
        
        Returns:
            Path to config directory
        """
        if sys.platform == "win32":
            # Windows: %APPDATA%/CustomRPCManager
            base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
            return base / "CustomRPCManager"
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/CustomRPCManager
            return Path.home() / "Library" / "Application Support" / "CustomRPCManager"
        else:
            # Linux: ~/.config/CustomRPCManager
            config_home = os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')
            return Path(config_home) / "CustomRPCManager"
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.
        
        Returns:
            Configuration dictionary
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"Loaded config from {self.config_file}")
                return config
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}, using defaults")
                return self._default_config()
        else:
            config = self._default_config()
            self._save_config(config)
            return config
    
    def _default_config(self) -> Dict[str, Any]:
        """
        Get default configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "theme": "dark",
            "run_on_startup": False,
            "auto_connect": False,
            "auto_connect_profile": None,
            "last_profile": None,
            "minimize_to_tray": True,
            "start_minimized": False,
            "log_level": "INFO",
            "notify_on_status_change": True,
        }
    
    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save (uses self.config if None)
        """
        config = config or self.config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            self.logger.info(f"Saved config to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value and save.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        self._save_config()
        self.logger.info(f"Set config {key} = {value}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.config.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = self._default_config()
        self._save_config()
        self.logger.info("Reset config to defaults")


# Import os for environment variables
import os
