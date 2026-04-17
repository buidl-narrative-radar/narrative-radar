# Narrative Radar Backend

Narrative Radar Backend는 크립토 디스커션 속에 분산된 정보를 구조화하여,
각 자산에 대한 군중의 실제 행동 패턴(Market Posture)을 추출하는 엔진이다.

우리는 감정을 분석하는 것이 아니라,
분산된 정보를 집계하여 군중의 행동을 드러낸다.

---

## 1. 문제 정의

크립토 시장은 텍스트로 가득하다.

- 기다려야 한다
- 여전히 bullish 하다
- 좋아 보인다

하지만 시장은 말이 아니라 행동으로 움직인다.

Narrative Radar는 사람들이 실제로 무엇을 하고 있는지를 추출한다.

---

## 2. 이론적 기반 (Hayek)

하이에크의 핵심은 다음과 같다.

- 정보는 분산되어 있다
- 각 참여자는 부분 정보만 가진다
- 시장은 이 정보들의 집합이다

즉 시장은 하나의 의견이 아니라,
분산된 판단들의 집계 결과이다.

Narrative Radar는 이 구조를 그대로 시스템으로 구현한다.

---

## 3. 시스템 개념

각 문서는 하나의 정보 조각이다.

- 개별 문서 → 부분 정보
- 전체 문서 → 시장 상태

이렇게 변환하여 군중의 행동을 복원한다.

---

## 4. 데이터 플로우

mock discussion docs  
→ adapter (정규화)  
→ LLM feature extractor  
→ document-level features  
→ asset 기준 그룹화  
→ state aggregator  
→ asset-level state  
→ LLM output generator  
→ frontend-ready JSON / API  

---

## 5. 처리 과정

Step 1. Mock Docs

각 문서는 다음 정보를 가진다.

- doc_id
- asset_key
- text
- published_at
- engagement

---

Step 2. Adapter

markdown 기반 mock 데이터를 내부 포맷으로 변환한다.

raw docs → normalized docs

---

Step 3. Feature Extraction (LLM)

각 문서에서 다음을 추출한다.

- mood
- playbook
- risk

---

Step 4. Aggregation

같은 asset끼리 묶어서 다음을 생성한다.

- mood_label
- playbook_label
- risk_flags
- confidence

---

Step 5. Output Generation (LLM)

최종 summary 문장을 생성한다.

이 summary는 LLM이 직접 작성한다.

---

## 6. 핵심 출력

각 asset마다 다음 정보를 제공한다.

- Mood
- Playbook
- Risk Flags
- Summary (LLM 생성)

---

## 7. 서버 구조

app 폴더에는 다음이 포함된다.

- adapters
- feature_extractor
- state_aggregator
- output

그 외 파일:

- main.py
- api.py
- mock_data

---

## 8. API 사용법

서버 상태 확인

GET /

응답:
{ "ok": true }

---

전체 asset 조회

GET /assets

---

특정 asset 조회

GET /asset/BNB

---

## 9. 응답 구조

예시:

{
  "asset_key": "bsc:BNB",
  "symbol": "BNB",
  "mood_label": "조심스러운 낙관",
  "playbook_label": "이벤트 선점",
  "risk_flags": ["유동성", "포인트 경쟁"],
  "summary": "BNB participants lean into event front-running...",
  "confidence_score": 0.50,
  "confidence_label": "Medium"
}

---

## 10. 프런트 연결 방법

프런트는 API를 호출해서 데이터를 가져오면 된다.

예시:

fetch("https://narrative-radar-backend.onrender.com/asset/BNB")
  .then(res => res.json())
  .then(data => {
    console.log(data);
  });

---

## 11. 프런트에서 사용할 필드

프런트는 다음 필드를 사용하면 된다.

- symbol
- mood_label
- playbook_label
- risk_flags
- summary
- confidence_label

중요:

summary는 백엔드에서 LLM이 생성한 문장이다.
프런트는 그대로 출력하면 된다.

---

## 12. 차별점

기존 방식은 단순 sentiment 분석이다.

- bullish / bearish
- positive / negative

Narrative Radar는 다음을 본다.

- 군중이 실제로 어떤 전략을 쓰는가
- 경쟁이 심해지는가
- 실행 리스크가 커지는가

즉 행동 기반 분석이다.

---

## 13. 현재 상태 (MVP)

- mock 데이터 기반
- LLM feature extraction
- aggregation
- API 제공 완료

---

## 14. 한 줄 요약

Narrative Radar는 분산된 정보를 집계하여
군중의 실제 행동을 드러내는 엔진이다.
