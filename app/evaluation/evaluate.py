from typing import Any, Dict, List, Optional

from app.state_aggregator.aggregator import classify_mood, classify_playbook


MOOD_HINT_MAP = {
    "fear_rebound": "공포 속 반등시도",
    "mixed": "혼잡",
    "cautious_heat": "조심스러운 낙관",
    "overheat": "과열",
}

PLAYBOOK_HINT_MAP = {
    "Event front-run": "이벤트 선점",
    "Wait-for-dip": "대기",
    "No-chase": "추격금지",
    "Small-repeat-trades": "소액 다회전",
}

RISK_HINT_MAP = {
    "Liquidity": "유동성",
    "Execution": "실행 리스크",
    "Security": "보안",
    "Point competition": "포인트 경쟁",
}


def normalize_mood_hint(raw_hint: str) -> str:
    if not isinstance(raw_hint, str):
        return "알 수 없음"
    return MOOD_HINT_MAP.get(raw_hint.strip(), "알 수 없음")


def normalize_playbook_hint(raw_hint: str) -> str:
    if not isinstance(raw_hint, str):
        return "알 수 없음"
    return PLAYBOOK_HINT_MAP.get(raw_hint.strip(), "알 수 없음")


def normalize_risk_hints(raw_hints: List[str]) -> List[str]:
    if not isinstance(raw_hints, list):
        return []

    normalized: List[str] = []
    for hint in raw_hints:
        if not isinstance(hint, str):
            continue
        mapped = RISK_HINT_MAP.get(hint.strip())
        if mapped:
            normalized.append(mapped)
    return normalized


def classify_document_playbook(play_probs: Dict[str, float]) -> str:
    return classify_playbook(play_probs)


def classify_document_risks(risk_scores: Dict[str, float]) -> List[str]:
    flags: List[str] = []

    if risk_scores.get("liquidity", 0.0) >= 0.25:
        flags.append("유동성")

    if risk_scores.get("point_competition", 0.0) >= 0.25:
        flags.append("포인트 경쟁")

    if risk_scores.get("security", 0.0) >= 0.25:
        flags.append("보안")

    if risk_scores.get("execution", 0.0) >= 0.25:
        flags.append("실행 리스크")

    return flags


def is_playbook_match(predicted: str, hint: str, play_probs: Dict[str, float]) -> Optional[bool]:
    """
    playbook 평가.
    hint가 '알 수 없음'이면 None 반환 → 평가 제외
    """
    if hint == "알 수 없음":
        return None

    if predicted == hint:
        return True

    soft_groups = [
        {"대기", "이벤트 선점"},
        {"대기", "추격금지"},
    ]

    for group in soft_groups:
        if predicted in group and hint in group:
            return True

    key_map = {
        "소액 다회전": "small_repeat_trades",
        "대기": "wait",
        "이벤트 선점": "event_front_run",
        "추격금지": "no_chase",
    }

    hint_key = key_map.get(hint)
    if hint_key and play_probs.get(hint_key, 0.0) >= 0.25:
        return True

    return False


def evaluate_feature(feature: Dict[str, Any]) -> Dict[str, Any]:
    labels = feature.get("_labels", {}) or {}

    predicted_mood = classify_mood(feature.get("mood_score", 0.0))
    predicted_playbook = classify_document_playbook(feature.get("play_probs", {}))
    predicted_risks = classify_document_risks(feature.get("risk_scores", {}))

    hint_mood = normalize_mood_hint(labels.get("mood_hint"))
    hint_playbook = normalize_playbook_hint(labels.get("playbook_hint"))
    hint_risks = normalize_risk_hints(labels.get("risk_hints", []))

    mood_match: Optional[bool]
    if hint_mood == "알 수 없음":
        mood_match = None
    else:
        mood_match = predicted_mood == hint_mood

    playbook_match = is_playbook_match(
        predicted_playbook,
        hint_playbook,
        feature.get("play_probs", {}),
    )

    # risk는 hint가 비어 있으면 평가 제외
    if len(hint_risks) == 0:
        risk_overlap: Optional[bool] = None
        risk_exact_match: Optional[bool] = None
    else:
        risk_overlap = len(set(predicted_risks) & set(hint_risks)) > 0
        risk_exact_match = set(predicted_risks) == set(hint_risks)

    return {
        "doc_id": feature.get("doc_id"),
        "asset_key": feature.get("asset_key"),
        "predicted": {
            "mood": predicted_mood,
            "playbook": predicted_playbook,
            "risks": predicted_risks,
        },
        "hint": {
            "mood": hint_mood,
            "playbook": hint_playbook,
            "risks": hint_risks,
        },
        "matches": {
            "mood_match": mood_match,
            "playbook_match": playbook_match,
            "risk_overlap": risk_overlap,
            "risk_exact_match": risk_exact_match,
        },
    }


def _safe_rate(values: List[Optional[bool]]) -> float:
    """
    None은 분모에서 제외하고 True/False만 계산
    """
    valid = [v for v in values if v is not None]
    if not valid:
        return 0.0
    return round(sum(1 for v in valid if v) / len(valid), 3)


def summarize_evaluations(results: List[Dict[str, Any]]) -> Dict[str, float]:
    if not results:
        return {
            "mood_match_rate": 0.0,
            "playbook_match_rate": 0.0,
            "risk_overlap_rate": 0.0,
            "risk_exact_match_rate": 0.0,
        }

    mood_values = [r["matches"]["mood_match"] for r in results]
    playbook_values = [r["matches"]["playbook_match"] for r in results]
    risk_overlap_values = [r["matches"]["risk_overlap"] for r in results]
    risk_exact_values = [r["matches"]["risk_exact_match"] for r in results]

    return {
        "mood_match_rate": _safe_rate(mood_values),
        "playbook_match_rate": _safe_rate(playbook_values),
        "risk_overlap_rate": _safe_rate(risk_overlap_values),
        "risk_exact_match_rate": _safe_rate(risk_exact_values),
    }


def print_evaluation_report(results: List[Dict[str, Any]]) -> None:
    for r in results[:10]:
        print(f"doc_id={r['doc_id']} asset={r['asset_key']}")
        print(
            f"  mood: predicted={r['predicted']['mood']} / hint={r['hint']['mood']} "
            f"/ match={r['matches']['mood_match']}"
        )
        print(
            f"  playbook: predicted={r['predicted']['playbook']} / hint={r['hint']['playbook']} "
            f"/ match={r['matches']['playbook_match']}"
        )
        print(
            f"  risks: predicted={r['predicted']['risks']} / hint={r['hint']['risks']} "
            f"/ overlap={r['matches']['risk_overlap']} / exact={r['matches']['risk_exact_match']}"
        )
        print()

    summary = summarize_evaluations(results)

    print("=== EVALUATION SUMMARY ===")
    print(summary)