---
Document ID: 1503
Title: LLM Observability
Phase: 1
Module: 1500
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['infrastructure', 'monitoring', 'observability', 'prometheus']
---

# 1503: LLM Observability

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [LLM-Specific Metrics](#llm-specific-metrics)
- [Performance Monitoring](#performance-monitoring)
- [Quality Monitoring](#quality-monitoring)
- [Context Window Monitoring](#context-window-monitoring)
- [Cost Optimization](#cost-optimization)
- [Production Checklist](#production-checklist)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Record TTFT, TPOT, decode rate, and cost for a request in the LLMRequestMetrics dataclass
- Stream-wrap generation to publish latency histograms, token counters, and cost gauges to Prometheus
- Score response quality with relevance, repetition, and safety heuristics and reason about their limits
- Flag candidate hallucinations from uncertainty, citation, and implausible-number indicators
- Track context-window utilization and compute overflow and nearest-rank p95 statistics
- Break down 7-day cost by model and apply the prompt, output-limit, and model-selection levers

---

## Abstract

LLM observability focuses on monitoring language model specific metrics including token usage, latency, costs, and output quality. This document covers comprehensive monitoring for production LLM systems.

---

## LLM-Specific Metrics

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      LLM Observability Metrics                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  PERFORMANCE METRICS                                             │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Time to First Token (TTFT)                                    │   │
│  │  • Tokens per Second (TPS)                                       │   │
│  │  • End-to-End Latency                                            │   │
│  │  • Queue Wait Time                                               │   │
│  │  • Request Throughput                                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  TOKEN METRICS                                                   │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Input Tokens (prompt length)                                  │   │
│  │  • Output Tokens (completion length)                             │   │
│  │  • Total Tokens                                                  │   │
│  │  • Cache Hit Rate (KV cache)                                     │   │
│  │  • Context Window Usage                                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  COST METRICS                                                    │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Cost per Request                                              │   │
│  │  • Cost per 1K Tokens                                            │   │
│  │  • Total Daily Cost                                              │   │
│  │  • Cost by User/Application                                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  QUALITY METRICS                                                 │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Response Relevance                                            │   │
│  │  • Hallucination Rate                                            │   │
│  │  • Safety Filter Triggers                                        │   │
│  │  • User Satisfaction Scores                                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Performance Monitoring

### Token Processing Metrics

```python
# llm_metrics.py
import time
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class LLMRequestMetrics:
    """Metrics for a single LLM request"""

    request_id: str
    model_name: str
    timestamp: datetime

    # Token counts
    input_tokens: int
    output_tokens: int
    total_tokens: int

    # Timing (ms)
    time_to_first_token: float
    time_per_output_token: float
    total_latency: float

    # Throughput
    tokens_per_second: float

    # Cost
    cost: float

    # Optional fields (dataclasses require defaults after non-default fields)
    queue_time: float = 0.0
    cache_hit_tokens: int = 0

class LLMMetricsCollector:
    """Collect LLM-specific metrics"""

    def __init__(self, pricing: dict):
        """
        Pricing dict: {model_name: {input_cost_per_1k, output_cost_per_1k}}
        """
        self.pricing = pricing

    def record_request(
        self,
        request_id: str,
        model_name: str,
        prompt: str,
        response: str,
        start_time: float,
        first_token_time: Optional[float] = None,
        end_time: Optional[float] = None,
        cache_hit_tokens: int = 0
    ) -> LLMRequestMetrics:
        """Record metrics for a request"""

        if end_time is None:
            end_time = time.time()

        # Count tokens (approximate: whitespace words. A word is often more
        # than one BPE token, so this undercounts; use the model's tokenizer,
        # e.g. tiktoken for OpenAI models, in production.)
        input_tokens = len(prompt.split())
        output_tokens = len(response.split())
        total_tokens = input_tokens + output_tokens

        # Timing
        total_latency_ms = (end_time - start_time) * 1000

        if first_token_time:
            time_to_first_token_ms = (first_token_time - start_time) * 1000
        else:
            time_to_first_token_ms = 0.0

        generation_time = end_time - (first_token_time or start_time)
        time_per_output_token_ms = (generation_time * 1000) / output_tokens if output_tokens > 0 else 0

        # Throughput: decode rate = output tokens over the generation window.
        # total_tokens / total_duration would fold prompt processing into the
        # number and inflate it several-fold on long prompts.
        tokens_per_second = output_tokens / generation_time if generation_time > 0 else 0

        # Cost calculation
        cost = self._calculate_cost(model_name, input_tokens, output_tokens)

        return LLMRequestMetrics(
            request_id=request_id,
            model_name=model_name,
            timestamp=datetime.fromtimestamp(start_time),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cache_hit_tokens=cache_hit_tokens,
            time_to_first_token=time_to_first_token_ms,
            time_per_output_token=time_per_output_token_ms,
            total_latency=total_latency_ms,
            tokens_per_second=tokens_per_second,
            cost=cost
        )

    def _calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate request cost"""

        if model_name not in self.pricing:
            return 0.0

        pricing = self.pricing[model_name]
        input_cost = (input_tokens / 1000) * pricing['input_cost_per_1k']
        output_cost = (output_tokens / 1000) * pricing['output_cost_per_1k']

        return input_cost + output_cost
```

### Real-Time Monitoring

```python
# llm_monitor.py

from prometheus_client import Histogram, Gauge, Counter, start_http_server
import time

from llm_metrics import LLMMetricsCollector, LLMRequestMetrics

# Prometheus metrics
llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration',
    ['model_name', 'status']
)

llm_time_to_first_token = Histogram(
    'llm_time_to_first_token_seconds',
    'Time to first token',
    ['model_name']
)

llm_tokens_per_second = Gauge(
    'llm_tokens_per_second',
    'Tokens processed per second',
    ['model_name']
)

llm_total_tokens = Counter(
    'llm_total_tokens',
    'Total tokens processed',
    ['model_name', 'token_type']
)

llm_cache_hit_rate = Gauge(
    'llm_cache_hit_rate',
    'KV cache hit rate',
    ['model_name']
)

llm_cost_total = Counter(
    'llm_cost_total_dollars',
    'Total LLM cost in dollars',
    ['model_name']
)

class LLMObserver:
    """Observe LLM requests in real-time"""

    def __init__(self, model_name: str, pricing: dict):
        self.model_name = model_name
        self.collector = LLMMetricsCollector(pricing)

    def observe_request(
        self,
        request_id: str,
        prompt: str,
        generate_func
    ) -> tuple[str, LLMRequestMetrics]:
        """Observe LLM request and collect metrics"""

        start_time = time.time()
        first_token_time = None
        response_builder = []

        # Wrap generation to capture first token time
        def wrapped_generator():
            nonlocal first_token_time

            for chunk in generate_func():
                if first_token_time is None:
                    first_token_time = time.time()

                response_builder.append(chunk)
                yield chunk

        # Execute request
        try:
            for _ in wrapped_generator():
                pass

            end_time = time.time()
            response = ''.join(response_builder)

            # Record metrics
            metrics = self.collector.record_request(
                request_id=request_id,
                model_name=self.model_name,
                prompt=prompt,
                response=response,
                start_time=start_time,
                first_token_time=first_token_time,
                end_time=end_time
            )

            # Publish to Prometheus
            self._publish_metrics(metrics, "success")

            return response, metrics

        except Exception as e:
            end_time = time.time()

            # Record failed request
            llm_request_duration.labels(
                model_name=self.model_name,
                status="error"
            ).observe(end_time - start_time)

            raise

    def _publish_metrics(self, metrics: LLMRequestMetrics, status: str):
        """Publish metrics to Prometheus"""

        llm_request_duration.labels(
            model_name=self.model_name,
            status=status
        ).observe(metrics.total_latency / 1000)

        # Non-streaming requests have no first-token timestamp (stored 0.0);
        # observing 0.0 would pollute the histogram with fake sub-ms samples.
        if metrics.time_to_first_token > 0:
            llm_time_to_first_token.labels(
                model_name=self.model_name
            ).observe(metrics.time_to_first_token / 1000)

        llm_tokens_per_second.labels(
            model_name=self.model_name
        ).set(metrics.tokens_per_second)

        llm_total_tokens.labels(
            model_name=self.model_name,
            token_type="input"
        ).inc(metrics.input_tokens)

        llm_total_tokens.labels(
            model_name=self.model_name,
            token_type="output"
        ).inc(metrics.output_tokens)

        llm_cost_total.labels(
            model_name=self.model_name
        ).inc(metrics.cost)

        if metrics.total_tokens > 0:
            llm_cache_hit_rate.labels(
                model_name=self.model_name
            ).set(metrics.cache_hit_tokens / metrics.total_tokens)


if __name__ == "__main__":
    start_http_server(8002)
    print("LLM observability metrics exposed on :8002/metrics")
    while True:
        time.sleep(3600)
```

---

## Quality Monitoring

### Response Quality Metrics

```python
# quality_metrics.py

from difflib import SequenceMatcher
from typing import Optional

class LLMQualityMonitor:
    """Monitor LLM response quality"""

    def __init__(self):
        self.quality_history = []

    def evaluate_response(
        self,
        prompt: str,
        response: str,
        expected_response: Optional[str] = None
    ) -> dict:
        """Evaluate response quality"""

        metrics = {}

        # Length metrics
        metrics['response_length'] = len(response.split())
        metrics['response_too_short'] = len(response.split()) < 10
        metrics['response_too_long'] = len(response.split()) > 1000

        # Relevance (basic)
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        overlap = len(prompt_words & response_words)
        metrics['relevance_score'] = overlap / len(prompt_words) if prompt_words else 0

        # Repetition check (hallucination indicator)
        words = response.lower().split()
        unique_ratio = len(set(words)) / len(words) if words else 0
        metrics['repetition_ratio'] = 1 - unique_ratio

        # Safety check
        metrics['safe_response'] = self._check_safety(response)

        # Expected response comparison
        if expected_response:
            metrics['matches_expected'] = self._similarity(response, expected_response)

        self.quality_history.append(metrics)

        return metrics

    def _check_safety(self, response: str) -> bool:
        """Basic safety check"""

        unsafe_patterns = [
            'i cannot help with',
            'i am not able',
            'against my guidelines',
            'violates safety'
        ]

        response_lower = response.lower()

        return not any(pattern in response_lower for pattern in unsafe_patterns)

    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity"""

        return SequenceMatcher(None, text1, text2).ratio()
```

### Hallucination Detection

```python
# hallucination_detector.py

import re

class HallucinationDetector:
    """Detect potential hallucinations in LLM responses"""

    def __init__(self, knowledge_base=None):
        self.knowledge_base = knowledge_base or []

    def detect(
        self,
        prompt: str,
        response: str
    ) -> dict:
        """Detect potential hallucinations"""

        indicators = {
            'is_hallucination': False,
            'confidence': 0.0,
            'indicators': []
        }

        # Indicator 1: Verbal uncertainty
        uncertainty_phrases = [
            'i think', 'maybe', 'possibly', 'probably',
            'i believe', 'it might be', 'i\'m not sure'
        ]

        response_lower = response.lower()
        uncertainty_count = sum(1 for phrase in uncertainty_phrases if phrase in response_lower)

        if uncertainty_count > 2:
            indicators['indicators'].append('high_uncertainty')

        # Indicator 2: Overly specific without sources
        if self._has_specific_claims(response):
            if not self._has_citations(response):
                indicators['indicators'].append('specific_without_sources')

        # Indicator 3: Unsupported by knowledge base. The substring check
        # cannot detect true contradiction - it only knows whether any known
        # fact appears verbatim in the response.
        if self.knowledge_base:
            if self._unsupported_by_knowledge(response):
                indicators['indicators'].append('unsupported_by_knowledge')
                indicators['is_hallucination'] = True

        # Indicator 4: Implausible numbers
        if self._has_implausible_numbers(response):
            indicators['indicators'].append('implausible_numbers')

        # Calculate confidence
        if len(indicators['indicators']) >= 2:
            indicators['is_hallucination'] = True
            indicators['confidence'] = 0.7
        elif len(indicators['indicators']) == 1:
            indicators['confidence'] = 0.4

        return indicators

    def _has_specific_claims(self, response: str) -> bool:
        """Check for specific factual claims"""

        # Look for patterns like: "According to X, ..." or "In year Y, ..."
        specific_patterns = [
            r'\d{4}',  # Years
            r'\d+\.\d+%',  # Percentages
            r'according to',
            r'states that',
            r'reportedly'
        ]

        return any(re.search(pattern, response.lower()) for pattern in specific_patterns)

    def _has_citations(self, response: str) -> bool:
        """Check if response has citations"""

        # Anchored patterns: a bare parenthetical like "(maybe)" is not a
        # citation, and treating "according to" as a citation would let the
        # same phrase be both the un-sourced claim and the source that clears it.
        citation_patterns = [
            r'\[\d+\]',         # [1], [12]
            r'\(\w+, \d{4}\)',  # (Author, Year)
            r'source:'
        ]

        return any(re.search(pattern, response.lower()) for pattern in citation_patterns)

    def _unsupported_by_knowledge(self, response: str) -> bool:
        """Check if response contains nothing from the knowledge base"""

        # Absence of supporting evidence is NOT the same as contradiction.
        # Verify with semantic similarity (or an NLI model) in production
        # before treating this flag as decisive.

        for fact in self.knowledge_base:
            if fact.lower() in response.lower():
                return False  # Consistent

        return True  # No supporting evidence found

    def _has_implausible_numbers(self, response: str) -> bool:
        """Check for implausible numbers"""

        # Extract percentages
        percentages = re.findall(r'\d+\.?\d*%', response)

        for pct in percentages:
            value = float(pct.replace('%', ''))
            if value > 100 or value < 0:
                return True

        # Extract years - the \b anchors keep 4-digit windows inside longer
        # numbers ("1000000" -> "1000") from being read as years
        years = re.findall(r'\b\d{4}\b', response)

        for year in years:
            year_int = int(year)
            if year_int > 2030 or year_int < 1900:
                return True

        return False
```

---

## Context Window Monitoring

### Context Usage Tracking

```python
# context_monitor.py

class ContextWindowMonitor:
    """Monitor context window usage"""

    def __init__(self, model_name: str, max_context: int):
        self.model_name = model_name
        self.max_context = max_context
        self.usage_history = []

    def track_usage(
        self,
        prompt_tokens: int,
        max_tokens: int
    ) -> dict:
        """Track context window usage"""

        total_needed = prompt_tokens + max_tokens
        utilization = total_needed / self.max_context
        fits_in_context = total_needed <= self.max_context

        result = {
            'prompt_tokens': prompt_tokens,
            'max_tokens': max_tokens,
            'total_needed': total_needed,
            'max_context': self.max_context,
            'utilization': utilization,
            'fits_in_context': fits_in_context,
            'overflow_tokens': max(0, total_needed - self.max_context)
        }

        self.usage_history.append(result)

        if utilization > 0.9:
            print(f"⚠️ High context usage: {utilization:.1%}")

        if not fits_in_context:
            print(f"🔴 Context overflow: {result['overflow_tokens']} tokens over")

        return result

    def get_usage_stats(self) -> dict:
        """Get context usage statistics"""

        if not self.usage_history:
            return {}

        utilizations = [u['utilization'] for u in self.usage_history]

        # Nearest-rank percentile. The naive int(n * 0.95) index returns the
        # MAXIMUM value for n <= 20 - p100 masquerading as p95.
        p95_index = max(0, int(len(utilizations) * 0.95) - 1)

        return {
            'avg_utilization': sum(utilizations) / len(utilizations),
            'max_utilization': max(utilizations),
            'p95_utilization': sorted(utilizations)[p95_index],
            'overflow_count': sum(1 for u in self.usage_history if not u['fits_in_context'])
        }
```

---

## Cost Optimization

### Token Usage Analytics

```python
# cost_analytics.py

from datetime import datetime

from llm_metrics import LLMRequestMetrics

class LLMCostAnalyzer:
    """Analyze and optimize LLM costs"""

    def __init__(self, pricing: dict):
        self.pricing = pricing
        self.request_log = []

    def log_request(self, metrics: LLMRequestMetrics):
        """Log request metrics for analysis"""

        self.request_log.append(metrics)

    def analyze_costs(
        self,
        window_days: int = 7
    ) -> dict:
        """Analyze costs over time window"""

        cutoff = datetime.now().timestamp() - (window_days * 24 * 3600)

        recent_requests = [
            r for r in self.request_log
            if r.timestamp.timestamp() > cutoff
        ]

        total_cost = sum(r.cost for r in recent_requests)
        total_tokens = sum(r.total_tokens for r in recent_requests)

        # Cost by model
        cost_by_model = {}
        for req in recent_requests:
            if req.model_name not in cost_by_model:
                cost_by_model[req.model_name] = 0
            cost_by_model[req.model_name] += req.cost

        # Cost breakdown
        input_cost = sum(
            r.input_tokens / 1000 * self.pricing.get(r.model_name, {}).get('input_cost_per_1k', 0)
            for r in recent_requests
        )

        output_cost = sum(
            r.output_tokens / 1000 * self.pricing.get(r.model_name, {}).get('output_cost_per_1k', 0)
            for r in recent_requests
        )

        return {
            'window_days': window_days,
            'total_requests': len(recent_requests),
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'cost_per_1k_tokens': (total_cost / total_tokens) * 1000 if total_tokens > 0 else 0,
            'cost_by_model': cost_by_model,
            'input_cost_ratio': input_cost / total_cost if total_cost > 0 else 0,
            'output_cost_ratio': output_cost / total_cost if total_cost > 0 else 0
        }

    def suggest_optimizations(self) -> list:
        """Suggest cost optimizations"""

        suggestions = []

        # Empty log: the averages below divide by zero and max() on an empty
        # dict raises ValueError
        if not self.request_log:
            return suggestions

        # Analyze request patterns
        avg_input_tokens = sum(r.input_tokens for r in self.request_log) / len(self.request_log)
        avg_output_tokens = sum(r.output_tokens for r in self.request_log) / len(self.request_log)

        if avg_input_tokens > 5000:
            suggestions.append({
                'type': 'prompt_optimization',
                'issue': 'High average input tokens',
                'suggestion': 'Consider prompt caching or summarization',
                'potential_savings': '20-30%'
            })

        if avg_output_tokens > 2000:
            suggestions.append({
                'type': 'output_limiting',
                'issue': 'High average output tokens',
                'suggestion': 'Set max_tokens parameter appropriately',
                'potential_savings': '10-20%'
            })

        # Check for model overuse
        costs_by_model = {}
        for req in self.request_log:
            if req.model_name not in costs_by_model:
                costs_by_model[req.model_name] = 0
            costs_by_model[req.model_name] += req.cost

        most_expensive = max(costs_by_model, key=costs_by_model.get)
        if costs_by_model[most_expensive] > sum(costs_by_model.values()) * 0.7:
            suggestions.append({
                'type': 'model_selection',
                'issue': f'{most_expensive} dominates costs',
                'suggestion': 'Consider smaller models for simple requests',
                'potential_savings': '40-60%'
            })

        return suggestions
```

---

## Production Checklist

### Monitoring Setup
- [ ] Token metrics (input/output/total)
- [ ] Performance metrics (TTFT, TPS, latency)
- [ ] Cost tracking (per request, per model)
- [ ] Quality metrics (relevance, safety)
- [ ] Context window usage
- [ ] Cache hit rate
- [ ] Error rates and types

### Alerting Thresholds
- [ ] High latency (>5s P95)
- [ ] Low TPS (<10 tokens/sec)
- [ ] High cost per day
- [ ] High context utilization (>90%)
- [ ] High error rate (>5%)
- [ ] Low cache hit rate (<50%)

---

## References

### Related ai-engineering-curriculum Documents

- [1501: Monitoring and Observability](./1501-Monitoring-and-Observability.md)
- [1502: Model Drift Detection](./1502-Model-Drift-Detection.md)

### External References

- [Prometheus: Metric Naming Best Practices](https://prometheus.io/docs/practices/naming/)
- [OpenTelemetry GenAI Semantic Conventions](https://github.com/open-telemetry/semantic-conventions-genai)
- [openai/tiktoken](https://github.com/openai/tiktoken)

---

## Next Steps

- Phase 1 Complete! Next: **[Phase 2: Foundations](../../phase2-foundations/)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [1501: Monitoring and Observability](./1501-Monitoring-and-Observability.md)
- [1502: Model Drift Detection](./1502-Model-Drift-Detection.md)
- [2101: Tensor Algebra and Linear Algebra for AI](../../phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)
- **Experiment:** [EXP_1503: Model Drift Detection Experiments](../../../../experiments/EXP_1503_DRIFT_DETECTION.md)
