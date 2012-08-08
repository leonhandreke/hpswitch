# -*- coding: utf-8 -*-
import struct

from pysnmp.proto import rfc1902
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


    def _get_ifindex(self):
        # TODO: is this correct?
        return self.vid + 577

    ifindex = property(_get_ifindex)

    def __eq__(self, other):
        return self.vid == other.vid and self.switch == other.switch

    def _get_name(self):
        """
        The name configured for the VLAN.
        """
        return unicode(self.switch.snmp_get(("dot1qVlanStaticName", self.vid)))

    def _set_name(self, value):
        # Make sure that the name is legal according to the allowed VLAN names detailed in section 1-40 of the HP
        # Advanced Traffic Management Guide
        assert(all(map(lambda illegal_char: illegal_char not in value, "\"\'@#$^&*")))
        self.switch.snmp_set((("dot1qVlanStaticName", self.vid), rfc1902.OctetString(value)))

    name = property(_get_name, _set_name)

    def _get_ipv4_addresses(self):
        """
        Get the IPv4 addresses configured configured for this VLAN.
        """
        # Get all address Entries in hpicfIpAddressTable
        hpicfIpAddressEntries = self.switch.snmp_get_subtree(("hpicfIpAddressEntry", ))
        vlan_ipv4_address_prefix_length_entries = filter(
                # oid[17] contains the ifindex
                lambda result: result[0][17] == self.ifindex
                # oid[18] is 1 for IPv4 addresses
                and result[0][18] == 1
                # hpicfIpAddressPrefixLength is oid[16] == 3
                and result[0][16] == 3,
                hpicfIpAddressEntries)

        ipv4_addresses = []
        for result in vlan_ipv4_address_prefix_length_entries:
            # Build an IPv4 address from the last 4 components of the oid
            ipv4_address_string = reduce(lambda a, b: a + "." + b, map(unicode, tuple(result[0][-4:])))
            ipv4_prefix_length_string = unicode(result[1])
            ipv4_addresses.append(ipaddress.IPv4Interface(ipv4_address_string + "/" + ipv4_prefix_length_string))
        return ipv4_addresses

    ipv4_addresses = property(_get_ipv4_addresses)

    def add_ipv4_address(self, address):
        """
        Add the given IPv4 address to the VLAN.

        `address` should be of type ipaddress.IPv4Interface.
        """
        ipv4_address_tuple = struct.unpack("4B", address.packed)
        self.switch.snmp_set(
                (("ipv4InterfaceEnableStatus", self.ifindex), rfc1902.Integer(1)),
                # hpicfIpv4InterfaceDhcpEnable off
                (("hpicfIpv4InterfaceDhcpEnable", self.ifindex), rfc1902.Integer(2)),
                (("hpicfIpAddressPrefixLength", self.ifindex, 1, 4) + ipv4_address_tuple,
                    rfc1902.Gauge32(address.prefixlen)),
                # hpicfIpAddressType IPv4
                (("hpicfIpAddressType", self.ifindex, 1, 4) + ipv4_address_tuple, rfc1902.Integer(1)),
                # hpicfIpAddressRowStatus createAndGo 4
                (("hpicfIpAddressRowStatus", self.ifindex, 1, 4) + ipv4_address_tuple, rfc1902.Integer(4))
                )

    def remove_ipv4_address(self, address):
        """
        Remove the given IPv4 address from the VLAN.

        `address` should be of type ipaddress.IPv4Interface.
        """
        ipv4_address_tuple = struct.unpack("4B", address.packed)
        self.switch.snmp_set(
                # hpicfIpAddressRowStatus destroy 6
                (("hpicfIpAddressRowStatus", self.ifindex, 1, 4) + ipv4_address_tuple, rfc1902.Integer(6))
                )

    def _get_ipv6_addresses(self):
        """
        Get the IPv6 addresses configured for this VLAN.
        """
        # Get all address Entries in hpicfIpAddressTable
        hpicfIpAddressEntries = self.switch.snmp_get_subtree(("hpicfIpAddressEntry", ))
        vlan_ipv6_address_prefix_length_entries = filter(
                # oid[17] contains the ifindex
                lambda result: result[0][17] == self.ifindex
                # oid[18] is 2 for IPv6 addresses
                and result[0][18] == 2
                # hpicfIpAddressPrefixLength is oid[16] == 3
                and result[0][16] == 3,
                hpicfIpAddressEntries)

        ipv6_addresses = []
        for result in vlan_ipv6_address_prefix_length_entries:
            # Build an IPv6 address from the last 16 components of the oid
            ipv6_address_string_without_colons = reduce(
                    lambda a, b: a + b, 
                    map(lambda x: unicode("%02x" % x), tuple(result[0][-16:]))
                    )
            ipv6_address_string = ""
            while True:
                ipv6_address_string += ipv6_address_string_without_colons[:4]
                ipv6_address_string_without_colons = ipv6_address_string_without_colons[4:]
                if len(ipv6_address_string_without_colons) != 0:
                    ipv6_address_string += ":"
                else:
                    break

            ipv6_prefix_length_string = unicode(result[1])
            ipv6_addresses.append(ipaddress.IPv6Interface(ipv6_address_string + "/" + ipv6_prefix_length_string))
        return ipv6_addresses

    ipv6_addresses = property(_get_ipv6_addresses)

    def add_ipv6_address(self, address):
        """
        Add the given IPv6 address to the VLAN.

        `address` should be of type ipaddress.IPv6Interface.
        """
        ipv6_address_tuple = struct.unpack("16B", address.packed)
        self.switch.snmp_set(
                (("ipv6InterfaceEnableStatus", self.ifindex), rfc1902.Integer(1)),
                #(("hpicfIpv4InterfaceDhcpEnable", self.ifindex), rfc1902.Integer(2)),
                (("hpicfIpAddressPrefixLength", self.ifindex, 2, 16) + ipv6_address_tuple,
                    rfc1902.Gauge32(address.prefixlen)),
                # hpicfIpAddressType IPv6
                (("hpicfIpAddressType", self.ifindex, 2, 16) + ipv6_address_tuple, rfc1902.Integer(1)),
                # hpicfIpAddressRowStatus createAndGo 4
                (("hpicfIpAddressRowStatus", self.ifindex, 2, 16) + ipv6_address_tuple, rfc1902.Integer(4))
                )

    def remove_ipv6_address(self, address):
        """
        Remove the given IPv6 address from the VLAN.

        `address` should be of type ipaddress.IPv6Interface.
        """
        ipv6_address_tuple = struct.unpack("16B", address.packed)
        self.switch.snmp_set(
                # hpicfIpAddressRowStatus destroy 6
                (("hpicfIpAddressRowStatus", self.ifindex, 2, 16) + ipv6_address_tuple, rfc1902.Integer(6))
                )


    def _get_tagged_interfaces(self):
        """
        Get a list of interface that have this VLAN configured as tagged.
        """
        pass

    tagged_interfaces = property(_get_tagged_interfaces)

    def add_tagged_interface(self, interface):
        """
        Configure this VLAN as tagged on the Interface `interface`.
        """
        pass

    def remove_tagged_interface(self, interface):
        """
        Remove this VLAN as tagged from the Interface `interface`.
        """
        pass

    def _get_untagged_interfaces(self):
        """
        Get a list of interface that have this VLAN configured as untagged.
        """
        pass

    untagged_interfaces = property(_get_untagged_interfaces)

    def add_untagged_interface(self, interface):
        """
        Configure this VLAN as untagged on the Interface `interface`.
        """
        pass

    def remove_untagged_interface(self, interface):
        """
        Remove this VLAN as untagged from the Interface `interface`.
        """
        pass
