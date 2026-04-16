from typing import Any, Dict, List
import math

PLAY_KEYS = [
"small_repeat_trades",
"wait",
"event_front_run",
"no_chase",
]

RISK_KEYS = [
"liquidity",
"point_competition",
"security",
"execution",
]

def _clamp(value : float, min_value : float, max_value : float) -> float:
    return max(min_value, min(value, max_value))

#1. max 계산
def compute_weight(feature : Dict[str, Any]) -> float:
    """
    w_i = 0.45R_i + 0.35C_i + 0.20E_i
    지금은 mock으로 간단히 계산
    """
    #최신성(지금은 1로 고정)
    R_i = 1.0

    #신뢰도
    aux_tags = feature.get("aux_tags", [])
    C_i = 0.75
    if "promo" in aux_tags:
        C_i -= 0.25
    if "warning" in aux_tags:
        C_i += 0.10
    
    C_i = _clamp(C_i, 0.0, 1.0)

    #반응도(mock)
    E_i = 0.5

    w_i = 0.45 * R_i + 0.35 * C_i + 0.20 * E_i
    return w_i

#상태 벡터 계산
def aggregate_state(features : List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    S_A = Σ(w_i * f_i) / Σ(w_i)
    """
    if not features:
        return {}
    
    total_weight = 0.0
    mood_sum = 0.0
    play_sum = {key : 0.0 for key in PLAY_KEYS}
    risk_sum = {key : 0.0 for key in RISK_KEYS}

    for feature in features:
        w = compute_weight(feature)

        total_weight += w

        mood_sum += w * feature["mood_score"]

        for key in PLAY_KEYS:
            play_sum[key] += w*feature["play_probs"].get(key, 0.0)
        
        for key in RISK_KEYS:
            risk_sum[key] += w*feature["risk_scores"].get(key, 0.0)
        
        if total_weight == 0:
            return {}

    mood = mood_sum / total_weight
    play = {k: v / total_weight for k, v in play_sum.items()}
    risk = {k: v / total_weight for k, v in risk_sum.items()}

    return {
        "mood": mood,
        "play": play,
        "risk": risk,
    }

 #3. Label 변환
def classify_mood(mood : float) -> str:
    if mood < -0.2:
        return "공포 속 반등시도"
    elif mood < 0.1:
        return "혼잡"
    elif mood < 0.6:
        return "조심스러운 낙관"
    else:
        return "과열"
     
def classify_playbook(play : Dict[str, float]) -> str:
    if not play:
        return "데이터 부족"
    
    best = max(play, key=play.get)
    best_val = play.get(best, 0.0)

    if best_val < 0.3:
        return "불확실"

    mapping = {
        "small_repeat_trades": "소액 다회전",
        "wait": "대기",
        "event_front_run": "이벤트 선점",
        "no_chase": "추격금지",
    }

    return mapping.get(best, "알 수 없음")

def classify_risk(risk : Dict[str, float]) -> List[str]:
    flags = []

    if risk.get("liquidity", 0) > 0.30:
        flags.append("유동성")

    if risk.get("point_competition", 0) > 0.30:
        flags.append("포인트 경쟁")

    if risk.get("security", 0) > 0.30:
        flags.append("보안")

    if risk.get("execution", 0) > 0.25:
        flags.append("실행 리스크")

    return flags

#4. 최종 결과
def build_asset_state(asset_key: str, features: List[Dict[str, Any]]) -> Dict[str, Any]:
    state = aggregate_state(features)

    if not state:
        return {}

    mood_label = classify_mood(state["mood"])
    playbook_label = classify_playbook(state["play"])
    risk_flags = classify_risk(state["risk"])

    confidence = min(len(features) / 10.0, 1.0)

    return {
        "asset_key": asset_key,
        "mood_label": mood_label,
        "playbook_label": playbook_label,
        "risk_flags": risk_flags,
        "confidence": confidence,
        "raw": state,
    }


# 🔥 테스트용
if __name__ == "__main__":
    sample_features = [
        {
            "doc_id": "1",
            "asset_key": "BTC",
            "clean_text": "",
            "aux_tags": ["event"],
            "mood_score": 0.4,
            "play_probs": {
                "small_repeat_trades": 0.2,
                "wait": 0.2,
                "event_front_run": 0.5,
                "no_chase": 0.1,
            },
            "risk_scores": {
                "liquidity": 0.2,
                "point_competition": 0.3,
                "security": 0.1,
                "execution": 0.4,
            },
        },
        {
            "doc_id": "2",
            "asset_key": "BTC",
            "clean_text": "",
            "aux_tags": ["warning"],
            "mood_score": -0.3,
            "play_probs": {
                "small_repeat_trades": 0.1,
                "wait": 0.5,
                "event_front_run": 0.1,
                "no_chase": 0.3,
            },
            "risk_scores": {
                "liquidity": 0.7,
                "point_competition": 0.2,
                "security": 0.3,
                "execution": 0.6,
            },
        },
    ]

    result = build_asset_state("BTC", sample_features)
    print(result)

    
