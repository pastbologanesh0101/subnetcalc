# subnetcalc

A tiny IPv4 subnet calculator with **zero dependencies** — pure Python standard
library. Give it a network in CIDR notation and it prints the network address,
broadcast, mask, wildcard, usable host range, and more. It can also carve a
block into equal-size subnets or test whether an address belongs to a network.

```
$ subnetcalc 192.168.1.0/24
CIDR               : 192.168.1.0/24
Network            : 192.168.1.0
Broadcast          : 192.168.1.255
Netmask            : 255.255.255.0
Wildcard           : 0.0.0.255
First host         : 192.168.1.1
Last host          : 192.168.1.254
Usable hosts       : 254
Total addresses    : 256
Class              : C
Private (RFC 1918) : True
```

## Install

```bash
git clone https://github.com/pastbologanesh0101/subnetcalc.git
cd subnetcalc
pip install .          # installs the `subnetcalc` command
```

Or run it straight from the source tree without installing:

```bash
python -m subnetcalc 10.0.0.0/8
```

## Usage

```
subnetcalc <cidr> [options]

  <cidr>              192.168.1.0/24  or  10.0.0.0/255.0.0.0
  -j, --json          emit JSON instead of a table
  -s, --split N       divide the block into at least N equal subnets
  -c, --contains IP   check whether IP is in the network (exit 0 = yes, 1 = no)
  -V, --version       print version
```

### Split a block

```
$ subnetcalc 10.0.0.0/24 --split 4
10.0.0.0/26          10.0.0.1 - 10.0.0.62  (62 hosts)
10.0.0.64/26         10.0.0.65 - 10.0.0.126  (62 hosts)
10.0.0.128/26        10.0.0.129 - 10.0.0.190  (62 hosts)
10.0.0.192/26        10.0.0.193 - 10.0.0.254  (62 hosts)
```

`--split` rounds up to the next power of two, so `--split 3` also yields four
`/26` subnets.

### Membership check

```
$ subnetcalc 172.16.0.0/12 --contains 172.20.5.5
172.20.5.5 is in 172.16.0.0/12
$ echo $?
0
```

### JSON for scripts

```
$ subnetcalc 192.168.1.0/24 --json | jq .usable_hosts
254
```

## Library use

```python
from subnetcalc import Subnet

net = Subnet.parse("192.168.1.0/24")
print(net.broadcast, net.usable_hosts)   # 3232236031 254
print(net.contains("192.168.1.50"))      # True
for piece in net.split(2):
    print(piece.as_dict()["cidr"])       # 192.168.1.0/25 ...
```

## Development

```bash
python -m unittest discover -s tests -v
```

No build tools, no fixtures, no network access — just the standard library.

## Notes

- `/31` networks follow RFC 3021: both addresses are usable, so `usable_hosts`
  is reported as 0 (no dedicated network/broadcast pair to subtract).
- `/32` is treated as a single host route.
- Subnet masks must be contiguous (`255.255.240.0` is fine, `255.0.255.0` is
  rejected).

## License

MIT — see [LICENSE](LICENSE).
