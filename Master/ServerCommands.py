from ProxyServer import ProxyServer
from ProxyServer import ProxyServers

CommandHandlers = {}


class CommandHandler(object):
    def __init__(self, command):
        self.command = command

    def __call__(self, f):
        CommandHandlers[self.command] = f


@CommandHandler("newserver")
def new_server(messageobj):
    s = ProxyServer(messageobj['ip'], messageobj['name'])
    if s.name not in ProxyServers:
        ProxyServers[s.name] = s
        print("[!!!] New server registered, named %s with ip %s" % (messageobj['name'], messageobj['ip']))


@CommandHandler("delserver")
def del_server(messageobj):
    if messageobj['name'] in ProxyServers:
        del ProxyServers[messageobj['name']]
        print("[---] Removed server %s." % messageobj['name'])


@CommandHandler("ping")
def ping(messageobj):
    if messageobj['name'] in ProxyServers:
        ProxyServers[messageobj['name']].users = messageobj['usercount']

        import WebAPI
        count = 0
        for server in ProxyServers.values():
            count += server.users
        if count > WebAPI.peakPlayers:
            WebAPI.peakPlayers = count
