from pathlib import Path
import shutil

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
PACKAGE = ROOT / "submission" / "final_supplement_assets"
FIGURES = PACKAGE / "figures"
TABLES = PACKAGE / "tables"

TOP_PCT = 0.20
FLOOD_TOP_PCT = 0.25
N_RANDOM_ITER = 10_000
N_BOOTSTRAP = 5_000
SEED = 20260508


def setup() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    font_path = Path("C:/Windows/Fonts/malgun.ttf")
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams["font.family"] = "Malgun Gothic"
    plt.rcParams["axes.unicode_minus"] = False


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return path


def load_evaluation_frame() -> pd.DataFrame:
    preds = pd.read_csv(require(OUTPUTS / "loeo_predictions.csv"), dtype={"adm_cd": str})
    local = pd.read_parquet(require(DATA / "panel_event_district_local_rain.parquet"))
    local["adm_cd"] = local["adm_cd"].astype(str)
    keep_cols = [
        "event_id",
        "adm_cd",
        "local_daily_rain",
        "local_max_12h_rain",
        "local_max_3h_rain",
        "flood_area_ratio",
        "sewage_density_m_per_km2",
        "elderly_ratio",
        "baseline_pop",
    ]
    df = preds.merge(local[keep_cols], on=["event_id", "adm_cd"], how="left")
    df["rainfall_only_score"] = (
        df["local_daily_rain"].fillna(0)
        + df["local_max_12h_rain"].fillna(0) * 0.001
        + df["local_max_3h_rain"].fillna(0) * 0.000001
    )
    df["flood_only_score"] = df["flood_area_ratio"].fillna(0)
    df["model_score"] = df["risk_score"]
    return df


def add_top_flag(
    df: pd.DataFrame,
    score_col: str,
    flag_col: str,
    top_pct: float = TOP_PCT,
) -> pd.DataFrame:
    out = df.copy()
    out[flag_col] = False
    for _, part in out.groupby("event_id", sort=False):
        k = max(1, int(np.ceil(len(part) * top_pct)))
        ordered = part.sort_values([score_col, "adm_cd"], ascending=[False, True])
        out.loc[ordered.head(k).index, flag_col] = True
    return out


def metric_from_flag(df: pd.DataFrame, flag_col: str) -> dict:
    selected = df[df[flag_col]]
    overall_rate = df["delayed"].mean()
    precision = selected["delayed"].mean()
    recall = selected["delayed"].sum() / df["delayed"].sum()
    return {
        "selected_n": int(selected.shape[0]),
        "overall_delayed_rate": overall_rate,
        "top_delayed_rate": precision,
        "recall": recall,
        "lift": precision / overall_rate if overall_rate else np.nan,
        "mean_recovery_days_selected": selected["recovery_days"].mean(),
    }


def build_baseline_comparison(df: pd.DataFrame) -> pd.DataFrame:
    configs = [
        ("기존 회복지연 모델", "model_score", "top_model"),
        ("Rainfall-only baseline", "rainfall_only_score", "top_rainfall"),
        ("Flood-only baseline", "flood_only_score", "top_flood"),
    ]
    work = df.copy()
    rows = []
    for label, score_col, flag_col in configs:
        work = add_top_flag(work, score_col, flag_col)
        metrics = metric_from_flag(work, flag_col)
        rows.append(
            {
                "method": label,
                "top_definition": "event-wise Top 20%",
                **metrics,
            }
        )
    summary = pd.DataFrame(rows)
    pct_cols = ["overall_delayed_rate", "top_delayed_rate", "recall"]
    for col in pct_cols:
        summary[f"{col}_pct"] = (summary[col] * 100).round(1)
    summary["lift_x"] = summary["lift"].round(2)
    summary["mean_recovery_days_selected"] = summary[
        "mean_recovery_days_selected"
    ].round(2)
    summary.to_csv(TABLES / "baseline_rainfall_flood_comparison.csv", index=False, encoding="utf-8-sig")

    plot_df = summary.set_index("method")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    colors = ["#2458a6", "#d68a2e", "#7a7f87"]

    axes[0].bar(plot_df.index, plot_df["recall"], color=colors)
    axes[0].set_title("Recall@20%")
    axes[0].set_ylim(0, max(0.9, plot_df["recall"].max() * 1.15))
    axes[0].set_ylabel("전체 지연 동 포착률")
    axes[0].tick_params(axis="x", rotation=18)
    for i, value in enumerate(plot_df["recall"]):
        axes[0].text(i, value + 0.02, f"{value * 100:.1f}%", ha="center", fontsize=10)

    axes[1].bar(plot_df.index, plot_df["lift"], color=colors)
    axes[1].set_title("Lift@20%")
    axes[1].set_ylim(0, max(4.6, plot_df["lift"].max() * 1.15))
    axes[1].set_ylabel("전체 평균 대비 위험 농축도")
    axes[1].tick_params(axis="x", rotation=18)
    for i, value in enumerate(plot_df["lift"]):
        axes[1].text(i, value + 0.12, f"{value:.2f}x", ha="center", fontsize=10)

    fig.suptitle("기존 모델 vs 단일 기준 baseline 비교", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "baseline_rainfall_flood_comparison.png", dpi=240, bbox_inches="tight")
    plt.close(fig)
    return work


def compute_metrics_for_subset(subset: pd.DataFrame, selected_col: str) -> dict:
    selected = subset[subset[selected_col]]
    if subset["delayed"].sum() == 0 or selected.empty:
        return {"precision": np.nan, "recall": np.nan, "lift": np.nan}
    precision = selected["delayed"].mean()
    overall = subset["delayed"].mean()
    return {
        "precision": precision,
        "recall": selected["delayed"].sum() / subset["delayed"].sum(),
        "lift": precision / overall if overall else np.nan,
    }


def build_random_and_bootstrap_validation(df: pd.DataFrame) -> None:
    rng = np.random.default_rng(SEED)
    work = add_top_flag(df, "model_score", "top_model")
    observed = compute_metrics_for_subset(work, "top_model")

    event_indices = []
    for event_id, part in work.groupby("event_id", sort=False):
        k = max(1, int(np.ceil(len(part) * TOP_PCT)))
        event_indices.append((event_id, part.index.to_numpy(), k))

    random_rows = []
    delayed = work["delayed"].to_numpy()
    total_delayed = delayed.sum()
    overall = delayed.mean()
    for i in range(N_RANDOM_ITER):
        selected_idx = np.concatenate(
            [rng.choice(indices, size=k, replace=False) for _, indices, k in event_indices]
        )
        selected_delayed = delayed[selected_idx]
        precision = selected_delayed.mean()
        recall = selected_delayed.sum() / total_delayed
        random_rows.append(
            {
                "iteration": i + 1,
                "precision": precision,
                "recall": recall,
                "lift": precision / overall if overall else np.nan,
            }
        )

    random_df = pd.DataFrame(random_rows)
    random_df.to_csv(TABLES / "random_topk_iterations.csv", index=False, encoding="utf-8-sig")

    summary_rows = []
    for metric in ["precision", "recall", "lift"]:
        values = random_df[metric]
        summary_rows.append(
            {
                "metric": metric,
                "model_observed": observed[metric],
                "random_mean": values.mean(),
                "random_p05": values.quantile(0.05),
                "random_p50": values.quantile(0.50),
                "random_p95": values.quantile(0.95),
                "empirical_p_value_random_ge_model": ((values >= observed[metric]).sum() + 1)
                / (N_RANDOM_ITER + 1),
            }
        )
    random_summary = pd.DataFrame(summary_rows)
    random_summary.to_csv(TABLES / "random_topk_validation_summary.csv", index=False, encoding="utf-8-sig")

    event_ids = work["event_id"].drop_duplicates().to_numpy()
    boot_rows = []
    event_parts = {event_id: part for event_id, part in work.groupby("event_id", sort=False)}
    for _ in range(N_BOOTSTRAP):
        sampled = rng.choice(event_ids, size=len(event_ids), replace=True)
        boot_df = pd.concat([event_parts[event_id] for event_id in sampled], ignore_index=True)
        boot_rows.append(compute_metrics_for_subset(boot_df, "top_model"))
    boot = pd.DataFrame(boot_rows)
    ci_rows = []
    for metric in ["precision", "recall", "lift"]:
        ci_rows.append(
            {
                "metric": metric,
                "observed": observed[metric],
                "bootstrap_mean": boot[metric].mean(),
                "ci_2_5": boot[metric].quantile(0.025),
                "ci_97_5": boot[metric].quantile(0.975),
                "n_bootstrap": N_BOOTSTRAP,
            }
        )
    ci = pd.DataFrame(ci_rows)
    ci.to_csv(TABLES / "bootstrap_ci_top20_model.csv", index=False, encoding="utf-8-sig")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, metric, label in [
        (axes[0], "recall", "Recall@20%"),
        (axes[1], "lift", "Lift@20%"),
    ]:
        ax.hist(random_df[metric], bins=45, color="#b8c1cc", edgecolor="white")
        ax.axvline(observed[metric], color="#2458a6", linewidth=2.5, label="기존 모델")
        ax.axvline(random_df[metric].mean(), color="#777777", linestyle="--", linewidth=2, label="무작위 평균")
        ax.set_title(label)
        ax.legend(frameon=False)
    fig.suptitle("Random Top-K 반복검증: 기존 모델 성과는 무작위 선택 분포 밖", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "random_topk_validation.png", dpi=240, bbox_inches="tight")
    plt.close(fig)


def rank_top_by_adm(df: pd.DataFrame, score_col: str, pct: float) -> pd.Series:
    n = max(1, int(np.ceil(len(df) * pct)))
    ordered = df.sort_values([score_col, "adm_cd"], ascending=[False, True])
    top_index = ordered.head(n).index
    return df.index.isin(top_index)


def build_maps(df: pd.DataFrame) -> None:
    geo = gpd.read_file(require(DATA / "seoul_dong.gpkg"))
    geo["adm_cd"] = geo["adm_cd"].astype(str)

    adm = (
        df.groupby(["adm_cd", "adm_nm"], as_index=False)
        .agg(
            mean_risk_score=("risk_score", "mean"),
            mean_delayed_rate=("delayed", "mean"),
            mean_recovery_days=("recovery_days", "mean"),
            flood_area_ratio=("flood_area_ratio", "mean"),
        )
    )
    adm["flood_trace_top25"] = rank_top_by_adm(adm, "flood_area_ratio", FLOOD_TOP_PCT)
    adm["recovery_delay_risk_top20"] = rank_top_by_adm(adm, "mean_risk_score", TOP_PCT)
    adm["both_top_groups"] = adm["flood_trace_top25"] & adm["recovery_delay_risk_top20"]
    adm.to_csv(TABLES / "map_top_group_membership.csv", index=False, encoding="utf-8-sig")

    overlap = pd.DataFrame(
        [
            {
                "flood_trace_top25_n": int(adm["flood_trace_top25"].sum()),
                "recovery_delay_risk_top20_n": int(adm["recovery_delay_risk_top20"].sum()),
                "overlap_n": int(adm["both_top_groups"].sum()),
                "overlap_share_of_recovery_top20": adm["both_top_groups"].sum()
                / adm["recovery_delay_risk_top20"].sum(),
                "message": "침수흔적 상위 지역과 회복지연 위험 상위 지역은 상당 부분 분리되어, 단순 침수면적 기준만으로는 사후 회복지연 취약지를 충분히 설명하기 어렵다.",
            }
        ]
    )
    overlap.to_csv(TABLES / "map_overlap_summary.csv", index=False, encoding="utf-8-sig")

    gdf = geo.merge(adm, on=["adm_cd", "adm_nm"], how="left")

    map_specs = [
        (
            "flood_trace_top25",
            "침수흔적 면적 Top25%",
            "과거 침수흔적 면적 비율 상위 행정동",
            "#d04e3c",
            FIGURES / "map_flood_trace_top25.png",
        ),
        (
            "recovery_delay_risk_top20",
            "회복지연 위험 Top-20%",
            "LOEO 평균 위험점수 기준 우선 대응 행정동",
            "#2458a6",
            FIGURES / "map_recovery_delay_risk_top20.png",
        ),
    ]

    for flag_col, title, subtitle, color, out_path in map_specs:
        fig, ax = plt.subplots(figsize=(7.8, 8.4))
        gdf.plot(ax=ax, color="#edf0f2", edgecolor="#ffffff", linewidth=0.35)
        gdf[gdf[flag_col].fillna(False)].plot(
            ax=ax, color=color, edgecolor="#252525", linewidth=0.45
        )
        ax.set_axis_off()
        ax.set_title(title, fontsize=18, fontweight="bold", pad=13)
        ax.text(
            0.5,
            0.985,
            subtitle,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=10.5,
            color="#444444",
        )
        ax.text(
            0.01,
            0.02,
            "회색: 기타 행정동",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9,
            color="#555555",
        )
        fig.savefig(out_path, dpi=260, bbox_inches="tight")
        plt.close(fig)


def copy_existing_assets() -> None:
    candidates = [
        OUTPUTS / "ranking_metrics.csv",
        OUTPUTS / "top20_lift.csv",
        OUTPUTS / "top20_lift_by_event.csv",
        OUTPUTS / "flood_trace_overlap_validation.csv",
        OUTPUTS / "flood_trace_overlap_interpretation.csv",
        OUTPUTS / "core_performance_summary.csv",
        OUTPUTS / "flood_trace_overlap_report.png",
        OUTPUTS / "report_assets" / "top20_lift_report.png",
    ]
    for src in candidates:
        if not src.exists():
            continue
        dst_dir = FIGURES if src.suffix.lower() == ".png" else TABLES
        shutil.copy2(src, dst_dir / src.name)


def build_readme() -> None:
    text = """# 최종 보완 첨부자료 패키지

## 바로 첨부할 그림
- figures/baseline_rainfall_flood_comparison.png: 기존 모델과 Rainfall-only / Flood-only baseline의 Recall, Lift 비교
- figures/random_topk_validation.png: Random Top-K 10,000회 반복검증 분포와 기존 모델 위치
- figures/map_flood_trace_top25.png: 침수흔적 면적 Top25% 지도
- figures/map_recovery_delay_risk_top20.png: 회복지연 위험 Top-20% 지도

## 표/근거 파일
- tables/baseline_rainfall_flood_comparison.csv
- tables/random_topk_validation_summary.csv
- tables/bootstrap_ci_top20_model.csv
- tables/map_overlap_summary.csv
- tables/map_top_group_membership.csv

## 산출 기준
- 비율 기반 비교는 각 호우 이벤트 안에서 동일한 Top-20% 비율을 선택했다. 고정 K 시나리오와 혼동하지 않는다.
- Rainfall-only는 행정동별 local_daily_rain을 중심으로 local_max_12h_rain, local_max_3h_rain을 tie-break에 사용했다.
- Flood-only는 과거 침수흔적 면적 비율(flood_area_ratio)만 사용했다.
- Bootstrap CI는 이벤트 단위 재표본추출로 계산했다.
"""
    (PACKAGE / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    setup()
    df = load_evaluation_frame()
    scored = build_baseline_comparison(df)
    build_random_and_bootstrap_validation(scored)
    build_maps(scored)
    copy_existing_assets()
    build_readme()
    print(f"Built supplement package: {PACKAGE}")


if __name__ == "__main__":
    main()
