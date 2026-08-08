Portal (Smart Hospital Portal)

Path:
- Capstone/integrated_triage_app.py

Run (example):
- In a terminal inside `Capstone/` run:

```powershell
pip install -r ../runbook/requirements.txt
python -m streamlit run integrated_triage_app.py --server.port 9000
```

Notes:
- The portal embeds module apps using `components.iframe(module_url, height=950)`. It expects each module to be reachable at the URLs defined in the `MODULES` list (currently `http://localhost:9001`, etc.).
- Do not change the portal code unless you need to update URL routes.
