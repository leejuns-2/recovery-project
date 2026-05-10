from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "submission" / "assets"


st.set_page_config(page_title="RecoveryOps Agent", layout="wide")


@st.cache_data
def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(ASSETS / name)


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def number(value: float) -> str:
    return f"{value:,.0f}"


def metric_value(perf: pd.DataFrame, indicator: str, default: str = "-") -> str:
    value = perf.loc[perf["indicator"].eq(indicator), "value"]
    return value.iloc[0] if not value.empty else default


def capacity_row(capacity: pd.DataFrame, k_support: int) -> pd.Series:
    row = capacity[
        capacity["strategy"].eq("risk_based") & capacity["k_support"].eq(k_support)
    ]
    if row.empty:
        return capacity[capacity["strategy"].eq("risk_based")].iloc[0]
    return row.iloc[0]


def make_briefing(event_df: pd.DataFrame, support_k: int, cap: pd.Series) -> str:
    selected = event_df.head(min(support_k, len(event_df)))
    top_names = ", ".join(
        selected.head(5).apply(lambda r: f"{r['gu_nm']} {r['adm_nm']}", axis=1)
    )
    types = selected["recovery_type"].value_counts().head(3)
    type_text = ", ".join([f"{idx} {cnt}개 동" for idx, cnt in types.items()])
    departments = ", ".join(selected["department"].dropna().astype(str).unique()[:4])
    actions = " / ".join(selected["recommended_action"].dropna().astype(str).unique()[:3])
    date = event_df["event_date"].iloc[0]
    max_rainfall = event_df["max_rainfall"].iloc[0]
    duration = event_df["duration_days"].iloc[0]

    return (
        f"{date} 호우 이벤트는 최대강수량 {max_rainfall:.1f}mm, 지속 {int(duration)}일로 집계되었습니다. "
        f"현재 자원 용량을 {support_k}개 동으로 두면 우선 대응 후보는 {top_names} 순입니다. "
        f"선정 동의 주요 회복유형은 {type_text}이며, 우선 협업 부서는 {departments}입니다. "
        f"권장 조치는 {actions}입니다. "
        f"과거 검증 기준으로 risk-based Top{support_k} 배치는 평균 delayed capture "
        f"{pct(cap['delayed_capture_rate'])}, lift {cap['mean_lift_k']:.2f}배 수준의 상대 효율을 보였습니다. "
        "이 결과는 실제 자원 투입의 인과효과가 아니라 동일 기준에서 배치전략별 상대 효율을 비교한 민감도 분석입니다."
    )


perf = read_csv("core_performance_summary.csv")
ranking = read_csv("ranking_metrics.csv")
priority = read_csv("event_priority_table.csv")
playbook = read_csv("playbook_table.csv")
capacity = read_csv("capacity_scenario_results.csv")
target_sensitivity = read_csv("target_sensitivity_summary.csv")
timing = read_csv("model_timing_comparison.csv")
flood_interp = read_csv("flood_trace_overlap_interpretation.csv")
external_validation = read_csv("external_validation_summary.csv")
case_metrics = read_csv("case_story_event_metrics.csv")
case_top10 = read_csv("case_story_top10.csv")


st.title("RecoveryOps Agent")
st.caption("집중호우 이후 72시간 생활활동 회복지연 위험 선별 및 복구자원 우선배치 데모")

st.markdown(
    "이 화면은 재난상황실 담당자가 호우 이벤트를 선택하고, 제한된 점검반·청소차·복지 인력 규모에 맞춰 "
    "어느 행정동부터 확인할지 결정하는 상황을 가정한 데모입니다."
)

with st.sidebar:
    st.header("상황 설정")
    events = priority[["event_id", "event_date"]].drop_duplicates().sort_values("event_id")
    event_labels = {
        int(row.event_id): f"event {int(row.event_id)} | {row.event_date}"
        for row in events.itertuples(index=False)
    }
    selected_event = st.selectbox(
        "호우 이벤트",
        list(event_labels.keys()),
        format_func=lambda x: event_labels[x],
    )
    support_k = st.select_slider("가용 자원", options=[5, 10, 20, 30, 50], value=10)
    st.markdown("자원은 하루에 커버 가능한 행정동 수로 해석합니다.")

event_priority = (
    priority[priority["event_id"].eq(selected_event)]
    .sort_values("rank")
    .reset_index(drop=True)
)
selected_capacity = capacity_row(capacity, support_k)
selected_plan = event_priority.head(min(support_k, len(event_priority))).copy()

top_metrics = st.columns(5)
top_metrics[0].metric("Recall@Top20", metric_value(perf, "Recall@Top20%"))
top_metrics[1].metric("Lift@Top20", metric_value(perf, "Lift@Top20%"))
top_metrics[2].metric("High-risk delayed", metric_value(perf, "High-risk 20% delayed rate"))
top_metrics[3].metric("Capacity lift", f"{selected_capacity['mean_lift_k']:.2f}x")
top_metrics[4].metric("Delayed capture", pct(selected_capacity["delayed_capture_rate"]))

tab_ops, tab_agent, tab_case, tab_evidence, tab_limits = st.tabs(
    ["상황실", "AI 브리핑", "대표 사례", "검증 근거", "한계와 사용조건"]
)

with tab_ops:
    st.subheader("우선 대응 후보")
    event_info = event_priority.iloc[0]
    st.markdown(
        f"**이벤트 일자:** {event_info['event_date']}  "
        f"**최대강수량:** {event_info['max_rainfall']:.1f}mm  "
        f"**지속일수:** {int(event_info['duration_days'])}일"
    )

    plan_cols = [
        "rank",
        "adm_nm",
        "gu_nm",
        "risk_score",
        "predicted_min_recovery_d1_d3",
        "expected_delay_level",
        "recovery_type",
        "top_reason_1",
        "recommended_action",
        "department",
        "timing",
        "resource_type",
        "monitoring_metric",
    ]
    st.dataframe(
        selected_plan[plan_cols],
        use_container_width=True,
        hide_index=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("선정 동 수", f"{len(selected_plan)}개")
    c2.metric("취약 생활인구 커버량", number(selected_capacity["vulnerable_pop_covered"]))
    c3.metric("추가 자원 한계효과", pct(selected_capacity["marginal_gain"]))

    st.subheader("유형별 조치 플레이북")
    visible_types = selected_plan["recovery_type"].unique()
    st.dataframe(
        playbook[playbook["recovery_type"].isin(visible_types)],
        use_container_width=True,
        hide_index=True,
    )

with tab_agent:
    st.subheader("자동 상황 브리핑")
    briefing = make_briefing(event_priority, support_k, selected_capacity)
    st.info(briefing)

    st.subheader("부서별 실행 체크")
    action_table = (
        selected_plan.groupby(["timing", "department", "resource_type"], as_index=False)
        .agg(
            districts=("adm_nm", lambda x: ", ".join(x.astype(str).head(8))),
            n_districts=("adm_nm", "count"),
            recommended_action=("recommended_action", lambda x: " / ".join(x.astype(str).unique()[:2])),
        )
        .sort_values(["timing", "n_districts"], ascending=[True, False])
    )
    st.dataframe(action_table, use_container_width=True, hide_index=True)

    st.subheader("담당자 질문 예시")
    examples = [
        f"점검반이 {support_k}개 동만 커버 가능하면 어디부터 가야 하나?",
        "복지 인력은 어느 유형 동에 먼저 배치해야 하나?",
        "이 결과를 정책효과로 말해도 되는가?",
    ]
    for question in examples:
        st.markdown(f"- {question}")

with tab_case:
    st.subheader("대표 호우 사례")
    case = case_metrics.iloc[0]
    st.markdown(
        f"**Event {int(case['event_id'])}** | "
        f"delayed {int(case['n_delayed'])}개 동 | "
        f"Top20 delayed {pct(case['top20_delayed_rate'])} | "
        f"Recall@Top20 {pct(case['recall_top20'])} | "
        f"Lift {case['lift_top20']:.2f}x"
    )
    st.dataframe(
        case_top10[
            [
                "rank",
                "adm_nm",
                "gu_nm",
                "risk_score",
                "recovery_type",
                "top_reason_1",
                "recommended_action",
                "department",
                "timing",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.info(
        "이 사례는 모델 결과가 단순 위험점수에서 끝나지 않고 담당부서, 조치시점, 자원유형까지 "
        "연결되는 운영 우선순위표로 변환된다는 점을 보여주는 발표용 사례입니다."
    )

with tab_evidence:
    st.subheader("랭킹 성능")
    st.dataframe(ranking, use_container_width=True, hide_index=True)
    st.image(str(ASSETS / "top20_lift_report.png"), use_container_width=True)

    st.subheader("제한자원 시나리오")
    st.dataframe(capacity, use_container_width=True, hide_index=True)
    st.image(str(ASSETS / "capacity_scenario_chart.png"), use_container_width=True)

    st.subheader("타깃 기준 민감도")
    st.dataframe(target_sensitivity, use_container_width=True, hide_index=True)

    st.subheader("외부 실적 검증 상태")
    st.dataframe(external_validation, use_container_width=True, hide_index=True)
    st.info(
        "현재 대시보드는 관측 행정수요를 직접 예측하지 않고, 생활인구 회복지연 기반의 "
        "잠재 행정수요 우선점검 후보를 보여줍니다. 민원·점검·폐기물 자료가 확보되면 "
        "external_validation_template.csv에 연결해 직접 검증을 추가할 수 있습니다."
    )

with tab_limits:
    st.subheader("사용 가능 시점")
    st.dataframe(timing, use_container_width=True, hide_index=True)

    st.subheader("침수흔적 overlap 해석")
    st.dataframe(flood_interp, use_container_width=True, hide_index=True)

    st.warning(
        "본 모델은 침수 발생 사전예측이나 회복 완료일 정밀예측 모델이 아닙니다. "
        "생활인구 회복률은 복구 완료가 아니라 생활활동 정상화의 대리지표이며, "
        "현재 산출물은 관측 행정수요 직접 예측이 아니라 잠재 행정수요 우선점검 후보 선별입니다. "
        "What-if와 capacity scenario는 실제 정책효과가 아닌 상대 효율 민감도 분석입니다."
    )
