from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
REPORT = OUT / "report_assets"
SUBMISSION = ROOT / "submission" / "assets"

TEMPLATE = DATA / "external" / "external_validation_template.csv"
PREDICTIONS = OUT / "loeo_predictions.csv"
SUMMARY_OUT = OUT / "external_validation_summary.csv"
BY_EVENT_OUT = OUT / "external_validation_by_event.csv"

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


def select_event_top_bottom(df: pd.DataFrame, pct: float = 0.2) -> pd.DataFrame:
    parts = []
    for _, part in df.groupby("event_id", sort=False):
        k = max(1, int(len(part) * pct + 0.999999))
        ordered = part.sort_values("risk_score", ascending=False).copy()
        ordered["risk_group_ext"] = "middle_60"
        ordered.iloc[:k, ordered.columns.get_loc("risk_group_ext")] = "high_20"
        ordered.iloc[-k:, ordered.columns.get_loc("risk_group_ext")] = "low_20"
        parts.append(ordered)
    return pd.concat(parts, ignore_index=True)


def load_priority_scores() -> pd.DataFrame:
    priority = pd.read_csv(PREDICTIONS, dtype={"adm_cd": str})
    priority["gu_nm"] = priority["adm_cd"].astype(str).str[:5].map(GU_MAP).fillna("미상")
    if "risk_score" not in priority.columns:
        priority["risk_score"] = 1 - pd.to_numeric(priority["y_pred"], errors="coerce")
    return priority


def make_template() -> None:
    DATA.joinpath("external").mkdir(parents=True, exist_ok=True)
    if TEMPLATE.exists():
        existing = pd.read_csv(TEMPLATE)
        metric_cols = [
            "complaint_count_d0_d7",
            "waste_ton_d0_d7",
            "field_check_count_d0_d7",
            "damage_report_count_d0_d7",
        ]
        has_metrics = any(
            col in existing.columns and pd.to_numeric(existing[col], errors="coerce").notna().any()
            for col in metric_cols
        )
        if has_metrics:
            return
    template = pd.DataFrame(
        [
            {
                "event_id": 6,
                "event_date": "2023-07-13",
                "adm_cd": "11020520",
                "adm_nm": "소공동",
                "gu_nm": "중구",
                "complaint_count_d0_d7": "",
                "waste_ton_d0_d7": "",
                "field_check_count_d0_d7": "",
                "damage_report_count_d0_d7": "",
                "source_note": "대표 사례 입력 예시입니다. 실제 외부 실적 데이터로 교체하세요.",
            },
            {
                "event_id": 17,
                "event_date": "2024-07-18",
                "adm_cd": "11020520",
                "adm_nm": "소공동",
                "gu_nm": "중구",
                "complaint_count_d0_d7": "",
                "waste_ton_d0_d7": "",
                "field_check_count_d0_d7": "",
                "damage_report_count_d0_d7": "",
                "source_note": "대표 사례 입력 예시입니다. 실제 외부 실적 데이터로 교체하세요.",
            },
            {
                "event_id": 34,
                "event_date": "2025-09-04",
                "adm_cd": "11020520",
                "adm_nm": "소공동",
                "gu_nm": "중구",
                "complaint_count_d0_d7": "",
                "waste_ton_d0_d7": "",
                "field_check_count_d0_d7": "",
                "damage_report_count_d0_d7": "",
                "source_note": "대표 사례 입력 예시입니다. 실제 외부 실적 데이터로 교체하세요.",
            }
        ]
    )
    template.to_csv(TEMPLATE, index=False, encoding="utf-8-sig")


def load_external(path: Path) -> tuple[pd.DataFrame, list[str], str] | tuple[None, list[str], str]:
    if not path.exists():
        return None, [], "not_available"
    df = pd.read_csv(path, dtype={"adm_cd": str}).fillna("")
    metric_cols = [
        "complaint_count_d0_d7",
        "waste_ton_d0_d7",
        "field_check_count_d0_d7",
        "damage_report_count_d0_d7",
    ]
    for col in metric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    usable_metrics = [col for col in metric_cols if col in df.columns and df[col].notna().any()]
    if not usable_metrics:
        return None, [], "not_available"

    has_adm_cd = "adm_cd" in df.columns and df["adm_cd"].astype(str).str.strip().ne("").any()
    has_gu = "gu_nm" in df.columns and df["gu_nm"].astype(str).str.strip().ne("").any()
    if has_adm_cd:
        return df[["event_id", "adm_cd"] + usable_metrics].copy(), usable_metrics, "adm_level"
    if has_gu:
        return df[["event_id", "gu_nm"] + usable_metrics].copy(), usable_metrics, "gu_level_proxy"
    return None, [], "not_available"


def aggregate_gu_priority(priority: pd.DataFrame) -> pd.DataFrame:
    gu = (
        priority.groupby(["event_id", "gu_nm"], as_index=False)
        .agg(
            risk_score=("risk_score", "max"),
            n_districts=("adm_cd", "count"),
            mean_risk_score=("risk_score", "mean"),
        )
    )
    return gu


def build_validation() -> None:
    priority = load_priority_scores()
    external, metric_cols, scope = load_external(TEMPLATE)
    REPORT.mkdir(parents=True, exist_ok=True)
    SUBMISSION.mkdir(parents=True, exist_ok=True)

    if external is None:
        status = pd.DataFrame(
            [
                {
                    "status": "not_available",
                    "message": (
                        "민원·폐기물·현장점검 외부 실적 데이터가 아직 투입되지 않았습니다. "
                        "data/external/external_validation_template.csv 형식으로 데이터를 넣으면 "
                        "위험 Top-20%/Bottom-20% 외부 검증표가 생성됩니다."
                    ),
                    "template_path": "data/external/external_validation_template.csv",
                }
            ]
        )
        status.to_csv(SUMMARY_OUT, index=False, encoding="utf-8-sig")
        status.to_csv(REPORT / SUMMARY_OUT.name, index=False, encoding="utf-8-sig")
        status.to_csv(SUBMISSION / SUMMARY_OUT.name, index=False, encoding="utf-8-sig")
        return

    if scope == "gu_level_proxy":
        priority = aggregate_gu_priority(priority)
        priority = select_event_top_bottom(priority)
        merged = priority.merge(external, on=["event_id", "gu_nm"], how="inner")
        group_key = "gu_nm"
    else:
        priority = select_event_top_bottom(priority)
        merged = priority.merge(external, on=["event_id", "adm_cd"], how="inner")
        group_key = "adm_cd"

    rows = []
    by_event_rows = []
    for metric in metric_cols:
        grouped = (
            merged.groupby("risk_group_ext", as_index=False)
            .agg(n=(group_key, "count"), metric_mean=(metric, "mean"), metric_sum=(metric, "sum"))
        )
        grouped["metric"] = metric
        grouped["validation_scope"] = scope
        rows.append(grouped)

        event_grouped = (
            merged.groupby(["event_id", "risk_group_ext"], as_index=False)
            .agg(n=(group_key, "count"), metric_mean=(metric, "mean"), metric_sum=(metric, "sum"))
        )
        event_grouped["metric"] = metric
        event_grouped["validation_scope"] = scope
        by_event_rows.append(event_grouped)

    summary = pd.concat(rows, ignore_index=True)
    by_event = pd.concat(by_event_rows, ignore_index=True)
    summary.to_csv(SUMMARY_OUT, index=False, encoding="utf-8-sig")
    by_event.to_csv(BY_EVENT_OUT, index=False, encoding="utf-8-sig")
    summary.to_csv(REPORT / SUMMARY_OUT.name, index=False, encoding="utf-8-sig")
    by_event.to_csv(REPORT / BY_EVENT_OUT.name, index=False, encoding="utf-8-sig")
    summary.to_csv(SUBMISSION / SUMMARY_OUT.name, index=False, encoding="utf-8-sig")
    by_event.to_csv(SUBMISSION / BY_EVENT_OUT.name, index=False, encoding="utf-8-sig")


def main() -> None:
    make_template()
    build_validation()


if __name__ == "__main__":
    main()
