import subprocess
from datetime import datetime


def sync(message=None):
    """
    Stages all changes in data/, commits, and pushes to GitHub.
    Call this after any tool that writes to a file.
    """
    if message is None:
        message = f"sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    commands = [
        ["git", "add", "data/"],
        ["git", "commit", "-m", message],
        ["git", "push"]
    ]

    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)

        # commit returns code 1 if there's nothing new to commit, that's fine
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            print(f"git error on '{' '.join(cmd)}': {result.stderr.strip()}")
            return False

    return True