---
Document ID: 1104
Title: "1104: The Protocol Stack - OSI Layers, TCP, and DNS"
Phase: 1
Module: 1100
Last Updated: 2026-10-07
Status: Complete
Difficulty: Beginner
Estimated Time: 2 hours
Prerequisites: [1101]
Related: [1102, 1103, 1402]
Tags: ['networking', 'infrastructure', 'inference', 'performance']
---

# 1104: The Protocol Stack - OSI Layers, TCP, and DNS

## Abstract

Every request this curriculum makes to a model server crosses the same seven-layer stack, and until now the stack itself was never taught. The 1100 quiz asks about the OSI model's seven layers, TCP's retransmissions against UDP's silent drops, DNS resolution, and the well-known ports - and its review map leaned those questions on the MTU lesson, which presupposes the layering model but never teaches it. The module README lists "TCP/IP Fundamentals" and "DNS" as prerequisites and points at external books; this lesson brings the stack in-house. The boundary is owned honestly: [1101](./1101-Fiber-GPON-Modem.md) owns the WAN uplink whose RTT every fence here prices, [1102](./1102-Star-Topology-Core.md) owns topology, VLANs, and DNS-safe host naming, [1103](./1103-Jumbo-Frames-and-MTU.md) owns the MTU boundary this lesson's segment counts reuse, [1402](../1400-llmops/1402-vLLM-and-TGI.md) owns the serving endpoint whose ports this lesson decomposes, 7204 owns the application-layer retries and rate limits that ride on TCP, and 1104 owns the stack itself - the seven layers as one HTTPS inference call, TCP versus UDP on a lossy uplink, DNS resolution and its TTL cache, the port and handshake ledger, and the end-to-end first-token budget.

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [The Seven Layers of One Request](#the-seven-layers-of-one-request)
- [Two Transports: TCP and UDP](#two-transports-tcp-and-udp)
- [DNS: From a Name to an Address](#dns-from-a-name-to-an-address)
- [Ports and the TLS Wrap](#ports-and-the-tls-wrap)
- [The End-to-End First-Token Budget](#the-end-to-end-first-token-budget)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After this lesson you will be able to:

- Classify every hop of one HTTPS inference call into the OSI model's seven layers (ISO/IEC 7498-1) and name each layer's PDU
- Explain why TCP retransmits while UDP drops silently, and price the difference on a lossy uplink
- Walk a cold DNS resolution end to end and predict which lookups a TTL cache absorbs
- Read the well-known ports table for a serving stack and count the round trips each scheme spends before the first byte
- Choose between cold, warm, and QUIC connection strategies using a first-token budget instead of folklore

## The Seven Layers of One Request

The OSI basic reference model (ISO/IEC 7498-1, also ITU-T X.200) divides network communication into seven layers. The fastest way to learn them is not to memorize the list but to send one real request through it - a `POST /v1/chat/completions` with a 40,000-byte context - and watch each layer do one job:

```python
import math

LAYERS = [
    (7, "Application", "data",    "HTTP POST /v1/chat/completions carries the JSON prompt"),
    (6, "Presentation", "data",   "the TLS record layer encrypts and authenticates bytes"),
    (5, "Session",      "data",   "the TLS session keys outlive one request (keep-alive)"),
    (4, "Transport",    "segment", "TCP numbers, acknowledges, and retransmits the bytes"),
    (3, "Network",      "packet", "IP routes each packet across the ISP to the server"),
    (2, "Data link",    "frame",  "Ethernet frames carry the packets over each local hop"),
    (1, "Physical",     "bit",    "light on the fiber, voltage on the copper"),
]
nums = [l[0] for l in LAYERS]
assert sorted(nums) == list(range(1, 8)), "each layer exactly once"
assert [l[0] for l in LAYERS] == [7, 6, 5, 4, 3, 2, 1], "top-down order"
for n, name, pdu, role in LAYERS:
    print(f"  L{n} {name:<12} {pdu:<8} {role}")
MSS_STD = 1500 - 40   # 1460 payload bytes under IPv4/TCP with a standard MTU
MSS_JUMBO = 9000 - 40
ctx = 40_000
seg_std = math.ceil(ctx / MSS_STD)
seg_jumbo = math.ceil(ctx / MSS_JUMBO)
print(f"  one {ctx:,}-byte context upload = {seg_std} segments at MTU 1500"
      f" (MSS {MSS_STD}), {seg_jumbo} at MTU 9000 (MSS {MSS_JUMBO})")
assert seg_std == 28 and seg_jumbo == 5
print(f"  jumbo frames collapse the L2 frame count {seg_std} -> {seg_jumbo}"
      f" ({seg_std / seg_jumbo:.1f}x fewer frames)")
```

The classification is exhaustive - layers 1 through 7 each appear exactly once, top-down. Notice what the count at the bottom says: the same 40,000-byte context upload is 28 transport segments under a standard MTU 1500 (payload MSS 1460) but only 5 under the jumbo MTU 9000 from [1103](./1103-Jumbo-Frames-and-MTU.md) - 5.6x fewer layer-2 frames carrying the identical layer-4 bytes. The layers are not a quiz taxonomy; each one's unit of work (segment, packet, frame, bit) is a real envelope wrapped around the one above it, and [1103](./1103-Jumbo-Frames-and-MTU.md) was optimizing the envelope this lesson just unfolded.

## Two Transports: TCP and UDP

Layer 4 has two standard carriers. TCP (RFC 9293, which obsoleted the classic RFC 793 in 2022) is connection-oriented: a three-way handshake opens the connection, every byte is numbered and acknowledged, and lost segments are retransmitted until they arrive. UDP (RFC 768, 1980) is connectionless: one datagram out, no setup, no tracking, no recovery. The difference is money on any real uplink - here is the same 1,000-segment upload over a link that loses 5 percent of packets:

```python
import random

P_LOSS = 0.05
N_SEG = 1_000
MSS_STD = 1500 - 40   # 1460 payload bytes under IPv4/TCP (the MTU 1500 case)
rng = random.Random(1104)
tcp_sends = 0
tcp_delivered = 0
tcp_extra_rtts = 0
for _ in range(N_SEG):
    tries = 0
    while True:
        tries += 1
        tcp_sends += 1
        if rng.random() >= P_LOSS:
            break
    tcp_extra_rtts += tries - 1
tcp_delivered = N_SEG
udp_delivered = sum(1 for _ in range(N_SEG) if rng.random() >= P_LOSS)
udp_lost = N_SEG - udp_delivered
print(f"  TCP : {tcp_delivered}/{N_SEG} segments delivered after"
      f" {tcp_sends} transmissions ({tcp_extra_rtts} extra sends,"
      f" each costing about one RTT)")
print(f"  UDP : {udp_delivered}/{N_SEG} datagrams arrived,"
      f" {udp_lost} silently dropped - no retransmit exists")
assert tcp_delivered == N_SEG
expected_extra = N_SEG * P_LOSS / (1 - P_LOSS)
print(f"  theory: extra sends ~ N*p/(1-p) = {expected_extra:.1f},"
      f" measured {tcp_extra_rtts}")
RTT_GPON = 12.0
tcp_time = tcp_extra_rtts * RTT_GPON
udp_gap_bytes = udp_lost * MSS_STD
print(f"  at the GPON's {RTT_GPON:.0f} ms RTT the recovery cost"
      f" ~{tcp_time:.0f} ms of pure waiting; UDP lost"
      f" {udp_gap_bytes:,} bytes with zero notice")
assert udp_gap_bytes == udp_lost * MSS_STD
```

TCP delivered 1,000 of 1,000 segments - after 1,054 transmissions, the 54 extra sends matching the geometric theory N·p/(1-p) = 52.6 and costing about one RTT each: roughly 648 ms of pure recovery waiting at the GPON's 12 ms RTT. UDP delivered 950 of 1,000 and the other 50 - 73,000 bytes of layer-4 payload - vanished without any notice, because UDP has no retransmit to notice with. This is why DNS queries ride UDP (RFC 1035): one small question either lands or is retried by the client above, so the protocol pays nothing for state it would never use; it is also why HTTP/3's QUIC (RFC 9000) rebuilds reliability on top of UDP - keeping UDP's connectionless framing while restoring TCP's guarantees in user space.

## DNS: From a Name to an Address

Before the first packet can even be addressed, `api.example.com` has to become an IP address. A cold resolution walks five hops:

```python
WALK = [
    ("browser cache",    "miss"),
    ("OS stub resolver", "miss -> forward to the recursive resolver"),
    ("recursive -> root", "referral to the .com TLD servers"),
    ("recursive -> .com TLD", "referral to the domain's nameservers"),
    ("recursive -> authoritative", "A record: the server's address"),
]
for hop, result in WALK:
    print(f"  {hop:<28} {result}")
n_upstream = sum(1 for h, _ in WALK if h.startswith("recursive"))
client_rtt_cold = 1 + n_upstream   # 1 to the resolver + each upstream hop
print(f"  cold resolution = {n_upstream} upstream lookups +"
      f" {client_rtt_cold - n_upstream} client-to-resolver round trip"
      f" = {client_rtt_cold} RTT total")
TTL = 300          # seconds the record may be cached (RFC 1035)
SESSION_MIN = 30   # a 30-minute working session
EVERY = 30         # one lookup every 30 seconds
n_queries = SESSION_MIN * 60 // EVERY
times = [t * EVERY for t in range(n_queries)]
misses = [t for t in times if t % TTL == 0]
hits = n_queries - len(misses)
print(f"  session: {n_queries} lookups over {SESSION_MIN} min,"
      f" TTL {TTL} s -> {len(misses)} cold misses at"
      f" t = {misses}, {hits} cache hits")
assert len(misses) == 6 and hits == 54
share = hits / n_queries
print(f"  {share:.0%} of lookups never leave the machine -"
      f" TTL, not the resolver, sets the re-resolution bill")
```

The cold walk costs 4 RTT: three upstream referrals (root, then .com TLD, then the domain's authoritative nameserver) plus the client-to-resolver round trip. But the record comes back with a TTL - RFC 1035's 32-bit statement of how long the answer may be cached - and the TTL does the rest of the work. A 30-minute session that looks the name up every 30 seconds issues 60 lookups, of which exactly 6 are cold (at t = 0, 300, 600, 900, 1200, 1500 - the TTL boundaries) and 54 hit the cache: 90 percent of lookups never leave the machine. When you pick a TTL for your own serving DNS, you are choosing this re-resolution bill; the DNS-safe hostnames from [1102](./1102-Star-Topology-Core.md) ride on top of whatever you decide.

## Ports and the TLS Wrap

The address says which machine; the port says which service. Six numbers cover the whole Phase 1 serving story:

```python
PORTS = [
    (22,    "SSH",    "terminal into the GPU box"),
    (53,    "DNS",    "name lookups (UDP, with TCP fallback)"),
    (80,    "HTTP",   "plain web traffic, no TLS wrap"),
    (443,   "HTTPS",  "HTTP inside TLS - the default API port"),
    (11434, "Ollama", "local model server (the Phase 1 default)"),
    (8000,  "vLLM",   "OpenAI-compatible serving endpoint"),
]
for port, svc, note in PORTS:
    print(f"  :{port:<5} {svc:<7} {note}")
def ledger(name, rtts_before_request, rtt):
    """rtts_before_request = round trips before the request itself is on
    the wire; 0-RTT puts the request in flight 1, so the count is 0."""
    to_first_byte = (rtts_before_request + 1) * rtt
    print(f"  {name:<38} {rtts_before_request} RTT to send"
          f" -> first byte {to_first_byte:>5.0f} ms")
    return to_first_byte
RTT = 12.0
a = ledger("http:// (TCP only)", 1, RTT)
b = ledger("https:// TLS 1.2 (RFC 5246 era)", 3, RTT)
c = ledger("https:// TLS 1.3 (RFC 8446)", 2, RTT)
d = ledger("https:// TLS 1.3 resumed (0-RTT)", 0, RTT)
e = ledger("HTTP/3 fresh over QUIC (RFC 9000)", 1, RTT)
assert a == 24.0 and b == 48.0 and c == 36.0 and d == 12.0 and e == 24.0
N_REQ = 1_000
new_conn = N_REQ * (c / RTT) * RTT
keepalive = (c / RTT) * RTT + N_REQ * RTT
print(f"  {N_REQ} requests, new connection each:"
      f" {new_conn:,.0f} ms; one kept-alive connection:"
      f" {keepalive:,.0f} ms ({(1 - keepalive / new_conn):.0%} saved)")
```

The ledger counts round trips, not folklore. Plain `http://` spends 1 RTT on TCP before the request can fly - first byte in 24 ms. The legacy TLS 1.2 stack needs TCP's RTT plus two more for the certificate and key exchange: 3 RTT, first byte in 48 ms. TLS 1.3 (RFC 8446) restructured the handshake to one round trip: 2 RTT total, 36 ms - and its 0-RTT resumption puts the request in the very first flight, 12 ms. QUIC folds transport and crypto setup into a single 1-RTT handshake on UDP: 24 ms fresh, and that is before any 0-RTT resumption. The amortization line is the one that changes how you configure clients: 1,000 requests on new connections cost 36,000 ms of handshake at this RTT, while one kept-alive connection costs 12,036 ms - 67 percent of the transport bill is connection setup, and the serving endpoints from [1402](../1400-llmops/1402-vLLM-and-TGI.md) inherit whatever you decide.

## The End-to-End First-Token Budget

Put the whole stack together into the number users actually feel: the first token. The model itself needs a fixed 80 ms here (prefill plus one decoded token); everything else is the stack you just learned:

```python
MODEL_FIRST = 80.0     # ms: prefill + first decoded token (toy, fixed)
RTT_LOCAL = 12.0       # the 1101 GPON, same-region endpoint
RTT_FAR = 80.0         # a cross-region VPS
def first_token(name, dns_rtts, tcp_tls_rtts, rtt):
    transport = (dns_rtts + tcp_tls_rtts + 1) * rtt
    total = transport + MODEL_FIRST
    share = transport / total
    print(f"  {name:<34} transport {transport:>5.0f} ms"
          f" -> first token {total:>5.0f} ms ({share:.0%} transport)")
    return transport
cold_far = first_token("A cold, cross-region, TLS 1.3", 4, 2, RTT_FAR)
cold_local = first_token("B cold, same-region, TLS 1.3", 4, 2, RTT_LOCAL)
warm_local = first_token("C warm (cached DNS + keep-alive)", 0, 0, RTT_LOCAL)
cold_h3 = first_token("D cold, HTTP/3 over QUIC", 4, 1, RTT_LOCAL)
CALLS = 100_000
per_day_cold = cold_local * CALLS / 1000 / 3600
per_day_warm = warm_local * CALLS / 1000 / 3600
saved = (cold_local - warm_local) * CALLS / 1000 / 3600
print(f"  {CALLS:,} calls/day of user-visible handshake time:")
print(f"    cold B: {per_day_cold:.1f} h   warm C: {per_day_warm:.1f} h"
   f"   handshake tax: {saved:.1f} h/day")
assert cold_far > cold_local > warm_local
print(f"  the model answers in {MODEL_FIRST:.0f} ms; config A makes users"
      f" wait {cold_far / MODEL_FIRST:.1f}x that in transport alone")
```

The ordering is strict - A (640 ms, 88 percent transport) over B (164 ms, 51 percent) over D (152 ms, 47 percent - QUIC's single handshake saving one of B's RTTs) down to C (92 ms, 13 percent, warm connections). At 100,000 calls a day, the difference between cold B and warm C is 2.0 hours of aggregate user-visible handshake time every day - and the cross-region config A makes users wait 7.0x the model's own answer time in transport alone. Nothing here touched the model: the entire win is layers 1 through 7 doing their jobs with fewer round trips, which is the whole reason a network lesson sits at the front of an LLM curriculum.

## Summary

- The seven layers are one request seen seven ways: HTTP data, TLS-encrypted records, session keys, TCP segments, IP packets, Ethernet frames, and bits on the fiber - and the same 40,000-byte context is 28 segments at MTU 1500 versus 5 at MTU 9000.
- TCP turns 5 percent packet loss into 1,000/1,000 delivery at 54 extra sends (~648 ms at a 12 ms RTT); UDP turns it into 50 silently missing datagrams - which is exactly right for DNS and exactly the hole QUIC re-plugs.
- Cold DNS costs 4 RTT and a TTL of 300 s absorbs 54 of a 30-minute session's 60 lookups - 90 percent never leave the machine.
- The handshake ledger at 12 ms RTT: 24 ms plain HTTP, 48 ms TLS 1.2, 36 ms TLS 1.3, 12 ms with 0-RTT, 24 ms fresh QUIC - and keep-alive reclaims 67 percent of a 1,000-request bill.
- The first-token budget says what it is all worth: 640 ms cold cross-region against 92 ms warm, 2.0 h/day of aggregate handshake tax at 100k calls - transport, not the model, is the cheapest latency you will ever delete.

## References

- [RFC 9293: Transmission Control Protocol (TCP)](https://www.rfc-editor.org/rfc/rfc9293.html) - the current TCP specification (August 2022), which obsoleted RFC 793; connection setup, numbering, acknowledgements, retransmission
- [RFC 768: User Datagram Protocol](https://www.rfc-editor.org/rfc/rfc768.html) - the 1980 connectionless datagram protocol: no setup, no delivery guarantee
- [RFC 1035: Domain Names - Implementation and Specification](https://www.rfc-editor.org/rfc/rfc1035.html) - the DNS query/response model and the 32-bit TTL field caches obey
- [RFC 8446: The Transport Layer Security (TLS) Protocol Version 1.3](https://www.rfc-editor.org/rfc/rfc8446.html) - the 1-RTT handshake and the 0-RTT resumption mode
- [RFC 9000: QUIC - A UDP-Based Multiplexed and Secure Transport](https://www.rfc-editor.org/rfc/rfc9000.html) - transport and TLS 1.3 integrated in one handshake
- ISO/IEC 7498-1 (ITU-T X.200), The Basic Model - the seven-layer reference this lesson's classification follows
- Kurose & Ross, Computer Networking: A Top-Down Approach, chapters 1-3 - the deeper treatment the module README already recommends

## Next Steps

- [1103: Jumbo Frames and MTU Optimization](./1103-Jumbo-Frames-and-MTU.md) - the MTU boundary this lesson's segment counts assumed
- [1201: Proxmox Hypervisor Standard Operating Procedures](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md) - the next module: virtualizing the machines this traffic runs between
- [1402: vLLM and TGI](../1400-llmops/1402-vLLM-and-TGI.md) - the serving endpoint whose ports and handshakes this lesson priced

**Estimated Time:** 2 hours
