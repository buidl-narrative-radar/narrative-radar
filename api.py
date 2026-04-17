from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from main import run_pipeline, run_single_asset_pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 해커톤 MVP용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"ok": True}


@app.get("/assets")
def get_assets():
    """
    전체 asset 결과 반환
    """
    try:
        return run_pipeline(mode="llm")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/asset/{symbol}")
def get_asset(symbol: str):
    """
    특정 asset 하나만 동적으로 계산해서 반환
    예: /asset/BNB
    """
    try:
        return run_single_asset_pipeline(symbol, mode="llm")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))