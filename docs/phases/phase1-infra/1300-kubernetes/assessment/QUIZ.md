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
B) Resource isolation and security scoping together
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
D) Node labels, pod affinity and taints/tolerations together

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

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 2, 4, 7, 8, 11, 12, 14, 15, 17, 20:** [1301: K3s Master-Worker Architecture](../1301-K3s-Master-Worker-Arch.md) — cluster core: nodes, pods, services, tooling
- **Questions 3, 5, 9, 13, 16, 18:** [1302: GPU Scheduler Configuration](../1302-GPU-Scheduler.md) — GPU scheduling and workload placement
- **Questions 6, 10, 19:** [1303: Storage Classes for Dynamic Provisioning](../1303-Storage-Classes.md) — persistent storage and provisioning

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | C | K3s is the lightweight Kubernetes distribution - single binary, edge/IoT focused |
| 2 | A | A pod is the smallest schedulable unit, wrapping one or more containers sharing network/storage |
| 3 | A | GPU exposure runs through device plugins advertising each node's GPU resources |
| 4 | A | A node is the worker machine (physical or VM) that pods run on |
| 5 | D | The GPU scheduler's job is placing pods onto nodes that have GPUs |
| 6 | D | Storage classes enable dynamic provisioning - volumes created on demand |
| 7 | B | A Service gives pods a stable endpoint and can expose them externally |
| 8 | A | K3s strips legacy/alpha components and bundles the essentials, cutting memory |
| 9 | C | GPU limits live at the container level (resources.limits inside the pod's container spec) |
| 10 | C | PersistentVolumes outlive pods - workloads restart, the data stays |
| 11 | B | Helm is the Kubernetes package manager; charts are its packages |
| 12 | D | A Deployment manages pods: replica counts, rollouts, rollbacks |
| 13 | A | The device plugin runs as a DaemonSet - one instance per node |
| 14 | B | K3s server nodes are also schedulable, which is how single-box setups run workloads |
| 15 | D | YAML declares Kubernetes configuration - every resource is a manifest |
| 16 | B | Namespaces provide both resource isolation (quotas) and security scoping (RBAC) |
| 17 | B | A ConfigMap stores non-secret configuration data; sensitive values go in Secrets |
| 18 | D | GPU workloads combine node labels, affinity, and taints/tolerations to land on the right nodes |
| 19 | C | Longhorn is distributed block storage for Kubernetes |
| 20 | C | Charts are templated definitions of Kubernetes resources; installing one renders and applies them |
