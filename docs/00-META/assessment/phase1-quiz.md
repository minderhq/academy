---
Document ID: PHASE1-QUIZ
Title: "Phase 1: Infrastructure Quiz"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Beginner
Tags: ['assessment', 'quiz', 'infrastructure']
---

# Phase 1: Infrastructure Quiz

**15 Questions | Passing Score: 80% | Time: 30 minutes**

## Instructions

- **15 questions**, one best answer each
- **Passing score: 80%** (12/15 correct)
- Answers live only in the Answer Key at the end of this quiz - attempt every question before checking it
- Graded below the line? The Need to Review? map above the Answer Key links every question to its closest lesson - rework those before your next attempt

---

## Questions

### 1. What is the primary purpose of jumbo frames in network configuration?
- a) Reduce packet overhead
- b) Improve encryption throughput during transfers
- c) Increase security
- d) Reduce latency

---

### 2. Which Kubernetes component manages GPU scheduling?
- a) device plugin
- b) controller-manager
- c) kubelet
- d) kube-scheduler

---

### 3. What is MTU 9000 used for in this course's infrastructure?
- a) Jumbo frames for high-throughput transfers
- b) VPN tunneling
- c) Security filtering of oversized datagrams at the edge
- d) Load balancing

---

### 4. In Proxmox, what is core pinning?
- a) Assigning specific CPU cores to VMs
- b) Network configuration
- c) Memory allocation
- d) Storage management policies that pin volumes to hosts

---

### 5. What is PCIe passthrough used for in the virtualization module?
- a) Network routing
- b) CPU optimization
- c) GPU passthrough to VM
- d) Storage expansion

---

### 6. Which storage protocol is used to share the central storage server over the network?
- a) SMB
- b) NFS
- c) iSCSI
- d) FC

---

### 7. What is the benefit of Ollama Enterprise?
- a) Cloud hosting
- b) GPU clustering
- c) Auto-scaling of licensed cloud seats per tenant
- d) Localized model APIs

---

### 8. What does PagedAttention in vLLM optimize?
- a) Network throughput
- b) CPU utilization
- c) Memory usage for KV cache
- d) Storage I/O

---

### 9. Which tool is used for log aggregation in Minder Academy?
- a) Prometheus
- b) Loki
- c) Grafana
- d) Tempo

---

### 10. What is model drift?
- a) Model size increase
- b) Training speed decrease
- c) Model performance degradation over time
- d) Inference latency spikes from hardware contention

---

### 11. What metric measures time to first token (TTFT)?
- a) Throughput
- b) Latency
- c) Tokens per second
- d) Memory usage

---

### 12. In Docker, what is a container?
- a) Virtual machine
- b) Physical server
- c) Network switch
- d) Isolated application environment

---

### 13. What is the purpose of Docker Compose?
- a) Image building
- b) Multi-container orchestration
- c) Network security
- d) Storage management

---

### 14. What does NFS stand for?
- a) Network File Storage
- b) Node File System
- c) Network File System
- d) Network File Service

---

### 15. What is K3s?
- a) Container runtime
- b) Network protocol
- c) Storage system
- d) Lightweight Kubernetes distribution

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 3:** [1103: Jumbo Frames and MTU](../../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md) — MTU sizing, jumbo frames and the packet-overhead math of big transfers
- **Question 2:** [1302: GPU Scheduler](../../phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md) — how the GPU scheduler places pods on device-capable nodes
- **Question 4:** [1201: Proxmox Hypervisor SOP](../../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md) — Proxmox core pinning and the hypervisor SOP
- **Question 5:** [1202: TB3 UT3G Passthrough](../../phases/phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md) — PCIe passthrough for TB3/UT3G-attached GPUs
- **Questions 6, 14:** [1303: Storage Classes](../../phases/phase1-infra/1300-kubernetes/1303-Storage-Classes.md) — NFS-backed shared storage and storage classes
- **Question 7:** [1401: Ollama Enterprise](../../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md) — Ollama Enterprise local model APIs
- **Question 8:** [1402: vLLM and TGI](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) — PagedAttention and serving throughput in vLLM and TGI
- **Question 9:** [1501: Monitoring and Observability](../../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md) — Loki log aggregation and the observability stack
- **Question 10:** [1502: Model Drift Detection](../../phases/phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) — model drift detection over time
- **Question 11:** [1503: LLM Observability](../../phases/phase1-infra/1500-monitoring/1503-LLM-Observability.md) — TTFT and the LLM latency metrics
- **Questions 12-13, 15:** [1301: K3s Master Worker Arch](../../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md) — containers, multi-container orchestration and the lightweight K3s control plane

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | A | Jumbo frames (MTU 9000) carry more payload per packet, cutting framing overhead on transfers |
| 2 | A | The Kubernetes device plugin advertises GPU resources so the scheduler can place GPU workloads |
| 3 | A | MTU 9000 enables jumbo frames, the high-throughput transfer setting used across the course's infrastructure |
| 4 | A | Core pinning assigns specific CPU cores to a VM for predictable performance |
| 5 | C | PCIe passthrough hands the physical GPU to the VM directly instead of emulating it |
| 6 | B | NFS shares the central storage server's volumes over the network |
| 7 | D | Ollama Enterprise's value is serving model APIs locally rather than hosting in the cloud |
| 8 | C | PagedAttention pages the KV cache in and out, cutting the memory waste that limits throughput |
| 9 | B | Loki aggregates logs in the Minder stack; Prometheus does metrics and Grafana dashboards |
| 10 | C | Drift is model performance degrading over time as inputs shift away from training data |
| 11 | B | TTFT is a latency metric: how long the user waits until the first token arrives |
| 12 | D | A container is an isolated application environment sharing the host kernel, not a VM or physical server |
| 13 | B | Docker Compose orchestrates multi-container applications from a single declarative file |
| 14 | C | NFS stands for Network File System |
| 15 | D | K3s is a lightweight Kubernetes distribution built for edge and small hosts |

**Passing: 12/15 (80%)**

