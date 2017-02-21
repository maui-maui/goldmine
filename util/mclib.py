"""Small Minecraft protocol library."""
import socket
import struct
from datetime import datetime
from .json import loads as jloads

def pop_int(conn):
    """Decode bytes from protocol."""
    acc = 0
    shift = 0
    byte = ord(conn.recv(1))
    while byte & 0x80:
        acc = acc | ((byte & 0x7f) << shift)
        shift = shift + 7
        byte = ord(conn.recv(1))
    return acc | (byte << shift)

def pack_varint(data):
    """Pack a VARINT for the protocol."""
    return bytes([(0x40 * (i != data.bit_length() // 7)) +
                  ((data >> (7 * i)) % 128) for i in range(1 + data.bit_length() // 7)])

def pack_data(data):
    """Pack some data with header for the protocol."""
    return pack_varint(len(data)) + data

def get_info(host, port):
    """Get server info in JSON format."""
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((host, port))
    pinged = False
    time_before = datetime.now()
    conn.send(pack_data(bytes(2) + pack_data(host.encode('utf-8')) +
                        struct.pack('>H', port) + bytes([1])) + bytes([1, 0]))
    pop_int(conn) # packet length
    pop_int(conn) # packet id
    len_int, data = pop_int(conn), bytes()
    while len(data) < len_int:
        data += conn.recv(1024)
        if not pinged:
            ping = (datetime.now() - time_before).total_seconds() * 1000
            pinged = True
    conn.close()
    final = jloads(data.decode('utf-8'))
    final['latency_ms'] = ping
    return final
