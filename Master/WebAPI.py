import calendar
from Config import YAMLConfig
import datetime
from ProxyServer import ProxyServers
import traceback
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web import server

import json
import os

upStart = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
peakPlayers = 0

web_config = YAMLConfig("web.cfg.yaml",
                        {"hostname": "example.com", "port": 8080, "servername": "PSO2Proxy Public Network",
                         "rconpass": "changeme"}, True)

hostName = web_config['hostname']
port = web_config['port']
serverName = web_config['servername']


class JSONConfig(Resource):
    isLeaf = True

    # noinspection PyPep8Naming
    @staticmethod
    def render_GET(request):
        request.setHeader("content-type", "application/json")
        config_json = {'version': 1, "name": serverName,
                       "publickeyurl": "http://%s:%i/publickey.blob" % (hostName, port),
                       "host": hostName}
        return json.dumps(config_json)


class PublicKey(Resource):
    isLeaf = True

    # noinspection PyPep8Naming
    @staticmethod
    def render_GET(request):
        request.setHeader("content-type", "application/octet-stream")
        if os.path.exists("keys/publickey.blob"):
            f = open("keys/publickey.blob", 'rb')
            pubkey_data = f.read()
            f.close()
            return pubkey_data


class WebAPI(Resource):
    # noinspection PyPep8Naming
    @staticmethod
    def render_GET(request):
        playerCount = 0
        servers = []
        for server_ in list(ProxyServers.values()):
            playerCount += server_.users
            servers.append({'name': server_.name, 'players': server_.users, 'ip': server_.address, 'enabled': server_.enabled})

        current_data = {'playerCount': playerCount,
                        'upSince': upStart,
                        'peakPlayers': peakPlayers, 'servers': servers}
        request.setHeader("content-type", "application/json")
        return json.dumps(current_data)

    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request)


class WEBRcon(Resource):
    isLeaf = True

    def render_GET(self, request):
        from Commands import Commands

        request.setHeader('content-type', "application/json")
        if 'key' not in request.args or request.args['key'][0] != web_config['rconpass']:
            return json.dumps({'success': False, 'reason': "Your RCON key is invalid!"})
        else:
            if 'command' not in request.args:
                return json.dumps({'success': False, 'reason': "Command not specified."})
            else:
                try:
                    if request.args['command'][0] in Commands:
                        Commands[request.args['command'][0]](request.args['params'][0] if 'params' in request.args else None)
                        return json.dumps({'success': True, 'output': "Command sent."})
                    else:
                        return json.dumps({'success': False, 'reason': "Command not found."})
                except Exception:
                    e = traceback.format_exc()
                    return json.dumps({'success': False, 'reason': "Error executing command\n%s" % e})


def setup_web():
    web_endpoint = TCP4ServerEndpoint(reactor, port)
    web_resource = WebAPI()
    web_resource.putChild("config.json", JSONConfig())
    web_resource.putChild("publickey.blob", PublicKey())
    web_resource.putChild("rcon", WEBRcon())
    web_endpoint.listen(server.Site(web_resource))

    print("[WEBAPI] WebAPI inited.")
