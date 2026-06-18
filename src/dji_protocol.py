import struct
from .crc import calc_crc16, calc_crc32

class DJIProtocol:
    """
    Implements the DJI SDK Protocol for CAN bus communication.
    Follows Little-Endian format for most fields, except for SeqNum which is Big-Endian.
    """

    SOF = 0xAA
    CMD_TYPE_CONTROL = 0x03
    CMD_SET_GIMBAL = 0x0E

    # Cmd Ids
    CMD_ID_MOVE_TO = 0x00
    CMD_ID_SET_SPEED = 0x01
    CMD_ID_GET_POSITION = 0x02

    def __init__(self):
        self._seq_num = 0x2210

    def _get_seq_num(self) -> int:
        val = self._seq_num
        self._seq_num += 1
        if self._seq_num >= 0xFFFD:
            self._seq_num = 0x0002
        return val

    def pack_message(self, cmd_id: int, payload: bytes) -> bytes:
        """
        Packs a command ID and payload into a full DJI CAN packet with CRC16 and CRC32.
        """
        packet_length = 10 + 2 + 2 + len(payload) + 4
        seq_num = self._get_seq_num()

        # Prefix: SOF(1), Length(2, LE), CmdType(1), Enc(1), Res(3), SeqNum(2, BE)
        # Format: < B H B B 3s >H
        prefix_part1 = struct.pack('<BHBB3s', self.SOF, packet_length, self.CMD_TYPE_CONTROL, 0x00, b'\x00\x00\x00')
        prefix_part2 = struct.pack('>H', seq_num)
        prefix = prefix_part1 + prefix_part2

        # Header CRC16 (2 bytes, LE)
        crc16_val = calc_crc16(prefix)
        header_with_crc = prefix + struct.pack('<H', crc16_val)

        # Data Segment: CmdSet(1), CmdId(1), Payload(N)
        data_segment = struct.pack('<BB', self.CMD_SET_GIMBAL, cmd_id) + payload
        packet_without_crc32 = header_with_crc + data_segment

        # Packet CRC32 (4 bytes, LE)
        crc32_val = calc_crc32(packet_without_crc32)
        final_packet = packet_without_crc32 + struct.pack('<I', crc32_val)

        return final_packet

    def move_to(self, yaw: int, roll: int, pitch: int, time_ms: int, absolute: bool = True) -> bytes:
        """
        Generates a move_to packet.
        Yaw, Roll, Pitch are 0.1 degree units.
        Time is divided by 100 before sending.
        """
        ctrl_byte = 0x00
        if absolute:
            ctrl_byte |= 0x01 # BIT1
        
        time_val = int(time_ms / 100)
        # Payload: yaw(2), roll(2), pitch(2), ctrl_byte(1), time(1)
        payload = struct.pack('<hhhBB', yaw, roll, pitch, ctrl_byte, time_val)
        return self.pack_message(self.CMD_ID_MOVE_TO, payload)

    def set_speed(self, yaw_speed: int, roll_speed: int, pitch_speed: int, speed_control: bool = False) -> bytes:
        """
        Generates a set_speed packet.
        Speeds are in 0.1 degree/sec units.
        """
        ctrl_byte = 0x00
        if not speed_control:
            ctrl_byte |= 0x80 # BIT7
        
        # FocalControl DISABLED by default
        ctrl_byte |= 0x08 # BIT3

        # Payload: yaw(2), roll(2), pitch(2), ctrl_byte(1)
        payload = struct.pack('<hhhB', yaw_speed, roll_speed, pitch_speed, ctrl_byte)
        return self.pack_message(self.CMD_ID_SET_SPEED, payload)

    def get_current_position(self) -> bytes:
        """
        Generates a request to get current position.
        """
        payload = b'\x01'
        return self.pack_message(self.CMD_ID_GET_POSITION, payload)

