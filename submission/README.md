# Analysis Artifacts

이 폴더에는 Recovery Priority AX의 커밋된 결과와 기술 문서를 모았습니다.

## Results

| File | Contents |
|---|---|
| `assets/core_performance_summary.csv` | 주요 성능 지표 |
| `assets/ranking_metrics.csv` | Top-K 랭킹 평가 |
| `assets/event_priority_table.csv` | 이벤트별 우선순위와 대응 정보 |
| `assets/playbook_table.csv` | 회복지연 유형별 대응 항목 |
| `assets/capacity_scenario_results.csv` | 자원 수별 민감도 분석 |
| `assets/case_story_event_metrics.csv` | 대표 호우 이벤트 지표 |
| `assets/case_study_report.html` | 대표 이벤트 HTML 요약 |

일부 PNG가 문서에서 언급되지만 Git에 포함되지 않은 경우가 있습니다. 표의 원자료는 커밋된 CSV에서 확인할 수 있습니다.

## Documentation

- [`docs/02_result_summary.md`](docs/02_result_summary.md): 결과와 해석
- [`docs/03_limitations.md`](docs/03_limitations.md): 기술적 한계
- [`docs/05_external_validation_plan.md`](docs/05_external_validation_plan.md): 직접 행정수요 자료가 확보될 때의 검증 방법
- [`docs/06_case_study.md`](docs/06_case_study.md): 세 호우 이벤트 사례
- [`docs/07_external_data_sources.md`](docs/07_external_data_sources.md): 외부 데이터 후보

민원·폐기물·현장점검 원자료는 저장소에 없습니다. 외부 행정수요 검증은 완료된 결과가 아니라 향후 검증 항목입니다.

## Demo

```powershell
pip install -r requirements-submission.txt
python -m streamlit run app\streamlit_app.py --server.port=8503
```

데모는 `assets/`의 저장된 결과를 읽습니다. 모델을 새로 학습하거나 실시간 위험을 예측하지 않습니다.
