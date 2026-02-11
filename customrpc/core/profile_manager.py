"""
Profile manager for CustomRPCManager.

Handles CRUD operations for RPC profiles.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging


class ProfileManager:
    """Manages RPC profiles."""
    
    def __init__(self, profiles_dir: Path):
        """
        Initialize profile manager.
        
        Args:
            profiles_dir: Directory for storing profiles
        """
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("customrpcmanager.profiles")
    
    def _get_profile_path(self, profile_name: str) -> Path:
        """Get file path for profile."""
        # Sanitize profile name for filesystem
        safe_name = "".join(c for c in profile_name if c.isalnum() or c in (' ', '-', '_')).strip()
        return self.profiles_dir / f"{safe_name}.json"
    
    def create_profile(self, profile_name: str, profile_data: Dict[str, Any]) -> bool:
        """
        Create a new profile.
        
        Args:
            profile_name: Name of the profile
            profile_data: Profile data dictionary
            
        Returns:
            True if created successfully
        """
        profile_path = self._get_profile_path(profile_name)
        
        if profile_path.exists():
            self.logger.error(f"Profile '{profile_name}' already exists")
            return False
        
        try:
            # Add metadata
            profile_data['name'] = profile_name
            profile_data['created_at'] = datetime.now().isoformat()
            profile_data['updated_at'] = datetime.now().isoformat()
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            
            self.logger.info(f"Created profile '{profile_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create profile '{profile_name}': {e}")
            return False
    
    def load_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a profile.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Profile data or None if not found
        """
        profile_path = self._get_profile_path(profile_name)
        
        if not profile_path.exists():
            self.logger.error(f"Profile '{profile_name}' not found")
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            self.logger.info(f"Loaded profile '{profile_name}'")
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Failed to load profile '{profile_name}': {e}")
            return None
    
    def update_profile(self, profile_name: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update an existing profile.
        
        Args:
            profile_name: Name of the profile
            profile_data: Updated profile data
            
        Returns:
            True if updated successfully
        """
        profile_path = self._get_profile_path(profile_name)
        
        if not profile_path.exists():
            self.logger.error(f"Profile '{profile_name}' not found")
            return False
        
        try:
            # Preserve creation time, update modification time
            existing = self.load_profile(profile_name)
            profile_data['name'] = profile_name
            profile_data['created_at'] = existing.get('created_at', datetime.now().isoformat())
            profile_data['updated_at'] = datetime.now().isoformat()
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            
            self.logger.info(f"Updated profile '{profile_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update profile '{profile_name}': {e}")
            return False
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            True if deleted successfully
        """
        profile_path = self._get_profile_path(profile_name)
        
        if not profile_path.exists():
            self.logger.error(f"Profile '{profile_name}' not found")
            return False
        
        try:
            profile_path.unlink()
            self.logger.info(f"Deleted profile '{profile_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete profile '{profile_name}': {e}")
            return False
    
    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """
        Rename a profile.
        
        Args:
            old_name: Current profile name
            new_name: New profile name
            
        Returns:
            True if renamed successfully
        """
        old_path = self._get_profile_path(old_name)
        new_path = self._get_profile_path(new_name)
        
        if not old_path.exists():
            self.logger.error(f"Profile '{old_name}' not found")
            return False
        
        if new_path.exists():
            self.logger.error(f"Profile '{new_name}' already exists")
            return False
        
        try:
            # Load, update name, and save to new location
            profile_data = self.load_profile(old_name)
            if profile_data:
                profile_data['name'] = new_name
                
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=2)
                
                old_path.unlink()
                self.logger.info(f"Renamed profile '{old_name}' to '{new_name}'")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to rename profile: {e}")
            return False
    
    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """
        Duplicate a profile.
        
        Args:
            source_name: Name of profile to duplicate
            new_name: Name for the duplicate
            
        Returns:
            True if duplicated successfully
        """
        source_data = self.load_profile(source_name)
        if not source_data:
            return False
        
        # Create new profile with same data
        return self.create_profile(new_name, source_data)
    
    def list_profiles(self) -> List[str]:
        """
        List all profile names.
        
        Returns:
            List of profile names
        """
        try:
            profiles = []
            for path in self.profiles_dir.glob("*.json"):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        profiles.append(data.get('name', path.stem))
                except Exception as e:
                    self.logger.error(f"Failed to read profile {path.name}: {e}")
            
            return sorted(profiles)
            
        except Exception as e:
            self.logger.error(f"Failed to list profiles: {e}")
            return []
    
    def export_profile(self, profile_name: str, export_path: Path) -> bool:
        """
        Export profile to file.
        
        Args:
            profile_name: Name of profile to export
            export_path: Path to export to
            
        Returns:
            True if exported successfully
        """
        profile_data = self.load_profile(profile_name)
        if not profile_data:
            return False
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2)
            
            self.logger.info(f"Exported profile '{profile_name}' to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export profile: {e}")
            return False
    
    def import_profile(self, import_path: Path, profile_name: Optional[str] = None) -> bool:
        """
        Import profile from file.
        
        Args:
            import_path: Path to import from
            profile_name: Optional name for imported profile
            
        Returns:
            True if imported successfully
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            # Use provided name or name from file
            name = profile_name or profile_data.get('name', import_path.stem)
            
            # Check if profile already exists
            if self._get_profile_path(name).exists():
                self.logger.error(f"Profile '{name}' already exists")
                return False
            
            return self.create_profile(name, profile_data)
            
        except Exception as e:
            self.logger.error(f"Failed to import profile: {e}")
            return False
