from fastapi import FastAPI
from pydantic import BaseModel
from celery.result import AsyncResult

# ⚠️ 注意：這裡要引入你原本已經寫好的 Celery App 和 Task
# 假設你的 Celery 實例叫 celery_app，任務叫 analyze_driver_task
# 如果你的檔名不同，請修改這裡的 import
from src.celery_worker import celery_app, analyze_driver_task

app = FastAPI(title="Geo Decision Matrix AI Core")

# 定義請求格式 (Data Model)
class DriverRequest(BaseModel):
    driver_id: str
    # 未來可以加更多參數，例如:
    # location: tuple
    # timestamp: int

@app.get("/")
def health_check():
    return {"status": "online", "gpu": "RTX 3090 Ready"}

# 1. 發送任務 (Producer)
@app.post("/analyze")
async def analyze_driver(request: DriverRequest):
    """
    接收前端請求 -> 丟進 Redis Queue -> 回傳 Task ID
    """
    # 使用 .delay() 進行非同步呼叫
    task = analyze_driver_task.delay(request.driver_id)
    
    return {
        "message": "Task submitted successfully",
        "task_id": task.id,
        "check_url": f"/result/{task.id}"
    }

# 2. 查詢結果 (Poling / Result Backend)
@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """
    前端透過 Task ID 來查詢運算進度或結果
    """
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'PENDING':
        return {"status": "Pending", "progress": "Waiting for worker..."}
    
    elif task_result.state == 'SUCCESS':
        return {
            "status": "Success", 
            "result": task_result.result  # 這裡會是你 Worker 算出來的 GPU 結果
        }
    
    elif task_result.state == 'FAILURE':
        return {"status": "Failure", "error": str(task_result.result)}
        
    return {"status": task_result.state}