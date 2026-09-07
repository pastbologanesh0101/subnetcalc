"""subnetcalc - a tiny, dependency-free IPv4 subnet calculator."""
from .core import Subnet, ip_to_int, int_to_ip

__version__ = "0.1.0"
__all__ = ["Subnet", "ip_to_int", "int_to_ip", "__version__"]
