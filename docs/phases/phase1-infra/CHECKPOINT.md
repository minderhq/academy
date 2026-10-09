---
Document ID: PHASE1-CHECKPOINT
Title: "Progress Checkpoints: Phase 1 - Infrastructure Fabric"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['checkpoint', 'infrastructure', 'gpu', 'networking']
---

# Progress Checkpoints: Phase 1 - Infrastructure Fabric

**Track your progress through Phase 1 modules**

---

## Phase 1 Overview

**Phase:** [1000] Infrastructure Fabric

**Modules:** 5 (1100, 1200, 1300, 1400, 1500)

**Estimated Time:** 2-3 weeks

**Difficulty:** ⭐⭐ Intermediate

---

## Phase Completion Goal

After completing Phase 1, you will:

- ✅ Run LLMs locally with Ollama
- ✅ Containerize applications with Docker
- ✅ Understand network topology basics
- ✅ Set up basic monitoring
- ✅ Be ready for Volume 2

---

## Module Checkpoints

### Module 1100: Network Fundamentals for LLM Infrastructure (Optional)

**After completing 1101-1103, you should:**

**Knowledge Check:**

- [ ] Explain bridge mode (and why it avoids double NAT)
- [ ] Understand star topology benefits
- [ ] Know when to use jumbo frames (MTU 9000)

**Practical Skills:**

- [ ] Configure modem for bridge mode
- [ ] Configure a managed switch (VLANs, MTU)
- [ ] Verify network throughput

**Troubleshooting:**

- [ ] Diagnose network issues
- [ ] Check MTU settings
- [ ] Verify cabling

**Checkpoint Quiz:**

1. What is the benefit of bridge mode?
2. Why use star topology over daisy-chain?
3. When should you enable jumbo frames?

**Ready for Next Module?**

- If YES → Continue to 1200
- If NO → Review [1101: Internet Uplink & Modem Configuration](../../phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md)

---

### Module 1200: Virtualization (Optional)

**After completing 1201-1204, you should:**

**Knowledge Check:**

- [ ] Understand hypervisor basics (Proxmox)
- [ ] Know PCIe passthrough requirements
- [ ] Understand GPU passthrough for AI workloads

**Practical Skills:**

- [ ] Create VM in Proxmox
- [ ] Configure CPU pinning
- [ ] Set up ZFS storage
- [ ] Pass through GPU to VM

**Troubleshooting:**

- [ ] Diagnose VM boot issues
- [ ] Fix GPU passthrough problems
- [ ] Manage virtual disks

**Checkpoint Quiz:**

1. Why use CPU pinning for VMs?
2. What are the benefits of ZFS for VM storage?
3. How does PCIe passthrough work?

**Ready for Next Module?**

- If YES → Continue to 1300
- If NO → Review [1201-Proxmox-Hypervisor-SOP.md](../../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)

---

### Module 1300: Kubernetes (Optional)

**After completing 1301-1303, you should:**

**Knowledge Check:**

- [ ] Understand K3s architecture
- [ ] Know GPU scheduling challenges
- [ ] Understand storage classes for dynamic provisioning

**Practical Skills:**

- [ ] Deploy K3s cluster
- [ ] Schedule GPU workloads
- [ ] Set up NFS storage class

**Troubleshooting:**

- [ ] Diagnose cluster issues
- [ ] Fix GPU scheduling problems
- [ ] Manage storage provisioning

**Checkpoint Quiz:**

1. What is the difference between K3s and full Kubernetes?
2. How does GPU scheduling work in K8s?
3. What are storage classes used for?

**Ready for Next Module?**

- If YES → Continue to 1400
- If NO → Review [1301-K3s-Master-Worker-Arch.md](../../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md)

---

### Module 1400: LLMOps (Required)

**After completing 1401-1402, 1403-1404, you should:**

**Knowledge Check:**

- [ ] Understand Ollama architecture
- [ ] Know vLLM vs TGI differences
- [ ] Understand when to use each inference engine

**Practical Skills:**

- [ ] Run models with Ollama
- [ ] Deploy vLLM for production
- [ ] Configure TGI for inference
- [ ] Choose right engine for use case

**Troubleshooting:**

- [ ] Diagnose model loading issues
- [ ] Fix inference bottlenecks
- [ ] Optimize throughput

**Checkpoint Quiz:**

1. When should you use Ollama vs vLLM?
2. What are the benefits of TGI?
3. How do you optimize inference throughput?

**Lab Verification:**

- [ ] Completed [LAB-001: Docker & LLM](../../learning-resources/labs/LAB-001-Docker-LLM.md)

**Ready for Next Module?**

- If YES → Continue to 1500
- If NO → Review [1401-Ollama-Enterprise.md](../../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)

---

### Module 1500: Monitoring (Required)

**After completing 1501-1503, you should:**

**Knowledge Check:**

- [ ] Understand Prometheus monitoring stack
- [ ] Know model drift detection methods
- [ ] Understand LLM observability metrics

**Practical Skills:**

- [ ] Set up Prometheus + Grafana
- [ ] Monitor model drift with PSI
- [ ] Track LLM metrics (TTFT, TPS)
- [ ] Create alerting rules

**Troubleshooting:**

- [ ] Diagnose monitoring issues
- [ ] Detect drift early
- [ ] Optimize monitoring overhead

**Checkpoint Quiz:**

1. What is PSI and how is it used for drift detection?
2. What are TTFT and TPS metrics?
3. When should you trigger model retraining?

**Lab Verification:**

- [ ] Completed [TUTORIAL-004: Monitoring](../../learning-resources/tutorials/TUTORIAL-004-Monitoring.md)

**Ready for Phase 2?**

- If YES → Continue to [Phase 2](../../phases/phase2-foundations/README.md)
- If NO → Review [1501-Monitoring-and-Observability.md](../../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)

---

## Phase Completion Assessment

### Final Checkpoint

**After completing ALL Phase 1 modules, verify:**

**Infrastructure Setup:**

- [ ] Docker installed and working
- [ ] Ollama running with models
- [ ] Can run LLMs locally
- [ ] Monitoring stack deployed

**Knowledge Verification:**

- [ ] Can explain infrastructure choices
- [ ] Understand when to use virtualization
- [ ] Know monitoring best practices
- [ ] Can troubleshoot common issues

**Practical Skills:**

- [ ] Run Ollama models independently
- [ ] Containerize simple applications
- [ ] Set up basic monitoring
- [ ] Diagnose infrastructure issues

### Phase 1 Capstone

**Build a Simple Project:**

- [ ] Run local LLM with custom prompt
- [ ] Containerize with Docker
- [ ] Add basic monitoring
- [ ] Document your setup

**Estimated Time:** 2-3 hours

---

## Progress Tracking

### Module Completion

```text
1100 Network: ☐ Optional
1200 Virtualization: ☐ Optional
1300 Kubernetes: ☐ Optional
1400 LLMOps: ☐ Required ⭐
1500 Monitoring: ☐ Required ⭐

Phase 1 Progress: ___ / 2 required modules
```

### Time Tracking

```text
Started: _____________
Module 1100: _____ hours
Module 1200: _____ hours
Module 1300: _____ hours
Module 1400: _____ hours
Module 1500: _____ hours

Total Time: _____ hours (Expected: 20-40 hours)
```

---

## Next Steps

### After Phase 1 Completion

**Immediate Next:**

1. **[Volume 2: AI/ML Foundations](../../volumes/VOLUME-2-AI-Foundations.md)** - Math and frameworks
2. **[PROJECT-001: AI Assistant](../../learning-resources/projects/PROJECT-001-AI-Assistant.md)** - First capstone

**Keep Practicing:**

- Run different LLM models
- Experiment with Docker compose
- Practice monitoring setup

**Review & Solidify:**

- [QUICK-START.md](../../00-META/QUICK-START.md)
- [LAB-001: Docker & LLM](../../learning-resources/labs/LAB-001-Docker-LLM.md)

---

## Tips for Success

1. **Don't Skip LLMOps (1400):** Essential for AI work
2. **Monitor Early:** Set up monitoring before you need it
3. **Practice Docker:** Used throughout curriculum
4. **Ask Questions:** Community forums are helpful
5. **Document Setup:** Helps troubleshooting later

---

## Common Pitfalls

1. **MTU Mismatch:** Mixed MTU settings between NIC, bridge and veth pairs cause silent packet fragmentation - verify with `ip link` before blaming the application
2. **GPU Passthrough Gaps:** Unsplit IOMMU groups leave the VM seeing no GPU at all - check `lspci` inside the guest before installing drivers
3. **No Rate Limiting:** An LLM endpoint without gateway rate limits melts under the first client retry storm - enforce limits at the ingress, not in the model server
4. **Wrong Storage Class:** Model weights on a low-IOPS storage class turn every cold start into a full download - pin weights to fast storage or pre-pull them

---

## Phase 1 Completion Badge

**Badge:** 🏗️ Infrastructure Architect

**You've earned it when:**

- All required modules (1400, 1500) completed
- Labs (TUTORIAL-004, LAB-001) completed
- Phase checkpoint passed
- Can run LLMs independently

---

**Phase:** 1000 - Infrastructure Fabric

**Next Phase:** 2000 - Cognitive Science & Frameworks
