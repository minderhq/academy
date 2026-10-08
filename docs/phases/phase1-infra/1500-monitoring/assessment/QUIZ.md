---
Document ID: 1500-QUIZ
Title: "1500: Monitoring - Quiz"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'infrastructure', 'monitoring']
---

# 1500: Monitoring - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Observability includes:**

- A) Only metrics, leaving logs and traces uncovered
- B) Metrics, logs, and traces
- C) Only logs
- D) Only traces

**2. Model drift occurs when:**

- A) Model performance degrades over time
- B) Model improves
- C) Data changes
- D) Performance degrades as the input data distribution changes over time

**3. Prometheus stores:**

- A) Logs, an append-only record that Prometheus does not store
- B) Time series metrics
- C) Traces
- D) Events

**4. Histogram in Prometheus:**

- A) Counts occurrences
- B) Tracks distributions
- C) Stores strings, a job for log backends rather than histogram buckets
- D) No use

**5. SLA stands for:**

- A) Service Level Assurance, a phrasing no SRE handbook uses
- B) System Level Agreement
- C) Service Level Agreement
- D) Service Level Invoice

**6. SLO is:**

- A) Service Level Option, a term that appears in no error-budget workflow
- B) Service Level Objective
- C) System Level Objective
- D) Service Level Intention

**7. SLI measures:**

- A) Service Level Index
- B) System Level Indicator, a mixture that no SLO definition sheet contains
- C) Service Level Indicator
- D) Service Level Interval

**8. Alert fatigue occurs when:**

- A) No alerts
- B) Too few alerts
- C) Too many alerts
- D) Perfect monitoring

**9. Golden signals are:**

- A) Network, storage
- B) CPU, memory, disk, a resource checklist the golden-signals method never fixed on
- C) Latency, traffic, errors, saturation
- D) Cache hit rate, queue depth

**10. Model drift detection:**

- A) Monitors output distribution
- B) Monitors input distribution
- C) Watches output and input distributions alike
- D) Tracks only serving latency

**11. Grafana displays:**

- A) Metrics dashboards
- B) Logs
- C) Traces
- D) Metrics, logs and traces together

**12. Jaeger is used for:**

- A) Metrics, the time-series side that Jaeger's tracing backend leaves to Prometheus
- B) Distributed tracing
- C) Logs
- D) Storage

**13. A rate in Prometheus:**

- A) No calculation
- B) Sums values, an operation rate() explicitly does not perform
- C) Averages values
- D) Calculates per-second rate

**14. Token throughput is:**

- A) Tokens per second
- B) Total tokens, a cumulative count rather than the throughput rate
- C) Batch size
- D) Tokens per dollar

**15. GPU utilization monitoring:**

- A) Measures GPU usage
- B) Measures memory
- C) Measures temperature
- D) GPU usage, memory and temperature together

**16. Logging best practices include:**

- A) Structured logs
- B) Log levels
- C) Contextual information
- D) Structured formats, log levels and contextual information together

**17. Distributed tracing helps:**

- A) Debug requests across services
- B) Monitor metrics
- C) Store logs, a retention job that belongs to a log backend like Loki
- D) Replace the log backend

**18. Alerting should be:**

- A) Based on symptoms
- B) Based on causes, the cause-first triage that symptom-based paging exists to replace
- C) Alert everything
- D) No alerts

**19. Model observability:**

- A) Tracks model inputs/outputs
- B) Only metrics, a slice that ignores the input and output streams
- C) Only latency
- D) Not needed

**20. The four golden signals are:**

- A) Latency, traffic, errors, saturation
- B) CPU, memory, disk, network
- C) Users, sessions, requests, errors, a product-analytics set
- D) P99, p50, error rate, uptime

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 3-9, 11-13, 16-18, 20:** [1501: Monitoring and Observability](../1501-Monitoring-and-Observability.md) — metrics, logs, traces, and SRE practice
- **Questions 2, 10, 19:** [1502: Model Drift Detection](../1502-Model-Drift-Detection.md) — drift types and detection
- **Questions 14, 15:** [1503: LLM Observability](../1503-LLM-Observability.md) — LLM-specific metrics and cost

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | B | Observability is the three pillars together: metrics, logs, traces |
| 2 | D | Model drift is both: performance degrades as the input data distribution changes over time |
| 3 | B | Prometheus is a time-series metrics store - logs belong to log backends |
| 4 | B | Histograms track value distributions through buckets |
| 5 | C | SLA = Service Level Agreement, the customer-facing contract |
| 6 | B | SLO = Service Level Objective, the internal reliability target |
| 7 | C | SLI = Service Level Indicator, the measured quantity an SLO is built on |
| 8 | C | Alert fatigue comes from too many alerts - responders stop trusting the page |
| 9 | C | Golden signals (Google SRE): latency, traffic, errors, saturation |
| 10 | C | Drift detection watches output distributions and input distributions alike |
| 11 | D | Grafana renders metrics, logs, and traces in one place |
| 12 | B | Jaeger is a distributed-tracing backend; time series stay with Prometheus |
| 13 | D | rate() computes the per-second rate of increase of a counter |
| 14 | A | Token throughput is tokens per second - a rate, not a cumulative count |
| 15 | D | GPU monitoring covers usage, memory, and temperature together |
| 16 | D | Structured formats, levels, and context - all three are logging best practices |
| 17 | A | Distributed tracing follows one request as it crosses services |
| 18 | A | Page on symptoms users feel; cause-based alerting drowns the on-call |
| 19 | A | Model observability tracks the model's inputs and outputs - features and predictions |
| 20 | A | The four golden signals: latency, traffic, errors, saturation |
