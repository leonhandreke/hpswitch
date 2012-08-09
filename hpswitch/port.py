# -*- coding: utf-8 -*-

from pysnmp.proto import rfc1902

class Port(object):
    """
    Represents a physical port on a switch.
    """
    def __init__(self, switch, identifier):
        """
        Construct a new Port with the given `identifier` located on the given `switch`.
        """
        self.switch = switch
        self.identifier = identifier

    #@staticmethod
    #def _get_port_location_for_ifindex(ifindex):
    #    """
    #    Get the location of the port corresponding to the interface identified by `ifindex`.
    #
    #    Note: This assumption obviously only works for some interfaces (namely those directly corresponding to ports)
    #    and is therefore very shaky.
    #    """
    #    return ((ifindex - 1)/52, (ifindex - 1) % 52 + 1)

    @staticmethod
    def _get_ifindex_for_port_location(port_location):
        """
        Get the ifindex of the interface that the port identified by `port_location` is a member of.
        """
        unit, port = port_location
        return unit * 24 + port

    @staticmethod
    def _get_ifindex_for_port_identifier(port_identifier):
        """
        Get the ifindex of the interface that the port identified by `port_identifier` is a member of.
        """
        unit = string.ascii_uppercase.index(port_identifier[0].upper())
        port = int(port_identifier[1:])
        return self._get_ifindex_for_port_location((unit, port))

    _get_base_port_for_port_identifier = _get_ifindex_for_port_identifier
    _get_base_port_for_port_location = _get_ifindex_for_port_location

    # Index of the interface that this port is a member of.
    ifindex = property(lambda self: Port._get_ifindex_for_port_identifier(self.identifier))

    # dot1dBasePortEntry index
    base_port = property(lambda self: Port._get_base_port_for_port_identifier(self.identifier))

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
