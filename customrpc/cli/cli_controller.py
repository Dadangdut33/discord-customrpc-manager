"""
CLI controller for executing commands.

Handles CLI command execution via IPC or direct control.
"""

import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class CLIController:
    """Controls CLI command execution."""
    
    def __init__(self, config_manager, profile_manager, rpc_manager, ipc_client=None):
        """
        Initialize CLI controller.
        
        Args:
            config_manager: Configuration manager instance
            profile_manager: Profile manager instance
            rpc_manager: RPC manager instance
            ipc_client: Optional IPC client for sending commands to running instance
        """
        self.config = config_manager
        self.profiles = profile_manager
        self.rpc = rpc_manager
        self.ipc_client = ipc_client
        self.logger = logging.getLogger("customrpc.cli")
    
    def execute_list_profiles(self) -> int:
        """
        Execute list-profiles command.
        
        Returns:
            Exit code
        """
        profiles = self.profiles.list_profiles()
        
        if not profiles:
            print("No profiles found.")
            return 0
        
        print("Available profiles:")
        for i, profile in enumerate(profiles, 1):
            print(f"  {i}. {profile}")
        
        return 0
    
    def execute_load_profile(self, profile_name: str) -> int:
        """
        Execute load-profile command.
        
        Args:
            profile_name: Name of profile to load
            
        Returns:
            Exit code
        """
        profile = self.profiles.load_profile(profile_name)
        
        if not profile:
            print(f"Error: Profile '{profile_name}' not found.")
            return 1
        
        print(f"Loaded profile '{profile_name}'")
        self.config.set('last_profile', profile_name)
        return 0
    
    def execute_connect(self, profile_name: Optional[str] = None) -> int:
        """
        Execute connect command.
        
        Args:
            profile_name: Optional profile name to load before connecting
            
        Returns:
            Exit code
        """
        # Load profile if specified
        if profile_name:
            profile = self.profiles.load_profile(profile_name)
            if not profile:
                print(f"Error: Profile '{profile_name}' not found.")
                return 1
        else:
            # Try to load last used profile
            last_profile = self.config.get('last_profile')
            if not last_profile:
                print("Error: No profile specified and no last profile found.")
                return 1
            
            profile = self.profiles.load_profile(last_profile)
            if not profile:
                print(f"Error: Last profile '{last_profile}' not found.")
                return 1
        
        # Connect to RPC
        app_id = profile.get('app_id')
        if not app_id:
            print("Error: Profile missing Application ID.")
            return 1
        
        if self.rpc.connect(app_id):
            # Update activity with profile data
            activity = self._build_activity(profile)
            if self.rpc.update_activity(activity):
                print(f"Connected to Discord RPC with profile: {profile.get('name')}")
                return 0
            else:
                print("Error: Failed to update activity.")
                return 1
        else:
            print("Error: Failed to connect to Discord RPC.")
            return 1
    
    def execute_disconnect(self) -> int:
        """
        Execute disconnect command.
        
        Returns:
            Exit code
        """
        self.rpc.disconnect()
        print("Disconnected from Discord RPC.")
        return 0
    
    def send_to_running_instance(self, command: Dict[str, Any]) -> bool:
        """
        Send command to running instance via IPC.
        
        Args:
            command: Command dictionary
            
        Returns:
            True if sent successfully
        """
        if self.ipc_client:
            return self.ipc_client.send_command(command)
        return False
    
    def _build_activity(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build activity dict from profile.
        
        Args:
            profile: Profile data
            
        Returns:
            Activity dictionary for RPC
        """
        activity = {}

        # Text fields
        if profile.get('name'):
            activity['name'] = profile['name']
        if profile.get('details'):
            activity['details'] = profile['details']
        if profile.get('state'):
            activity['state'] = profile['state']
        
        # Timestamps
        if profile.get('start_timestamp'):
            activity['start'] = profile['start_timestamp']
        if profile.get('end_timestamp'):
            activity['end'] = profile['end_timestamp']
        
        # Images
        if profile.get('large_image_key'):
            activity['large_image'] = profile['large_image_key']
        if profile.get('large_image_text'):
            activity['large_text'] = profile['large_image_text']
        if profile.get('small_image_key'):
            activity['small_image'] = profile['small_image_key']
        if profile.get('small_image_text'):
            activity['small_text'] = profile['small_image_text']
        
        # Party
        if profile.get('party_size') or profile.get('party_max'):
            party_size = profile.get('party_size', 0)
            party_max = profile.get('party_max', 0)
            if party_size > 0 and party_max > 0:
                activity['party_size'] = [party_size, party_max]
        
        # Buttons
        buttons = profile.get('buttons', [])
        if buttons:
            activity['buttons'] = buttons
        
        # Instance
        if profile.get('instance') is not None:
            activity['instance'] = profile['instance']
        
        return activity
