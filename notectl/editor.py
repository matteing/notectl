import os

from pathlib import Path
from .config import get_config_value

def open_in_editor(path = Path | str ):
    editor_command = get_config_value("editor", "command", assert_value=True)
    os.system(f"{editor_command} '{path}'")
