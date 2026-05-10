from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCX = next(path for path in ROOT.glob("*.docx") if "backup" not in path.name)
BACKUP = ROOT / "analysis_report_final_review_backup.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W)


def qn(tag: str) -> str:
    return f"{{{W}}}{tag}"


def text_of(element: ET.Element) -> str:
    return "".join((t.text or "") for t in element.findall(".//" + qn("t"))).strip()


def make_paragraph(text: str, *, bold: bool = False, spacing_after: int | None = None) -> ET.Element:
    paragraph = ET.Element(qn("p"))
    properties = ET.SubElement(paragraph, qn("pPr"))
    if spacing_after is not None:
        ET.SubElement(properties, qn("spacing"), {qn("after"): str(spacing_after)})
    run = ET.SubElement(paragraph, qn("r"))
    if bold:
        run_properties = ET.SubElement(run, qn("rPr"))
        ET.SubElement(run_properties, qn("b"))
    text_node = ET.SubElement(run, qn("t"))
    text_node.text = text
    return paragraph


def remove_performance_table_empty_rows(root: ET.Element) -> int:
    removed = 0
    for table in root.findall(".//" + qn("tbl")):
        direct_rows = table.findall("./" + qn("tr"))
        is_performance_table = False
        for row in direct_rows:
            first_cell = row.find("./" + qn("tc"))
            if first_cell is not None and text_of(first_cell) == "2025 holdout R2":
                is_performance_table = True
                break
        if not is_performance_table:
            continue
        for row in direct_rows:
            cell_texts = [text_of(cell) for cell in row.findall("./" + qn("tc"))]
            if cell_texts and all(not text for text in cell_texts):
                table.remove(row)
                removed += 1
    return removed


def add_conclusion(body: ET.Element) -> bool:
    existing = [text_of(paragraph) for paragraph in body.findall("./" + qn("p"))]
    if "결론" in existing:
        return False

    conclusion_title = make_paragraph("결론", bold=True, spacing_after=120)
    conclusion_body = make_paragraph(
        "본 분석은 호우 이후 제한된 복구자원을 우선 투입할 행정동을 선별하기 위한 "
        "랭킹 기반 운영 모델이다. 위험 상위 20% 행정동은 전체 회복지연 동의 "
        "82.2%를 포착했고, 무작위 선별 대비 4.07배 높은 위험 농축도를 보였다. "
        "따라서 본 모델은 단순 침수위험 정보만으로 설명하기 어려운 사후 회복지연 "
        "취약성을 보완적으로 제시하며, 서울시와 자치구의 D+1 복구자원 배치 "
        "의사결정에 활용될 수 있다.",
        spacing_after=160,
    )

    children = list(body)
    insert_at = len(children)
    for index, child in enumerate(children):
        if child.tag == qn("sectPr"):
            insert_at = index
            break
    body.insert(insert_at, conclusion_title)
    body.insert(insert_at + 1, conclusion_body)
    return True


def main() -> None:
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)

    source = BACKUP if BACKUP.exists() else DOCX
    with zipfile.ZipFile(source, "r") as zin:
        entries = {info.filename: zin.read(info.filename) for info in zin.infolist()}

    root = ET.fromstring(entries["word/document.xml"])
    body = root.find(".//" + qn("body"))
    if body is None:
        raise RuntimeError("word/document.xml body not found")

    removed_rows = remove_performance_table_empty_rows(root)
    conclusion_added = add_conclusion(body)

    entries["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    temp = DOCX.with_suffix(".tmp.docx")
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)

    try:
        shutil.move(str(temp), str(DOCX))
    except PermissionError:
        fallback = ROOT / "analysis_report_final_revised.docx"
        shutil.move(str(temp), str(fallback))
        print(f"locked_original={DOCX}")
        print(f"fallback={fallback}")
        return

    print(f"updated={DOCX}")
    print(f"backup={BACKUP}")
    print(f"removed_empty_rows={removed_rows}")
    print(f"conclusion_added={conclusion_added}")


if __name__ == "__main__":
    main()
