# Repository Map

## Submission Package

```text
submission/
  README.md
  assets/
    core_performance_summary.csv
    top20_lift_report.png
    event_priority_table.csv
    playbook_table.csv
    case_study_report.html
    capacity_scenario_chart.png
    capacity_scenario_results.csv
    ranking_metrics.csv
    target_sensitivity_summary.csv
    model_timing_comparison.csv
    flood_trace_overlap_interpretation.csv
    flood_trace_overlap_report.png
    external_validation_summary.csv
    case_story_event_metrics.csv
    case_story_top10.csv
  docs/
    01_competition_positioning.md
    02_result_summary.md
    03_limitations_and_defense.md
    04_repository_map.md
    05_external_validation_plan.md
    06_case_story.md
```

## Analysis Pipeline

```text
notebooks/
  01_data_collection.ipynb
  02_event_detection.ipynb
  03_auxiliary_data.ipynb
  04_feature_spatial.ipynb
  05_event_windows_baseline.ipynb
  06_label_generation.ipynb
  07_model.ipynb
  08_validation_package.ipynb
  09_decision_package.ipynb
  10_whatif_case_study.ipynb
  11_weather_event_v2.ipynb
  12_local_rain_model.ipynb
  13_panel_regression_checks.ipynb
  14_report_outputs.ipynb
  15_final_outputs.ipynb
  16_ranking_metrics.ipynb
  17_feature_availability.ipynb
  18_d0_model_comparison.ipynb
  19_capacity_whatif.ipynb
  20_flood_trace_validation.ipynb
```

## Reproducible Report Step

```powershell
python scripts/generate_operational_evidence.py
```

This script rebuilds the ranking sensitivity, target sensitivity, capacity scenario, priority table enrichment, and flood-trace interpretation outputs.

## Dashboard Demo

```text
app/
  streamlit_app.py
requirements-submission.txt
```

```powershell
python -m streamlit run app\streamlit_app.py --server.port=8503
```

The dashboard presents a situation-room workflow: event selection, resource capacity selection, Top-K priority table, rule-based AI briefing, department action checklist, ranking evidence, and usage cautions.
