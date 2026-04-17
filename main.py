import json
from typing import Any, Dict, List

# adapters
from app.adapters.moltbook_adapter import load_mock_docs_from_md

# feature extraction
from app.feature_extractor.extractor import extract_features

# aggregation
from app.state_aggregator.aggregator import build_asset_state

# evaluation
from app.evaluation.evaluate import evaluate_feature, print_evaluation_report

# output
from app.output.generator import generate_asset_summary
from app.output.templates import render_template


def extract_all_features(docs: List[Dict[str, Any]], mode: str = "llm") -> List[Dict[str, Any]]:
    features: List[Dict[str, Any]] = []

    for doc in docs:
        feature = extract_features(doc, mode=mode)

        # 평가용 label metadata 유지
        if "_labels" in doc:
            feature["_labels"] = doc["_labels"]

        # 가중치 계산용 engagement 유지
        if "engagement" in doc:
            feature["engagement"] = doc["engagement"]

        features.append(feature)

    return features


def group_features_by_asset(features: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for feature in features:
        asset_key = feature["asset_key"]
        if asset_key not in grouped:
            grouped[asset_key] = []
        grouped[asset_key].append(feature)

    return grouped


def build_all_asset_states(grouped_features: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    asset_states: List[Dict[str, Any]] = []

    for asset_key, features in grouped_features.items():
        asset_state = build_asset_state(asset_key, features)
        asset_states.append(asset_state)

    return asset_states


def to_confidence_label(score: float) -> str:
    if score >= 0.66:
        return "High"
    if score >= 0.45:
        return "Medium"
    return "Low"


def main() -> None:
    # 1) mock md 문서 로드
    file_path = "mock_data/moltbook_mock_docs.md"
    docs = load_mock_docs_from_md(file_path)

    print("=== NORMALIZED DOCS (d_i) ===")
    print(f"loaded docs: {len(docs)}")
    for doc in docs[:3]:
        print(doc)
    print()

    # 2) extractor 실행
    features = extract_all_features(docs, mode="llm")

    print("=== EXTRACTED FEATURES ===")
    for feature in features[:3]:
        print(feature)
    print()

    # 3) 문서 단위 평가
    evaluation_results = [evaluate_feature(feature) for feature in features]

    print("=== DOCUMENT-LEVEL EVALUATION ===")
    print_evaluation_report(evaluation_results)
    print()

    # 4) asset_key 기준 grouping
    grouped_features = group_features_by_asset(features)

    print("=== GROUPED FEATURES ===")
    for asset_key, asset_features in grouped_features.items():
        print(f"{asset_key}: {len(asset_features)} docs")
    print()

    # 5) asset별 최종 상태 계산
    asset_states = build_all_asset_states(grouped_features)

    print("=== FINAL ASSET STATES ===")
    for state in asset_states:
        print(state)
    print()

    # 6) 출력용 summary 생성 + 프런트용 JSON 변환
    print("=== OUTPUT SUMMARIES ===")

    output: List[Dict[str, Any]] = []

    for state in asset_states:
        asset_key = state["asset_key"]
        symbol = asset_key.split(":")[-1] if ":" in asset_key else asset_key

        try:
            summary = generate_asset_summary(state)
        except Exception as e:
            print(f"⚠️ output LLM failed for {asset_key}: {e}")
            summary = render_template(state)

        print(f"[{asset_key}]")
        print(summary)
        print()

        output.append(
            {
                "asset_key": asset_key,  # ex) bsc:BNB
                "symbol": symbol,  # ex) BNB
                "mood_label": state["mood_label"],
                "playbook_label": state["playbook_label"],
                "risk_flags": state["risk_flags"],
                "summary": summary,
                "confidence_score": state["confidence"],
                "confidence_label": to_confidence_label(state["confidence"]),
            }
        )

    # 7) JSON 파일 저장
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("✅ output.json saved")


if __name__ == "__main__":
    main()