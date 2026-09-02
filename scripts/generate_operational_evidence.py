from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
REPORT = OUT / "report_assets"
TOP_PCTS = [0.1, 0.2, 0.3]
K_SUPPORT = [5, 10, 20, 30, 50]
N_RANDOM_ITER = 500


GU_MAP = {
    "11010": "종로구",
    "11020": "중구",
    "11030": "용산구",
    "11040": "성동구",
    "11050": "광진구",
    "11060": "동대문구",
    "11070": "중랑구",
    "11080": "성북구",
    "11090": "강북구",
    "11100": "도봉구",
    "11110": "노원구",
    "11120": "은평구",
    "11130": "서대문구",
    "11140": "마포구",
    "11150": "양천구",
    "11160": "강서구",
    "11170": "구로구",
    "11180": "금천구",
    "11190": "영등포구",
    "11200": "동작구",
    "11210": "관악구",
    "11220": "서초구",
    "11230": "강남구",
    "11240": "송파구",
    "11250": "강동구",
}


def add_gu_name(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["gu_nm"] = out["adm_cd"].astype(str).str[:5].map(GU_MAP).fillna("미상")
    return out


def require_file(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    return path


def select_top_bottom_by_event(
    df: pd.DataFrame,
    score_col: str,
    pct: float,
    event_col: str = "event_id",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select the same Top/Bottom pct definition everywhere: ceil within each event."""
    top_parts = []
    bottom_parts = []
    for _, part in df.groupby(event_col, sort=False):
        k = max(1, int(np.ceil(len(part) * pct)))
        ordered = part.sort_values(score_col, ascending=False)
        top_parts.append(ordered.head(k))
        bottom_parts.append(ordered.tail(k))
    return pd.concat(top_parts, ignore_index=True), pd.concat(bottom_parts, ignore_index=True)


def compute_recovery_days(recovery_daily: pd.DataFrame, threshold: float) -> pd.DataFrame:
    df = recovery_daily.copy()
    df["is_recovered"] = df["recovery_rate"].ge(threshold)
    df = df.sort_values(["event_id", "adm_cd", "relative_day"])
    df["next_recovered"] = df.groupby(["event_id", "adm_cd"])["is_recovered"].shift(-1).fillna(False)
    df["two_day_recovered"] = df["is_recovered"] & df["next_recovered"]

    first = (
        df[df["two_day_recovered"]]
        .groupby(["event_id", "adm_cd"], as_index=False)["relative_day"]
        .min()
        .rename(columns={"relative_day": "recovery_days_alt"})
    )
    base = df[["event_id", "adm_cd", "adm_nm"]].drop_duplicates()
    max_day = df.groupby(["event_id", "adm_cd"], as_index=False)["relative_day"].max()
    result = base.merge(first, on=["event_id", "adm_cd"], how="left").merge(
        max_day, on=["event_id", "adm_cd"], how="left"
    )
    result["recovery_days_alt"] = result["recovery_days_alt"].fillna(result["relative_day"] + 1)
    return result.drop(columns=["relative_day"])


def build_target_sensitivity() -> None:
    recovery_daily = pd.read_parquet(require_file(DATA / "recovery_daily.parquet"))
    preds = pd.read_csv(require_file(OUT / "loeo_predictions.csv"))
    recovery_daily["adm_cd"] = recovery_daily["adm_cd"].astype(str)
    preds["adm_cd"] = preds["adm_cd"].astype(str)

    scenarios = [
        (0.85, 3),
        (0.85, 4),
        (0.90, 4),
        (0.95, 4),
        (0.90, 5),
    ]

    rows = []
    for threshold, delayed_days in scenarios:
        labels = compute_recovery_days(recovery_daily, threshold)
        labels["delayed_alt"] = labels["recovery_days_alt"].ge(delayed_days).astype(int)

        eval_df = preds[["event_id", "adm_cd", "risk_score"]].merge(
            labels[["event_id", "adm_cd", "delayed_alt", "recovery_days_alt"]],
            on=["event_id", "adm_cd"],
            how="inner",
        )

        top, bottom = select_top_bottom_by_event(eval_df, "risk_score", 0.2)

        overall = eval_df["delayed_alt"].mean()
        top_rate = top["delayed_alt"].mean()
        bottom_rate = bottom["delayed_alt"].mean()
        rows.append(
            {
                "recovery_threshold": f"{int(threshold * 100)}%",
                "delayed_threshold_days": delayed_days,
                "delayed_rate": round(overall, 4),
                "top_20pct_delayed_rate": round(top_rate, 4),
                "bottom_20pct_delayed_rate": round(bottom_rate, 4),
                "lift": round(top_rate / overall, 4) if overall else pd.NA,
                "top_20pct_mean_recovery_days": round(top["recovery_days_alt"].mean(), 4),
                "bottom_20pct_mean_recovery_days": round(bottom["recovery_days_alt"].mean(), 4),
            }
        )

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "target_sensitivity_summary.csv", index=False, encoding="utf-8-sig")
    out.to_csv(REPORT / "target_sensitivity_summary.csv", index=False, encoding="utf-8-sig")


def build_ranking_support_tables() -> None:
    preds = pd.read_csv(require_file(OUT / "loeo_predictions.csv"))
    preds["adm_cd"] = preds["adm_cd"].astype(str)
    rows = []
    sensitivity_rows = []
    summary_rows = []

    n_events_no_delayed = int(preds.groupby("event_id")["delayed"].sum().eq(0).sum())
    overall_delayed_rate = preds["delayed"].mean()
    for pct in TOP_PCTS:
        top_all, _ = select_top_bottom_by_event(preds, "risk_score", pct)
        global_precision = top_all["delayed"].mean()
        global_recall = top_all["delayed"].sum() / preds["delayed"].sum()
        global_lift = global_precision / overall_delayed_rate if overall_delayed_rate else pd.NA

        event_rows_for_pct = []
        for event_id, part in preds.groupby("event_id"):
            event_rate = part["delayed"].mean()
            n_delayed = int(part["delayed"].sum())
            k = max(1, int(np.ceil(len(part) * pct)))
            ordered = part.sort_values("risk_score", ascending=False)
            selected = ordered.head(k)
            precision = selected["delayed"].mean()
            recall = selected["delayed"].sum() / n_delayed if n_delayed else pd.NA
            lift = precision / event_rate if event_rate else pd.NA
            event_rows_for_pct.append({"precision": precision, "recall": recall, "lift": lift})
            sensitivity_rows.append(
                {
                    "event_id": event_id,
                    "top_pct": pct,
                    "k": k,
                    "precision": round(precision, 4),
                    "recall": round(recall, 4) if pd.notna(recall) else pd.NA,
                    "lift": round(lift, 4) if pd.notna(lift) else pd.NA,
                    "event_delayed_rate": round(event_rate, 4),
                    "n_delayed": n_delayed,
                }
            )
            if pct == 0.2:
                bottom = ordered.tail(k)
                rows.append(
                    {
                        "event_id": event_id,
                        "n_districts": len(part),
                        "k_at_20pct": k,
                        "event_delayed_rate": round(event_rate, 4),
                        "top_20pct_delayed_rate": round(precision, 4),
                        "bottom_20pct_delayed_rate": round(bottom["delayed"].mean(), 4),
                        "recall_at_20pct": round(recall, 4) if pd.notna(recall) else pd.NA,
                        "lift_at_20pct": round(lift, 4) if pd.notna(lift) else pd.NA,
                        "n_delayed": n_delayed,
                    }
                )
        event_metric_df = pd.DataFrame(event_rows_for_pct)
        summary_rows.append(
            {
                "top_pct": pct,
                "global_precision": round(global_precision, 4),
                "global_recall": round(global_recall, 4),
                "global_lift": round(global_lift, 4) if pd.notna(global_lift) else pd.NA,
                "macro_precision": round(event_metric_df["precision"].mean(skipna=True), 4),
                "macro_recall": round(event_metric_df["recall"].mean(skipna=True), 4),
                "macro_lift": round(event_metric_df["lift"].mean(skipna=True), 4),
                "overall_delayed_rate": round(overall_delayed_rate, 4),
                "n_events_no_delayed": n_events_no_delayed,
            }
        )

    pd.DataFrame(summary_rows).to_csv(
        OUT / "ranking_metrics.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(sensitivity_rows).to_csv(
        OUT / "topk_sensitivity.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(rows).to_csv(
        OUT / "top20_lift_by_event.csv", index=False, encoding="utf-8-sig"
    )


def enrich_priority_tables() -> None:
    event_priority = pd.read_csv(require_file(REPORT / "event_priority_table.csv"))
    event_priority = add_gu_name(event_priority)
    if "event_rank" in event_priority.columns:
        event_priority = event_priority.rename(columns={"event_rank": "rank"})

    event_priority["expected_delay_level"] = pd.cut(
        event_priority["rank"],
        bins=[0, 3, 7, float("inf")],
        labels=["높음", "중간", "낮음"],
        right=True,
    ).astype(str)
    event_priority["resource_type"] = event_priority["department"].map(
        lambda x: "치수 / 청소"
        if "치수" in str(x)
        else ("복지" if "복지" in str(x) or "주민센터" in str(x) else "상황관리 / 청소")
    )
    event_priority["monitoring_metric"] = "D+3 회복률, 민원, 현장점검"

    preferred = [
        "event_id",
        "event_date",
        "rank",
        "adm_nm",
        "gu_nm",
        "risk_score",
        "predicted_min_recovery_d1_d3",
        "expected_delay_level",
        "recovery_type",
        "top_reason_1",
        "top_reason_2",
        "top_reason_3",
        "recommended_action",
        "department",
        "timing",
        "resource_type",
        "monitoring_metric",
    ]
    rest = [c for c in event_priority.columns if c not in preferred]
    event_priority = event_priority[preferred + rest]
    event_priority.to_csv(REPORT / "event_priority_table.csv", index=False, encoding="utf-8-sig")
    event_priority.to_csv(DATA / "event_priority_table.csv", index=False, encoding="utf-8-sig")

    stable_path = DATA / "historical_priority_table_stable.csv"
    if stable_path.exists():
        stable = add_gu_name(pd.read_csv(stable_path))
        stable["expected_delay_level"] = pd.cut(
            stable["historical_priority_score"],
            bins=[-0.01, 0.33, 0.66, 1.01],
            labels=["낮음", "중간", "높음"],
        ).astype(str)
        stable["resource_type"] = stable["department"].map(
            lambda x: "치수 / 청소"
            if "치수" in str(x)
            else ("복지" if "복지" in str(x) or "주민센터" in str(x) else "상황관리 / 청소")
        )
        stable["monitoring_metric"] = "우기 전 점검, D+3 회복률, 민원"
        stable.to_csv(DATA / "historical_priority_table_stable.csv", index=False, encoding="utf-8-sig")
        stable.head(30).to_csv(
            REPORT / "historical_priority_stable_top30.csv",
            index=False,
            encoding="utf-8-sig",
        )


def update_core_performance() -> None:
    ranking = pd.read_csv(require_file(OUT / "ranking_metrics.csv"))
    top20 = ranking.loc[ranking["top_pct"].eq(0.2)].iloc[0]
    perf = pd.read_csv(require_file(REPORT / "core_performance_summary.csv"))

    additions = pd.DataFrame(
        [
            {
                "indicator": "Precision@20%",
                "value": f"{top20['global_precision'] * 100:.1f}%",
                "interpretation": "위험 상위 20% 중 실제 지연 동 비율",
            },
            {
                "indicator": "Recall@20%",
                "value": f"{top20['global_recall'] * 100:.1f}%",
                "interpretation": "전체 지연 동 중 상위 20%가 포착한 비율",
            },
            {
                "indicator": "Lift@20%",
                "value": f"{top20['global_lift']:.2f}x",
                "interpretation": "전체 평균 delayed rate 대비 위험 농축도",
            },
        ]
    )
    perf = perf[~perf["indicator"].isin(additions["indicator"])]
    pd.concat([perf, additions], ignore_index=True).to_csv(
        REPORT / "core_performance_summary.csv", index=False, encoding="utf-8-sig"
    )
    pd.concat([perf, additions], ignore_index=True).to_csv(
        OUT / "core_performance_summary.csv", index=False, encoding="utf-8-sig"
    )


def enrich_capacity_scenarios() -> None:
    preds = pd.read_csv(require_file(OUT / "loeo_predictions.csv"))
    panel = pd.read_parquet(require_file(DATA / "panel_event_district.parquet"))
    preds["adm_cd"] = preds["adm_cd"].astype(str)
    panel["adm_cd"] = panel["adm_cd"].astype(str)
    eval_df = preds.merge(
        panel[["event_id", "adm_cd", "baseline_pop", "elderly_ratio"]],
        on=["event_id", "adm_cd"],
        how="left",
    )
    eval_df["vulnerable_pop_proxy"] = eval_df["baseline_pop"] * eval_df["elderly_ratio"]

    rows = []
    for strategy in ["risk_based", "random"]:
        n_iter = N_RANDOM_ITER if strategy == "random" else 1
        for k in K_SUPPORT:
            iter_rows = []
            for iteration in range(n_iter):
                event_rows = []
                selected_parts = []
                for event_id, part in eval_df.groupby("event_id", sort=False):
                    k_actual = min(k, len(part))
                    if strategy == "risk_based":
                        selected = part.sort_values("risk_score", ascending=False).head(k_actual)
                    else:
                        seed = 100000 * iteration + int(event_id) + k
                        selected = part.sample(n=k_actual, random_state=seed)

                    n_delayed_total = int(part["delayed"].sum())
                    n_delayed_selected = int(selected["delayed"].sum())
                    overall_rate = part["delayed"].mean()
                    precision = n_delayed_selected / k_actual if k_actual else 0
                    recall = n_delayed_selected / n_delayed_total if n_delayed_total else np.nan
                    lift = precision / overall_rate if overall_rate else np.nan
                    event_rows.append(
                        {
                            "recall": recall,
                            "precision": precision,
                            "lift": lift,
                            "has_delayed": n_delayed_total > 0,
                        }
                    )
                    selected_parts.append(selected)

                event_df = pd.DataFrame(event_rows)
                selected_all = pd.concat(selected_parts, ignore_index=True)
                iter_rows.append(
                    {
                        "mean_recall_k": event_df["recall"].mean(skipna=True),
                        "mean_precision_k": event_df["precision"].mean(skipna=True),
                        "mean_lift_k": event_df["lift"].mean(skipna=True),
                        "vulnerable_pop_covered": selected_all["vulnerable_pop_proxy"].sum(),
                        "events_with_delayed": int(event_df["has_delayed"].sum()),
                    }
                )

            iter_df = pd.DataFrame(iter_rows)
            rows.append(
                {
                    "strategy": strategy,
                    "k_support": k,
                    "delayed_capture_rate": round(iter_df["mean_recall_k"].mean(), 4),
                    "benefit_index_per_resource": round(iter_df["mean_precision_k"].mean(), 4),
                    "vulnerable_pop_covered": round(iter_df["vulnerable_pop_covered"].mean(), 2),
                    "mean_recall_k": round(iter_df["mean_recall_k"].mean(), 4),
                    "mean_precision_k": round(iter_df["mean_precision_k"].mean(), 4),
                    "mean_lift_k": round(iter_df["mean_lift_k"].mean(), 2),
                    "random_recall_sd": round(iter_df["mean_recall_k"].std(ddof=0), 4)
                    if strategy == "random"
                    else 0.0,
                    "random_lift_sd": round(iter_df["mean_lift_k"].std(ddof=0), 4)
                    if strategy == "random"
                    else 0.0,
                    "events_with_delayed": int(iter_df["events_with_delayed"].iloc[0]),
                    "n_random_iter": n_iter,
                }
            )

    result = pd.DataFrame(rows).sort_values(["strategy", "k_support"])
    result["marginal_gain"] = result.groupby("strategy")["delayed_capture_rate"].diff().fillna(
        result["delayed_capture_rate"]
    )

    preferred = [
        "strategy",
        "k_support",
        "delayed_capture_rate",
        "benefit_index_per_resource",
        "vulnerable_pop_covered",
        "marginal_gain",
        "mean_recall_k",
        "mean_precision_k",
        "mean_lift_k",
        "random_recall_sd",
        "random_lift_sd",
        "events_with_delayed",
        "n_random_iter",
    ]
    rest = [c for c in result.columns if c not in preferred]
    result[preferred + rest].to_csv(
        OUT / "capacity_scenario_results.csv", index=False, encoding="utf-8-sig"
    )
    result[preferred + rest].to_csv(
        REPORT / "capacity_scenario_results.csv", index=False, encoding="utf-8-sig"
    )
    build_capacity_chart(result)


def build_capacity_chart(result: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    styles = {
        "risk_based": ("#cc5533", "Risk-based"),
        "random": ("#5577aa", "Random mean"),
    }
    for strategy, (color, label) in styles.items():
        sub = result[result["strategy"].eq(strategy)]
        axes[0].plot(sub["k_support"], sub["mean_recall_k"], marker="o", color=color, label=label)
        axes[1].plot(sub["k_support"], sub["mean_lift_k"], marker="o", color=color, label=label)
        if strategy == "random":
            lo = (sub["mean_recall_k"] - 1.96 * sub["random_recall_sd"]).clip(lower=0)
            hi = sub["mean_recall_k"] + 1.96 * sub["random_recall_sd"]
            axes[0].fill_between(sub["k_support"], lo, hi, color=color, alpha=0.15)

    axes[0].set_title("Delayed Capture Rate by Capacity")
    axes[0].set_xlabel("Supported districts per event")
    axes[0].set_ylabel("Delayed capture rate")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    axes[1].set_title("Lift by Capacity")
    axes[1].set_xlabel("Supported districts per event")
    axes[1].set_ylabel("Lift")
    axes[1].axhline(1.0, color="gray", linestyle="--", linewidth=0.8)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(OUT / "capacity_scenario_chart.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPORT / "capacity_scenario_chart.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def build_flood_trace_chart() -> None:
    df = pd.read_csv(require_file(OUT / "flood_trace_overlap_validation.csv"))
    hi = df.loc[df["risk_group"].eq("위험 상위 20%")].iloc[0]
    lo = df.loc[df["risk_group"].eq("위험 하위 20%")].iloc[0]
    if hi["pct_flood_top25"] > lo["pct_flood_top25"]:
        interpretation = (
            "위험 상위 동이 과거 침수흔적 상위 지역과 더 많이 겹쳐, "
            "생활활동 회복지연 위험이 물리적 침수취약성과 같은 방향임을 보조적으로 시사한다."
        )
    else:
        interpretation = (
            "위험 상위 동은 과거 침수흔적 면적 상위 지역과 덜 겹친다. "
            "따라서 본 모델의 회복지연 위험은 침수면적 자체보다 생활인구 노출, 고령층, "
            "서비스·인프라 병목 등 사후 운영 취약성을 더 강하게 반영하는 것으로 해석한다."
        )
    pd.DataFrame(
        [
            {
                "high20_pct_flood_top25": round(hi["pct_flood_top25"], 4),
                "low20_pct_flood_top25": round(lo["pct_flood_top25"], 4),
                "interpretation": interpretation,
            }
        ]
    ).to_csv(OUT / "flood_trace_overlap_interpretation.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {
                "high20_pct_flood_top25": round(hi["pct_flood_top25"], 4),
                "low20_pct_flood_top25": round(lo["pct_flood_top25"], 4),
                "interpretation": interpretation,
            }
        ]
    ).to_csv(
        REPORT / "flood_trace_overlap_interpretation.csv", index=False, encoding="utf-8-sig"
    )
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    x = range(len(df))
    label_map = {
        "위험 상위 20%": "High risk 20%",
        "중간 60%": "Middle 60%",
        "위험 하위 20%": "Low risk 20%",
    }
    xlabels = [label_map.get(v, str(v)) for v in df["risk_group"]]
    ax1.bar(x, df["pct_flood_top25"] * 100, color="#5577aa", label="Flood top25 overlap (%)")
    ax1.set_ylabel("Flood top25 overlap (%)")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(xlabels, rotation=0)
    ax2 = ax1.twinx()
    ax2.plot(x, df["mean_delayed_rate"] * 100, color="#cc5533", marker="o", label="Delayed rate (%)")
    ax2.set_ylabel("Delayed rate (%)")
    ax1.set_title("Flood Trace Overlap vs Recovery Delay")
    fig.tight_layout()
    fig.savefig(OUT / "flood_trace_overlap_report.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPORT / "flood_trace_overlap_report.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def copy_front_assets() -> None:
    copies = [
        (OUT / "playbook_table.csv", REPORT / "playbook_table.csv"),
        (OUT / "capacity_scenario_chart.png", REPORT / "capacity_scenario_chart.png"),
        (OUT / "capacity_scenario_results.csv", REPORT / "capacity_scenario_results.csv"),
        (OUT / "ranking_metrics.csv", REPORT / "ranking_metrics.csv"),
        (OUT / "topk_sensitivity.csv", REPORT / "topk_sensitivity.csv"),
        (OUT / "top20_lift_by_event.csv", REPORT / "top20_lift_by_event.csv"),
        (OUT / "model_timing_comparison.csv", REPORT / "model_timing_comparison.csv"),
        (OUT / "flood_trace_overlap_validation.csv", REPORT / "flood_trace_overlap_validation.csv"),
        (
            OUT / "flood_trace_overlap_interpretation.csv",
            REPORT / "flood_trace_overlap_interpretation.csv",
        ),
    ]
    for src, dst in copies:
        if src.exists():
            dst.write_bytes(src.read_bytes())


def main() -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    build_target_sensitivity()
    build_ranking_support_tables()
    enrich_priority_tables()
    update_core_performance()
    enrich_capacity_scenarios()
    build_flood_trace_chart()
    copy_front_assets()


if __name__ == "__main__":
    main()
