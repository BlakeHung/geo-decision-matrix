from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import os

app = FastAPI(title="Geo-Decision AI")

# 讀取 Spark 算好的數據
if os.path.exists("data/risk_summary.json"):
    with open("data/risk_summary.json", "r") as f:
        RISK_CONTEXT = json.dumps(json.load(f))
else:
    RISK_CONTEXT = "無數據"

# 設定 Ollama (連線到宿主機)
llm = Ollama(model="llama3", base_url="http://host.docker.internal:11434")

template = """
你是地圖服務切換的技術決策顧問。
我們正在評估是否將地圖商從 Google 換成 Map8。

### Spark 分析數據:
{risk_context}

### 決策標準:
- 安全: 平均誤差 < 20m 且 風險率 < 5% -> 建議切換
- 危險: 平均誤差 > 50m 或 風險率 > 20% -> 強烈建議**不要**切換

請用繁體中文回答。

問題: {question}
"""

prompt = PromptTemplate(template=template, input_variables=["question"], partial_variables={"risk_context": RISK_CONTEXT})
chain = prompt | llm | StrOutputParser()

class Query(BaseModel):
    question: str

@app.post("/consult")
async def consult(q: Query):
    return {"analysis": chain.invoke({"question": q.question})}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)