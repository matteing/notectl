import os
import subprocess
from .config import get_config_value, get_vault_path

def take_git_snapshot():
    vault_path = get_vault_path()
    should_take_snapshot = get_config_value("git", "enable_git_snapshot", assert_value=False)
    if not should_take_snapshot:
        return

    # Get the absolute path of the take-snapshot.sh file in the current directory
    script_path = os.path.join(os.path.dirname(__file__), "scripts/take-git-snapshot.sh")

    # Make the file executable
    os.chmod(script_path, 0o755)

    # Run the file
    try:
        subprocess.run(f"'{script_path}'", shell=True, check=True, cwd=vault_path)
    except subprocess.CalledProcessError as e:
        print("Error: Could not take snapshot.")
        exit(1)