from __future__ import annotations

import copy
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(
    r"C:\Users\JSLEE\Desktop\2026년도 AX 아이디어 경진대회_데이터 분석_자유 분석 부문_ 양식 및 동의서"
    r"\2026년도 AX 아이디어 경진대회_데이터 분석_자유 분석 부문_보고서 양식.docx"
)
OUT = ROOT / "submission" / "docs" / "AX_분석보고서_양식반영_수정본.docx"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
ET.register_namespace("w", W_NS)


def qn(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def text_of(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.findall(".//w:t", NS))


def set_text(block: ET.Element, text: str) -> None:
    runs = block.findall(".//w:r", NS)
    if runs:
        first_run = runs[0]
        rpr = first_run.find("w:rPr", NS)
        for child in list(first_run):
            first_run.remove(child)
        if rpr is not None:
            first_run.append(copy.deepcopy(rpr))
        t = ET.SubElement(first_run, qn("t"))
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = text
        for run in runs[1:]:
            parent = _find_parent(block, run)
            if parent is not None:
                parent.remove(run)
        return

    p = block if block.tag == qn("p") else block.find(".//w:p", NS)
    if p is None:
        return
    r = ET.SubElement(p, qn("r"))
    t = ET.SubElement(r, qn("t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text


def _find_parent(root: ET.Element, child: ET.Element) -> ET.Element | None:
    for node in root.iter():
        for candidate in list(node):
            if candidate is child:
                return node
    return None


def cell_text(cell: ET.Element) -> str:
    return text_of(cell)


def set_cell(cell: ET.Element, text: str) -> None:
    p = cell.find("w:p", NS)
    if p is None:
        p = ET.SubElement(cell, qn("p"))
    set_text(p, text)


def table_rows(table: ET.Element) -> list[list[ET.Element]]:
    return [row.findall("w:tc", NS) for row in table.findall("w:tr", NS)]


def shrink_table_columns(table: ET.Element, keep: list[int]) -> None:
    grid = table.find("w:tblGrid", NS)
    if grid is not None:
        grid_cols = grid.findall("w:gridCol", NS)
        for idx in reversed(range(len(grid_cols))):
            if idx not in keep:
                grid.remove(grid_cols[idx])

    for row in table.findall("w:tr", NS):
        cells = row.findall("w:tc", NS)
        for idx in reversed(range(len(cells))):
            if idx not in keep:
                row.remove(cells[idx])


def replace_first_paragraph(paragraphs: list[ET.Element], old: str, new: str) -> bool:
    for p in paragraphs:
        if text_of(p) == old:
            set_text(p, new)
            return True
    return False


def append_paragraph_after(parent: ET.Element, after: ET.Element, text: str, style_like: ET.Element | None = None) -> ET.Element:
    new_p = copy.deepcopy(style_like if style_like is not None else after)
    for child in list(new_p):
        if child.tag != qn("pPr"):
            new_p.remove(child)
    r = ET.SubElement(new_p, qn("r"))
    t = ET.SubElement(r, qn("t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    children = list(parent)
    parent.insert(children.index(after) + 1, new_p)
    return new_p


def append_paragraph_to_body(body: ET.Element, text: str) -> ET.Element:
    new_p = ET.Element(qn("p"))
    r = ET.SubElement(new_p, qn("r"))
    t = ET.SubElement(r, qn("t"))
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    children = list(body)
    insert_at = len(children)
    if children and children[-1].tag == qn("sectPr"):
        insert_at -= 1
    body.insert(insert_at, new_p)
    return new_p


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(TEMPLATE, "r") as zin:
        xml = zin.read("word/document.xml")
        root = ET.fromstring(xml)
        body = root.find("w:body", NS)
        if body is None:
            raise RuntimeError("word/document.xml body not found")

        paragraphs = root.findall(".//w:p", NS)
        tables = root.findall(".//w:tbl", NS)

        replace_first_paragraph(
            paragraphs,
            "본 과제의 핵심은 회복률 수치를 정밀하게 맞히는 것이 아니라, 제한된 복구자원을 먼저 투입할 후보 동을 선별하는 것이다. 따라서 R2는 보조 지표로 제시하고, Recall/Lift/Precision@K를 중심 성능으로 평가하였다. 위험 상위 20%의 delayed 비율은 16.3%였고, 위험 하위 20%는 0.5%로 나타나 우선점검 후보군 분리 가능성을 확인하였다.",
            "본 과제의 핵심은 회복률 수치를 정밀하게 맞히는 것이 아니라, 제한된 복구자원을 먼저 투입할 후보 동을 선별하는 것이다. 따라서 R2는 보조 지표로 제시하고, Recall/Lift/Precision@K를 중심 성능으로 평가하였다. 가장 중요한 결과는 위험 상위 20% 행정동이 전체 회복지연 동의 82.2%를 포착했다는 점이다. 또한 전체 delayed 비율이 약 4%인 상황에서 위험 상위 20%의 delayed 비율은 16.3%로 나타나, 무작위 선별보다 약 4배 높은 밀도로 위험 동을 모았다. 위험 하위 20%의 delayed 비율은 0.5%에 그쳐, 상위군과 하위군의 실제 회복지연 비율은 약 32배 차이를 보였다.",
        )

        replace_first_paragraph(
            paragraphs,
            "이는 본 모델이 물리적 침수면적 자체보다 생활인구 노출, 상업·업무 밀집, 고령층, 서비스·인프라 병목 등 “호우 이후 운영 취약성”을 포착한다는 의미이다. 즉 침수위험 지도와 별도로, 사후 회복 운영을 위한 우선점검 모델이 필요하다.",
            "이는 본 모델이 물리적 침수면적 자체보다 생활인구 노출, 상업·업무 밀집, 고령층, 서비스·인프라 병목 등 “호우 이후 운영 취약성”을 포착한다는 의미이다. 따라서 본 모델은 침수위험 지도를 대체하는 것이 아니라, 침수지도와 다른 축의 사후 회복지연 위험을 보완적으로 포착하는 모델로 해석해야 한다. 즉 기존 침수위험 지도와 별도로, 사후 회복 운영을 위한 우선점검 모델이 필요하다.",
        )

        replace_first_paragraph(
            paragraphs,
            "본 제출본은 실제 예산 집행 효과를 관측한 인과적 편익 분석이 아니다. 따라서 확정 예산절감액을 주장하지 않고, 운영 도입 시 기대 가능한 효율 개선 범위를 가정 기반 시나리오로만 제시한다.비용은 모델 유지보수 및 반기 재학습 약 200만 원/년, 소규모 서버 운영 약 100만 원/년, 담당자 교육 및 문서화 약 100만 원/년으로 가정하여 총 약 400만 원/년으로 산정하였다.주요 호우 이벤트 연 3회, 이벤트당 복구 투입 인력·장비 예산을 5억 원으로 가정하되, 모델 성능이 실제 예산절감으로 1:1 전환된다고 보지 않는다. 아래 값은 현장 검증 전 잠재 효율 개선 범위이며, 실제 예산절감액이 아니다.",
            "본 제출본은 실제 예산 집행 효과를 관측한 인과적 편익 분석이 아니다. 따라서 확정 예산절감액을 주장하지 않고, 운영 도입 시 기대 가능한 효율 개선 범위를 가정 기반 시나리오로만 제시한다. 도입·운영비는 모델 유지보수, 소규모 서버 운영, 담당자 교육을 합산해 약 400만 원/년으로 가정하였다. 아래 값은 현장 검증 전 잠재 효율 개선 범위이며, 실제 예산절감액이 아니다.",
        )

        # Table 8: 유형별 운영 플레이북, 5 columns -> 3 columns.
        playbook = tables[7]
        shrink_table_columns(playbook, [0, 3, 4])
        rows = table_rows(playbook)
        set_cell(rows[0][0], "유형")
        set_cell(rows[0][1], "주요 원인")
        set_cell(rows[0][2], "권장 대응")

        # Table 9: representative cases, 5 columns -> 4 columns.
        cases = tables[8]
        shrink_table_columns(cases, [0, 1, 3, 4])
        rows = table_rows(cases)
        set_cell(rows[0][0], "이벤트")
        set_cell(rows[0][1], "실제 지연 동")
        set_cell(rows[0][2], "Recall@20%")
        set_cell(rows[0][3], "Lift@20%")

        # Table 11: shorten B/C assumptions.
        bc = tables[10]
        rows = table_rows(bc)
        set_cell(rows[0][2], "잠재 효율")
        set_cell(rows[1][1], "유형맞춤 효율의 5% 실현")
        set_cell(rows[2][1], "유형맞춤 효율의 10% 실현")
        set_cell(rows[3][1], "유형맞춤 효율 전체를 이론 상한으로 해석")

        # Add a concise conclusion at the end of the document body.
        append_paragraph_to_body(body, "결론")
        append_paragraph_to_body(
            body,
            "본 모델은 회복률 절대값을 정밀 예측하는 모델이라기보다, 호우 이후 제한된 복구자원을 우선 투입할 행정동을 선별하는 랭킹 기반 운영 모델이다. 위험 상위 20% 행정동은 전체 회복지연 동의 82.2%를 포착했고, 무작위 선별 대비 4.07배 높은 위험 농축도를 보였다. 또한 위험 상위군과 하위군의 delayed 비율은 각각 16.3%와 0.5%로 나타나, 사후 점검 후보군 분리 가능성을 확인하였다.",
        )
        append_paragraph_to_body(
            body,
            "최종 산출물은 이벤트별 우선순위표, 유형별 대응 플레이북, 제한자원 시나리오, 상황실형 대시보드로 연결된다. 본 모델은 서울시 사전 침수위험 정보와 실제 재난자원 배치 사이에서, 호우 이후 생활서비스 회복지연 위험을 보완적으로 제시하는 사후 회복 운영 의사결정 모듈로 활용될 수 있다.",
        )

        new_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = new_xml
                zout.writestr(item, data)

    print(OUT)


if __name__ == "__main__":
    main()
