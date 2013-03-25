# -*- coding: utf-8 -*-
import string

from pysnmp.proto import rfc1902


class Port(object):
    """
    Represents a physical port on a switch.
    """
    def __init__(self, switch, identifier=None, base_port=None, alias=None):
        """
        Construct a new Port with the given `identifier`, `base_port` or current `alias` located on the given `switch`.
        """
        self.switch = switch
        # If an indentifier was given, infer the port index
        if identifier != None:
            unit = string.ascii_uppercase.index(identifier[0].upper())
            port = int(identifier[1:])
            self.base_port = unit * 24 + port
        elif base_port != None:
            self.base_port = base_port
        elif alias != None:
            # Get all aliases and look for the interface with the given alias
            ifAliases = self.switch.snmp_get_subtree(("ifAlias", ))
            # ifAliases is index by ifIndex, which is the same as dot1dBasePort for Ports
            matching_ifindexes = map(lambda oid: oid[0][-1],
                    filter(
                        lambda result: unicode(result[1]) == alias,
                        ifAliases)
                    )
            if len(matching_ifindexes) > 1:
                raise PortInstantiationError("Multiple ports with matching alias exist")
            elif len(matching_ifindexes) == 1:
                self.base_port = matching_ifindexes[0]
            elif len(matching_ifindexes) == 0:
                raise PortInstantiationError("No port with matching alias exists")
        else:
            raise PortInstantiationError("Port insufficiently specified")

    def __unicode__(self):
        return u"{0} on {1}".format(self.identifier, self.switch.hostname)

    def __eq__(self, other):
        return self.switch == other.switch and self.base_port == other.base_port

    def __ne__(self, other):
        return not self.__eq__(other)

    # Index of the interface that this port is a member of.
    ifindex = property(lambda self: self.base_port)

    # Port identifier corresponding to chassis labeling on the switch
    identifier = property(lambda self: string.ascii_uppercase[self.base_port / 24] + unicode(self.base_port % 24))

    def _get_alias(self):
        """
        Get the friendly name configured for this port.
        """
        ifAlias = self.switch.snmp_get(("ifAlias", self.ifindex))
        return unicode(ifAlias)

    def _set_alias(self, value):
        """
        Configure the name `value` as the friendly name for this port.
        """
        # Make sure that the name is legal according to the allowed interface names detailed in section 2-23 of the HP
        # Management and Configuration Guide
        assert(all(map(lambda letter: letter in (string.ascii_letters + string.digits), value)))
        # Set the new alias on the switch
        self.switch.snmp_set((("ifAlias", self.ifindex), rfc1902.OctetString(value)))


    alias = property(_get_alias, _set_alias)

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
        self.switch.snmp_set((("ifAdminStatus", self.ifindex), rfc1902.Integer(1 if value else 2)))

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
        # Import vlan.VLAN here to avoid circular import
        from vlan import VLAN
        untagged_vlan = VLAN(self.switch, int(self.switch.snmp_get(("dot1qPvid", self.base_port))))
        # If no untagged VLAN is configured, dot1qPvid is still DEFAULT_VLAN,
        # so check if the port is really in the VLAN
        if self in untagged_vlan.untagged_ports:
            return untagged_vlan
        else:
            return None

    untagged_vlan = property(_get_untagged_vlan)

    def _get_tagged_vlans(self):
        """
        Get a list of the tagged VLANs configured on this port.
        """
        raise NotImplementedError

    tagged_vlans = property(_get_tagged_vlans)


class PortInstantiationError(Exception):
    pass
