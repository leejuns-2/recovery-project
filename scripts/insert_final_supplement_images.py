from pathlib import Path
import re
import shutil
import struct
import zipfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "분석_보고서_최종보완본.docx"
BACKUP = ROOT / "analysis_report_final_before_images_backup.docx"
OUTPUT = ROOT / "analysis_report_final_with_images.docx"
FIG_DIR = ROOT / "submission" / "final_supplement_assets" / "figures"

FIGURES = [
    {
        "file": FIG_DIR / "baseline_rainfall_flood_comparison.png",
        "title": "그림 1. 기존 모델과 단일 기준 baseline 비교",
        "desc": (
            "기존 회복지연 모델은 Top-20% 기준 Recall 82.2%, Lift 4.07배로 "
            "Rainfall-only와 Flood-only 단일 기준보다 실제 회복지연 동을 훨씬 효과적으로 포착하였다."
        ),
        "width_in": 6.2,
        "page_break_before": False,
    },
    {
        "file": FIG_DIR / "random_topk_validation.png",
        "title": "그림 2. Random Top-K 반복검증 결과",
        "desc": (
            "무작위 Top-20% 반복선택의 평균 Recall은 약 20.2%, Lift는 약 1.00배였으나, "
            "기존 모델은 Recall 82.2%, Lift 4.07배로 무작위 분포를 크게 벗어났다."
        ),
        "width_in": 6.2,
        "page_break_before": False,
    },
    {
        "file": FIG_DIR / "map_flood_trace_top25.png",
        "title": "그림 3. 침수흔적 면적 Top25% 행정동",
        "desc": "과거 침수흔적 면적 비율이 높은 행정동을 표시한 지도이며, 물리적 침수 이력이 집중된 공간 분포를 보여준다.",
        "width_in": 4.9,
        "page_break_before": True,
    },
    {
        "file": FIG_DIR / "map_recovery_delay_risk_top20.png",
        "title": "그림 4. 회복지연 위험 Top-20% 행정동",
        "desc": (
            "모델이 산출한 회복지연 위험 상위 행정동은 침수흔적 Top25%와 8개 동만 겹쳐, "
            "단순 침수면적이 아닌 생활인구 노출·고령층·서비스 및 인프라 병목 등 "
            "사후 회복 취약성을 별도로 포착함을 보여준다."
        ),
        "width_in": 4.9,
        "page_break_before": False,
    },
]

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"

for prefix, uri in [
    ("w", W),
    ("r", R),
    ("wp", WP),
    ("a", A),
    ("pic", PIC),
    ("rel", REL),
    ("ct", CT),
]:
    ET.register_namespace(prefix, uri)


def qn(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Not a PNG: {path}")
        f.read(4)
        if f.read(4) != b"IHDR":
            raise ValueError(f"Invalid PNG: {path}")
        return struct.unpack(">II", f.read(8))


def make_p(
    text: str = "",
    *,
    bold: bool = False,
    align: str | None = None,
    spacing_after: int | None = None,
) -> ET.Element:
    p = ET.Element(qn(W, "p"))
    p_pr = ET.SubElement(p, qn(W, "pPr"))
    if align:
        ET.SubElement(p_pr, qn(W, "jc"), {qn(W, "val"): align})
    if spacing_after is not None:
        ET.SubElement(p_pr, qn(W, "spacing"), {qn(W, "after"): str(spacing_after)})
    if text:
        r = ET.SubElement(p, qn(W, "r"))
        if bold:
            r_pr = ET.SubElement(r, qn(W, "rPr"))
            ET.SubElement(r_pr, qn(W, "b"))
        t = ET.SubElement(r, qn(W, "t"))
        t.text = text
    return p


def make_page_break_p() -> ET.Element:
    p = ET.Element(qn(W, "p"))
    r = ET.SubElement(p, qn(W, "r"))
    ET.SubElement(r, qn(W, "br"), {qn(W, "type"): "page"})
    return p


def make_image_p(
    rel_id: str,
    name: str,
    width_px: int,
    height_px: int,
    width_in: float,
    docpr_id: int,
) -> ET.Element:
    emu_per_in = 914400
    cx = int(width_in * emu_per_in)
    cy = int(cx * height_px / width_px)

    p = ET.Element(qn(W, "p"))
    p_pr = ET.SubElement(p, qn(W, "pPr"))
    ET.SubElement(p_pr, qn(W, "jc"), {qn(W, "val"): "center"})
    r = ET.SubElement(p, qn(W, "r"))
    drawing = ET.SubElement(r, qn(W, "drawing"))
    inline = ET.SubElement(
        drawing,
        qn(WP, "inline"),
        {"distT": "0", "distB": "0", "distL": "0", "distR": "0"},
    )
    ET.SubElement(inline, qn(WP, "extent"), {"cx": str(cx), "cy": str(cy)})
    ET.SubElement(
        inline,
        qn(WP, "effectExtent"),
        {"l": "0", "t": "0", "r": "0", "b": "0"},
    )
    ET.SubElement(inline, qn(WP, "docPr"), {"id": str(docpr_id), "name": name})
    ET.SubElement(inline, qn(WP, "cNvGraphicFramePr"))
    graphic = ET.SubElement(inline, qn(A, "graphic"))
    graphic_data = ET.SubElement(graphic, qn(A, "graphicData"), {"uri": PIC})
    pic = ET.SubElement(graphic_data, qn(PIC, "pic"))
    nv_pic_pr = ET.SubElement(pic, qn(PIC, "nvPicPr"))
    ET.SubElement(nv_pic_pr, qn(PIC, "cNvPr"), {"id": "0", "name": name})
    ET.SubElement(nv_pic_pr, qn(PIC, "cNvPicPr"))
    blip_fill = ET.SubElement(pic, qn(PIC, "blipFill"))
    ET.SubElement(blip_fill, qn(A, "blip"), {qn(R, "embed"): rel_id})
    stretch = ET.SubElement(blip_fill, qn(A, "stretch"))
    ET.SubElement(stretch, qn(A, "fillRect"))
    sp_pr = ET.SubElement(pic, qn(PIC, "spPr"))
    xfrm = ET.SubElement(sp_pr, qn(A, "xfrm"))
    ET.SubElement(xfrm, qn(A, "off"), {"x": "0", "y": "0"})
    ET.SubElement(xfrm, qn(A, "ext"), {"cx": str(cx), "cy": str(cy)})
    prst_geom = ET.SubElement(sp_pr, qn(A, "prstGeom"), {"prst": "rect"})
    ET.SubElement(prst_geom, qn(A, "avLst"))
    return p


def next_rid(rels_root: ET.Element) -> str:
    used = {rel.attrib.get("Id") for rel in rels_root.findall(qn(REL, "Relationship"))}
    max_id = 0
    for rid in used:
        match = re.match(r"rId(\d+)$", rid or "")
        if match:
            max_id = max(max_id, int(match.group(1)))
    while True:
        max_id += 1
        rid = f"rId{max_id}"
        if rid not in used:
            return rid


def read_docx_entries(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path, "r") as zin:
        return {info.filename: zin.read(info.filename) for info in zin.infolist()}


def main() -> None:
    if not ORIGINAL.exists():
        raise FileNotFoundError(ORIGINAL)
    if not BACKUP.exists():
        shutil.copy2(ORIGINAL, BACKUP)
    for figure in FIGURES:
        if not figure["file"].exists():
            raise FileNotFoundError(figure["file"])

    entries = read_docx_entries(BACKUP)
    root = ET.fromstring(entries["word/document.xml"])
    body = root.find(qn(W, "body"))
    rels_root = ET.fromstring(entries["word/_rels/document.xml.rels"])
    content_root = ET.fromstring(entries["[Content_Types].xml"])
    media_names = {name for name in entries if name.startswith("word/media/")}

    insert_blocks = [
        make_page_break_p(),
        make_p("Ⅵ. 최종 보완 검증자료", bold=True, spacing_after=120),
        make_p(
            "아래 보완 그림은 기존 모델이 단일 기준 baseline 및 무작위 Top-K보다 "
            "회복지연 동을 안정적으로 선별하며, 침수흔적 위험과 회복지연 위험이 "
            "공간적으로 구분됨을 보여준다.",
            spacing_after=180,
        ),
    ]

    for idx, figure in enumerate(FIGURES, start=1):
        if figure["page_break_before"]:
            insert_blocks.append(make_page_break_p())
        image_name = f"final_supplement_{idx}_{figure['file'].name}"
        target = f"word/media/{image_name}"
        counter = 1
        while target in media_names:
            image_name = f"final_supplement_{idx}_{counter}_{figure['file'].name}"
            target = f"word/media/{image_name}"
            counter += 1
        media_names.add(target)
        entries[target] = figure["file"].read_bytes()

        rid = next_rid(rels_root)
        ET.SubElement(
            rels_root,
            qn(REL, "Relationship"),
            {
                "Id": rid,
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                "Target": f"media/{image_name}",
            },
        )

        width_px, height_px = png_size(figure["file"])
        insert_blocks.append(make_p(figure["title"], bold=True, spacing_after=80))
        insert_blocks.append(
            make_image_p(
                rid,
                image_name,
                width_px,
                height_px,
                figure["width_in"],
                1000 + idx,
            )
        )
        insert_blocks.append(make_p(figure["desc"], spacing_after=220))

    if not any(
        child.tag == qn(CT, "Default") and child.attrib.get("Extension") == "png"
        for child in content_root
    ):
        ET.SubElement(
            content_root,
            qn(CT, "Default"),
            {"Extension": "png", "ContentType": "image/png"},
        )

    children = list(body)
    insert_at = None
    for i, child in enumerate(children):
        text = "".join((t.text or "") for t in child.findall(".//" + qn(W, "t"))).strip()
        if child.tag == qn(W, "p") and text == "결론":
            insert_at = i
            break
    if insert_at is None:
        insert_at = len(children) - 1

    for offset, block in enumerate(insert_blocks):
        body.insert(insert_at + offset, block)

    entries["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    entries["word/_rels/document.xml.rels"] = ET.tostring(
        rels_root, encoding="utf-8", xml_declaration=True
    )
    entries["[Content_Types].xml"] = ET.tostring(
        content_root, encoding="utf-8", xml_declaration=True
    )

    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)

    try:
        shutil.copy2(OUTPUT, ORIGINAL)
        print(f"updated_original={ORIGINAL}")
    except PermissionError:
        print(f"updated_original=failed_permission_locked:{ORIGINAL}")
    print(f"output={OUTPUT}")
    print(f"backup={BACKUP}")


if __name__ == "__main__":
    main()
