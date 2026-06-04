import os
import sys

def get_base_dir():
    """
    Returns the root directory of the application.
    If compiled with PyInstaller, this is the temporary folder sys._MEIPASS.
    If running as a script, this is the directory containing main.py.
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        # This file is in utils/paths.py, so parent is utils, and parent's parent is root
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_data_dir():
    """
    Returns the folder where persistent data (settings, logs) should be stored.
    This should be a directory in the user's filesystem, not the temp directory.
    When frozen, this is the directory of the executable.
    When running as a script, this is the root directory of the project.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_asset_path(relative_path):
    """Returns the absolute path to an asset file in the base directory."""
    return os.path.join(get_base_dir(), relative_path)

def get_data_path(relative_path):
    """Returns the absolute path to a data file (settings, logs) in the data directory."""
    return os.path.join(get_data_dir(), relative_path)
