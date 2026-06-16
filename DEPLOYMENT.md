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

5. Deploy.

The app uses the root `requirements.txt` and `.streamlit/config.toml`. It reads
the committed model outputs from `model/outputs/`; if those outputs are missing,
the app can regenerate them by running `model/run_mvm.py` (and the Q2.1 experiment
via `model/q2_1_circularity_interventions.py`).

### Tabs
Overview · **Q2.1 Interventions** (circular-innovation policy mix + ROI band) ·
Supply Security · Companies · Regional Jobs · Data Quality.

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
