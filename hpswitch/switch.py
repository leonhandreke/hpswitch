import ipaddress
import paramiko
import re

import route

class Switch(object):
    """
    Represents a generic HP Networking switch.
    """
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password

        # Establish a new SSH connection to the switch.

        # TODO: what happens if the connection drops?
        self._ssh_connection = paramiko.SSHClient()
        self._ssh_connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh_connection.connect(self.hostname,
                username=self.username, password=self.password,
                allow_agent=False)
        # Request a new pseudo-terminal and immediately resize it to something huge. Else, the switch will try to make
        # the output scrollable with a keyboard, which is somewhat hard to emulate in code.
        self._ssh_pty = self._ssh_connection.invoke_shell()
        self._ssh_pty.resize_pty(width = 1000000, height=1000000)
        # Receive the annoying HP welcome message and skip it immediately.
        self._ssh_pty.recv(9000)
        self._ssh_pty.send('\n')
        self._ssh_pty.recv(9000)

    def execute_command(self, command, timeout=5):
        """
        Execute a command on the switch using the SSH protocol.

        The `timeout` given in seconds dictates how long this method should wait for the switch to send the command
        output before raising a `socket.timeout` exception.

        Returns the output of the command.
        """
        # Set the timout for the SSH channel to return the command output and run the desired command.
        self._ssh_pty.settimeout(timeout)
        self._ssh_pty.send(command + '\n')

        recv_buffer = ''
        while True:
            # Receive lots of bytes so that in most cases, another `recv()` call is not required.
            recv_buffer += self._ssh_pty.recv(1000000)
            # Clean up the vt100 control sequences that the switch inserts. The regular expression is stolen from a
            # thread on [python-list](http://mail.python.org/pipermail/python-list/2009-September/1219674.html).
            recv_buffer = re.sub("\x1B[^A-Za-z]*?[A-Za-z]", '', recv_buffer)
            # Check if the received string ends with a `# ` shell-prompt. If so, it's pretty safe to assume that the
            # command has finished executing and all desired output has been received.
            if recv_buffer.endswith('# '):
                break

        # Strip off the command entered command at the beginning and the last line containing the shell prompt
        recv_buffer = re.sub(r"^" + command, "", recv_buffer)
        recv_buffer = re.sub(r"\r\n.*?# $", "", recv_buffer)

        return recv_buffer

    def _get_static_ipv4_routes(self):
        run_output = self.execute_command("show running-config")
        ipv4_route_matches = re.finditer(
                r"^ip route " \
                        # Match the IPv4 address consisting of 4 groups of up to 3 digits
                        "(?P<destination_address>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        " " \
                        # Match the IPv4 netmask consisting of 4 groups of up to 3 digits
                        "(?P<destination_netmask>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        " " \
                        # Match the gateway address consisting of 4 groups of up to 3 digits
                        "(?P<gateway>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        "\s*$",
                run_output, re.MULTILINE)

        routes = []
        for match in ipv4_route_matches:
            routes.append(
                    route.IPv4Route(
                        ipaddress.IPv4Network(match.group('destination_address') + '/' + match.group('destination_netmask')),
                        ipaddress.IPv4Address(match.group('gateway'))
                        )
                    )

        return routes

    static_ipv4_routes = property(_get_static_ipv4_routes)

    def add_static_ipv4_route(self, add_route):
        if type(add_route) is not route.IPv4Route:
            raise Exception("Given route to add is not of type IPv4Route.")

        self.execute_command("config")
        route_output = self.execute_command("ip route {route.destination} {route.gateway}".format(route=add_route))
        self.execute_command("exit")

    def remove_static_ipv4_route(self, remove_route):
        if type(remove_route) is not route.IPv4Route:
            raise Exception("Given route to remove is not of type IPv4Route.")

        self.execute_command("config")
        route_output = self.execute_command(
                "no ip route {route.destination} {route.gateway}".format(route=remove_route)
                )
        self.execute_command("exit")

        if route_output == "The route not found or not configurable.":
            raise Exception("The route {route} could not be removed because it is not configured on this " \
                    "switch.".format(route=remove_route))

    def _get_static_ipv6_routes(self):
        """
        Get all static IPv6 routes configured on this switch.
        """
        run_output = self.execute_command("show running-config")
        ipv6_route_matches = re.finditer(
                r"^ipv6 route " \
                        # Match the IPv6 address containing hex-digits, : and / to separate the netmask
                        "(?P<destination>[0-9abcdefABCDEF:/]+)" \
                        " " \
                        # Match the IPv6 address of the gateway, which should not contain a /
                        "(?P<gateway>[0-9abcdefABCDEF:]+)" \
                        "\s*$",
                run_output, re.MULTILINE)

        routes = []
        for match in ipv6_route_matches:
            routes.append(
                    route.IPv6Route(
                        ipaddress.IPv6Network(match.group('destination')),
                        ipaddress.IPv6Address(match.group('gateway'))
                        )
                    )

        return routes

    static_ipv6_routes = property(_get_static_ipv6_routes)

    def add_static_ipv6_route(self, add_route):
        """
        Add the static IPv6 route `add_route` to the switch configuration.
        """
        if type(add_route) is not route.IPv6Route:
            raise Exception("Given route to add is not of type IPv6Route.")

        self.execute_command("config")
        route_output = self.execute_command("ipv6 route {route.destination} {route.gateway}".format(route=add_route))
        self.execute_command("exit")

    def remove_static_ipv6_route(self, remove_route):
        """
        Remove the static IPv6 route `remove_route` from the switch configuration.
        """
        if type(remove_route) is not route.IPv6Route:
            raise Exception("Given route to remove is not of type IPv6Route.")

        self.execute_command("config")
        route_output = self.execute_command(
                "no ipv6 route {route.destination} {route.gateway}".format(route=remove_route)
                )
        self.execute_command("exit")

        if route_output == "The route not found or not configurable.":
            raise Exception("The route {route} could not be removed because it is not configured on this " \
                    "switch.".format(route=remove_route))
