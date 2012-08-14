# -*- coding: utf-8 -*-
import string

from pysnmp.proto import rfc1902

class Port(object):
    """
    Represents a physical port on a switch.
    """
    def __init__(self, switch, identifier=None, base_port=None):
        """
        Construct a new Port with the given `identifier` located on the given `switch`.
        """
        self.switch = switch
        # If an indentifier was given, infer the port index
        if identifier != None:
            unit = string.ascii_uppercase.index(identifier[0].upper())
            port = int(identifier[1:])
            self.base_port = unit * 24 + port
        else:
            self.base_port = base_port

    # Index of the interface that this port is a member of.
    ifindex = property(lambda self: self.base_port)

    # Port identifier corresponding to chassis labeling on the switch
    identifier = property(lambda self: string.ascii_uppercase[self.base_port / 8] + unicode(self.base_port % 8))

    def _get_name(self):
        """
        Get the friendly name configured for this port.
        """
        raise NotImplementedError

    def _set_name(self, value):
        """
        Configure the name `value` as the friendly name for this port.
        """
        # Make sure that the name is legal according to the allowed interface names detailed in section 2-23 of the HP
        # Management and Configuration Guide
        assert(all(map(lambda letter: letter in (string.ascii_letters + string.digits), value)))
        # Issue the commands on the switch to set the new name.
        raise NotImplementedError

    def _del_name(self):
        """
        Deconfigure the friendly name on this port.
        """
        raise NotImplementedError

    name = property(_get_name, _set_name, _del_name)

    def _get_enabled(self):
        """
        Get the admin status of this port.
        """
        ifAdminStatus = self.switch.snmp_get(("ifAdminStatus", self.ifindex))
        return int(ifAdminStatus) == 1

    def _set_enabled(self, value):
        """
        Set the admin status of this port.
        """
        # ifAdminStatus 1 means up, 2 means down
        self.switch.snmp_set(("ifAdminStatus", self.ifindex), rfc1902.Integer(1 if value else 2))

    enabled = property(_get_enabled, _set_enabled)

    def _get_operational(self):
        """
        Get the operational status of this port.
        """
        ifOperStatus = self.switch.snmp_get(("ifOperStatus", self.ifindex))
        return int(ifOperStatus) == 1

    operational = property(_get_operational)

    def _get_untagged_vlan(self):
        """
        Get the untagged VLAN configured on this port.
        """
        return int(self.switch.snmp_get(("dot1qPvid", self.base_port)))

    untagged_vlan = property(_get_untagged_vlan)

    def _get_tagged_vlans(self):
        """
        Get a list of the tagged VLANs configured on this port.
        """
        raise NotImplementedError

    tagged_vlans = property(_get_tagged_vlans)
