# 📊 Narrative Radar – Data Flow (MVP)

## 1. 개요

Narrative Radar는 다양한 소스에서 수집된 시장 담론 텍스트를 분석하여
각 자산의 **시장 상태(Mood / Playbook / Risk)**를 추출하는 시스템이다.

현재 MVP 단계에서는 **데이터 수집 방식(API vs 크롤링)**이 확정되지 않았으며,
이를 고려하여 **유연한 데이터 파이프라인 구조**를 설계한다.

---

## 2. 전체 데이터 흐름

```plaintext
[External Source (Moltbook 등)]
        ↓
[Raw Data]
        ↓
[Adapter / Normalization Layer]
        ↓
[Internal Doc Format]
        ↓
[Feature Extractor]
        ↓
[Feature Vectors]
        ↓
[State Aggregator]
        ↓
[Final Asset State Output]
```

---

## 3. 단계별 설명

### 3.1 External Source (미정)

현재 고려 중인 데이터 수집 방식:

* API (가능한 경우)
* 웹 크롤링

이 단계의 특징:

* 데이터 형식이 일정하지 않음
* 텍스트만 존재할 수도 있음
* 메타데이터가 일부 누락될 수 있음

---

### 3.2 Raw Data

외부에서 가져온 원본 데이터

예시:

* 단일 텍스트 문자열
* HTML에서 추출된 텍스트
* JSON 구조 데이터

이 단계에서는 **가공 없이 그대로 유지**

---

### 3.3 Adapter / Normalization Layer

역할:

> 외부 데이터 → 내부 표준 문서 구조로 변환

파일:

```
app/adapters/moltbook_adapter.py
```

출력 형식 (Internal Doc):

```python
{
  "doc_id": str,
  "asset_key": str,
  "text": str,
  "source": "moltbook",
  "published_at": str | None,
  "engagement": {
    "views": int,
    "likes": int,
    "reposts": int,
    "comments": int
  }
}
```

특징:

* 누락된 값은 기본값으로 채움
* asset_key는 추정 또는 raw 데이터에서 추출
* 다양한 소스를 동일 구조로 통일

---

### 3.4 Feature Extractor

파일:

```
app/feature_extractor/extractor.py
```

역할:

> 텍스트 → 구조화된 feature로 변환

출력:

```python
{
  "doc_id": str,
  "asset_key": str,
  "clean_text": str,
  "aux_tags": List[str],
  "mood_score": float,
  "play_probs": Dict[str, float],
  "risk_scores": Dict[str, float]
}
```

현재 방식:

* Rule-based mock extractor

향후:

* LLM 기반 feature extraction으로 교체 예정

---

### 3.5 State Aggregator

파일:

```
app/state_aggregator/aggregator.py
```

역할:

> 여러 문서의 feature를 하나의 자산 상태로 집계

핵심 연산:

```
S_A = Σ(w_i * f_i) / Σ(w_i)
```

출력:

```python
{
  "asset_key": str,
  "mood_label": str,
  "playbook_label": str,
  "risk_flags": List[str],
  "confidence": float,
  "raw": {...}
}
```

---

## 4. 설계 원칙

### 4.1 입력과 분석 로직 분리

* 외부 데이터 형식에 의존하지 않도록 adapter 분리
* extractor는 항상 동일한 입력 구조를 받음

---

### 4.2 확장성

향후 추가 가능:

* Twitter adapter
* Reddit adapter
* Binance Square adapter

---

### 4.3 LLM 교체 가능 구조

현재:

```
infer_mock_features()
```

향후:

```
infer_llm_features()
```

→ extractor 내부에서 교체 가능

---

## 5. MVP 범위

현재 구현 범위:

* mock 데이터 기반 end-to-end 실행
* rule-based feature extraction
* weighted aggregation
* label 생성

미구현:

* 실제 데이터 수집 (API / 크롤링)
* LLM 기반 feature extraction
* 실시간 데이터 파이프라인

---

## 6. 향후 계획

1. Moltbook 데이터 수집 방식 결정 (API vs 크롤링)
2. adapter 구현 및 raw → doc 변환 테스트
3. LLM 기반 extractor 도입
4. feature calibration dataset 구축
5. 실시간 파이프라인 구축

---

## 7. 한 줄 요약

> Narrative Radar는
> “분산된 시장 담론을 수집 → 구조화 → 집계하여
> 자산별 행동 상태로 변환하는 시스템”이다.
