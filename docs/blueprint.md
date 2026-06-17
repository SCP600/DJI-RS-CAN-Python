# DJI RS 穩定器 USB-CAN 控制藍圖

## 專案目標
本專案旨在透過 Python 結合簡易的 USB-CAN 轉接器（支援序列通訊字串轉譯），並串接至 DJI RS Focus Wheel (跟焦輪) 的 CAN 接口，達成對 DJI RS 2 / RS 4 穩定器的姿態控制（如上下左右旋轉）。

## 架構設計 (四層架構)

### 1. 硬體連接層 (Hardware Layer)
- **實體線路**：PC (USB) <-> USB-CAN 轉接器 <-> DJI RS Focus Wheel 的 CAN 接口 (CAN_H, CAN_L, GND)。
- **通訊參數**：DJI CAN 總線預設使用 1 Mbps 的鮑率 (Baudrate)。

### 2. 序列通訊與 CAN 轉換層 (Data Link Layer)
- **技術選擇**：優先使用 `python-can` 套件搭配對應的轉接器介面（如 `robotell` 或 `slcan` 介面，視硬體實際支援的協定而定）。
  - *效能評估*：對於控制雲台（更新頻率通常為 10Hz~50Hz）而言，直接使用套件與手刻 `pyserial` 處理的**效能差異微乎其微**。最大的好處是 `python-can` 提供了標準化的 `can.Message` API，可以避免我們重複造輪子，讓程式碼更乾淨、更好維護。
  - *降級 (Fallback) 方案*：若硬體通訊協定較為特殊，與套件內建的解析有衝突，我們再改為手刻 `pyserial` 擷取 ASCII 字串 (`t1238...`) 來解析。

### 3. DJI 協議封裝層 (DJI Protocol Layer)
參考 C++ 版本的 `ConstantRobotics/DJIR_SDK` 邏輯，並將其移植至 Python。
- **封包結構 (Packet Packing)**：
  - `SOF` (起始字節 0xAA)
  - `Length` (封包長度)
  - `Version` & `Session`
  - `CRC8` (Header 校驗碼)
  - `CmdSet` / `CmdId` (控制雲台的指令集)
  - `Payload` (資料內容，如旋轉的速度或角度)
  - `CRC16` (完整封包的校驗碼)
- **核心實作**：`crc8` 與 `crc16` 的查表法 (Lookup Table) 演算法實作，以通過 DJI 設備的資料驗證。

### 4. 應用控制層 (Application Layer)
封裝出乾淨的 API 供您的主程式直接呼叫。
- **背景通訊執行緒 (Background Thread)**：處理接收 DJI 穩定器的狀態回報，並可能需要維持連線。
- **雲台控制 API**：提供例如 `gimbal.move_speed(yaw, pitch, roll)` 的直覺方法，將您的命令打包並下發至底層。

---

## 開發流程規劃 (Milestones)

1. **環境建置與硬體測試 (Phase 1)**
   - 建立 Python 虛擬環境，安裝 `python-can`、`pyserial`。
   - 撰寫硬體測試腳本，測試是否能順利讀取 CAN Bus 上 DJI 發出的原始封包（Heartbeat）。
2. **協議層實作 - CRC 與 Packing (Phase 2)**
   - 在 Python 中刻出 DJI SDK 的封包產生器與解析器。
3. **控制邏輯對接 (Phase 3)**
   - 根據 SDK 規範，組裝雲台控制指令，發送控制封包給穩定器進行實際動作測試。
4. **API 封裝與優化 (Phase 4)**
   - 完善錯誤處理與重連機制，封裝為易用的 Python 模組。
