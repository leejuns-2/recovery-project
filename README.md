# Recovery Priority AX

침수위험과 회복지연위험은 다르다는 문제의식에서 출발해, 집중호우 이후 72시간 내 생활활동 회복지연 위험 행정동을 Top-K로 선별하고 제한된 복구자원을 어디에 먼저 배치할지 제안하는 AX 기반 복구운영 의사결정 모델입니다.

## Core Position

본 프로젝트는 침수 발생 여부나 회복 완료일을 정밀 예측하는 모델이 아닙니다. 서울 행정동 단위 생활인구, AWS 강수, 침수흔적, 하수도·복지·행정시설 데이터를 결합해 집중호우 이후 생활활동 회복지연 위험 상위 동을 선별하는 운영형 랭킹 모델입니다.

본 제출본이 다루는 것은 민원·점검·폐기물 같은 관측 행정수요의 직접 예측이 아니라, 그 수요가 커질 가능성이 있는 잠재 행정수요 후보군 선별입니다. 직접 행정수요 자료가 확보되면 검증 강도를 높일 수 있지만, 현재 제출 구조는 추가 자료 없이도 내부 Top-K 검증, 대표 사례 검증, 침수흔적 보조 비교로 완결되도록 구성했습니다.

## Competition Fit

2026 기후부 AX 아이디어 경진대회의 데이터 분석 부문 또는 정책 아이디어형 제출에 맞춥니다. 공모전이 요구하는 축은 공공·민간 데이터와 AI를 활용한 기후·환경·에너지 분야 정책현안 해결, 분석 결과, 시각화, 서비스화 가능성입니다.

## Key Results

이 문제는 절대 회복률 예측보다 제한된 복구자원을 어디에 먼저 투입할지 결정하는 랭킹 문제입니다. 따라서 성능 평가는 R2보다 Precision/Recall/Lift@K를 중심으로 제시합니다.

| Metric | Result | Interpretation |
|---|---:|---|
| Recall@Top20% | 82.2% | 전체 delayed 동 중 상위 20%가 포착한 비율 |
| Lift@Top20% | 4.07x | 전체 평균 대비 delayed 위험 농축도 |
| Precision@Top20% | 16.3% | 위험 상위 20% 중 실제 delayed 비율 |
| High vs Low recovery days | 1.83 vs 1.06 days | 위험군 간 실제 회복일수 차이 |
| Capacity Top20 lift | 5.55x | 제한자원 배치 시 위험기반 선별 효율 |
| LOEO R2 | 0.1148 | 새 호우 이벤트 절대값 예측은 제한적 |
| 2025 holdout R2 | 0.4781 | 특정 연도 holdout에서는 설명력 있음 |

## Submission Entry Points

- [submission/README.md](submission/README.md): 제출용 요약
- [submission/docs/01_competition_positioning.md](submission/docs/01_competition_positioning.md): 주제 경쟁력과 수상 가능성 분석
- [submission/docs/02_result_summary.md](submission/docs/02_result_summary.md): 객관적 결과 요약
- [submission/docs/03_limitations_and_defense.md](submission/docs/03_limitations_and_defense.md): 한계와 방어 논리
- [submission/docs/05_external_validation_plan.md](submission/docs/05_external_validation_plan.md): 외부 실적 검증 계획
- [submission/docs/06_case_story.md](submission/docs/06_case_story.md): 대표 호우 사례 스토리
- [app/streamlit_app.py](app/streamlit_app.py): 상황실형 데모 대시보드

## Validation Strategy

민원·폐기물·현장점검 원자료가 확보되면 `data/external/external_validation_template.csv` 형식으로 넣어 Top20/Bottom20 외부 실적 검증을 수행합니다. 현재 제출본에는 해당 원자료가 없으므로 외부 검증을 완료 주장하지 않고, 대표 호우 사례 기반 case validation으로 보완합니다.

대표 사례는 2023-07-13, 2024-07-18, 2025-09-04입니다. 세 이벤트 모두 Top20 Lift가 4배 이상으로 나타났고, 2025-09-04 이벤트에서는 Top20 선별이 실제 delayed 동의 97.3%를 포착했습니다.

검증은 3층으로 해석합니다. 1차 검증은 생활인구 회복지연 Top-K 선별 성능, 2차 검증은 침수흔적과 대표 사례를 활용한 보조 해석, 3차 검증은 향후 민원·점검·폐기물·피해신고 자료가 들어왔을 때 수행하는 직접 행정수요 검증입니다.

## Front Assets

전면 제출 산출물은 `submission/assets/`에 모았습니다.

1. `core_performance_summary.csv`
2. `top20_lift_report.png`
3. `event_priority_table.csv`
4. `playbook_table.csv`
5. `case_study_report.html`
6. `capacity_scenario_chart.png`

## Dashboard Demo

```powershell
python -m streamlit run app\streamlit_app.py --server.port=8503
```

## Rebuild

보고서 보강 산출물은 아래 명령으로 재생성합니다.

```powershell
python scripts/generate_operational_evidence.py
python scripts/external_validation.py
python scripts/build_case_story.py
```

## Required Cautions

- 생활인구 회복률은 복구 완료가 아니라 생활활동 정상화의 대리지표입니다.
- 현재 모델은 관측 행정수요를 직접 예측하지 않고, 잠재 행정수요가 클 수 있는 우선점검 후보를 선별합니다.
- 민원·폐기물·현장점검 자료 추가 수집은 필수 실행 조건이 아니라 제출 방어력을 높이는 선택 보강입니다.
- What-if와 운영 효율 시나리오는 인과효과 추정이나 확정 예산절감액이 아니라 배치전략별 상대 효율 민감도 분석입니다.
- `duration_days`는 이벤트 종료 후 확정되는 변수이므로 D+1~D+3 운영 갱신 단계에서만 사용합니다.
- 침수흔적 overlap 결과는 모델이 과거 침수면적 자체보다 사후 운영 취약성을 포착한다는 보조 해석으로 사용합니다.
