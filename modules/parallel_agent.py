import threading
import sys
from pathlib import Path

# Import the agent's main function dynamically since the directory uses a hyphen
AGENT_DIR = Path(__file__).resolve().parent.parent / "parallel-task-agent" / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.append(str(AGENT_DIR))

from main import main

_agent_thread = None


def start_agent() -> bool:
    """Start the parallel task agent in a background thread."""
    global _agent_thread
    if _agent_thread and _agent_thread.is_alive():
        return False
    _agent_thread = threading.Thread(target=main, daemon=True)
    _agent_thread.start()
    return True

