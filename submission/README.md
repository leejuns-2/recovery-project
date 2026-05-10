# Submission Package

## Title

침수위험과 회복지연위험은 다르다: 집중호우 이후 서울 행정동 생활서비스 회복지연 Top-K 선별 모델

## One-Line Pitch

집중호우 이후 어느 행정동에 제한된 복구자원을 먼저 투입해야 하는지, 생활인구 회복 신호와 공공 인프라 데이터를 결합해 Top-K 우선순위로 제안하는 AX 기반 복구운영 의사결정 모델입니다.

## Recommended Track

데이터 분석 부문 - 자유 분석

활용 부문으로 제출할 수도 있지만, 현재 강점은 제품성보다 데이터 결합, 모델 검증, 정책 의사결정 산출물에 있습니다. 따라서 분석 부문이 가장 안전합니다.

## Performance First Message

본 과제는 회복률 절대값을 맞히는 회귀 문제가 아니라 제한된 복구자원을 어디에 먼저 배치할지 결정하는 랭킹 문제입니다. 따라서 성능표는 R2보다 Recall/Lift/Precision@K를 먼저 제시합니다.

| Metric | Value | Meaning |
|---|---:|---|
| Recall@Top20% | 82.2% | 전체 delayed 동 중 상위 20%가 포착한 비율 |
| Lift@Top20% | 4.07x | 전체 평균 delayed rate 대비 위험 농축도 |
| Precision@Top20% | 16.3% | 위험 상위 20% 중 실제 delayed 비율 |
| Capacity Top20 lift | 5.55x | 제한자원 배치 시 risk-based 선별 효율 |
| LOEO R2 | 0.1148 | 절대값 예측 일반화 한계 |

## Main Deliverables

| Order | Asset | Role |
|---:|---|---|
| 1 | `assets/core_performance_summary.csv` | 핵심 성능 수치 |
| 2 | `assets/top20_lift_report.png` | 랭킹 모델 성능 |
| 3 | `assets/event_priority_table.csv` | 이벤트별 운영 우선순위 |
| 4 | `assets/playbook_table.csv` | 유형별 권장 조치 |
| 5 | `assets/case_study_report.html` | 실제 호우 사례 |
| 6 | `assets/capacity_scenario_chart.png` | 제한자원 배치 시뮬레이션 |

## Validation Extensions

| Asset | Role |
|---|---|
| `docs/05_external_validation_plan.md` | 민원·폐기물·현장점검 데이터 확보 시 적용할 외부 검증 설계 |
| `docs/07_external_data_sources.md` | 외부 검증 후보 데이터 출처와 결합 전략 |
| `assets/external_data_source_candidates.csv` | 외부 검증 후보 데이터 목록 |
| `assets/external_validation_summary.csv` | 현재 외부 실적 데이터 투입 상태 |
| `docs/06_case_story.md` | 대표 호우 이벤트 발표 스토리 |
| `assets/case_story_top10.csv` | 대표 호우 이벤트 Top10 운영 우선순위 |

현재 민원·폐기물·현장점검 원자료는 확보되지 않았으므로 외부 실적 검증 완료를 주장하지 않습니다. 대신 외부 검증 템플릿과 자동 검증 스크립트를 제공하고, 대표 호우 사례 기반 case validation으로 제출 설득력을 보완합니다.

## Core Claims

- 정밀 수치 예측이 아니라 회복지연 위험 상위 동 선별 모델입니다.
- LOEO R2는 낮지만, Recall@Top20% 82.2%와 Lift@Top20% 4.07x로 운영형 랭킹 성능을 확인했습니다.
- 제한자원 시나리오에서 위험기반 Top20 배치는 무작위 대비 높은 delayed 포착 효율을 보였습니다.
- 최종 활용물은 위험지도보다 `event_priority_table.csv`와 `playbook_table.csv`입니다.

## Suggested Demo Flow

1. 문제: 호우 이후 어느 동부터 점검하고 자원을 배치할지 정량 기준이 부족합니다.
2. 데이터: 생활인구, AWS 강수, 침수흔적, 하수도, 복지·행정시설을 event x district 패널로 결합했습니다.
3. 모델: XGBoost 회귀 예측값을 위험점수로 바꿔 이벤트별 Top-K 행정동을 선별합니다.
4. 검증: R2보다 Precision/Recall/Lift@K를 중심 성능으로 제시합니다.
5. 활용: 이벤트별 우선순위표, 유형별 플레이북, 제한자원 배치 시나리오로 행정 의사결정을 지원합니다.
6. 사례: 2023-07-13, 2024-07-18, 2025-09-04 대표 이벤트 모두 Top20 Lift가 4배 이상으로 나타났습니다.
7. 검증 확장: 민원·폐기물·현장점검 데이터가 확보되면 `data/external/external_validation_template.csv` 형식으로 투입해 Top20/Bottom20 외부 실적 검증을 수행합니다.

## Dashboard Demo

```powershell
python -m streamlit run app\streamlit_app.py --server.port=8503
```

데모 화면은 재난상황실 담당자가 호우 이벤트와 가용 자원 수를 선택하면, 우선 대응 동, 부서별 실행 체크, 자동 상황 브리핑, 검증 근거, 사용 제한을 한 번에 확인하는 흐름으로 구성했습니다.

## Not-To-Claim

- 침수 발생 사전 예측 모델이 아닙니다.
- 복구 완료일의 정밀 예측 모델이 아닙니다.
- What-if와 운영 효율 시나리오는 정책 인과효과나 확정 예산절감액이 아닙니다.
- 생활인구 회복률은 복구 완료가 아니라 생활활동 정상화 대리지표입니다.
