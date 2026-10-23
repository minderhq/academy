---
Document ID: CHEAT-SHEET-063
Title: "CHEAT-SHEET-063: Realtime Voice Agents - the Serial Bill, the Streaming Overlap, and the Turn-Taking Gate"
Last Updated: 2026-10-23
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'multimodal', 'serving', 'inference']
---

# CHEAT-SHEET-063: Realtime Voice Agents - the Serial Bill, the Streaming Overlap, and the Turn-Taking Gate

The scope scan that picked this page: a repo-wide scan for speech-to-speech, voice agents, realtime APIs, and streaming TTS returns zero of the catalog's 563 markdown docs, and turn detection returns zero too - the loop's one named mechanism surfaces only as asides, barge-in in two files (a voice-pipeline latency line in CHEAT-SHEET-022 and an interruption aside in 3502-Audio-Models), neither the operator page. The pieces live apart: 3502 teaches the audio models, LAB-012 builds the voice-assistant container, TUTORIAL-006 the real-time streaming patterns, and CHEAT-SHEET-022 the multimodal latency line - each a piece, none the turn-taking operator page. The operator questions that start the moment a voice loop goes live have no home: what does one turn cost before the first word, what does overlap buy, where does turn-taking break, and how does the stack meet a first-audio budget. No dedicated operator page and no dedicated module exists anywhere in the catalog.

The sheet runs as seven exhibits: the serial bill (F1 - every stage waits for the last one), the streaming bill (F2 - overlap buys 230 ms and the budget still loses), the endpoint and barge-in gate (F3 - a dial between latency and false turns), the prefix-cache bill (F4 - the system prompt is the working set), the TTS cutover (F5 - speak at the first sentence), the turn ladder (F6 - four levers take 1,300 ms to 570 ms), and the ablation audit (F7 - no single lever carries the stack). Every number below is printed by the canonical fence at the bottom of the page: the full 211-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 57-line output sits frozen below it byte-for-byte.

## The Serial Bill - Every Stage Waits for the Last One

The serial pipeline sums its legs. On the fixture, every turn pays 400 ms of VAD endpoint + 200 ms ASR commit + 300 ms LLM prefill-to-first-token + 300 ms TTS-to-first-audio + 100 ms of serialized network = 1,300 ms of first-audio latency against the 700 ms operator budget - 600 ms over the line (+85.7%), 1.86x the budget. No single stage is the problem; the stack is: every stage waits for the previous one to fully finish. This bill is the baseline every lever below spends against.

```text
  legs per turn (ms): endpoint 400 + asr 200 + llm 300 + tts 300 + net 100
  serial first-audio: 1,300 ms
  operator budget:    700 ms
  over the line by:   600 ms (+85.7%)
  ratio:              1.86x the budget
  -> the one-model-per-stage stack cannot meet the turn-taking line: every stage waits for the previous one to fully finish
```

## The Streaming Bill - Overlap Buys 230 ms and the Budget Still Loses

Streaming overlaps the stages and buys back 230 ms: ASR partials stream into the LLM on voice activity (150 ms), TTS warms during decode (180 ms), headers piggyback on open streams (40 ms) - first audio at 1,070 ms (-17.7%). The overlap hides 50 ms of ASR-commit pipelining, 120 ms of TTS warm-start and 60 ms of header overlap. The stack is still 370 ms over the line - streaming is the first rung, not the fix.

```text
  streamed legs (ms): endpoint 400 + asr 150 + llm 300 + tts 180 + net 40
  streaming first-audio: 1,070 ms (-230 ms, -17.7%)
  overlap hides: asr-commit pipelining 50 + tts warm-start 120 + header overlap 60 = 230 ms
  -> streaming buys 230 ms and the stack is still 370 ms over: the stages overlap, the budget still loses
```

## The Endpoint and Barge-In Gate - a Dial Between Latency and False Turns

The endpoint timeout is a dial between latency and false turns. Cutting VAD silence from 400 to 250 ms hands every turn 150 ms (stack 1,070 -> 920 ms) at a measured price: false turn-ends rise from 2 to 7 per 100 turns, each one a reply the pipeline cut off and had to recover. Barge-in prices the same trade at conversation scale: the fixture's 12 interruptions speak on for 16.8 s with no cancel policy; a 120 ms cancel window cuts the waste to 1.44 s (-91.4%).

```text
  endpoint 400 -> 250 ms: every turn gains 150 ms (stack 1,070 -> 920)
  price: false turn-ends 2 -> 7 of 100 turns (+5 recoveries)
  barge-in: 12 interruptions x 1,400 ms spoken-on = 16.8 s wasted; 120 ms cancel = 1.44 s (-91.4%)
  -> the endpoint timeout is a dial between latency and false turns; the barge-in cancel window decides how much of the reply the user has to talk over
```

## The Prefix-Cache Bill - the System Prompt Is the Working Set

The voice loop re-sends its context on every turn: 1,500 tokens (1,300 system + 200 user). Cacheless, that is 100 turns x 1,500 = 150,000 prefilled tokens = 300 ms of TTFT per turn at 0.2 ms/tok. Prefix caching serves the same turns at 40 ms (-260 ms, -86.7%) and never prefills 130,000 tokens across the session - 26.0 s of TTFT returned to it. The system prompt is the voice loop's working set, and the tiered cache from CHEAT-SHEET-062 is what keeps it warm.

```text
  context per turn: 1,500 tokens (1,300 system + 200 user), re-sent every turn
  cacheless prefill: 100 turns x 1,500 tok = 150,000 tokens at 0.2 ms/tok = 300 ms TTFT
  cached prefill:    20,000 fresh tokens = 40 ms TTFT (-260 ms, -86.7%)
  session bill: 130,000 tokens never prefilled (-86.7%); 26.0 s of TTFT returned to the session
  -> the system prompt is the voice loop's working set: it is the same 1,300 tokens on every turn, and the tiered cache from CHEAT-SHEET-062 is what keeps it warm
```

## The TTS Cutover - Speak at the First Sentence

The TTS leg is 180 ms and half of it is smoothing: a 90 ms three-sentence buffer before synthesis plus 90 ms of synth-to-first-audio. Cut over at the first sentence boundary and the buffer disappears - the leg drops to 90 ms (-90 ms). Prosody starts on fewer than three sentences; the buffer was smoothing audio the user has not waited for yet.

```text
  tts leg 180 ms = 90 ms buffer + 90 ms synth-to-first-audio
  speak at the first sentence boundary: buffer removed, tts leg 90 ms (-90 ms)
  -> prosody starts on fewer than three sentences; the buffer was smoothing audio the user has not waited for yet
```

## The Turn Ladder - Four Levers Take 1,300 ms to 570 ms

The levers stack additively because each owns one leg: serial 1,300 ms -> streaming 1,070 (-230) -> endpoint 250: 920 (-150) -> prefix cache: 660 (-260) -> TTS cutover: 570 (-90). The final stack is 130 ms under the 700 ms line - 43.8% of the serial bill. Four levers moved the first-audio line, and no one of them is optional.

```text
  serial           1,300 ms
  streaming        1,070 ms  (-230)
  +endpoint 250    920 ms  (-150)
  +prefix cache    660 ms  (-260)
  +tts cutover     570 ms  (-90)
  final stack: 570 ms, 130 ms under the 700 ms line (43.8% of serial)
  -> four levers moved the first-audio line 1,300 -> 570 ms; the rungs are additive because each lever owns one leg
```

## The Ablation Audit - No Single Lever Carries the Stack

Grade the stack by ablation. Remove the prefix cache: 830 ms, over by 130. Remove streaming: 800 ms, over by 100. Remove the endpoint tune: 720 ms, over by 20. Remove the TTS cutover: 660 ms - the only removal that survives. Three of four single removals break the line, and the deltas order the build: cache first, streaming second, endpoint third, cutover last. The biggest rung is the one serving already owns - the warm prefix.

```text
  -cache        back to 830 ms - over by 130
  -streaming    back to 800 ms - over by 100
  -endpoint     back to 720 ms - over by 20
  -tts cutover  back to 660 ms - under by 40
  3 of 4 single removals break the line; the deltas order the build: cache first, streaming second, endpoint third, cutover last
  -> no single lever carries the stack to 700 ms; the audio stack is a composition, and the biggest rung is the one serving already owns - the warm prefix
```

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Pricing the stack per model instead of per turn | F1: no leg exceeds 400 ms yet the turn lands at 1,300 - the line is first audio, not any stage's latency |
| Shipping streaming as the whole fix | F2: overlap buys 230 ms and the stack is still 370 ms over - streaming is rung one of four |
| Tuning the endpoint without counting false turns | F3: 400 -> 250 ms buys 150 ms per turn at 2 -> 7 false turn-ends per 100 - the recoveries are the bill |
| Re-sending the context cacheless | F4: 150,000 prefilled tokens is 300 ms of TTFT per turn - the 1,300-token system prompt is 86.7% of the bill |
| Waiting on the multi-sentence TTS buffer | F5: the buffer is 90 ms of a 180 ms leg - it smooths audio the user has not waited for |
| Shipping one lever and declaring victory | F7: -cache alone leaves 830 ms (over by 130) - no single lever reaches 700; the deltas order the build |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| first audio is still over the line | the endpoint timeout is stock - cut VAD silence toward 250 ms and log false turn-ends next to TTFT (fixture: 150 ms per turn at 2 -> 7 false ends) (f2) |
| users get cut off mid-sentence | the aggressive endpoint fires on pauses - gate turn-end on prosody as well as silence, and keep a 120 ms barge-in cancel so a wrong cut costs a token, not a reply (f3) |
| every turn pays full TTFT | the context is re-sent cacheless - pin the 1,300-token system prompt as a cached prefix; the fixture returns 260 ms per turn and 26.0 s per session (f4) |
| replies sound clipped or rushed | the TTS buffer was cut without a floor - speak at the first sentence boundary and keep sentence two synthesizing warm behind it (f5) |
| the stack regresses after a serving change | no per-leg probe - alert each leg (endpoint / asr / llm / tts / net) against its ladder rung; one regression lands on one leg at a time (f6) |
| one lever shipped and the budget is still missed | the rungs are additive but not optional - cache alone leaves 830 ms, cutover alone 1,210; the deltas order the build (f7) |

## Quick Reference For

- [4204: KV-Cache Paging and Prefix Caching](../../phases/phase4-quantization/4200-kv-cache/4204-KV-Cache-Paging-and-Prefix-Caching.md) - the paging and prefix-caching layer the F4 bill spends.
- [4201: Context Window Physics and OOM Prevention](../../phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md) - the context-window physics behind the re-sent 1,500 tokens.
- [3502: Audio Models](../../phases/phase3-transformers/3500-multimodal/3502-Audio-Models.md) - the audio-models lesson the loop's ASR and TTS legs stand on.
- [1402: vLLM and TGI High-Concurrency Inference](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - the serving surface whose prefix cache keeps the loop warm.
- [1405: SGLang RadixAttention Serving](../../phases/phase1-infra/1400-llmops/1405-SGLang.md) - the serving stack whose radix cache serves the same working set.

## The Canonical Fence

This sheet's every number - the serial bill, the streaming bill, the endpoint and barge-in gate, the prefix-cache bill, the TTS cutover, the turn ladder, the ablation audit - comes from the fence below, printed by a real run and pinned with asserts: the full 211-line stdlib program reproduces F1 through F7, and its 57-line output sits frozen under it byte-for-byte.

```python
"""CHEAT-SHEET-063: Realtime Voice Agents - the Serial Bill, the
Streaming Overlap, and the Turn-Taking Gate.

Fixture: one 100-turn voice session. Every turn is one user utterance plus
one assistant reply. The context re-sent on every turn is 1,500 tokens
(1,300 system + 200 user). Prefill runs at 0.2 ms/token (5,000 tok/s).
The session carries 12 user interruptions. The operator budget this sheet
scores against is the 700 ms first-audio line: past it, the user starts
talking over a reply that has not started.
All numbers below are fixture constants or arithmetic on them - no RNG,
no wall clock, two runs print the same bytes.
"""
# ---------------------------------------------------------------- fixtures
TURNS = 100
INTERRUPTS = 12
TARGET_MS = 700
RULE = "=" * 64       # exhibit separator; the sheet slices the run on it

# serial per-turn legs, milliseconds
EP_SERIAL = 400      # VAD endpoint: silence before the turn is declared over
ASR_COMMIT = 200     # ASR: partial accepted, final hypothesis committed
LLM_TTFT = 300       # LLM: prefill of the 1,500-token context to first token
TTS_FIRST = 300      # TTS: text in, first audio byte out
NET_SERIAL = 100     # network: 50 up + 50 down, serialized request/response

SERIAL = EP_SERIAL + ASR_COMMIT + LLM_TTFT + TTS_FIRST + NET_SERIAL
assert SERIAL == 1300, SERIAL

print(RULE)
print("F1 | THE SERIAL BILL")
print("  legs per turn (ms): endpoint %d + asr %d + llm %d + tts %d + net %d"
      % (EP_SERIAL, ASR_COMMIT, LLM_TTFT, TTS_FIRST, NET_SERIAL))
print("  serial first-audio: %s ms" % format(SERIAL, ","))
print("  operator budget:    %s ms" % format(TARGET_MS, ","))
over = SERIAL - TARGET_MS
assert over == 600, over
print("  over the line by:   %s ms (+%.1f%%)" % (format(over, ","),
                                                100.0 * over / TARGET_MS))
print("  ratio:              %.2fx the budget" % (SERIAL / TARGET_MS))
print("  -> the one-model-per-stage stack cannot meet the turn-taking line: "
      "every stage waits for the previous one to fully finish")

# ---------------------------------------------------------------- F2
# streaming overlap: three legs shrink because the stages run concurrently
ASR_STREAM = 150      # partials stream into the LLM on voice activity
TTS_STREAM = 180      # TTFB -> first chunk: synth warms during LLM decode
NET_STREAM = 40       # headers piggyback on open streams

STREAM = EP_SERIAL + ASR_STREAM + LLM_TTFT + TTS_STREAM + NET_STREAM
assert STREAM == 1070, STREAM
D_STREAM = SERIAL - STREAM
assert D_STREAM == 230, D_STREAM

print()
print(RULE)
print("F2 | THE STREAMING BILL")
print("  streamed legs (ms): endpoint %d + asr %d + llm %d + tts %d + net %d"
      % (EP_SERIAL, ASR_STREAM, LLM_TTFT, TTS_STREAM, NET_STREAM))
print("  streaming first-audio: %s ms (-%s ms, -%.1f%%)"
      % (format(STREAM, ","), format(D_STREAM, ","),
         100.0 * D_STREAM / SERIAL))
print("  overlap hides: asr-commit pipelining %d + tts warm-start %d + "
      "header overlap %d = %d ms"
      % (ASR_COMMIT - ASR_STREAM, TTS_FIRST - TTS_STREAM,
         NET_SERIAL - NET_STREAM, D_STREAM))
print("  -> streaming buys %s ms and the stack is still %s ms over: the "
      "stages overlap, the budget still loses"
      % (format(D_STREAM, ","), format(STREAM - TARGET_MS, ",")))

# ---------------------------------------------------------------- F3
# the endpoint gate: shorter silence timeout, faster turns, more false ones
EP_TUNED = 250
STACK_EP = STREAM - (EP_SERIAL - EP_TUNED)
assert STACK_EP == 920, STACK_EP
D_EP = EP_SERIAL - EP_TUNED
assert D_EP == 150, D_EP

FALSE_AT_400 = 2      # pauses mistaken for turn ends, per 100 turns
FALSE_AT_250 = 7
WASTE_NO_POLICY_MS = INTERRUPTS * 1400    # pipeline speaks on, avg overrun
WASTE_CANCEL_MS = INTERRUPTS * 120        # barge-in cancel window
CUT = 1.0 - WASTE_CANCEL_MS / WASTE_NO_POLICY_MS
assert abs(CUT - 0.9142857142857143) < 1e-9, CUT

print()
print(RULE)
print("F3 | THE ENDPOINT AND BARGE-IN GATE")
print("  endpoint %d -> %d ms: every turn gains %d ms (stack %s -> %s)"
      % (EP_SERIAL, EP_TUNED, D_EP, format(STREAM, ","),
         format(STACK_EP, ",")))
print("  price: false turn-ends %d -> %d of %d turns (+%d recoveries)"
      % (FALSE_AT_400, FALSE_AT_250, TURNS, FALSE_AT_250 - FALSE_AT_400))
print("  barge-in: %d interruptions x 1,400 ms spoken-on = %s s wasted; "
      "120 ms cancel = %.2f s (-%.1f%%)"
      % (INTERRUPTS, format(WASTE_NO_POLICY_MS / 1000.0, ".1f"),
         WASTE_CANCEL_MS / 1000.0, 100.0 * CUT))
print("  -> the endpoint timeout is a dial between latency and false "
      "turns; the barge-in cancel window decides how much of the reply "
      "the user has to talk over")

# ---------------------------------------------------------------- F4
CTX = 1500
SYS = 1300
USER = CTX - SYS
RATE_MS_PER_TOK = 0.2
LLM_CACHED = round((CTX - SYS) * RATE_MS_PER_TOK)
assert LLM_CACHED == 40, LLM_CACHED
D_CACHE = LLM_TTFT - LLM_CACHED
assert D_CACHE == 260, D_CACHE

TOK_CACHELESS = TURNS * CTX
TOK_CACHED = TURNS * (CTX - SYS)
SAVED_TOK = TOK_CACHELESS - TOK_CACHED
SAVED_S = D_CACHE * TURNS / 1000.0
assert SAVED_TOK == 130000, SAVED_TOK
assert SAVED_S == 26.0, SAVED_S

print()
print(RULE)
print("F4 | THE PREFIX-CACHE BILL")
print("  context per turn: %s tokens (%s system + %s user), re-sent "
      "every turn" % (format(CTX, ","), format(SYS, ","),
                      format(USER, ",")))
print("  cacheless prefill: %s turns x %s tok = %s tokens at %.1f ms/tok "
      "= %s ms TTFT"
      % (TURNS, format(CTX, ","), format(TOK_CACHELESS, ","),
         RATE_MS_PER_TOK, format(LLM_TTFT, ",")))
print("  cached prefill:    %s fresh tokens = %s ms TTFT (-%s ms, -%.1f%%)"
      % (format(TOK_CACHED, ","), format(LLM_CACHED, ","),
         format(D_CACHE, ","), 100.0 * D_CACHE / LLM_TTFT))
print("  session bill: %s tokens never prefilled (-%.1f%%); %s s of TTFT "
      "returned to the session"
      % (format(SAVED_TOK, ","), 100.0 * SAVED_TOK / TOK_CACHELESS,
         format(SAVED_S, ".1f")))
print("  -> the system prompt is the voice loop's working set: it is the "
      "same %s tokens on every turn, and the tiered cache from "
      "CHEAT-SHEET-062 is what keeps it warm" % format(SYS, ","))

# ---------------------------------------------------------------- F5
TTS_BUFFER = 90        # three-sentence smoothing buffer before synth
TTS_CUT = TTS_STREAM - TTS_BUFFER
assert TTS_CUT == 90, TTS_CUT
D_TTS = TTS_STREAM - TTS_CUT
assert D_TTS == 90, D_TTS

print()
print(RULE)
print("F5 | THE TTS CUTOVER")
print("  tts leg %d ms = %d ms buffer + %d ms synth-to-first-audio"
      % (TTS_STREAM, TTS_BUFFER, TTS_CUT))
print("  speak at the first sentence boundary: buffer removed, tts leg "
      "%d ms (-%d ms)" % (TTS_CUT, D_TTS))
print("  -> prosody starts on fewer than three sentences; the buffer was "
      "smoothing audio the user has not waited for yet")

# ---------------------------------------------------------------- F6
stacks = [("serial", SERIAL), ("streaming", STREAM),
          ("+endpoint 250", STACK_EP),
          ("+prefix cache", STACK_EP - D_CACHE),
          ("+tts cutover", STACK_EP - D_CACHE - D_TTS)]
FINAL = stacks[-1][1]
assert FINAL == 570, FINAL
assert FINAL == EP_TUNED + ASR_STREAM + LLM_CACHED + TTS_CUT + NET_STREAM
assert all(a - b == d for (na, a), (nb, b), d in
           zip(stacks, stacks[1:], [230, 150, 260, 90])), stacks
HEADROOM = TARGET_MS - FINAL
assert HEADROOM == 130, HEADROOM

print()
print(RULE)
print("F6 | THE TURN LADDER")
prev = None
for name, ms in stacks:
    step = "" if prev is None else "  (-%d)" % (prev - ms)
    print("  %-16s %s ms%s" % (name, format(ms, ","), step))
    prev = ms
print("  final stack: %s ms, %s ms under the %s ms line (%.1f%% of serial)"
      % (format(FINAL, ","), format(HEADROOM, ","), format(TARGET_MS, ","),
         100.0 * FINAL / SERIAL))
print("  -> four levers moved the first-audio line %s -> %s ms; the rungs "
      "are additive because each lever owns one leg"
      % (format(SERIAL, ","), format(FINAL, ",")))

# ---------------------------------------------------------------- F7
ABL = [("cache", D_CACHE, FINAL + D_CACHE),
       ("streaming", D_STREAM, FINAL + D_STREAM),
       ("endpoint", D_EP, FINAL + D_EP),
       ("tts cutover", D_TTS, FINAL + D_TTS)]
over_count = sum(1 for _, _, ms in ABL if ms > TARGET_MS)
assert over_count == 3, over_count
order = sorted(ABL, key=lambda t: -t[1])
assert [t[0] for t in order] == ["cache", "streaming", "endpoint",
                                 "tts cutover"], order

print()
print(RULE)
print("F7 | THE ABLATION AUDIT")
for name, d, ms in ABL:
    verdict = ("over by %d" % (ms - TARGET_MS)) if ms > TARGET_MS \
        else "under by %d" % (TARGET_MS - ms)
    print("  -%-12s back to %s ms - %s"
          % (name, format(ms, ","), verdict))
print("  %d of 4 single removals break the line; the deltas order the "
      "build: cache first, streaming second, endpoint third, cutover last"
      % over_count)
print("  -> no single lever carries the stack to %s ms; the audio stack "
      "is a composition, and the biggest rung is the one serving already "
      "owns - the warm prefix" % format(TARGET_MS, ","))

print()
print("FENCE-063-OK")
```

```text
================================================================
F1 | THE SERIAL BILL
  legs per turn (ms): endpoint 400 + asr 200 + llm 300 + tts 300 + net 100
  serial first-audio: 1,300 ms
  operator budget:    700 ms
  over the line by:   600 ms (+85.7%)
  ratio:              1.86x the budget
  -> the one-model-per-stage stack cannot meet the turn-taking line: every stage waits for the previous one to fully finish

================================================================
F2 | THE STREAMING BILL
  streamed legs (ms): endpoint 400 + asr 150 + llm 300 + tts 180 + net 40
  streaming first-audio: 1,070 ms (-230 ms, -17.7%)
  overlap hides: asr-commit pipelining 50 + tts warm-start 120 + header overlap 60 = 230 ms
  -> streaming buys 230 ms and the stack is still 370 ms over: the stages overlap, the budget still loses

================================================================
F3 | THE ENDPOINT AND BARGE-IN GATE
  endpoint 400 -> 250 ms: every turn gains 150 ms (stack 1,070 -> 920)
  price: false turn-ends 2 -> 7 of 100 turns (+5 recoveries)
  barge-in: 12 interruptions x 1,400 ms spoken-on = 16.8 s wasted; 120 ms cancel = 1.44 s (-91.4%)
  -> the endpoint timeout is a dial between latency and false turns; the barge-in cancel window decides how much of the reply the user has to talk over

================================================================
F4 | THE PREFIX-CACHE BILL
  context per turn: 1,500 tokens (1,300 system + 200 user), re-sent every turn
  cacheless prefill: 100 turns x 1,500 tok = 150,000 tokens at 0.2 ms/tok = 300 ms TTFT
  cached prefill:    20,000 fresh tokens = 40 ms TTFT (-260 ms, -86.7%)
  session bill: 130,000 tokens never prefilled (-86.7%); 26.0 s of TTFT returned to the session
  -> the system prompt is the voice loop's working set: it is the same 1,300 tokens on every turn, and the tiered cache from CHEAT-SHEET-062 is what keeps it warm

================================================================
F5 | THE TTS CUTOVER
  tts leg 180 ms = 90 ms buffer + 90 ms synth-to-first-audio
  speak at the first sentence boundary: buffer removed, tts leg 90 ms (-90 ms)
  -> prosody starts on fewer than three sentences; the buffer was smoothing audio the user has not waited for yet

================================================================
F6 | THE TURN LADDER
  serial           1,300 ms
  streaming        1,070 ms  (-230)
  +endpoint 250    920 ms  (-150)
  +prefix cache    660 ms  (-260)
  +tts cutover     570 ms  (-90)
  final stack: 570 ms, 130 ms under the 700 ms line (43.8% of serial)
  -> four levers moved the first-audio line 1,300 -> 570 ms; the rungs are additive because each lever owns one leg

================================================================
F7 | THE ABLATION AUDIT
  -cache        back to 830 ms - over by 130
  -streaming    back to 800 ms - over by 100
  -endpoint     back to 720 ms - over by 20
  -tts cutover  back to 660 ms - under by 40
  3 of 4 single removals break the line; the deltas order the build: cache first, streaming second, endpoint third, cutover last
  -> no single lever carries the stack to 700 ms; the audio stack is a composition, and the biggest rung is the one serving already owns - the warm prefix

FENCE-063-OK
```
