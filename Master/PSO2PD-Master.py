import json
import os

from twisted.internet.endpoints import TCP4ServerEndpoint
try:
    from twisted.internet import epollreactor
    epollreactor.install()
    from twisted.internet import reactor
except ImportError:
    from twisted.internet import reactor
from twisted.internet import stdio

from twisted.protocols import basic

from WebAPI import setup_web

from Commands import Commands
from ProxyRedis import p
from ProxyRedis import r
from ProxyRedis import redis_config
from PSO2Protocols import BlockSenderFactory
from PSO2Protocols import ShipInfoFactory


class ServerConsole(basic.LineReceiver):
    def __init__(self):
        self.delimiter = os.linesep

    def connectionMade(self):
        self.transport.write('>>> ')

    def lineReceived(self, line):
        """

        :type line: str
        """
        command = line.split(' ')[0]
        if command in Commands:
            if len(line.split(' ')) > 1:
                Commands[command](line.split(' ', 1)[1])
            else:
                Commands[command](line)
        else:
            print("[PSO2PD] Command not found.")
        self.transport.write('>>> ')


print("=== PSO2Proxy-Distributed master server starting...")

rthread = p.run_in_thread(sleep_time=0.001)

print("[Redis] Messaging thread running.")

print("[PSO2PD] Getting ship statuses...")

print("[PSO2PD] Cached ship query.")

print("[PSO2PD] Starting reactors...")

for x in range(0, 10):
    endpoint = TCP4ServerEndpoint(
        reactor,
        12000 + (100 * x),
        interface=redis_config['bindip']
    )
    endpoint.listen(BlockSenderFactory())

for x in range(0, 10):
    endpoint = TCP4ServerEndpoint(
        reactor,
        12099 + (100 * x),
        interface=redis_config['bindip']
    )
    endpoint.listen(ShipInfoFactory())

stdio.StandardIO(ServerConsole())

print("[PSO2PD] Reactor started.")

print("[PSO2PD] Announcing presence...")
r.publish("proxy-global", json.dumps({'command': "register"}))

setup_web()

reactor.run()

rthread.stop()
