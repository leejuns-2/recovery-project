# Case Story: Three Representative Rainfall Events

## Why Three Cases

대표 사례는 2023년, 2024년, 2025년 주요 호우 3개로 제시한다. 단일 이벤트만 강조하면 cherry-picking처럼 보일 수 있으므로, 서로 다른 연도의 호우에서 Top20 선별력이 반복되는지 함께 보여준다.

## Cross-Event Evidence

| Event | Actual delayed districts | Event delayed rate | Top20 delayed rate | Recall@Top20 | Lift@Top20 |
|---|---:|---:|---:|---:|---:|
| 2023-07-13 (`event_id=6`) | 49 | 11.5% | 48.8% | 85.7% | 4.25x |
| 2024-07-18 (`event_id=17`) | 46 | 10.8% | 48.8% | 91.3% | 4.52x |
| 2025-09-04 (`event_id=34`) | 37 | 8.7% | 41.9% | 97.3% | 4.82x |

세 이벤트 모두 위험 상위 20%에서 실제 delayed 동이 전체 평균 대비 4배 이상 농축되었다.

## Main Presentation Case: Event 34

## Situation

- Event date: 2025-09-04
- Max rainfall: 74.5mm
- Duration: 1 days
- Districts evaluated: 426
- Actual delayed districts: 37

## Model Decision

The model selected the following districts as the first response candidates:

중구 소공동, 중구 명동, 금천구 가산동, 영등포구 여의동, 강남구 역삼1동

Top10 recovery types:

배수·침수 병목형 4개 동, 고노출 회복지연형 4개 동, 생활지원 공백형 2개 동

## Evidence

| Metric | Value |
|---|---:|
| Event delayed rate | 8.7% |
| Top20 delayed rate | 41.9% |
| Bottom20 delayed rate | 0.0% |
| Recall@Top20 | 97.3% |
| Lift@Top20 | 4.82x |

## Operational Action

- Priority departments: 치수과·청소행정과, 재난상황실·청소행정과, 복지정책과·동주민센터
- Recommended actions: 빗물받이 점검, 배수로 점검, 침수잔재 제거 / 민원대응 인력 증원, 폐기물 수거, 현장 공지 강화 / 안부확인, 임시복지거점 운영, 이동지원
- Monitoring metric: D+3 recovery rate, complaints, field inspection

## Capacity Scenario

If only 10 districts can be covered, use ranks 1-10 in `case_story_top10.csv`.

Historical validation for risk-based Top10:

| Metric | Value |
|---|---:|
| Delayed capture rate | 13.9% |
| Benefit index per resource | 34.1% |
| Lift | 5.90x |

## Presentation Sentence

세 개 대표 호우에서 Top20 Lift는 모두 4배 이상이었다. 특히 2025-09-04 사례에서 모델은 위험 상위 동을 지도 표시로 끝내지 않고, 담당부서·조치시점·자원유형까지 연결한 운영 우선순위표로 변환했다. Top20 선별은 실제 delayed 동의 97.3%를 포착했고, 전체 평균 대비 4.82배 높은 delayed 농축도를 보였다.

## Caution

This is not a causal estimate of policy effect. It is an operational ranking and resource allocation sensitivity analysis based on observed post-rainfall recovery outcomes.
