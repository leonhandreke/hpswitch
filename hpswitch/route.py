import ipaddress


class Route(object):
    """
    An IP route conisting of a destination network and a gateway router.

    This class is not designed to be instantiated directly. Please use the the protocol-specific `IPv4Route` and
    `IPv6Route` instead.
    """
    def __init__(self, destination, gateway):
        self.destination = destination
        self.gateway = gateway

    def __str__(self):
        return str(self.destination) + " via " + str(self.gateway)


class IPv4Route(Route):
    pass


class IPv6Route(Route):
    pass
