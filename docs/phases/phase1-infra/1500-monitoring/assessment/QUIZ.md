---
Document ID: 1500-QUIZ
Title: "1500: Monitoring - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
---

# 1500: Monitoring - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Observability includes:**

A) Only metrics, leaving logs and traces uncovered
B) Metrics, logs, and traces
C) Only logs
D) Only traces

**2. Model drift occurs when:**

A) Model performance degrades over time
B) Model improves
C) Data changes
D) Both A and C

**3. Prometheus stores:**

A) Logs, an append-only record that Prometheus does not store
B) Time series metrics
C) Traces
D) Events

**4. Histogram in Prometheus:**

A) Counts occurrences
B) Tracks distributions
C) Stores strings, a job for log backends rather than histogram buckets
D) No use

**5. SLA stands for:**

A) Service Level Assurance, a phrasing no SRE handbook uses
B) System Level Agreement
C) Service Level Agreement
D) None

**6. SLO is:**

A) Service Level Option, a term that appears in no error-budget workflow
B) Service Level Objective
C) System Level Objective
D) None

**7. SLI measures:**

A) Service Level Indicator
B) System Level Indicator, a mixture that no SLO definition sheet contains
C) Service Level Index
D) None

**8. Alert fatigue occurs when:**

A) Too many alerts
B) Too few alerts
C) No alerts
D) Perfect monitoring

**9. Golden signals are:**

A) Latency, traffic, errors, saturation
B) CPU, memory, disk, a resource checklist the golden-signals method never fixed on
C) Network, storage
D) None

**10. Model drift detection:**

A) Monitors output distribution
B) Monitors input distribution
C) Both A and B
D) Neither

**11. Grafana displays:**

A) Metrics dashboards
B) Logs
C) Traces
D) All of the above

**12. Jaeger is used for:**

A) Metrics, the time-series side that Jaeger's tracing backend leaves to Prometheus
B) Distributed tracing
C) Logs
D) Storage

**13. A rate in Prometheus:**

A) Calculates per-second rate
B) Sums values, an operation rate() explicitly does not perform
C) Averages values
D) No calculation

**14. Token throughput is:**

A) Tokens per second
B) Total tokens, a cumulative count rather than the throughput rate
C) Batch size
D) None

**15. GPU utilization monitoring:**

A) Measures GPU usage
B) Measures memory
C) Measures temperature
D) All of the above

**16. Logging best practices include:**

A) Structured logs
B) Log levels
C) Contextual information
D) All of the above

**17. Distributed tracing helps:**

A) Debug requests across services
B) Monitor metrics
C) Store logs, a retention job that belongs to a log backend like Loki
D) None

**18. Alerting should be:**

A) Based on symptoms
B) Based on causes, the cause-first triage that symptom-based paging exists to replace
C) Alert everything
D) No alerts

**19. Model observability:**

A) Tracks model inputs/outputs
B) Only metrics, a slice that ignores the input and output streams
C) Only latency
D) Not needed

**20. The four golden signals are:**

A) Latency, traffic, errors, saturation
B) CPU, memory, disk, network
C) Users, sessions, requests, errors, a product-analytics set
D) None

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | B |
| 2 | D |
| 3 | B |
| 4 | B |
| 5 | C |
| 6 | B |
| 7 | A |
| 8 | A |
| 9 | A |
| 10 | C |
| 11 | D |
| 12 | B |
| 13 | A |
| 14 | A |
| 15 | D |
| 16 | D |
| 17 | A |
| 18 | A |
| 19 | A |
| 20 | A |
