#!/usr/bin/env python3
"""course_card_check - the module README course card must not lie about its lessons.

Every module directory carries a README whose front matter Difficulty is the
course card the platform will read as catalog metadata, and six module READMEs
additionally render a "Module Documents" table whose star and time cells are
the per-lesson display layer. Neither surface was gated, so 22 of 33 course
cards floated free of the lessons they summarize - born at commit 775f898's
"universal frontmatter migration" boilerplate and never reconciled: a
3100-attention card reading Beginner while both of its lessons are Advanced
is the course-catalog lie this corpus's own unlock-order law (PQ-07) kills one
level down.

CC-01  README FM Difficulty equals the max tier of its lessons' FM Difficulty
       (Beginner=1 / Intermediate=2 / Advanced=3, the FF-02-proven star map).
       Lessons = module-dir *.md minus README.md minus PREREQUISITES.md (the
       PREREQUISITES doc states entry expectations, not lesson content).
       Skipped when the README carries no FM Difficulty or no lesson carries an
       in-vocabulary tier - FV-07 owns the enum, this gate never double-reports
       another gate's finding.
CC-02  In a Module Documents table row whose target carries an in-vocabulary FM
       Difficulty, the star cell (>=1 U+2B50) must carry exactly TIER_STARS of
       the target tier; a starless cell - including word-form "Advanced" text -
       fires. Out-of-vocabulary or FM-less targets are skipped (FV-07 again).
CC-03  The row's duration cell equals the target FM Estimated Time, compared
       minute-exact (hours*60). When the table header promises a Time column,
       a row with no duration token at all fires (the LI-05 class: a promised
       display column cannot go silently empty); when the target carries no
       parseable FM time, the comparison is skipped.
CC-04  Every lesson basename is linked somewhere in the README (any link form,
       fence-aware) - the CI-01 class: a lesson that exists on disk but is
       invisible from its own module index.
CC-05  Where a Module Documents table exists, every lesson has a row in it
       (extra rows pointing at guides are tolerated display richness; only
       missing lessons fire). Modules without such a table are CC-04 territory.
CC-06  The card's FM Estimated Time exists and equals ceil(sum of lesson FM
       Estimated Time minutes / 60) - the LI-05-proven parts-sum arithmetic
       lifted to course scope. The platform catalog reads one time budget
       per course card, so a card with no FM ET fires (presence clause),
       an unparseable value fires, and a value disagreeing with the
       arithmetic fires. The equality is computed only when every lesson
       carries a parseable FM ET; a lesson-less parse gap is not reported
       here twice.
CC-07  Every lesson carries a parseable FM Estimated Time ('N hours' or
       'N minutes') - the invariant that makes CC-06's equality
       precondition unconditional instead of silently skippable: a
       lesson-side parse gap silently disabled the course-sum check,
       so the gap itself is now the finding, listed per module in the
       CC-04/CC-05 list style.
CC-08  Every module directory is linked from its phase README (any link
       form, fence-aware) - the CC-04 invariant one level up: phase
       pages are the platform's course browse list, so a module that is
       visible from its own module index (CC-04) but absent from its
       phase page is invisible above the cards.
CC-09  A phase README's module links must first appear in ascending
       curriculum order - the browse list order is the unlock order
       (fence-aware; a link with no module-dir component is a lesson
       link and does not enter the order).
CC-10  Every module's PREREQUISITES.md carries at least one internal
       course link (a target ending .md) - the entry page a platform
       renders must offer the learner a clickable way into the
       course, not prose alone.
CC-11  A module README's lesson links must first appear in ascending
       order - the course card's lesson order is the unlock order,
       the CC-09 invariant one level down (fence-aware; non-lesson
       targets never enter the order).
CC-12  The module README must link its own PREREQUISITES.md (any
       link form, fence-aware, resolved against the module dir) -
       the card a platform renders must offer the learner its
       entry door, the CC-10 invariant mirrored inward: the spine
       phase page -> card -> door -> first lesson is only a spine
       if every rung is clickable.
CC-13  Where a PREREQUISITES.md carries an If-YES proceed line,
       the line must carry at least one internal course link and
       every link it carries must resolve inside its own module -
       the proceed line is the learner's 'start here' click, and
       an exit opening into another course is a trap.
CC-14  A phase README's FM Difficulty equals the max tier of its
       module cards' FM Difficulty - the CC-01 invariant one
       level up: the phase header is the course group a
       platform filters and badges by, and a group containing
       an advanced course filters as advanced. Computed only
       when every module card under the phase carries an
       in-vocabulary tier (FS owns the missing name, FV-07 the
       stray value - never double-report).
CC-15  A module's PREREQUISITES.md FM Difficulty equals the course
       card's (README.md) FM Difficulty - the entry door must
       not contradict the card the platform renders beside it
       (one tier per course, mirrored on every surface: lessons
       take the max via CC-01, the phase header the group max
       via CC-14, the entry page the card's own). Computed only
       when both pages carry an in-vocabulary tier (FS owns the
       missing name, FV-07 the stray value - never double-report).
CC-16  A module's PREREQUISITES.md FM carries only the 6-field
       entry-page keyset (Document ID, Title, Last Updated,
       Status, Difficulty, Tags) - one schema for 33 entry
       pages, so a platform parser reads every entry door the
       same way. Negative-excess only: FS owns field presence,
       this clause owns field excess - never double-report.
CC-17  A course card's (README.md) FM carries only the 7-field
       card keyset (the 6 universal fields + Estimated Time) -
       one schema for 33 cards, so a platform parser reads
       every card the same way it reads every entry page
       (CC-16). Negative-excess only: FS owns field presence,
       this clause owns field excess - never double-report.
CC-18  Every lesson's FM carries only the 13-field lesson keyset
       (the 7-field card keyset + Module/Phase + Prerequisites/
       Related + the optional Hardware/Software lab-requirements
       pair) - one family for the 93-lesson surface, so a
       platform parser reads every lesson through one schema the
       same way it reads every entry page (CC-16) and card
       (CC-17). Negative-excess only: FS owns field presence,
       this clause owns field excess - never double-report.
CC-19  Every guide's FM carries only the 11-field guide keyset
       (the 7-field card keyset + Module/Phase + Prerequisites/
       Related - the lesson core without the optional Hardware/
       Software pair) - one family for the 21 enrichment guides,
       so a platform parser reads every guide through the same
       core the lessons live in. Negative-excess only: FS owns
       field presence, this clause owns field excess - never
       double-report.
CC-20  Every assessment bank's FM carries only the 9-field
       assessment keyset (the 6-field entry keyset +
       Estimated Time + Prerequisites/Related - the card
       core without Module/Phase and without the optional
       Hardware/Software pair) - one family for the 66
       PRACTICE/QUIZ banks, so a platform parser reads
       every assessment through one schema. Negative-excess
       only: FS owns field presence, this clause owns
       field excess - never double-report.
CC-21  Every phase README's FM carries only the 6-field
       phase keyset (the same 6-field entry keyset) - one
       family for the 7 phase headers, the course-group
       pages a platform browses by, so a platform parser
       reads every phase header through the same schema
       its entry pages live in. Negative-excess only: FS
       owns field presence, this clause owns field
       excess - never double-report.
CC-22  Every phase-level assessment page's FM carries only
       the 6-field entry keyset - one family for the 14
       phase-practice/phase-quiz pages under 00-META/
       assessment, the phase-completion checkpoints a
       platform renders between one course group and the
       next, so a platform parser reads every phase
       assessment through the same schema its entry
       pages live in. Negative-excess only: FS owns
       field presence, this clause owns field
       excess - never double-report.
CC-23  Every learning-resources reference page's FM
       carries only the 6-field entry keyset - one
       family for the 43 standalone reference pages
       (bridges, case-studies, cheat-sheets, guides,
       interactive, projects, resources,
       troubleshooting), the enrichment layer a platform
       renders beside the curriculum, so a platform
       parser reads every reference page through the
       same schema its entry pages live in. Negative-
       excess only: FS owns field presence, this
       clause owns field excess - never double-report.
CC-24  Every learning-resources tutorial's FM carries
       only the 8-field tutorial keyset (the 6-field
       entry keyset + Estimated Time + Prerequisites)
       - one family for the 15 tutorials under
       learning-resources/tutorials, the hands-on
       walkthroughs a platform renders beside the
       curriculum, so a platform parser reads every
       tutorial through the same schema its entry
       pages live in. Negative-excess only: FS owns
       field presence, this clause owns field
       excess - never double-report.
CC-25  Every learning-resources lab's FM carries
       only the 7-field lab keyset (the card
       keyset: the 6-field entry keyset +
       Estimated Time) - one family for the 15
       hands-on lab docs under learning-resources/
       labs, the executable workshops a platform
       renders beside the curriculum with a time
       budget per lab, so a platform parser reads
       every lab through the same schema its
       course cards live in. Negative-excess
       only: FS owns field presence, this clause
       owns field excess - never double-report.
CC-26  Every SOLUTION-LAB answer key's FM carries
       only the 6-field entry keyset - one family
       for the 15 SOLUTION-LAB-0xx docs under
       learning-resources/labs/solutions, the
       sibling half of the labs tree a platform
       renders as the answer side of every lab,
       so a platform parser reads the whole labs
       tree through one vouched schema. Negative-
       excess only: FS owns field presence, this
       clause owns field excess - never
       double-report.
CC-27  Every 00-META meta page's FM carries
       only the 6-field entry keyset - one family
       for the 20 root-level docs under docs/
       00-META (MASTER-INDEX, SITEMAP, ORGANIZATION-
       GUIDE, QA-TOOLING and the rest of the meta
       surface a platform renders as help,
       navigation and governance beside the
       catalog), so a platform parser reads the
       meta layer through the same schema. Non-
       recursive by design: the phase assessments
       under 00-META/assessment are CC-22 and stay
       outside. Negative-excess only: FS owns
       field presence, this clause owns field
       excess - never double-report.
CC-28  Every volumes page's FM carries
       only the 6-field entry keyset - one family
       for the 7 volume guides under docs/
       volumes (VOLUME-1 through VOLUME-7, the
       book-style spine a platform renders as
       the curriculum's table of contents
       beside the catalog), so a platform
       parser reads the volume layer through
       the same schema. Non-recursive by
       design: the volumes root has no
       subdirectories. Negative-excess only:
       FS owns field presence, this clause
       owns field excess - never double-report.
CC-29  Every phase CHECKPOINT's FM carries
       only the 6-field entry keyset - one family
       for the 7 phase-level completion
       checkpoints under docs/phases/phase*/
       CHECKPOINT.md (the gate a platform
       renders at the boundary between one
       phase's modules and the next), so a
       platform parser reads the checkpoint
       layer through the same schema. Negative-
       excess only: FS owns field presence,
       this clause owns field excess - never
       double-report.

The gate is order-agnostic about table columns (3500-multimodal renders Time
before Difficulty and both orders pass). Dead row targets are skipped here -
linkcheck owns them. Born tick-576 after a 35-finding drain (22 FM cards, 2
body badges that mirrored the drifted FM, 10 star cells, 2 time cells, 1
missing table row); the drain obeys the 11-of-33 modules that already satisfy
CC-01 - the contract is the curated majority's convention, not an invention.
CC-06 born tick-578: the census found 29 of 33 cards carrying no FM Estimated
Time at all and the 4 boilerplate carriers (12/18/28/37 hours, born 775f898)
overshooting every computable source; the drain wrote the ceil lesson sum
into all 33 cards (29 insertions, 4 corrections - every sum whole hours) and
the lock freezes the arithmetic. CC-07 born tick-579 as a zero-drain lock in
the PQ-06 shape: the lesson-level census read 93/93 module lessons clean, so
the precondition CC-06 leans on is frozen as its own invariant. CC-08 born
tick-580 as the second zero-drain lock in the same shape: the census read
all 7 phase READMEs covering all 33 module dirs (the house convention links
lessons inside each module dir from the phase page), so the browse spine
above the cards is frozen too. CC-09 born tick-581 at zero (7/7 phase pages
first-appear ascending); CC-10 born tick-581 after a one-line drain -
3500-multimodal's entry page was the lone PREREQUISITES.md of 33 with no
clickable way into the course (32 siblings linked their first lesson; the
drain wrote the house 'If YES: Start with [3501: ...]' form). CC-11 born
tick-582 at zero - the third zero-drain lock in the PQ-06/CC-08/CC-09
shape: all 93 lesson links across the 33 module READMEs first appear in
ascending order, so the course card's lesson order froze as the unlock
order.
CC-12 born tick-583 at zero - the fourth zero-drain lock in the
PQ-06/CC-08/CC-09/CC-11 shape: all 33 module READMEs already link
their own PREREQUISITES.md (58 door links, every one the plain
'./PREREQUISITES.md' form). CC-13 born the same tick at zero: 24
of 33 entry pages carry an If-YES proceed line, all in the house
'Start with [NNN1: ...](./NNN1-...)' form, all 24 landing inside
their own module - the 9 modules consciously shipping none and
the 26-of-119 / 179-of-534 links that legitimately cross modules
(cross-course next pointers, EXP_* experiments, labs, tutorials)
stayed unlocked by honest census.
CC-14 born tick-584 from the family's first multi-file drift since
576: the census read 4 of 7 phase headers already at their modules'
max tier while phase1-infra, phase2-foundations and phase6-rag sat a
level low (Intermediate headers over Advanced-containing course
groups - revamp-zone residue from modules that arrived advanced),
so the drain bumped exactly those 3 FM lines to Advanced and the
equality froze. The lesson-FM hypotheses died at census before they
became fiction: Tags presence is TG-01..04's, the Difficulty value
is FV-07's, the six FS names own field presence corpus-wide - and
Status read 408/408 'Complete' uniform, parked as an FV-12
candidate rather than a second clause.
CC-15 born tick-585 from the family's largest drift since 576:
the census read 23 of 33 entry pages already mirroring their
card while 10 contradicted it - two directions (5 prereq tiers
below the card, 5 above), hand-written rot rather than a
systematic bias, so the drain set each page's FM Difficulty to
its card's (5 bumps up, 5 down) and coupled 6100-vector's body
badge - the lone entry-page badge still mirroring its old FM -
to the canonical Intermediate form (the tick-584 BD-01 coupling,
pre-censused this time instead of caught by the fleet).
CC-16 born tick-586 after a 20-line drain: the census read 29
of 33 entry pages already on the minimal 6-field keyset while
the 4 phase2 pages carried 5 legacy extras (Module, Phase,
Prerequisites, Related, Estimated Time - a review-range ET and
self-referential 'See module README' prose), so the drain
deleted exactly those 20 FM lines and the keyset froze; the
impact probe moved only prereq_census's statement counters
(docs 204->200, free-text 186->182) - tokens, edges,
tier-edges and the related cycle untouched. The census
honestly killed two hypotheses before they became fiction:
guides/ tier parity (17 of 21 guides are Advanced by design -
depth material, CC-05's display-richness contract) and
prereq-ET parity (review-of-prerequisites time is not course
budget - the tick-579 doctrine).
CC-17 born tick-587 as CC-16's mirror on the card surface:
the corpus-wide FM keyset census read 29 of 33 cards already
on the 7-field majority while the SAME 4 phase2 modules
(2100/2200/2300/2400) carried 4 legacy extras (Module, Phase,
Prerequisites, Related) - the same rot CC-16 drained from
their entry pages one tick earlier, now on the page a
platform renders per course - so the drain deleted exactly
those 16 FM lines and both surfaces froze at one schema;
the impact probe moved only prereq_census's statement
counters (docs 200->196, free-text 182->178) - tokens,
edges, tier-edges and the related cycle untouched - while
front_matter_census FM-05/06 and frontmatter_lint FM-08
stayed silent by design (absence-tolerant: they fire only
when the field exists and contradicts the path). The census
honestly parked the remaining heterogeneity before it
became a rule: guides 12-vs-9 (Module/Phase extras on 9 of
21) is the lesson-family surface, and the lesson class
itself reads 159 files - 93 linked lessons plus the
unlinked assessment/EXP/lab support docs - needing a
classifier split before any lock; meta surfaces
(learning-resources 4 forms, use-cases / industry /
enterprise-solutions singles) stay census-only for now.
CC-18 born tick-588 as the third surface of the FM keyset
family (entry CC-16, card CC-17, lesson CC-18): the tick-588
classifier census split the lesson class honestly and killed
the tick-587 parking hypothesis - the direct module-dir
surface is 93 files and every one of them is linked from its
README (0 unlinked; the tick-587 figure of 159 was a
recursive-slice over-count, recursive reads 180 and the extra
87 live in module subdirectories - labs/assessments support
files, a separate class from the lesson surface). The class
read three forms: 81 on the 11-field core (the 6 universal
+ Estimated Time + Module/Phase + Prerequisites/Related),
6 widening it with the Hardware/Software lab-requirements
pair (the hardware-lab lessons: GPON modem, star topology,
USB passthrough, self-attention deep-dive, GGUF physics,
ReAct system), and 6 missing the Module/Phase navigation
pair (5103, 5203, 5204, 6203, 7302, 7403 - phase5/6/7 rot
from lessons written before the card convention froze).
The lock freezes the family, negative excess only, and the
same-tick normalization drain wrote the derivable
navigation pair into exactly those 6 files (12 lines,
values read off the module dir) so the surface reads two
exact forms - 87 on the core and 6 on the core + the
requirements pair - both inside the declared family.
CC-19 born tick-589 as the fourth surface of the FM keyset
family (entry CC-16, card CC-17, lesson CC-18, guide CC-19):
the guides class was already clean - the tick-589 census
read the 21 module-level guides (docs/phases/*/*/guides/,
all 21 linked from their module READMEs, 0 unlinked) and
two forms - 12 on the 9-field subset (the core without the
Module/Phase navigation pair) and 9 on the full 11-field
core, 0 out of family and no Hardware/Software anywhere -
so the lock froze the 11-field core (negative excess only)
and the same-tick 24-line normalization drain wrote the
derivable pair (values read off the module/phase dir
names) into exactly those 12 files, making the surface one
exact form; the fence coupling the fleet caught at
tick-588 this time caught by the same-tick battery: the 12
guides carry 42 accepted fence rows in accepted_exec_census
(4203 none), the +2 FM shift moved every one, and a
count-asserted re-bless re-blessed the 42 rows at +2 (40
same-class, 2 family-reclassified on re-execution: 3403
RUNNER-CRASH->TIMEOUT, 7103 the recorded
CODE-SIGNAL:RuntimeError FLAKY_FAMILY pair) with their
notes carried, the accepted_exec_census _meta recording
the shift - no fence content changed; the module
subdirectory class also resolved as assessment 66 + guides
21 = 87, the count tick-588 parked.

CC-20 was born tick-590 as the fifth FM-keyset surface (entry
CC-16, card CC-17, lesson CC-18, guide CC-19, assessment
CC-20): the census read 66 banks - every module the
PRACTICE.md/QUIZ.md pair, all 100% linked from their module
READMEs, 0 no-FM - splitting two forms, 64 on the 9-field
assessment keyset (entry 6 + Estimated Time +
Prerequisites/Related) and 2 phase2 legacy carriers widening
with Module/Phase (2300-framework-engineering PRACTICE and
QUIZ), so the drain deleted exactly those 4 FM lines
count-asserted and the family froze at 66/66, with the
impact probe showing all four FM-adjacent gates
byte-identical (FM-05/06 and FM-08 absence-tolerant, prereq
untouched - no Prerequisites/Related line moved) and the
fence coupling one file small: only 2300's PRACTICE.md
carries accepted rows (2 rows / 2 notes - QUIZ none, the
other 37 assessment census entries a different class), the
-2 shift moved both, and the count-asserted re-bless
re-blessed them at their shifted lines 72->70 and 316->314,
same class on re-execution (ENV-GAP:tensorflow, UN-LEAK),
notes carried, the accepted_exec_census _meta recording the
shift - no fence content changed.

CC-21 was born tick-591 as the sixth FM-keyset surface (entry
CC-16, card CC-17, lesson CC-18, guide CC-19, assessment
CC-20, phase header CC-21): the census read the 7 phase
READMEs born-clean - every one already on the exact 6-field
keyset, all 7 linked from MASTER-INDEX, and MASTER-INDEX
itself on the same form - so the lock is a zero-drain one
in the PQ-06/CC-08/09/11/12/13 shape: the course-group
browse surface a platform renders above every card froze
at the family the moment it was named, no drain, no fence
coupling, nothing to probe.

CC-22 was born tick-592 as the seventh FM-keyset surface
(entry CC-16, card CC-17, lesson CC-18, guide CC-19,
assessment CC-20, phase header CC-21, phase assessment
CC-22): the census read the 14 phase-practice/phase-quiz
pages under 00-META/assessment born-clean - every one
already on the exact 6-field entry keyset, all 14 linked
(from MASTER-INDEX, SITEMAP and their phase READMEs) - so
the lock is a zero-drain one in the CC-21 shape: the
phase-completion checkpoint surface a platform renders
between course groups froze at the family the moment it
was named, no drain, no fence coupling, nothing to probe.

CC-23 was born tick-593 as the eighth FM-keyset surface
(entry CC-16, card CC-17, lesson CC-18, guide CC-19,
assessment CC-20, phase header CC-21, phase assessment
CC-22, reference page CC-23): the census read the 43
learning-resources reference pages born-clean - every one
of bridges/case-studies/cheat-sheets/guides/interactive/
projects/resources/troubleshooting already on the exact
6-field entry keyset - while labs (15/15 split between
entry and entry+Estimated Time) and tutorials (13 on the
8-field core, 2 legacy carriers widening with Category
and Related) read different forms and stayed unlocked
this tick, each its own census-first surface. So the
lock is a zero-drain one in the CC-21/CC-22 shape: the
enrichment reference surface a platform renders beside
the curriculum froze at the family the moment it was
named, no drain, no fence coupling, nothing to probe.

CC-24 was born tick-594 as the ninth FM-keyset surface
(entry CC-16, card CC-17, lesson CC-18, guide CC-19,
assessment CC-20, phase header CC-21, phase assessment
CC-22, reference page CC-23, tutorial CC-24): the
tick-593 census parked tutorials as 13 files on the
8-field core with 2 legacy carriers widening with
Category and Related, so the drain deleted exactly
those 4 FM lines count-asserted (TUTORIAL-007's
'Category: Tutorial' - derivable from the directory -
and its Related list, and the same pair on
TUTORIAL-014) and the family froze at 15/15, with the
impact probe showing prereq_census byte-identical
(Related feeds only the related graph, reported never
gated), related_census shrinking honestly to 183 docs
/ 26 tokens / 9 bracketed with RL-01..03 still zero,
linkcheck unchanged (the Related values were bare
tokens, never markdown links) and fence coupling one
file small - TUTORIAL-007 carries 5 accepted
fence rows / 5 notes in accepted_exec_census
(TUTORIAL-014 none), the -2 shift moved all 5,
and the count-asserted re-bless re-blessed them
at the shifted lines 164->162, 208->206,
276->274, 327->325, 389->387, same class on
re-execution, notes carried, no fence content
changed.

CC-25 was born tick-595 as the tenth FM-keyset
surface (entry CC-16, card CC-17, lesson CC-18,
guide CC-19, assessment CC-20, phase header
CC-21, phase assessment CC-22, reference page
CC-23, tutorial CC-24, lab CC-25): the tick-593
census parked the labs tree as a 15/15 split
between entry and entry+Estimated Time with no
majority, and the tick-595 census dissolved the
park structurally - the wide 15 are exactly the
15 LAB-0xx lab docs (every one on the exact
7-field card keyset, every one carrying an
authored 1-12 hour budget) and the minimal 15
are exactly the 15 SOLUTION-LAB-0xx answer keys
under labs/solutions (every one on the exact
6-field entry keyset) - two disjoint sub-
surfaces, each born at 100% uniformity, 0
no-FM, 0 unlinked, so no ET decision exists to
make and the lab half locks zero-drain in the
CC-21/CC-22/CC-23 shape while the solutions
half stays parked for its own clause (CC-26)
next tick; the labs tree carries 58 accepted
fence rows in accepted_exec_census but a
zero-drain lock moves nothing, so nothing to
re-bless.

CC-26 was born tick-596 as the eleventh
FM-keyset surface (entry CC-16, card CC-17,
lesson CC-18, guide CC-19, assessment CC-20,
phase header CC-21, phase assessment CC-22,
reference page CC-23, tutorial CC-24, lab
CC-25, solution CC-26): the tick-595 census
showed the minimal 15 of the labs tree are
exactly the 15 SOLUTION-LAB-0xx answer keys
under labs/solutions, and the tick-596 census
read the class clean - all 15 already on the
exact 6-field entry keyset (Document ID,
Title, Last Updated, Status, Difficulty,
Tags), 0 no-FM, all 15 linked (MASTER-INDEX
and SITEMAP; SOLUTION-LAB-000 also from
ORGANIZATION-GUIDE) - so the lock is a
zero-drain one in the CC-21/CC-22/CC-23 shape:
the answer-key surface froze at the family the
moment it was named, no drain, no fence
coupling (the 58 accepted fence rows live on
the LAB docs, not the solutions), nothing to
probe.

CC-27 was born tick-597 as the twelfth
FM-keyset surface (entry CC-16, card CC-17,
lesson CC-18, guide CC-19, assessment CC-20,
phase header CC-21, phase assessment CC-22,
reference page CC-23, tutorial CC-24, lab
CC-25, solution CC-26, meta page CC-27): the
tick-597 uncovered-surface census read the
rest beyond CC-16..26 as 53 files in four
families - 49 already on the exact 6-field
entry keyset scattered across nine roots
(00-META 20, volumes 7, phase CHECKPOINTs 7,
comparisons 3, industry 3, diagrams 4,
enterprise-solutions 2, use-cases 2,
notebooks 1) and 4 drift carriers (UC-001/002
with Related, IND-003 with Estimated Time,
SOL-002 with Category/Estimated Time/
Prerequisites/Related) - so the largest
single-root family, the 20 root-level
00-META docs, locked first, born-clean: all
20 already on the exact 6-field entry
keyset, 0 no-FM, 0 off-keyset, heavily
cross-linked (SITEMAP from 7 docs, GLOSSARY
from 7, VOLUME-GUIDE from 12) - a zero-drain
lock in the CC-21/CC-22/CC-23 shape, non-
recursive so 00-META/assessment (CC-22)
stays outside, no drain, no fence coupling,
nothing to probe; the remaining exact-6
scatter and the 4 drift carriers park for
their own clauses.

CC-28 was born tick-598 as the thirteenth
FM-keyset surface (entry CC-16, card CC-17,
lesson CC-18, guide CC-19, assessment CC-20,
phase header CC-21, phase assessment CC-22,
reference page CC-23, tutorial CC-24, lab
CC-25, solution CC-26, meta page CC-27,
volume CC-28): the tick-597 uncovered-surface
census had parked the volumes tree among the
exact-6 scatter, and the tick-598 census read
the class clean - all 7 volume guides already
on the exact 6-field entry keyset (Document
ID, Title, Last Updated, Status, Difficulty,
Tags), 0 no-FM, 0 off-keyset, all 7 linked
(SITEMAP, VOLUME-GUIDE and PROGRESS-TRACKER
beside projects and peer volumes) - so the
lock is a zero-drain one in the CC-21/CC-22/
CC-23 shape: the volume surface froze at the
family the moment it was named, no drain,
no fence coupling (the 23 accepted fence
rows live on 6 of the volume docs and
zero-drain moves nothing), nothing to probe;
the phase CHECKPOINTs (7) and the rest of
the exact-6 scatter and the 4 drift
carriers park for their own clauses.

CC-29 was born tick-599 as the fourteenth
FM-keyset surface (entry CC-16, card CC-17,
lesson CC-18, guide CC-19, assessment CC-20,
phase header CC-21, phase assessment CC-22,
reference page CC-23, tutorial CC-24, lab
CC-25, solution CC-26, meta page CC-27,
volume CC-28, checkpoint CC-29): the
tick-597 uncovered-surface census had parked
the phase CHECKPOINTs among the exact-6
scatter, and the tick-599 census read the
class clean - all 7 CHECKPOINT pages already
on the exact 6-field entry keyset (Document
ID, Title, Last Updated, Status, Difficulty,
Tags), 0 no-FM, 0 off-keyset, all 7 linked
(each from its phase README beside
MASTER-INDEX, SITEMAP, ORGANIZATION-GUIDE
and PROGRESS-CHECKPOINTS; linkcheck vouches
0 broken) - so the lock is a zero-drain one
in the CC-21/CC-22/CC-23 shape: the
checkpoint surface froze at the family the
moment it was named, no drain, no fence
coupling (no CHECKPOINT carries accepted
fence rows), nothing to probe; the rest of
the exact-6 scatter (13 files) and the 4
drift carriers park for their own clauses.

CC-30 was born tick-600 as the fifteenth
FM-keyset surface (entry CC-16 through
checkpoint CC-29): the same tick-597 census
had read the six scattered enrichment roots
as 15 clean exact-6 files plus 4 drift
carriers, and the tick-600 census confirmed
the split, then drained the drift -
UC-001/UC-002 lost Related, IND-003 lost
Estimated Time, SOL-002 lost
Category/Estimated Time/Prerequisites/Related
(numeric module references and prose pointers,
no doc links, no fence rows moved,
count-asserted) - leaving all 19 files across
comparisons, diagrams, industry,
enterprise-solutions, use-cases and notebooks
(READMEs included, non-recursive) on the exact
6-field entry keyset, 0 no-FM, 0 off-keyset.

Exit 1 on any finding; prints one line per finding.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path, PurePosixPath

TIER_STARS = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
ENTRY_KEYSET = {
    "Document ID",
    "Title",
    "Last Updated",
    "Status",
    "Difficulty",
    "Tags",
}
CARD_KEYSET = ENTRY_KEYSET | {"Estimated Time"}
LESSON_KEYSET = CARD_KEYSET | {
    "Module",
    "Phase",
    "Prerequisites",
    "Related",
    "Hardware",
    "Software",
}
GUIDE_KEYSET = CARD_KEYSET | {
    "Module",
    "Phase",
    "Prerequisites",
    "Related",
}
ASSESSMENT_KEYSET = ENTRY_KEYSET | {
    "Estimated Time",
    "Prerequisites",
    "Related",
}
# the phase header shares the 6-field entry family - one
# clause each, never double-reported
PHASE_KEYSET = ENTRY_KEYSET
# the phase-level assessment page shares the entry family
# too - its module-level CC-20 sibling carries the 9-field
# bank, but the phase-completion page stays minimal
PHASE_ASSESSMENT_KEYSET = ENTRY_KEYSET
# the learning-resources reference pages share the entry
# family as well - labs and tutorials read other forms
# and stay outside this clause
REFERENCE_KEYSET = ENTRY_KEYSET
REFERENCE_DIRS = (
    "bridges",
    "case-studies",
    "cheat-sheets",
    "guides",
    "interactive",
    "projects",
    "resources",
    "troubleshooting",
)
# the tutorials carry Prerequisites but no Related -
# the 8-field core is the 15-file majority family
# (Category was pure directory noise, drained tick-594)
TUTORIAL_KEYSET = ENTRY_KEYSET | {"Estimated Time", "Prerequisites"}
# the labs tree split 15/15 by structure, not by drift - the
# wide 15 are the LAB docs (7-field card keyset, authored
# time budgets), the minimal 15 the SOLUTION-LAB answer
# keys under labs/solutions (6-field entry, locked CC-26)
LAB_KEYSET = CARD_KEYSET
# the answer keys froze at the 6-field entry keyset the
# tick-596 census read them on - sibling half of the labs
# tree, locked the tick after its LAB counterpart
SOLUTION_KEYSET = ENTRY_KEYSET
# the 00-META meta pages froze at the 6-field entry
# keyset the tick-597 uncovered-surface census read
# them on - help/navigation/governance layer beside
# the catalog; non-recursive, assessment/ is CC-22
META_KEYSET = ENTRY_KEYSET
# the volumes pages froze at the 6-field entry
# keyset the tick-598 census read them on - the
# book-style spine beside the catalog; the root
# has no subdirectories, glob is non-recursive
VOLUME_KEYSET = ENTRY_KEYSET
# the phase CHECKPOINTs froze at the 6-field entry
# keyset the tick-599 census read them on - the
# phase-completion gates between module groups
CHECKPOINT_KEYSET = ENTRY_KEYSET

# the scattered enrichment roots froze at the
# 6-field entry keyset after the tick-600
# drain emptied the four drift carriers -
# comparisons, diagrams, industry,
# enterprise-solutions, use-cases, notebooks
SCATTER_KEYSET = ENTRY_KEYSET
SCATTER_ROOTS = (
    "comparisons", "diagrams", "industry",
    "enterprise-solutions", "use-cases", "notebooks",
)
FM_DASH = re.compile(r"^---\s*$")
FM_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9 _-]*):")
DIFF_FIELD = re.compile(r"^Difficulty:(.*)$")
ET_FIELD = re.compile(r"^Estimated Time:(.*)$")
DUR = re.compile(r"(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minutes?)\b")
LINK = re.compile(r"\]\(([^)]+)\)")
YES_LINE = re.compile(r"\bIf YES\b")
TABLE_HEAD = re.compile(r"^#{1,3} .*Module Documents")
STAR = "\u2b50"  # U+2B50 - SH-01 keeps sources pure ASCII  # U+2B50, the FF-02 house escape - SH-01 keeps sources pure ASCII


def fm_fields(path: Path) -> dict | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or not FM_DASH.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_DASH.match(lines[i]):
            d: dict = {}
            for raw in lines[1:i]:
                m = DIFF_FIELD.match(raw)
                if m:
                    d["diff"] = m.group(1).strip()
                m = ET_FIELD.match(raw)
                if m:
                    d["et"] = m.group(1).strip()
            return d
    return None


def fm_keys(path: Path) -> set[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()
    if not lines or not FM_DASH.match(lines[0]):
        return set()
    for i in range(1, min(len(lines), 40)):
        if FM_DASH.match(lines[i]):
            keys: set[str] = set()
            for raw in lines[1:i]:
                m = FM_KEY.match(raw)
                if m:
                    keys.add(m.group(1))
            return keys
    return set()


def fm_minutes(et: str | None) -> float | None:
    if not et:
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*hours?", et)
    if m:
        return float(m.group(1)) * 60
    m = re.fullmatch(r"(\d+)\s*minutes?", et)
    if m:
        return float(m.group(1))
    return None


def unfenced_lines(text: str) -> list[str]:
    out, fenced = [], False
    for ln in text.splitlines():
        if ln.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(ln)
    return out


def table_rows(lines: list[str]) -> tuple[list[list[str]], bool]:
    """Rows of the Module Documents table plus whether the header has Time."""
    rows: list[list[str]] = []
    header: list[str] | None = None
    in_tbl = False
    for ln in lines:
        if TABLE_HEAD.match(ln):
            in_tbl = True
            header = None
            continue
        if not in_tbl:
            continue
        if re.match(r"^#{1,3} ", ln):
            in_tbl = False
            continue
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if len(cells) == len(header) and set("".join(cells)) <= set("-: "):
            continue  # separator
        if "Document" in " ".join(header) and cells and not cells[0]:
            continue
        rows.append(cells)
    has_time = header is not None and any(
        h.lower().strip() == "time" for h in (header or [])
    )
    return rows, has_time


def cell_minutes(cells: list[str]) -> float | None:
    for c in cells:
        m = DUR.search(c)
        if m:
            v = float(m.group(1))
            return v * 60 if m.group(2).startswith("h") else v
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    findings: list[str] = []

    phases = root / "docs" / "phases"
    for mod in sorted(p for p in phases.glob("phase*/*") if p.is_dir()):
        rm = mod / "README.md"
        if not rm.exists():
            continue
        rel = rm.relative_to(root).as_posix()
        rfm = fm_fields(rm)
        text = rm.read_text(encoding="utf-8")
        lines = unfenced_lines(text)

        lessons = [
            p
            for p in sorted(mod.glob("*.md"))
            if p.name not in ("README.md", "PREREQUISITES.md")
        ]
        ltiers = {}
        letm: dict[str, float] = {}
        lgap: list[str] = []
        for p in lessons:
            f = fm_fields(p)
            if f and f.get("diff") in TIER_STARS:
                ltiers[p.name] = TIER_STARS[f["diff"]]
            lm = fm_minutes(f.get("et")) if f else None
            if lm is not None:
                letm[p.name] = lm
            else:
                lgap.append(p.name)

        # CC-01: card tier == max lesson tier
        if rfm and rfm.get("diff") in TIER_STARS and ltiers:
            want = max(ltiers.values())
            if TIER_STARS[rfm["diff"]] != want:
                findings.append(
                    f"{rel} CC-01 course card FM Difficulty "
                    f"'{rfm['diff']}' != max lesson tier "
                    f"'{[t for t, v in TIER_STARS.items() if v == want][0]}' "
                    f"(lessons: {sorted(ltiers)})"
                )

        # CC-06: card FM Estimated Time present and == ceil(lesson ET sum)
        card_et = (rfm or {}).get("et")
        if card_et is None:
            findings.append(
                f"{rel} CC-06 course card carries no FM Estimated Time "
                f"(the platform catalog reads a time budget per course)"
            )
        else:
            card_m = fm_minutes(card_et)
            if card_m is None:
                findings.append(
                    f"{rel} CC-06 course card FM Estimated Time "
                    f"'{card_et}' is not a parseable hour/minute budget "
                    f"(want 'N hours')"
                )
            elif lessons and len(letm) == len(lessons):
                want_h = math.ceil(sum(letm.values()) / 60)
                if card_m != want_h * 60:
                    findings.append(
                        f"{rel} CC-06 course card FM Estimated Time "
                        f"'{card_et}' != ceil lesson sum "
                        f"({sum(letm.values()):g}min -> {want_h}h)"
                    )

        # CC-07: every lesson carries a parseable FM Estimated Time - the
        # invariant that keeps CC-06's equality precondition unconditional
        if lgap:
            findings.append(
                f"{rel} CC-07 lessons carrying no parseable FM Estimated "
                f"Time (want 'N hours' or 'N minutes' - the budget the "
                f"platform renders per lesson): {lgap}"
            )

        # CC-10: PREREQUISITES.md must offer the learner a way into the
        # course - the entry page a platform renders needs at least one
        # internal course link, not prose alone
        prm = mod / "PREREQUISITES.md"
        if prm.exists():
            pblob = "\n".join(unfenced_lines(prm.read_text(encoding="utf-8")))
            exits = [
                m.group(1)
                for m in LINK.finditer(pblob)
                if m.group(1).endswith(".md")
                and not m.group(1).startswith(
                    ("http://", "https://", "mailto:")
                )
            ]
            if not exits:
                findings.append(
                    f"{prm.relative_to(root).as_posix()} CC-10 "
                    f"PREREQUISITES.md carries no internal course link "
                    f"(the entry page must offer the learner a clickable "
                    f"way into the course)"
                )

        # CC-04: every lesson linked somewhere in the README
        linked = {
            PurePosixPath(m.group(1).split("#")[0]).name
            for m in LINK.finditer("\n".join(lines))
            if not m.group(1).startswith(("http://", "https://"))
        }
        missing = sorted(p.name for p in lessons if p.name not in linked)
        if missing:
            findings.append(
                f"{rel} CC-04 lessons on disk but linked nowhere in the "
                f"README: {missing}"
            )

        # CC-11: lesson links must first appear in ascending order -
        # the course card's lesson order is the unlock order (the
        # CC-09 invariant one level down)
        lorder: list[str] = []
        for m in LINK.finditer("\n".join(lines)):
            tgt = m.group(1).split("#")[0]
            if tgt.startswith(("http://", "https://", "mailto:")):
                continue
            base = PurePosixPath(tgt).name.removesuffix(".md")
            hit = next(
                (p.name for p in lessons if p.stem == base), None
            )
            if hit and hit not in lorder:
                lorder.append(hit)
        lnums = [int(n[:4]) for n in lorder]
        if lnums != sorted(lnums):
            findings.append(
                f"{rel} CC-11 module README lesson links first appear "
                f"out of unlock order - {lorder}"
            )

        # CC-12: the card must offer its entry door - the README
        # links its own PREREQUISITES.md (the CC-10 invariant's
        # mirror: the spine phase page -> card -> door -> lesson
        # is only a spine if every rung is clickable)
        if prm.exists():
            door = any(
                (mod / m.group(1).split("#")[0]).resolve() == prm.resolve()
                for m in LINK.finditer("\n".join(lines))
                if not m.group(1).startswith(
                    ("http://", "https://", "mailto:")
                )
            )
            if not door:
                findings.append(
                    f"{rel} CC-12 module README links its own "
                    f"PREREQUISITES.md nowhere (the card a platform "
                    f"renders must offer the learner its entry door)"
                )

        # CC-13: the If-YES proceed line is the learner's 'start
        # here' click - where it exists it must carry an internal
        # course link and every link it carries must land inside
        # this module (an exit opening into another course is a
        # trap the entry page must never spring)
        if prm.exists():
            pblob = "\n".join(unfenced_lines(prm.read_text(encoding="utf-8")))
            ygap: list[str] = []
            yout: list[str] = []
            for yl in pblob.split("\n"):
                if not YES_LINE.search(yl):
                    continue
                ytg = [
                    m.group(1).split("#")[0]
                    for m in LINK.finditer(yl)
                    if not m.group(1).startswith(
                        ("http://", "https://", "mailto:")
                    )
                ]
                if not ytg:
                    ygap.append(yl.strip()[:80])
                for t in ytg:
                    if (mod / t).resolve().parent != mod.resolve():
                        yout.append(t)
            if ygap:
                findings.append(
                    f"{rel} CC-13 If-YES proceed line carries no "
                    f"internal course link - {ygap}"
                )
            if yout:
                findings.append(
                    f"{rel} CC-13 If-YES proceed line exits the "
                    f"module - {yout}"
                )

        # CC-15: the entry door must not contradict the course
        # card - the PREREQUISITES.md FM Difficulty mirrors the
        # card's own (a platform rendering the entry page beside
        # the card badges the same course twice)
        if prm.exists():
            pfm = fm_fields(prm)
            ctier = rfm.get("diff")
            ptier = (pfm or {}).get("diff")
            if (
                ctier in TIER_STARS
                and ptier in TIER_STARS
                and ptier != ctier
            ):
                findings.append(
                    f"{prm.relative_to(root).as_posix()} CC-15 "
                    f"PREREQUISITES.md FM Difficulty '{ptier}' != "
                    f"card FM Difficulty '{ctier}' (the entry door "
                    f"must not contradict the course card)"
                )

        # CC-16: the entry page carries only the entry-page FM
        # keyset - a platform parsing 33 entry doors expects one
        # schema, not 29 minimal pages and 4 legacy extras (FS
        # owns field presence; this clause owns field excess)
        if prm.exists():
            extra = sorted(fm_keys(prm) - ENTRY_KEYSET)
            if extra:
                findings.append(
                    f"{prm.relative_to(root).as_posix()} CC-16 "
                    f"PREREQUISITES.md FM carries fields outside "
                    f"the entry-page keyset - {', '.join(extra)}"
                )

        # CC-17: the course card carries only the card FM
        # keyset - CC-16's mirror on the card surface: a
        # platform parsing 33 cards expects one schema, not
        # 29 minimal cards and 4 legacy extras (FS owns
        # field presence; this clause owns field excess)
        extra = sorted(fm_keys(rm) - CARD_KEYSET)
        if extra:
            findings.append(
                f"{rm.relative_to(root).as_posix()} CC-17 "
                f"README.md FM carries fields outside the "
                f"card keyset - {', '.join(extra)}"
            )

        # CC-18: every lesson carries only the lesson FM
        # keyset - the card's schema widened by the
        # Module/Phase navigation pair, the Prerequisites/
        # Related link pair and the optional Hardware/
        # Software lab-requirements pair: a platform
        # parsing 93 lessons expects one family, not
        # three forms (FS owns field presence; this
        # clause owns field excess)
        for p in lessons:
            extra = sorted(fm_keys(p) - LESSON_KEYSET)
            if extra:
                findings.append(
                    f"{p.relative_to(root).as_posix()} CC-18 "
                    f"lesson FM carries fields outside the "
                    f"lesson keyset - {', '.join(extra)}"
                )

        # CC-19: every guide carries only the guide FM
        # keyset - the lesson core without the optional
        # Hardware/Software pair: a platform parsing the
        # 21 enrichment guides reads the same 11-field
        # family the lessons live in, not a fourth
        # schema (FS owns field presence; this clause
        # owns field excess)
        for p in sorted(mod.glob("guides/*.md")):
            extra = sorted(fm_keys(p) - GUIDE_KEYSET)
            if extra:
                findings.append(
                    f"{p.relative_to(root).as_posix()} CC-19 "
                    f"guide FM carries fields outside the "
                    f"guide keyset - {', '.join(extra)}"
                )

        # CC-20: every assessment bank carries only the
        # assessment FM keyset - the card core without
        # Module/Phase and without the optional
        # Hardware/Software pair: a platform parsing the
        # 66 PRACTICE/QUIZ banks reads one 9-field family
        # (FS owns field presence; this clause owns
        # field excess)
        for p in sorted(mod.glob("assessment/*.md")):
            extra = sorted(fm_keys(p) - ASSESSMENT_KEYSET)
            if extra:
                findings.append(
                    f"{p.relative_to(root).as_posix()} CC-20 "
                    f"assessment FM carries fields outside the "
                    f"assessment keyset - {', '.join(extra)}"
                )

        # Module Documents table: CC-02/03 per row, CC-05 coverage
        rows, has_time = table_rows(lines)
        if not rows:
            continue
        row_targets: dict[str, list[str]] = {}
        for cells in rows:
            m = LINK.search(cells[0]) if cells else None
            base = PurePosixPath(m.group(1).split("#")[0]).name if m else None
            if base:
                row_targets.setdefault(base, []).append(" | ".join(cells))
            if not m:
                continue
            target = mod / m.group(1)
            if not target.exists():
                continue  # linkcheck's territory
            tfm = fm_fields(target)
            if not tfm:
                continue
            tier = tfm.get("diff")

            # CC-02: star cell count == TIER_STARS[target tier]
            if tier in TIER_STARS:
                star_i = next(
                    (c for c in cells if c.count(STAR) > 0), None
                )
                if star_i is None:
                    findings.append(
                        f"{rel} CC-02 table row for {base} shows no star "
                        f"cell (want {TIER_STARS[tier]} for {tier})"
                    )
                elif star_i.count(STAR) != TIER_STARS[tier]:
                    findings.append(
                        f"{rel} CC-02 table row for {base} shows "
                        f"{star_i.count(STAR)} stars, target FM tier "
                        f"'{tier}' wants {TIER_STARS[tier]}"
                    )

            # CC-03: duration cell == FM Estimated Time (minute-exact)
            fm_m = fm_minutes(tfm.get("et"))
            cell_m = cell_minutes(cells)
            if cell_m is None and has_time:
                findings.append(
                    f"{rel} CC-03 table row for {base} carries no duration "
                    f"but the table promises a Time column (FM ET="
                    f"{tfm.get('et')})"
                )
            elif cell_m is not None and fm_m is not None and cell_m != fm_m:
                findings.append(
                    f"{rel} CC-03 table row for {base} shows "
                    f"{cell_m:g}min, target FM Estimated Time is "
                    f"{tfm.get('et')} ({fm_m:g}min)"
                )

        # CC-05: every lesson has a row in the table
        tbl_miss = sorted(
            p.name
            for p in lessons
            if p.name not in {b for b in row_targets if b}
        )
        if tbl_miss:
            findings.append(
                f"{rel} CC-05 Module Documents table exists but misses "
                f"lessons: {tbl_miss}"
            )

    # CC-08: every module is linked from its phase README - the CC-04
    # invariant one level up: a module invisible from its phase page is
    # invisible from the platform's course browse list
    for ph in sorted(p for p in phases.glob("phase*") if p.is_dir()):
        prm = ph / "README.md"
        if not prm.exists():
            continue
        prel = prm.relative_to(root).as_posix()

        # CC-21: the phase header carries only the entry
        # FM keyset - the course-group page a platform
        # browses by reads the same 6-field family the
        # entry pages live in, not a sixth schema (FS
        # owns field presence; this clause owns
        # field excess)
        extra = sorted(fm_keys(prm) - PHASE_KEYSET)
        if extra:
            findings.append(
                f"{prel} CC-21 phase-header FM carries fields "
                f"outside the phase keyset - {', '.join(extra)}"
            )

        blob = "\n".join(unfenced_lines(prm.read_text(encoding="utf-8")))
        targets = [
            m.group(1).split("#")[0]
            for m in LINK.finditer(blob)
            if not m.group(1).startswith(("http://", "https://"))
        ]
        here = sorted(d.name for d in ph.iterdir() if d.is_dir())
        ghost = [mn for mn in here if not any(mn in t for t in targets)]
        if ghost:
            findings.append(
                f"{prel} CC-08 modules on disk but linked nowhere in "
                f"the phase index (the CC-04 invariant one level up - "
                f"this page is the platform's course browse list): "
                f"{ghost}"
            )

        # CC-09: the phase page's module links must first appear in
        # ascending curriculum order - the browse list order is the
        # unlock order (a link with no module-dir component is a
        # lesson link and does not enter the order)
        order: list[int] = []
        for t in targets:
            dm = re.search(r"(?<!\d)(\d{4})-[a-z0-9-]+(?:/|$)", t)
            if dm:
                n = int(dm.group(1))
                if n not in order:
                    order.append(n)
        if order != sorted(order):
            findings.append(
                f"{prel} CC-09 phase page browse order is not the "
                f"unlock order - module links first appear as {order}, "
                f"want ascending {sorted(order)}"
            )

        # CC-14: the phase page's FM Difficulty equals the max tier of
        # its module cards - the CC-01 invariant one level up: the
        # phase header is the course group a platform filters and
        # badges by, and a group containing an advanced course
        # filters as advanced (computed only when every module card
        # carries an in-vocabulary tier - FS/FV own the missing or
        # stray value, this gate never double-reports)
        mdirs = [
            d for d in sorted(ph.iterdir())
            if d.is_dir() and (d / "README.md").exists()
        ]
        ctiers = [
            TIER_STARS[c]
            for c in ((fm_fields(d / "README.md") or {}).get("diff")
                      for d in mdirs)
            if c in TIER_STARS
        ]
        pfm = fm_fields(prm)
        if (pfm and pfm.get("diff") in TIER_STARS and mdirs
                and len(ctiers) == len(mdirs)):
            want = max(ctiers)
            if TIER_STARS[pfm["diff"]] != want:
                findings.append(
                    f"{prel} CC-14 phase page FM Difficulty "
                    f"'{pfm['diff']}' != max module-card tier "
                    f"'{[t for t, v in TIER_STARS.items() if v == want][0]}' "
                    f"(the CC-01 invariant one level up - a group "
                    f"containing an advanced course filters as advanced)"
                )

    # CC-22: the phase-level assessment pages carry only
    # the entry FM keyset - the phase-completion
    # checkpoints a platform renders between course
    # groups read the same 6-field family the entry
    # pages live in (their module-level CC-20 siblings
    # carry the 9-field bank; these pages stay minimal)
    pa_dir = root / "docs" / "00-META" / "assessment"
    for pap in sorted(pa_dir.glob("*.md")):
        prel = pap.relative_to(root).as_posix()
        extra = sorted(fm_keys(pap) - PHASE_ASSESSMENT_KEYSET)
        if extra:
            findings.append(
                f"{prel} CC-22 phase-assessment FM carries fields "
                f"outside the phase-assessment keyset - "
                f"{', '.join(extra)}"
            )

    # CC-23: the learning-resources reference pages carry
    # only the entry FM keyset - the enrichment layer a
    # platform renders beside the curriculum reads the
    # same 6-field family the entry pages live in
    # (labs and tutorials read other forms and stay
    # outside this clause)
    lr_dir = root / "docs" / "learning-resources"
    for dname in REFERENCE_DIRS:
        for rp in sorted((lr_dir / dname).rglob("*.md")):
            rrel = rp.relative_to(root).as_posix()
            extra = sorted(fm_keys(rp) - REFERENCE_KEYSET)
            if extra:
                findings.append(
                    f"{rrel} CC-23 reference-page FM carries "
                    f"fields outside the reference keyset - "
                    f"{', '.join(extra)}"
                )

    # CC-24: the learning-resources tutorials carry only
    # the 8-field tutorial keyset (entry + Estimated
    # Time + Prerequisites) - the hands-on walkthrough
    # surface a platform renders beside the curriculum
    # (labs read other forms and stay outside this
    # clause)
    for tp in sorted(
        (root / "docs" / "learning-resources" / "tutorials").rglob("*.md")
    ):
        trel = tp.relative_to(root).as_posix()
        extra = sorted(fm_keys(tp) - TUTORIAL_KEYSET)
        if extra:
            findings.append(
                f"{trel} CC-24 tutorial FM carries fields "
                f"outside the tutorial keyset - "
                f"{', '.join(extra)}"
            )

    # CC-25: the learning-resources labs carry only the
    # 7-field lab keyset (the card keyset) - the
    # executable workshops a platform renders beside
    # the curriculum; non-recursive on purpose, the
    # SOLUTION-LAB answer keys under labs/solutions
    # read the 6-field entry keyset under CC-26
    for lp in sorted(
        (root / "docs" / "learning-resources" / "labs").glob("*.md")
    ):
        lrel = lp.relative_to(root).as_posix()
        extra = sorted(fm_keys(lp) - LAB_KEYSET)
        if extra:
            findings.append(
                f"{lrel} CC-25 lab FM carries fields "
                f"outside the lab keyset - "
                f"{', '.join(extra)}"
            )

    # CC-26: the SOLUTION-LAB answer keys carry only
    # the 6-field entry keyset - the sibling half
    # of the labs tree a platform renders as the
    # answer side of every lab; zero-drain lock in
    # the CC-23 shape (the 58 accepted fence rows
    # live on the LAB docs, not here)
    for sp in sorted(
        (root / "docs" / "learning-resources" / "labs" / "solutions").glob("*.md")
    ):
        srel = sp.relative_to(root).as_posix()
        extra = sorted(fm_keys(sp) - SOLUTION_KEYSET)
        if extra:
            findings.append(
                f"{srel} CC-26 solution FM carries fields "
                f"outside the solution keyset - "
                f"{', '.join(extra)}"
            )

    # CC-27: the 00-META meta pages carry only the
    # 6-field entry keyset - help, navigation and
    # governance a platform renders beside the
    # catalog; non-recursive, the phase
    # assessments under 00-META/assessment are
    # CC-22 and stay outside this clause
    for mp in sorted((root / "docs" / "00-META").glob("*.md")):
        mrel = mp.relative_to(root).as_posix()
        extra = sorted(fm_keys(mp) - META_KEYSET)
        if extra:
            findings.append(
                f"{mrel} CC-27 meta FM carries fields "
                f"outside the meta keyset - "
                f"{', '.join(extra)}"
            )

    # CC-28: the volumes pages carry only the
    # 6-field entry keyset - the book-style
    # spine a platform renders as the
    # curriculum's table of contents;
    # non-recursive, the root has no
    # subdirectories
    for vp in sorted((root / "docs" / "volumes").glob("*.md")):
        vrel = vp.relative_to(root).as_posix()
        extra = sorted(fm_keys(vp) - VOLUME_KEYSET)
        if extra:
            findings.append(
                f"{vrel} CC-28 volume FM carries fields "
                f"outside the volume keyset - "
                f"{', '.join(extra)}"
            )

    # CC-29: the phase CHECKPOINTs carry only the
    # 6-field entry keyset - the phase-completion
    # gates a platform renders between one
    # phase's modules and the next
    for cp in sorted((root / "docs" / "phases").glob("phase*/CHECKPOINT.md")):
        crel = cp.relative_to(root).as_posix()
        extra = sorted(fm_keys(cp) - CHECKPOINT_KEYSET)
        if extra:
            findings.append(
                f"{crel} CC-29 checkpoint FM carries fields "
                f"outside the checkpoint keyset - "
                f"{', '.join(extra)}"
            )

    # CC-30: the scattered enrichment roots carry
    # only the 6-field entry keyset - comparisons,
    # diagrams, industry, enterprise-solutions,
    # use-cases, notebooks (READMEs included,
    # non-recursive)
    for sroot in SCATTER_ROOTS:
        for sp in sorted((root / "docs" / sroot).glob("*.md")):
            srel = sp.relative_to(root).as_posix()
            extra = sorted(fm_keys(sp) - SCATTER_KEYSET)
            if extra:
                findings.append(
                    f"{srel} CC-30 scattered-root FM carries "
                    f"fields outside the entry keyset - "
                    f"{', '.join(extra)}"
                )

    for f in findings:
        print(f)
    if findings:
        print(
            f"course_card_check: {len(findings)} finding(s)",
            file=sys.stderr,
        )
        return 1
    print("course_card_check: 0 findings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
