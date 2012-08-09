# -*- coding: utf-8 -*-

import string
import sys

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.smi import builder, view

import ipaddress

class Switch(object):
    """
    Represents a generic HP Networking switch.
    """
    def __init__(self, hostname, community="public"):
        self.hostname = hostname
        self.community = community

        mib_builder = builder.MibBuilder()
        mib_builder.setMibPath(*(mib_builder.getMibPath() + (sys.path[0],)))
        mib_builder.loadModules('RFC1213-MIB', 'BRIDGE-MIB', 'IF-MIB', 'Q-BRIDGE-MIB', 'IP-MIB', 'HP-ICF-IPCONFIG')

        self.mib_view_controller = view.MibViewController(mib_builder)

        self.command_generator = cmdgen.CommandGenerator()
        self.command_generator.mibViewController = view.MibViewController(mib_builder)

    def _get_oid_for_managed_object_name(self, name):
        """
        Translade a MIB object name to an OID
        """
        oid, label, suffix = self.mib_view_controller.getNodeName(name)
        return oid + suffix

    def _get_port_location_for_ifindex(self, ifindex):
        return ((ifindex - 1)/52 + 1, (ifindex - 1) % 52 + 1)

    def _get_ifindex_for_port_location(self, port_location):
        unit, port = port_location
        return (unit - 1)*24 + port

    def _get_ifindex_for_port_identifier(self, port_identifier):
        unit = string.ascii_uppercase.index(port_identifier[0].upper()) + 1
        port = int(port_identifier[1:])
        return self._get_ifindex_for_port_location((unit, port))

    def snmp_get(self, oid):
        errorIndication, errorStatus, errorIndex, varBinds = self.command_generator.getCmd(
                cmdgen.CommunityData('my-agent', self.community, 1),
                cmdgen.UdpTransportTarget((self.hostname, 161), timeout=8, retries=5),
                self._get_oid_for_managed_object_name(oid)
                )
        return varBinds[0][1]

    def snmp_set(self, *var_binds):
        errorIndication, errorStatus, errorIndex, varBinds = self.command_generator.setCmd(
                cmdgen.CommunityData('my-agent', self.community, 1),
                cmdgen.UdpTransportTarget((self.hostname, 161), timeout=8, retries=5),
                *[(self._get_oid_for_managed_object_name(oid), value) for (oid, value) in var_binds]
                )
        return varBinds[0][1]

    def snmp_get_subtree(self, oid):
        errorIndication, errorStatus, errorIndex, varBinds = self.command_generator.nextCmd(
                cmdgen.CommunityData('my-agent', self.community, 1),
                cmdgen.UdpTransportTarget((self.hostname, 161), timeout=8, retries=5),
                self._get_oid_for_managed_object_name(oid)
                )
        return [tuple(x[0]) for x in varBinds]


    # == Static route management ==

    # === IPv4 static route management ===

    def _get_static_ipv4_routes(self):
        """
        Get all static IPv4 routes configured on this switch.
        """
        pass

    static_ipv4_routes = property(_get_static_ipv4_routes)

    def add_static_ipv4_route(self, add_route):
        """
        Add the static IPv4 route `add_route` to the switch configuration.
        """
        pass

    def remove_static_ipv4_route(self, remove_route):
        """
        Remove the static route `remove_route` from the switch configuration.
        """
        pass

    # === IPv6 static route management ===

    def _get_static_ipv6_routes(self):
        """
        Get all static IPv6 routes configured on this switch.
        """
        pass

    static_ipv6_routes = property(_get_static_ipv6_routes)

    def add_static_ipv6_route(self, add_route):
        """
        Add the static IPv6 route `add_route` to the switch configuration.
        """
        pass

    def remove_static_ipv6_route(self, remove_route):
        """
        Remove the static IPv6 route `remove_route` from the switch configuration.
        """
        pass
