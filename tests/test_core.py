import unittest

from subnetcalc.core import (
    Subnet,
    int_to_ip,
    ip_to_int,
    ipv4_class,
    is_private,
    netmask_from_prefix,
    prefix_from_netmask,
)


class ConversionTests(unittest.TestCase):
    def test_roundtrip(self):
        for ip in ("0.0.0.0", "192.168.1.1", "255.255.255.255", "10.0.0.7"):
            self.assertEqual(int_to_ip(ip_to_int(ip)), ip)

    def test_rejects_bad_octets(self):
        for bad in ("256.0.0.1", "1.2.3", "1.2.3.4.5", "a.b.c.d", "10.01.0.0"):
            with self.assertRaises(ValueError):
                ip_to_int(bad)

    def test_prefix_netmask_roundtrip(self):
        for prefix in range(0, 33):
            mask = netmask_from_prefix(prefix)
            self.assertEqual(prefix_from_netmask(int_to_ip(mask)), prefix)

    def test_rejects_noncontiguous_mask(self):
        with self.assertRaises(ValueError):
            prefix_from_netmask("255.0.255.0")

    def test_class_boundaries(self):
        self.assertEqual(ipv4_class(10), "A")
        self.assertEqual(ipv4_class(172), "B")
        self.assertEqual(ipv4_class(192), "C")
        self.assertEqual(ipv4_class(224), "D (multicast)")
        self.assertEqual(ipv4_class(240), "E (reserved)")


class SubnetTests(unittest.TestCase):
    def test_basic_24(self):
        net = Subnet.parse("192.168.1.10/24")
        d = net.as_dict()
        self.assertEqual(d["network"], "192.168.1.0")
        self.assertEqual(d["broadcast"], "192.168.1.255")
        self.assertEqual(d["netmask"], "255.255.255.0")
        self.assertEqual(d["wildcard"], "0.0.0.255")
        self.assertEqual(d["first_host"], "192.168.1.1")
        self.assertEqual(d["last_host"], "192.168.1.254")
        self.assertEqual(d["usable_hosts"], 254)
        self.assertEqual(d["total_addresses"], 256)
        self.assertTrue(d["private"])

    def test_netmask_notation_matches_cidr(self):
        self.assertEqual(
            Subnet.parse("10.0.0.0/255.255.255.0").as_dict(),
            Subnet.parse("10.0.0.0/24").as_dict(),
        )

    def test_slash31_has_no_host_reservation(self):
        net = Subnet.parse("192.0.2.0/31")
        self.assertEqual(net.usable_hosts, 0)
        self.assertEqual(net.first_host, ip_to_int("192.0.2.0"))
        self.assertEqual(net.last_host, ip_to_int("192.0.2.1"))

    def test_slash32(self):
        net = Subnet.parse("8.8.8.8/32")
        d = net.as_dict()
        self.assertEqual(d["network"], "8.8.8.8")
        self.assertEqual(d["broadcast"], "8.8.8.8")
        self.assertEqual(d["usable_hosts"], 0)
        self.assertFalse(d["private"])

    def test_contains(self):
        net = Subnet.parse("172.16.0.0/12")
        self.assertTrue(net.contains("172.16.5.5"))
        self.assertTrue(net.contains("172.31.255.255"))
        self.assertFalse(net.contains("172.32.0.1"))

    def test_split_exact_power_of_two(self):
        pieces = Subnet.parse("10.0.0.0/24").split(4)
        self.assertEqual(len(pieces), 4)
        self.assertEqual(
            [p.as_dict()["cidr"] for p in pieces],
            [
                "10.0.0.0/26",
                "10.0.0.64/26",
                "10.0.0.128/26",
                "10.0.0.192/26",
            ],
        )

    def test_split_rounds_up(self):
        pieces = Subnet.parse("10.0.0.0/24").split(3)
        self.assertEqual(len(pieces), 4)
        self.assertEqual(pieces[0].prefix, 26)

    def test_split_too_many_raises(self):
        with self.assertRaises(ValueError):
            Subnet.parse("10.0.0.0/30").split(5)

    def test_parse_requires_slash(self):
        with self.assertRaises(ValueError):
            Subnet.parse("192.168.1.0")

    def test_is_private_helper(self):
        self.assertTrue(is_private(ip_to_int("10.1.2.3") & netmask_from_prefix(8)))
        self.assertFalse(is_private(ip_to_int("8.8.8.0")))


if __name__ == "__main__":
    unittest.main()
