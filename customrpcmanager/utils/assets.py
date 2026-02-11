import sys
from pathlib import Path
import logging

def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource.
    
    Args:
        relative_path: Path relative to resources directory (e.g. 'icons/icon.png')
        
    Returns:
        Path object pointing to resource
    """
    # Determine base path
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS).parent
    else:
        # Running from source
        # This file is in customrpcmanager/utils/assets.py
        # We want customrpcmanager/resources/
        base_path = Path(__file__).parent.parent / "resources"

    return base_path / relative_path

def get_icon_path() -> Path:
    """Get path to application icon."""
    return get_resource_path("icons/icon.png")
