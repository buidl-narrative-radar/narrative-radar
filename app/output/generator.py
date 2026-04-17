import os
from typing import Dict, Any

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_asset_summary(state: Dict[str, Any]) -> str:
    """
    asset_state -> 짧고 날카로운 market summary (최종 버전)
    """

    asset_key = state.get("asset_key", "UNKNOWN")
    asset = asset_key.split(":")[-1] if ":" in asset_key else asset_key

    mood_label = state.get("mood_label", "알 수 없음")
    playbook_label = state.get("playbook_label", "알 수 없음")
    risk_flags = state.get("risk_flags", [])
    confidence = state.get("confidence", 0.0)

    raw = state.get("raw", {})
    raw_mood = raw.get("mood", 0.0)
    raw_play = raw.get("play", {})
    raw_risk = raw.get("risk", {})

    risk_text = ", ".join(risk_flags) if risk_flags else "뚜렷한 리스크 없음"

    prompt = f"""
Asset: {asset}

Structured signal:
- Mood: {mood_label}
- Playbook: {playbook_label}
- Risks: {risk_text}
- Confidence: {confidence}

Raw:
- Mood score: {raw_mood}
- Play: {raw_play}
- Risk: {raw_risk}

Write a sharp 2-sentence market interpretation.

Rules:
- Focus on what is actually happening in positioning
- Highlight tension if present (e.g. waiting vs front-running)
- Emphasize what makes this asset different from others
- Avoid repeating the same phrasing across assets
- Vary sentence openings; avoid repeating patterns like "Positioning in X"
- Avoid generic phrases:
  - "the market shows"
  - "participants are"
  - "sentiment is"
- Do NOT start every sentence with "traders" or "the crowd"
- Avoid exaggerated predictions like:
  - "will crash"
  - "sharp reversal"
  - "will fail"
- Prefer grounded phrasing like:
  - "keeps conviction fragile"
  - "leaves little room for error"
  - "raises the cost of being early"
- Mention risks naturally
- Reflect confidence subtly (moderate / not strong)
- Keep it tight (max 2 sentences)
- Output only plain text

Tone:
- analytical
- grounded
- slightly sharp
- like a trading desk note
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise crypto market interpreter. "
                    "Write concise, grounded summaries of crowd behavior."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.45,
        max_tokens=120,
    )

    return response.choices[0].message.content.strip()