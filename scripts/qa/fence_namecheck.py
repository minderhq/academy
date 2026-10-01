#!/usr/bin/env python3
"""undefined-name gate for python fences (hard since tick-531).

Syntax gates prove a fence parses, the import gate proves its imports
resolve, but neither proves the code's names resolve - a typo or a
helper called before the fence that defines it is a NameError the
learner hits on the first run. This gate grew through two designs on
the same dimension:

- 2026-09-29 triage (report mode): a document-wide bound set sorted
  unbound loads into NC-01 module-access-without-import (certain
  NameError, the only signal kept) and NC-02 fragment idiom (accepted
  teaching texture). Lenient by design: 794 findings / 99 files could
  not be drained, so usage-before-setup was accepted wholesale.
- tick-531 census lock (this gate): pyflakes supplies per-fence scoped
  analysis, the corpus's lesson-flow convention (fences share state
  top-to-bottom in one file) is applied as a SEQUENTIAL bound set -
  earlier fences only, so usage-before-setup stops being free - and
  the whole residual queue is locked as ACCEPTED_CENSUS. Anything
  outside the census is a NEW undefined name: it prints, the run
  exits 1. The strictness the first triage wanted became shippable
  the moment the census technique arrived.

UN-01  undefined name - not bound by this fence, any earlier fence in
       the file, or a builtin
UN-02  local referenced before assignment in an enclosing scope

Design, shared with fence_import_check:
- the fence universe is codeblock_syntax_scan's exactly (exact ```
  / ~~~ markers, python/py/python3 labels, textwrap.dedent before
  parsing), so every fence gate sees the same blocks
- per-fence pyflakes check carries proper Python scoping, so a name
  bound only inside a function is correctly NOT bound for module-level
  code - flagging that use is right, it is a NameError as written
- cross-fence state: module-level bindings of every earlier fence in
  the file (targets, imports, def/class, with/for/handler/except and
  match-capture names, conditional bodies included; function and class
  bodies excluded - their binds are local, and using one globally is
  itself a NameError) feed the bound set for later fences
- a star import makes the file opaque from that fence on - its
  namespace is unknowable, so later fences stop being flagged rather
  than flood the census with false positives
- unparseable fences are counted, not findings: CB-01 (fence syntax,
  baseline 0) owns that dimension

The census was locked at birth: 1027 line findings across 106 files
(651 distinct file+name pairs after dedup) audited by class - every
entry is one of the corpus's established conventions (prose-bound
placeholders like model/query/x/ACC, cross-lesson class references
like QdrantCollection/RMSNorm/Agent, signature-less method-body
fragments using self, credential placeholders like YOUR_CLIENT_ID,
third-party libraries used without boilerplate imports in excerpt
fences like torch/np). One signature-bearing defect was fixed instead
of accepted: phase3 README's forward_with_checkpointing promised a
runnable function but used self.attention/self.ffn. Drain census
entries opportunistically by editing content, then deleting the pair.

Run over the whole corpus:
    python scripts/qa/fence_namecheck.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
import textwrap
from pathlib import Path

from pyflakes.api import check

FENCE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")
PYTHON_LANGS = ("python", "py", "python3")
UNDEFINED_CLASSES = ("UndefinedName", "UndefinedLocal")

# Census locked at birth (tick-531). Anything outside this census is a
# NEW undefined name and fails the gate.
ACCEPTED_CENSUS = """\
docs/00-META/ENVIRONMENT-SETUP.md: model
docs/00-META/STYLE-GUIDE.md: SpecificError input_data logger process_data risky_operation
docs/00-META/assessment/phase6-practice.md: np
docs/00-META/assessment/phase7-practice.md: llm llm_client
docs/comparisons/CP-001-RAG-vs-FineTuning-vs-Agents.md: Agent calculator_function call_api database_function database_query docs load_dataset load_finetuned_model rag_search search_function web_search your_dataset your_documents your_func
docs/industry/IND-001-Healthcare-AI-Applications.md: DeIdentifier DocumentationAgent Encryption RoutingAgent SymptomAnalysisAgent ai_model all_metric_pass calculate_accuracy calculate_confidence calculate_sensitivity calculate_specificity check_data_completeness clinical_ai_app clinical_cases clinician_review cross_validate deploy deploy_with_rollback evaluate explain_alternatives_rejection external_validation extract_history_contributions extract_lab_contributions extract_symptom_contributions get_recent_clinical_cases independent_dataset is_grounded is_monthly_update is_quarterly_update llm log_update log_warning measure_sensitivity measure_specificity medical_db model normalize_labs normalize_vitals patient_name prospective_study pubmed real_clinics retrain_with_new_data retrieve_evidence sample_predictions schedule_retraining ssn symptoms test_set train_data training_data validate_clinically vector_db
docs/industry/IND-002-Finance-AI-Applications.md: DataQualityError QdrantCollection QuantizedEmbedder RegulatoryComplianceError SentenceTransformer TransactionEmbedder add_source_citations ai_model audit_trail calculate_technicals calculate_trend combine_signals compliance_checker create_audit_trail deploy deploy_model evaluate_model execute_trades extract_business_overview extract_controls extract_financial_numbers extract_financials extract_risk_factors fetch_stock_data finance_embedder finbert fine_tuned_llm fulltext_search generate_certifications generate_with_sources get_confirmed_fraud_cases get_financial_news get_market_data get_predictions get_recent_data handle_outliers historical_data is_calculated_value llm load_latest_model load_template log_error log_info log_warning model np position_checker reciprocal_rank_fusion retrain_model train_model validate_financial_data validate_model validate_regulatory_requirements vector_db
docs/industry/IND-003-Manufacturing-AI.md: grab_frame live_metrics maintenance quality_inspection send_alert sensor_windows twin
docs/learning-resources/bridges/TUTORIAL-TO-LAB-BRIDGE.md: APIError add_lora_layer api base_model data logger
docs/learning-resources/case-studies/REAL-WORLD-EXAMPLES.md: ClinicalGuidelines CodeReviewAgent ConsensusAgent DiagnosticAgent GraphRAGAgent GuidelineAgent LiteratureSearchAgent Neo4jStore NewsSearchTool PerformanceAgent PubMed RiskAssessmentAgent SECFilingTool SecurityAgent SequentialWorkflow StyleAgent SummaryAgent SupplyChainMapperTool YahooFinanceTool
docs/learning-resources/cheat-sheets/CHEAT-SHEET-002-Python-AI.md: complex_function data dataloader df1 df2 e process
docs/learning-resources/cheat-sheets/CHEAT-SHEET-005-RAG-Systems.md: bm25_results docs embedding_model keyword_results markdown_text queries query query_embedding text vector_results
docs/learning-resources/cheat-sheets/QUICK-REF-VOLUME-2.md: batch_A batch_B criterion dataloader extract_choice format_mmlu_prompt input_tensor model optimizer target
docs/learning-resources/cheat-sheets/QUICK-REF-VOLUME-4.md: compute_scales_zero_points in_features out_features quantize_per_channel
docs/learning-resources/cheat-sheets/QUICK-REF-VOLUME-5.md: AutoModelForCausalLM dataloader format_instruction optimizer
docs/learning-resources/cheat-sheets/QUICK-REF-VOLUME-7.md: AnalystAgent CriticAgent ResearcherAgent WriterAgent generate_response search_tool
docs/learning-resources/guides/GUIDE-INTERVIEW.md: softmax
docs/learning-resources/interactive/FLASHCARDS.md: my_lora_layer
docs/learning-resources/labs/LAB-005-GraphRAG.md: text_lower
docs/learning-resources/labs/LAB-012-Audio-AI.md: whisper
docs/learning-resources/labs/solutions/SOLUTION-LAB-002-RAG-Implementation.md: vector_store
docs/learning-resources/labs/solutions/SOLUTION-LAB-004-ReAct-Agent.md: llm
docs/learning-resources/labs/solutions/SOLUTION-LAB-006-Train-Model-From-Scratch.md: Path
docs/learning-resources/labs/solutions/SOLUTION-LAB-007-Production-RAG.md: EmbeddingService OllamaLLM
docs/learning-resources/projects/PROJECT-007-Production-AI-System.md: WebSocketDisconnect stream_response streaming_service
docs/learning-resources/projects/templates/TEMPLATE-004-Agent-Framework.md: critic researcher writer
docs/learning-resources/projects/templates/TEMPLATE-005-Model-Quantization.md: calibration_dataset model
docs/learning-resources/projects/templates/TEMPLATE-006-Synthetic-Data-Generator.md: original_data question_list raw_data
docs/learning-resources/projects/templates/TEMPLATE-007-LLM-Evaluation-Benchmark.md: answer_checker question_list
docs/learning-resources/projects/templates/TEMPLATE-009-Model-Deployment.md: GenerationRequest model model_config request
docs/learning-resources/projects/templates/TEMPLATE-010-Chatbot-UI.md: ChatRequest StreamingResponse llm_service memory_service
docs/learning-resources/projects/templates/TEMPLATE-011-Model-Merging-MoE.md: calibration_dataset dataset input_tensor model router_outputs
docs/learning-resources/projects/templates/TEMPLATE-012-End-to-End-LLM-Pipeline.md: FormatConverter config data_config gpu_usage latency splitter test_data throughput
docs/learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md: DocumentChunker adapter_path model_name prompts qdrant query results torch vector
docs/learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md: keyword_search
docs/notebooks/README.md: model
docs/phases/phase1-infra/1200-virtualization/1204-Multi-GPU-Setup.md: MyModel criterion dataloader input_data train_dataset
docs/phases/phase1-infra/1500-monitoring/assessment/PRACTICE.md: detokenize generate tokenize
docs/phases/phase2-foundations/2300-framework-engineering/2301-Framework-Design-Patterns.md: MyModel predictions targets
docs/phases/phase2-foundations/README.md: A B Model a b criterion dataloader f1 f2 local_rank model optimizer target weights
docs/phases/phase3-transformers/3100-attention/3102-Flash-Attention.md: torch
docs/phases/phase3-transformers/3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md: math positional_encoding token_embeddings torch
docs/phases/phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md: load_legal_corpus load_tokenizer model test_texts
docs/phases/phase3-transformers/3300-decoding/3302-Normalization-Layers.md: FeedForward MultiHeadAttention torch x
docs/phases/phase3-transformers/3300-decoding/guides/3303-Activation-Function-Comparison.md: x
docs/phases/phase3-transformers/3400-architectures/3402-Decoder-Only-Models.md: CausalSelfAttention RMSNorm SlidingWindowAttention SwiGLUFFN
docs/phases/phase3-transformers/3400-architectures/README.md: CausalSelfAttention CrossAttention FeedForward LayerNorm RMSNorm SelfAttention SwiGLU
docs/phases/phase3-transformers/3400-architectures/guides/3403-Model-Architecture-Comparison.md: long_article qdrant torch
docs/phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md: indexed_images
docs/phases/phase3-transformers/3500-multimodal/3502-Audio-Models.md: _write_temp
docs/phases/phase3-transformers/3500-multimodal/README.md: encode_base64
docs/phases/phase3-transformers/README.md: AutoTokenizer K Q V apply_rotary_emb d seq_len softmax sqrt
docs/phases/phase4-quantization/4100-low-bit/4102-EXL2-and-AWQ.md: quantize_4bit
docs/phases/phase4-quantization/4100-low-bit/4103-Double-Quantization.md: pack_4bit
docs/phases/phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md: inputs torch
docs/phases/phase4-quantization/4200-kv-cache/4202-Speculative-Decoding.md: generate_sequence
docs/phases/phase4-quantization/4300-quantization-aware-training/4301-QAT-Foundations.md: enable_quantization model num_epochs train_epoch
docs/phases/phase4-quantization/4300-quantization-aware-training/4302-Fake-Quantization.md: MyModel dataloader inputs scale torch train_epoch weight
docs/phases/phase4-quantization/4300-quantization-aware-training/4303-QAT-for-Transformers.md: attn dequantize epoch fake_quantize gelu k layer_norm model optimizer q qat_start_epoch scores self softmax train_epoch v val_loader validate weight x
docs/phases/phase4-quantization/4300-quantization-aware-training/4304-Low-bit-QAT.md: dataloader load_student_model load_teacher_model train_epoch
docs/phases/phase4-quantization/4300-quantization-aware-training/4305-Quantization-Configuration.md: disable_quantization_for_layer enable_quantization_for_layer evaluate evaluate_with_config fake_quantize get_quantizable_layers impact_on_accuracy model
docs/phases/phase4-quantization/4300-quantization-aware-training/guides/4306-PyTorch-QAT.md: train_epoch train_loader
docs/phases/phase4-quantization/4300-quantization-aware-training/guides/4307-Transformers-QAT.md: epoch eval_dataset inputs model_fp32 optimizer qat_start_epoch test_dataloader train_dataset
docs/phases/phase4-quantization/4300-quantization-aware-training/guides/4308-BitBlade-QAT.md: HybridConfig calibration_dataloader dataloader get_calibration_dataloader test_loader train_dataset train_epoch
docs/phases/phase4-quantization/4400-advanced-techniques/4402-AWQ.md: calibration_texts convert_to_gptq_format
docs/phases/phase4-quantization/4400-advanced-techniques/4405-Sparsity-Quantization.md: linear
docs/phases/phase4-quantization/4400-advanced-techniques/guides/4408-Quantizing-for-Production.md: tokenizer
docs/phases/phase4-quantization/README.md: load_model load_target_domain_samples quantize random_tokens representative_dataset speculative_decode
docs/phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md: TaskType base_model get_peft_model llama_model trainer
docs/phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md: Trainer train_dataset
docs/phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md: base_model instruction_dataset policy_model preference_dataset prompt_dataset reference_model sft_model value_model
docs/phases/phase5-finetuning/5200-alignment/5204-Preference-Dataset-Creation.md: annotator_a_labels annotator_b_labels generate parse_choice prompt
docs/phases/phase5-finetuning/5300-synthetic/5301-Knowledge-Distillation.md: dataloader student_acc student_hidden_states student_probs teacher_a teacher_acc teacher_b teacher_hidden_states teacher_probs
docs/phases/phase5-finetuning/5300-synthetic/5303-Federated-Learning.md: E build_model test train
docs/phases/phase5-finetuning/5300-synthetic/assessment/PRACTICE.md: code
docs/phases/phase5-finetuning/5400-distributed-training/5401-Data-Parallelism.md: ACC build_model ddp_model nullcontext optimizer step train_dataset
docs/phases/phase5-finetuning/5400-distributed-training/5402-Model-Parallelism.md: batch model
docs/phases/phase5-finetuning/5400-distributed-training/5403-Mixed-Precision.md: build_model criterion loader optimizer x y
docs/phases/phase5-finetuning/5400-distributed-training/assessment/PRACTICE.md: LargeModel MyModel criterion epochs train_dataset
docs/phases/phase5-finetuning/5500-advanced-optimization/5501-Optimizer-Variants.md: loader model total_steps
docs/phases/phase5-finetuning/5500-advanced-optimization/5502-Learning-Rate-Scheduling.md: loader model num_epochs train_dataloader
docs/phases/phase5-finetuning/5500-advanced-optimization/5503-Advanced-Techniques.md: criterion loader loss model optimizer scaler scheduler
docs/phases/phase5-finetuning/README.md: Adam Trainer TrainingArguments batch_size epochs evaluate large_dataset lora_params pretrained_params small_dataset test_data train train_data train_dataset val_data
docs/phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md: semantic_model
docs/phases/phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md: CrossEncoderReranker HybridSearch bm25 corpus llm_client reciprocal_rank_fusion
docs/phases/phase6-rag/6200-retrieval/6203-Advanced-Retrieval.md: cos rel split_sentences
docs/phases/phase6-rag/6300-context/6301-Neo4j-and-Knowledge-Graphs.md: G
docs/phases/phase6-rag/6300-context/6302-CAG-Long-Context-Architectures.md: content
docs/phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md: chunked_docs embedding_384d query_embedding query_embedding_384d
docs/phases/phase6-rag/6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md: query_vector
docs/phases/phase6-rag/README.md: HNSWIndex SentenceTransformer chunk_text cross_encoder_rerank generate_with_citations openai_embed sentence_transformers_embed text texts vector_db
docs/phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md: Plan
docs/phases/phase7-agentic/7100-architecture/7102-Planning-Decomposition.md: ReActAgent
docs/phases/phase7-agentic/7100-architecture/guides/7103-ReAct-Implementation-Guide.md: input_data result tool
docs/phases/phase7-agentic/7300-orchestration/README.md: AnalystAgent CriticAgent END ExtractionAgent LoadingAgent ResearchAgent TransformationAgent WriterAgent aggregate_results
docs/phases/phase7-agentic/7400-memory/7403-Vector-Memory.md: parse_json_objects parse_ts search uuid4
docs/phases/phase7-agentic/README.md: action_history agent args available_tools content conversation_history current_context embedding_model execute missing_info next_action query run_in_sandbox selected_tool task task_complete tool tool_params user_code
docs/use-cases/README.md: PointStruct coordinator load_documents
docs/use-cases/UC-001-Vector-Database-Applications.md: embed find_users_with_similar_preferences logger postgres qdrant repo_path sent_tokenize user_123 users
docs/use-cases/UC-002-RAG-Applications.md: CrossEncoder Neo4jClient SentenceTransformer YOUR_CLIENT_ID YOUR_CLIENT_SECRET auth_code llm postgres query retrieved_docs
docs/use-cases/UC-003-Agent-Applications.md: CustomerServiceAgent charge_payment issue_description send_confirmation ship_item subprocess validate_order
docs/volumes/VOLUME-2-AI-Foundations.md: A B batch_A batch_B complex_function input_tensor
docs/volumes/VOLUME-3-LLM-Internals.md: apply_rotary_emb gate
docs/volumes/VOLUME-5-Model-Adaptation.md: A B SFTTrainer W_frozen alpha base_model benchmark_dataset dataset evaluate evaluate_alignment evaluate_perplexity evaluate_task filter_quality finetuned_model load_model load_your_domain_prompts preference_dataset rank ref_model test_set tokenizer train_dataset train_reward_model
docs/volumes/VOLUME-6-Data-Nexus.md: CRITICAL_INFORMATION_HERE PointStruct bm25_search chunk_documents chunk_text decompose_query document embed extract_text_from_path instruction llm llm_judge_faithfulness llm_judge_relevance load_documents model_a model_b more_context parse_entities query rag relevant_document_at_end relevant_document_at_start relevant_document_in_middle some_context supporting_context synthesize_answers system_instruction text vector_search
docs/volumes/VOLUME-7-Production-Mastery.md: Agent diagram_tool duration embed execute file_tool lint_tool llm model_name parse_subtasks plan previous_steps req_id test_tool think token_count tokens user_id
"""


def _parse_census(text: str) -> dict[str, frozenset[str]]:
    accepted: dict[str, frozenset[str]] = {}
    for line in text.splitlines():
        rel, sep, names = line.partition(": ")
        if rel and sep and names:
            accepted[rel] = frozenset(names.split())
    return accepted


ACCEPTED = _parse_census(ACCEPTED_CENSUS)
_NO_ACCEPTS: frozenset[str] = frozenset()


class _Collector:
    """pyflakes reporter protocol: collect, never print."""

    def __init__(self) -> None:
        self.flakes: list = []

    def flake(self, message) -> None:
        self.flakes.append(message)

    def unexpectedError(self, filename: str, msg: str) -> None:
        pass

    def syntaxError(self, *args) -> None:  # noqa: ANN002 - pyflakes protocol
        pass


def _target_names(target: ast.AST, bound: set[str]) -> None:
    if isinstance(target, ast.Name):
        bound.add(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            _target_names(elt, bound)
    elif isinstance(target, ast.Starred):
        _target_names(target.value, bound)
    # Attribute / Subscript targets bind attributes and items, not module names


def _match_capture_names(pattern: ast.AST, bound: set[str]) -> None:
    for node in ast.walk(pattern):
        if isinstance(node, ast.MatchAs) and node.name:
            bound.add(node.name)
        elif isinstance(node, ast.MatchStar) and node.name:
            bound.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bound.add(node.rest)


def module_bound_names(tree: ast.Module) -> set[str]:
    """Names bound at module level by one fence; function/class bodies excluded."""
    bound: set[str] = set()

    def walk_stmts(stmts: list[ast.stmt]) -> None:
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound.add(stmt.name)
            elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
                for alias in stmt.names:
                    if alias.name != "*":
                        bound.add(alias.asname or alias.name.split(".")[0])
                    if isinstance(stmt, ast.ImportFrom) and alias.name == "*":
                        bound.add("*")  # opaque marker
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    _target_names(target, bound)
            elif isinstance(stmt, (ast.AnnAssign, ast.AugAssign)):
                _target_names(stmt.target, bound)
            elif isinstance(stmt, (ast.For, ast.AsyncFor)):
                _target_names(stmt.target, bound)
                walk_stmts(stmt.body)
                walk_stmts(stmt.orelse)
            elif isinstance(stmt, (ast.While, ast.If)):
                walk_stmts(stmt.body)
                walk_stmts(stmt.orelse)
            elif isinstance(stmt, (ast.With, ast.AsyncWith)):
                for item in stmt.items:
                    if item.optional_vars is not None:
                        _target_names(item.optional_vars, bound)
                walk_stmts(stmt.body)
            elif isinstance(stmt, ast.Try) or type(stmt).__name__ == "TryStar":
                walk_stmts(stmt.body)
                for handler in stmt.handlers:
                    if handler.name:
                        bound.add(handler.name)
                    walk_stmts(handler.body)
                walk_stmts(stmt.orelse)
                walk_stmts(stmt.finalbody)
            elif isinstance(stmt, ast.Match):
                for case in stmt.cases:
                    _match_capture_names(case.pattern, bound)
                    walk_stmts(case.body)

    walk_stmts(tree.body)
    return bound


def has_star_import(tree: ast.Module) -> bool:
    return any(
        isinstance(node, ast.ImportFrom)
        and any(alias.name == "*" for alias in node.names)
        for node in ast.walk(tree)
    )


def scan_file(
    root: Path, path: Path, findings: list[tuple[str, str]], stats: list[int],
    accepted: dict[str, frozenset[str]] = ACCEPTED,
) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    in_fence = False
    lang = ""
    start = 0
    body: list[str] = []
    prior_bounds: set[str] = set()
    opaque = False
    for i, raw in enumerate(lines):
        m = FENCE.match(raw)
        if m:
            if in_fence:
                in_fence = False
                if lang not in PYTHON_LANGS:
                    body = []
                    continue
                stats[0] += 1
                src = textwrap.dedent("\n".join(body))
                body = []
                if not src.strip():
                    continue
                try:
                    tree = ast.parse(src)
                except SyntaxError:
                    stats[3] += 1  # CB-01 owns fence syntax
                    continue
                own_bounds = module_bound_names(tree)
                if not opaque:
                    collector = _Collector()
                    check(src, rel, collector)
                    for message in collector.flakes:
                        cls = type(message).__name__
                        if cls not in UNDEFINED_CLASSES:
                            continue
                        name = message.message_args[0]
                        if not isinstance(name, str):
                            continue
                        if name in prior_bounds or name in own_bounds:
                            continue  # bound by an earlier fence: lesson flow
                        if name in accepted.get(rel, _NO_ACCEPTS):
                            stats[5] += 1
                            continue  # census-accepted convention, tick-531
                        code = "UN-01" if cls == "UndefinedName" else "UN-02"
                        stats[1 if code == "UN-01" else 2] += 1
                        findings.append((rel, (
                            f"{rel}:{start + message.lineno + 1}: {code} "
                            f"undefined name '{name}' - pyflakes "
                            f"{message.message % message.message_args}, not "
                            f"bound by this fence or any earlier fence "
                            f"in the file")))
                prior_bounds |= own_bounds
                if has_star_import(tree):
                    opaque = True
                    stats[4] += 1
            else:
                in_fence = True
                lang = m.group(2).lower()
                start = i
                body = []
            continue
        if in_fence:
            body.append(raw)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[tuple[str, str]] = []
    stats = [0, 0, 0, 0, 0, 0]  # fences, UN-01, UN-02, unparseable, opaque, census
    files_seen: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        before = len(findings)
        try:
            scan_file(args.root, path, findings, stats)
        except (UnicodeDecodeError, OSError):
            continue
        if len(findings) > before:
            files_seen.add(path.relative_to(args.root).as_posix())
    for _, text in findings:
        print(text.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"fence_namecheck: {stats[1]} new undefined names (UN-01) + "
          f"{stats[2]} new use-before-bind (UN-02) in {len(files_seen)} files "
          f"across docs/; {stats[0]} python fences checked, "
          f"{stats[5]} census-accepted names, {stats[4]} star-import-opaque "
          f"fences, {stats[3]} unparseable (CB-01 owns fence syntax) -> "
          f"{'PASS' if not findings else 'FAIL'}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
