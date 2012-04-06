import re
import ipaddress


class VLAN(object):
    """
    Represents a 802.1Q VLAN.
    """
    def __init__(self, switch, vid):
        """
        Constructs a new VLAN with the given VLAN ID `vid` on the given `switch`.
        """
        self.vid = vid
        self.switch = switch

    def _get_name(self):
        """
        The name configured for the VLAN.
        """
        run_output = self.switch.execute_command("show running-config vlan " + str(self.vid))
        # Try to extract the VLAN name, which may also contain spaces. This is achieved by greedily matching whitespace
        # at the end of the line and matching the `   name ` prefix a the beginning and using whatever remains of the
        # string as the VLAN name. The `name` group is matched in a non-greedy fashion as to not "eat up" all the
        # following whitespace which is not part of the name.
        name_match = re.search(r"^   name \"(?P<name>.*?)\"\s*$", run_output, re.MULTILINE)
        return name_match.group('name')

    def _set_name(self, value):
        # Make sure that the name is legal according to the allowed VLAN names detailed in section 1-40 of the HP
        # Advanced Traffic Management Guide
        assert(all(map(lambda illegal_char: illegal_char not in value, "\"\'@#$^&*")))
        # Issue the commands on the switch to set the new name.
        self.switch.execute_command("config")
        # Pass the name to the switch wrapped in quotes because the name could contain spaces.
        self.switch.execute_command("vlan {0} name \"{1}\"".format(self.vid, value))
        self.switch.execute_command("exit")

    name = property(_get_name, _set_name)

    def _get_ipv4_addresses(self):
        """
        Get the IPv4 addresses configured configured for this VLAN.
        """
        run_output = self.switch.execute_command("show running-config vlan " + str(self.vid))
        ipv4_address_matches = re.finditer(
                r"^   ip address " \
                        # Match the IPv4 address consisting of 4 groups of up to 3 digits
                        "(?P<address>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        " " \
                        # Match the IPv4 netmask consisting of 4 groups of up to 3 digits
                        "(?P<netmask>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        "\s*$",
                run_output, re.MULTILINE)

        addresses = []
        for match in ipv4_address_matches:
            addresses.append(ipaddress.IPv4Interface(match.group('address') + '/' + match.group('netmask')))

        return addresses

    ipv4_addresses = property(_get_ipv4_addresses)

    def add_ipv4_address(self, address):
        """
        Add the given IPv4 address to the VLAN.

        `address` should be of type ipaddress.IPv4Interface.
        """
        if type(address) is not ipaddress.IPv4Interface:
            raise TypeError("The given address to configure is not an ipaddress.IPv4Interface.")

        self.switch.execute_command('config')
        add_output = self.switch.execute_command('vlan {0} ip address {1}'.format(self.vid, address.with_prefixlen))
        self.switch.execute_command('exit')

        # HP switches seem to be somewhat picky about the IPv4 addresses they like. For example, running `vlan 1001 ip
        # address 192.168.1.1/32` results in the output `192.168.1.1/32: bad IP address.`.  Therefore, we try to catch
        # the worst things that could happen here.
        if "bad IP address" in add_output:
            raise Exception("IPv4 address {0} deemed \"bad\" by switch.".format(address.with_prefixlen))

        # Check if configuring the address failed because the address was already configured on this switch.
        if add_output == "The IP address (or subnet) {0} already exists.".format(address.with_prefixlen):
            raise Exception("The IPv4 address {0} could not be configured because it was already configured for " \
                    "this VLAN.".format(address.with_prefixlen))

    def remove_ipv4_address(self, address):
        """
        Remove the given IPv4 address from the VLAN.

        `address` should be of type ipaddress.IPv4Interface.
        """
        if type(address) is not ipaddress.IPv4Interface:
            raise TypeError("The given address to remove is not an ipaddress.IPv4Interface.")

        self.switch.execute_command('config')
        remove_output = self.switch.execute_command('no vlan {0} ip address {1}'.format(self.vid, address.with_prefixlen))
        self.switch.execute_command('exit')

        # Check if the address successfully removed or if it wasn't even configured.
        if remove_output == "The IP address {0} is not configured on this VLAN.".format(address.with_prefixlen):
            raise Exception("The IPv4 address {0} could not be removed because it is not configured for this " \
            "VLAN.".format(address.with_prefixlen))

    def _get_ipv6_addresses(self):
        """
        Get the IPv6 addresses configured for this VLAN.
        """
        run_output = self.switch.execute_command("show running-config vlan " + str(self.vid))
        ipv6_address_matches = re.finditer(
                r"^   ipv6 address " \
                        # Match the IPv6 address containing hex-digits, : and / to separate the netmask
                        "(?P<address>[0-9abcdefABCDEF:/]+)" \
                        "\s*$",
                run_output, re.MULTILINE)

        addresses = []
        for match in ipv6_address_matches:
            addresses.append(ipaddress.IPv6Interface(match.group('address')))

        return addresses

    ipv6_addresses = property(_get_ipv6_addresses)

    def add_ipv6_address(self, address):
        """
        Add the given IPv6 address to the VLAN.

        `address` should be of type ipaddress.IPv6Interface.
        """
        if type(address) is not ipaddress.IPv6Interface:
            raise TypeError("The given address to configure is not an ipaddress.IPv6Interface.")

        self.switch.execute_command('config')
        add_output = self.switch.execute_command('vlan {0} ipv6 address {1}'.format(self.vid, address.with_prefixlen))
        self.switch.execute_command('exit')

        # Check if configuring the address failed because the address this VLAN was already configured on the switch.
        if add_output == "The IP address (or subnet) {0} already exists.".format(address.with_prefixlen):
            raise Exception("The IPv6 address {0} could not be configured because it was already configured for " \
                    "this VLAN.".format(address.with_prefixlen))

    def remove_ipv6_address(self, address):
        """
        Remove the given IPv6 address from the VLAN.

        `address` should be of type ipaddress.IPv6Interface.
        """
        if type(address) is not ipaddress.IPv6Interface:
            raise TypeError("The given address to remove is not an ipaddress.IPv6Interface.")

        self.switch.execute_command('config')
        remove_output = self.switch.execute_command('no vlan {0} ipv6 address {1}'.format(self.vid, address.with_prefixlen))
        self.switch.execute_command('exit')

        # Check if the address on this VLAN was successfully removed or if it wasn't even configured on this switch.
        if remove_output == "The IP address {0} is not configured on this VLAN.".format(address.with_prefixlen):
            raise Exception("The IPv6 address {0} could not be removed because it is not configured for this " \
            "VLAN.".format(address.with_prefixlen))
