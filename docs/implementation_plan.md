# 模擬測試實作計畫

因目前無實體硬體，我們將調整開發流程，利用 `python-can` 內建的 **虛擬 CAN 匯流排 (Virtual CAN Bus)** 功能來進行模擬測試。這允許我們在同一台電腦上執行多個 Python 程式，讓它們透過虛擬的 CAN 介面互相傳遞訊息，完美模擬真實的硬體通訊環境。

## User Review Required

> [!IMPORTANT]  
> 由於我們使用純軟體模擬，將會跳過第一階段針對特定 USB-CAN 轉接器 (如 CH340 / slcan) 的硬體驅動層設定，直接專注於**通訊協議 (DJI Protocol)** 與**控制邏輯**的開發。未來取得硬體後，只需將 `python-can` 的介面參數從 `virtual` 改為實際硬體介面 (如 `com3`, `slcan`) 即可，上層程式碼不需大幅修改。請確認此流程是否符合您的預期。

## Proposed Changes

我們將建立以下元件來建構模擬環境：

### 核心套件與環境
#### [NEW] [requirements.txt](file:///d:/DJIwithCAN/requirements.txt)
- 加入 `python-can` 套件依賴。

### 模擬器 (硬體替身)
#### [NEW] [tools/mock_stabilizer.py](file:///d:/DJIwithCAN/tools/mock_stabilizer.py)
- **功能**：模擬 DJI RS 穩定器。
- **行為**：
  1. 連接至名為 `dji_sim_bus` 的虛擬 CAN 介面。
  2. 使用背景執行緒，每秒發送假的 Heartbeat (心跳) CAN 封包。
  3. 監聽虛擬 CAN 匯流排，接收來自控制端的控制指令，並印出收到的 Hex 數值（後續可加入 CRC 驗證邏輯來測試封包是否正確）。

### 協議層與控制端
#### [NEW] [src/dji_protocol.py](file:///d:/DJIwithCAN/src/dji_protocol.py)
- **功能**：實作 DJI SDK 的封包結構。
- **行為**：包含 CRC8、CRC16 演算法以及將控制指令打包成 CAN Message 的邏輯。

#### [NEW] [src/client_test.py](file:///d:/DJIwithCAN/src/client_test.py)
- **功能**：模擬我們的 PC 控制端程式。
- **行為**：
  1. 連接至同一個 `dji_sim_bus` 虛擬 CAN 介面。
  2. 接收並印出模擬器發出的 Heartbeat 封包 (完成 Milestone Phase 1)。
  3. 呼叫 `dji_protocol.py` 產生測試用的控制封包並發送至虛擬匯流排。

## Verification Plan

### Manual Verification
1. 開啟終端機執行 `python tools/mock_stabilizer.py`，它應開始持續發送虛擬心跳包並等待指令。
2. 開啟另一個終端機執行 `python src/client_test.py`。
3. 預期結果：`client_test.py` 能成功印出模擬器發送的心跳包；同時 `mock_stabilizer.py` 能成功印出 `client_test.py` 發送的測試控制封包。這證明我們的虛擬 CAN 雙向通訊已成功建立。
