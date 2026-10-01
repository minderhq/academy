#!/usr/bin/env python3
"""One-command quality scorecard for the PROJECT-OMEGA curriculum corpus.

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
    assessment_lint    assessment/QUIZ.md + PRACTICE.md coverage (AS-01..AS-12;
                       AS-09 option-shuffle queue is report-mode, shown
                       separately; AS-10 option uniformity - a question
                       carrying options carries exactly A-D, born tick-498
                       born-at-zero 655/655 four-option mcq; AS-11 answer-key
                       rows carry a filled explanation cell, born tick-514
                       born-at-zero after the 33/33-bank explanation drain;
                       AS-12 review maps must exist-consistently cite and
                       fully cover the bank's questions, applied where the
                       map exists, coverage grows with the review-map drain)
    quiz_export        quiz bank parses into complete question records
    quiz_integrity_scan
                       content-level quiz integrity (QI-01..06 +
                       QI-08/09 + QI-11/12/13 hard: self-referential positional
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
                       QI-13 tick-475, QI-14 tick-476,
                       baseline 0) on top of
                       quiz_export's parser; QI-07/QI-10
                       are the report inventory (the
                       skewed-answer-key shuffle queue that
                       refines AS-09's 70% tripwire + the
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
                       browse graph; README/TEMPLATE/CHANGELOG exempt)
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
                       5.x; use token=); comment-only mentions are
                       not findings
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
                       runs manifest_export + quiz_export for real and
                       locks their invariants (FP-00..FP-07: module
                       sets, counts vs arrays, hierarchy vs documents
                       lessons, quiz-file membership, bank-internal
                       totals, assessment.quiz flags, manifest vs the
                       on-disk docs/*.md tree) - consistency only,
                       content totals stay the living baseline
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
    prereq_census Prerequisites chain integrity (PQ-01..03, hard):
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
                       authoring-stage pointers
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
                      Badge parity (DB-01, hard): where a doc
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
                      FM VALUE contracts (FV-01..11,
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
                      allowlist)
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
                      hardens at 0 (exit 0 by design, the AS-09
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
                       rows and 0 findings
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
    checkpoint_coverage_scan  Phase-checkpoint coverage (CK-00..09,
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
                       pitfalls)
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
    pitfall_shape_scan  Pitfalls item-shape standardization (PS-01..03,
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
                       6 files same tick, born-at-zero)
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
    quiz_claim_scan  Quiz self-claim integrity (QC-01..04, hard):
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
                       consistent at birth)

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

    print("PROJECT-OMEGA quality report - %s" % date.today().isoformat())
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
            # CI contract: the gate itself decides via its exit code
            # (queued items like AS-09 exit 0 by design).
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
