import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' can always be imported
backend_dir = Path(__file__).resolve().parent.parent
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
