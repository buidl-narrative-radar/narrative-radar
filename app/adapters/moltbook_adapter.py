import re
import os
from typing import Any, Dict, List


def extract_asset_symbol(asset_key: str) -> str:
    """
    asset_key 예: 'bsc:BNB' -> 'BNB'
    """
    if not isinstance(asset_key, str) or not asset_key.strip():
        return "UNKNOWN"

    if ":" in asset_key:
        return asset_key.split(":")[-1].strip().upper()

    return asset_key.strip().upper()


def normalize_engagement_from_line(line: str) -> Dict[str, int]:
    """
    예:
    'views 848 / likes 26 / reposts 7 / comments 10'
    를 파싱해서 dict로 변환
    """
    if not isinstance(line, str):
        return {"views": 0, "likes": 0, "reposts": 0, "comments": 0}

    patterns = {
        "views": r"views\s+(\d+)",
        "likes": r"likes\s+(\d+)",
        "reposts": r"reposts\s+(\d+)",
        "comments": r"comments\s+(\d+)",
    }

    result: Dict[str, int] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, line, flags=re.IGNORECASE)
        result[key] = int(match.group(1)) if match else 0

    return result


def build_text(title: str, content: str) -> str:
    """
    extractor가 읽을 최종 text.
    title + content를 합친다.
    """
    title = title.strip() if isinstance(title, str) else ""
    content = content.strip() if isinstance(content, str) else ""

    if title and content:
        return f"{title}\n\n{content}"
    if title:
        return title
    return content


def parse_risk_hints(raw: str) -> List[str]:
    """
    예:
    'Liquidity, Execution'
    -> ['Liquidity', 'Execution']
    """
    if not isinstance(raw, str) or not raw.strip():
        return []

    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_doc_block(block: str) -> Dict[str, Any]:
    """
    하나의 ### doc_xxx 블록을 파싱해서
    엔진 입력용 doc dict + 평가용 _labels를 만든다.
    """
    lines = [line.rstrip() for line in block.splitlines() if line.strip()]
    raw: Dict[str, Any] = {
        "doc_id": "",
        "submolt": "",
        "asset_key": "",
        "title": "",
        "content": "",
        "published_at": None,
        "engagement": {"views": 0, "likes": 0, "reposts": 0, "comments": 0},
        "mood_hint": None,
        "playbook_hint": None,
        "risk_hints": [],
    }

    # 첫 줄: ### doc_001
    first_line = lines[0]
    doc_match = re.match(r"^###\s+(doc_\d+)\s*$", first_line)
    if doc_match:
        raw["doc_id"] = doc_match.group(1)

    for line in lines[1:]:
        # 예: - submolt: `bsc-traders`
        field_match = re.match(r"^-+\s*([a-zA-Z_]+)\s*:\s*(.*)$", line)
        if not field_match:
            continue

        key = field_match.group(1).strip()
        value = field_match.group(2).strip()

        # backtick 제거
        if value.startswith("`") and value.endswith("`"):
            value = value[1:-1].strip()

        if key == "submolt":
            raw["submolt"] = value
        elif key == "asset_key":
            raw["asset_key"] = value
        elif key == "title":
            raw["title"] = value
        elif key == "content":
            raw["content"] = value
        elif key == "published_at":
            raw["published_at"] = value
        elif key == "engagement":
            raw["engagement"] = normalize_engagement_from_line(value)
        elif key == "mood_hint":
            raw["mood_hint"] = value
        elif key == "playbook_hint":
            raw["playbook_hint"] = value
        elif key == "risk_hints":
            raw["risk_hints"] = parse_risk_hints(value)

    doc = {
        "doc_id": raw["doc_id"],
        "source": "mock_discussion",
        "source_type": "discussion_document",
        "author_id": raw["submolt"],
        "asset_key": raw["asset_key"],
        "asset_symbol": extract_asset_symbol(raw["asset_key"]),
        "text": build_text(raw["title"], raw["content"]),
        "published_at": raw["published_at"],
        "engagement": raw["engagement"],
        # 엔진 입력으로는 쓰지 않고 평가용으로만 둠
        "_labels": {
            "mood_hint": raw["mood_hint"],
            "playbook_hint": raw["playbook_hint"],
            "risk_hints": raw["risk_hints"],
        },
    }

    return doc


def split_into_doc_blocks(md_text: str) -> List[str]:
    """
    전체 md 텍스트를 ### doc_xxx 기준으로 문서 블록으로 분리한다.
    헤더/설명문은 무시된다.
    """
    if not isinstance(md_text, str):
        return []

    matches = list(re.finditer(r"^###\s+doc_\d+\s*$", md_text, flags=re.MULTILINE))
    if not matches:
        return []

    blocks: List[str] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        block = md_text[start:end].strip()
        blocks.append(block)

    return blocks


def load_mock_docs_from_md(file_path: str) -> List[Dict[str, Any]]:
    """
    .md 파일을 읽어서 doc 리스트로 변환한다.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    blocks = split_into_doc_blocks(md_text)
    docs = [parse_doc_block(block) for block in blocks]
    return docs


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(BASE_DIR, "mock_data", "moltbook_mock_docs.md")

    docs = load_mock_docs_from_md(file_path)

    print(f"loaded docs: {len(docs)}")
    if docs:
        print(docs[0])