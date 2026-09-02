from pathlib import Path
import shutil
import zipfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DOCX = next(path for path in ROOT.glob("*.docx") if "backup" not in path.name)
BACKUP = ROOT / "analysis_report_final_wording_backup.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W)


def qn(tag: str) -> str:
    return f"{{{W}}}{tag}"


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join((node.text or "") for node in paragraph.findall(".//" + qn("t")))


def set_paragraph_text(paragraph: ET.Element, text: str) -> None:
    text_nodes = paragraph.findall(".//" + qn("t"))
    if not text_nodes:
        run = ET.SubElement(paragraph, qn("r"))
        text_node = ET.SubElement(run, qn("t"))
        text_node.text = text
        return
    text_nodes[0].text = text
    for node in text_nodes[1:]:
        node.text = ""


def make_paragraph_like(reference: ET.Element, text: str) -> ET.Element:
    paragraph = ET.Element(qn("p"))
    ref_properties = reference.find(qn("pPr"))
    if ref_properties is not None:
        paragraph.append(ET.fromstring(ET.tostring(ref_properties, encoding="utf-8")))
    run = ET.SubElement(paragraph, qn("r"))
    text_node = ET.SubElement(run, qn("t"))
    text_node.text = text
    return paragraph


def replace_text_in_paragraphs(root: ET.Element) -> int:
    replacements = {
        "침수위험과 회복지연위험은 다르다: 집중호우 이후 서울 행정동 생활서비스 회복지연 Top-K 선별 모델": (
            "침수위험과 회복지연위험은 다르다: 집중호우 이후 서울 행정동 생활활동 회복지연 Top-K 선별 모델"
        ),
        "서울시 무더위쉼터 위치·용량 데이터(2025년 4,107개소)": (
            "서울시 공공 생활지원시설 자료(무더위쉼터 위치·용량, 2025년 4,107개소)"
        ),
        "복지·지원시설 접근성": "복지·생활지원 거점 접근성",
        "지원시설 접근성": "생활지원 거점 접근성",
        "시설 위치 x 행정동": "공공 생활지원시설 위치 x 행정동",
        "생활서비스·민원 대응": "생활활동·민원 대응",
        "본 모델은 호우 이후 제한된 복구자원을 우선 투입할 행정동을 선별하는 랭킹 기반 운영 모델이다. 위험 상위 20% 행정동은 전체 회복지연 동의 82.2%를 포착했고, 무작위 선별 대비 4.07배 높은 위험 농축도를 보였다. 따라서 본 모델은 침수위험 정보만으로 설명하기 어려운 사후 회복지연 취약성을 보완적으로 제시하며, 서울시·자치구의 D+1 복구자원 배치 의사결정에 활용될 수 있다.": (
            "본 분석은 호우 이후 생활인구 기반 회복지연 위험을 활용해 제한된 복구자원을 우선 투입할 행정동을 선별하는 랭킹형 의사결정 보조모델이다. 위험 상위 20% 행정동은 전체 회복지연 동의 82.2%를 포착했고, 무작위 선별 대비 4.07배 높은 위험 농축도를 보였다. 따라서 본 모델은 단순 침수위험 정보만으로 설명하기 어려운 사후 회복 취약성을 보완적으로 제시하며, 서울시와 자치구의 D+1 우선점검 후보 선정에 활용될 수 있다."
        ),
        "본 분석은 호우 이후 제한된 복구자원을 우선 투입할 행정동을 선별하기 위한 랭킹 기반 운영 모델이다. 위험 상위 20% 행정동은 전체 회복지연 동의 82.2%를 포착했고, 무작위 선별 대비 4.07배 높은 위험 농축도를 보였다. 따라서 본 모델은 단순 침수위험 정보만으로 설명하기 어려운 사후 회복지연 취약성을 보완적으로 제시하며, 서울시와 자치구의 D+1 복구자원 배치 의사결정에 활용될 수 있다.": (
            "본 분석은 호우 이후 생활인구 기반 회복지연 위험을 활용해 제한된 복구자원을 우선 투입할 행정동을 선별하는 랭킹형 의사결정 보조모델이다. 위험 상위 20% 행정동은 전체 회복지연 동의 82.2%를 포착했고, 무작위 선별 대비 4.07배 높은 위험 농축도를 보였다. 따라서 본 모델은 단순 침수위험 정보만으로 설명하기 어려운 사후 회복 취약성을 보완적으로 제시하며, 서울시와 자치구의 D+1 우선점검 후보 선정에 활용될 수 있다."
        ),
        "아래 보완 그림은 기존 모델이 단일 기준 baseline 및 무작위 Top-K보다 회복지연 동을 안정적으로 선별하며, 침수흔적 위험과 회복지연 위험이 공간적으로 구분됨을 보여준다.": (
            "최종 보완 검증은 세 가지 질문에 답한다. 첫째, 본 모델이 단순 강수량·침수흔적 기준보다 실제 회복지연 동을 더 잘 선별하는가. 둘째, 무작위 Top-K와 비교해 선별 결과가 우연이 아닌가. 셋째, 회복지연 위험이 기존 침수흔적 위험과 다른 공간 패턴을 보이는가."
        ),
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


def insert_internal_validation_paragraph(root: ET.Element) -> bool:
    target = (
        "또한 duration_days 제외 시에도 macro Lift@20%가 3.53x로 유지되어, 결과가 이벤트 지속일 단일 피처에만 "
        "의존하지 않음을 보조 확인하였다. 다만 LOEO R2가 낮기 때문에 본 모델은 회복률 절대값을 확정 예측하는 "
        "도구가 아니라, 사후 점검 후보군을 좁히는 랭킹형 의사결정 보조도구로 한정해 활용한다."
    )
    insert_text = (
        "다만 delayed 라벨 역시 생활인구 회복 궤적에서 파생된 사후 평가 지표이므로, 본 검증은 "
        "민원·폐기물·현장점검 실적에 대한 외부 검증이 아니라 생활인구 기반 회복지연 선별력에 대한 "
        "내부 일관성 검증으로 해석한다. 향후 실제 행정수요 데이터가 확보되면 외부 타깃을 활용한 "
        "재검증이 필요하다."
    )
    if any(paragraph_text(p) == insert_text for p in root.findall(".//" + qn("p"))):
        return False

    for parent in root.iter():
        children = list(parent)
        for index, child in enumerate(children):
            if child.tag == qn("p") and paragraph_text(child) == target:
                parent.insert(index + 1, make_paragraph_like(child, insert_text))
                return True
    return False


def strengthen_whatif_paragraph(root: ET.Element) -> bool:
    old = (
        "본 과제의 What-if 분석은 동일한 보수적 개선 가정하에서 배치전략별 상대 효율을 비교한 민감도 분석이다. "
        "Recovery Benefit Index는 실제 예산절감액이 아니라, 위험 후보군에 조기 점검·복구자원을 배치했을 때 "
        "기대되는 회복 개선 효과를 전략 간 상대 비교하기 위한 지표로 사용하였다. 산식은 “Σ(기준선 생활인구 × "
        "예상 회복률 개선폭 × 전략·유형별 조치효율 가중치)”의 구조로 해석하며, 절대 금액이 아니라 전략 간 "
        "우선순위 비교에 목적이 있다."
    )
    new = (
        old
        + " 예상 회복률 개선폭과 조치효율 가중치는 실제 효과를 관측한 값이 아니라, 모든 전략에 동일한 "
        "보수적 개선폭을 적용한 뒤 유형 적합도에 따라 상대 가중치를 둔 민감도 분석용 가정값이다. 따라서 "
        "Recovery Benefit Index는 정책효과의 절대 추정치가 아니라 전략 간 우선순위를 비교하기 위한 내부 "
        "비교지표이다."
    )
    for paragraph in root.findall(".//" + qn("p")):
        if paragraph_text(paragraph) == old:
            set_paragraph_text(paragraph, new)
            return True
    return False


def main() -> None:
    if not BACKUP.exists():
        shutil.copy2(DOCX, BACKUP)

    with zipfile.ZipFile(DOCX, "r") as zin:
        entries = {info.filename: zin.read(info.filename) for info in zin.infolist()}

    root = ET.fromstring(entries["word/document.xml"])
    changed_paragraphs = replace_text_in_paragraphs(root)
    inserted_validation = insert_internal_validation_paragraph(root)
    strengthened_whatif = strengthen_whatif_paragraph(root)

    entries["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    temp = DOCX.with_suffix(".tmp.docx")
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries.items():
            zout.writestr(name, data)
    shutil.move(str(temp), str(DOCX))

    print(f"updated={DOCX}")
    print(f"backup={BACKUP}")
    print(f"changed_paragraphs={changed_paragraphs}")
    print(f"inserted_validation={inserted_validation}")
    print(f"strengthened_whatif={strengthened_whatif}")


if __name__ == "__main__":
    main()
