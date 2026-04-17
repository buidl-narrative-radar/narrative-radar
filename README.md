# Narrative Radar Backend

**Narrative Radar Backend**는 크립토 디스커션 속에 분산된 정보를 구조화하여,  
각 자산에 대한 **군중의 실제 행동 패턴(Market Posture)** 을 추출하고 프런트에 전달하는 백엔드 엔진이다.

> 우리는 감정을 읽는 것이 아니라,  
> **분산된 정보를 집계해 군중의 행동을 드러낸다.**

---

## 1. 프로젝트 개요

크립토 시장에서는 수많은 글, 댓글, 디스커션이 올라온다.

사람들은 다음과 같이 말한다.

- “기다려야 한다”
- “여전히 bullish 하다”
- “아직 괜찮아 보인다”

하지만 실제 시장에서 중요한 것은  
**사람들이 무엇을 말하는가**가 아니라  
**무엇을 하고 있는가**이다.

Narrative Radar Backend는 이 문제를 해결하기 위해:

- discussion text를 읽고
- 자산별로 군중의 상태를 추출한 뒤
- 최종적으로 프런트가 바로 사용할 수 있는 JSON과 summary를 제공한다.

---

## 2. 이론적 기반: 하이에크(Hayek)

이 백엔드의 핵심 철학은 하이에크의 **분산 정보 이론**에 기반한다.

### 하이에크의 핵심 주장

하이에크에 따르면 시장 정보는 중앙에 완전히 모여 있지 않다.

- 각 개인은 부분적인 정보만 가진다
- 이 정보는 각자의 판단과 행동에 반영된다
- 전체 시장 상태는 이 분산된 정보들을 집계해야만 드러난다

즉:

> 시장은 “하나의 문장”으로 이해되는 것이 아니라,  
> **수많은 참여자의 부분 정보와 행동이 합쳐져 형성된다**

---

## 3. Narrative Radar가 하이에크를 어떻게 구현하는가

Narrative Radar Backend는 각 discussion 문서를  
**시장 참여자의 부분 정보 조각**으로 취급한다.

각 문서에서:

- mood (분위기)
- playbook (행동 패턴)
- risk (잠재 리스크)

를 추출하고,  
이를 자산 기준으로 집계하여 **전체 시장 상태**를 만든다.

즉:

- 개별 텍스트 = 부분 정보
- 여러 텍스트의 집합 = 시장 상태
- 최종 출력 = 군중의 실제 행동 패턴

이 시스템은 단순 감성 분석이 아니라:

> **분산된 시장 정보를 구조화하여,  
> 군중의 행동을 복원하는 엔진**

이다.

---

## 4. 핵심 출력

각 asset마다 다음 4가지를 만든다.

### 1) Mood
군중의 전반적 상태

예:
- 조심스러운 낙관
- 과열
- 혼잡
- 공포 속 반등 시도

### 2) Playbook
군중이 실제로 취하고 있는 전략

예:
- 이벤트 선점
- 대기
- 추격 금지
- 소액 다회전

### 3) Risk Flags
현재 posture 아래에서 함께 형성되는 위험

예:
- 유동성
- 포인트 경쟁
- 실행 리스크
- 보안

### 4) Summary
최종적으로 LLM이 생성하는 자연어 문장  
(프런트에서 그대로 출력 가능)

---

## 5. 데이터 플로우 (Data Flow)

```text
mock discussion docs
        ↓
adapter (문서 정규화)
        ↓
LLM feature extractor
        ↓
document-level features
        ↓
group by asset
        ↓
state aggregator
        ↓
asset-level state
        ↓
LLM output generator
        ↓
frontend-ready JSON / API response
6. 처리 과정 상세
Step 1. Mock Discussion Docs

현재 MVP에서는 mock 문서를 사용한다.

각 문서는 대략 다음 정보를 가진다.

doc_id
asset_key
text
published_at
engagement

예:

bsc:BNB
bsc:CAKE
bsc:LISTA
Step 2. Adapter

app/adapters/moltbook_adapter.py

markdown 기반 mock 데이터를 엔진 내부 포맷으로 정규화한다.

즉:

raw mock docs
→
normalized documents
Step 3. Feature Extraction

app/feature_extractor/extractor.py

각 문서마다 LLM을 사용해 다음을 추출한다.

mood_score
play_probs
risk_scores

예:

{
  "mood_score": 0.35,
  "play_probs": {
    "small_repeat_trades": 0.10,
    "wait": 0.20,
    "event_front_run": 0.50,
    "no_chase": 0.20
  },
  "risk_scores": {
    "liquidity": 0.40,
    "point_competition": 0.30,
    "security": 0.00,
    "execution": 0.60
  }
}
Step 4. Group by Asset

main.py

문서 feature들을 asset_key 기준으로 묶는다.

예:

bsc:BNB → 10 docs
bsc:CAKE → 10 docs
...
Step 5. State Aggregation

app/state_aggregator/aggregator.py

같은 자산에 속한 문서들의 feature를 집계하여:

최종 mood
최종 playbook
risk flags
confidence

를 생성한다.

예:

{
  "asset_key": "bsc:BNB",
  "mood_label": "조심스러운 낙관",
  "playbook_label": "이벤트 선점",
  "risk_flags": ["유동성", "포인트 경쟁", "실행 리스크"],
  "confidence": 0.50
}
Step 6. Output Generation

app/output/generator.py

최종 asset state를 바탕으로 LLM이 자연어 summary를 생성한다.

예:

BNB participants lean into event front-running...
Elevated execution and liquidity risks...

이 summary는 프런트에서 그대로 출력 가능하다.

7. 백엔드 구조
app/
  adapters/
    moltbook_adapter.py

  feature_extractor/
    extractor.py

  state_aggregator/
    aggregator.py

  evaluation/
    evaluate.py

  output/
    generator.py
    templates.py

mock_data/
  moltbook_mock_docs.md

main.py
api.py
requirements.txt
output.json
8. 실행 방식

이 백엔드는 두 가지 방식으로 동작한다.

1) 배치 실행 (main.py)

전체 mock docs를 기반으로 전체 자산 상태를 생성하고
output.json을 만든다.

python3 main.py
2) API 실행 (api.py)

FastAPI + Render를 통해 프런트가 직접 호출할 수 있게 한다.

uvicorn api:app --reload
9. 서버 연결 방식

이 백엔드는 Render에 배포되어 있고,
프런트는 이 서버를 통해 데이터를 가져간다.

루트 확인
https://narrative-radar-backend.onrender.com/

응답:

{"ok": true}
전체 asset 조회
GET https://narrative-radar-backend.onrender.com/assets
특정 asset 조회
GET https://narrative-radar-backend.onrender.com/asset/BNB
10. API 응답 구조

특정 asset 호출 시 응답 예시:

{
  "asset_key": "bsc:BNB",
  "symbol": "BNB",
  "mood_label": "조심스러운 낙관",
  "playbook_label": "이벤트 선점",
  "risk_flags": ["유동성", "포인트 경쟁", "실행 리스크"],
  "summary": "BNB participants lean into event front-running while balancing a notable share of cautious waiting...",
  "confidence_score": 0.501,
  "confidence_label": "Medium"
}
11. 프런트에서는 이렇게 연결하면 된다

프런트는 JSON 자체를 사용자에게 보여주는 것이 아니라,
API 응답을 받아 UI 카드나 Ask AI 박스에 렌더링하면 된다.

예시 1: 특정 asset 하나 가져오기
fetch("https://narrative-radar-backend.onrender.com/asset/BNB")
  .then((res) => res.json())
  .then((data) => {
    console.log(data);
  });
예시 2: 전체 asset 리스트 가져오기
fetch("https://narrative-radar-backend.onrender.com/assets")
  .then((res) => res.json())
  .then((data) => {
    console.log(data);
  });
12. 프런트에서 사용하면 되는 필드

프런트는 아래 필드를 그대로 사용하면 된다.

asset_key
symbol
mood_label
playbook_label
risk_flags
summary
confidence_score
confidence_label
13. 프런트 렌더링 예시
카드 UI
제목 → symbol
mood badge → mood_label
playbook 텍스트 → playbook_label
risk chips → risk_flags
설명 문장 → summary
confidence 표시 → confidence_label

즉:

최종 문장은 프런트가 만드는 것이 아니라,
백엔드의 output LLM이 생성한 summary를 그대로 출력하면 된다.

14. 이 백엔드의 핵심 차별점

기존 방식:

bullish / bearish
positive / negative
sentiment score

Narrative Radar Backend:

사람들이 기다린다고 말하지만 실제로는 선점 중인지
crowd가 이미 경쟁 상태인지
entry quality가 나빠지고 있는지
execution risk가 커지고 있는지

즉:

이 백엔드는 sentiment analyzer가 아니라
crowd behavior engine이다.

15. 현재 MVP 범위

현재 MVP는 다음을 목표로 한다.

mock docs 기반 ingestion
LLM 기반 feature extraction
asset-level aggregation
output LLM summary 생성
frontend API 제공
16. 현재 서버 운영 방식

현재 Render 서버는:

API로 요청을 받고
특정 asset 기준으로 백엔드를 실행하고
해당 asset에 대한 최종 상태와 LLM summary를 반환한다

즉:

프런트 → asset 요청
백엔드 → 해당 asset 계산
LLM → summary 생성
프런트 → summary 출력
17. 향후 확장 방향
real-time ingestion
실제 Moltbook / Binance discussion source 연결
historical tracking
refresh endpoint
alert system
watchlist personalization
production-grade caching
18. 한 줄 요약

Narrative Radar Backend는
분산된 시장 정보를 집계해
군중의 실제 행동을 프런트에 전달하는 엔진이다.
