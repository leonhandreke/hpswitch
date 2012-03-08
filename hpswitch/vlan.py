import re

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

