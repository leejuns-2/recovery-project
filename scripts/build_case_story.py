from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
REPORT = OUT / "report_assets"
SUBMISSION = ROOT / "submission"
ASSETS = SUBMISSION / "assets"
DOCS = SUBMISSION / "docs"


def pick_case_event(lift: pd.DataFrame) -> int:
    candidates = lift[lift["n_delayed"].ge(30)].copy()
    if candidates.empty:
        candidates = lift[lift["n_delayed"].gt(0)].copy()
    candidates["score"] = (
        candidates["recall_top20"].fillna(0) * 0.5
        + candidates["lift_top20"].fillna(0).rank(pct=True) * 0.3
        + candidates["top20_delayed_rate"].fillna(0).rank(pct=True) * 0.2
    )
    return int(candidates.sort_values("score", ascending=False).iloc[0]["event_id"])


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    lift = pd.read_csv(REPORT / "top20_lift_by_event.csv")
    priority = pd.read_csv(REPORT / "event_priority_table.csv", dtype={"adm_cd": str})
    capacity = pd.read_csv(REPORT / "capacity_scenario_results.csv")
    case_event = pick_case_event(lift)

    event_lift = lift[lift["event_id"].eq(case_event)].iloc[0]
    event_priority = priority[priority["event_id"].eq(case_event)].sort_values("rank").copy()
    top10 = event_priority.head(10)

    top10.to_csv(ASSETS / "case_story_top10.csv", index=False, encoding="utf-8-sig")
    event_lift.to_frame().T.to_csv(
        ASSETS / "case_story_event_metrics.csv", index=False, encoding="utf-8-sig"
    )

    cap10 = capacity[
        capacity["strategy"].eq("risk_based") & capacity["k_support"].eq(10)
    ].iloc[0]

    type_counts = top10["recovery_type"].value_counts()
    type_text = ", ".join(f"{idx} {cnt}개 동" for idx, cnt in type_counts.items())
    top_names = ", ".join(top10.head(5).apply(lambda r: f"{r['gu_nm']} {r['adm_nm']}", axis=1))
    actions = " / ".join(top10["recommended_action"].dropna().astype(str).unique()[:3])
    departments = ", ".join(top10["department"].dropna().astype(str).unique()[:4])
    row0 = top10.iloc[0]

    md = f"""# Case Study: Event {case_event}

## Situation

- Event date: {row0['event_date']}
- Max rainfall: {row0['max_rainfall']:.1f}mm
- Duration: {int(row0['duration_days'])} days
- Districts evaluated: {int(event_lift['n_districts'])}
- Actual delayed districts: {int(event_lift['n_delayed'])}

## Model Decision

The model selected the following districts as the first response candidates:

{top_names}

Top10 recovery types:

{type_text}

## Evidence

| Metric | Value |
|---|---:|
| Event delayed rate | {event_lift['event_delayed_rate']:.1%} |
| Top20 delayed rate | {event_lift['top20_delayed_rate']:.1%} |
| Bottom20 delayed rate | {event_lift['bottom20_delayed_rate']:.1%} |
| Recall@Top20 | {event_lift['recall_top20']:.1%} |
| Lift@Top20 | {event_lift['lift_top20']:.2f}x |

## Operational Action

- Priority departments: {departments}
- Recommended actions: {actions}
- Monitoring metric: D+3 recovery rate, complaints, field inspection

## Capacity Scenario

If only 10 districts can be covered, use ranks 1-10 in `case_story_top10.csv`.

Historical validation for risk-based Top10:

| Metric | Value |
|---|---:|
| Delayed capture rate | {cap10['delayed_capture_rate']:.1%} |
| Benefit index per resource | {cap10['benefit_index_per_resource']:.1%} |
| Lift | {cap10['mean_lift_k']:.2f}x |

## Interpretation

이 이벤트에서 위험 상위 동은 담당부서·조치시점·자원유형과 함께 우선순위표로 정리됩니다. Top20 선별은 관측된 delayed 동의 {event_lift['recall_top20']:.1%}를 포착했고, 이벤트 전체 평균 대비 {event_lift['lift_top20']:.2f}배 높은 delayed 농축도를 보였습니다.

## Caution

This is not a causal estimate of policy effect. It is an operational ranking and resource allocation sensitivity analysis based on observed post-rainfall recovery outcomes.
"""
    (DOCS / "06_case_study.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
