# Recovery Priority AX

## Problem

집중호우가 끝난 뒤 생활활동 회복이 늦어질 가능성이 큰 서울 행정동을 순위화하고, 제한된 복구자원을 어디에 먼저 배치할지 지원하는 프로젝트입니다.

침수 위험과 회복지연 위험은 같은 문제가 아닙니다. 이 모델은 침수 발생이나 정확한 회복 완료일을 예측하지 않습니다. 민원·폐기물·현장점검 수요를 직접 예측하는 모델도 아닙니다. 생활인구 회복지연을 기준으로 먼저 확인할 후보 지역을 선별합니다.

## Data

저장된 분석 결과는 다음 범주의 데이터를 결합해 만들었습니다.

- 행정동별 생활인구
- 호우 이벤트와 AWS 강수
- 침수흔적
- 하수도 관련 정보
- 복지·행정시설

분석 단위는 호우 이벤트와 행정동의 조합이며, 타깃은 D+1~D+3의 최소 생활인구 회복률입니다. `recovery_days`와 `delayed`는 운영 평가 지표로 사용했습니다.

## Method

XGBoost 회귀 예측값을 회복지연 위험점수로 변환하고, 이벤트별로 행정동을 정렬합니다. 목적이 제한된 자원의 우선 배치이므로 절대값 회귀 성능과 함께 Precision, Recall, Lift@Top-K를 평가합니다.

새 호우 이벤트에 대한 일반화를 확인하기 위해 leave-one-event-out(LOEO) 결과를 사용했습니다. 특정 연도 holdout 결과도 함께 남겼지만, 낮은 LOEO R²는 숨기지 않고 절대 회복률 예측의 한계로 해석합니다.

## Results

커밋된 결과 파일에서 확인되는 주요 수치는 다음과 같습니다.

| Metric | Result | Interpretation |
|---|---:|---|
| Recall@Top20% | 82.2% | 전체 delayed 동 중 위험 상위 20%가 포착한 비율 |
| Lift@Top20% | 4.07x | 전체 평균 대비 상위 20%의 delayed 농축도 |
| Precision@Top20% | 16.3% | 위험 상위 20% 중 delayed 동의 비율 |
| High vs low recovery days | 1.83 vs 1.06 days | 위험 상·하위군의 관측 회복일수 차이 |
| Capacity Top20 lift | 5.55x | 제한자원 시나리오의 위험기반 선별 효율 |
| LOEO R² | 0.1148 | 새 이벤트의 절대값 예측 성능은 낮음 |
| 2025 holdout R² | 0.4781 | 특정 연도 holdout 결과 |

랭킹 성능이 절대 회귀 성능의 약점을 없애는 것은 아닙니다. 이 결과는 우선점검 후보를 고르는 용도에는 신호가 있지만, 정확한 회복률이나 회복일을 예측하기에는 일반화가 제한적이라는 뜻입니다.

상세 표는 [`submission/docs/02_result_summary.md`](submission/docs/02_result_summary.md), 한계는 [`submission/docs/03_limitations.md`](submission/docs/03_limitations.md), 대표 이벤트는 [`submission/docs/06_case_study.md`](submission/docs/06_case_study.md)에서 확인할 수 있습니다.

## Demo

커밋된 `submission/assets` CSV를 읽는 Streamlit 데모는 공개 저장소만으로 실행할 수 있습니다.

```powershell
pip install -r requirements-submission.txt
python -m streamlit run app\streamlit_app.py --server.port=8503
```

데모는 이벤트, 자원 수, 우선순위 행정동, 권장 대응, 저장된 평가 지표를 보여줍니다. 실시간 예측 서비스는 아닙니다.

## Reproducibility

공개 저장소에서 바로 확인하거나 실행할 수 있는 범위:

- `submission/assets/`의 최종 결과 CSV와 HTML
- Streamlit 데모
- 외부 행정수요 검증용 빈 템플릿과 검증 스크립트 구조

공개 저장소만으로 재생성할 수 없는 범위:

- 모델 학습과 LOEO 예측
- `scripts/generate_operational_evidence.py`가 만드는 전체 분석 산출물
- case-study 재생성

재생성 스크립트는 `data/processed/*.parquet`, `outputs/*.csv`, `outputs/report/*.csv` 등 Git에서 제외된 원자료·중간결과를 요구합니다. 따라서 이 README는 해당 명령을 fresh clone의 전체 재현 절차로 제시하지 않습니다. 비공개 데이터가 있는 원래 작업 환경에서는 스크립트를 다시 실행할 수 있지만, 공개 저장소에서는 최종 아티팩트와 데모 재현이 가능한 범위입니다.

## Limitations

- 생활인구 회복은 복구 완료가 아니라 생활활동 정상화의 대리지표입니다.
- 민원·폐기물·현장점검 같은 직접 행정수요 자료로 검증하지 못했습니다.
- LOEO R²가 낮아 새로운 호우의 절대 회복률 예측에는 한계가 있습니다.
- What-if와 capacity 결과는 인과효과나 확정 예산절감액이 아니라 동일 가정 아래의 민감도 분석입니다.
- `duration_days`는 이벤트 종료 뒤 확정되므로 D+1~D+3 갱신 단계에서만 사용할 수 있습니다.
- 침수흔적 overlap은 물리적 침수 검증이 아니라 보조 비교 자료입니다.
- 서울 외 지역에 적용하려면 데이터 정의와 모델을 다시 점검해야 합니다.
