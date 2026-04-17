# Narrative Radar

**Narrative Radar는 크립토 디스커션 데이터를 읽고, 군중이 실제로 어떤 행동을 하고 있는지 추출하는 엔진이다.**

> 우리는 감정을 읽는 게 아니라, 행동을 추출한다.  
> (**We don’t read sentiment. We extract behavior.**)

---

## 1. 문제 정의

크립토 시장에서는 사람들이 다음과 같이 말한다.

- “지금은 기다려야 한다”
- “여전히 bullish 하다”
- “좋아 보인다”

하지만 실제로 중요한 것은  
**사람들이 무엇을 말하는가가 아니라, 무엇을 하고 있는가이다.**

기존 sentiment 분석은:
- 긍정 / 부정
- bullish / bearish

정도만 보여주기 때문에  
**말과 행동의 괴리**를 잡아내지 못한다.

---

## 2. 해결 방식

Narrative Radar는 discussion 데이터를 읽어서 다음 3가지를 추출한다.

### 1) Mood (분위기)
군중의 전반적인 상태

예:
- 조심스러운 낙관
- 과열
- 혼잡
- 공포 속 반등 시도

---

### 2) Playbook (행동 패턴)
군중이 실제로 취하고 있는 전략

예:
- 이벤트 선점 (front-run)
- 대기
- 추격 금지
- 소액 다회전

---

### 3) Risk (리스크)
현재 상황에서 함께 올라오는 위험 요소

예:
- 유동성
- 포인트 경쟁
- 실행 리스크
- 보안

---

## 3. 핵심 아이디어

같은 sentiment라도 행동은 다를 수 있다.

예:

- A 토큰 → “기다리자”라고 말하지만 실제로는 **선점 중**
- B 토큰 → 실제로 **대기 중**

Narrative Radar는 이 차이를 잡는다.

---

## 4. 데이터 흐름 (Data Flow)


mock discussion docs
↓
adapter (문서 정규화)
↓
LLM feature extractor
↓
문서 단위 feature
↓
asset 기준 그룹화
↓
state aggregator
↓
asset 단위 상태 생성
↓
LLM 출력 생성
↓
JSON + 자연어 summary


---

## 5. 처리 과정

### Step 1. 입력 데이터
Moltbook 스타일의 discussion 문서

각 문서는 다음 정보를 가진다:

- asset_key (예: bsc:BNB)
- text
- timestamp
- engagement

---

### Step 2. Feature 추출 (LLM)

각 문서에서 다음을 추출:

- mood_score
- playbook 확률
- risk 점수

---

### Step 3. Asset 기준 그룹화

예:

- BNB → 10개 문서
- CAKE → 10개 문서
- LISTA → 10개 문서

---

### Step 4. Aggregation (집계)

각 asset별로:

- 평균 mood
- 주요 playbook
- 주요 risk
- confidence

를 계산

---

### Step 5. 최종 상태 생성

예:

```json
{
  "asset_key": "bsc:BNB",
  "mood_label": "조심스러운 낙관",
  "playbook_label": "이벤트 선점",
  "risk_flags": ["유동성", "포인트 경쟁", "실행 리스크"],
  "confidence": 0.50
}
Step 6. 자연어 요약 생성

LLM이 최종 상태를 기반으로 summary 생성

예:

기다린다고 말하지만 실제로는 선점 중
경쟁 심화 + 실행 리스크 증가
진입 난이도 상승
6. 프로젝트 구조
app/
  adapters/            # 데이터 정규화
  feature_extractor/   # LLM 기반 feature 추출
  state_aggregator/    # asset 상태 생성
  evaluation/          # 성능 평가
  output/              # summary 생성

mock_data/             # 테스트 데이터
main.py                # 전체 실행 파일
7. 실행 방법
pip install -r requirements.txt
python3 main.py
8. 결과

실행 시:

1) 터미널 출력
evaluation 결과
asset 상태
summary
2) output.json 생성

프런트에서 바로 사용 가능

예:

[
  {
    "asset_key": "bsc:BNB",
    "symbol": "BNB",
    "mood_label": "조심스러운 낙관",
    "playbook_label": "이벤트 선점",
    "risk_flags": ["유동성", "포인트 경쟁", "실행 리스크"],
    "summary": "BNB는 현재 선점 움직임이 강해지고 있으며...",
    "confidence_label": "Medium"
  }
]
9. 프런트 연동

프런트는 아래 필드만 사용하면 된다:

asset_key
symbol
mood_label
playbook_label
risk_flags
summary
confidence_label
10. 기존 방식과 차이

기존:

bullish / bearish
sentiment score

Narrative Radar:

기다린다고 말하지만 실제로는 선점 중인지
crowd가 이미 경쟁 상태인지
진입 난이도가 올라가고 있는지
11. 현재 MVP 범위
mock 데이터 기반
LLM feature extraction
asset-level aggregation
JSON output
12. 향후 확장
실시간 데이터 수집
알림 시스템
watchlist
API 서버
히스토리 추적
13. 한 줄 요약

Narrative Radar는 시끄러운 디스커션을 읽고, 군중의 실제 행동을 보여준다.
