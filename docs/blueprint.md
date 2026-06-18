# DJI RS 穩定器 USB-CAN 控制藍圖

## 專案目標
本專案旨在透過 Python 結合簡易的 USB-CAN 轉接器（支援序列通訊字串轉譯），並串接至 DJI RS Focus Wheel (跟焦輪) 的 CAN 接口，達成對 DJI RS 2 / RS 4 穩定器的姿態控制（如上下左右旋轉）。

## 架構設計 (四層架構)

### 1. 硬體連接層 (Hardware Layer)
- **實體線路**：PC (USB) <-> USB-CAN 轉接器 <-> DJI RS Focus Wheel 的 CAN 接口 (CAN_H, CAN_L, GND)。
- **通訊參數**：DJI CAN 總線預設使用 1 Mbps 的鮑率 (Baudrate)。

### 2. 序列通訊與 CAN 轉換層 (Data Link Layer)
- **技術選擇**：全面使用 `python-can` 套件，並直接指定 `interface='robotell'`。
  - *硬體原生支援*：`python-can` 已內建 Robotell 專屬的二進位協議解析介面，無需手動透過 `pyserial` 撰寫封包拆解邏輯。底層通訊仍會自動依賴 `pyserial` 來完成 USB-to-Serial 的資料傳輸。
  - *無縫切換*：開發初期使用 `interface='virtual'` 建立虛擬 CAN 匯流排進行模擬測試。未來取得實體 Robotell 轉接器後，僅需將介面改為 `robotell`，並設定 `channel='COMx'` (對應的 COM Port)、`ttyBaudrate=115200` 以及 DJI 所要求的 `bitrate=1000000` (1 Mbps)，上層邏輯程式碼**完全不需修改**。
  - *效能優勢*：使用標準化的 `can.Message` API，讓封包收發更為穩定，維護性也大幅提升。

### 3. DJI 協議封裝層 (DJI Protocol Layer)
參考 C++ 版本的 `ConstantRobotics/DJIR_SDK` 邏輯，並將其移植至 Python。
- **封包結構 (Packet Packing)**：
  - `SOF` (起始字節 0xAA)
  - `Length` (封包長度 2 bytes, Little Endian)
  - `CmdType` (1 byte, 控制指令為 0x03)
  - `ENC`, `RES1-3` (共 4 bytes, 皆為 0x00)
  - `Seq_Num` (流水號 2 bytes, Big Endian)
  - `CRC16` (Header 校驗碼，針對前 10 bytes 計算，以 Little Endian 附加)
  - `CmdSet` / `CmdId` (控制雲台的指令集)
  - `Payload` (資料內容，如旋轉的速度或角度，Little Endian)
  - `CRC32` (完整封包的校驗碼，針對前面所有 bytes 計算，以 Little Endian 附加)
- **核心實作**：使用特定的 `crc16` (XorIn: 0xc55c) 與 `crc32` (XorIn: 0xc55c0000) 演算法實作，以通過 DJI 設備的資料驗證。

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
