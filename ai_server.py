"""
AI Assistant HTTP Server
GET  /health          → 確認 server 存活
POST /query           → 自然語言 → 組件路由
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json

app = FastAPI()

# 允許 localhost 任何 port 呼叫（Vue3 dev server 用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 台智雲設定 ──────────────────────────────────────────
API_KEY  = "bf3c97af-ea08-4286-8dc3-9467fd216b9b"
CONV_URL = "https://api-ams.twcc.ai/api/models/conversation"
MODEL    = "llama3.3-ffm-70b-32k-chat"

HEADERS = {
    "accept": "application/json",
    "X-API-KEY": API_KEY,
    "content-type": "application/json",
}

PARAMETERS = {
    "max_new_tokens": 512,
    "temperature": 0.1,
    "top_k": 100,
    "top_p": 0.93,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "show_accident_heatmap",
            "description": "顯示雙北行人交通事故熱點地圖，包含事故密度分布、高風險路口排名、時段分析",
            "parameters": {
                "type": "object",
                "properties": {
                    "district": {"type": "string", "description": "行政區，例如：信義區、板橋區。留空表示全市"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_ltc_care",
            "description": "顯示長照關懷儀表板，包含高齡人口分布、長照需求人數、依賴比趨勢、照服員人力",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["taipei", "metrotaipei"], "description": "使用者明確說「台北市」才填 taipei，其餘（雙北、新北、或未指定）一律填 metrotaipei"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_map_layers",
            "description": "顯示圖資資訊地圖，包含腳踏車道、YouBike 站點等圖資圖層",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["taipei", "metrotaipei"], "description": "使用者明確說「台北市」才填 taipei，其餘（雙北、新北、或未指定）一律填 metrotaipei"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_transportation",
            "description": "顯示務實交通儀表板，包含電動公車比例、YouBike 可用率、自行車路網",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_population_flow",
            "description": "顯示人口流動儀表板，包含日間活動人口、夜間停留人口、電信信令人口分布、各行政區人口流動",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "enum": ["taipei", "metrotaipei"], "description": "使用者明確說「台北市」才填 taipei，其餘（雙北、新北、或未指定）一律填 metrotaipei"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_transit_isochrone",
            "description": "顯示大眾運輸步行等時圈地圖，包含捷運站、公車站、台鐵站的步行可及範圍覆蓋率分析",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

SYSTEM_PROMPT = (
    "你是雙北通勤可及性地圖的智慧助理。"
    "根據使用者的問題，呼叫最符合的工具。判斷原則：\n"
    "- 行人事故、危險路口、行人安全 → show_accident_heatmap\n"
    "- 長照、高齡、老人、照服員、長期照護 → show_ltc_care（判斷是台北市還是雙北）\n"
    "- 圖資、地圖圖層、腳踏車道、人行道、自行車道、地理資料 → show_map_layers（判斷是台北市還是雙北）\n"
    "- 交通、公車、YouBike、電動巴士、自行車 → show_transportation\n"
    "- 人口流動、日間人口、夜間人口、電信信令、活動人口、停留人口、行政區人口 → show_population_flow（判斷是台北市還是新北市）\n"
    "- 等時圈、捷運步行、公車站可及、台鐵覆蓋、大眾運輸可及性、步行範圍 → show_transit_isochrone\n"
    "如果問題完全不相關，直接回覆無法找到對應組件，不要呼叫工具。\n"
    "城市判斷（show_ltc_care / show_map_layers）：提到新北、雙北、大台北 → metrotaipei；只提到台北市 → taipei；沒有特別說 → 預設 metrotaipei。\n"
    "城市判斷（show_population_flow）：提到新北、雙北、大台北 → metrotaipei；只提到台北市 → taipei；沒有特別說 → 預設 metrotaipei。"
)


class QueryRequest(BaseModel):
    text: str


class QueryResponse(BaseModel):
    action: str
    params: dict


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": req.text},
        ],
        "tools": TOOLS,
        "parameters": PARAMETERS,
        "stream": False,
    }

    try:
        resp = requests.post(CONV_URL, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"台智雲 API 錯誤: {e.response.status_code}")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"連線失敗: {e}")

    data = resp.json()
    tool_calls = data.get("tool_calls", [])

    if tool_calls:
        tc = tool_calls[0]
        args_raw = tc["function"].get("arguments", "{}")
        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
        return QueryResponse(action=tc["function"]["name"], params=args)

    # fallback
    text = data.get("generated_text") or data.get("content", "")
    return QueryResponse(action="show_text", params={"message": text})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
