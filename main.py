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

        if "_labels" in doc:
            feature["_labels"] = doc["_labels"]

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


def state_to_frontend_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    asset_key = state["asset_key"]
    symbol = asset_key.split(":")[-1] if ":" in asset_key else asset_key

    try:
        summary = generate_asset_summary(state)
    except Exception:
        summary = render_template(state)

    return {
        "asset_key": asset_key,
        "symbol": symbol,
        "mood_label": state["mood_label"],
        "playbook_label": state["playbook_label"],
        "risk_flags": state["risk_flags"],
        "summary": summary,
        "confidence_score": state["confidence"],
        "confidence_label": to_confidence_label(state["confidence"]),
    }


def run_pipeline(mode: str = "llm") -> List[Dict[str, Any]]:
    """
    전체 60개 mock docs를 돌려 frontend-ready output 리스트 반환
    """
    file_path = "mock_data/moltbook_mock_docs.md"
    docs = load_mock_docs_from_md(file_path)

    features = extract_all_features(docs, mode=mode)
    grouped_features = group_features_by_asset(features)
    asset_states = build_all_asset_states(grouped_features)

    output = [state_to_frontend_payload(state) for state in asset_states]
    return output


def run_single_asset_pipeline(symbol: str, mode: str = "llm") -> Dict[str, Any]:
    """
    symbol 하나만 처리해서 frontend-ready payload 반환
    예: BNB, CAKE, LISTA
    """
    symbol = symbol.upper().strip()
    target_asset_key = f"bsc:{symbol}"

    file_path = "mock_data/moltbook_mock_docs.md"
    docs = load_mock_docs_from_md(file_path)

    filtered_docs = [doc for doc in docs if doc.get("asset_key") == target_asset_key]

    if not filtered_docs:
        raise ValueError(f"Asset not found: {symbol}")

    features = extract_all_features(filtered_docs, mode=mode)
    asset_state = build_asset_state(target_asset_key, features)

    return state_to_frontend_payload(asset_state)


def main() -> None:
    docs_output = run_pipeline(mode="llm")

    print("=== OUTPUT ===")
    for item in docs_output:
        print(item)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(docs_output, f, indent=2, ensure_ascii=False)

    print("✅ output.json saved")


if __name__ == "__main__":
    main()