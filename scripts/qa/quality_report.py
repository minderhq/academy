#!/usr/bin/env python3
"""One-command quality scorecard for the Minder Academy curriculum corpus.

Runs every committed QA gate as a subprocess, harvests its summary line,
and prints a single scorecard - the fast answer to "where does the corpus
stand today?" without running each tool by hand.

  hard gates (exit 1 on findings, CI contract):
    frontmatter_lint   frontmatter completeness/consistency (FM-01..FM-09)
    doc_id_check       Document ID unique across the corpus (DD-01):
                       manifest_export copies it into the platform
                       manifest's primary `id` field, so two docs
                       sharing one ID collapse the join; FM-03 locks
                       existence and FM-07 filename-prefix match,
                       this locks cross-file uniqueness - born from
                       the tick-328 census (408 files, 408 distinct
                       IDs, 0 duplicates)
    pip_uv_scan        bare pip install only inside documented exceptions
                       (Docker/container, conda workflows, uv bootstraps,
                       uv-first fallback blocks)
    langchain_census   every langchain/langgraph import in a ```python
                       fence resolves against the installed stack (LC-01)
    legacy_chain_scan  bare Name uses of langchain_classic-only chain/
                       agent names (LC-02) - catches the import-less
                       usage that the import-census cannot see (tick-224)
    legacy_langgraph_scan
                       legacy LangGraph entry/finish setter calls in
                       python fences (LG-01) - the modern surface builds
                       the same edge with add_edge(START, node) and the
                       corpus's own 7303 guide calls the setter the
                       legacy spelling; drained born-at-zero the same
                       tick-677 that landed the gate (the SS-01
                       zero-drain shape)
    codeblock_syntax_scan
                       every ```python fence parses as Python (CB-01);
                       non-Python content lives in an honest fence label
                       (text/bash/yaml) instead
    bashblock_syntax_scan
                       every ```bash fence passes bash -n (BB-01); doc
                       placeholders use runnable ${VAR} form, not <name>
    datablock_syntax_scan
                       every ```json fence parses as JSON (DB-01) and
                       every ```yaml fence parses as a YAML document
                       stream (DB-02); prose/formulas live in text fences
    assessment_lint    assessment/QUIZ.md + PRACTICE.md coverage (AS-01..AS-22;
                       AS-09 graduated tick-566 to a hard ceil(N/4) letter
                       ceiling - no letter above a quarter of the bank's
                       answered questions - over the 33 module banks AND
                       the 7 phase quizzes, which joined the gate's scope
                       the same tick (AS-03 numbering, AS-04 inline
                       coverage, AS-08 inline-vs-key-block agreement, in
                       the "### N." / lowercase-inline shape): the birth
                       census caught all seven phase banks skewed (phase 2
                       answering D on 70% of its questions, phase 5 B on
                       56.7%) and the option positions were permuted to
                       quarter shares (56 swaps, semantics untouched) before
                       the ceiling locked; AS-10 option uniformity - a question
                       carrying options carries exactly A-D, born tick-498
                       born-at-zero 655/655 four-option mcq; AS-11 answer-key
                       rows carry a filled explanation cell, born tick-514
                       born-at-zero after the 33/33-bank explanation drain;
                       AS-12 review maps must exist-consistently cite and
                       fully cover the bank's questions, applied where the
                       map exists, coverage grows with the review-map drain;
                       AS-13 the MASTER-INDEX phase-practice/quiz tables'
                       per-row count columns against the linked files -
                       practice rows count Exercise headings outside the
                       appendix reference-implementations section, quiz
                       rows count the numbered "### N." headings; born
                       tick-562 with the MI exercise column drifted on 5
                       of 7 phases (42 promised vs 34 on disk) and
                       drained to disk truth first; AS-14 each phase
                       quiz's learner-facing "**Passing: N/M (80%)**"
                       line - exactly one per quiz, its total equal to
                       the question count, its percentage the corpus's
                       80% convention, its threshold the integer ceil
                       of that percentage - born tick-567
                       census-proven at zero across all seven quizzes;
                       AS-15 the answer-length cue: the correct option
                       may be longest-or-tied (words AND characters,
                       QI-10's exact metric) in at most 50% of a quiz's
                       >= 4-option answered questions, under 10 such
                       questions exempt - a learner who always picks the
                       longest option would pass without reading; born
                       tick-568 catching exactly the seven phase quizzes
                       (83.3% corpus tied rate, peak 93.3%, a
                       longest-picker scoring ~83% against the 80%
                       passing line) while the module banks had already
                       drained to 2.4% under the report queue, drained
                       same tick with 75 one-distractor lengthenings;
                       AS-16 within-question option hygiene - no two
                       options of one question may carry the same
                       text (casefold + whitespace-collapse exact,
                       punctuation preserved) and no deferred or
                       compound option ("All of the above", "Both A
                       and C" letter-lists) may occupy an option
                       slot, since a repeat makes the key ambiguous
                       and a compound hides multi-answer logic in a
                       single-answer bank (corrupting the balance
                       AS-09 locks); born tick-569 catching exactly
                       35 deferred options across 16 module banks,
                       22 with the key ON the compound (a pick-two
                       question graded as one) and zero true
                       duplicates, drained same tick to concrete
                       keyed summaries and concrete false options);
                       AS-17 the stem-echo lock - the stem must
                       not hand over the answer: the keyed option
                       may not appear verbatim in the stem, and
                       >= 2 informative tokens shared by the stem
                       and the keyed option but by no distractor
                       is the phrase-match tell (a single echoed
                       token is normal vocabulary overlap,
                       measured 63/835 = 7.5% and legal; two or
                       more was exactly 7, three never occurs);
                       born tick-570 catching exactly 7 stem
                       echoes across 7 module banks, drained same
                       tick by rewording the keyed options off
                       their echoed tokens (4100-low-bit q8 keeps
                       its "channel" - the per-channel concept IS
                       the key - and its distractor gains the
                       token instead);
                       AS-18 the header-count-claim contract -
                       the phase quiz's learner-facing "**N
                       Questions | ...**" header must exist and
                       equal the quiz's actual question count,
                       scoped to the seven phase quizzes (the
                       passing line's total is AS-14's), born
                       tick-626 census-zero 7/7 headers present,
                       0 drift across 180 questions (15/20/25/30/30/30/30);
                       AS-19 the exercise-numbering contract -
                       inside each phase practice file the
                       "Exercise N" headings run 1..K with no
                       gap, repeat or wrong start, per segment
                       (main body and the phase 6-7 appendix
                       references each restart at 1), born
                       tick-627 census-zero 9/9 segments
                       contiguous (main 5/4/4/4/3/7/7,
                       appendix 6/5); module surface
                       joined tick-628 - all 33
                       PRACTICE.md files vouch one
                       1..K run per file, born
                       census 33/33 single-segment
                       contiguous, 184 exercises
                       (169 H3 + 15 H2 headings;
                       the H2 shape lives in
                       2300/4300/4400);
                       AS-20 the answer-key
                       written-numbering contract -
                       the phase quiz's "## Answer
                       Key" comma-pair entries must
                       run exactly 1..N, no gap,
                       repeat or broken order (the
                       dict collapses duplicates at
                       capture, AS-08 compares only
                       the intersection, RM-00 reads
                       only the 33 banks' key
                       tables), the tick-631
                       partition shape - a citation
                       outside the question set
                       stays AS-08's stale branch,
                       inside the set the written
                       sequence is AS-20's; joined
                       tick-635 - born census 7/7
                       keys write exact 1..N
                       (15/20/25/30/30/30/30,
                       180 entries);
                       AS-21 the phase-README
                       quiz-claim contract - each
                       phase README's Assessment
                       bullet "(NN questions, PP% to
                       pass)" must exist exactly
                       once, carry the linked quiz's
                       true question count and state
                       the corpus 80% convention
                       (feed_parity_check totals the
                       corpus aggregates,
                       course_card_check walks the
                       module READMEs - the claim
                       was vouched by nothing; the
                       quiz header is AS-18's, the
                       passing line AS-14's, the MI
                       rows AS-13's, a broken link
                       linkcheck's); joined tick-636
                       - census 7/7 carry the line,
                       1/7 (phase 3) wrote the true
                       count, 6 drained same tick -
                       born-at-zero
    quiz_export        quiz bank parses into complete question records
                       (blank-stem clause since tick-615: a question
                       whose stem line lost its text parses as a
                       finding for every type - born 0 across 660;
                       beyond-D clauses since tick-616: option rows
                       and key letters outside the A-D grammar parse
                       as findings - born 0 across 660;
                       platform-metadata clauses since tick-617:
                       the Instructions 'N questions' claim and
                       every key row's question presence are vouched
                       against the parsed bank - born 0/0 across 33
                       modules; passing-score clauses since tick-618:
                       the '(X/Y correct)' parenthetical's denominator,
                       percentage pairing and arithmetic are vouched
                       against the parsed bank - born 0/0/0 across the
                       32 modules carrying the form; duplicate-row
                       clauses since tick-619: a duplicated option row
                       or duplicated key row is a finding, not a
                       silent overwrite - born 0/0 across 33 modules; numbering
                       clause since tick-620: question numbers must run
                       1..N contiguously - born 0 gaps across 33 modules; duplicate-text
                       clause since tick-621: two options of one question
                       sharing the same text - born 0 across 660 questions; Instructions
                       section clause since tick-622: every module quiz
                       carries the section - born 33/33; duplicate-stem clause
                       since tick-623: two questions of one module
                       sharing a stem - born 0 across 33 modules; identity clauses
                       since tick-624: no Document ID, no Title, and
                       cross-module ID duplicates - born 0/0/0 across 33
                       modules; zero-points clause since tick-625:
                       graded against 0 points - born 0 across 660
                       questions)
    quiz_integrity_scan
                       content-level quiz integrity (QI-01..06 +
                       QI-08/09 + QI-11/12/13/15/16/17/18/19/20 hard:
                       self-referential positional
                       option, in-module duplicate stem, duplicate
                       option text, option beyond A-D, numbering
                       gap, cross-module stem dup, duplicate
                       Answer Key rows, orphan
                       Answer Key rows, QI-11 answer key with
                       no matching option row or <2-option
                       mcq, QI-12 ungradeable question (neither
                       mcq options nor a Score points line),
                       QI-13 unparseable Answer Key row ([A-D]-
                       only row regexes silently drop E+ /
                       two-letter cells), QI-14 checkpoint-quiz
                       item duplicating a bank stem (verbatim
                       item in a phase CHECKPOINT.md's 3-item
                       Checkpoint Quiz re-asks a bank question;
                       QI-11 born tick-374, QI-12 tick-474,
                       QI-13 tick-475, QI-14 tick-476, QI-15
                       tick-567 phase-quiz item duplicating a bank
                       or phase-quiz stem - born at 4 (all in
                       phase5-quiz.md), drained same tick,
                       baseline 0; QI-16 tick-629 option letters
                       written out of A-D order with the set
                       complete - born 655/655 mcq ABCD across
                       660 questions; phase surface tick-630
                       owns both sub-classes there
                       (assessment_lint's letter-keyed dict
                       collapses duplicates and destroys
                       order) - born 180/180 exact abcd
                       across 180 questions; QI-17 tick-631
                       checkpoint quiz item numbering (CK-04
                       reads only the item COUNT, QI-14 only
                       the stems) - born 33/33 module blocks
                       exact 1,2,3 across 99 items; QI-18
                       tick-642 within-bank duplicate answer-key
                       explanation text (AS-11 vouches the
                       cell's presence, QI-08 the duplicate
                       row - the text itself was read by
                       nothing; >= 2 distinct question numbers
                       per group) - born 0 duplicate groups
                       across 33 banks / 655 key rows; QI-19
                       tick-643 answer-key explanation restating
                       the keyed option verbatim (AS-11 vouches
                       the cell's presence, QI-18 the
                       cross-question duplicate - the
                       within-question mirror was read by
                       nothing) - born exactly 1
                       (3500-multimodal Q18) across 33 banks /
                       655 key rows, drained same tick; QI-20
                       tick-644 answer-key explanation restating
                       the question stem verbatim (AS-11 vouches
                       the cell's presence, QI-18 the
                       cross-question duplicate, QI-19 the
                       keyed-option mirror, AS-17 the
                       stem-to-keyed-option leak - the
                       explanation-to-stem mirror was read by
                       nothing; full mnorm() mirror only,
                       definition-shaped explanations and
                       partial restatements out) - born 0 mirrors
                       against 82 partial containments
                       across 33 banks / 655 key rows) on top of
                       quiz_export's parser; QI-07/QI-10
                       are the report inventory (the
                       skewed-answer-key shuffle queue -
                       superseded tick-566 by AS-09's hard
                       ceil(N/4) ceiling, which the queue
                       now merely previews + the
                       answer-length-bias queue: the correct
                       option is longest-or-tied in >=50% of a
                       module's questions - born from the
                       tick-290 census that measured a ~70%
                       pick-the-longest win rate vs ~25% chance,
                       31/33 modules queued) - born
                       from the tick-284 census (2 self-reference
                       bugs fixed at birth); QI-08/09 born from the
                       tick-285 census (0/0 - the one-directional
                       Answer Key join locked in reverse)
    structure_lint     fence parity + H1 discipline corpus-wide
    linkcheck          every relative link target exists on disk
    casecheck          case-sensitive href/disk match (Windows-invisible
                       breaks) + missing targets + orphan gate (a content
                       doc with zero inbound links is invisible to the
                       browse graph; README/TEMPLATE/CHANGELOG exempt);
                       crash-proofed tick-637 - a segment the OS path
                       normalization swallows (Win32 trailing dots/spaces)
                       lands in MISSING with file/line/href named, never
                       a bare IndexError
    anchor_check       in-document anchors vs GitHub-accurate slugger
                       (2 known inline-code examples allowlisted)
    table_lint         ragged GFM tables - header/separator/body lines
                       with differing cell counts (TL-01); escaped \\|
                       is a literal pipe, not a separator; loose rows
                       right after a table (TL-02 - an unescaped-pipe
                       line GFM swallows as an extra ragged row;
                       born tick-373, baseline 0)
    mermaid_lint       mermaid diagram fences: known diagram-type header
                       (MM-01), balanced () [] {} (MM-02), declared
                       direction on graph/flowchart (MM-03), no % outside
                       double quotes (MM-04 - lexer aborts the render)
    deprecated_scan    deprecated API calls in python fences (DA-01:
                       datetime.utcnow/utcfromtimestamp - Python 3.12+;
                       use datetime.now(timezone.utc); DA-02: HF
                       use_auth_token kwarg - removed in transformers
                       5.x; use token=; DA-03: pydantic v1 validation
                       and .dict() API - use @field_validator and
                       model_dump(); DA-04: torch.cuda.amp namespace -
                       use torch.amp; DA-05: transformers torch_dtype
                       kwarg - kept in v5 only as a BC shim, warns on
                       every load on the installed 5.10.2 stack; use
                       dtype=, born tick-639, drained same tick: 42
                       sites across 24 files + 5 text/bash riders);
                       comment-only mentions are not findings
    unsafe_exec_scan   unsafe dynamic execution in python fences
                       (UE-01: single-argument builtin eval()/exec()
                       - model output runs with full globals, a
                       prompt-injection -> code-execution path; use
                       the two-argument sandbox idiom
                       eval(expr, {"__builtins__": {}}, {}) or a
                       danger-marked teaching fence; .eval() method
                       calls and ast.literal_eval are out by
                       construction, born tick-645, drained same
                       tick: 13 sites across 9 files)
    unsafe_deserialize_scan
                       unsafe deserialization in python fences
                       (UD-01: torch.load() without weights_only -
                       a checkpoint is a pickle payload and torch
                       >= 2.6 defaults weights_only=True; UD-02:
                       pickle-family load/loads - unpickling executes
                       __reduce__ payloads, 7500-security vouches
                       serialization as can-execute-code, drain to
                       JSON; UD-03: yaml.load() without Loader= -
                       born-at-zero, SafeLoader taught everywhere;
                       kwarg presence, write-side calls, json.load
                       and danger-marked fences are out by
                       construction, born tick-646, drained same
                       tick: 11 sites across 7 files)
    unsafe_shell_scan  unsafe shell execution in python fences
                       (US-01: subprocess run/call/check_call/
                       check_output/Popen with shell=True - the
                       command string goes to /bin/sh, so
                       metacharacters in interpolated values
                       defeat any name-level allowlist/blocklist;
                       US-02: os.system/os.popen, born-at-zero,
                       7500-security's own scanner regexes name
                       them; US-03: subprocess.getoutput/
                       getstatusoutput - shell=True by
                       construction, born-at-zero; the argv list
                       form (7202's teaching), shell=False and
                       danger-marked fences are out by
                       construction, born tick-647, drained same
                       tick: 2 sites across 2 files)
    broad_except_scan  bare/broad except with a pass-only body in
                       python fences (BE-01: a bare except: whose
                       body is only pass catches KeyboardInterrupt/
                       SystemExit/GeneratorExit too and discards all
                       of them silently - 6304-GraphRAG's own
                       comment teaches this; BE-02: except Exception/
                       BaseException, tuple members included; the
                       corpus-taught narrow forms, handlers whose
                       body does work, string mentions and
                       danger-marked fences are out by construction,
                       born tick-648, drained same tick: 5 sites
                       across 5 files)
    cypher_interp_scan Cypher interpolation into the positions
                       $parameters cannot fill (CI-01: label/
                       rel-type position - the f-string literal
                       before the interpolated value ends with a
                       colon, (n:{label}/[r:{rel_type}] - 6301
                       vouches: values are bound with $parameters,
                       never interpolated into the string; CI-02:
                       variable-length path bound - literal ends
                       with ../*, parameters cannot set those
                       bounds per 6304, so int-cast then
                       interpolate, hop_bound = max(1, int(depth)));
                       the parameterized Constant form, colon+space
                       prompt literals, the LIMIT position,
                       int-cast bounds (6304 x3) and allowlist-
                       guarded labels are out by construction,
                       one-hop query-variable delivery resolved
                       per-function-scope, born tick-649, drained
                       same tick: 5 sites across 2 files)
    mutable_default_scan
                       mutable-default-argument shared state in
                       python fences (MD-01: a mutable literal
                       default - []/ {}/ set literal - is created
                       once at def time and shared across every
                       call, so any mutation writes into every
                       other call's view; MD-02: the same class
                       one step removed, a zero-arg list()/dict()/
                       set() constructor call as the default;
                       dataclasses refuses the exact form at
                       class-creation time - ValueError, use
                       default_factory - and the corpus teaches
                       field(default_factory=...) in 15+ places;
                       the None-sentinel idiom, immutable
                       literals, call-with-args defaults, lambda/
                       comprehension defaults, string mentions
                       and danger-marked fences are out by
                       construction, born tick-650, drained same
                       tick: 7 sites across 7 files)
    open_encoding_scan
                       text-write encoding holes in python
                       fences (OE-01: a builtin open() in text
                       write mode - mode carries w/a/x/+ and
                       never b - without an explicit encoding=
                       kwarg writes through
                       locale.getpreferredencoding(False)
                       (cp1252/cp1254 on Windows, an ASCII-ish
                       locale on CI), so non-ASCII content
                       mojibakes or raises UnicodeEncodeError;
                       OE-02: the same class one step removed,
                       Path.write_text(data) without encoding=;
                       PEP 597 warns, PEP 686 flips the default
                       to UTF-8 only in 3.15; the corpus teaches
                       encoding="utf-8" in 24 places; encoding=
                       with any value, binary modes, read-only
                       opens, non-constant modes, write_bytes,
                       method .open() calls, string mentions and
                       danger-marked fences are out by
                       construction, born tick-651, drained same
                       tick: 31 sites across 16 files)
    http_timeout_scan
                       unbounded HTTP waits in python fences
                       (RT-01: a requests get/post/put/delete/
                       patch/head/options/request call without a
                       timeout= kwarg - requests sets NO default
                       timeout, the socket read blocks
                       indefinitely, so one dead or slow peer
                       hangs the caller forever: a monitor loop
                       that stops monitoring, a web worker that
                       never returns, a batch job stuck mid-
                       flight; RT-02: the same call carrying
                       verify=False - TLS certificate
                       verification disabled, the MITM door
                       opened, born-at-zero owned preemptively
                       per the US-02/US-03 precedent; the corpus
                       teaches timeout= in 30+ places - 5 status
                       pings, 120 LLM inference, 30 general API
                       - yet the same corpus signed 42 bare
                       calls, in one case the vouched 5s form
                       and the bare form of the very same
                       endpoint 9 lines apart; timeout= with any
                       value, httpx (5s default, client-level
                       timeout at the single corpus site), the
                       Session form, other-object .get/.post,
                       string mentions and danger-marked fences
                       are out by construction, born tick-652,
                       drained same tick: 42 sites across 15
                       files)
    sql_interp_scan
                       SQL value interpolation into execution
                       calls in python fences (SQ-01: an f-string
                       carrying SQL text passed to execute/
                       executemany/executescript/read_sql - the
                       interpolated value is merged into the query
                       text client-side, before the driver ever
                       sees it, so no placeholder can bind it: a
                       value containing a quote closes the literal
                       and the rest executes as SQL, direct and
                       via a query variable both fire; SQ-02: the
                       same client-side merge through percent-
                       format, str.format() and concatenation
                       whose fragments carry no %s/? placeholder;
                       the corpus's SQL discipline is 36/36
                       execution calls parameterized - Constant
                       query text, %s/? placeholders plus a
                       params second argument, and the
                       placeholder-carrying builder query +=
                       " AND x <= %s" with params.append, the
                       7402-Agent-Memory idiom; constant queries,
                       the params forms, the builder chain, non-
                       SQL execute calls, string mentions and
                       danger-marked fences are out by
                       construction, born tick-653, zero-drain:
                       the class froze at the rule the moment it
                       was named, the EC-03/fence_lang shape)
    crypto_hygiene_scan
                       security-material crypto hygiene in python
                       fences (CH-01: a randomness producer building
                       security material - random is a Mersenne
                       Twister predictable from observed output, so
                       api_key = random.choice(alphabet), token =
                       random.randbytes(16) or def generate_token()
                       returning getrandbits is forgeable; fires only
                       when the vocabulary attaches AT THE CALL
                       SITE: an enclosing assign target, string-
                       Constant or Name arguments, keyword names or
                       the enclosing def name; CH-02: collision-
                       broken md5/sha1 hashing security material -
                       a hashed password/token can be swapped, not
                       just guessed; the affirmative forms the
                       corpus teaches stay out: secrets.token_hex
                       (TUTORIAL-013-AI-Security) and
                       hashlib.sha256 (the 7500-security phase),
                       non-security randomness (the corpus's 39
                       random.* calls are dropout, sampling and
                       canary rolls) and the 15 md5 dedup/bucketing
                       calls (the corpus's own "BUCKETING, not
                       security" comments) are out by construction,
                       born tick-654, zero-drain, owned preemptively
                       per the US-02/US-03 and RT-02 precedent)
    insecure_temp_scan
                       insecure temp-file creation in python fences
                       (TF-01: tempfile.mktemp - the name exists before
                       the file does, so another process can create the
                       path first or squat it between the call and the
                       write, the TOCTOU race class, Bandit B306; the
                       affirmative atomic forms stay out: mkstemp and
                       NamedTemporaryFile open the fd at creation time
                       and TemporaryDirectory hands out a private
                       directory - the corpus practices mkdtemp x6,
                       NamedTemporaryFile x7 and TemporaryDirectory
                       and never teaches mktemp; TF-02: a string
                       constant starting with /tmp, /var/tmp or
                       /dev/shm passed DIRECTLY to open, os.open,
                       os.mkdir, os.makedirs or os.mknod puts content
                       at a predictable world-writable location on
                       multi-user hosts, Bandit B108's location class
                       - composite literals like tmpfs={"/tmp": ...},
                       list literals like ALLOWED_PATHS and
                       non-creation calls like tf.profiler's
                       /tmp/xla_profile are out by construction, born
                       tick-655, zero-drain, owned preemptively per
                       the US-02/US-03, RT-02 and CH-01 precedent)
    cors_wildcard_scan
                       CORS wildcard origins combined with
                       allow_credentials=True in a CORS call (the
                       Fetch spec forbids the pair: credentialed
                       cross-origin responses must name the actual
                       origin - browsers reject the wildcard, or the
                       middleware reflects it into every-origin
                       credentialed access); attaches on add_middleware
                       whose first argument is the CORSMiddleware
                       class (a bare Name, a constructor Call or a
                       string) or a direct CORSMiddleware call -
                       wildcard alone, credentials with explicit
                       origins, credentials=False and non-constant
                       origins are out by construction, born tick-656,
                       drained in-line the same tick (2 sites, zero
                       line shift), hard from the rule's naming)
    trust_remote_code_scan
                       trust_remote_code=True on any loader call
                       (from_pretrained, from_quantized, vLLM's
                       LLM constructor - the flag downloads and
                       executes the repository's own modeling
                       Python on the local machine at load time;
                       HF guidance is default-False, pinned
                       revision when truly needed); the corpus's
                       10 sites all load stock-code checkpoints
                       (Mistral-7B, Llama-2-7b, the Llama-2 AWQ
                       export, a local GPTQ export, gpt2) whose
                       code ships inside transformers, and the
                       same corpus loads the same models
                       flag-free lines away; the absent kwarg,
                       False, non-constant values, string
                       mentions, danger-marker fences and
                       notebooks are out by construction, born
                       tick-657, drained in-line the same tick
                       (10 sites, zero line shift), hard from
                       the rule's naming)
    async_block_scan
                       blocking calls inside async def bodies in
                       python fences (AB-01: a blocking requests
                       verb call runs the whole HTTP round-trip
                       on the event-loop thread and freezes every
                       other coroutine - wrap with await
                       asyncio.to_thread(...) or use a native
                       async client; AB-02: time.sleep parks the
                       loop's thread - await asyncio.sleep(...);
                       sync def bodies, the affirmative
                       to_thread/sleep forms, non-verb attributes,
                       nested-scope attribution, string mentions,
                       danger-marker fences and notebooks are out
                       by construction, born tick-658, drained
                       in-line the same tick (13 sites), hard
                       from birth)
    unawaited_coro_scan
                       a bare-Name call to a fence-local async def
                       standing alone as a full statement discards
                       the coroutine object - the work never runs,
                       only a RuntimeWarning whispers; the corpus
                       teaches every consumed form itself (await,
                       gather over comprehensions and
                       generator-expressions, async for,
                       StreamingResponse generators, asyncio.run
                       entry points); consumed
                       argument/comprehension/assign positions,
                       sync-only names, shadowed sync+async names,
                       string mentions, danger-marker fences and
                       notebooks are out by construction, born
                       tick-659 at zero across 1861 fences / 197
                       async defs, hard from birth)
    bare_except_scan
                       a bare ``except:`` handler catches
                       BaseException - KeyboardInterrupt,
                       SystemExit and asyncio.CancelledError are
                       swallowed (Ctrl+C dies silently, task
                       cancellation no-ops), PEP 8 names it too
                       broad; the corpus teaches the bounded forms
                       itself (except Exception x124, specific
                       types x65 of 206 handlers); every typed
                       handler (Name / Attribute / Tuple /
                       Subscript / Call), except* ExceptionGroups,
                       pass-only bodies (broad_except BE-01's
                       slice, disjoint by body shape), string
                       mentions, danger-marker fences,
                       non-python fences and notebooks are out
                       by construction, born tick-660 at
                       exactly 17
                       bare handlers across 12 files, drained
                       in-line the same tick (except: ->
                       except Exception:, zero line shift), hard
                       from birth)
    secret_shape_scan
                       a credentialed-shaped string literal in a
                       python fence (SS-01: provider key shapes -
                       sk- + 20+ OpenAI/Anthropic, ghp_/gho_/ghu_/
                       ghs_/ghr_ + 30+ and github_pat_ + 22+
                       GitHub, AKIA + 16 AWS, AIza + 35 Google,
                       xox* Slack) is either a leaked real
                       credential or a reader template that looks
                       exactly like one - the repo is publish-bound
                       and GitHub secret scanning flags these
                       shapes on push; the affirmative form is the
                       corpus's own env-var idiom (os.environ /
                       os.getenv), placeholder literals cannot
                       satisfy the prefix+tail demands by
                       construction, the word-boundary anchor keeps
                       task-specific-style strings silent, env
                       reads, danger-marker fences, non-python
                       fences and notebooks are out by
                       construction, born tick-664 at zero across
                       1861 fences, hard from birth)
    md_link_leak_scan
                       markdown link syntax inside a quoted string
                       (ML-01: a quote-delimited string whose entire
                       visible content is one markdown link is not a
                       URL - it is link syntax leaked into a string
                       literal, almost always a fence's URL value;
                       no gate owned the class - fences compile as
                       string constants, the AST family reads calls
                       and kwargs not string contents, and linkcheck
                       counted the shapes as valid self-resolving
                       links), fence-agnostic by design (the corpus
                       nests inner example-fences whose parity flip
                       blinds fence-walking gates exactly where the
                       drain lived - UC-002's OAuth example), born
                       tick-675 at exactly 3 findings, drained the
                       same tick before the gate landed (wrappers
                       stripped, zero line shift), hard from birth
    action_version_scan
                       uses: pins in docs must match the canonical
                       action registry (AV-01: current majors -
                       checkout@v7, setup-uv@v9, cache@v4,
                       codecov@v5, buildx/login@v3, metadata@v5,
                       build-push@v6, artifact@v7/v8); comment-only
                       mentions are not findings; born tick-368,
                       baseline 0
    unicode_ws_hygiene_scan
                       invisible/control characters (UW-01: ZWSP/
                       NBSP/mid-file BOM etc - copy-paste debris,
                       runtime poison inside code fences), real
                       trailing whitespace (UW-02; the corpus uses
                       no hard-break double spaces) and mixed line
                       endings per file (UW-03); CR-normalized;
                       born tick-371, baseline 0
    kwarg_lint         calls with removed/renamed kwargs on known APIs
                       (KW-01 langchain constructor kwargs, KW-02 removed
                       qdrant .search kwargs, KW-03 removed qdrant
                       .search_batch methods in qdrant-importing docs,
                       locally defined shadows respected) - hard gate
                       since the query_points migration drained
                       (tick-220); KW-03 born from the tick-324
                       blind-spot note, drained at tick-326
    typing_legacy_scan legacy typing spellings in python fences (TL-01:
                       Optional[ Union[ List[ Dict[ Tuple[ Set[
                       FrozenSet[ Type[) - hard gate since the PEP
                       585/604 modernization epic drained (typing /3);
                       TL-02 legacy import lines / TL-03 bare legacy
                       generics born tick-376 as report queues (census
                       139 / 426 - the /1-/3 fixer's bracket pattern
                       missed both); 4-backtick super-fence teaching
                       content is invisible to the fence model by
                       design
    version_alignment_scan
                       code-side python-version drift in ANY fence
                       (VA-01 FROM python:X.Y, VA-02 python3.X
                       binaries, VA-03 --python X.Y flags, VA-04
                       uv python install/pin X.Y): everything must
                       be the corpus standard 3.13 - born from the
                       tick-257 census that found one production
                       Dockerfile on python3.10 after the 3.13
                       epic was declared done
    feed_parity_check  cross-feed contract between the platform feeds:
                       runs manifest_export + quiz_export +
                       curriculum_metrics for real and locks their
                       invariants (FP-00..FP-10: module sets, counts
                       vs arrays, hierarchy vs documents lessons,
                       quiz-file membership, bank-internal totals,
                       assessment.quiz flags, manifest vs the on-disk
                       docs/*.md tree, experiments vs the
                       experiments/*.md tree minus TEMPLATE.md,
                       curriculum corpus vs the hierarchy, metrics
                       quiz total vs the bank) - consistency only,
                       content totals stay the living baseline.
                       Scope tick-613: the feed learned the second
                       tree (manifest_export now carries
                       experiments[] on the 5-field EC-01 keyset)
                       and FP-08 lifts FP-07's zeroth platform
                       contract to it, pure path-set parity both
                       ways - born at 47 == 47. Scope tick-614: the
                       third feed joined - curriculum_metrics runs
                       for real and FP-09/FP-10 lock its corpus
                       counts and quiz total to the hierarchy and
                       the bank - born at 114/33/7 and 660 == 660.
    readme_claims_check
                       every measurable number in README.md (badges,
                       resource tables, per-phase document table,
                       footer) vs its disk measurement (RC-01; RC-00
                       missing README/failed borrow) - born from two
                       consecutive drift waves (tick-260 "463 files",
                       tick-261 experiments/labs/phase-table)
    sitemap_claims_check
                       every measurable number in SITEMAP.md: section
                       headers vs disk, headers vs their own list
                       entries, and the fenced Statistics block
                       (SC-01; SC-00 missing SITEMAP/failed measure)
                       - SITEMAP called itself "derived from the file
                       tree" while its Statistics block had rotted
                       (tick-262: 458/407/1 vs measured 462/408/4)
    meta_claims_check
                       every measurable number in the remaining entry
                       docs: FAQ.md intro sentence, MASTER-INDEX.md
                       (Total Files line, per-phase Status rows,
                       numbered section headers, lab header 3-way
                       split, File Counts block incl. TOTAL as its
                       own sum, module-table "N docs" cells = lesson
                       files), ORGANIZATION-GUIDE.md tree labels,
                       VOLUME-GUIDE.md (tree labels, labs 2-way
                       split, SITEMAP line, Total Documents footer)
                       and PROGRESS-TRACKER.md (per-volume bars +
                       headers, Total bar, SITEMAP line, stats-table
                       targets; bar percent/fill are learner state,
                       only targets are locked)
                       (MC-01; MC-00 missing file/failed measure) -
                       born while these docs still said 462/463
                       documents, 427 total files and 256 "Module
                       Documents" (tick-263; VOLUME-GUIDE joined in
                       tick-264 while it still said "85 files across
                       7 volumes"; PROGRESS-TRACKER joined in
                       tick-265 while it still targeted "0/97 core
                       files")
    volume_checklist_scan
                       every checklist item in the seven VOLUME-*.md
                       Core/Advanced sections must resolve to a real
                       corpus file (VC-01: "NNNN:"/"TUTORIAL-NNN:"/
                       "LAB-NNN:"/"EXP_NNNN:" IDs; Project A/B/C and
                       prose goals are curricular choices, skipped)
                       with a title that matches what the file is
                       (VC-02: zero keyword overlap vs filename
                       suffix OR front-matter Title - filenames can
                       lag, e.g. 7301-Orchestration.md is titled
                       "Collaborative Tasking"); a dead or mislabeled
                       checklist entry is a learner-facing platform
                       bug - born tick-455 from the three mislabeled
                       V7 items found in tick-454, baseline 0 (81
                       items parsed)
    lab_registry_check every `LAB-0NN: Topic` label corpus-wide vs the
                       labs' own frontmatter Titles (LB-01 wrong lab
                       identity - the topic belongs to a different lab
                       than the one labelled; LB-02 unknown/ambiguous
                       topic - teach the signal table or fix the label;
                       LR-01 lab id with no file on disk). Labels carry
                       identities, not numbers, so the claims gates
                       cannot see this class - born from the tick-267
                       census (301 labels) that found DPO Alignment
                       credited to LAB-005 twice and "Custom
                       Quantization" invented for LAB-004 three times
    resource_id_check  numbered-resource id identity across the 43
                       resources (LAB-000..014, PROJECT-001..007,
                       TUTORIAL-000..014, CHEAT-SHEET-001..006): every
                       resource's frontmatter Title and first H1 must
                       carry the filename's own `FAMILY-0NN:` id, and
                       the pre-campaign spaced spellings ("LAB 007",
                       "CHEAT SHEET 004", any case) are banned
                       corpus-wide - born from the tick-268..271
                       canonicalization campaign; lab_registry_check
                       locks what each id points at, this gate locks
                       the id itself
    resource_ref_check cross-document references to the 43 resources
                       (RR-01 out-of-range id: "see LAB-016" with no
                       LAB-016 on disk) - a dead pointer in plain
                       prose that linkcheck cannot see because it is
                       not a relative link href; the valid id set is
                       derived from the same disk glob
                       resource_id_check uses; lowercase matches
                       (lab-001) are out of scope by design - the
                       birth census (tick-327: 1316 uppercase
                       references, 0 out of range; 101 lowercase,
                       all filesystem-path idioms) locked baseline 0
                       at birth
    fence_variant_check undefined lexical variants inside ```python
                       fences (PY-01): a bare name loaded but defined
                       nowhere (scope chain, fence module, same doc,
                       builtins) that is a near-miss of an in-scope
                       name - vocab_size vs vocab, range(epochs) vs
                       the epoch loop var, calculate vs
                       calculator_function; lambda/nested bodies
                       resolve against the enclosing chain, two
                       ambient names + CP-001's placeholder-suffix
                       idiom are allowlisted with reasons; the birth
                       census (tick-330/331: 1857 fences, 7 survivors
                       -> 5 drained, 2 FP classes absorbed by design)
                       locked baseline 0
    fence_variant_check_module module-level lexical variants in
                       ```python fences (PY-02): PY-01 v1's declared
                       out-of-scope region - a bare name loaded at
                       module level (outside any function/class body)
                       that is a near-miss of an in-scope name, same
                       predicate; the region is fragment-densest (296
                       distinct bare non-variant names accepted by
                       design) so only the variant class is locked;
                       birth census (tick-332: 35 hits; tick-333
                       drain 13 across 7 docs + 1 reclassified FP)
                       left 16 hits in 6 recorded FP classes - ambient
                       import classes, wrong/right placeholders, QKV
                       notation, documented __main__ fragment,
                       loop-sibling shape, placeholder pipeline
                       functions - each a reasoned (rel, name) accept;
                       locked baseline 0 at birth
    bash_vars_check     undefined shell variables in ```bash fences
                       (BB-02): the shell counterpart of PY-01 - a
                       plain $VAR or bare-braced ${VAR} load stored
                       nowhere (fence, same doc, builtins, systemd
                       Environment= directives, os-release keys after
                       a source) is reported; guarded ${VAR:-def}
                       idiom tolerates absence by design, and
                       template placeholders plus nginx runtime
                       variables in bash-labeled nginx fragments are
                       absorbed as reasoned (rel, name) accepts; born
                       from the tick-335/336 census (697 fences, 22
                       plain -> 38 with braced loads, 5 drained)
                       locked baseline 0 at birth
    uv_install_check    plain 'pip install' bypassing the uv
                       standard (UV-01) inside bash/sh/shell/
                       dockerfile fences; lines using the uv
                       interface (uv pip install) are never
                       reported; reasoned (rel, exact-line)
                       accepts cover the documented fallback,
                       conda, antiexample, bootstrap and notebooks
                       classes; born from the tick-337 census
                       (715 fences, 145 pip-family lines, 30
                       plain) locked baseline 0 at birth
    uv_workflow_census  uv project-workflow adoption census
                       (report): per-subcommand occurrence
                       counts inside bash/sh/shell/dockerfile/
                       powershell fences plus per-doc mention
                       counts of pyproject.toml, uv.lock and
                       requirements.txt; born from the tick-339
                       census - the corpus was fluent in the
                       imperative layer (uv pip install 135)
                       but silent on the declarative standard
                       (uv init/add/sync/run at 0, uv.lock in
                       0 docs) until ENVIRONMENT-SETUP taught
                       the pyproject.toml + uv.lock workflow;
                       numbers are expected to move as the
                       declarative standard spreads - exit 0
                       by design
    fence_label_census fence-label accuracy census (report,
                       FLC-01): a raw Dockerfile or nginx config
                       pasted into a bash/sh/shell fence is a
                       mislabel (>= 4 Dockerfile directives or
                       >= 2 nginx markers with no shell tokens);
                       heredoc-wrapped generation (cat > ...
                       << 'EOF') is the correct shell idiom and
                       only counted as embedded; born from the
                       tick-341 sweep that closed both backlog
                       relabel items as verified-clean - 699
                       shell fences, 0 raw / 0 raw, 3 + 4
                       embedded, 12 nginx + 18 dockerfile
                       fences already correct; a future raw
                       paste surfaces here - exit 0 by design
    term_consistency_scan brand-term consistency (both HARD): one
                       canonical spelling per brand in prose - bare
                       "HuggingFace" tokens (identifier continuations
                       like HuggingFaceEmbeddings/H4/TB excluded by
                       the predicate) and prose-lowercase "ollama"
                       (fences, inline code, frontmatter tag
                       vocabulary and quoted terminal-error spans
                       legal by predicate); born from the tick-400
                       ad-hoc sweep that found the corpus 55/45
                       split (66 bare HuggingFace vs 54 "Hugging
                       Face"; TensorFlow/LangChain/PyTorch/OpenAI
                       already consistent at 0); drained tick-401,
                       TC-01 promoted to hard then; TC-02 went hard
                       2026-09-30 when its four report rows all
                       proved legal literals - they moved into the
                       predicate, zero doc edits
    front_matter_census front-matter integrity (FM-01..FM-06,
                       hard): every doc needs a complete,
                       terminated YAML front-matter block;
                       Difficulty within {Beginner, Intermediate,
                       Advanced, Expert}; Status within {Complete,
                       In Progress, Draft}; Last Updated
                       YYYY-MM-DD and never a future date; declared
                       Phase/Module matching the docs/phases/ path.
                       Born tick-402 measuring 0 across 408 docs in
                       every class, promoted same tick (KW-03
                       pattern) - new enum values must update the
                       script in the same commit
    tag_vocabulary_census tags vocabulary closure (TV-01..03
                       hard): platform filtering and
                       related-content navigation need a closed,
                       single-form tag vocabulary. WHITELIST frozen
                       at tick-403 birth (111 docs, 216 tags, 0
                       dups, 0 case clashes); TV-01 unknown tag
                       (new tags are deliberate WHITELIST edits in
                       the same commit), TV-02 duplicate tag within
                       one doc, TV-03 known variant form naming the
                       canonical spelling; 7 variant sites drained
                       tick-404, vocabulary now 209 single-form
                       tags, TV-03 hard since the drain
    related_census Related-field link integrity (RL-01..03, hard):
                       cross-reference navigation rides on the
                       front-matter Related field; RL-01 dangling
                       token (no file), RL-02 ambiguous token
                       (multiple files), RL-03 machine-parseable
                       value not in canonical bracketed-list form
                       (Tags-style). Born tick-405 measuring
                       110 docs / 35 tokens, all resolving exactly
                       one file - hard from birth (KW-03); 2 bare
                       lists drained to bracketed tick-406, linked
                       shape now closed (11 bracketed, free-text
                       "See module README"/"See References" allowed
                       as authoring-stage pointer)
    estimated_time_census Estimated Time parseability (ET-01..03,
                       hard): the platform uses Estimated Time for
                       scheduling math, so every value must parse
                       and the field name must be exact. ET-01
                       unparseable value, ET-02 field-name variant
                       (exact name is "Estimated Time:") - both
                       hard from birth, measured 0 across 111 docs
                       at tick-407 (KW-03). ET-03 range values
                       ("6-8 hours") - 6 sites drained tick-408 to
                       single durations (midpoint half-up, integer
                       hours), hard since the drain; dual-mode
                       "quick/full review" entries are a legal
                       shape, both durations parse
    prereq_census Prerequisites chain integrity (PQ-01..03 +
                       PQ-06..08, hard):
                       prerequisites are the learning-path
                       backbone - a dangling prerequisite is a
                       lesson that can never be unlocked. PQ-01
                       dangling machine-parseable token, PQ-02
                       ambiguous token - both hard from birth,
                       measured 0 across 108 docs / 7 tokens at
                       tick-409 (KW-03). PQ-03 machine-parseable
                       value not in canonical bracketed bare-token
                       list form - 5 sites drained tick-410 (3
                       titled brackets stripped, 2 bare lists
                       bracketed), hard since the drain; free-text
                       and prose entries remain allowed as
                       authoring-stage pointers. PQ-06 (born
                       tick-574 at zero) the machine-parseable
                       Prerequisites subgraph must be ACYCLIC
                       (Tarjan SCC) - on the platform a prereq
                       cycle is an unlock deadlock, neither side
                       ever satisfiable; the live graph is 8
                       machine-parseable docs / 12 tokens / 12
                       edges, every edge forward in the lesson
                       order, and the shared-dependency diamond
                       (1103 requiring 1101+1102) is a legal DAG
                       that must stay legal; edges come only
                       from the gate's own shapes - prose and
                       the tolerated [PHASE-N] brackets carry
                       none; Related's one sibling cycle
                       (1101->1102->1103->1101) is navigation,
                       printed, never gated; PO-01/02 own the
                       spine-local half, PQ-06 is the
                       numbering-free whole-graph half covering
                       the LAB-/TUTORIAL- edges PO excludes.
                       PQ-07 (born tick-575 at zero) difficulty
                       never climbs the unlock path: on every
                       PQ-06 edge where both endpoints carry a
                       canonical FM Difficulty (Beginner=1 /
                       Intermediate=2 / Advanced=3, the
                       TIER_STARS map footer_fm_parity proved)
                       the prerequisite's tier must be <= the
                       doc's own tier - equal-tier and downhill
                       edges are legal pedagogy (the live 12
                       edges: 6 equal-tier, 6 downhill), an
                       uphill edge is a lesson demanding harder
                       material than itself, wrong opening
                       order; out-of-vocabulary Difficulty skips
                       the comparison (FV-07 owns the enum).
                       PQ-08 (born tick-607 at zero) the
                       pointer contract: a doc whose
                       Prerequisites defers 'See module
                       README' requires that module README to
                       carry a canonical machine-parseable
                       Prerequisites field - the indirection
                       exists so the README is the module's
                       single source of prereq truth, and 177
                       docs (111 lessons + 66 assessments)
                       resolved it to nothing machine-parseable
                       until the drain transcribed each
                       module's own PREREQUISITES.md
                       cross-module declarations into the
                       README FM (module-granularity
                       normalization: a Review/Read bullet
                       naming another module's lesson
                       normalizes to that lesson's module) -
                       33/33 READMEs now carry the canonical
                       field, `[]` is the canonical 'no
                       prerequisites, unlock immediately'
                       (honestly reclassifying
                       TUTORIAL-000/002 from prose to
                       canonical: 43 canonical / 8 prose), 9
                       modules with dependencies / 10
                       module-level edges (2200->[2100],
                       2300->[2200], 2400->[2200],
                       3100->[3200] the one forward edge -
                       advanced attention reviews the
                       embeddings module's RoPE lesson, legal
                       downhill under PQ-07 - 4100->[1500],
                       4300->[4100], 4400->[4100, 4300],
                       5100->[4100], 5400->[5300]; every
                       remaining module `[]`, 5500's 'see
                       5400 if scaling is your bottleneck'
                       left out honestly as conditional
                       advice, not a prerequisite); PQ-08
                       fires per offending README, aggregating
                       the pointer docs that defer to it, and
                       a pointer doc with no resolvable module
                       dir fires its own finding; the token
                       index resolves a bare 4-digit module
                       token to its module README (0 filename
                       collisions across the 33 codes,
                       measured before the extension); the
                       README field's presence+canonicity is
                       PQ-08's, its keyset allowance
                       course_card_check CC-17's
                       (README_KEYSET widened tick-607)
    prereq_ordering_scan
                      Learning-path order integrity (PO-01/02,
                      hard, born at zero): corpus numbering is
                      monotonic along the curriculum, so "earlier
                      on the path" is exactly "smaller 4-digit
                      number" - PO-01 forward reference (prereq
                      token greater than the referrer's own
                      number) is an unlock deadlock on the
                      platform, PO-02 self reference. No
                      false-positive class exists; birth census
                      2026-09-30 measured the whole
                      machine-parseable surface clean (95 numbered
                      docs, 4 tokens, 13 non-numbered docs are
                      free-text/resource pointers, visible in the
                      skip line)
    qa_tooling_coverage_check
                      QA-TOOLING doc locked to this inventory
                      (QT-01, hard, born at zero): every script
                      in GATES must be named in
                      docs/00-META/QA-TOOLING.md by script stem
                      or gate label - the hand-written doc cannot
                      silently drift behind the CI contract again
                      (birth census 2026-09-30: 22 of 59 gates
                      unlisted; 1 matcher FP, 21 rows drained
                      same tick, hard since). Presence only -
                      the prose stays hand-written
    pacing_consistency_census
                      Estimated Time vs real reading load (PC-01,
                      report-only census): claimed hours against
                      lesson_stats words/code at 200/100 wpm,
                      ratio distribution per doc; birth census
                      2026-09-30 measured 111 docs, median ratio
                      4.50 (p10 2.51, p90 8.87) - the labels carry
                      a hands-on-budget, not reading-time,
                      semantics corpus-wide, so the naive 2x band
                      flags 107/111 and hardening is deferred
                      until the platform picks the semantics
    prereq_free_text_check
                      Prerequisites free-text vocabulary closure
                      (PQ-04, hard): every non-token value must be
                      exactly one of the two role-canonical
                      strings - lessons "See module README",
                      module READMEs "See PREREQUISITES.md" - so
                      the platform nav generator can classify
                      every pointer; born 2026-09-30 at 4 prose
                      variants (a vague assumption + three
                      "Phase N completion" statements redundant
                      with spine position), drained same tick,
                      hard since; bracketed resource tokens stay
                      PQ-01..02 territory
    prereq_target_check
                      Canonical pointer target integrity (PQ-05,
                      hard): every "See module README" / "See
                      PREREQUISITES.md" pointer must land - the
                      nearest README-bearing ancestor's README
                      exists and carries a prerequisites section,
                      the PREREQUISITES.md exists; born at zero
                      (census 2026-09-30: 33/33 module READMEs)
    nav_coverage_check
                      Module README navigation coverage (NV-01,
                      hard): every learner-facing doc in a module
                      - root lessons, guides/, assessment/ - must
                      be filename-linked from its module README;
                      a lesson the README never links is invisible
                      to the platform nav no matter how good the
                      content. linkcheck proves that links which
                      exist resolve; NV-01 proves nothing
                      learner-facing is unlinked. Born 2026-09-30
                      at 45 orphans over 17 module READMEs (30
                      prose-described but unlinked lessons, 6
                      never mentioned, 9 assessments without
                      Location lines), drained same tick, hard
                      since. NV-02 (hard since the same-tick
                      drain): the 7 phase-level CHECKPOINT.md
                      files must be filename-linked from their
                      phase READMEs - born unlinked, drained by
                      adding a checkpoint bullet to each phase
                      README's Assessment section (the drain also
                      fixed the "Phase s Practice" typo in the
                      phase-2/3 READMEs)
    last_updated_check
                      Last Updated parseability (LU-01/LU-02,
                      hard): every doc's Last Updated frontmatter
                      date must be present and ISO YYYY-MM-DD -
                      the platform's freshness display and
                      recently-updated sorting need a machine-
                      parseable value; prose or locale variants
                      sort wrong or not at all. Born at zero
                      (census 2026-09-30: 408/408 docs carry the
                      field, all ISO-parseable, zero variants)
    lesson_order_check
                      Module README lesson order (LO-01, hard):
                      the first-occurrence order of lesson links
                      in a module README must be strictly
                      increasing - the platform renders nav in
                      document order, so README order IS the
                      learning path, and IDs encode the intended
                      sequence. First occurrence only: phase-1/2
                      READMEs legitimately repeat the full list
                      in a tail summary. Guides/assessments are
                      genre extras, positions free. Born 2026-09-
                      30 at 5 stray bullets (5103/5203/5204/6203/
                      7403, appended by the nav drain before the
                      first lesson header), drained same tick by
                      relocating each after its ID-sorted block,
                      hard since
    toc_coverage_check
                      TOC completeness (TC-01, hard): in a TOC-
                      carrying doc every real content H2 (outside
                      frontmatter/fences, closing trio exempt)
                      must appear as a TOC bullet - text match OR
                      href-slug match (a "Part 1:" prefix or
                      stripped emoji in the label is house style,
                      the nav pane needs the link, not the label).
                      The TOC becomes the platform's in-doc nav
                      pane, so an unlisted section is invisible in
                      navigation. Fence-aware: a naive census saw
                      2 "missing" H2s in 2301 that were literal
                      text inside a python example block. Born
                      2026-09-30 whole-corpus (141 TOC-carrying
                      docs): 45 birth rows = 24 label mismatches
                      (resolved by the slug rule, zero edits) + 21
                      gaps (19 phase-README tail sections, 2 guide
                      Abstracts - drained), hard since
    render_hygiene_check
                      Render hygiene (RH-01..04, hard): no raw HTML
                      outside code (most platform renderers sanitize
                      or escape it - GitHub's collapsible <details>
                      renders as literal text elsewhere), no
                      heading-level skips (platform TOC trees hang
                      off the hierarchy), no bare URLs outside
                      links/code (unwrapped URLs render as plain
                      text - not clickable), no empty image alt
                      text. Born 2026-09-30: 12 raw-HTML tags (3
                      <details> Solution blocks in TUTORIAL-000,
                      drained to bold labels) + 46 bare URLs over 16
                      docs (drained to [url](url) self-links);
                      skips/alts born zero
    status_vocab_check
                      Status vocabulary (SV-01, hard): the FM Status
                      field must be from the closed vocab
                      {"Complete"} - a free-text status degrades
                      into variants that filter wrong or not at all
                      (same argument that closed Difficulty).
                      Extending the vocab is a deliberate edit to
                      the script, not a doc-level choice. Born
                      2026-09-30 at 408/408 'Complete', zero
                      variants
    tags_coverage_check
                      Tags coverage (TG-01 hard, TG-02/03 report):
                      a numbered in-phase lesson outside guides/
                      with no Tags field is invisible to the
                      platform tag filter and related-content
                      navigation; born 2026-09-30 at 0 after the
                      6-lesson drain (5103/5203/5204/6203/7302/
                      7403, all 5-key-minimum docs) - 93/93 carry
                      Tags. TG-02 keeps the guides/ genre's split
                      inventory visible (9/21 tagged) and TG-03
                      the meta docs' phase2-revamp trail (10/146
                      tagged) until a tag-all-or-none standard is
                      decided
    front_matter_scan
                      Front-matter presence + standard fields
                      (FS-01/02, hard): closes the coverage
                      gates' blind spot - a doc committed
                      WITHOUT front matter is invisible to
                      TG/TS/TV (fm_tags None -> skip), so
                      presence itself is the contract. FS-01
                      closed FM block in the first 40 lines,
                      FS-02 all six standard fields (Document
                      ID / Title / Last Updated / Status /
                      Difficulty / Tags) - field-NAME variants
                      pass the value gates of the canonical
                      name and die here. Born tick-457 at
                      408/408, KW-03 pattern
    difficulty_badge_scan
                      Badge parity (BD-01, hard,
                      renamed from DB-01 at tick-577
                      - the DB- namespace belongs to
                      datablock_syntax_scan): where a doc
                      renders a `**Difficulty:**` body badge it
                      must mirror the FM Difficulty exactly -
                      canonical 1/2/3 stars + the FM band; no
                      badge is fine (FM is the data). Born
                      tick-457: 87 sites drained across five
                      rot classes (dead-enum 4-5 star 'Expert'
                      badges from the retired level, band
                      mismatches where mass-added FM defaults
                      contradicted badge intent, starless
                      badges, phase-hub range badges,
                      'Absolute Beginner')
    course_card_check
                      Course-card parity (CC-01..33, hard):
                      a module README's front-matter
                      Difficulty is the course card a
                      platform catalog reads and the
                      Module Documents table some READMEs
                      render is the per-lesson display
                      layer. CC-01 the card equals the max
                      tier of the module's lessons (the
                      FF-02 star map; lessons = module-dir
                      *.md minus README minus
                      PREREQUISITES), CC-02/03 the table's
                      star and time cells mirror each
                      target's FM tier and Estimated Time
                      minute-exact (header-conditional
                      emptiness, the LI-05 class), CC-04
                      every lesson linked somewhere in the
                      README, CC-05 every lesson has a row
                      where the table exists. Born tick-576
                      at 35 findings: 22 of 33 cards floated
                      free of their lessons since the
                      775f898 boilerplate migration (a 3100
                      card reading Beginner over Advanced
                      lessons), 10 star cells and 2 time
                      cells drifted, 7300 omitted 7302, 2
                      body badges mirrored the drift; the
                      drain obeys the 11 curated cards
                      already satisfying CC-01. CC-06 the
                      card's FM Estimated Time exists
                      (presence - the platform catalog
                      reads one time budget per course)
                      and equals the ceil of its lessons'
                      FM ET sum to the whole hour (the
                      LI-06 parts-sum arithmetic at
                      course scope; an unparseable card
                      value fires, equality computed only
                      when every lesson parses). Born
                      tick-578: 29 of 33 cards carried no
                      FM ET and the 4 boilerplate
                      carriers (2100/2200/2300/2400 at
                      12/18/28/37 hours) overshot every
                      computable source - the drain wrote
                      the ceil lesson sum into all 33
                      cards, 29 insertions plus 4
                      corrections. CC-07 every lesson
                      carries a parseable FM Estimated
                      Time ('N hours' or 'N minutes' - the
                      budget the platform renders per
                      lesson) so CC-06's equality
                      precondition is an invariant instead
                      of a silent skip; the gap itself is
                      the finding, listed per module.
                      Born tick-579 as a zero-drain lock
                      in the PQ-06 shape: 93/93 module
                      lessons clean, stripped lines and
                      range forms fire exactly once with
                      CC-06 kept silent. CC-08 every
                      module dir is linked from its
                      phase README (any link form,
                      fence-aware) - the CC-04
                      invariant one level up: phase
                      pages are the platform's course
                      browse list, so a module absent
                      there is invisible above its
                      own index. Born tick-580 as the
                      second zero-drain lock in the
                      same shape: 7/7 phase READMEs
                      covering all 33 module dirs
                      clean, killed targets and
                      fence-wrapped lines fire
                      exactly once with CC-01..07
                      kept silent

                      CC-09 born tick-581 at zero: a
                      phase README's module links
                      must first appear in ascending
                      curriculum order (browse order
                      is unlock order), 7/7 phase
                      pages clean - an out-of-order
                      module link pair fires exactly
                      once with CC-01..08 kept
                      silent. CC-10 born tick-581
                      after a one-line drain: every
                      module's PREREQUISITES.md must
                      carry at least one internal
                      course link (a target ending
                      .md), 3500-multimodal's entry
                      page being the lone dead end of
                      33 - de-linking or
                      fence-wrapping the only exit
                      link fires exactly once.
                      CC-11 born tick-582 at zero -
                      the third zero-drain lock in
                      the PQ-06/CC-08/CC-09 shape: a
                      module README's lesson links
                      must first appear in ascending
                      order (the course card's lesson
                      order is the unlock order,
                      CC-09 one level down), census
                      93/93 lesson links across the
                      33 module READMEs clean - an
                      out-of-order lesson link pair
                      fires exactly once with
                      CC-01..10 kept silent.
                      CC-12 born tick-583 at zero -
                      the fourth zero-drain lock in
                      the PQ-06/CC-08/CC-09/CC-11
                      shape: a module README must
                      link its own PREREQUISITES.md
                      (the card a platform renders
                      must offer the learner its
                      entry door, the CC-10 invariant
                      mirrored inward), census 58
                      door links across the 33 module
                      READMEs, every one the plain
                      './PREREQUISITES.md' form - a
                      de-linked door fires exactly
                      once with CC-01..11 kept
                      silent. CC-13 born the same
                      tick at zero: where a
                      PREREQUISITES.md carries an
                      If-YES proceed line the line
                      must carry an internal course
                      link landing inside its own
                      module (24 of 33 carry one, all
                      landing home; the 9 shipping
                      none and the 26-of-119 /
                      179-of-534 links that
                      legitimately cross modules
                      stayed unlocked by honest
                      census) - a link-less or
                      module-exiting proceed line
                      fires exactly once with CC-10
                      kept silent. CC-14 born
                      tick-584 as the family's
                      first multi-file drift since
                      576: a phase README's FM
                      Difficulty equals the max
                      tier of its module cards
                      (the CC-01 invariant one
                      level up - the phase header
                      is the course group a
                      platform filters and badges
                      by, so a group containing
                      an advanced course filters
                      as advanced; computed only
                      when every module card
                      carries an in-vocabulary
                      tier, FS owns the missing
                      name and FV-07 the stray
                      value - never
                      double-reported), census 4
                      of 7 phase headers already
                      at their modules' max tier
                      while phase1-infra,
                      phase2-foundations and
                      phase6-rag sat a level low
                      (Intermediate headers over
                      Advanced-containing course
                      groups, revamp-zone
                      residue from modules that
                      arrived advanced) - the
                      drain bumped exactly those
                      3 FM lines to Advanced,
                      a coupled second drain
                      bumping the same 3
                      headers' body badges to
                      the canonical Advanced
                      form under the BD-01
                      badge-mirrors-FM rule
                      (103/103 canonical
                      after); a header
                      downgrade fires exactly
                      once with CC-01..13
                      kept silent. CC-15 born
                      tick-585 as the family's
                      largest drift since 576:
                      a module's
                      PREREQUISITES.md FM
                      Difficulty equals its
                      course card's (README.md)
                      FM Difficulty - the entry
                      door must not contradict
                      the card the platform
                      renders beside it (one
                      tier per course mirrored
                      on every surface:
                      lessons take the max via
                      CC-01, the phase header
                      the group max via CC-14,
                      the entry page the
                      card's own; computed
                      only when both pages
                      carry an in-vocabulary
                      tier, FS owns the
                      missing name and FV-07
                      the stray value - never
                      double-reported), census
                      23 of 33 entry pages
                      already mirroring their
                      card while 10
                      contradicted it in two
                      directions (5 prereq
                      tiers below the card, 5
                      above - hand-written
                      rot, not a systematic
                      bias) - the drain set
                      each page's FM
                      Difficulty to its card's
                      (5 bumps up, 5 down)
                      and coupled 6100-vector's
                      body badge - the lone
                      entry-page badge still
                      mirroring its old FM -
                      to the canonical
                      Intermediate form (the
                      tick-584 BD-01 coupling
                      pre-censused this time
                      instead of caught by
                      the fleet); a flipped
                      prereq tier fires
                      exactly once with
                      CC-01..14 kept
                      silent. CC-16 the
                      entry page's FM
                      carries only the
                      6-field keyset
                      (Document ID, Title,
                      Last Updated, Status,
                      Difficulty, Tags) -
                      one schema for 33
                      entry pages, so a
                      platform parser reads
                      every entry door the
                      same way (negative
                      excess only: FS owns
                      field presence, this
                      clause owns field
                      excess - never
                      double-reported).
                      Born tick-586 after
                      a 20-line drain:
                      the census read 29
                      of 33 entry pages
                      already on the
                      minimal keyset while
                      the 4 phase2 pages
                      carried 5 legacy
                      extras (Module,
                      Phase, Prerequisites,
                      Related, Estimated
                      Time - a review-range
                      ET and
                      self-referential
                      'See module README'
                      prose) and the
                      impact probe moved
                      only prereq_census's
                      statement counters
                      (docs 204->200,
                      free-text 186->182)
                      with tokens, edges
                      and tier-edges
                      untouched; an extra
                      FM field on a prereq
                      page fires exactly
                      once with CC-01..15
                      kept silent, the
                      same field on the
                      card fires 0 (the
                      rule is entry-page
                      scoped), and two
                      pages aggregate into
                      exactly 2 CC-16.
                      CC-17 the mirror on the card surface: a course
                      card's FM carries only the 7-field card keyset
                      (the 6 universal fields + Estimated Time) - one
                      schema for 33 cards, the corpus-wide keyset
                      census reading 29 of 33 already there while the
                      SAME 4 phase2 modules (2100/2200/2300/2400)
                      carried 4 legacy extras (Module, Phase,
                      Prerequisites, Related) - the same rot CC-16
                      drained from their entry pages one tick
                      earlier, now on the page a platform renders
                      per course; the 16-line drain moved only
                      prereq_census's statement counters (docs
                      200->196, free-text 182->178) while FM-05/06
                      and FM-08 stay silent by design (absence-
                      tolerant) and the entry-page surface keeps
                      its own CC-16 scoping - an extra FM field on
                      a card fires exactly 1 CC-17 with CC-01..16
                      kept silent, the same field on that module's
                      PREREQUISITES.md fires exactly 1 CC-16 and
                      0 CC-17, two cards aggregate into exactly
                      2 CC-17.
                      CC-18 the third surface of the FM keyset
                      family: a lesson's FM carries only the
                      13-field lesson keyset (card keyset +
                      Module/Phase + Prerequisites/Related +
                      the optional Hardware/Software pair),
                      negative excess only; the tick-588
                      classifier census split the lesson class
                      honestly - the direct module-dir surface
                      is 93 files, 100% linked (tick-587's 159
                      figure was a recursive-slice over-count;
                      the extra 87 live in module
                      subdirectories), three forms read
                      81 + 6 (+HW/SW) + 6 (-Module/-Phase)
                      and the 12-line drain wrote the
                      derivable navigation pair into exactly
                      those 6 so the surface reads two exact
                      forms inside the family - an extra FM
                      field on a lesson fires exactly 1 CC-18
                      with CC-01..17 kept silent, the same
                      field on the card fires exactly 1 CC-17
                      and 0 CC-18, two lessons aggregate into
                      exactly 2 CC-18.
                      CC-19 the fourth surface of the FM keyset
                      family: a guide's FM carries only the
                      11-field guide keyset (card keyset +
                      Module/Phase + Prerequisites/Related,
                      the lesson core without the optional
                      Hardware/Software pair), negative
                      excess only; the tick-589 census read
                      the 21 module-level guides clean of
                      excess - all linked, 12 on the 9-field
                      subset and 9 on the full core - and
                      the 24-line drain wrote the derivable
                      navigation pair into exactly those 12
                      (the +2 FM shift then moved the 42
                      accepted fence rows the 12 guides
                      carry - the coupling the same-tick
                      battery caught - and the count-
                      asserted re-bless re-blessed them at
                      +2, 40 same-class and 2 family-
                      reclassified on re-execution: 3403
                      RUNNER-CRASH->TIMEOUT, 7103 the
                      recorded FLAKY_FAMILY pair, notes
                      carried, no fence content changed) so
                      the surface reads one exact form - an
                      extra FM field on a
                      guide fires exactly 1 CC-19 with
                      CC-01..18 kept silent, the same field
                      on a lesson fires exactly 1 CC-18 and
                      0 CC-19, two guides aggregate into
                      exactly 2 CC-19.
                      CC-20 the fifth surface of the FM
                      keyset family: an assessment bank's
                      FM carries only the 9-field
                      assessment keyset (entry keyset +
                      Estimated Time + Prerequisites/
                      Related - the card core without
                      Module/Phase and without the
                      optional Hardware/Software pair),
                      negative excess only; the tick-590
                      census read the 66 PRACTICE/QUIZ
                      banks clean of excess - every
                      module the pair, all linked, 64 on
                      the 9-field keyset and 2 phase2
                      legacy carriers widening with
                      Module/Phase (2300-framework-
                      engineering PRACTICE/QUIZ) - and
                      the 4-line drain deleted the
                      legacy pair so the family froze
                      at 66/66, the fence coupling one
                      file small: only 2300's PRACTICE
                      carries accepted rows, the -2
                      shift moved its 2 and the re-bless
                      re-blessed them at 72->70 and
                      316->314 same-class, notes
                      carried, no fence content changed
                      - an extra FM field on an
                      assessment fires exactly 1 CC-20
                      with CC-01..19 kept silent, the
                      same field on a guide fires
                      exactly 1 CC-19 and 0 CC-20, two
                      assessments aggregate into
                      exactly 2 CC-20.
                      CC-21 the sixth surface of the FM
                      keyset family: a phase README's FM
                      carries only the 6-field phase
                      keyset (the same entry keyset),
                      negative excess only; the tick-591
                      census read the 7 phase headers
                      born-clean - every one on the
                      exact keyset, all linked from
                      MASTER-INDEX, MASTER-INDEX itself
                      on the same form - so the lock is
                      a zero-drain one: the course-group
                      browse surface above every card
                      froze at the family the moment it
                      was named - an extra FM field on a
                      phase header fires exactly 1 CC-21
                      with CC-01..20 kept silent, the
                      same field on a card fires exactly
                      1 CC-17 and 0 CC-21, two phase
                      headers aggregate into
                      exactly 2 CC-21.
                      CC-22 the seventh surface of the FM
                      keyset family: a phase-level
                      assessment page's FM carries only
                      the 6-field entry keyset, negative
                      excess only; the tick-592 census
                      read the 14 phase-practice/quiz
                      pages under 00-META/assessment
                      born-clean - every one on the exact
                      keyset, all 14 linked (MASTER-INDEX,
                      SITEMAP, their phase READMEs) - so
                      the lock is a zero-drain one in the
                      CC-21 shape: the phase-completion
                      checkpoint surface between course
                      groups froze at the family the
                      moment it was named (module-level
                      CC-20 siblings carry the 9-field
                      bank; these stay minimal) - an extra
                      FM field on a phase assessment fires
                      exactly 1 CC-22 with CC-01..21 kept
                      silent, the same field on a phase
                      header fires exactly 1 CC-21 and
                      0 CC-22, two phase assessments
                      aggregate into
                      exactly 2 CC-22.
                      CC-23 the eighth surface of the FM
                      keyset family: a learning-resources
                      reference page's FM carries only
                      the 6-field entry keyset, negative
                      excess only; the tick-593 census
                      read the 43 standalone reference
                      pages born-clean (bridges, case-
                      studies, cheat-sheets, guides,
                      interactive, projects, resources,
                      troubleshooting) while labs (15/15
                      entry vs entry+ET) and tutorials
                      (13 core + 2 legacy carriers) read
                      other forms and stayed unlocked -
                      so the lock is a zero-drain one in
                      the CC-21/CC-22 shape: the
                      enrichment reference surface froze
                      at the family the moment it was
                      named - an extra FM field on a
                      cheat-sheet fires exactly 1 CC-23
                      with CC-01..22 kept silent, the
                      same field on a tutorial fires 0
                      (out of scope), a cheat-sheet and a
                      project aggregate into
                      exactly 2 CC-23.
                      CC-24 the ninth surface of the FM
                      keyset family: a learning-resources
                      tutorial's FM carries only the
                      8-field tutorial keyset (the 6-field
                      entry keyset + Estimated Time +
                      Prerequisites), negative excess
                      only; the tick-593 census parked
                      tutorials as 13 files on the
                      8-field core with 2 legacy carriers
                      widening with Category and Related
                      (TUTORIAL-007, TUTORIAL-014), so
                      the tick-594 drain deleted exactly
                      those 4 FM lines count-asserted
                      and the family froze at 15/15 -
                      prereq_census byte-identical
                      (Related feeds only the related
                      graph, reported never gated),
                      related_census honestly at
                      183 docs / 26 tokens / 9 bracketed
                      with RL-01..03 still zero,
                      linkcheck unchanged (bare tokens,
                      never markdown links), fence
                      coupling one file small -
                      TUTORIAL-007 carries 5 accepted
                      fence rows / 5 notes in
                      accepted_exec_census (TUTORIAL-
                      014 none), the -2 shift moved
                      all 5 and the count-asserted
                      re-bless re-blessed them at the
                      shifted lines 164->162, 208->206,
                      276->274, 327->325, 389->387,
                      same class on re-execution,
                      notes carried, no fence content
                      changed - an extra FM field
                      on a tutorial fires exactly 1
                      CC-24 with CC-01..23 kept silent,
                      the same field on a cheat-sheet
                      fires exactly 1 CC-23 and 0 CC-24,
                      two tutorials aggregate into
                      exactly 2 CC-24.
                      CC-25 the tenth surface of the FM
                      keyset family: a learning-resources
                      lab's FM carries only the 7-field
                      lab keyset (the card keyset: the
                      6-field entry keyset + Estimated
                      Time), negative excess only; the
                      tick-593 park dissolved
                      structurally - the tick-595 census
                      read the labs tree as two disjoint
                      sub-surfaces, the wide 15 exactly
                      the LAB-0xx lab docs (all on the
                      exact 7-field card keyset, all
                      carrying authored 1-12 hour
                      budgets) and the minimal 15
                      exactly the SOLUTION-LAB-0xx answer
                      keys under labs/solutions (all on
                      the exact 6-field entry keyset),
                      each born at 100% uniformity, 0
                      no-FM, 0 unlinked - so no ET
                      decision exists to make, the lab
                      half locks zero-drain in the
                      CC-21/22/23 shape (non-recursive
                      glob keeps solutions out of scope)
                      and the solutions half stays parked
                      for its own clause (CC-26) next
                      tick - an extra FM field on a lab
                      fires exactly 1 CC-25 with
                      CC-01..24 kept silent, the same
                      field on a SOLUTION-LAB answer key
                      fires 0 (out of scope), two labs
                      aggregate into exactly 2 CC-25.
                      CC-26 the eleventh surface of the FM
                      keyset family: a SOLUTION-LAB answer
                      key's FM carries only the 6-field
                      entry keyset, negative excess only;
                      the tick-595 census showed the
                      minimal 15 of the labs tree are
                      exactly the 15 SOLUTION-LAB-0xx
                      answer keys under labs/solutions and
                      the tick-596 census read the class
                      clean - all 15 already on the exact
                      6-field entry keyset, 0 no-FM, all
                      15 linked (MASTER-INDEX and SITEMAP;
                      SOLUTION-LAB-000 also from
                      ORGANIZATION-GUIDE) - so the lock is
                      a zero-drain one in the CC-21/22/23
                      shape: the answer-key surface froze
                      at the family the moment it was
                      named, no drain, no fence coupling
                      (the 58 accepted fence rows live on
                      the LAB docs, not the solutions) -
                      an extra FM field on a solution
                      fires exactly 1 CC-26 with
                      CC-01..25 kept silent, the same
                      field on a LAB doc fires exactly 1
                      CC-25 and 0 CC-26 (clause scoping,
                      never double-reported), two
                      solutions aggregate into exactly
                      2 CC-26.
                      CC-27 the twelfth surface of the FM
                      keyset family: a 00-META meta page's
                      FM carries only the 6-field entry
                      keyset, negative excess only; the
                      tick-597 uncovered-surface census read
                      the rest beyond CC-16..26 as 53 files
                      in four families - 49 already on the
                      exact 6-field entry keyset scattered
                      across nine roots (00-META 20, volumes
                      7, phase CHECKPOINTs 7, comparisons 3,
                      diagrams 4, industry 3,
                      enterprise-solutions 2, use-cases 2,
                      notebooks 1) and 4 drift carriers
                      (UC-001/002 with Related, IND-003 with
                      Estimated Time, SOL-002 with
                      Category/Estimated Time/Prerequisites/
                      Related) - the largest single-root
                      family, the 20 root-level 00-META docs
                      (MASTER-INDEX, SITEMAP,
                      ORGANIZATION-GUIDE, QA-TOOLING and the
                      rest of the help/navigation/governance
                      layer), locks first, born-clean: all
                      20 on the exact keyset, 0 no-FM, 0
                      off-keyset, heavily cross-linked
                      (SITEMAP from 7 docs, GLOSSARY from 7,
                      VOLUME-GUIDE from 12); zero-drain in
                      the CC-21/22/23 shape, non-recursive
                      so 00-META/assessment (CC-22) stays
                      outside - an extra FM field on a meta
                      page fires exactly 1 CC-27 with
                      CC-01..26 kept silent, the same field
                      on a SOLUTION-LAB answer key fires
                      exactly 1 CC-26 and 0 CC-27 (clause
                      scoping, never double-reported), two
                      meta pages aggregate into exactly
                      2 CC-27.
                      CC-28 the thirteenth surface of
                      the FM keyset family: a volumes
                      page's FM carries only the 6-field
                      entry keyset, negative excess only;
                      the tick-597 census had parked the
                      volumes tree among the exact-6
                      scatter and the tick-598 census
                      read the class clean - all 7 volume
                      guides (VOLUME-1 through VOLUME-7,
                      the book-style spine a platform
                      renders as the curriculum's table
                      of contents) already on the exact
                      6-field keyset, 0 no-FM, 0
                      off-keyset, all 7 linked (SITEMAP,
                      VOLUME-GUIDE and PROGRESS-TRACKER
                      beside projects and peer volumes);
                      zero-drain in the CC-21/22/23
                      shape, no fence coupling (the 23
                      accepted fence rows live on 6 of
                      the volume docs and zero-drain
                      moves nothing), non-recursive by
                      design - an extra FM field on a
                      volume fires exactly 1 CC-28 with
                      CC-01..27 kept silent, the same
                      field on a meta page fires exactly
                      1 CC-27 and 0 CC-28 (clause
                      scoping, never double-reported),
                      two volumes aggregate into exactly
                      2 CC-28.
                      CC-29 the fourteenth surface of
                      the FM keyset family: a phase
                      CHECKPOINT's FM carries only the
                      6-field entry keyset, negative
                      excess only; the tick-597 census
                      had parked the phase CHECKPOINTs
                      among the exact-6 scatter and the
                      tick-599 census read the class
                      clean - all 7 phase-level
                      completion checkpoints
                      (docs/phases/phase*/CHECKPOINT.md,
                      the gate between one phase's
                      modules and the next) already on
                      the exact 6-field keyset, 0 no-FM,
                      0 off-keyset, all 7 linked (each
                      from its phase README beside
                      MASTER-INDEX, SITEMAP,
                      ORGANIZATION-GUIDE and
                      PROGRESS-CHECKPOINTS); zero-drain
                      in the CC-21/22/23 shape, no
                      fence coupling (no CHECKPOINT
                      carries accepted fence rows) - an
                      extra FM field on a CHECKPOINT
                      fires exactly 1 CC-29 with
                      CC-01..28 kept silent, the same
                      field on a volume fires exactly
                      1 CC-28 and 0 CC-29 (clause
                      scoping, never double-reported),
                      two CHECKPOINTs aggregate into
                      CC-30 born tick-600 as the fifteenth surface - the six
                      scattered enrichment roots (comparisons, diagrams,
                      industry, enterprise-solutions, use-cases, notebooks,
                      READMEs included, non-recursive) drained of their 4
                      drift carriers (UC-001/UC-002 Related, IND-003
                      Estimated Time, SOL-002 Category/Estimated Time/
                      Prerequisites/Related - numeric references and prose
                      pointers, no doc links; the drain shifted
                      the 10 accepted fence rows on the three
                      row-carrying carriers (SOL-002 5 rows at
                      -4, IND-003 3 rows at -1, UC-001 2 rows at
                      -1) and the gate's own --update re-bless
                      re-blessed them at the shifted lines, same
                      class on re-execution, notes carried, no
                      fence content changed, while prereq_census
                      statement counters moved honestly docs
                      196->195 / ft 178->177 with edges/tier-edges
                      untouched) then locked on the exact 6-field
                      entry keyset across all 19 files, 0 no-FM, 0
                      off-keyset; negatively tested across five runs -
                      pristine 0, an extra FM field on UC-003 fires
                      exactly 1 CC-30 with CC-01..29 kept silent, the same
                      field on a phase CHECKPOINT fires exactly 1 CC-29
                      and 0 CC-30, two scattered files aggregate into
                      CC-31 born tick-601 as the first filename-derivation
                      lock - every docs/ md whose FM carries a Document
                      ID and whose stem is not one of the five fixed-name
                      classes (README, PRACTICE, QUIZ, PREREQUISITES,
                      CHECKPOINT) must have stem == ID (exact, lowercased,
                      or ID+'-' prefix); census 408 docs with IDs, 0
                      without - 256/256 non-fixed-name files clean (242
                      exact, 14 lowercased phase assessments) while the
                      152 deviations decompose exactly into the five
                      fixed-name classes carrying path-qualified IDs by
                      convention (1100-PRACTICE, PHASE1-PRACTICE,
                      COMPARISONS-README), out of scope; zero-drain, born
                      at 0 findings, no fence coupling; negatively tested
                      across five runs - pristine 0, a mutated ID on
                      UC-003 fires exactly 1 CC-31 with CC-01..30 kept
                      silent, the same mutation on a fixed-name 1100
                      PRACTICE fires 0 anywhere, two mutated IDs
                      CC-32 born tick-602 as the fixed-stem
                      completion of CC-31 - the five fixed-name
                      classes now get their own derivation rule:
                      Document ID must end '-'+stem and the
                      prefix must be the scope anchor, the full
                      scope dir uppercased for READMEs and the
                      anchor segment for the rest (numeric module
                      codes, PHASEn, or dir.upper()); census
                      152/152 fixed-stem IDs ending '-'+stem
                      with exactly 4 short-form README carriers
                      (2100/2200/2300/2400 in phase2) drained to
                      the long form - 0 external references to the
                      old short IDs, no fence coupling, 152/152
                      clean after the drain; negatively tested
                      across five runs - pristine 0, a wrong-prefix
                      ID on a fixed-name 1100 PRACTICE fires
                      exactly 1 CC-32 with CC-01..31 kept silent,
                      the same mutation on non-fixed UC-003 fires
                      exactly 1 CC-31 and 0 CC-32, two fixed-stem
                      CC-33 born tick-603 as the Tags
                      vocabulary lock - a Tags value must be
                      a bracket list whose items are each
                      single-quoted kebab-case tokens (lowercase
                      letters, digits, hyphens); census 408/408
                      FM docs already on the quoted
                      bracket-list shape, 238 distinct tags with
                      0 near-duplicate pairs and exactly 1
                      charset deviation ('llama.cpp' in
                      4101-GGUF-Physics) drained to 'llamacpp' -
                      1507 clean items across the tree (the
                      same-commit TV-01 protocol amend
                      replaced the WHITELIST entry and VARIANTS
                      gained the correcting map);
                      negatively tested across five runs -
                      pristine 0, an uppercase tag core on
                      4101-GGUF-Physics fires exactly 1 CC-33
                      with CC-01..32 kept silent, an extra FM
                      field on UC-003 fires exactly 1 CC-30 and
                      0 CC-33, two Tags mutants aggregate into
                      exactly 2 CC-33, post-restore
                      byte-identical.
    heading_scan
                      Heading skeleton soundness (HS-01..05,
                      hard): the platform renders a TOC and
                      anchor deep-links from heading structure,
                      so the skeleton must be sound. HS-01 no
                      level skip (child more than one level
                      under its parent), HS-02 no empty heading
                      text, HS-03 every doc carries at least
                      one H2 (no flat bodies), HS-04 no
                      emoji-led heading, HS-05 no emoji
                      anywhere inside a heading - structure
                      headings are plain text (tick-482 canon;
                      HS-04: labs tick-485, rest of the corpus
                      tick-486 after the 558-header drain with
                      its 40 coupled `#-` anchor rewrites;
                      HS-05: tick-487, the 2-header non-LED
                      drain; typographic arrows stay legal).
                      Born tick-459 at 0/0/0 across 408 docs,
                      KW-03. The birth census also measured
                      245 duplicate heading texts in 30 docs
                      (Task/Pros/Cons template repeats under
                      per-item parents) - triaged ACCEPT,
                      deliberately not gated:
                      hierarchical-correct, slug dedup is
                      deterministic, links verified by the
                      anchor gate
    table_scan
                      Markdown table integrity (TB-01/02,
                      hard): TB-01 every row's cell count
                      equals the header's (escape-aware:
                      literal pipes inside cells are escaped
                      and not column breaks), TB-02 the
                      separator row is well-formed and matches
                      the header width. The platform renders
                      tables directly - one broken row is a
                      visible defect. Born tick-459: 533
                      tables scanned, one merged separator+row
                      line drained in CP-002 (Indexing Speed)
    updated_badge_scan
                      Body Last Updated badge parity (UB-01,
                      hard): the FM Last Updated field is the
                      canonical gated freshness value, but ~16
                      docs also render a display badge in the
                      header block; where it exists it must
                      mirror FM exactly. Born tick-461 after
                      syncing 14 stale badges - 7
                      February-frozen display badges, 7
                      late-Sept near-misses - a class invisible
                      to date_cohort (which reads FM only)
    diagram_scan
                      Mermaid diagram integrity (DM-01..03,
                      hard): the corpus carries 56 mermaid
                      blocks (52 graph, 2 state, 2 sequence)
                      that the platform renders directly - a
                      syntax-broken block is a visible error
                      box. DM-01 known diagram-type header,
                      DM-02 no unquoted ()[]{} in graph node
                      labels (quote- and shape-aware: [(db)]
                      ([stadium]) ((circle)) {{hex}} [/para/]
                      understood), DM-03 no node opened and
                      closed by an edge operator / EOL. Born
                      tick-462 at 0 across 56 blocks / 19 docs
    link_case_scan
                      Link case-sensitivity portability
                      (LC-01, hard): linkcheck/anchor_check
                      resolve with os.path.exists - case-
                      insensitive on the Windows authoring
                      machine, case-sensitive on the Linux
                      hosting platform - so `./Guide-Career.md`
                      vs `GUIDE-CAREER.md` would be invisible
                      locally and break only in production.
                      LC-01 resolves every internal link path
                      segment-exactly. Born tick-463 at 0
                      across 3015 docs/ links (3325 repo-wide)
    link_text_scan
                      Intra-doc link text quality (LT-01,
                      hard): no emoji in an internal link's
                      label - internal targets are corpus
                      headings, which HS-04/05 keep emoji-
                      free, so an emoji nav label mismatches
                      what the reader finds at the anchor
                      (screen readers read the glyph name
                      aloud; the platform TOC generator
                      copies labels verbatim). External
                      links out (brand glyphs legal); vague
                      link text triaged ACCEPT - corpus
                      weak-text sites are all deliberate
                      teaching examples in the style guides.
                      Born tick-488 born-at-zero after the
                      12-link drain across 1849 intra-doc
                      links
    invisible_scan
                      Invisible-character hygiene
                      (IV-01, hard): no zero-width
                      space/non-joiner/word joiner,
                      soft hyphen, no-break space
                      (plain and narrow), BOM/zero-
                      width no-break space, bidi
                      control or stray control
                      character outside fences -
                      paste-in characters that render
                      as nothing but break exact-
                      match search, heading slugs
                      and copy-out of code samples.
                      ZWJ/VS16 emoji joiners stay
                      legal (tick-486 emoji class);
                      in-fence is code content, out
                      of scope; CRLF is a different
                      class (repo is LF-normalized).
                      Hazard classes are built with
                      chr() so the script source
                      stays pure ASCII (tick-488
                      lesson). Born tick-489 born-at-
                      zero, KW-03 prophylactic
                      pattern: the birth census
                      measured all 408 docs clean in
                      and out of fences - the gate
                      guards the platform era where
                      contributors paste from the web
    line_ending_scan
                      Line-ending + final-newline
                      hygiene (LE-01/02, hard), the
                      one BYTE-level gate in the
                      fleet: every other scan reads
                      with universal newlines, which
                      silently translates CRLF to LF
                      - the whole fleet is
                      structurally blind to this
                      axis. LE-01 no carriage-return
                      byte in any doc (no CRLF, no
                      lone CR); LE-02 every non-
                      empty doc ends with a newline.
                      Whole file by design - fences
                      and FM are irrelevant to line
                      endings. Committed content was
                      already 100% LF (measured byte-
                      exact; .gitattributes eol=lf
                      normalizes at add time) - the
                      birth drain renormalized 120
                      stale-CRLF worktree copies of
                      clean blobs plus 24 notebooks/
                      yml, and content-fixed 2 README
                      blobs missing their final
                      newline. Born tick-490 born-at-
                      zero
    script_hygiene_scan
                      QA-fleet source hygiene
                      (SH-01/02, hard) - the one
                      gate that watches the fleet
                      itself: every .py under
                      scripts/ (106 at birth).
                      SH-01 pure-ASCII sources
                      (tick-488: literal emoji
                      inserted by a tool survived
                      until a byte check); SH-02
                      compile with SyntaxWarning-
                      as-error (tick-490: a bare
                      invalid escape warned on
                      every run, hard error in a
                      future Python). compile()
                      never executes the module.
                      Born tick-491 born-at-zero
                      after a 26-replacement drain
                      across 10 files, every
                      runtime value proven intact
    filename_scan
                      Filename hygiene (FN-01..06,
                      hard) - path segments are
                      API: git, shells and the
                      web platform all consume
                      them. FN-01 case-only
                      collision in one dir (NTFS
                      hides it, Linux CI
                      overwrites silently), FN-02
                      spaces (URL %20), FN-03
                      Windows-invalid + URL-
                      significant chars, FN-04
                      non-ASCII segments, FN-05
                      edge-whitespace/trailing-
                      dot (unrepresentable on
                      Windows), FN-06 paths over
                      200 (MAX_PATH headroom).
                      Whole repo, any-depth
                      ignore of generated/vendor
                      trees. Born tick-492 born-
                      at-zero: 597 tracked files
                      censused clean
    frontmatter_value_scan
                      FM VALUE contracts (FV-01..13,
                      hard) - the platform
                      ingestion simulation: does
                      exactly what the platform
                      will do, yaml.safe_load the
                      block, then type-check the
                      metadata-driving fields.
                      FV-01 Last Updated ISO
                      YYYY-MM-DD (yaml auto-
                      converts to a real date -
                      the conversion IS the
                      contract), FV-02 Estimated
                      Time machine-comparable
                      (single-regime or the
                      canonical PREREQUISITES
                      two-regime form), FV-03
                      Tags list-of-string, FV-04
                      the whole block parses to a
                      dict (catches ValueError
                      too - PyYAML raises OUT of
                      safe_load on an impossible
                      bare date: ingestion
                      crash). Related arms: FV-05
                      no dangling integer id
                      (two-pass cross-file - the
                      platform renders Related
                      as next-lesson cards),
                      FV-06 Related is a prose
                      pointer or a list of
                      ids/names, never another
                      scalar or a mapping. Enum/
                      display arms: FV-07
                      Difficulty is one of
                      Beginner/Intermediate/
                      Advanced (closed filter
                      enum), FV-08 Title is a
                      non-empty string (platform
                      card title), FV-09 Last
                      Updated is never in the
                      future (recently-updated
                      sorts), FV-10 a string
                      Document ID is a URL-safe
                      key: uppercase-initial or
                      module-numbered, hyphen-
                      separated alphanumerics,
                      no whitespace/punctuation
                      (canonical key AND URL
                      slug). FV-11 a Related
                      string element in the
                      LAB-/TUTORIAL- namespaces
                      resolves to a real file
                      under learning-resources
                      (pass-1 filename universe;
                      same broken-card bug as
                      FV-05, string edition).
                      The fleet's only
                      third-party import (PyYAML)
                      - deliberate: the rule
                      under test IS yaml parsing.
                      Born tick-493, one drain
                      ('1 hours' -> '1 hour');
                      Related tick-494, tier/
                      title/date tick-495, key-
                      shape tick-496, resource
                      refs tick-497, all born-
                      at-zero; heading-case
                      candidate formally SKIPPED
                      with measurement (8795
                      H2/H3: 5617 sentence /
                      3158 sentence+Title-Case
                      topic phrases / 20 all-
                      caps - would need a
                      curated proper-noun
                      allowlist). Scope tick-611:
                      the simulation walks both
                      trees. Scope tick-612:
                      FV-12 under experiments/
                      the keyset fields Title/
                      Status/Difficulty are
                      present (FM-03 walks docs/
                      only, EC-01 binds the
                      Document ID alone; Last
                      Updated absence is FV-01's,
                      no double-report), FV-13
                      Status is the FM-04 enum
                      {Complete} - before this
                      the second tree's Status
                      column answered to no
                      gate. Born tick-612 born-
                      at-zero: 48/48 five-field
                      keysets, 48/48 Complete
    glossary_scan
                      Glossary integrity (GS-01..03, hard):
                      GLOSSARY.md is the platform's
                      terminology backbone - lookups, tooltips
                      and search generate from its tables.
                      GS-01 no Correct/Incorrect row lists its
                      own canonical term as incorrect (LLMOps
                      did), GS-02 no dead entries (every term
                      used corpus-wide; 01.AI removed), GS-03
                      one row per term (Parameters was
                      duplicated across two tables, merged).
                      Born tick-464 after those three drains;
                      67 terms
    emphasis_scan
                      Emphasis parity (EM-01, hard): bold `**`
                      must pair within one render block - headings
                      are own blocks, paragraphs span lines, fences
                      and inline code (double-backtick first) are
                      skipped. Tick-465 census found 7 PREREQUISITES
                      headings reading `### If you're not
                      familiar:**` - a stray `**` leaked from the
                      sibling `**If you're not familiar:**` paragraph
                      template, rendering a literal `**` - drained
                      same tick; born at 0 across 408 docs
    whitespace_scan
                      Whitespace hygiene (WS-01..03, hard, all
                      fence-aware): WS-01 3+ consecutive blank
                      lines outside fences (markdown collapses
                      them to one break - authoring residue;
                      both birth sites sat at EOF after the
                      final `---` separator), WS-02 trailing
                      whitespace (2+ trailing spaces are a
                      CommonMark hard break, 1 is editor
                      residue), WS-03 mid-line tabs (corpus is
                      spaces-only). Invisible-character rot
                      (NBSP/ZWSP/BOM/control) censused the same
                      tick: zero corpus-wide, un-gated until a
                      class appears. Born tick-466 after 4
                      triple-blank drains; the first census's
                      blank regex was CRLF-blind - the two CRLF
                      sites surfaced only under the line-based
                      scanner
    difficulty_distribution_scan
                      Difficulty as a sequence dimension (DX-01,
                      report-only census): per-phase B/I/A
                      distribution and per-doc anomalies >=2 bands
                      from the phase median; birth census
                      2026-09-30 measured the ramp coherent
                      (phase-1 Intermediate -> 3/4/5/7 Advanced,
                      260 in-phase docs) with 25 anomaly
                      candidates that are almost all entry-point
                      READMEs by design - only 2 real lesson
                      candidates (3301/3302 Beginner primers in
                      the Advanced wall, kept: short reference
                      primers); README aggregate class is known
    difficulty_census Difficulty vocabulary closure (DI-01..03,
                      hard): the platform renders difficulty as
                      a filter/sequence dimension, so the
                      vocabulary must be closed and exact. DI-01
                      missing, empty or unknown value, DI-02
                      field-name variant (canonical is
                      "Difficulty:") - both hard from birth,
                      measured 0 across 408 docs at tick-411
                      (KW-03). DI-03 value outside the canonical
                      Beginner/Intermediate/Advanced enum - the
                      drain list was {"Expert"} - 5 sites drained
                      tick-412 to Advanced (3-level enum closed),
                      hard since the drain
    lesson_anatomy_census
                      Lesson anatomy (LA-01): every lesson doc
                      opens its pedagogy with the canonical
                      "Learning Objectives" H2 - the platform's
                      syllabus card and progress model key on it.
                      Born from the tick-413 census (104/114
                      lessons already carried the exact heading);
                      the 10 missing sites were drained to the
                      canonical H2 in tick-414, so the corpus is
                      114/114 and the gate holds it (same scope
                      as lesson_id_scan - 114 lesson docs).
                      LA-02: the canonical H2 must also be listed
                      in the lesson's Table of Contents (the
                      syllabus card reads the TOC). Born hard in
                      tick-415 - the 3 census sites were drained
                      in the same tick, baseline 0. LA-03: every
                      lesson states its Abstract H2. Born hard in
                      tick-416 - the 2 census sites (2305/2306
                      guides) were drained in the same tick,
                      baseline 0
    closure_census
                      Closing blocks (CL-01..03): a lesson closes
                      the way it opens - Summary-class recap,
                      References, Next Steps (fence-invisible
                      H2s, numbered variants allowed). CL-01 no
                      Summary-class closing H2 (Summary /
                      Conclusion / Key Takeaways) - REPORT
                      queue: the tick-417 census found only
                      14/114 lessons carrying one; the 100-site
                      queue drains phase-by-phase and the check
                      hardens at 0 (exit 0 by design, the report-queue
                      pattern). CL-02 no References-class
                      closing H2 (References / Further Reading)
                      - hard from birth tick-417: the single
                      census site (7301-Orchestration) was
                      drained the same tick to the sibling-7303
                      pattern, baseline 0. CL-03 no "Next Steps"
                      closing H2 - hard from birth, 114/114
                      already carried one
    unfinished_marker_scan unfinished-content markers in prose
                       (UM-01): outside any code fence, inline code
                       scrubbed, a line must not carry "coming soon",
                       "under construction", "to be written", "to be
                       added", "work in progress" or an uppercase
                       TODO/TBD/FIXME - code fences are invisible by
                       design (starter-code "# TODO:" exercise prompts
                       are the codified notebooks/README.md convention)
                       and fence markers may carry a ">" blockquote
                       prefix; born from the tick-276 census (108 raw
                       matches, every one in a legitimate class) that
                       turned the census into a permanent lock at
                       baseline 0
    notebook_unfinished_scan
                       the same unfinished-content marker vocabulary
                       over the .ipynb universe UM-01 structurally
                       cannot see (NU-01 markdown-cell prose with the
                       same inline-code scrub; NU-02 a marker in a
                       code cell at a non-comment position - markers
                       inside "#" comment segments stay invisible by
                       design, the notebooks/README.md "# TODO:"
                       exercise-prompt convention the corpus carries
                       108 of across all 20 notebooks); born tick-550
                       born-at-zero: 109 raw marker-shaped hits, 108
                       in the legitimate comment-prompt class and the
                       one remaining hit NB-703's prompt-injection
                       test string, matched by no rule
    notebook_catalog_check
                       the 20-notebook catalog lives twice (the
                       fleet's own README index and MASTER-INDEX's
                       Notebooks table - tick-549 mirrored the rows
                       verbatim, duplicating data across two files
                       with no lock); NC-01 id-set parity (a row in
                       one catalog only), NC-02 verbatim field
                       parity per shared id (title, topics,
                       difficulty - README's star run stripped to
                       its word - duration, and the same link
                       basename); the content-drift class link
                       checks cannot see, born tick-551 at 20/20
                       rows and 0 findings; NC-03 joined tick-564
                       locking the "### Notebooks (N files)" header
                       to the notebooks directory's own *.ipynb
                       count (census-proven true but the rows were
                       the only thing read - the header was
                       unlocked)
    changelog_summary_check
                       the changelog's three release surfaces stay
                       synchronized (CS-01/02 every "## [X.Y.Z]"
                       section has a Version Summary row and every
                       row a section, CS-03 date parity, CS-04 the
                       bracketed reference-link definition exists,
                       CS-05 order parity); born tick-552 at the
                       maximal finding - 1.3.0 carried none of its
                       own index surfaces while 1.2.0/1.1.0/1.0.0
                       did, drained in the same tick
    lab_index_parity_check
                       MASTER-INDEX's "### Labs" table mirrors every
                       lab's front-matter contract verbatim (LI-01
                       id-set parity both directions, LI-02 duration
                       equals Estimated Time, LI-03 title equals the
                       Title with its "LAB-NNN: " prefix stripped);
                       born tick-553 at the maximal finding - 12 of
                       15 durations drifted (index summed ~53 hours
                       against a declared ~85, LAB-009 read 4 hours
                       against 12) and 10 of 15 titles, drained in
                       the same tick; LI-04 joined tick-564 locking
                       the "### Labs (N files: A labs + B solutions)"
                       header arithmetic to disk - census-proven
                       true (30 = 15+15) but the header itself was
                       unlocked; LI-05/LI-06 joined tick-572
                       locking the lab's own time budget (every
                       Exercise/Part heading carries a duration
                       unless marked Optional; Estimated Time
                       equals the ceil of the part sum to the
                       whole hour, Final Challenge deliberately
                       outside it) - born at zero findings, the
                       ceiling held on all 15 labs at birth
    tutorial_index_parity_check
                       MASTER-INDEX's "### Tutorials" table locks to
                       every tutorial's front matter (TI-01 difficulty
                       parity, TI-02 Estimated Time completeness and
                       parity, TI-03 Prerequisites completeness and
                       normalized-set parity, TI-04 every item
                       normalizes - free-text prerequisites are
                       findings, TI-05 id-set parity both directions);
                       born tick-554 at the maximal finding - 13 of 15
                       front matters carried no Estimated Time and 13
                       no Prerequisites (the index's columns floated),
                       TUTORIAL-006's difficulty disagreed with its own
                       Intermediate body, four durations drifted - the
                       mirror follows the evidence-backed richer side
                       per field (the opposite of the lab lock, where
                       the front matter was the contract), drained in
                       the same tick; TI-06 joined tick-564 locking
                       the "### Tutorials (N files)" header to the
                       table's row count and the tutorials directory
                       (census-proven true at 15 = 15 = 15 but the
                       header itself was unlocked)
    cheatsheet_index_parity_check
                       MASTER-INDEX's "### Cheat Sheets" table locks
                       to the 13-file cheat-sheet fleet (CI-01 id-set
                       parity both directions with QUICK-REF-VN ->
                       QUICK-REF-VOLUME-N normalization, CI-02 topic
                       equals the Title minus its "CHEAT-SHEET-NNN: "
                       or "Volume N: " prefix verbatim, CI-03 the
                       header's file count equals the row count,
                       CI-04 every row's link names its own file);
                       born tick-555 at the maximal finding -
                       CHEAT-SHEET-006 existed on disk, in File
                       Counts (13) and SITEMAP but its row was never
                       added (12 rows under a "13 files" header, the
                       newest cheat sheet invisible to the one
                       surface learners browse first) alongside 11
                       abbreviated Topic cells, drained in the same
                       tick
    project_index_parity_check
                       MASTER-INDEX's "### Projects" table locks
                       to the 7-file capstone fleet (PJ-01 id-set
                       parity both directions, PJ-02 project cell
                       equals the Title minus its "CAPSTONE
                       PROJECT-NNN: " prefix verbatim, PJ-03 the
                       header's file count equals the row count,
                       PJ-04 every row's link names its own file,
                       PJ-05 every row carries the front-matter
                       Difficulty verbatim, PJ-06 the Duration
                       cell is "N weeks" or "N-N weeks" -
                       projects deliberately carry no Estimated
                       Time and the weeks form stays an index-side
                       planning surface, since seeding one would
                       poison the pacing census's hour/minute
                       arithmetic); born tick-556 at 13 findings -
                       6 of 7 Project cells abbreviated away the
                       front-matter Title and every row lacked
                       the Difficulty the front matter declares
                       (the inverse of the tutorial lock: the
                       front matter is the richer side, so the
                       index gains the column), drained in the
                       same tick
    small_index_parity_check
                       MASTER-INDEX's six small resource tables
                       (Career Guides, Comparisons, Industry
                       Applications, Use Cases, Solutions,
                       Diagrams) lock to their directories'
                       files (SG-01 id-set parity per table,
                       SG-02 every row's link text names its
                       own target, SG-03 the header's file
                       count equals the row count, SG-04 the
                       description cell equals the
                       front-matter Title verbatim - this
                       fleet's title conventions are
                       heterogeneous (CP-NNN:/IND-NNN:/
                       UC-NNN:/SOL-NNN: prefixes and natural
                       "Title: Subtitle" shapes on the
                       diagrams), so the mirror is
                       deliberately prefix-free); born
                       tick-557 at 21 findings - all 21
                       description cells abbreviated away
                       the front-matter Title, drained in
                       the same tick
    project_prereq_parity_check
                       the projects fleet's supporting
                       guides lock to their projects and
                       their planning surface (PP-01 every
                       PREREQUISITES-NNN's front-matter
                       Document ID matches its filename and
                       its "For:" line links PROJECT-NNN,
                       resolving to a real project file,
                       PP-02 the target project body links
                       back to its walkthrough (navigation
                       is not one-directional), PP-03 the
                       MASTER-INDEX Projects section links
                       every supporting guide in the
                       directory); born tick-558 at 5
                       findings - PROJECT-001/007 carried
                       rich inline prerequisite sections
                       but never mentioned their own
                       dedicated walkthroughs, and none of
                       the three supporting guides had a
                       MASTER-INDEX row, drained in the
                       same tick
    fleet_count_parity_check
                       the count claims a learner plans
                       from lock to disk (FC-01 every
                       MASTER-INDEX File Counts row
                       equals its disk definition -
                       Experiments counts experiments/
                       EXP_*.md excluding TEMPLATE,
                       Phase Documents every .md under
                       docs/phases, Meta Docs top level
                       only, FC-02 the TOTAL row equals
                       the category sum, FC-03 the
                       SITEMAP Experiments header equals
                       disk, FC-04 the README summary
                       equals disk, FC-05 the README
                       Experiments section lists every
                       EXP file in both directions, FC-06
                       each group header equals its own
                       block, FC-07 the seven VOLUME-*.md
                       Statistics tables equal their own
                       volume's curated path (Core/
                       Optional Documents vs checklist
                       bullets, Experiments/Labs/
                       Tutorials/Cheat Sheets vs the
                       unique id references the volume
                       body carries, Projects vs the
                       fleet id referenced or the
                       Capstone section's Project
                       headings, every id resolving on
                       disk); born tick-559 at 16
                       findings - the README summary
                       said 46 against 47 on disk and 15
                       experiments were listed nowhere
                       on the README surface, drained in
                       the same tick; FC-07 joined
                       tick-565 born at zero after a
                       definition-discovery census -
                       every claim proved true under the
                       undocumented definition its
                       surface secretly follows
                       (VOLUME-3's "4 experiments" are its
                       4 referenced EXP files though the
                       phase pool holds 6; Volumes 2-7's
                       "3 projects" are their Capstone
                       sections' three A/B/C headings)
    sitemap_listing_parity_check
                       the SITEMAP's listing identities
                       lock to disk (SL-01 fleet-section
                       listing parity both directions
                       across 19 fleets - every bullet
                       entry resolves to a member of its
                       section's documented fleet and
                       every fleet file is listed exactly
                       once, so misroutes, duplicates,
                       orphans and ghosts are findings,
                       SL-02 every docs/**/*.md plus the
                       root README is reachable from
                       SITEMAP.md, SL-03 each phase
                       module's "N lessons, M guides"
                       equals its non-boilerplate
                       entries, SL-04 registered headers
                       keep the "(N files: A x + B y)"
                       decomposition with A+B == N and
                       each part equal to its own disk
                       definition); born tick-560
                       census-proven clean at zero -
                       count parity was already SC-locked,
                       the identities behind the counts
                       were not; SL-04 joined tick-561
                       after the MI-vs-SITEMAP census
                       found 4 definitional divergences
                       (Notebooks 20 vs 21, Capstone
                       Projects 7 vs 10, Experiments
                       47 vs 48, Meta Docs 20 vs 11)
                       and the three bare headers
                       drained to the self-explaining
                       form, SL-05 joined tick-563 -
                       7 of the 29 counted headers
                       carried the bare "(N)" form
                       against the corpus convention
                       SC's docstring documents,
                       drained to "(N files)"/
                       "(N file)" and the form
                       locked (every counted header
                       opens "(N files", singular
                       "(N file" at N==1, suffix
                       free; numbers stay SC-locked)
    empty_section_scan every heading must own content (ES-01): a
                       section is empty iff nothing but blanks/HRs/
                       blockquotes/HTML-comments sits between its
                       heading and the next same-or-higher-level
                       heading; a filled child fills its parent, so
                       container sections are legitimate. Born from
                       the tick-277 census (8 findings, all one class:
                       same-level children under container headings -
                       "## Part 1" + "## 1.1" - that left every Part
                       with an empty body and mis-nested the outline);
                       fixed by re-leveling 123 headings across 3
                       files, fence model length-aware as
                       structure_lint's
    emoji_shortcode_scan gemoji shortcodes in prose (EM-01): the
                       corpus idiom is literal emoji - a platform
                       load step would need a shortcode->emoji
                       mapping while literals render everywhere
                       (``:star3:`` even rendered as raw text on
                       GitHub); inline code is scrubbed, technical
                       lookalikes (:memory:, :server:) stay invisible
    fence_label_scan   fence info-strings (FL-01 uppercase label,
                       FL-02 unlabeled fence): code gates key on the
                       exact lowercase label, so ``Python`` or a bare
                       open is code every gate silently skips - an
                       audit hole, not a style nit; census at birth
                       (tick-280): 4243 open fences, 21 labels, all
                       lowercase and labeled
    setext_scan        latent setext headings and divider hygiene
                       (SE-01 underline run under a non-blank line,
                       SE-02 bare '===', SE-03 non-'---' thematic
                       break): a '---' directly under text is a
                       setext H2 in every renderer - a heading the
                       ATX-only outline gates cannot see; blank line
                       above every divider, ATX for headings; born
                       from the tick-281 census (7 doubled dividers,
                       all one footer-nav template artifact)
    title_h1_parity_scan
                       frontmatter Title == first ATX H1 (TH-01/02/03):
                       manifest_export takes the platform nav label
                       from the Title while the rendered page title
                       is the first H1, so any drift means the nav
                       tree names a different page than the one that
                       opens; fix direction is Title := H1 verbatim;
                       born from the tick-283 census (89 lesson docs
                       where the id prefix lived only in the H1)
    fence_class_scan   fence-label classes must be classified (FC-01
                       unknown label class): fence_label_scan locks
                       that a label EXISTS, this locks that it is
                       owned - 5 parser-validated classes (python/
                       bash/json/yaml/mermaid have syntax judges) +
                       16 explicitly accepted unvalidated classes
                       (text/markdown prose, dockerfile/powershell/
                       nginx/cypher/cuda/promql/cron/gitignore
                       operational config, html/typescript/tsx/sql/
                       cpp/c teaching samples); anything else is
                       invisible code - a ``toml`` fence would skip
                       every data-block gate and a platform load
                       step could not tell code from prose; born
                       from the tick-285 label census (21 labels /
                       4244 fences), baseline 0 at birth
    lesson_id_scan     every lesson doc carries its filename's NNNN
                       id (LI-01 first H1 prefix / LI-02 Title
                       prefix): the id is the stable platform join
                       key across filename, manifest nav label and
                       rendered page; title_h1_parity_scan already
                       forces Title := H1 so the prefix lives in
                       both faces or neither, this locks the prefix
                       itself - resource_id_check is the same
                       discipline for the 43 family resources; born
                       from the tick-287 census (114/114 clean),
                       baseline 0 at birth
    census_note_gate   every accepted census row carries its adjudication
                       note (CN-01 empty or missing) and every note
                       references an accepted row (CN-02 orphan) - makes
                       the census _meta "must be adjudicated before
                       fence_exec_gate runs" contract mechanical instead
                       of a hand audit; born tick-544 after 3501@162's
                       TIMEOUT row shipped with an empty note for many
                       ticks, baseline 0/0 at birth
    footer_fm_parity_check
                       the EOF metadata footer must not
                       contradict the front matter it
                       visually mirrors (FF-01 the
                       Difficulty word verbatim, FF-02
                       the star count equal to the tier
                       index - the corpus FM vocabulary
                       is exactly Beginner 71 /
                       Intermediate 117 / Advanced 220,
                       "Expert" is illegal vocabulary,
                       FF-03 the Time Estimate verbatim
                       when the FM carries one - the 12
                       templates' footer-only time is
                       the legal sole carrier, FF-04
                       Prerequisites exactly "None" on
                       an empty FM list) - conditional
                       by design, 10/15 labs and 13/15
                       tutorials and SOLUTION-LAB-010/011
                       carry no footer at all; born
                       tick-573 at 14 findings across 6
                       files (5 lab footers ranged
                       against LI-06-proven hours, 3
                       carrying an Expert tier absent
                       from the corpus, TUTORIAL-000
                       ranged, starless and flourished),
                       drained the same tick; body-header
                       blocks and blockquote callouts
                       are the elaboration layer, unread
    module_code_census
                       module-code continuity (MC-01..03,
                       hard): the platform renders the
                       catalog from numeric codes - phase
                       pages list module dirs in code
                       order, module pages list lessons
                       and guides in stem order, the
                       volume spine paginates by VOLUME-N
                       - so a skipped code is a hole a
                       learner falls into; MC-01 module
                       dirs per phase contiguous +100
                       from phase#*1000+100, MC-02 the
                       SET of 4-digit numeric stems
                       across top-level *.md + guides +
                       assessment per module contiguous
                       (dups allowed - a guide may share
                       its lesson's code), MC-03 volumes
                       1..N; born tick-604 after the
                       census read 7 phases / 33 modules
                       / 7 volumes all clean except one
                       real hole - 1400-llmops guides
                       sat at 1404/1405 with 1403 absent
                       from birth (the only baseline
                       1403 was experiments/EXP_1403,
                       outside docs/), drained same tick
                       by renaming 1404-vLLM to 1403 and
                       1405-TGI to 1404 (12 referencing
                       files, 29 stem/display
                       replacements, 0 residual);
                       7400-memory needed nothing - its
                       guide 7402 rides between lessons
                       7401/7403 so the union set is
                       contiguous; hard from birth
    label_code_parity_scan
                       label-code parity (LP-01..05, hard):
                       linkcheck proves a link's target
                       exists and link_case_scan proves
                       its casing is portable, but
                       nothing proved the numeric code a
                       display label advertises belongs
                       to the file or module the link
                       opens - a card reading `5302:
                       Distributed Training` that opens
                       5402-Model-Parallelism is a lie
                       the learner clicks; LP-01 file
                       stem within the label range, LP-02
                       stemless file target (README/QUIZ/
                       PRACTICE/PREREQUISITES) equals the
                       nearest coded ancestor dir, LP-03
                       dir labels equal the module prefix
                       or the exact stem span, LP-04
                       phase-root links equal phase#*1000,
                       LP-05 EXP_NNNN labels open the
                       same-numbered experiment file;
                       born tick-605 from a
                       3361-internal-link census, all
                       clean after a 13-edit
                       drain (10 stale LEARNING-PATH
                       module ranges, 1 lesson-code
                       module label, 1 wrong file target
                       on VOLUME-5, 1 EXP label pointing
                       at another experiment's file);
                       hard from birth
  fence_lang_scan
                       fence-language lock (FL-01..03,
                       hard): a platform renders,
                       highlights and classifies code
                       blocks by the fence's language
                       tag, but linkcheck walks links
                       and fence_exec_gate executes
                       python fences while nothing
                       pinned the one tag every fence
                       carries - a bare ``` is a block
                       no renderer can classify and a
                       typo'd tag (`pyton`) silently
                       drops highlighting; FL-01 bare
                       opener, FL-02 tag outside the
                       accepted 22-language
                       vocabulary (a new real language
                       joins by amending LANGS), FL-03
                       fence unclosed at end of file;
                       CommonMark width-aware so 4-
                       backtick templates may embed
                       ``` fences as literal content;
                       born tick-606 from a
                       4258-fence census across 408
                       docs, zero-drain: zero bare,
                       zero off-vocabulary, zero
                       unclosed; hard from birth
  experiment_id_scan
                       experiments identity lock
                       (EC-01..03, hard): experiments/
                       is the one content directory
                       outside docs/ and the platform
                       catalogs content by Document ID
                       while its catalog walks docs/
                       links, yet doc_id_check scans
                       docs/ only - experiment
                       identity was unvouched. EC-01
                       every experiments/*.md carries a
                       top-level FM Document ID in the
                       EXP_NNNN form equal to the
                       file's own code token (the LP-05
                       label rule lifted to file
                       identity; TEMPLATE.md is the one
                       by-design exemption - a template
                       cannot honestly carry a real
                       code, the CC-31 carve-out
                       shape); EC-02 IDs unique across
                       experiments/ and disjoint from
                       the docs/ namespace (the ID
                       space is global; two files
                       answering to one ID is an
                       ambiguous catalog row); EC-03
                       every experiment referenced from
                       at least one docs/ file by name
                       or stem (the CHEAT-SHEET-006
                       orphan class fleet_count_parity
                       proved - linkcheck green while
                       15 of 47 experiments were
                       invisible from the README front
                       door). Born tick-608 from a
                       48-file census (48 FM, 1 keyset
                       shape, 47 real IDs all matching
                       their filename codes, 0
                       duplicates, 0 docs/ collisions,
                       48/48 linked), zero-drain, hard
                       from birth
  hierarchy_scan
                       catalog placement lock
                       (HZ-01..03, hard): the
                       platform builds its catalog
                       hierarchy (phase -> module ->
                       lesson) from the FM Phase /
                       Module declarations while
                       the disk layout under
                       docs/phases/ is the ground
                       truth they denormalize - a
                       drifted copy files a lesson
                       under the wrong phase or
                       module page with linkcheck
                       green. HZ-01 FM Phase parses
                       as an integer equal to the
                       phaseN directory above the
                       doc; HZ-02 FM Module is a
                       bare 4-digit code equal to
                       the NNNN- module directory;
                       HZ-03 every module-scoped
                       content doc (lesson file or
                       guides/ subtree) carries
                       BOTH fields, README.md,
                       PREREQUISITES.md and the
                       CC-20 assessment/ banks
                       (whose 9-field keyset admits
                       no placement fields - a past
                       drain deleted exactly those 4
                       lines from 2300's pair) the
                       by-design exemptions. Born
                       tick-609 from a 260-doc
                       census (114 carriers: 93
                       lessons + 21 guides, uniform
                       bare-digit grammar, 0 drift),
                       zero-drain, hard from birth
  title_uniqueness_scan
                       display-title uniqueness
                       (TU-01, hard): the
                       display-title space is
                       global like the Document
                       ID space - doc_id_check
                       locks ID uniqueness so two
                       files can never answer to
                       one catalog row, this locks
                       the display side so two
                       rows can never be
                       indistinguishable to a
                       learner listing or
                       searching by name. One
                       finding per extra file in a
                       case-folded duplicate group
                       across docs/ + experiments/;
                       Title presence stays
                       frontmatter_lint FM-03's
                       duty (never double-
                       reported) and
                       experiments/TEMPLATE.md
                       carries no uniqueness
                       exemption (EC-02's lesson).
                       Born tick-610 from a 456-doc
                       census (456 distinct, 0
                       duplicate groups), zero-
                       drain, hard from birth
  gate_robustness_audit
                       no QA gate may die ugly
                       on hostile input (GRA-01
                       traceback, GRA-02 hang,
                       hard from birth,
                       tick-638): every
                       scripts/qa/*.py joins
                       the roster
                       automatically and runs
                       against a synthetic
                       malformed tree (unclosed
                       fence, ragged table,
                       invalid UTF-8, absent
                       corpus anchors,
                       degenerate empty
                       corpora); exit 0 or
                       exit-nonzero-WITH-
                       diagnostic passes, a
                       traceback or a hang
                       fails naming the gate;
                       7 by-contract
                       exclusions (the
                       orchestrator itself,
                       the spawn child, the
                       fence executors, the
                       network gate, the
                       scripts-dir auditor,
                       the git-history
                       report); born census:
                       20 crash gates in 4
                       classes, all drained
                       same tick - 15 absent-
                       anchor gates SKIP (the
                       anchor's existence is
                       linkcheck's single
                       ownership), the
                       curriculum_metrics
                       empty-corpus onion
                       (median -> mean -> min,
                       three census runs)
                       landed as one SKIP
                       guard, quiz_balance and
                       bashblock got named
                       guards; NEG proves
                       detection both ways
                       (staged revert -> CRASH
                       exactly 1, planted hang
                       -> TIMEOUT exactly 1);
                       the NEG staging itself
                       surfaced a 5th class -
                       the legacy trio
                       (brand_scan,
                       legacy_ad_rename,
                       legacy_ad_scan) anchored
                       ROOT to __file__ and
                       ignored --root, so a
                       relocated copy rglob'd
                       the parent dir ->
                       TIMEOUT, drained by
                       honoring --root (fleet
                       unchanged - the runner
                       always passes --root);
                       the fleet smoke then
                       caught the auditor in
                       its own ARGERROR class
                       (argparse without
                       --root -> rc=2, no
                       summary line), fixed by
                       accepting --root
  queue gate (drain in progress; never fails the report unless --fail-on-queue):
    objectives_lint    template-objective artifacts (OL-01/OL-02), phase by phase
    fence_namecheck    unbound names in python fences (report mode), two
                       codes: NC-01 module access without import (a known
                       module used as `name.attr` that no fence in the
                       document imports - certain NameError) and NC-02
                       fragment idiom (accepted teaching texture) - the
                       2026-09-29 triage split 794 flat findings into
                       4 real module accesses (all fixed) + 790 fragments
    duplicate_heading_scan
                       duplicate headings split by parent context
                       (DH-01 HARD, DH-02 report): same-parent text
                       duplicates are the copy-paste artifact
                       signature - hard, born drained (tick-432
                       parent-context triage: 67/68 classes
                       cross-parent texture, the single same-parent
                       pair 2102 'Solutions' x2 renamed same day);
                       the H2 nav layer rides inside the rule since
                       every H2's parent is the doc H1. DH-02 is the
                       cross-parent per-item texture inventory
                       (Task/Requirements per exercise, Overview/
                       Pros/Cons per database) - accepted, platform
                       TOC generators suffix these slugs
    fence_import_check unresolvable imports in python fences (IC-01,
                       hard gate since tick-325): every import in every
                       ```python fence resolves against the
                       kurulu-stack - generalizes langchain_census
                       from the langchain family to all third-party
                       packages, so a lesson teaching code that raises
                       ModuleNotFoundError as written fails the gate;
                       ast-based (CB-01 owns fence syntax), 4-backtick
                       super-fence teaching content invisible by the
                       fence_class_scan model, relative imports
                       skipped; the tick-323/324 census (429 -> 424)
                       classified into two accepted classes locked in
                       the gate's ACCEPTED_PREFIXES (alternative/
                       optional third-party stacks, lesson-local
                       fragments)
    fm_staleness       curriculum freshness map (report mode): Last Updated
                       age distribution across docs/ - surfaces the oldest
                       material so modernization passes can target it; a
                       stale date is a review queue, not a failure
    ordered_list_scan  Ordered-list integrity (OL-01, hard): a list-marker
                       line carrying 3+ embedded enumeration markers
                       ("1. c, 2. b, 3. c, ...") - a comma-separated key
                       pasted as prose; CommonMark eats the leading marker
                       as the list marker, so the tick-468 census caught
                       all 7 phase-quiz Answer Key blocks rendering as one
                       broken list starting at "c," with every wrapped
                       line opening a new list at 11, 21, ... Drained by
                       escaping 19 line-start markers (1. -> 1\\.); born
                       clean across 408 docs. Sibling classes censused the
                       same tick and left un-gated: HR styles uniform
                       (3003 dash / 0 others), list delimiters uniform
                       (2090 dot / 0 paren), task-list syntax clean,
                       non-1 list starts = 337 deliberate continuation
                       numbering (CommonMark-legal)
    model_form_report  Model-name form consistency (report mode): MF-01
                       space-form checkpoint inside a table row, MF-02
                       hyphen form in flowing prose - the vendor
                       two-form convention (prose "Mistral 7B" vs
                       repo-id Mistral-7B) applied per context; the
                       tick-470 census drained the mismatches and the
                       rule is codified in STYLE-GUIDE Name Forms;
                       birth hits are documented intended uses
                       (concept-definition row, Tech Stack
                       enumeration, capstone download target,
                       full-repo-id parenthetical)
    link_reach_report  Corpus-wide link reachability (report mode):
                       BFS from the root README over .md links; a doc
                       no entry point reaches is stranded content -
                       invisible to browsing and un-crawlable - even
                       when all its own links resolve. Complements
                       NV-01 (in-degree from ONE parent) with global
                       reach. Birth census (tick-471): CHANGELOG.md
                       was the only stranded file of 410; drained via
                       a README Community > Resources row + a [1.2.0]
                       entry that brought the changelog current
    checkpoint_coverage_scan  Phase-checkpoint coverage (CK-00..10,
                       hard): the phase CHECKPOINT.md is the learner's
                       review page for everything above it, so every
                       module group of the phase must appear in its
                       overview line, its text, and as a "### Module
                       NNNN:" section. Born tick-472 after the phase-4
                       drain: the checkpoint still claimed "Modules:
                       2 (4100, 4200)" - the two-module era - while
                       4300 QAT and 4400 Advanced Techniques (17
                       lessons between them) had joined the phase.
                       CK-04/05 tick-478: per-module anatomy - a
                       3-item Checkpoint Quiz and a 3-checkbox
                       hands-on floor (12 modules had no checkbox
                       section, 3 Lab Verification blocks had only
                       2 lab links; all drained same tick).
                       CK-06/07/08 tick-479: Completion Badge
                       anatomy - the criteria block must carry the
                       "All required modules completed" bullet (the
                       platform-tracked criterion), at least 3 plain
                       bullets, no decorated prefixes, Badge line
                       before the criteria (phases 4-7 lacked the
                       modules bullet, phase 2 said "All modules
                       completed", phase 1 was emoji-decorated and
                       Badge-last; all drained same tick).
                       CK-09 tick-480: the review page must carry a
                       "## Common Pitfalls" section of at least 4
                       numbered "**Name:**" items grounded in the
                       phase's own modules (phases 2-7 had none,
                       phase 1 carried generic filler; drained same
                       tick, phase 1's items drawn from its own README
                       pitfalls).
                       CK-10 tick-633: the item numbers inside
                       CK-09's 4-pitfall count are their own
                       1..K run - a gap, duplicate or restart
                       served the review list broken (tick-631
                       partition shape: the count floor stays
                       CK-09's, the numbering inside it is
                       CK-10's; born census 7/7 checkpoints
                       write exact 1..4, born-at-zero)
    lab_anatomy_scan  Lab-file anatomy (LA-01..06, hard): each
                       LAB-*.md carries an "Estimated Time:" claim
                       matching the derived core-path effort
                       (ceil(part-durations/60), challenge/optional
                       headers excluded - convention validated against
                       LAB-006's own 420min -> 7h and LAB-010's
                       330min -> 6h), and a "## ...Completion
                       Checklist" section of at least 3 real "- [ ]"
                       items. Born tick-481 after the same-tick
                       census: LAB-001..005 kept their checklists
                       inside fenced ```text blocks (rendered as
                       code, zero real checkboxes), LAB-006 had no
                       checklist section at all, and 13 labs lacked
                       the Estimated Time line; all drained same tick.
                       LA-04..06 (born tick-485, born-at-zero after the
                       125-header canonization drain): the checklist
                       header is exactly "## Lab Completion Checklist",
                       the overview header exactly "## Lab Overview",
                       and no H1-H4 header starts with an emoji
                       (fence-aware - bash comment lines inside code
                       fences are not headers; LAB-006/010 were already
                       plain, the corpus vote)
    pitfall_shape_scan  Pitfalls item-shape standardization (PS-01..04,
                       hard): every non-checkpoint pitfalls section
                       carries at least 3 structured items in one of
                       the corpus shapes (numbered "N. **Name:**"
                       one-liners, canonical "### Pitfall N: Name"
                       subsections, or the numbered-outline pitfall
                       table), and every in-section "### " subsection
                       is canonical - sequential numbering, no emoji
                       prefix. Fence-aware: bash comment lines inside
                       code fences are not headers. Born tick-482
                       after the same-tick drain: subsection headers
                       in 4 shapes (plain / warning-emoji / x-emoji
                       "Pitfall N:" / canonical) across 18 rich files,
                       and 17 module-group READMEs with thin
                       unnumbered "- **Name**: advice" bullets (83
                       bullets); all canonized same tick. PS-03 born
                       tick-483: in-section bold paragraph labels must
                       be the canonical **Pitfall:** / **Solution:**
                       pair (corpus had **Problem:** x22 and **Fix:**
                       x3 alongside them; 25 labels canonized across
                       6 files same tick, born-at-zero). PS-04 born
                       tick-634: the numbered one-liner items' written
                       numbering must run contiguous 1..K per run -
                       PS-01 reads only the item count (number values
                       dropped at match time), so a gap, duplicate or
                       restart inside a run served the learner a
                       broken numbered review list; born census 17/17
                       one-liner runs across the 36 non-checkpoint
                       sections already 1..K, born-at-zero
    label_variance_scan  Bold-label variance (LV-01..02, hard): the
                       eight canonized callout keys (Estimated Time /
                       What You'll Learn / Best For / Troubleshooting /
                       Requirements / Real-World Example / Verification /
                       Note - all plain Title-case) must use exactly
                       their fixed surface form, and no other
                       emoji/space/case-normalized label key may carry
                       2+ surface forms corpus-wide. Born tick-484
                       after the same-tick drain: census found 8
                       multi-surface keys - 34 minority labels across
                       14 files (lowercase Estimated time x5, What
                       you'll learn x7, Best for x8, emoji-prefixed
                       Troubleshooting/Verification x8 in LAB-000,
                       REQUIREMENTS x2, Real-world example x1, NOTE x3);
                       all renamed to the vote winners, born-at-zero
    quiz_claim_scan  Quiz self-claim integrity (QC-01..05, hard):
                       a QUIZ.md's own promises checked against the
                       bank quiz_export parses - "**N questions**"
                       claims vs the parsed count, the two
                       passing-score line forms' arithmetic, and
                       points-totals vs the derived sum (explicit
                       **Score:** points + 1 per question without
                       one). Born tick-473 after an all-clean census
                       (33 banks; the census's first-pass 2300 hit
                       was the census's own format blindness, not a
                       defect), QC-04 tick-477 (all 33 banks
                       consistent at birth), QC-05 tick-632
                       (pass-line percentage value vs the
                       corpus 80 convention - QC-02/03 own the
                       arithmetic, tick-618 the internal
                       consistency, AS-14 the phase quizzes;
                       born 32 correct-form lines + 2300's
                       points-form line all stating exactly 80)

Plus corpus stats (lesson files / modules / phases) so the scorecard doubles
as a curriculum inventory.

Usage:
    python scripts/qa/quality_report.py [--root REPO_ROOT] [--fail-on-queue]

Exit codes: 0 = all hard gates pass (and queue empty unless --fail-on-queue),
            1 = any hard gate fails (or queue non-empty with --fail-on-queue).
Output is ASCII-escaped so it is safe on cp1254 consoles.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

LESSON_FILE = re.compile(r"^\d{4}-.*\.md$")
MODULE_DIR = re.compile(r"^\d{4}-")
PHASE_DIR = re.compile(r"^phase\d+-")

# (script, label, hard gate?)
GATES = [
    ("frontmatter_lint.py", "frontmatter_lint", True),
    ("doc_id_check.py", "doc_id_check", True),
    ("pip_uv_scan.py", "pip_uv_scan", True),
    ("langchain_census.py", "langchain_census", True),
    ("legacy_chain_scan.py", "legacy_chain_scan", True),
    ("legacy_langgraph_scan.py", "legacy_langgraph_scan", True),
    ("codeblock_syntax_scan.py", "codeblock_syntax_scan", True),
    ("bashblock_syntax_scan.py", "bashblock_syntax_scan", True),
    ("datablock_syntax_scan.py", "datablock_syntax_scan", True),
    ("assessment_lint.py", "assessment_lint", True),
    ("quiz_export.py", "quiz_export", True),
    ("quiz_integrity_scan.py", "quiz_integrity_scan", True),
    ("review_map_check.py", "review_map_check", True),
    ("structure_lint.py", "structure_lint", True),
    ("linkcheck.py", "linkcheck", True),
    ("casecheck.py", "casecheck", True),
    ("anchor_check.py", "anchor_check", True),
    ("table_lint.py", "table_lint", True),
    ("mermaid_lint.py", "mermaid_lint", True),
    ("deprecated_scan.py", "deprecated_scan", True),
    ("unsafe_exec_scan.py", "unsafe_exec_scan", True),
    ("unsafe_deserialize_scan.py", "unsafe_deserialize_scan", True),
    ("unsafe_shell_scan.py", "unsafe_shell_scan", True),
    ("broad_except_scan.py", "broad_except_scan", True),
    ("cypher_interp_scan.py", "cypher_interp_scan", True),
    ("mutable_default_scan.py", "mutable_default_scan", True),
    ("open_encoding_scan.py", "open_encoding_scan", True),
    ("http_timeout_scan.py", "http_timeout_scan", True),
    ("sql_interp_scan.py", "sql_interp_scan", True),
    ("crypto_hygiene_scan.py", "crypto_hygiene_scan", True),
    ("insecure_temp_scan.py", "insecure_temp_scan", True),
    ("cors_wildcard_scan.py", "cors_wildcard_scan", True),
    ("trust_remote_code_scan.py", "trust_remote_code_scan", True),
    ("async_block_scan.py", "async_block_scan", True),
    ("unawaited_coro_scan.py", "unawaited_coro_scan", True),
    ("bare_except_scan.py", "bare_except_scan", True),
    ("secret_shape_scan.py", "secret_shape_scan", True),
    ("md_link_leak_scan.py", "md_link_leak_scan", True),
    ("action_version_scan.py", "action_version_scan", True),
    ("unicode_ws_hygiene_scan.py", "unicode_ws_hygiene_scan", True),
    ("objectives_lint.py", "objectives_lint", False),
    ("fence_namecheck.py", "fence_namecheck", True),
    ("duplicate_heading_scan.py", "duplicate_heading_scan", True),
    ("fence_import_check.py", "fence_import_check", True),
    ("fm_staleness_scan.py", "fm_staleness", False),
    ("kwarg_lint.py", "kwarg_lint", True),
    ("typing_legacy_scan.py", "typing_legacy_scan", True),
    ("version_alignment_scan.py", "version_alignment_scan", True),
    ("feed_parity_check.py", "feed_parity_check", True),
    ("readme_claims_check.py", "readme_claims_check", True),
    ("sitemap_claims_check.py", "sitemap_claims_check", True),
    ("meta_claims_check.py", "meta_claims_check", True),
    ("volume_checklist_scan.py", "volume_checklist_scan", True),
    ("lab_registry_check.py", "lab_registry_check", True),
    ("resource_id_check.py", "resource_id_check", True),
    ("resource_ref_check.py", "resource_ref_check", True),
    ("fence_variant_check.py", "fence_variant_check", True),
    ("fence_variant_check_module.py", "fence_variant_check_module", True),
    ("bash_vars_check.py", "bash_vars_check", True),
    ("uv_install_check.py", "uv_install_check", True),
    ("uv_workflow_census.py", "uv_workflow_census", False),
    ("fence_label_census.py", "fence_label_census", False),
    ("term_consistency_scan.py", "term_consistency_scan", True),
    ("front_matter_census.py", "front_matter_census", True),
    ("tag_vocabulary_census.py", "tag_vocabulary_census", True),
    ("related_census.py", "related_census", True),
    ("estimated_time_census.py", "estimated_time_census", True),
    ("prereq_census.py", "prereq_census", True),
    ("prereq_ordering_scan.py", "prereq_ordering_scan", True),
    ("qa_tooling_coverage_check.py", "qa_tooling_coverage_check", True),
    ("pacing_consistency_census.py", "pacing_consistency_census", False),
    ("difficulty_distribution_scan.py", "difficulty_distribution_scan", False),
    ("prereq_free_text_check.py", "prereq_free_text_check", True),
    ("prereq_target_check.py", "prereq_target_check", True),
    ("nav_coverage_check.py", "nav_coverage_check", True),
    ("last_updated_check.py", "last_updated_check", True),
    ("lesson_order_check.py", "lesson_order_check", True),
    ("toc_coverage_check.py", "toc_coverage_check", True),
    ("render_hygiene_check.py", "render_hygiene_check", True),
    ("status_vocab_check.py", "status_vocab_check", True),
    ("tags_coverage_check.py", "tags_coverage_check", True),
    ("front_matter_scan.py", "front_matter_scan", True),
    ("difficulty_badge_scan.py", "difficulty_badge_scan", True),
    ("difficulty_census.py", "difficulty_census", True),
    ("lesson_anatomy_census.py", "lesson_anatomy_census", True),
    ("closure_census.py", "closure_census", True),
    ("unfinished_marker_scan.py", "unfinished_marker_scan", True),
    ("empty_section_scan.py", "empty_section_scan", True),
    ("emoji_shortcode_scan.py", "emoji_shortcode_scan", True),
    ("fence_label_scan.py", "fence_label_scan", True),
    ("setext_scan.py", "setext_scan", True),
    ("title_h1_parity_scan.py", "title_h1_parity_scan", True),
    ("fence_class_scan.py", "fence_class_scan", True),
    ("lesson_id_scan.py", "lesson_id_scan", True),
    ("heading_scan.py", "heading_scan", True),
    ("table_scan.py", "table_scan", True),
    ("updated_badge_scan.py", "updated_badge_scan", True),
    ("diagram_scan.py", "diagram_scan", True),
    ("link_case_scan.py", "link_case_scan", True),
    ("link_text_scan.py", "link_text_scan", True),
    ("invisible_scan.py", "invisible_scan", True),
    ("line_ending_scan.py", "line_ending_scan", True),
    ("script_hygiene_scan.py", "script_hygiene_scan", True),
    ("filename_scan.py", "filename_scan", True),
    ("frontmatter_value_scan.py", "frontmatter_value_scan", True),
    ("glossary_scan.py", "glossary_scan", True),
    ("emphasis_scan.py", "emphasis_scan", True),
    ("whitespace_scan.py", "whitespace_scan", True),
    ("ordered_list_scan.py", "ordered_list_scan", True),
    ("checkpoint_coverage_scan.py", "checkpoint_coverage_scan", True),
    ("lab_anatomy_scan.py", "lab_anatomy_scan", True),
    ("pitfall_shape_scan.py", "pitfall_shape_scan", True),
    ("label_variance_scan.py", "label_variance_scan", True),
    ("quiz_claim_scan.py", "quiz_claim_scan", True),
    ("fence_exec_gate.py", "fence_exec_gate", True),
    ("census_note_gate.py", "census_note_gate", True),
    ("notebook_unfinished_scan.py", "notebook_unfinished_scan", True),
    ("notebook_catalog_check.py", "notebook_catalog_check", True),
    ("notebook_hygiene_scan.py", "notebook_hygiene_scan", True),
    ("notebook_code_scan.py", "notebook_code_scan", True),
    ("notebook_link_scan.py", "notebook_link_scan", True),
    ("notebook_title_scan.py", "notebook_title_scan", True),
    ("notebook_execution_scan.py", "notebook_execution_scan", True),
    ("notebook_pip_scan.py", "notebook_pip_scan", True),
    ("notebook_mdcell_scan.py", "notebook_mdcell_scan", True),
    ("changelog_summary_check.py", "changelog_summary_check", True),
    ("course_card_check.py", "course_card_check", True),
    ("lab_index_parity_check.py", "lab_index_parity_check", True),
    ("tutorial_index_parity_check.py", "tutorial_index_parity_check", True),
    ("cheatsheet_index_parity_check.py", "cheatsheet_index_parity_check", True),
    ("project_index_parity_check.py", "project_index_parity_check", True),
    ("small_index_parity_check.py", "small_index_parity_check", True),
    ("project_prereq_parity_check.py", "project_prereq_parity_check", True),
    ("fleet_count_parity_check.py", "fleet_count_parity_check", True),
    ("sitemap_listing_parity_check.py", "sitemap_listing_parity_check",
     True),
    ("footer_fm_parity_check.py", "footer_fm_parity_check", True),
    ("module_code_census.py", "module_code_census", True),
    ("label_code_parity_scan.py", "label_code_parity_scan", True),
    ("fence_lang_scan.py", "fence_lang_scan", True),
    ("experiment_id_scan.py", "experiment_id_scan", True),
    ("hierarchy_scan.py", "hierarchy_scan", True),
    ("title_uniqueness_scan.py", "title_uniqueness_scan", True),
    ("gate_robustness_audit.py", "gate_robustness_audit", True),
]


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


QUEUE_SUMMARY = re.compile(r"(\d+) template-objective findings in (\d+) files")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    default_root = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", type=Path, default=default_root,
                        help="repository root (default: %(default)s)")
    parser.add_argument("--fail-on-queue", action="store_true",
                        help="exit 1 while the objectives queue is non-empty")
    args = parser.parse_args()

    phases = sorted(d for d in (args.root / "docs" / "phases").iterdir()
                    if d.is_dir() and PHASE_DIR.match(d.name))
    modules = sorted(d for p in phases for d in p.iterdir()
                     if d.is_dir() and MODULE_DIR.match(d.name))
    lessons = sorted(p for m in modules for p in m.rglob("*.md")
                     if LESSON_FILE.match(p.name))

    print("Minder Academy quality report - %s" % date.today().isoformat())
    print("=" * 72)
    print("corpus: %d lesson files, %d modules, %d phases"
          % (len(lessons), len(modules), len(phases)))
    print()

    failed = False
    queued = False
    for script, label, hard in GATES:
        proc = subprocess.run(
            [sys.executable, str(args.root / "scripts" / "qa" / script),
             "--root", str(args.root)],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        lines = (proc.stdout or "").strip().split("\n")
        summary = next((l for l in reversed(lines)
                        if l.startswith(label)), "no summary line")
        if hard:
            # CI contract: the gate itself decides via its exit code.
            status = "PASS" if proc.returncode == 0 else "FAIL"
            if status == "FAIL":
                failed = True
        else:
            m = QUEUE_SUMMARY.search(summary)
            queued = bool(m and int(m.group(1)) > 0)
            status = "QUEUE" if queued else "PASS"
        print("%-22s %-6s %s" % (label, status, esc(summary)))

    print()
    if failed:
        print("result: FAIL - a hard gate has findings (see its output above)")
    elif queued and args.fail_on_queue:
        print("result: QUEUE - objectives queue still draining (--fail-on-queue)")
    elif queued:
        print("result: PASS - hard gates clean; objectives queue draining "
              "(run objectives_lint.py for the file list)")
    else:
        print("result: PASS - all gates clean")
    return 1 if (failed or (queued and args.fail_on_queue)) else 0


if __name__ == "__main__":
    sys.exit(main())
