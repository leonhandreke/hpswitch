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
    def __init__(self, destination, gateway):
        if type(destination) is not ipaddress.IPv4Network:
            raise Exception("Given destination network is not of type ipaddress.IPv4Network.")
        if type(gateway) is not ipaddress.IPv4Address:
            raise Exception("Given gateway address is not of type ipaddress.IPv4Address.")

        super(IPv4Route, self).__init__(destination, gateway)


class IPv6Route(Route):
    def __init__(self, destination, gateway):
        if type(destination) is not ipaddress.IPv6Network:
            raise Exception("Given destination network is not of type ipaddress.IPv6Network.")
        if type(gateway) is not ipaddress.IPv6Address:
            raise Exception("Given gateway address is not of type ipaddress.IPv6Address.")

        super(IPv6Route, self).__init__(destination, gateway)
