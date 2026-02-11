"""
CLI argument parser for CustomRPC.

Handles command-line interface arguments and options.
"""

import argparse
from typing import Tuple


class CLIParser:
    """Parses command-line arguments."""
    
    def __init__(self):
        """Initialize CLI parser."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create argument parser.
        
        Returns:
            Configured ArgumentParser
        """
        parser = argparse.ArgumentParser(
            prog='customrpc',
            description='CustomRPC Manager - Discord Rich Presence Manager',
            epilog='Examples:\n'
                   '  customrpc --list-profiles'
                   '  customrpc --profile "Gaming" --connect\n'
                   '  customrpc --disconnect\n',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument(
            '--profile',
            type=str,
            metavar='NAME',
            help='Load and use specified profile'
        )
        
        parser.add_argument(
            '--connect',
            action='store_true',
            help='Connect to Discord RPC'
        )
        
        parser.add_argument(
            '--disconnect',
            action='store_true',
            help='Disconnect from Discord RPC'
        )
        
        parser.add_argument(
            '--quit',
            action='store_true',
            help='Quit the running application'
        )
        
        parser.add_argument(
            '--list-profiles',
            action='store_true',
            help='List all available profiles'
        )
        
        parser.add_argument(
            '--minimized',
            action='store_true',
            help='Start minimized to system tray'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug logging'
        )
        
        return parser
    
    def parse(self) -> Tuple[argparse.Namespace, bool]:
        """
        Parse command-line arguments.
        
        Returns:
            Tuple of (parsed args, is_headless_mode)
        """
        args = self.parser.parse_args()
        
        # Determine if in headless mode (CLI commands without GUI)
        headless = any([
            args.profile and args.connect,
            args.disconnect,
            args.quit,
            args.list_profiles
        ])
        
        return args, headless
