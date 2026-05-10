# External Data Source Candidates

## Why Add These Data

현재 모델의 타깃인 생활인구 회복률은 복구 완료 지표가 아니라 생활활동 정상화의 대리지표입니다. 따라서 민원, 폐기물, 현장점검, 피해신고 실적을 붙이면 모델 위험점수가 관측 행정수요와 같은 방향인지 직접 검증할 수 있습니다. 자료가 없을 때는 관측 행정수요를 예측했다고 주장하지 않고, 잠재 행정수요 우선점검 후보 선별로 해석합니다.

## Priority

| Priority | Data | Best Granularity | Use | Status |
|---:|---|---|---|---|
| 1 | 침수/도로/배수 민원 | event x adm_dong x day | 모델 위험 상위 동이 관측 생활불편 수요와 같은 방향인지 검증 | 일부 공개 통계 가능, 세부 원자료는 제한 가능 |
| 2 | 현장점검 건수 | event x adm_dong x day | 우선순위 동이 실제 점검수요와 연결되는지 검증 | 부서 내부/정보공개 가능성 높음 |
| 3 | 수해 폐기물 수거량 | event x gu or adm_dong x day | 청소·폐기물 자원 배치 필요성 검증 | 자치구/부서 자료 가능성 |
| 4 | 피해 신고 건수 | event x gu or adm_dong x day | 실제 피해행정수요와의 방향성 검증 | 재난부서 내부/정보공개 가능성 |
| 5 | 공개 위치별 불편신고 통계 | month x location/category | 직접 검증이 어려울 때 보조 방향성 점검 | 서울 열린데이터광장 공개 |

## Public Candidate Sources

| Candidate | Source | How to Use | Limitation |
|---|---|---|---|
| 서울시 위치별 불편신고건수 정보 | 서울 열린데이터광장 `OA-12053` | 위치/월별 불편신고 건수를 행정동 또는 자치구로 매핑해 complaint proxy 생성 | 월 단위이면 D0~D+7 직접 검증은 어려움 |
| 서울시 스마트 불편신고 분야별 신고 현황 | 서울 열린데이터광장 `OA-12051` | 도로, 청소, 배수 관련 분야가 있으면 월별 행정수요 proxy로 사용 | 분야별/월별 통계 중심, 행정동 직접 매칭 제한 가능 |
| 응답소/120다산콜 침수 민원 | 서울시/120다산콜 내부 데이터 | 침수·배수·도로 민원을 이벤트 창 D0~D+7로 집계 | 원자료는 공개되지 않을 수 있어 협조/정보공개 필요 |
| 침수흔적도 | 서울 열린데이터광장 `OA-15636` | 이미 결합 완료. 물리적 침수면적과 회복지연 위험의 차이 해석 | 현재 결과는 고위험 동과 침수면적 상위 지역 overlap이 낮음 |

## Validation Design

1. 민원/폐기물/점검/피해 데이터를 `event_id + adm_cd` 기준으로 정리합니다.
2. `data/external/external_validation_template.csv`에 값을 채웁니다.
3. `python scripts\external_validation.py`를 실행합니다.
4. `outputs/external_validation_summary.csv`에서 high_20, middle_60, low_20의 외부 실적 평균/합계를 비교합니다.

## Interpretation Rules

외부 지표가 high_20에서 높으면:

> 위험 상위 동이 관측 행정수요 지표에서도 높게 나타나, 생활인구 회복지연 위험점수가 복구운영 수요와 같은 방향임을 보조적으로 확인하였다.

외부 지표가 차이가 없거나 반대이면:

> 외부 실적 지표와의 연결성은 제한적이었다. 본 모델은 해당 실적의 직접 예측기가 아니라 생활활동 회복지연 후보군을 선별하는 운영형 랭킹 도구로 해석한다.

데이터가 없으면:

> 외부 실적 데이터는 향후 검증 확장 항목으로 남기고, 본 제출본에서는 LOEO 기반 Top-K 성능과 대표 사례 검증을 중심으로 운영 활용 가능성을 평가하였다.

## Sources

- 서울시 위치별 불편신고건수 정보, 서울 열린데이터광장: https://data.seoul.go.kr/dataList/OA-12053/A/1/datasetView.do
- 서울시 스마트 불편신고 분야별 신고 현황, 서울 열린데이터광장: https://data.seoul.go.kr/dataList/OA-12051/A/1/datasetView.do
- 서울시 침수흔적도, 서울 열린데이터광장: https://data.seoul.go.kr/dataList/OA-15636/F/1/datasetView.do
- 120다산콜 실시간 침수 민원 대응 시스템 관련 보도: https://www.fnnews.com/news/202508221115210594
