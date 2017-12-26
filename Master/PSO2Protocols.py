from ProxyServer import ProxyServers
from twisted.internet import protocol
from twisted.internet import threads

import io
import socket
import struct

queryShipArr = [(12199, "210.189.208.1"),
                (12299, "210.189.208.16"),
                (12399, "210.189.208.31"),
                (12499, "210.189.208.46"),
                (12599, "210.189.208.61"),
                (12699, "210.189.208.76"),
                (12799, "210.189.208.91"),
                (12899, "210.189.208.106"),
                (12999, "210.189.208.121"),
                (12099, "210.189.208.136")]
curShipIndex = 0


def scrape_ship_packet(ship_ip, ship_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(30)
    try:
        s.connect((ship_ip, ship_port))
    except socket.error:
        return None
    except Exception:
        return None
    data = io.BytesIO()
    try:
        data.write(s.recv(4))
    except socket.error:
        return None
    except Exception:
        return None
    actual_size = struct.unpack_from('i', data.getvalue(), 0x0)[0]
    try:
        data.write(s.recv(actual_size - 4))
    except socket.error:
        return None
    except Exception:
        return None
    s.close()
    data.flush()
    data = bytearray(data.getvalue())
    return str(data)


def get_ship_query():
    global curShipIndex, queryShipArr
    ship_port, ship_address = queryShipArr[curShipIndex]
    data = scrape_ship_packet(ship_address, ship_port)
    curShipIndex += 1
    if curShipIndex >= len(queryShipArr):
        curShipIndex = 0
    return data


class ShipInfo(protocol.Protocol):
    def __init__(self):
        pass

    def connectionMade(self):
        d = threads.deferToThread(get_ship_query)
        d.addCallback(self.send_ship_list)

    def send_ship_list(self, data):
        if data:
            self.transport.write(data)
        self.transport.loseConnection()


class ShipInfoFactory(protocol.Factory):
    def __init__(self):
        pass

    def buildProtocol(self, addr):
        return ShipInfo()


def get_users(server):
    return server.users


class BlockSender(protocol.Protocol):
    def __init__(self):
        pass

    def connectionMade(self):
        if len(ProxyServers) < 1:
            self.transport.loseConnection()
            return
        servers = sorted(list(ProxyServers.values()), key=get_users)
        server = None
        for pserver in servers:
            if pserver.enabled:
                server = pserver
                break
        if server is None:
            self.transport.loseConnection()
            return
        o1, o2, o3, o4 = server.address.split(".")
        buf = bytearray()
        buf += struct.pack('i', 0x90)
        buf += struct.pack('BBBB', 0x11, 0x2C, 0x0, 0x0)
        buf += struct.pack('96x')  # lol SEGA
        buf += struct.pack('BBBB', int(o1), int(o2), int(o3), int(o4))
        buf += struct.pack('H', self.transport.getHost().port)
        buf += struct.pack('34x')

        print(
            (
                "[BlockSend] Sending client to server {} currently with {}"
                " users.".format
                (
                    server.name,
                    server.users
                )
            )
        )
        server.users += 1
        self.transport.write(str(buf))
        self.transport.loseConnection()


class BlockSenderFactory(protocol.Factory):
    def __init__(self):
        pass

    def buildProtocol(self, addr):
        return BlockSender()
