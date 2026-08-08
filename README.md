Smart Hospital Portal — Runbook

Overview
- This runbook contains the shared app entry points, module folders, and artifact copies needed to run the Smart Hospital Portal and integrated modules locally on Windows.
- It is intended as a shareable local evaluation package.

Runbook contents
- `runbook/portal/` — portal launcher file and copied portal script.
- `runbook/er_triage/` — ER Triage app, backend, and model artifacts.
- `runbook/wait_time/` — Wait Time app and model files.
- `runbook/adaptive/` — Adaptive Question Flow app, backend, and support assets.
- `runbook/cost_predictor/` — Cost Predictor frontend, backend, and model artifacts.
- `runbook/outbreak_prediction/` — Outbreak Prediction frontend, backend, and model artifacts.

What has been implemented
- Fixed `runbook/collect_artifacts.ps1` so the runbook folder can be populated cleanly.
- Confirmed that `runbook/` now contains the required module folders and key app files.
- Updated `Capstone/run_all.bat` as the final startup script for all module services and the portal.
- Synchronized the copied portal batch script at `runbook/portal/run_all.bat`.

Quick start
1. Create and activate a Python 3.11 virtual environment.

   PowerShell:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the shared dependencies:

   ```powershell
   python -m pip install -r runbook/requirements.txt
   ```

3. Launch the portal and modules:
   - From the repository: `Capstone\run_all.bat`
   - Or from the runbook copy: `runbook\portal\run_all.bat`

Module ports expected by the portal
- ER Triage: `http://localhost:9001`
- Wait Time: `http://localhost:9002`
- Adaptive: `http://localhost:9003`
- Cost Predictor: `http://localhost:9004`
- Outbreak Prediction: `http://localhost:9005`
- Portal: `http://localhost:9000`

Notes
- Each module folder contains its own `requirements.txt` if additional package installation is needed.
- The runbook folder now holds the main required files for each module and the final startup script.
