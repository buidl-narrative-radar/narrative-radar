import re
from typing import Any, Dict, List

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

def preprocess_text(text : str) -> str:
    """
    Raw text를 분석 가능한 clean_text로 정리한다.

    처리:
    - URL 제거
    - 공백 정리
    - 앞뒤 공백 제거
    """
    if not isinstance(text, str):
        return " "
    
    text = re.sub(r"http\S+|www\.\S+", "", text)

    text = re.sub(r"\s+", " ", text).strip()


    return text

def extract_aux_tag(clean_text : str) -> List[str]:
    """
    텍스트의 의미 추출을 돕는 보조 태그를 뽑는다.
    지금은 간단한 키워드 규칙 기반으로 처리한다.
    """
    text = clean_text.lower()
    tags : List[str] = []

    event_keywords = [
         "airdrop", "listing", "launch", "announcement", "event",
        "상장", "에어드랍", "출시", "발표", "이벤트"
    ]
    promo_keywords = [
        "100x", "moon", "gem", "don't miss", "dont miss", "join now",
        "pump", "to the moon", "무조건", "지금 타", "떡상"
    ]
    warning_keywords = [
         "risk", "danger", "avoid", "careful", "beware",
        "위험", "조심", "피해", "설거지", "끝물"
    ]
    crowd_keywords = [
        "everyone", "people", "crowd", "many are buying",
        "다들", "사람들", "몰린다", "물량 모으는"
    ]
    liquidity_keywords = [
        "liquidity", "thin liquidity", "spread", "depth",
        "유동성", "스프레드", "호가", "깊이"
    ]
    wait_keywords = [
        "wait", "hold on", "stay patient",
        "기다려", "관망", "지켜보자"
    ]

    if any(keyword in text for keyword in event_keywords):
        tags.append("event")
    if any(keyword in text for keyword in promo_keywords):
        tags.append("promo")
    if any(keyword in text for keyword in warning_keywords):
        tags.append("warning")
    if any(keyword in text for keyword in crowd_keywords):
        tags.append("crowd")
    if any(keyword in text for keyword in liquidity_keywords):
        tags.append("liquidity")
    if any(keyword in text for keyword in wait_keywords):
        tags.append("wait_signal")

    return tags

def _normalize_play_probs(play_probs : Dict[str, float]) -> Dict[str, float]:
    """
    play_probs의 합이 1이 되도록 정규화한다.
    """
    total = sum(play_probs.values())

    if total == 0:
        default_value = 1.0 / len(PLAY_KEYS)
        return {key : default_value for key in PLAY_KEYS}
    return {key : value / total for key, value in play_probs.items()}

def _clamp(value : float, min_value : float, max_value : float) -> float:
    return max(min_value, min(value, max_value))

def infer_mock_features(clean_text: str, aux_tags: List[str]) -> Dict[str, Any]:
    """
    지금 단계에서는 LLM 대신 규칙 기반으로
    mood_score / play_probs / risk_scores를 대략 추정한다.

    나중에 이 함수가 LLM 호출 함수로 교체될 핵심 자리다.
    """
    text = clean_text.lower()

    mood_score = 0.0

    play_probs = {
        "small_repeat_trades": 0.25,
        "wait": 0.25,
        "event_front_run": 0.25,
        "no_chase": 0.25,
    }

    risk_scores = {
        "liquidity": 0.0,
        "point_competition": 0.0,
        "security": 0.0,
        "execution": 0.0,
    }

    positive_keywords = [
        "bullish", "strong", "accumulate", "momentum", "breakout",
        "낙관", "강하다", "모으는", "붙는 느낌", "선점"
    ]
    negative_keywords = [
        "dump", "sell-off", "avoid", "exit", "rug", "scam",
        "덤핑", "매도", "피해", "러그", "사기", "설거지", "끝물"
    ]

    if any(keyword in text for keyword in positive_keywords):
        mood_score += 0.35

    if any(keyword in text for keyword in negative_keywords):
        mood_score -= 0.45

    if "event" in aux_tags:
        mood_score += 0.20
        play_probs["event_front_run"] += 0.55
        risk_scores["execution"] += 0.20

    if "promo" in aux_tags:
        mood_score += 0.20
        play_probs["event_front_run"] += 0.10
        risk_scores["point_competition"] += 0.20

    if "warning" in aux_tags:
        mood_score -= 0.35
        play_probs["wait"] += 0.20
        play_probs["no_chase"] += 0.30
        risk_scores["execution"] += 0.20
        risk_scores["security"] += 0.15

    if "crowd" in aux_tags:
        mood_score += 0.10
        play_probs["event_front_run"] += 0.15
        risk_scores["point_competition"] += 0.15

    if "liquidity" in aux_tags:
        risk_scores["liquidity"] += 0.40
        play_probs["wait"] += 0.15
        play_probs["no_chase"] += 0.10
        mood_score -= 0.10

    if "wait_signal" in aux_tags:
        play_probs["wait"] += 0.35
        play_probs["no_chase"] += 0.10
        mood_score -= 0.05

    # 추가 키워드 기반 리스크
    if "security" in text or "hack" in text or "exploit" in text or "보안" in text or "해킹" in text:
        risk_scores["security"] += 0.50
        mood_score -= 0.30

    if "execution" in text or "slippage" in text or "실행" in text or "슬리피지" in text:
        risk_scores["execution"] += 0.40

    if "scalp" in text or "rotate" in text or "짧게" in text or "단타" in text:
        play_probs["small_repeat_trades"] += 0.35

    if "wait" in text or "관망" in text or "지켜보자" in text:
        play_probs["wait"] += 0.25

    if "don't chase" in text or "dont chase" in text or "추격 금지" in text:
        play_probs["no_chase"] += 0.40
        mood_score -= 0.10

    mood_score = _clamp(mood_score, -1.0, 1.0)
    risk_scores = {key: _clamp(value, 0.0, 1.0) for key, value in risk_scores.items()}
    play_probs = _normalize_play_probs(play_probs)

    return {
        "mood_score": mood_score,
        "play_probs": play_probs,
        "risk_scores": risk_scores,
    }

def build_feature_result(
    doc_id: str,
    asset_key: str,
    clean_text: str,
    aux_tags: List[str],
    mood_score: float,
    play_probs: Dict[str, float],
    risk_scores: Dict[str, float],
) -> Dict[str, Any]:
    """
    aggregator가 사용하기 좋게 feature 결과를 표준 포맷으로 만든다.
    """
    return {
        "doc_id": doc_id,
        "asset_key": asset_key,
        "clean_text": clean_text,
        "aux_tags": aux_tags,
        "mood_score": mood_score,
        "play_probs": play_probs,
        "risk_scores": risk_scores,
    }

def extract_features(doc : Dict[str, Any]) -> Dict[str, Any]:
    """
    문서 하나를 받아 feature 하나를 반환하는 extractor 메인 함수.
    """
    
    doc_id = str(doc.get("doc_id", ""))
    asset_key = str(doc.get("asset_key", ""))
    raw_text = str(doc.get("text", ""))

    clean_text = preprocess_text(raw_text)
    aux_tags = extract_aux_tag(clean_text)
    inferred = infer_mock_features(clean_text, aux_tags)

    return build_feature_result(
        doc_id=doc_id,
        asset_key=asset_key,
        clean_text=clean_text,
        aux_tags=aux_tags,
        mood_score=inferred["mood_score"],
        play_probs=inferred["play_probs"],
        risk_scores=inferred["risk_scores"],
    )

if __name__ == "__main__":
    sample_doc = {
        "doc_id": "doc_001",
        "asset_key": "BTC",
        "text": "에어드랍 이벤트 전에 다들 물량 모으는 느낌. 근데 유동성은 좀 얕아서 추격은 조심.",
        "source": "moltbook",
        "published_at": "2026-04-16T10:00:00",
        "engagement": {
            "views": 1200,
            "likes": 80,
            "reposts": 10,
            "comments": 12,
        },
    }

if __name__ == "__main__":
    sample_doc = {
        "doc_id": "doc_001",
        "asset_key": "BTC",
        "text": "에어드랍 이벤트 전에 다들 물량 모으는 느낌. 근데 유동성은 좀 얕아서 추격은 조심.",
        "source": "moltbook",
        "published_at": "2026-04-16T10:00:00",
        "engagement": {
            "views": 1200,
            "likes": 80,
            "reposts": 10,
            "comments": 12,
        },
    }

if __name__ == "__main__":
    sample_doc = {
        "doc_id": "doc_001",
        "asset_key": "BTC",
        "text": "에어드랍 이벤트 전에 다들 물량 모으는 느낌. 근데 유동성은 좀 얕아서 추격은 조심.",
        "source": "moltbook",
        "published_at": "2026-04-16T10:00:00",
        "engagement": {
            "views": 1200,
            "likes": 80,
            "reposts": 10,
            "comments": 12,
        },
    }

    result = extract_features(sample_doc)
    print(result)