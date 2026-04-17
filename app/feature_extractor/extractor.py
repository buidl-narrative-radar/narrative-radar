import json
import os
import re
from typing import Any, Dict, List

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def preprocess_text(text: str) -> str:
    """
    Raw text를 분석 가능한 clean_text로 정리한다.

    처리:
    - URL 제거
    - 공백 정리
    - 앞뒤 공백 제거
    """
    if not isinstance(text, str):
        return ""

    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_aux_tags(text: str) -> List[str]:
    """
    간단한 보조 태그 추출.
    LLM 모드에서도 참고용으로 유지한다.
    """
    if not isinstance(text, str):
        return []

    lowered = text.lower()
    tags: List[str] = []

    crowd_keywords = [
        "crowd", "crowding", "everyone", "urgent", "people",
        "다들", "몰린", "유입", "물량"
    ]
    wait_keywords = [
        "wait", "waiting", "pullback", "cleaner reset", "observe",
        "관망", "기다", "지켜보"
    ]
    warning_keywords = [
        "fragile", "worse", "risk", "danger", "late entry",
        "위험", "조심", "fragile", "불편"
    ]
    liquidity_keywords = [
        "liquidity", "thin", "spread", "depth", "slippage",
        "유동성", "스프레드", "얕"
    ]
    event_keywords = [
        "front-run", "catalyst", "before others", "early positioning",
        "이벤트", "선점", "미리", "먼저"
    ]

    if any(k in lowered for k in crowd_keywords):
        tags.append("crowd")
    if any(k in lowered for k in wait_keywords):
        tags.append("wait_signal")
    if any(k in lowered for k in warning_keywords):
        tags.append("warning")
    if any(k in lowered for k in liquidity_keywords):
        tags.append("liquidity")
    if any(k in lowered for k in event_keywords):
        tags.append("event")

    return tags


def normalize_play_probs(play_probs: Dict[str, float]) -> Dict[str, float]:
    """
    play_probs 합이 1이 되도록 정규화.
    """
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
    """
    risk_scores를 0~1 범위로 클램프.
    """
    keys = ["liquidity", "point_competition", "security", "execution"]
    return {
        k: min(max(float(risk_scores.get(k, 0.0)), 0.0), 1.0)
        for k in keys
    }


def infer_mock_features(text: str, aux_tags: List[str]) -> Dict[str, Any]:
    """
    규칙 기반 mock feature 추론.
    비교 / fallback 용도로 유지한다.
    """
    mood_score = 0.0

    play_probs = {
        "small_repeat_trades": 0.2,
        "wait": 0.2,
        "event_front_run": 0.2,
        "no_chase": 0.2,
    }

    risk_scores = {
        "liquidity": 0.0,
        "point_competition": 0.0,
        "security": 0.0,
        "execution": 0.0,
    }

    lowered = text.lower()

    positive_keywords = ["strong", "constructive", "optimistic", "upside", "healthy"]
    negative_keywords = ["fear", "fragile", "worse", "risk", "danger", "uncomfortable"]

    mood_score += 0.15 * sum(1 for k in positive_keywords if k in lowered)
    mood_score -= 0.15 * sum(1 for k in negative_keywords if k in lowered)

    if "crowd" in aux_tags:
        mood_score += 0.10
        play_probs["event_front_run"] += 0.12
        risk_scores["point_competition"] += 0.15

    if "wait_signal" in aux_tags:
        play_probs["wait"] += 0.25
        play_probs["no_chase"] += 0.10

    if "event" in aux_tags:
        mood_score += 0.20
        play_probs["event_front_run"] += 0.55
        risk_scores["execution"] += 0.20

    if "warning" in aux_tags:
        mood_score -= 0.20
        play_probs["no_chase"] += 0.18
        play_probs["wait"] += 0.08
        risk_scores["execution"] += 0.20

    if "liquidity" in aux_tags:
        mood_score -= 0.15
        play_probs["no_chase"] += 0.12
        risk_scores["liquidity"] += 0.40

    # execution 관련 키워드 직접 반영
    if "execution risk" in lowered or "entry quality" in lowered or "timing" in lowered:
        risk_scores["execution"] += 0.20

    # security 관련 키워드
    if "security" in lowered or "exploit" in lowered or "smart contract" in lowered:
        risk_scores["security"] += 0.50

    mood_score = max(min(mood_score, 1.0), -1.0)
    play_probs = normalize_play_probs(play_probs)
    risk_scores = clamp_risk_scores(risk_scores)

    return {
        "mood_score": mood_score,
        "play_probs": play_probs,
        "risk_scores": risk_scores,
    }


def infer_llm_features(text: str) -> Dict[str, Any]:
    """
    LLM 기반 feature 추론.
    text를 읽고 mood / play / risk를 구조화 JSON으로 반환한다.
    """
    prompt = f"""
You are analyzing a crypto market discussion post.

Your goal is NOT to extract the author's advice.

Your goal is to infer the actual crowd behavior and market posture described in the text.

Return ONLY valid JSON:

{{
  "mood_score": float,
  "play_probs": {{
    "small_repeat_trades": float,
    "wait": float,
    "event_front_run": float,
    "no_chase": float
  }},
  "risk_scores": {{
    "liquidity": float,
    "point_competition": float,
    "security": float,
    "execution": float
  }}
}}

Core rule:
You must infer what the crowd is ACTUALLY doing, not what the author recommends.

Even if the text says:
- wait
- be cautious
- avoid chasing

the actual market behavior may still be:
- event_front_run

Interpretation principles:

1. If the market is:
- still constructive
- still has upside
- but entries are getting worse
- crowd is getting urgent

then event_front_run should often be significant.

2. If:
- people are competing for early positioning
- entries feel worse because many are trying to enter early

then event_front_run and execution risk should both be significant.

3. Use "wait" only if the dominant behavior is truly patience / observation.

4. Use "no_chase" only if the text mainly describes avoiding late entry behavior.

Mood:
- optimistic but fragile -> around 0.2 to 0.5
- mixed -> around -0.1 to 0.1
- fear dominant -> below -0.2
- euphoric / overheated -> above 0.6

Risk:
You MUST assign risk_scores even if not directly stated.

Infer from context:
- liquidity: fragile entries, thinning liquidity, weak depth, worsening entry quality
- point_competition: too many people crowding the same trade/opportunity
- security: exploit / contract / trust risk
- execution: hard timing, crowded positioning, poor entry quality, front-run pressure

Examples:

Example 1
Text:
"BNB still looks constructive, but the crowd is getting more aggressive and new entries feel worse. Earlier entries were clean, now people sound more urgent."

Output:
{{
  "mood_score": 0.35,
  "play_probs": {{
    "small_repeat_trades": 0.10,
    "wait": 0.20,
    "event_front_run": 0.50,
    "no_chase": 0.20
  }},
  "risk_scores": {{
    "liquidity": 0.40,
    "point_competition": 0.30,
    "security": 0.00,
    "execution": 0.60
  }}
}}

Example 2
Text:
"This setup still works, but I prefer waiting for a better entry."

Output:
{{
  "mood_score": 0.20,
  "play_probs": {{
    "small_repeat_trades": 0.10,
    "wait": 0.55,
    "event_front_run": 0.10,
    "no_chase": 0.25
  }},
  "risk_scores": {{
    "liquidity": 0.20,
    "point_competition": 0.10,
    "security": 0.00,
    "execution": 0.40
  }}
}}

Example 3
Text:
"Everyone is trying to position before the next move. Timing is getting harder."

Output:
{{
  "mood_score": 0.30,
  "play_probs": {{
    "small_repeat_trades": 0.10,
    "wait": 0.10,
    "event_front_run": 0.60,
    "no_chase": 0.20
  }},
  "risk_scores": {{
    "liquidity": 0.30,
    "point_competition": 0.40,
    "security": 0.00,
    "execution": 0.70
  }}
}}

Now analyze this text:

\"\"\"
{text}
\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a precise crypto market text analyzer. Return JSON only."
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {content}") from e

    mood_score = float(parsed.get("mood_score", 0.0))
    mood_score = max(min(mood_score, 1.0), -1.0)

    play_probs = normalize_play_probs(parsed.get("play_probs", {}))
    risk_scores = clamp_risk_scores(parsed.get("risk_scores", {}))

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
    최종 feature dict 생성.
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


def extract_features(doc: Dict[str, Any], mode: str = "llm") -> Dict[str, Any]:
    """
    문서 1개를 받아 feature를 추출한다.

    mode:
    - "llm": LLM 기반 추론
    - "mock": 규칙 기반 mock 추론
    """
    doc_id = str(doc.get("doc_id", ""))
    asset_key = str(doc.get("asset_key", ""))
    raw_text = str(doc.get("text", ""))

    clean_text = preprocess_text(raw_text)
    aux_tags = extract_aux_tags(clean_text)

    if mode == "llm":
        print(f" LLM CALLED: {doc_id}")
        inferred = infer_llm_features(clean_text)
    else:
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
        "asset_key": "bsc:BNB",
        "text": (
            "BNB still looks strong, but entries are getting worse. "
            "The crowd is clearly less comfortable than before."
        ),
    }

    print("=== MOCK MODE ===")
    print(extract_features(sample_doc, mode="mock"))

    # API 키가 있을 때만 테스트
    if os.getenv("OPENAI_API_KEY"):
        print("=== LLM MODE ===")
        print(extract_features(sample_doc, mode="llm"))