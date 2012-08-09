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
        Translate a MIB object name to an OID
        """
        oid, label, suffix = self.mib_view_controller.getNodeName(name)
        return oid + suffix

    def snmp_get(self, oid):
        """
        Perform an SNMP GET request on the switch.

        Returns the value returned by the switch.
        """
        errorIndication, errorStatus, errorIndex, varBinds = self.command_generator.getCmd(
                cmdgen.CommunityData('hpswitch', self.community, 1),
                cmdgen.UdpTransportTarget((self.hostname, 161), timeout=8, retries=5),
                self._get_oid_for_managed_object_name(oid)
                )
        return varBinds[0][1]

    def snmp_set(self, *var_binds):
        """
        Perform an SNMP SET request on the switch.

        Takes an arbitrary number of (oid, value) pairs as arguments.
        """
        errorIndication, errorStatus, errorIndex, varBinds = self.command_generator.setCmd(
                cmdgen.CommunityData('hpswitch', self.community, 1),
                cmdgen.UdpTransportTarget((self.hostname, 161), timeout=8, retries=5),
                *[(self._get_oid_for_managed_object_name(oid), value) for (oid, value) in var_binds]
                )

    def snmp_get_subtree(self, oid):
        """
        Recursively get all objects that have `oid` as a parent using SNMP GETNEXT.

        Returns a list of (oid, value) pairs.
        """
        errorIndication, errorStatus, errorIndex, varBinds = self.command_generator.nextCmd(
                cmdgen.CommunityData('hpswitch', self.community, 1),
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
