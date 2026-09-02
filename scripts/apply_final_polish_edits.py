from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCX = next(path for path in ROOT.glob("*.docx") if "backup" not in path.name)
BACKUP = ROOT / "analysis_report_final_polish_backup.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W)


def qn(tag: str) -> str:
    return f"{{{W}}}{tag}"


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join((node.text or "") for node in paragraph.findall(".//" + qn("t")))


def set_paragraph_text(paragraph: ET.Element, text: str) -> None:
    nodes = paragraph.findall(".//" + qn("t"))
    if not nodes:
        run = ET.SubElement(paragraph, qn("r"))
        node = ET.SubElement(run, qn("t"))
        node.text = text
        return
    nodes[0].text = text
    for node in nodes[1:]:
        node.text = ""


def replace_text(root: ET.Element) -> int:
    replacements = {
        "기존 회복지연 모델은 Top20% 기준 Recall 82.2%, Lift 4.07배로 Rainfall-only와 Flood-only 단일 기준보다 실제 회복지연 동을 훨씬 효과적으로 포착하였다.": (
            "본 회복지연 모델은 Top-20% 기준 Recall 82.2%, Lift 4.07배로 Rainfall-only와 Flood-only 단일 기준보다 실제 회복지연 동을 더 효과적으로 포착하였다."
        ),
        "2. 정밀 B/C 분석": "2. 가정 기반 B/C 시나리오",
        "2025 holdout R2": "2025 holdout R²",
        "LOEO R2": "LOEO R²",
        "다만 LOEO R2가 낮기 때문에": "다만 LOEO R²가 낮기 때문에",
        "R2는 회복률 수치 자체를": "R²는 회복률 수치 자체를",
        "따라서 R2는 보조 지표로": "따라서 R²는 보조 지표로",
    }
    changed = 0
    for paragraph in root.findall(".//" + qn("p")):
        text = paragraph_text(paragraph)
        new_text = text
        for old, new in replacements.items():
            new_text = new_text.replace(old, new)
        if new_text != text:
            set_paragraph_text(paragraph, new_text)
            changed += 1
    return changed


def remove_trailing_duplicate_conclusion(root: ET.Element) -> bool:
    body = root.find(".//" + qn("body"))
    if body is None:
        return False
    children = list(body)
    for index, child in enumerate(children):
        if child.tag != qn("p") or paragraph_text(child).strip() != "결론":
            continue
        next_child = children[index + 1] if index + 1 < len(children) else None
        next_text = paragraph_text(next_child).strip() if next_child is not None else ""
        if next_text.startswith("본 분석은 호우 이후 생활인구 기반 회복지연 위험을 활용해"):
            body.remove(child)
            body.remove(next_child)
            return True
    return False


def main() -> None:
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)

    with zipfile.ZipFile(DOCX, "r") as zin:
        entries = {info.filename: zin.read(info.filename) for info in zin.infolist()}

    root = ET.fromstring(entries["word/document.xml"])
    changed = replace_text(root)
    removed_duplicate_conclusion = remove_trailing_duplicate_conclusion(root)

    entries["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    temp = DOCX.with_suffix(".tmp.docx")
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)
    shutil.move(str(temp), str(DOCX))

    print(f"updated={DOCX}")
    print(f"backup={BACKUP}")
    print(f"changed_paragraphs={changed}")
    print(f"removed_duplicate_conclusion={removed_duplicate_conclusion}")


if __name__ == "__main__":
    main()
