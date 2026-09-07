"""Core IPv4 math for subnetcalc. No third-party dependencies."""
from __future__ import annotations

from dataclasses import dataclass

_ALL_ONES = 0xFFFFFFFF


def ip_to_int(ip: str) -> int:
    """Convert a dotted-quad string to a 32-bit integer."""
    parts = ip.split(".")
    if len(parts) != 4:
        raise ValueError(f"invalid IPv4 address: {ip!r}")
    octets = []
    for part in parts:
        if not part.isdigit() or (len(part) > 1 and part[0] == "0"):
            raise ValueError(f"invalid IPv4 address: {ip!r}")
        value = int(part)
        if value > 255:
            raise ValueError(f"octet out of range in {ip!r}: {value}")
        octets.append(value)
    return (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]


def int_to_ip(value: int) -> str:
    """Convert a 32-bit integer to a dotted-quad string."""
    if value < 0 or value > _ALL_ONES:
        raise ValueError(f"value out of 32-bit range: {value}")
    return ".".join(str((value >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def prefix_from_netmask(netmask: str) -> int:
    """Return the prefix length for a dotted-quad subnet mask."""
    bits = bin(ip_to_int(netmask))[2:].zfill(32)
    if "01" in bits:
        raise ValueError(f"not a contiguous subnet mask: {netmask!r}")
    return bits.count("1")


def netmask_from_prefix(prefix: int) -> int:
    """Return the 32-bit mask integer for a prefix length."""
    if prefix < 0 or prefix > 32:
        raise ValueError(f"prefix length out of range: {prefix}")
    if prefix == 0:
        return 0
    return (_ALL_ONES << (32 - prefix)) & _ALL_ONES


def ipv4_class(first_octet: int) -> str:
    """Classful (pre-CIDR) network class for the leading octet."""
    if first_octet < 128:
        return "A"
    if first_octet < 192:
        return "B"
    if first_octet < 224:
        return "C"
    if first_octet < 240:
        return "D (multicast)"
    return "E (reserved)"


def is_private(network: int) -> bool:
    """True if the network falls inside RFC 1918 private space."""
    ranges = (
        (ip_to_int("10.0.0.0"), 8),
        (ip_to_int("172.16.0.0"), 12),
        (ip_to_int("192.168.0.0"), 16),
    )
    return any(
        network & netmask_from_prefix(bits) == base for base, bits in ranges
    )


@dataclass(frozen=True)
class Subnet:
    """An IPv4 network described by a base address and a prefix length."""

    address: int
    prefix: int

    @classmethod
    def parse(cls, spec: str) -> "Subnet":
        """Parse ``10.0.0.0/24`` or ``10.0.0.0/255.255.255.0``."""
        spec = spec.strip()
        if "/" not in spec:
            raise ValueError(
                f"expected CIDR notation like 10.0.0.0/24, got {spec!r}"
            )
        addr_part, _, mask_part = spec.partition("/")
        address = ip_to_int(addr_part)
        if "." in mask_part:
            prefix = prefix_from_netmask(mask_part)
        elif mask_part.isdigit():
            prefix = int(mask_part)
            if prefix > 32:
                raise ValueError(f"prefix length out of range: {prefix}")
        else:
            raise ValueError(f"invalid prefix length: {mask_part!r}")
        return cls(address=address, prefix=prefix)

    @property
    def netmask(self) -> int:
        return netmask_from_prefix(self.prefix)

    @property
    def wildcard(self) -> int:
        return (~self.netmask) & _ALL_ONES

    @property
    def network(self) -> int:
        return self.address & self.netmask

    @property
    def broadcast(self) -> int:
        return self.network | self.wildcard

    @property
    def total_addresses(self) -> int:
        return 1 << (32 - self.prefix)

    @property
    def usable_hosts(self) -> int:
        # /31 (RFC 3021 point-to-point) and /32 have no host range to spare.
        if self.prefix >= 31:
            return 0
        return self.total_addresses - 2

    @property
    def first_host(self) -> int:
        return self.network if self.prefix >= 31 else self.network + 1

    @property
    def last_host(self) -> int:
        return self.broadcast if self.prefix >= 31 else self.broadcast - 1

    def contains(self, ip: str) -> bool:
        return ip_to_int(ip) & self.netmask == self.network

    def split(self, count: int) -> list["Subnet"]:
        """Divide this block into at least ``count`` equal-size subnets."""
        if count < 1:
            raise ValueError("count must be >= 1")
        new_prefix = self.prefix
        while (1 << (new_prefix - self.prefix)) < count:
            new_prefix += 1
        if new_prefix > 32:
            raise ValueError(
                f"cannot split /{self.prefix} into {count} subnets"
            )
        step = 1 << (32 - new_prefix)
        pieces = 1 << (new_prefix - self.prefix)
        return [
            Subnet(self.network + i * step, new_prefix) for i in range(pieces)
        ]

    def as_dict(self) -> dict:
        return {
            "cidr": f"{int_to_ip(self.network)}/{self.prefix}",
            "network": int_to_ip(self.network),
            "broadcast": int_to_ip(self.broadcast),
            "netmask": int_to_ip(self.netmask),
            "wildcard": int_to_ip(self.wildcard),
            "first_host": int_to_ip(self.first_host),
            "last_host": int_to_ip(self.last_host),
            "usable_hosts": self.usable_hosts,
            "total_addresses": self.total_addresses,
            "class": ipv4_class((self.network >> 24) & 0xFF),
            "private": is_private(self.network),
        }
