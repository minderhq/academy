---
Document ID: 1300-QUIZ
Title: "1300: Kubernetes - Quiz"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Intermediate
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'infrastructure', 'kubernetes']
---

# 1300: Kubernetes - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. K3s is:**

A) Full Kubernetes distribution
B) Monitoring tool
C) Lightweight Kubernetes
D) Container runtime

**2. A pod is:**

A) One or more containers
B) A VM, a virtual-machine unit Kubernetes does not schedule directly
C) A container
D) A service

**3. GPU in Kubernetes requires:**

A) Device plugins
B) Special scheduler
C) No configuration
D) Only Nvidia GPUs

**4. A node is:**

A) A worker machine
B) A container
C) A pod
D) A service, a stable networking endpoint rather than a machine

**5. GPU scheduler ensures:**

A) Load balancing
B) All nodes have GPUs, a homogeneous-fleet condition the scheduler does not demand
C) Autoscaling
D) Pods are scheduled on GPU nodes

**6. Storage classes provide:**

A) Only local storage
B) Static storage
C) No storage
D) Dynamic provisioning

**7. A service exposes:**

A) Storage
B) Pods externally
C) ConfigMaps
D) Nodes, machines the Service abstraction does not expose

**8. K3s uses less memory because:**

A) Removed unnecessary components
B) No components
C) Uses SQLite
D) Only runs on ARM

**9. GPU resource limits are specified:**

A) In node spec
B) In pod spec, a level the GPU limit field does not live at
C) In container spec
D) In service spec

**10. Persistent volumes:**

A) Are deleted with pods
B) Are not supported
C) Survive pod restarts
D) Only work with GPUs

**11. Helm is:**

A) A monitoring tool, a role that belongs to Prometheus and friends
B) A package manager for K8s
C) A storage driver
D) A container runtime

**12. A deployment:**

A) Manages services
B) Manages nodes
C) Manages storage
D) Manages pods

**13. The GPU device plugin runs:**

A) On each node
B) In a separate cluster
C) On master only
D) On demand

**14. K3s master node can also:**

A) No workloads
B) Run workloads
C) Only schedule
D) Only manage, a restriction single-node K3s setups routinely disprove

**15. YAML is used for:**

A) Storage only
B) Container images, artifacts image registries and build tools own instead
C) Monitoring
D) K8s configuration

**16. Namespace provides:**

A) Resource isolation
B) Both A and C
C) Security
D) Neither

**17. A ConfigMap stores:**

A) Storage
B) Configuration data
C) Secrets
D) Pods, runtime workloads a ConfigMap only feeds data to

**18. For GPU workloads, you need:**

A) Node labels
B) Pod affinity
C) Taints and tolerations
D) All of the above

**19. Longhorn provides:**

A) File storage
B) Object storage
C) Block storage
D) No storage

**20. Helm charts:**

A) Are services, one resource type among those charts can template
B) Are containers
C) Define K8s resources
D) Deploy applications

---

## Answer Key

| # | Answer |
|---|--------|
| 1 | C |
| 2 | A |
| 3 | A |
| 4 | A |
| 5 | D |
| 6 | D |
| 7 | B |
| 8 | A |
| 9 | C |
| 10 | C |
| 11 | B |
| 12 | D |
| 13 | A |
| 14 | B |
| 15 | D |
| 16 | B |
| 17 | B |
| 18 | D |
| 19 | C |
| 20 | C |
