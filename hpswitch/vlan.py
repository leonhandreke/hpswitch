import re
import ipaddress


class VLAN(object):
    """
    Represents a 802.1Q VLAN.
    """
    def __init__(self, switch, vid):
        """
        Constructs a new VLAN and retrieves its attributes from the given `switch` by using the given VID.
        """
        self.vid = vid
        self.switch = switch

    def _get_name(self):
        """
        The name configured for the VLAN.
        """
        run_output = self.switch.execute_command("show run vlan " + str(self.vid))
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
        # Update the internally-cached attribute with the newly-set value.
        self._name = value

    name = property(_get_name, _set_name)

    def _get_ipv4_interfaces(self):
        """
        Get the IPv4 addresses configured, together with their netmasks called "interfaces" configured on this VLAN.
        """
        run_output = self.switch.execute_command("show run vlan " + str(self.vid))
        ipv4_address_matches = re.finditer(
                r"^   ip address " \
                        # Match the IPv4 address consisting of 4 groups of up to 4 digits
                        "(?P<address>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        " " \
                        # Match the IPv4 netmask consisting of 4 groups of up to 4 digits
                        "(?P<netmask>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        "\s*$",
                run_output, re.MULTILINE)

        interfaces = []
        for match in ipv4_address_matches:
            interfaces.append(ipaddress.IPv4Interface(match.group('address') + '/' + match.group('netmask')))

        return interfaces

    ipv4_interfaces = property(_get_ipv4_interfaces)

    def add_ipv4_interface(self, interface):
        """
        Add the given IPv4 interface to the VLAN.
        """
        self.switch.execute_command('config')
        add_output = self.switch.execute_command('vlan {0} ip address {1}'.format(self.vid, interface.with_prefixlen))
        self.switch.execute_command('exit')

        # HP switches seem to be somewhat picky about the IPv4 addresses they like to assign to interfaces. For example,
        # running `vlan 1001 ip address 192.168.1.1/32` results in the output `192.168.1.1/32: bad IP address.`.
        # Therefore, we try to catch the worst things that could happen here.
        if "bad IP address" in add_output:
            raise Exception("IPv4 address {0} deemed \"bad\" by switch.".format(interface.with_prefixlen))

        # Check if configuring the interface failed because the interface that we thought would not yet be configured on
        # this VLAN was already configured on the switch.
        if add_output == "The IP address (or subnet) {0} already exists.".format(interface.with_prefixlen):
            raise Exception("The IPv4 interface {0} could not be configured because it was already configured for " \
                    "this VLAN.".format(interface.with_prefixlen))

    def remove_ipv4_interface(self, interface):
        """
        Remove the given IPv4 interface from the VLAN.
        """
        self.switch.execute_command('config')
        remove_output = self.switch.execute_command('no vlan {0} ip address {1}'.format(self.vid, interface.with_prefixlen))
        self.switch.execute_command('exit')

        # Check if the interface that we thought would be configured on this VLAN was successfully removed or if it
        # didn't even exist and our `ipv4_interfaces` list was inconsistent.
        if remove_output == "The IP address {0} is not configured on this VLAN.".format(interface.with_prefixlen):
            raise Exception("The IPv4 interface {0} could not be removed because it is not configured on this " \
            "VLAN.".format(interface.with_prefixlen))
