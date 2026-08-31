# Case Study: Three Rainfall Events

서로 다른 연도의 세 호우 이벤트에서 위험 상위 20%의 delayed 농축도를 확인했습니다. 이는 대표 사례 분석이며, 전체 이벤트에 대한 추가 일반화 근거로 과장하지 않습니다.

| Event | Actual delayed districts | Event delayed rate | Top20 delayed rate | Recall@Top20 | Lift@Top20 |
|---|---:|---:|---:|---:|---:|
| 2023-07-13 (`event_id=6`) | 49 | 11.5% | 48.8% | 85.7% | 4.25x |
| 2024-07-18 (`event_id=17`) | 46 | 10.8% | 48.8% | 91.3% | 4.52x |
| 2025-09-04 (`event_id=34`) | 37 | 8.7% | 41.9% | 97.3% | 4.82x |

## Event 34 Example

2025-09-04 이벤트에서 저장된 우선 대응 후보에는 중구 소공동·명동, 금천구 가산동, 영등포구 여의동, 강남구 역삼1동이 포함됩니다. 우선순위는 회복지연 유형과 연결되어 배수·침수 점검, 생활지원, 현장 공지 등의 확인 항목을 제공합니다.

이 이벤트의 위험 상위 20%는 delayed 동의 97.3%를 포착했고 Lift@Top20은 4.82배였습니다. 이 값은 해당 이벤트에서 관측된 사후 평가 결과이며, 정책 개입 효과나 미래 이벤트 성능을 뜻하지 않습니다.

상세 행정동 순위는 `../assets/case_story_top10.csv`, 이벤트별 수치는 `../assets/case_story_event_metrics.csv`에 있습니다.

## Capacity Interpretation

전체 검증 결과에서 위험기반 Top10의 delayed capture rate는 13.9%, lift는 5.90배였습니다. 자원 수별 결과는 상대적 선별 효율을 비교하기 위한 민감도 분석입니다. 실제 자원 배치가 같은 효과를 낸다는 인과 추정은 아닙니다.
