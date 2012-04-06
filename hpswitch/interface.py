import re
import string

class Interface(object):
    """
    Represents a physical interface on a switch.
    """
    def __init__(self, switch, identifier):
        """
        Construct a new Interface with the given `identifier` located on the given `switch`.
        """
        self.switch = switch
        self.identifier = identifier

    def _get_name(self):
        """
        Get the friendly name configured for this interface.
        """
        run_output = self.switch.execute_command("show running-config interface " + str(self.identifier))
        # Try to extract the interface name, which may also contain spaces. This is achieved by greedily matching
        # whitespace at the end of the line and matching the `   name ` prefix a the beginning and using whatever
        # remains of the string as the interface name. The `name` group is matched in a non-greedy fashion as to not
        # "eat up" all the following whitespace which is not part of the name.
        name_match = re.search(r"^   name \"(?P<name>.*?)\"\s*$", run_output, re.MULTILINE)
        # Only return the name of the interface if a name was found.
        if name_match:
            return name_match.group('name')
        # If no name was configured, return None.
        return None

    def _set_name(self, value):
        """
        Configure the name `value` as the friendly name for this interface.
        """
        # Make sure that the name is legal according to the allowed interface names detailed in section 2-23 of the HP
        # Management and Configuration Guide
        assert(all(map(lambda letter: letter in (string.ascii_letters + string.digits), value)))
        # Issue the commands on the switch to set the new name.
        self.switch.execute_command("config")
        self.switch.execute_command("interface {0} name {1}".format(self.identifier, value))
        self.switch.execute_command("exit")

    def _del_name(self):
        """
        Deconfigure the friendly name on this interface.
        """
        self.switch.execute_command("config")
        self.switch.execute_command("no interface {0} name".format(self.identifier))
        self.switch.execute_command("exit")

    name = property(_get_name, _set_name, _del_name)
