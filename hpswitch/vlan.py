import re
import ipaddress

class VLAN(object):
    """
    Represents a 802.1Q VLAN.
    """
    def __init__(self, switch, identifier):
        """
        Constructs a new VLAN and retrieves its attributes from the given `switch` by using the given `identifier`.

        `identifier` should either be a VLAN name or a valid VID, ready to be passed to the `show vlans` command.
        """
        self.switch = switch
        # The name `ipv4_interfaces` is really a bit of a misnomer here. An "Interface" is what the `ipaddress` module
        # calls a hybrid construct that represents "an IP address on a network", i.e. an address and a netmask. To make
        # things more clear, this name is reused here.
        self._ipv4_interfaces = []
        self._get_attributes(identifier)

    def _get_attributes(self, identifier):
        """
        Fetch attributes of the VLAN from the switch.
        """
        show_output = self.switch.execute_command("show vlans " + str(identifier))

        # When matching the attributes in the output, use `re.MULTILINE` mode to be able to match the beginning and the
        # end of a line using the `^` and `$` operators.

        # Try to match the the VID, which may be up to 4 digits long. Immediately convert it to an Integer, because
        # that's what it should be when it is retrieved.
        self._vid = int(re.search(r"^  VLAN ID : (?P<vid>\d{1,4})\s*$", show_output, re.MULTILINE).group('vid'))

        # Try to extract the VLAN name, which may also contain spaces. This is achieved by greedily matching whitespace
        # at the end of the line and matching the `  Name : ` prefix a the beginning and using whatever remains of the
        # string as the VLAN name. The `name` group is matched in a non-greedy fashion as to not "eat up" all the
        # following whitespace which is not part of the name.
        self._name = re.search(r"^  Name : (?P<name>.*?)\s*$", show_output, re.MULTILINE).group('name')

        # Run the `show vlans` command with three custom columns: The VID to identify the VLAN and the IPv4 address and
        # netmask
        show_output = self.switch.execute_command("show vlans custom id ipaddr ipmask")


        ipv4_address_matches = re.finditer(
                # Try to match a VID ad the beginning of the line, although this field could be empty because the line
                # might only contain IP addresses belonging to the VLAN on the previous line
                r"^ (?P<vid>\d{0,4})\s*" \
                        # Match the IPv4 address consisting of 4 groups of up to 4 digits
                        "(?P<address>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        "\s*" \
                        # Match the IPv4 netmask consisting of 4 groups of up to 4 digits
                        "(?P<netmask>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}))" \
                        "\s*$",
                show_output, re.MULTILINE)

        # `vlan_found` indicates, if the VLAN has already been found in the list. After the first line belonging to the
        # sought VLAN is seen, this value is set to `True` and all following lines without a VID explicitly given are
        # attributed to this VLAN.
        vlan_found = False
        for match_line in ipv4_address_matches:
            match_vid = match_line.group('vid')
            match_interface = ipaddress.IPv4Interface(match_line.group('address') + '/' + match_line.group('netmask'))
            if vlan_found:
                if match_vid == '':
                    self._ipv4_interfaces.append(match_interface)
                else:
                    # Another VID has been found, which means that this line no longer implicitly belongs to the found
                    # VLAN but gives information about another VLAN that we don't care about.
                    break
            elif match_vid == str(self._vid):
                self._ipv4_interfaces.append(match_interface)
                vlan_found = True

    @property
    def name(self):
        """
        The name configured for the VLAN.
        """
        return self._name

    @name.setter
    def name(self, value):
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

    @property
    def vid(self):
        return self._vid

    @property
    def ipv4_interfaces(self):
        """
        The IPv4 addresses configured, together with their netmasks called "interfaces" configured on this VLAN.
        """
        return self._ipv4_interfaces
