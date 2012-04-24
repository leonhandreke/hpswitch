import re
import ipaddress

import interface

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

    def __eq__(self, other):
        return self.vid == other.vid and self.switch == other.switch

    def _get_running_config_output(self):
        """
        Get the output of the `show running-config vlan [vid]` command for this interface.
        """
        run_output = self.switch.execute_command("show running-config vlan " + str(self.vid))
        if "VLAN configuration is not available" in run_output:
            raise Exception("VLAN {0} is not configured on the switch {1}.".format(self.vid, self.switch.hostname))
        return run_output

    def _get_name(self):
        """
        The name configured for the VLAN.
        """
        run_output = self._get_running_config_output()
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
        run_output = self._get_running_config_output()
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
        run_output = self._get_running_config_output()
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
        self.switch.execute_command('config')
        remove_output = self.switch.execute_command('no vlan {0} ipv6 address {1}'.format(self.vid, address.with_prefixlen))
        self.switch.execute_command('exit')

        # Check if the address on this VLAN was successfully removed or if it wasn't even configured on this switch.
        if remove_output == "The IP address {0} is not configured on this VLAN.".format(address.with_prefixlen):
            raise Exception("The IPv6 address {0} could not be removed because it is not configured for this " \
            "VLAN.".format(address.with_prefixlen))


    def _interface_list_from_interface_list_string(self, interface_list_string):
        """
        Given a complicated interface list string output by the `show running-config` command, return a list of
        Interface objects described by this string.
        """
        interface_list = []

        # Ranges are seperated by commas, so split them up first.
        interface_range_strings = interface_list_string.split(',')
        # Resolve each interface range individually.
        for interface_range_string in interface_range_strings:
            # If this string is a range, the first and the last interface in the range are seperated by a hyphen. If the
            # item is only a single interface, splitting will do nothing.
            interface_range_components = interface_range_string.split('-')
            # Check if the current string describes only a single interface.
            if len(interface_range_components) is 1:
                # Create and remember the single interface that was found in the list to return.
                interface_list.append(interface.Interface(self.switch, interface_range_components[0]))
            # Check if the current string describes a range of interfaces.
            elif len(interface_range_components) is 2:
                # Interface ranges always have a common prefix consisting only of letters. Find out what this component
                # is.
                interface_alpha_component = re.split('([a-zA-Z]+)', interface_range_components[0])[1]
                # Strip off this non-numeric alpha component from the range components to receive numeric ranges.
                interface_range_start = int(interface_range_components[0][len(interface_alpha_component):])
                interface_range_end = int(interface_range_components[1][len(interface_alpha_component):])
                # For each of the numbers in the range, prepend the alpha component to construct the final interface
                # identifier string.
                for i in range(interface_range_start, interface_range_end + 1):
                    # Add the found interface to the list of interfaces to return.
                    interface_list.append(interface.Interface(self.switch, interface_alpha_component + str(i)))
            else:
                raise Exception("Invalid interface range format encountered.")

        return interface_list

    def _get_tagged_interfaces(self):
        """
        Get a list of interface that have this VLAN configured as tagged.
        """
        run_output = self._get_running_config_output()
        tagged_match = re.search(r"^   tagged (?P<tagged_vlan_list_string>.*?)\s*$", run_output, re.MULTILINE)
        # If no interfaces have this VLAN configured as tagged, return an empty list.
        if not tagged_match:
            return []

        return self._interface_list_from_interface_list_string(tagged_match.group('tagged_vlan_list_string'))

    tagged_interfaces = property(_get_tagged_interfaces)

    def add_tagged_interface(self, interface):
        """
        Configure this VLAN as tagged on the Interface `interface`.
        """
        self.switch.execute_command('config')
        add_output = self.switch.execute_command('vlan {0} tagged {1}'.format(self.vid, interface.identifier))
        self.switch.execute_command('exit')

    def remove_tagged_interface(self, interface):
        """
        Remove this VLAN as tagged from the Interface `interface`.
        """
        self.switch.execute_command('config')
        add_output = self.switch.execute_command('no vlan {0} tagged {1}'.format(self.vid, interface.identifier))
        self.switch.execute_command('exit')

    def _get_untagged_interfaces(self):
        """
        Get a list of interface that have this VLAN configured as untagged.
        """
        run_output = self._get_running_config_output()
        untagged_match = re.search(r"^   untagged (?P<untagged_vlan_list_string>.*?)\s*$", run_output, re.MULTILINE)
        # If no interfaces have this VLAN configured as untagged, return an empty list.
        if not untagged_match:
            return []

        return self._interface_list_from_interface_list_string(untagged_match.group('untagged_vlan_list_string'))

    untagged_interfaces = property(_get_untagged_interfaces)

    def add_untagged_interface(self, interface):
        """
        Configure this VLAN as untagged on the Interface `interface`.
        """
        self.switch.execute_command('config')
        add_output = self.switch.execute_command('vlan {0} untagged {1}'.format(self.vid, interface.identifier))
        self.switch.execute_command('exit')

    def remove_untagged_interface(self, interface):
        """
        Remove this VLAN as untagged from the Interface `interface`.
        """
        self.switch.execute_command('config')
        add_output = self.switch.execute_command('no vlan {0} untagged {1}'.format(self.vid, interface.identifier))
        self.switch.execute_command('exit')
