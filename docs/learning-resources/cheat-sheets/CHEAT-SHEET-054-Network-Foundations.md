---
Document ID: CHEAT-SHEET-054
Title: "CHEAT-SHEET-054: Network Foundations - the Wire-Efficiency Bill, the Handshake Ledger, and the First-Token Budget"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'networking', 'mtu', 'performance']
---

# CHEAT-SHEET-054: Network Foundations - the Wire-Efficiency Bill, the Handshake Ledger, and the First-Token Budget

The scope scan that picked this page: phase1-infra's 1100-network track carries four modules - 1101 Fiber GPON Modem, 1102 Star Topology Core, 1103 Jumbo Frames and MTU and 1104 Protocol Stack TCP and DNS - and no sheet anywhere in the track; it is the first phase a student meets and the only one with no single-page reference to fall back on at 2am when the transfer crawls, the pods drop large payloads, or the API feels five times slower than the model it fronts. This sheet takes the questions the operator actually asks: what the wire really costs per frame, which MTU every path carries, what a 2.5G link truly delivers, how one switch becomes five networks, and what loss and connection setup do to the first token.

The sheet runs as seven priced exhibits: the wire-efficiency bill (F1 - 84% fewer packets for the same bytes), the MTU ladder (F2 - every path carries its own ceiling), the 2.5G throughput ledger (F3 - measured, not marketed), the VLAN plan (F4 - one switch, five networks), the segment fold (F5 - one 40,000-byte context, 28 frames or 5), the loss bill (F6 - what 5% loss does to TCP and to UDP), and the handshake ledger and first-token budget (F7 - 640 ms cold cross-region, 92 ms warm). Every number below is printed by the canonical fence at the bottom of the page: the full 321-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 83-line output sits frozen below it byte-for-byte.

## The Wire-Efficiency Bill - the 84% the Wire Never Sees

Every frame pays a fixed toll - preamble, headers, FCS, interframe gap - and the toll is per-frame, not per-byte. The fence prices the two regimes: at MTU 1500, 1,460 bytes of payload ride 1,538 wire bytes (94.9% efficiency); at MTU 9000, 8,960 ride 9,038 (99.1%) - 4.2 percentage points of every wire byte back. Per MiB that is 718.2 packets against 117.0, and for the 11 GB model file the operator actually ships: 7,534,247 packets against 1,227,679 - 84% fewer. Each packet also costs the CPU about 2.86 us at 10,000 cycles per packet on a 3.5 GHz core, so the same file costs 21.5 s versus 3.5 s of pure packet processing. Jumbo frames do not make the wire faster; they make it stop repeating itself.

| Quantity | MTU 1500 | MTU 9000 |
| --- | --- | --- |
| Wire bytes per frame | 1,538 B | 9,038 B |
| Payload efficiency | 94.9% | 99.1% |
| Packets per MiB | 718.2 | 117.0 |
| Packets for 11 GB | 7,534,247 | 1,227,679 |
| CPU at 2.86 us/packet | 21.5 s | 3.5 s |

## The MTU Ladder - Every Path Carries Its Own Ceiling

The MTU is a property of the path, not of the NIC, and every tunnel in the chain spends bytes: PPPoE takes 8, WireGuard drops the ceiling to 1420, and a VXLAN pod under a 9000 host lands at 8950 (9000 - 50 of tunnel overhead). The probe arithmetic is one line - a ping payload is MTU minus 28 of IP+ICMP headers, so 1472 probes a 1500 path and 8972 probes a 9000 path, sent with the do-not-fragment bit so nothing fragments silently. When "fragmentation needed" ICMP is filtered somewhere, PMTUD goes black-hole: the fix is MSS clamping on the router, forcing the TCP MSS down to the real path MTU.

```text
Every path carries its own ceiling: wan 1500, pppoe 1492, mobile 1420-1440,
jumbo lan 9000, k8s pod (vxlan) 8950 = 9000 - 50, wireguard 1420.
Probe with ping -M do -s <mtu - 28>: 1472 at mtu 1500, 8972 at mtu 9000.
Jumbo is a lan-only optimization - the wan stays 1500/1492.
```

## The 2.5G Throughput Ledger - Measured, Not Marketed

The port advertises 2.5 Gbps; the protocols deliver less, and by consistent fractions: TCP and NFS land 2.35 Gbps (94% efficiency), SMB 2.25 (90%). Jumbo frames buy the difference back measurably - the module's iperf3 run moves 2.23 to 2.40 Gbits/sec at MTU 9000, +7.6% throughput on 15% less CPU. The LACP line is where hope goes to die: three bonded 2.5G ports read 7.5 Gbps and deliver about 6 across parallel streams, and a single-stream NFS transfer gains nothing - LACP raises the aggregate, never one flow. Size the link from the ledger, not the label.

```text
2.5 gbps is the marketing number; tcp and nfs land 2.35 (94%), smb 2.25 (90%).
Jumbo frames move iperf3 2.23 -> 2.40 gbits/sec (+7.6%) and cut cpu 15%.
LACP 3 x 2.5G reads 7.5 gbps and delivers ~6 for parallel streams - and a
single-stream nfs transfer gains nothing: lacp raises the aggregate.
```

## The VLAN Plan - One Switch, Five Networks

One managed switch, five logical networks, and the roles are not symmetric: VLAN 10 MGMT carries hypervisor UIs, switch/AP admin and BMCs - the most protected vlan in the house; VLAN 20 STORAGE carries NFS, iSCSI and backups with no gateway at all, so it is unreachable from anywhere but itself; 30 COMPUTE takes node-to-node training traffic, 40 INFERENCE takes serving APIs and user ingress, 50 CLIENTS takes everything with a person behind it. Star topology is what makes the plan flat: any device to any device is 2 hops through the core, where a daisy chain pays up to n. Assign static IPs to anything a firewall rule or an NFS export names by address.

```text
One managed switch, five vlans: 10 mgmt (most protected), 20 storage
(no gateway - unreachable from the internet), 30 compute, 40 inference,
50 clients. Star topology: any-to-any is 2 hops; a daisy chain pays up to n.
Static ips for anything a firewall rule or an nfs export names.
```

## The Segment Fold - One 40,000-Byte Context Through the Stack

The stack folds the same bytes through four shapes - L4 segments, L3 packets, L2 frames, L1 bits - and each fold adds its header. TCP's segment size is the MSS: MTU minus 40 of IP+TCP headers, 1460 at MTU 1500 and 8,960 at MTU 9000. One 40,000-byte LLM context ships as 28 segments at MTU 1500 but 5 at MTU 9000 - 5.6x fewer layer-2 frames carrying identical layer-4 bytes. That is the whole mechanism behind F1's bill: fewer folds, fewer headers, less repetition on the wire.

```text
The stack folds: data -> segments -> packets -> frames -> bits.
Mss = mtu - 40: 1460 at mtu 1500, 8960 at mtu 9000.
One 40,000-byte context ships as 28 segments at mtu 1500, 5 at mtu 9000 -
5.6x fewer layer-2 frames carrying identical layer-4 bytes.
```

## The Loss Bill - What 5% Loss Does to TCP and to UDP

The fence drops exactly 5% of 1,000 segments on a seeded link. TCP recovers every one: 1,000/1,000 delivered after 1,054 transmissions - 54 extra sends, right on the theory's n*p/(1-p) = 52.6 - and at the GPON's 12 ms RTT those retransmits cost about 648 ms of pure waiting. UDP tells no one: 950/1,000 arrived, 50 datagrams - 73,000 bytes - vanished with no notice. The law that falls out: DNS rides UDP because the client retries above, and QUIC (HTTP/3) re-plugs the hole in user space - loss is not a reason to avoid UDP, it is a reason to know which layer owns recovery.

## The Handshake Ledger and the First-Token Budget

Before a byte of model output, the network collects its tolls: a cold DNS walk is 4 RTT (root, TLD, authoritative, plus the client leg), and even a 300 s TTL still misses 6 times in a 30-minute session - 54 hits, 90% cached, but the misses each pay the full walk. Connection setup is the second toll, and it is priced in round trips:

| Connection setup | RTT cost | First byte at 12 ms RTT |
| --- | --- | --- |
| HTTP (plain) | 1 | 24 ms |
| HTTPS, TLS 1.2 | 3 | 48 ms |
| HTTPS, TLS 1.3 | 2 | 36 ms |
| TLS 1.3 resumed (0-RTT) | 0 | 12 ms |
| HTTP/3 (QUIC), fresh | 1 | 24 ms |

Keep the connection alive and the toll amortizes: 1,000 requests cost 36,000 ms on a new connection per request but 12,036 ms on one kept-alive connection - 67% is pure handshake tax. Now the bill an LLM operator actually feels, the first token (model TTFB 80 ms; local RTT 12 ms, cross-region 80 ms):

| Config | Transport | First token | Transport share |
| --- | --- | --- | --- |
| A cold, cross-region | 560 ms | 640 ms | 88% |
| B cold, same-region | 84 ms | 164 ms | 51% |
| C warm (keep-alive) | 12 ms | 92 ms | 13% |
| D cold, HTTP/3 | 72 ms | 152 ms | 47% |

Config A makes users wait 7.0x the model's own 80 ms in transport alone; config C is the only one where the model dominates its own latency. At 100,000 calls a day, the B-to-C gap is 2.0 hours of user-visible handshake time - every day, for a keep-alive setting.

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Sizing the link from the port's bit rate | 2.5G delivers 2.35 best-case; quote the measured ledger, not the label |
| Jumbo frames on one hop and nowhere else | ping -M do -s 8972 goes silent at the mismatched hop; walk the path |
| Expecting LACP to speed up one stream | 3 x 2.5G delivers ~6 across streams; a single nfs transfer gains nothing |
| Treating UDP loss as rare | 5% loss ate 73,000 bytes of 1,460,000 in the fence's run, silently |
| Calling the API without keep-alive | 1,000 requests: 36,000 ms new-conn vs 12,036 ms reused - 67% is handshake tax |
| Assuming dns "is cached" | a 300 s ttl still misses 6 times per 30-minute session at 4 rtt each |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Transfers cap near 2.3 gbps on 2.5G | 94% is healthy tcp; smb's 90% is the protocol, not the wire |
| Large transfers stall across the wan | pmtud black hole: mss-clamp to the real path mtu or un-filter the icmp |
| Pods drop large payloads intermittently | pod mtu 8950 vs host 9000 mismatch; every tunnel hop must agree |
| The api feels 5x slower than the model | read the first-token budget: warm the connection, same region, keep-alive |
| Random resets under a lossy link | tcp retransmitting (54 extra sends in the fence's run) - the protocol working |
| Dns intermittently slow | cold misses are 4 rtt; raise the ttl or pin a local resolver |

## Quick Reference For

- [Module 1101: Fiber GPON Modem](../../phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md) - the optics, the signal budgets and the throughput evaluation this sheet's wire bill prices.
- [Module 1102: Star Topology Core](../../phases/phase1-infra/1100-network/1102-Star-Topology-Core.md) - the switch criteria, the VLAN plan and the 2.5G protocol ledger, measured in full.
- [Module 1103: Jumbo Frames and MTU](../../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md) - the packet arithmetic and the iperf3 evidence behind the efficiency bill.
- [Module 1104: Protocol Stack TCP and DNS](../../phases/phase1-infra/1100-network/1104-Protocol-Stack-TCP-and-DNS.md) - the loss and handshake simulations this sheet's fence reproduces.

## The Canonical Fence

Every number on this page comes from one stdlib-only script - the 321-line fence below, run once and frozen. It carries its own asserts, so a drifted number dies loudly instead of printing; the run needs no network, no model, and its one random draw is seeded, so two runs agree byte for byte. Its 83-line output sits frozen under it.

```python
"""tick-1030 canonical fence - CHEAT-SHEET-054: Network Foundations.

Stdlib only. One run prints every canonical number on the sheet:
F1 the wire-efficiency bill, F2 the MTU ladder, F3 the 2.5G
throughput ledger, F4 the VLAN plan, F5 the segment fold,
F6 the loss bill, F7 the handshake ledger and the first-token
budget.
"""
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

LINE = "------------------------------------------------------------"


def rule(label):
    print(LINE)
    print(label)
    print(LINE)


# ============================================================
# F1  THE WIRE-EFFICIENCY BILL (MTU 1500 vs MTU 9000, IPv4)
# ============================================================
rule("F1 the wire-efficiency bill (mtu 1500 vs mtu 9000, ipv4)")

MTU_STD = 1500
MTU_JUMBO = 9000
HDRS = 40          # 20 B IPv4 + 20 B TCP

MSS_STD = MTU_STD - HDRS
MSS_JUMBO = MTU_JUMBO - HDRS
assert MSS_STD == 1460 and MSS_JUMBO == 8960

WIRE_STD = 1538    # frame + preamble + FCS + interframe gap
WIRE_JUMBO = 9038
eff_std = MSS_STD / WIRE_STD
eff_jumbo = MSS_JUMBO / WIRE_JUMBO
print(f"  wire cost    : {WIRE_STD} B on the wire per {MSS_STD} B of payload"
      f" ({eff_std:.1%} efficiency)")
print(f"  wire cost    : {WIRE_JUMBO} B on the wire per {MSS_JUMBO} B of payload"
      f" ({eff_jumbo:.1%} efficiency)")
gain_pp = (eff_jumbo - eff_std) * 100
print(f"  gain         : +{gain_pp:.1f} percentage points of every wire byte")
assert eff_std > 0.949 and eff_std < 0.950, eff_std
assert eff_jumbo > 0.991 and eff_jumbo < 0.992, eff_jumbo
assert abs(gain_pp - 4.2) < 0.05, gain_pp

MIB = 1024 * 1024
pp_mib_std = MIB / MSS_STD
pp_mib_jumbo = MIB / MSS_JUMBO
print(f"  packets/MiB  : {pp_mib_std:.1f} at mtu 1500 vs {pp_mib_jumbo:.1f}"
      f" at mtu 9000")
reduction = 1 - pp_mib_jumbo / pp_mib_std
print(f"  reduction    : {reduction:.0%} fewer packets for the same bytes")
assert abs(pp_mib_std - 718.2) < 0.1
assert abs(pp_mib_jumbo - 117.0) < 0.1

TRANSFER = 11_000_000_000   # the 11 GB model file
pkts_std = math.ceil(TRANSFER / MSS_STD)
pkts_jumbo = math.ceil(TRANSFER / MSS_JUMBO)
print(f"  11 GB file   : {pkts_std:,} packets vs {pkts_jumbo:,}"
      f" ({1 - pkts_jumbo / pkts_std:.1%} fewer)")
assert pkts_std == 7_534_247 and pkts_jumbo == 1_227_679

CYCLES_PER_PKT = 10_000
CPU_HZ = 3.5e9
us_per_pkt = CYCLES_PER_PKT / CPU_HZ * 1e6
cpu_std = pkts_std * CYCLES_PER_PKT / CPU_HZ
cpu_jumbo = pkts_jumbo * CYCLES_PER_PKT / CPU_HZ
print(f"  cpu bill     : {us_per_pkt:.2f} us per packet (10,000 cycles"
      f" @ 3.5 ghz)")
print(f"  cpu bill     : {cpu_std:.1f} s vs {cpu_jumbo:.1f} s of packet"
      f" processing for the same 11 GB")
assert abs(us_per_pkt - 2.86) < 0.01
assert abs(cpu_std - 21.5) < 0.1 and abs(cpu_jumbo - 3.5) < 0.1
print("F1-OK")

# ============================================================
# F2  THE MTU LADDER (every path carries its own ceiling)
# ============================================================
rule("F2 the mtu ladder (every path carries its own ceiling)")

LADDER = [
    ("wan (dhcp)",       1500, "standard ethernet payload"),
    ("wan (pppoe)",      1492, "8 B consumed by the pppoe header"),
    ("mobile / fwa",     1420, "tunnel overhead varies (1420-1440)"),
    ("lan (jumbo)",      9000, "lan-only optimization - wan stays 1500/1492"),
    ("k8s pod (vxlan)",  8950, "host 9000 minus 50 B vxlan overhead"),
    ("wireguard",        1420, "tunnel overhead"),
]
for name, mtu, why in LADDER:
    print(f"  {name:<18} {mtu:>5}  {why}")
assert LADDER[1][1] == 1492 and LADDER[3][1] == 9000
assert LADDER[4][1] == 9000 - 50

ICMP_IP = 28       # 20 B IP + 8 B ICMP around a ping payload
print(f"  probe        : payload = mtu - {ICMP_IP} (ip + icmp headers):"
      f" {1500 - ICMP_IP} for mtu 1500, {9000 - ICMP_IP} for mtu 9000")
assert 1500 - ICMP_IP == 1472 and 9000 - ICMP_IP == 8972
print("  mss clamp    : tcp mss -> pmtu, the fix when icmp 'fragmentation"
      " needed' is filtered")
print("  walk the path: ping -M do -s 8972 hop by hop; the first silent hop"
      " owns the mismatch")
print("F2-OK")

# ============================================================
# F3  THE 2.5G THROUGHPUT LEDGER (measured, not marketed)
# ============================================================
rule("F3 the 2.5g throughput ledger (measured, not marketed)")

LINE_RATE = 2.5
MEASURED = [
    ("tcp (ipv4)",  2.35),
    ("nfs (linux)", 2.35),
    ("smb (win)",   2.25),
]
for proto, real in MEASURED:
    print(f"  {proto:<11}: {LINE_RATE} gbps theoretical -> {real}"
          f" gbps measured ({real / LINE_RATE:.0%} efficiency)")
assert abs(MEASURED[0][1] / LINE_RATE - 0.94) < 1e-9
assert abs(MEASURED[2][1] / LINE_RATE - 0.90) < 1e-9

IPERF_STD = 2.23
IPERF_JUMBO = 2.40
print(f"  jumbo delta  : iperf3 {IPERF_STD} -> {IPERF_JUMBO} gbits/sec at"
      f" mtu 9000 ({(IPERF_JUMBO / IPERF_STD - 1):.1%} throughput,"
      f" cpu -15%)")
assert abs((IPERF_JUMBO / IPERF_STD - 1) - 0.076) < 0.001

PORTS = 3
lagg_theory = PORTS * LINE_RATE
print(f"  lacp         : {PORTS} x 2.5G = {lagg_theory} gbps theoretical"
      f" -> ~{lagg_theory * 0.8:.1f} gbps for parallel streams")
print("  lacp caveat  : single-stream nfs gains nothing - lacp raises"
      " the aggregate, not one stream")
assert lagg_theory == 7.5
print("F3-OK")

# ============================================================
# F4  THE VLAN PLAN (one physical switch, five logical nets)
# ============================================================
rule("F4 the vlan plan (one physical switch, five logical nets)")

VLANS = [
    (10, "mgmt",      "192.168.10.0/24", "hypervisor ui, switch/ap admin, bmc"
     " - the most protected vlan"),
    (20, "storage",   "192.168.20.0/24", "nfs, iscsi, backups - no gateway,"
     " unreachable from the internet"),
    (30, "compute",   "192.168.30.0/24", "node-to-node training traffic,"
     " cluster overlay"),
    (40, "inference", "192.168.40.0/24", "serving apis, user ingress"),
    (50, "clients",   "192.168.50.0/24", "workstations, personal devices"),
]
for vid, name, subnet, carries in VLANS:
    print(f"  vlan {vid:<3}{name:<10} {subnet:<17} {carries}")
assert [v[0] for v in VLANS] == [10, 20, 30, 40, 50]
print("  star hop     : any-to-any = 2 hops (device-switch-device); a"
      " daisy chain pays up to n")
print("  ip hygiene   : static for anything with a firewall rule or an"
      " nfs export; ranges by role")
print("F4-OK")

# ============================================================
# F5  THE SEGMENT FOLD (one 40,000-byte context through the stack)
# ============================================================
rule("F5 the segment fold (one 40,000-byte context through the stack)")

LAYERS = [
    (7, "application", "data"),
    (6, "presentation", "data"),
    (5, "session", "data"),
    (4, "transport", "segment"),
    (3, "network", "packet"),
    (2, "data link", "frame"),
    (1, "physical", "bit"),
]
pdu_line = " / ".join(f"L{n} {pdu}" for n, _, pdu in LAYERS)
print(f"  seven layers : {pdu_line}")
assert sorted(n for n, _, _ in LAYERS) == list(range(1, 8))

CTX = 40_000
seg_std = math.ceil(CTX / MSS_STD)
seg_jumbo = math.ceil(CTX / MSS_JUMBO)
print(f"  mss          : {MSS_STD} B payload at mtu 1500;"
      f" {MSS_JUMBO} B at mtu 9000")
print(f"  40,000 B up  : {seg_std} segments at mtu 1500 vs {seg_jumbo}"
      f" at mtu 9000")
print(f"  collapse     : {seg_std / seg_jumbo:.1f}x fewer layer-2 frames"
      f" carrying identical layer-4 bytes")
assert seg_std == 28 and seg_jumbo == 5
assert abs(seg_std / seg_jumbo - 5.6) < 1e-9
print("F5-OK")

# ============================================================
# F6  THE LOSS BILL (1,000 segments over a link that drops 5%)
# ============================================================
rule("F6 the loss bill (1,000 segments over a link that drops 5%)")

P_LOSS = 0.05
N_SEG = 1_000
RTT_GPON = 12.0
rng = random.Random(1104)

tcp_sends = 0
tcp_extra = 0
for _ in range(N_SEG):
    tries = 0
    while True:
        tries += 1
        tcp_sends += 1
        if rng.random() >= P_LOSS:
            break
    tcp_extra += tries - 1
tcp_delivered = N_SEG

udp_delivered = sum(1 for _ in range(N_SEG) if rng.random() >= P_LOSS)
udp_lost = N_SEG - udp_delivered

theory_extra = N_SEG * P_LOSS / (1 - P_LOSS)
recovery_ms = tcp_extra * RTT_GPON
lost_bytes = udp_lost * MSS_STD
print(f"  tcp : {tcp_delivered:,}/{N_SEG:,} delivered after {tcp_sends:,}"
      f" transmissions ({tcp_extra} extra sends; theory"
      f" n*p/(1-p) = {theory_extra:.1f})")
print(f"        at the gpon's {RTT_GPON:.0f} ms rtt that is"
      f" ~{recovery_ms:.0f} ms of pure retransmit waiting")
print(f"  udp : {udp_delivered:,}/{N_SEG:,} arrived; {udp_lost} datagrams -"
      f" {lost_bytes:,} bytes - vanished with no notice")
assert tcp_delivered == N_SEG and udp_delivered + udp_lost == N_SEG
assert tcp_extra == 54, tcp_extra
assert abs(theory_extra - 52.6) < 0.1
assert lost_bytes == 73_000
print("  law : dns rides udp because the client retries above; quic"
      " (http/3) re-plugs the hole in user space")
print("F6-OK")

# ============================================================
# F7  THE HANDSHAKE LEDGER AND THE FIRST-TOKEN BUDGET (rtt 12 ms)
# ============================================================
rule("F7 the handshake ledger and the first-token budget (rtt 12 ms)")

RTT = 12.0

DNS_HOPS = 3      # root, .com tld, authoritative - plus the client leg
dns_cold = DNS_HOPS + 1
print(f"  dns cold walk : {dns_cold} rtt (root, tld, authoritative +"
      f" client-to-resolver)")
assert dns_cold == 4

TTL = 300
SESSION_MIN = 30
EVERY = 30
n_lookups = SESSION_MIN * 60 // EVERY
misses = [t * EVERY for t in range(n_lookups) if (t * EVERY) % TTL == 0]
hits = n_lookups - len(misses)
print(f"  ttl {TTL} s     : {n_lookups} lookups in a"
      f" {SESSION_MIN}-min session -> {len(misses)} cold misses (t ="
      f" {misses[0]}..{misses[-1]}), {hits} hits ({hits / n_lookups:.0%}"
      f" cached)")
assert len(misses) == 6 and hits == 54


def first_byte(scheme, setup_rtts):
    fb = (setup_rtts + 1) * RTT
    print(f"  {scheme:<18} {setup_rtts} rtt setup -> first byte"
          f" {fb:>4.0f} ms")
    return fb


fb_http = first_byte("http://", 1)
fb_tls12 = first_byte("https tls 1.2", 3)
fb_tls13 = first_byte("https tls 1.3", 2)
fb_0rtt = first_byte("tls 1.3 resumed", 0)
fb_quic = first_byte("http/3 quic fresh", 1)
assert fb_http == 24.0 and fb_tls12 == 48.0 and fb_tls13 == 36.0
assert fb_0rtt == 12.0 and fb_quic == 24.0

N_REQ = 1_000
new_conn_ms = N_REQ * fb_tls13
keepalive_ms = fb_tls13 + N_REQ * RTT
saved = 1 - keepalive_ms / new_conn_ms
print(f"  keep-alive    : {N_REQ:,} requests: {new_conn_ms:,.0f} ms"
      f" new-conn vs {keepalive_ms:,.0f} ms one connection"
      f" ({saved:.0%} saved)")
assert new_conn_ms == 36_000 and keepalive_ms == 12_036

MODEL_FIRST = 80.0
RTT_LOCAL = 12.0
RTT_FAR = 80.0


def first_token(name, dns_rtts, tls_rtts, rtt):
    transport = (dns_rtts + tls_rtts + 1) * rtt
    total = transport + MODEL_FIRST
    print(f"  {name:<18} transport {transport:>4.0f} ms -> first token"
          f" {total:>4.0f} ms ({transport / total:.0%} transport)")
    return transport, total


a_t, a_tot = first_token("A cold cross-region", 4, 2, RTT_FAR)
b_t, b_tot = first_token("B cold same-region", 4, 2, RTT_LOCAL)
c_t, c_tot = first_token("C warm keep-alive", 0, 0, RTT_LOCAL)
d_t, d_tot = first_token("D cold http/3", 4, 1, RTT_LOCAL)
assert (a_tot, b_tot, c_tot, d_tot) == (640.0, 164.0, 92.0, 152.0)
assert a_t > b_t > d_t > c_t

CALLS = 100_000
tax_h = (b_tot - c_tot) * CALLS / 1000 / 3600
print(f"  100k calls/day: the B-C gap is {tax_h:.1f} h/day of"
      f" user-visible handshake time")
print(f"  transport-only: config A makes users wait {a_t / MODEL_FIRST:.1f}x"
      f" the model's own {MODEL_FIRST:.0f} ms in transport alone")
assert abs(tax_h - 2.0) < 0.05 and abs(a_t / MODEL_FIRST - 7.0) < 0.01
print("F7-OK")

print(LINE)
print("CHEAT-SHEET-054 fence: seven exhibits, every number asserted.")
print("FENCE-054-OK")
```

```text
------------------------------------------------------------
F1 the wire-efficiency bill (mtu 1500 vs mtu 9000, ipv4)
------------------------------------------------------------
  wire cost    : 1538 B on the wire per 1460 B of payload (94.9% efficiency)
  wire cost    : 9038 B on the wire per 8960 B of payload (99.1% efficiency)
  gain         : +4.2 percentage points of every wire byte
  packets/MiB  : 718.2 at mtu 1500 vs 117.0 at mtu 9000
  reduction    : 84% fewer packets for the same bytes
  11 GB file   : 7,534,247 packets vs 1,227,679 (83.7% fewer)
  cpu bill     : 2.86 us per packet (10,000 cycles @ 3.5 ghz)
  cpu bill     : 21.5 s vs 3.5 s of packet processing for the same 11 GB
F1-OK
------------------------------------------------------------
F2 the mtu ladder (every path carries its own ceiling)
------------------------------------------------------------
  wan (dhcp)          1500  standard ethernet payload
  wan (pppoe)         1492  8 B consumed by the pppoe header
  mobile / fwa        1420  tunnel overhead varies (1420-1440)
  lan (jumbo)         9000  lan-only optimization - wan stays 1500/1492
  k8s pod (vxlan)     8950  host 9000 minus 50 B vxlan overhead
  wireguard           1420  tunnel overhead
  probe        : payload = mtu - 28 (ip + icmp headers): 1472 for mtu 1500, 8972 for mtu 9000
  mss clamp    : tcp mss -> pmtu, the fix when icmp 'fragmentation needed' is filtered
  walk the path: ping -M do -s 8972 hop by hop; the first silent hop owns the mismatch
F2-OK
------------------------------------------------------------
F3 the 2.5g throughput ledger (measured, not marketed)
------------------------------------------------------------
  tcp (ipv4) : 2.5 gbps theoretical -> 2.35 gbps measured (94% efficiency)
  nfs (linux): 2.5 gbps theoretical -> 2.35 gbps measured (94% efficiency)
  smb (win)  : 2.5 gbps theoretical -> 2.25 gbps measured (90% efficiency)
  jumbo delta  : iperf3 2.23 -> 2.4 gbits/sec at mtu 9000 (7.6% throughput, cpu -15%)
  lacp         : 3 x 2.5G = 7.5 gbps theoretical -> ~6.0 gbps for parallel streams
  lacp caveat  : single-stream nfs gains nothing - lacp raises the aggregate, not one stream
F3-OK
------------------------------------------------------------
F4 the vlan plan (one physical switch, five logical nets)
------------------------------------------------------------
  vlan 10 mgmt       192.168.10.0/24   hypervisor ui, switch/ap admin, bmc - the most protected vlan
  vlan 20 storage    192.168.20.0/24   nfs, iscsi, backups - no gateway, unreachable from the internet
  vlan 30 compute    192.168.30.0/24   node-to-node training traffic, cluster overlay
  vlan 40 inference  192.168.40.0/24   serving apis, user ingress
  vlan 50 clients    192.168.50.0/24   workstations, personal devices
  star hop     : any-to-any = 2 hops (device-switch-device); a daisy chain pays up to n
  ip hygiene   : static for anything with a firewall rule or an nfs export; ranges by role
F4-OK
------------------------------------------------------------
F5 the segment fold (one 40,000-byte context through the stack)
------------------------------------------------------------
  seven layers : L7 data / L6 data / L5 data / L4 segment / L3 packet / L2 frame / L1 bit
  mss          : 1460 B payload at mtu 1500; 8960 B at mtu 9000
  40,000 B up  : 28 segments at mtu 1500 vs 5 at mtu 9000
  collapse     : 5.6x fewer layer-2 frames carrying identical layer-4 bytes
F5-OK
------------------------------------------------------------
F6 the loss bill (1,000 segments over a link that drops 5%)
------------------------------------------------------------
  tcp : 1,000/1,000 delivered after 1,054 transmissions (54 extra sends; theory n*p/(1-p) = 52.6)
        at the gpon's 12 ms rtt that is ~648 ms of pure retransmit waiting
  udp : 950/1,000 arrived; 50 datagrams - 73,000 bytes - vanished with no notice
  law : dns rides udp because the client retries above; quic (http/3) re-plugs the hole in user space
F6-OK
------------------------------------------------------------
F7 the handshake ledger and the first-token budget (rtt 12 ms)
------------------------------------------------------------
  dns cold walk : 4 rtt (root, tld, authoritative + client-to-resolver)
  ttl 300 s     : 60 lookups in a 30-min session -> 6 cold misses (t = 0..1500), 54 hits (90% cached)
  http://            1 rtt setup -> first byte   24 ms
  https tls 1.2      3 rtt setup -> first byte   48 ms
  https tls 1.3      2 rtt setup -> first byte   36 ms
  tls 1.3 resumed    0 rtt setup -> first byte   12 ms
  http/3 quic fresh  1 rtt setup -> first byte   24 ms
  keep-alive    : 1,000 requests: 36,000 ms new-conn vs 12,036 ms one connection (67% saved)
  A cold cross-region transport  560 ms -> first token  640 ms (88% transport)
  B cold same-region transport   84 ms -> first token  164 ms (51% transport)
  C warm keep-alive  transport   12 ms -> first token   92 ms (13% transport)
  D cold http/3      transport   72 ms -> first token  152 ms (47% transport)
  100k calls/day: the B-C gap is 2.0 h/day of user-visible handshake time
  transport-only: config A makes users wait 7.0x the model's own 80 ms in transport alone
F7-OK
------------------------------------------------------------
CHEAT-SHEET-054 fence: seven exhibits, every number asserted.
FENCE-054-OK
```
