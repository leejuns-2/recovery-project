# External Validation Plan

## Current Status

현재 공개 저장소에는 민원, 수해 폐기물, 현장점검, 피해신고 실적 원자료가 없습니다. 따라서 외부 실적 검증을 완료된 결과로 주장하지 않고, 데이터가 확보될 때 적용할 검증 설계와 템플릿만 포함합니다.

현재 검증 범위는 생활인구 회복지연 기반 후보 선별까지입니다. 직접 행정수요 자료는 모델이 실제 행정 대응 수요와 연결되는지 확인하기 위해 필요합니다.

## Demand Definitions

| 구분 | 의미 | 현재 반영 방식 |
|---|---|---|
| 관측 행정수요 | 민원 건수, 현장점검 건수, 수해 폐기물 수거량, 피해신고 건수 | 현재 원자료 없음, 확보 시 외부 검증 |
| 잠재 행정수요 | 생활인구 회복지연, 고노출 지역, 배수·침수 병목, 생활지원 공백 | 현재 모델의 직접 산출 대상 |

현재 모델은 관측 행정수요를 직접 예측하지 않고, 생활활동 회복지연 가능성이 큰 우선점검 후보를 선별합니다.

## Data Template

외부 실적 데이터는 아래 파일 형식으로 투입합니다.

```text
data/external/external_validation_template.csv
```

Required keys:

| Column | Meaning |
|---|---|
| `event_id` | 내부 호우 이벤트 ID |
| `event_date` | 이벤트 일자 |
| `adm_cd` | 행정동 코드 |
| `adm_nm` | 행정동명 |
| `gu_nm` | 자치구명 |

Optional validation metrics:

| Column | Meaning |
|---|---|
| `complaint_count_d0_d7` | D0~D+7 침수/배수/생활불편 민원 건수 |
| `waste_ton_d0_d7` | D0~D+7 수해 폐기물 수거량 |
| `field_check_count_d0_d7` | D0~D+7 현장점검 건수 |
| `damage_report_count_d0_d7` | D0~D+7 피해신고 건수 |

## Validation Logic

1. 이벤트별 risk score 상위 20%, 중간 60%, 하위 20%를 구분합니다.
2. 외부 실적 지표를 event_id + adm_cd 기준으로 결합합니다.
3. 위험 상위 20%와 하위 20%의 민원/폐기물/현장점검 실적 평균과 합계를 비교합니다.
4. 지표가 자치구 단위만 확보될 경우, 행정동 risk score를 자치구 단위 평균/상위값으로 집계한 보조 검증으로 낮춰 해석합니다.

## Outputs

```text
outputs/external_validation_summary.csv
outputs/external_validation_by_event.csv
submission/assets/external_validation_summary.csv
submission/assets/external_validation_by_event.csv
```

## Safe Report Sentence

외부 실적 데이터가 확보된 경우:

> 민원·폐기물·현장점검 실적과의 직접 검증을 통해 위험 상위 동이 관측 행정수요와 같은 방향으로 연결되는지 보조적으로 확인하였다.

외부 실적 데이터가 확보되지 않은 경우:

> 민원·폐기물·현장점검 데이터는 향후 검증 확장 항목으로 남기고, 본 제출본에서는 LOEO 기반 Top-K 성능, target sensitivity, 침수흔적 및 사례 검증을 중심으로 모델의 운영 활용 가능성을 평가하였다.

직접 행정수요 자료가 없는 현재 상태:

> 이 모델은 관측 행정수요를 직접 예측하지 않고, 생활인구 회복지연을 기준으로 우선점검 후보를 선별한다. 직접 행정수요 검증은 자료 확보 뒤 수행해야 한다.
