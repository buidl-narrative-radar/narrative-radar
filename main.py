from typing import Any, Dict, List
from app.feature_extractor.extractor import extract_features
from app.state_aggregator.aggregator import build_asset_state

def build_sample_docs() -> List[Dict[str, Any]]:
    """
    end-to-end 테스트용 샘플 문서들.
    실제 Moltbook 연결 전까지는 이걸로 전체 파이프라인을 검증한다.
    """
    return [
        {
            "doc_id": "doc_001",
            "asset_key": "BTC",
            "text": "에어드랍 이벤트 전에 다들 물량 모으는 느낌. 늦으면 끝일 수도 있다.",
            "source": "moltbook",
            "published_at": "2026-04-16T10:00:00",
            "engagement": {
                "views": 1200,
                "likes": 80,
                "reposts": 10,
                "comments": 12,
            },
        },
        {
            "doc_id": "doc_002",
            "asset_key": "BTC",
            "text": "유동성이 얕고 스프레드가 커서 추격은 조심해야 한다.",
            "source": "moltbook",
            "published_at": "2026-04-16T11:00:00",
            "engagement": {
                "views": 900,
                "likes": 40,
                "reposts": 5,
                "comments": 7,
            },
        },
        {
            "doc_id": "doc_003",
            "asset_key": "BTC",
            "text": "지금은 관망이 맞다. 급하게 들어갈 자리는 아닌 듯.",
            "source": "moltbook",
            "published_at": "2026-04-16T12:00:00",
            "engagement": {
                "views": 700,
                "likes": 30,
                "reposts": 4,
                "comments": 5,
            },
        },
        {
            "doc_id": "doc_004",
            "asset_key": "ETH",
            "text": "다들 들어가는 분위기라 과열 느낌도 있다. 너무 늦게 타면 위험하다.",
            "source": "moltbook",
            "published_at": "2026-04-16T10:30:00",
            "engagement": {
                "views": 1500,
                "likes": 100,
                "reposts": 18,
                "comments": 20,
            },
        },
        {
            "doc_id": "doc_005",
            "asset_key": "ETH",
            "text": "보안 이슈는 아직 없어 보이지만 지금은 추격 금지 쪽이 더 맞아 보인다.",
            "source": "moltbook",
            "published_at": "2026-04-16T11:30:00",
            "engagement": {
                "views": 1100,
                "likes": 60,
                "reposts": 8,
                "comments": 10,
            },
        },
    ]

def extract_all_features(docs : List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    문서 리스트를 받아 각 문서에 extractor를 실행한다.
    """
    features = []
    for doc in docs:
        feature = extract_features(doc)
        features.append(feature)
    return features

def group_features_by_asset(features : List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    feature들을 asset_key 기준으로 묶는다.
    """
    grouped :  Dict[str, List[Dict[str, Any]]] = {}

    for feature in features:
        asset_key = feature["asset_key"]
        if asset_key not in grouped:
            grouped[asset_key] = []
        grouped[asset_key].append(feature)
    return grouped

def build_all_asset_states(grouped_features : List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    asset별 feature 묶음을 받아 최종 asset state를 생성한다.
    """
    asset_states = []

    for asset_key, features in grouped_features.items():
        asset_state = build_asset_state(asset_key, features)
        asset_states.append(asset_state)

    return asset_states

def main() -> None:
    # 1) 샘플 문서 준비
    docs = build_sample_docs()
    
    print("=== RAW DOCS ===")
    for doc in docs:
        print(doc)
    print()

    # 2) 문서별 feature 추출
    features =  extract_all_features(docs)

    print("=== EXTRACTED FEATURES ===")
    for feature in features:
        print(feature)
    print()

    # 3) asset_key 기준 묶기
    grouped_features = group_features_by_asset(features)

    print("=== GROUPED FEATURES ===")
    for asset_key, asset_features in grouped_features.items():
        print(f"{asset_key}: {len(asset_features)} docs")
    print()

    # 4) asset별 최종 상태 계산
    asset_states = build_all_asset_states(grouped_features)

    print("=== FINAL ASSET STATES ===")
    for state in asset_states:
        print(state)
    print()

if __name__ == "__main__":
    main()