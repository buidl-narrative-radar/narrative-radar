# Narrative Radar

**Narrative Radar는 크립토 디스커션 속에 분산된 정보를 모아, 군중의 실제 행동 패턴을 추출하는 market posture engine이다.**

> 우리는 감정을 분석하는 것이 아니라,  
> **분산된 정보를 집계해 행동을 드러낸다.**

---

## 1. 문제 정의

크립토 시장은 텍스트로 가득하다.

- “기다려야 한다”
- “여전히 bullish”
- “좋아 보인다”

하지만 실제 시장은 말이 아니라 행동으로 움직인다.

> 사람들은 “대기”를 말하면서도  
> 이미 선점(front-run)하고 있을 수 있다.

기존 sentiment 분석은:
- 긍정 / 부정
- bullish / bearish

만을 다루기 때문에  
**실제 행동 구조를 보여주지 못한다.**

---

## 2. 이론적 기반: 하이에크 (Hayek)

Narrative Radar는 하이에크의 **분산 정보 이론**을 기술적으로 구현한다.

### 하이에크의 핵심 주장

> 시장 정보는 중앙에 존재하지 않는다.  
> 각 개인이 부분적인 정보를 가지고 있으며,  
> 이 정보는 행동 속에 반영된다.

즉:

- 정보는 텍스트로 완전하게 표현되지 않는다
- **행동(선택, 포지셔닝)에 녹아 있다**
- 전체 시장 상태는 이 행동들을 집계해야만 보인다

---

### 제품에 적용

Narrative Radar는 다음을 수행한다:

- 개별 텍스트 → 부분 정보
- 각 문서 → 부분적 시그널
- 전체 문서 집합 → 시장 상태

> ❗ 즉, 이 시스템은  
> **“분산된 정보를 행동 기반으로 재구성하는 엔진”이다**

---

## 3. 핵심 아이디어

같은 sentiment라도 행동은 다르다.

예:

- BNB → “기다리자”지만 실제로는 선점 중
- CAKE → 실제로 대기 중

Narrative Radar는 이 차이를 잡는다.

---

## 4. 데이터 흐름 (Data Flow)


mock discussion docs (분산된 정보)
↓
adapter (정규화)
↓
LLM feature extractor (부분 정보 해석)
↓
document-level features (부분 시그널)
↓
group by asset (시장 단위 구성)
↓
state aggregator (정보 집계)
↓
asset-level state (시장 상태)
↓
LLM output generator (해석)
↓
JSON + summary (사용자 출력)


---

## 5. 처리 과정

### Step 1. 입력 (분산된 정보)

각 문서는 시장 참여자의 부분 정보이다.

```text
asset_key
text
timestamp
engagement
Step 2. Feature 추출 (부분 정보 → 구조화)

LLM이 각 문서에서 다음을 추출:

mood_score
playbook probabilities
risk_scores

출력 예:

{
  "mood_score": 0.30,
  "play_probs": {
    "wait": 0.20,
    "event_front_run": 0.50
  },
  "risk_scores": {
    "liquidity": 0.40,
    "execution": 0.60
  }
}
Step 3. 그룹화 (시장 단위)

문서들을 asset 기준으로 묶는다.

BNB → 하나의 시장 상태
CAKE → 또 다른 시장 상태
Step 4. 집계 (하이에크 핵심 단계)

여러 문서의 정보를 집계하여
시장 전체 상태를 복원한다

출력:

{
  "asset_key": "bsc:BNB",
  "mood_label": "조심스러운 낙관",
  "playbook_label": "이벤트 선점",
  "risk_flags": ["유동성", "실행 리스크"],
  "confidence": 0.50
}

이 단계가 핵심이다:

❗ 분산된 정보를 집계하여
단일한 시장 상태를 만든다

Step 5. 해석 (사용자 출력)

최종 상태를 자연어로 변환

예:

대기라고 말하지만 이미 선점 중
경쟁 심화
진입 난이도 상승
6. 핵심 출력

각 asset에 대해:

Mood

군중의 상태

Playbook

군중의 행동

Risk

시장 내 위험 구조

7. 프로젝트 구조
app/
  adapters/            # 데이터 정규화
  feature_extractor/   # LLM 기반 feature 추출
  state_aggregator/    # 정보 집계 (핵심)
  evaluation/          # 성능 검증
  output/              # 결과 생성

mock_data/
main.py
8. 실행 방법
pip install -r requirements.txt
python3 main.py
9. 결과
1) 터미널 출력
평가 결과
asset 상태
summary
2) output.json 생성

프런트에서 바로 사용 가능

[
  {
    "asset_key": "bsc:BNB",
    "symbol": "BNB",
    "mood_label": "조심스러운 낙관",
    "playbook_label": "이벤트 선점",
    "risk_flags": ["유동성", "포인트 경쟁", "실행 리스크"],
    "summary": "...",
    "confidence_label": "Medium"
  }
]
10. 기존 방식과 차이

기존:

감정 분석
bullish / bearish
sentiment score

Narrative Radar:

분산된 정보 집계
행동 기반 해석
군중 전략 분석
리스크 구조 파악
11. 한 줄 요약

Narrative Radar는
분산된 시장 정보를 집계하여
군중의 실제 행동을 보여주는 시스템이다.
