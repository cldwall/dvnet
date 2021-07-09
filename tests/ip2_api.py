import unittest

# As our project contains several packages under ../src
    # we are adding said directory to python's path so
    # that the coloured_formatter class can be imported.
import sys, os
sys.path.insert(0, '/home/vagrant/docker-virt-net/src')

from ip2_api.exceptions import IP2Error, UtilError
import ip2_api.link as iplink
import ip2_api.addr as ipaddr
import ip2_api.route as ipr
import ip2_api.utils as iputil

class TestIproute2API(unittest.TestCase):
    def test_veths(self):
        if not os.geteuid() == 0:
            self.fail("These tests must be run as root!")
        self.assertRaises(IP2Error, iplink.veth.remove, "foo")
        self.assertRaises(IP2Error, iplink.veth.activate, "foo")
        iplink.veth.create("foo", "faa")
        iplink.veth.activate("foo")
        iplink.veth.activate("faa")
        iplink.veth.remove("foo")
        self.assertRaises(IP2Error, iplink.veth.remove, "faa")

    def test_bridges(self):
        if not os.geteuid() == 0:
            self.fail("These tests must be run as root!")
        self.assertRaises(IP2Error, iplink.bridge.remove, "foo_brd")
        self.assertRaises(IP2Error, iplink.bridge.activate, "foo_brd")
        iplink.bridge.create("foo_brd")
        iplink.bridge.activate("foo_brd")
        iplink.bridge.remove("foo_brd")
        self.assertRaises(IP2Error, iplink.bridge.remove, "foo_brd")

    def test_addressing(self):
        if not os.geteuid() == 0:
            self.fail("The tests must be run as root!")
        self.assertRaises(IP2Error, ipaddr.assign, "foo", "10.0.0.1/24")
        iplink.veth.create("fee", "fii")
        ipaddr.assign("fee", "10.0.0.1/24")
        ipaddr.reset("fee")
        iplink.veth.remove("fee")

    def test_utils(self):
        if not os.geteuid() == 0:
            self.fail("The tests must be run as root!")
        iputil.alter_brd_iptables_calls()
        iputil.alter_ipv4_forwarding()
        iputil.restore_brd_iptables_calls()
        iputil.restore_ipv4_forwarding()
        iputil.create_netns_dir()

if __name__ == "__main__":
    unittest.main()
