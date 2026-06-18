# 專案規格與技術要求 (Project Specification)

> **開發角色設定**：資深韌體工程師 (Senior Firmware Engineer)
> 本專案需以底層思維出發，注重記憶體位元組操作 (Byte manipulation)、通訊時序 (Timing/Jitter) 以及硬體資源的穩定性。

## 技術棧與核心能力要求 (Technology Stack)

為了順利完成這個專案，開發者需要具備以下技術能力：

1. **Python 系統級編程**
   - 熟練使用 `struct` 模組處理 C/C++ 結構體與 Python 之間的二進位序列化 (Little/Big Endian 轉換)。
   - 多執行緒 (`threading`) 與多進程 (`multiprocessing`) 架構設計，以分離 UI/邏輯層與底層 I/O 通訊。
2. **通訊協定實作 (CAN Bus)**
   - 熟悉 Controller Area Network (CAN) 2.0A/B 協定基礎（標準/擴展幀、Arbitration ID）。
   - 精通 `python-can` 套件架構與虛擬/實體介面切換。
3. **演算法與位元運算 (Bitwise Operations)**
   - 具備手刻或移植自訂 CRC (Cyclic Redundancy Check) 演算法的能力，包含查表法 (Lookup Table)、特定多項式 (Poly) 與 XOR 初始值設定。
4. **硬體時序控制 (Timing Control)**
   - 了解作業系統層級的計時器限制，能實作 Spin-lock 或利用 `ctypes.windll.winmm` 處理高精度毫秒級時序控制。

---

## 核心程式碼簡略範例

### 1. DJI SDK 協議轉換 (C++ 轉 Python 概念)
DJI 的封包要求嚴格的 Little/Big Endian 混合以及兩段式 CRC 驗證。身為資深韌體工程師，我們在 Python 中不依賴龐大的框架，而是精準操作 Byte Array。

```python
import struct

def build_dji_can_packet(yaw: int, roll: int, pitch: int, seq_num: int) -> bytes:
    """
    範例：將雲台位置指令打包為 DJI CAN 封包格式
    """
    # 1. 準備 Payload (Little Endian 的 int16)
    # <hhhB 代表 3個 short (2 bytes) + 1個 unsigned char (1 byte)
    ctrl_byte = 0x01
    payload = struct.pack('<hhhB', yaw, roll, pitch, ctrl_byte)
    
    # 2. 準備 Header 前綴 (長度包含 CRC32 等)
    cmd_type = 0x03
    cmd_set = 0x0E
    cmd_id = 0x00
    packet_length = 10 + 2 + 2 + len(payload) + 4
    
    # SOF (0xAA), Length(LE), CmdType, Enc/Res(0x00 * 4), SeqNum(BE)
    prefix = struct.pack('<BHB4s', 0xAA, packet_length, cmd_type, b'\x00'*4)
    prefix += struct.pack('>H', seq_num) # Seq Num 是 Big Endian
    
    # 3. 計算 Header CRC16 (自訂 XorIn: 0xc55c)
    crc16_val = calc_custom_crc16(prefix)
    header_with_crc = prefix + struct.pack('<H', crc16_val)
    
    # 4. 組合 Data Segment 並計算完整 CRC32 (自訂 XorIn: 0xc55c0000)
    data_segment = struct.pack('<BB', cmd_set, cmd_id) + payload
    packet_without_crc32 = header_with_crc + data_segment
    
    crc32_val = calc_custom_crc32(packet_without_crc32)
    final_packet = packet_without_crc32 + struct.pack('<I', crc32_val)
    
    return final_packet
```

### 2. Robotell USB-CAN 與虛擬模擬器整合
透過 `python-can`，我們可以輕易在開發階段的「虛擬環境」與現場的「實體 Robotell 轉接器」之間無縫切換。

```python
import can

def get_can_bus(is_simulation=True):
    """
    獲取 CAN Bus 介面。透過參數一鍵切換實體/模擬硬體。
    """
    if is_simulation:
        # 開發階段：無硬體時使用虛擬匯流排
        print("Initializing Virtual CAN Bus...")
        return can.Bus(interface='virtual', channel='dji_sim_bus')
    else:
        # 實戰階段：接上 Robotell USB-CAN 轉接器
        print("Initializing Robotell CAN Interface on COM8...")
        return can.Bus(
            interface='robotell', 
            channel='COM8',       # 需對應裝置管理員的 COM Port
            ttyBaudrate=115200,   # Robotell 序列傳輸速率
            bitrate=1000000       # DJI CAN Bus 要求 1 Mbps
        )

# 傳送指令範例
bus = get_can_bus(is_simulation=True)
raw_bytes = build_dji_can_packet(yaw=100, roll=0, pitch=-50, seq_num=1)

# DJI CAN 訊息的 Arbitration ID 通常根據通訊節點而定 (如 0x223)
msg = can.Message(arbitration_id=0x223, data=raw_bytes, is_extended_id=False)
bus.send(msg)
```
