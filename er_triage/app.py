from pathlib import Path
import importlib.util
import sys

root = Path(__file__).resolve().parent
app_path = root / "triage_v3" / "app.py"

spec = importlib.util.spec_from_file_location("triage_v3_app", app_path)
module = importlib.util.module_from_spec(spec)
sys.modules["triage_v3_app"] = module
spec.loader.exec_module(module)
