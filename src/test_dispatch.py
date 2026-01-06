from src.celery_worker import analyze_driver_risk
import time

# 1. 模擬一筆高風險的駕駛數據
driver_id = "UBER-888"
speed = 10  # 時速極慢
stuck_count = 25  # 卡住很多次

print(f"📡 [Producer] 正在發送任務: 司機 {driver_id}...")

# 2. 發送任務 (使用 .delay() 方法進行非同步呼叫)
# 這行程式碼會瞬間完成，因為它只是把訊息丟進 Redis，不會等結果
async_task = analyze_driver_risk.delay(driver_id, speed, stuck_count)

print(f"✅ [Producer] 任務已發送！Task ID: {async_task.id}")
print("⏳ [Producer] 正在等待 Worker (RTX 3090) 運算結果...")

# 3. 輪詢 (Polling) 等待結果
# 在真實 API 中，我們通常會直接回傳 Task ID 給前端，讓前端來輪詢
while not async_task.ready():
    print(".", end="", flush=True)
    time.sleep(0.5)

# 4. 取得結果
result = async_task.get()

print("\n\n🎉 [Producer] 收到運算結果：")
print("====================================")
print(result)
print("====================================")