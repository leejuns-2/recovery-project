# Result Summary

## Objective

집중호우 이후 D+1~D+3 생활활동 회복률이 낮아질 위험이 높은 행정동을 선별하고, 제한된 복구자원 배치 우선순위를 제안합니다.

본 결과는 민원·점검·폐기물 발생량을 직접 예측한 결과가 아니라, 생활활동 회복지연을 기준으로 잠재 행정수요가 커질 수 있는 우선점검 후보를 선별한 결과입니다.

## Data Structure

- 분석 범위: 서울 행정동 단위
- 패널: 29개 호우 이벤트 x 426개 행정동
- 타깃: `min_recovery_rate_d1_d3`
- 정책 KPI: `recovery_days`, `delayed`
- 위험점수: `1 - predicted_min_recovery_d1_d3`

## Performance Message

이 문제는 회복률 절대값을 정밀하게 맞히는 회귀 문제가 아니라, 제한된 복구자원을 우선 투입할 후보 동을 고르는 랭킹 문제입니다. 따라서 R2는 보조 지표이고, 핵심 성능은 Precision/Recall/Lift@K입니다.

## Main Metrics

| Metric | Value | Meaning |
|---|---:|---|
| Recall@Top20% | 82.2% | 전체 delayed 동 중 상위 20%가 포착한 비율 |
| Lift@Top20% | 4.07x | 전체 평균 delayed rate 대비 위험 농축도 |
| Precision@Top20% | 16.3% | 위험 상위 20% 중 실제 delayed 비율 |
| High vs Low recovery days | 1.83 vs 1.06 days | 위험군 간 실제 회복일수 차이 |
| Capacity Top20 lift | 5.55x | 제한자원 배치에서 risk-based Top20의 상대 효율 |
| LOEO R2 | 0.1148 | 새 이벤트에서 절대값 예측 일반화는 제한적 |
| 2025 holdout R2 | 0.4781 | 특정 연도 holdout에서는 설명력 있음 |

## Capacity Scenario

| Strategy | K | Delayed Capture | Lift |
|---|---:|---:|---:|
| Risk-based | 5 | 7.0% | 5.97x |
| Risk-based | 10 | 13.9% | 5.90x |
| Risk-based | 20 | 26.1% | 5.55x |
| Random mean | 20 | 4.6% | 0.97x |

Random baseline은 500회 반복 평균입니다.

## External Validation Status

민원·폐기물·현장점검 원자료는 현재 로컬 프로젝트에 없습니다. 따라서 외부 실적 검증을 완료된 주 검증으로 주장하지 않습니다. 대신 다음 두 가지로 보완합니다.

1. `data/external/external_validation_template.csv` 형식의 외부 검증 템플릿과 자동 검증 스크립트를 제공합니다.
2. 대표 호우 이벤트 case validation을 통해 모델 결과가 운영 우선순위표와 부서별 조치로 연결되는 흐름을 보여줍니다.

따라서 현재 제출본의 검증 범위는 다음처럼 구분합니다.

| 단계 | 검증 질문 | 현재 상태 |
|---|---|---|
| 1차 내부 검증 | 생활인구 회복지연 위험 상위 동을 잘 선별하는가 | 완료 |
| 2차 보조 검증 | 침수흔적·대표 사례와 함께 운영 해석이 가능한가 | 완료 |
| 3차 직접 행정수요 검증 | 민원·점검·폐기물·피해신고 실적과 같은 방향인가 | 템플릿 제공, 자료 확보 시 실행 |

## Case Validation

대표 사례는 단일 이벤트가 아니라 3개 연도 주요 호우로 제시합니다. 이는 특정 이벤트 cherry-picking 우려를 줄이고, 운영 우선순위표가 반복적으로 작동한다는 점을 보여주기 위한 구성입니다.

| Event | Actual delayed districts | Top20 delayed rate | Recall@Top20 | Lift@Top20 |
|---|---:|---:|---:|---:|
| 2023-07-13 (`event_id=6`) | 49 | 48.8% | 85.7% | 4.25x |
| 2024-07-18 (`event_id=17`) | 46 | 48.8% | 91.3% | 4.52x |
| 2025-09-04 (`event_id=34`) | 37 | 41.9% | 97.3% | 4.82x |

세 사례에서 모두 Top20 Lift가 4배 이상으로 나타났습니다. 모델은 위험 상위 동을 단순 지도 표시로 끝내지 않고, 담당부서·조치시점·자원유형까지 연결한 운영 우선순위표로 변환합니다.

## Operational Outputs

- `event_priority_table.csv`: 호우 이벤트별 Top10 행정동, 담당부서, 조치, 모니터링 지표
- `playbook_table.csv`: 회복 유형별 권장 조치
- `capacity_scenario_results.csv`: 지원 가능한 동 수 K별 delayed 포착률과 효율
- `target_sensitivity_summary.csv`: 회복률/지연일수 기준 민감도
- `case_story_top10.csv`: 대표 호우 사례 Top10 우선순위

## Interpretation

LOEO R2=0.1148은 새로운 호우 이벤트에서 회복률 절대값을 정밀 예측하는 데 한계가 있음을 보여줍니다. 그러나 본 연구의 운영 목적은 제한된 복구자원을 우선 투입할 후보 동을 선별하는 것이므로, 성능 평가는 Precision/Recall/Lift@K를 중심으로 수행했습니다. 그 결과 위험 상위 20% 동은 전체 delayed 동의 82.2%를 포착했고, 전체 평균 대비 4.07배 높은 delayed 농축도를 보였습니다.

해석상 “위험 상위 동은 실제 행정수요가 높다”고 단정하지 않습니다. 더 안전한 표현은 “위험 상위 동은 생활활동 회복지연 가능성이 높아, 민원·점검·청소·복지 대응을 먼저 확인할 우선점검 후보로 활용할 수 있다”입니다.
