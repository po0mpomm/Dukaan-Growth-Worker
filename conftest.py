import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' can always be imported
root_backend = Path(__file__).resolve().parent / "backend"
if root_backend.exists() and str(root_backend) not in sys.path:
    sys.path.insert(0, str(root_backend))
