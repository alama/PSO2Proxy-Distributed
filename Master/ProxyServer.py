__author__ = 'Sean'

ProxyServers = {}


class ProxyServer(object):
    def __init__(self, address, name):
        self.address = address
        self.name = name
        self.users = 0
        self.enabled = True
