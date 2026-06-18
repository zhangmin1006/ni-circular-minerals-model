# Online Dashboard Deployment

The repository is prepared for Streamlit Community Cloud.

## Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to <https://share.streamlit.io/>.
3. Choose the repository and branch.
4. Set the main file path to:

```text
streamlit_app.py
```

5. **In "Advanced settings", set the Python version to 3.12** (matches CI;
   3.11–3.13 are fine). Then deploy.

The app uses the root `requirements.txt` and `.streamlit/config.toml`. It reads
the committed model outputs from `model/outputs/` (all tracked in git, so the
deployed app has data immediately); if those outputs are ever missing, the app
offers a button to regenerate them by running `model/run_mvm.py` (and the per-
question experiments).

> **Why the build is split (this fixes the "won't boot" build error).** Streamlit
> Community Cloud installs the **root `requirements.txt`**, which is deliberately
> slim — only `streamlit`, `pandas`, `matplotlib` (+ transitive numpy). The online
> app *only reads the committed outputs and renders them*; it never imports
> `mesa` / `scipy` / `networkx`, so installing them on cloud just risked the
> C-extension build failures (scipy/mesa toolchain) that break the deploy. The
> **full model + experiment + export stack lives in `model/requirements.txt`**,
> used by CI and local runs (`pip install -r model/requirements.txt`). Both are
> pinned with upper bounds so a fresh install resolves to the tested-good majors
> (Streamlit ≥ 1.49 for the `width="stretch"` API; pandas < 3.1; numpy < 3) and a
> future breaking release cannot silently break the deploy.

### Tabs (13)
Overview · Q2.1 Interventions · Q2.2 Opportunities · Q2.3 Business Support ·
Q2.4 Secure Supply · Q2.5 Jobs & Skills · Q2.6 Economic Benefits ·
Q2.7 Negative Impacts · Demand & Supply · Supply Security · Companies ·
Regional Jobs · Data Quality.

### Troubleshooting a broken online app
- **"Error installing requirements" / app won't boot:** the cloud build was
  trying to install/compile the heavy model stack (scipy/mesa). The slim root
  `requirements.txt` (streamlit + pandas + matplotlib only) prevents this. Make
  sure the deploy is on the latest `master`, then **Reboot** from "Manage app"
  (and check "Manage app → logs" for the failing package if it persists).
- **A tab shows a Python error:** usually means the committed outputs are stale vs
  the code. Re-run `python model/run_mvm.py` + the `q2_*` scripts locally, commit
  the regenerated `model/outputs/`, and push (the cloud auto-redeploys).
- **App is blank / spinning:** check the "Manage app" logs; a `MemoryError`
  means a `Run … now` button was clicked (the on-cloud model run can exceed the
  free-tier RAM). With outputs committed, those buttons should never appear.
- **Smoke-test locally exactly as cloud runs it:**
  `python -m streamlit run streamlit_app.py --server.headless true`.

### One-click deploy link
Repo: <https://github.com/zhangmin1006/ni-circular-minerals-model> (private).
Deploy this app (sign in to Streamlit with the same GitHub account):
<https://share.streamlit.io/deploy?repository=zhangmin1006/ni-circular-minerals-model&branch=master&mainModule=streamlit_app.py>

## Local Run

```bash
python -m streamlit run streamlit_app.py
```

## Data Caveat

The app is a policy-scenario dashboard, not a forecast. Company scores,
behavioural parameters, I-O coefficients, and CGE calibration values remain
proxy/desk-researched until replaced with audited datasets and survey evidence.
