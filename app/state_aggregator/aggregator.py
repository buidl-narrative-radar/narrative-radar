import math
from typing import Any, Dict, List


PLAY_LABEL_MAP = {
    "small_repeat_trades": "소액 다회전",
    "wait": "대기",
    "event_front_run": "이벤트 선점",
    "no_chase": "추격금지",
}


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def normalize_play_probs(play_probs: Dict[str, float]) -> Dict[str, float]:
    keys = ["small_repeat_trades", "wait", "event_front_run", "no_chase"]
    cleaned = {k: max(float(play_probs.get(k, 0.0)), 0.0) for k in keys}
    total = sum(cleaned.values())

    if total <= 0:
        return {
            "small_repeat_trades": 0.25,
            "wait": 0.25,
            "event_front_run": 0.25,
            "no_chase": 0.25,
        }

    return {k: v / total for k, v in cleaned.items()}


def clamp_risk_scores(risk_scores: Dict[str, float]) -> Dict[str, float]:
    keys = ["liquidity", "point_competition", "security", "execution"]
    return {
        k: clamp(float(risk_scores.get(k, 0.0)), 0.0, 1.0)
        for k in keys
    }


def compute_engagement_score(feature: Dict[str, Any]) -> float:
    """
    engagement 기반 문서 가중치.
    큰 값 폭주를 막기 위해 log 사용.
    """
    engagement = feature.get("engagement", {}) or {}
    views = float(engagement.get("views", 0.0))
    likes = float(engagement.get("likes", 0.0))
    reposts = float(engagement.get("reposts", 0.0))
    comments = float(engagement.get("comments", 0.0))

    raw = views + 3 * likes + 5 * reposts + 4 * comments
    return 1.0 + math.log1p(raw) / 10.0


def compute_feature_weight(feature: Dict[str, Any]) -> float:
    """
    지금 MVP에서는 engagement 중심 가중치만 사용.
    """
    return compute_engagement_score(feature)


def aggregate_weighted_mood(features: List[Dict[str, Any]]) -> float:
    numerator = 0.0
    denominator = 0.0

    for feature in features:
        weight = compute_feature_weight(feature)
        numerator += weight * float(feature.get("mood_score", 0.0))
        denominator += weight

    return safe_div(numerator, denominator)


def aggregate_weighted_play(features: List[Dict[str, Any]]) -> Dict[str, float]:
    totals = {
        "small_repeat_trades": 0.0,
        "wait": 0.0,
        "event_front_run": 0.0,
        "no_chase": 0.0,
    }
    denominator = 0.0

    for feature in features:
        weight = compute_feature_weight(feature)
        play_probs = normalize_play_probs(feature.get("play_probs", {}))

        for key in totals:
            totals[key] += weight * play_probs.get(key, 0.0)

        denominator += weight

    if denominator == 0:
        return normalize_play_probs(totals)

    averaged = {key: totals[key] / denominator for key in totals}
    return normalize_play_probs(averaged)


def aggregate_weighted_risk(features: List[Dict[str, Any]]) -> Dict[str, float]:
    totals = {
        "liquidity": 0.0,
        "point_competition": 0.0,
        "security": 0.0,
        "execution": 0.0,
    }
    denominator = 0.0

    for feature in features:
        weight = compute_feature_weight(feature)
        risks = clamp_risk_scores(feature.get("risk_scores", {}))

        for key in totals:
            totals[key] += weight * risks.get(key, 0.0)

        denominator += weight

    if denominator == 0:
        return totals

    averaged = {key: totals[key] / denominator for key in totals}
    return clamp_risk_scores(averaged)


def classify_mood(mood_score: float) -> str:
    """
    asset-level mood 라벨링
    """
    if mood_score >= 0.45:
        return "과열"
    if mood_score >= 0.10:
        return "조심스러운 낙관"
    if mood_score <= -0.20:
        return "공포 속 반등시도"
    return "혼잡"


def classify_playbook(play: Dict[str, float]) -> str:
    """
    확률 최대값 + top1/top2 gap을 같이 보는 방식.
    """
    if not play:
        return "데이터 부족"

    play = normalize_play_probs(play)
    sorted_items = sorted(play.items(), key=lambda x: x[1], reverse=True)

    best_key, best_val = sorted_items[0]
    second_val = sorted_items[1][1] if len(sorted_items) > 1 else 0.0

    gap = best_val - second_val

    # 너무 박빙이면 불확실
    if best_val < 0.30 and gap < 0.05:
        return "불확실"

    # 아주 약한 우위도 불확실
    if gap < 0.05:
        return "불확실"

    return PLAY_LABEL_MAP.get(best_key, "알 수 없음")


def classify_risk_flags(risk: Dict[str, float]) -> List[str]:
    flags: List[str] = []

    if risk.get("liquidity", 0.0) >= 0.30:
        flags.append("유동성")

    if risk.get("point_competition", 0.0) >= 0.30:
        flags.append("포인트 경쟁")

    if risk.get("security", 0.0) >= 0.30:
        flags.append("보안")

    if risk.get("execution", 0.0) >= 0.30:
        flags.append("실행 리스크")

    return flags


def compute_confidence(features, mood_score, play_probs, risk_scores):

    coverage = min(len(features) / 5.0, 1.0)  

    mood_strength = abs(mood_score)

    top_prob = max(play_probs.values()) if play_probs else 0.0

    risk_strength = sum(risk_scores.values()) / len(risk_scores) if risk_scores else 0.0

    confidence = (
        0.2 * coverage +
        0.4 * mood_strength +
        0.3 * top_prob +
        0.1 * risk_strength
    )

    return round(min(max(confidence, 0.0), 1.0), 3)


def build_asset_state(asset_key: str, features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    asset 단위 feature 리스트를 받아 최종 posture state 생성.
    """
    mood_score = aggregate_weighted_mood(features)
    play_probs = aggregate_weighted_play(features)
    risk_scores = aggregate_weighted_risk(features)

    mood_label = classify_mood(mood_score)
    playbook_label = classify_playbook(play_probs)
    risk_flags = classify_risk_flags(risk_scores)
    confidence = compute_confidence(
        features=features,
        mood_score=mood_score,
        play_probs=play_probs,
        risk_scores=risk_scores,
    )

    return {
        "asset_key": asset_key,
        "mood_label": mood_label,
        "playbook_label": playbook_label,
        "risk_flags": risk_flags,
        "confidence": confidence,
        "raw": {
            "mood": mood_score,
            "play": play_probs,
            "risk": risk_scores,
        },
    }