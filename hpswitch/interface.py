import re
import string

import vlan

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

    def _get_running_config_output(self):
        """
        Get the output of the `show running-config interface [identifier]` command for this interface.
        """
        run_output = self.switch.execute_command("show running-config interface " + str(self.identifier))

        # If an error was returned by the switch, raise an Exception.
        if "Module not present for port or invalid port" in run_output:
            raise Exception("Invalid interface identifier.")
        return run_output

    def _get_name(self):
        """
        Get the friendly name configured for this interface.
        """
        run_output = self._get_running_config_output()
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

    def _get_enabled(self):
        """
        Get the admin status of this interface.
        """
        run_output = self._get_running_config_output()
        disable_match = re.search(r"^   disable\s*$", run_output, re.MULTILINE)
        # If nothing hinting at a disabled port has been matched, return True, else False.
        return disable_match is None

    def _set_enabled(self, value):
        """
        Set the admin status of this interface.
        """
        self.switch.execute_command("config")
        if value:
            self.switch.execute_command("interface {0} enable".format(self.identifier))
        else:
            self.switch.execute_command("interface {0} disable".format(self.identifier))
        self.switch.execute_command("exit")

    enabled = property(_get_enabled, _set_enabled)

    def _get_untagged_vlan(self):
        """
        Get the untagged VLAN configured on this interface.
        None is returned in case no VLAN is configured as untagged on this interface.
        """
        run_output = self._get_running_config_output()
        untagged_match = re.search(r"^   untagged vlan (?P<vid>\d{1,4})\s*$", run_output, re.MULTILINE)

        if untagged_match:
            return vlan.VLAN(self.switch, int(untagged_match.group('vid')))
        return None

    untagged_vlan = property(_get_untagged_vlan)

    def _get_tagged_vlans(self):
        """
        Get a list of the tagged VLANs configured on this interface.
        """
        tagged_vlans = []

        run_output = self._get_running_config_output()

        # To extract the complicated string describing the tagged VLANs, greedily match whitespace at the end and take
        # the rest as the result.
        tagged_vlan_match = re.search(r"^   tagged vlan (?P<vlan_list_string>.*?)\s*$", run_output, re.MULTILINE)
        if tagged_vlan_match:
            # VLAN range descriptors in running-config are seperated by commas, so seperate them.
            vlan_range_strings = tagged_vlan_match.group('vlan_list_string').split(',')
            # Resolve each VLAN range individually.
            for vlan_range_string in vlan_range_strings:
                # If this is a range, the first and the last VLAN in the range are seperated by a hyphen. If the item is
                # only a single VLAN, splitting will do nothing.
                vlan_range_components = vlan_range_string.split('-')
                # Check if the current string describes a single VLAN.
                if len(vlan_range_components) is 1:
                    # Create and remember a VLAN object with the single VLAN that was found
                    tagged_vlans.append(vlan.VLAN(self.switch, int(vlan_range_components[0])))
                elif len(vlan_range_components) is 2:
                    # Iterate over the whole range given by the range string.
                    for vid_in_range in range(int(vlan_range_components[0]), int(vlan_range_components[1]) + 1):
                        # Append each VLAN in the range to the list of tagged VLANs.
                        tagged_vlans.append(vlan.VLAN(self.switch, vid_in_range))
                else:
                    raise Exception("Invalid VLAN range format encountered.")

        return tagged_vlans

    tagged_vlans = property(_get_tagged_vlans)
