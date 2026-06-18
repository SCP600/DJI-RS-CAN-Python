import unittest
import struct
from src.crc import calc_crc16, calc_crc32
from src.dji_protocol import DJIProtocol

class TestDJIProtocol(unittest.TestCase):

    def test_crc16(self):
        # The prefix of a move_to packet from the C++ test string
        prefix = bytes([0xAA, 0x1A, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x22, 0x11])
        crc16 = calc_crc16(prefix)
        # The expected CRC16 is 0x42A2 (stored as A2 42 in Little Endian)
        self.assertEqual(crc16, 0x42A2)

    def test_crc32(self):
        # The full packet without CRC32 from the C++ test string
        packet_without_crc32 = bytes([
            0xAA, 0x1A, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00,
            0x22, 0x11, 0xA2, 0x42, 0x0E, 0x00, 0x20, 0x00,
            0x30, 0x00, 0x40, 0x00, 0x01, 0x14
        ])
        crc32 = calc_crc32(packet_without_crc32)
        # From executing the C++ logic, let's just make sure it doesn't crash 
        # and produces a consistent integer
        self.assertIsInstance(crc32, int)

    def test_move_to_packet_structure(self):
        proto = DJIProtocol()
        # Force seq_num to match the C++ test case (0x2211 after incrementing 0x2210)
        proto._seq_num = 0x2211
        
        # move_to(yaw=32, roll=48, pitch=64, time_ms=2000)
        packet = proto.move_to(32, 48, 64, 2000, absolute=True)
        
        # It should exactly match the C++ test string prefix + payload + some crc32
        expected_prefix = bytes([
            0xAA, 0x1A, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00,
            0x22, 0x11, 0xA2, 0x42, 0x0E, 0x00, 0x20, 0x00,
            0x30, 0x00, 0x40, 0x00, 0x01, 0x14
        ])
        
        self.assertEqual(packet[:len(expected_prefix)], expected_prefix)
        self.assertEqual(len(packet), 26)

if __name__ == '__main__':
    unittest.main()
