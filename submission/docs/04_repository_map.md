# Repository Map

```text
app/
  streamlit_app.py          # committed result viewer
data/external/
  README.md
  external_validation_template.csv
scripts/
  external_validation.py   # optional external-demand validation
  generate_operational_evidence.py
  build_case_story.py
submission/
  assets/                   # committed result tables and HTML
  docs/
    02_result_summary.md
    03_limitations.md
    04_repository_map.md
    05_external_validation_plan.md
    06_case_study.md
    07_external_data_sources.md
```

## Publicly Runnable Component

The Streamlit app reads committed files from `submission/assets/`:

```powershell
pip install -r requirements-submission.txt
python -m streamlit run app\streamlit_app.py --server.port=8503
```

## Analysis Scripts

`scripts/generate_operational_evidence.py` and `scripts/build_case_story.py` require ignored processed data and model outputs. They document the original analysis workflow but do not form a complete fresh-clone rebuild path. See the main README for the required file categories and reproducibility boundary.
