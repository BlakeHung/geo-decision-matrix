// src/legacy_benchmark.js
const fs = require('fs');
const path = require('path');

// 模擬一個外部 API 呼叫 (例如 Google Maps API)
// 這會造成 "Waiting" 狀態，並佔用 Event Loop
const mockExternalApiCall = (record) => {
    return new Promise((resolve) => {
        // 模擬 10ms - 50ms 的網路延遲
        const delay = Math.random() * 40 + 10; 
        setTimeout(() => {
            resolve({
                id: record.user_id,
                processed: true,
                // 模擬回傳的大型 JSON payload，加速記憶體消耗
                payload: Array(100).fill("mock_data_payload_to_spike_memory") 
            });
        }, delay);
    });
};

const runBenchmark = async () => {
    console.log(">>> [Legacy System] 啟動舊版 Node.js 批次處理程序...");
    console.log(">>> 讀取 CSV 檔案中 (模擬不當的 Memory Loading)...");

    const filePath = path.join(__dirname, '../data/gps_tracks.csv');
    
    try {
        // 錯誤示範 1: 一次把檔案全部讀進記憶體 (而不是用 Stream)
        const data = fs.readFileSync(filePath, 'utf8');
        const lines = data.split('\n').slice(1); // 去掉 Header
        
        console.log(`>>> 成功讀取 ${lines.length} 筆資料`);
        console.log(">>> 開始發送模擬 API 請求 (準備迎接 Event Loop Blocking)...");

        const startTime = Date.now();
        const promises = [];

        // 錯誤示範 2: 沒有控制併發數 (Concurrency)，瞬間塞爆 Event Loop
        // 當 lines 數量很大 (如 10萬筆) 時，這裡會產生數萬個 Pending Promises
        for (let i = 0; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            
            const cols = lines[i].split(',');
            const record = { user_id: cols[0], lat: cols[2], lon: cols[3] };

            // 每 1000 筆監控一次記憶體
            if (i % 1000 === 0) {
                const used = process.memoryUsage().heapUsed / 1024 / 1024;
                process.stdout.write(`\r[Processing] 已發送 ${i} 筆請求 | 目前記憶體使用: ${Math.round(used * 100) / 100} MB`);
            }

            // 把 Promise 推入陣列 (這是導致 OOM 的主因)
            promises.push(mockExternalApiCall(record));
        }

        console.log("\n>>> 等待所有 API 回應...");
        
        // 這裡就是「死亡交叉點」：等待數萬個 Promises 同時回傳
        await Promise.all(promises);

        const endTime = Date.now();
        console.log(`\n>>> 處理完成！耗時: ${(endTime - startTime) / 1000} 秒`);

    } catch (error) {
        console.error("\n\n!!! 系統崩潰 (SYSTEM CRASH) !!!");
        console.error("錯誤類型:", error.message);
        console.error("錯誤堆疊:", error.stack);
        
        const used = process.memoryUsage().heapUsed / 1024 / 1024;
        console.error(`崩潰時記憶體使用量: ${Math.round(used * 100) / 100} MB`);
    }
};

runBenchmark();