# External Validation Data Guide

민원·폐기물·현장점검·피해신고 실적 데이터가 확보되면 본 폴더에 넣습니다. 현재 프로젝트의 외부 검증 스크립트는 `external_validation_template.csv` 형식을 읽어 Top20/Bottom20 외부 실적 비교표를 생성합니다.

## Required Join Keys

| Column | Required | Meaning |
|---|---|---|
| `event_id` | yes | 내부 호우 이벤트 ID |
| `event_date` | recommended | 이벤트 일자 |
| `adm_cd` | yes | 행정동 코드 |
| `adm_nm` | recommended | 행정동명 |
| `gu_nm` | recommended | 자치구명 |

## Recommended Metrics

| Column | Priority | Meaning |
|---|---:|---|
| `complaint_count_d0_d7` | 1 | D0~D+7 침수/배수/도로/생활불편 민원 건수 |
| `field_check_count_d0_d7` | 2 | D0~D+7 현장점검 건수 |
| `waste_ton_d0_d7` | 3 | D0~D+7 수해 폐기물 수거량 |
| `damage_report_count_d0_d7` | 4 | D0~D+7 피해신고 건수 |

## Granularity Rules

가장 좋은 단위는 `event_id x adm_cd`입니다. 데이터가 자치구 단위만 있으면 `event_id x gu_nm`으로 집계해 보조 검증으로 낮춰 사용합니다. 월 단위 데이터만 있으면 이벤트별 검증이 아니라 `월별/자치구별 사후 행정수요 방향성 점검`으로만 표현합니다.

## Rebuild

```powershell
python scripts\external_validation.py
```

If no usable metric columns are filled, the script writes a `not_available` status file instead of pretending validation was completed.

외부 데이터의 제공기관, 기간, 집계 단위, 이용 조건은 `source_note`에 기록해야 합니다. 개인정보나 민원 원문은 이 저장소에 커밋하지 않습니다.
