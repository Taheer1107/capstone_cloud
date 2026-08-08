from pathlib import Path
import importlib.util
import sys

root = Path(__file__).resolve().parent
backend_path = root / "triage_v3" / "backend.py"

spec = importlib.util.spec_from_file_location("triage_v3_backend", backend_path)
module = importlib.util.module_from_spec(spec)
sys.modules["triage_v3_backend"] = module
spec.loader.exec_module(module)

app = module.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
