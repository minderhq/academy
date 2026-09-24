---
Document ID: 5303
Title: Federated Learning
Phase: 5
Module: 5300
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['finetuning', 'synthetic-data', 'distillation', 'federated']
---

# 5303: Federated Learning

**Project:** AI Engineering Curriculum
**Phase:** [5300] Synthetic Data
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 4 hours

---

## Abstract

Federated Learning enables training AI models across decentralized data sources while preserving privacy. This document covers federated averaging, differential privacy, and production deployment.

---

## Federated Averaging Algorithm

```python
# federated_learning.py

import torch
import torch.nn as nn
from typing import List, Dict
from copy import deepcopy

class FederatedClient:
    """Federated learning client"""

    def __init__(
        self,
        model: nn.Module,
        train_loader,
        epochs: int = 5,
        learning_rate: float = 0.01
    ):
        self.model = model
        self.train_loader = train_loader
        self.epochs = epochs
        self.optimizer = torch.optim.SGD(
            model.parameters(),
            lr=learning_rate
        )

    def train_round(self) -> Dict:
        """Train for one federated round"""

        self.model.train()

        for epoch in range(self.epochs):
            for batch_idx, (data, target) in enumerate(self.train_loader):
                self.optimizer.zero_grad()
                output = self.model(data)
                loss = nn.CrossEntropyLoss()(output, target)
                loss.backward()
                self.optimizer.step()

        # Return model updates
        state_dict = self.model.state_dict()

        return {
            'parameters': state_dict,
            'num_samples': len(self.train_loader.dataset)
        }

class FederatedServer:
    """Federated learning server"""

    def __init__(self, model: nn.Module):
        self.global_model = model
        self.round = 0

    def aggregate_updates(
        self,
        client_updates: List[Dict],
        differential_privacy: bool = False,
        epsilon: float = 1.0
    ) -> Dict:
        """Aggregate client updates using federated averaging"""

        self.round += 1

        # Calculate total samples
        total_samples = sum(
            update['num_samples']
            for update in client_updates
        )

        # Initialize aggregated parameters
        aggregated_params = {}

        # Get parameter names
        param_names = client_updates[0]['parameters'].keys()

        for param_name in param_names:
            # Weighted average of parameters
            weighted_sum = None
            weight_sum = 0

            for update in client_updates:
                weight = update['num_samples'] / total_samples
                params = update['parameters'][param_name]

                if weighted_sum is None:
                    weighted_sum = params * weight
                else:
                    weighted_sum += params * weight

                weight_sum += weight

            aggregated_params[param_name] = weighted_sum

            # Add differential privacy noise
            if differential_privacy:
                sensitivity = 2.0 / total_samples  # L2 sensitivity
                sigma = sensitivity / epsilon
                noise = torch.randn_like(aggregated_params[param_name]) * sigma
                aggregated_params[param_name] += noise

        # Update global model
        self.global_model.load_state_dict(aggregated_params)

        # Evaluate global model
        metrics = self._evaluate_global_model()

        return {
            'round': self.round,
            'clients': len(client_updates),
            'total_samples': total_samples,
            'metrics': metrics
        }

    def _evaluate_global_model(self) -> Dict:
        """Evaluate global model"""

        # Implementation depends on validation set
        return {'accuracy': 0.0}
```

---

## Privacy Preservation

### Differential Privacy

```python
# differential_privacy.py

class DPSGDFederatedClient:
    """Client with differential privacy"""

    def __init__(
        self,
        model: nn.Module,
        train_loader,
        noise_multiplier: float = 0.5,
        max_grad_norm: float = 1.0,
        delta: float = 1e-5
    ):
        self.model = model
        self.train_loader = train_loader
        self.noise_multiplier = noise_multiplier
        self.max_grad_norm = max_grad_norm
        self.delta = delta

    def train_with_dp(self):
        """Train with DP-SGD"""

        for data, target in self.train_loader:
            self.model.zero_grad()
            output = self.model(data)
            loss = nn.CrossEntropyLoss()(output, target)
            loss.backward()

            # Clip gradients
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                self.max_grad_norm
            )

            # Add noise
            for param in self.model.parameters():
                if param.grad is not None:
                    noise = torch.randn_like(param.grad)
                    noise = noise * self.noise_multiplier * self.max_grad_norm
                    param.grad += noise

            # Update
            # optimizer step...
```

---

## Production Deployment

### Federated Learning Orchestration

```python
# federated_orchestration.py

class FederatedLearningOrchestrator:
    """Orchestrate federated learning across clients"""

    def __init__(
        self,
        server: FederatedServer,
        clients: List[FederatedClient],
        min_clients: int = 3,
        rounds: int = 10
    ):
        self.server = server
        self.clients = clients
        self.min_clients = min_clients
        self.rounds = rounds

    def run_federated_learning(self) -> List[Dict]:
        """Run federated learning"""

        history = []

        for round_num in range(self.rounds):
            print(f"\n=== Round {round_num + 1}/{self.rounds} ===")

            # Select clients for this round
            participating_clients = self._select_clients()

            # Send global model to clients
            global_params = self.server.global_model.state_dict()

            client_updates = []

            # Train on each client
            for client in participating_clients:
                # Load global model
                client.model.load_state_dict(global_params)

                # Train locally
                update = client.train_round()
                client_updates.append(update)

            # Aggregate updates
            round_result = self.server.aggregate_updates(client_updates)
            history.append(round_result)

            print(f"✅ Round complete - Accuracy: {round_result['metrics']['accuracy']:.3f}")

        return history

    def _select_clients(self) -> List[FederatedClient]:
        """Randomly select clients for this round"""

        # Ensure minimum participation
        num_clients = max(
            self.min_clients,
            int(len(self.clients) * 0.7)  # 70% participation
        )

        selected = np.random.choice(
            self.clients,
            size=num_clients,
            replace=False
        )

        return list(selected)
```

---

## Related Resources

- **Related:** [5301: Knowledge Distillation](./5301-Knowledge-Distillation.md)
- **Related:** [5302: Distributed Training](./5302-Distributed-Training.md)
- **Related:** [7502: PII Redaction](../../phase7-agentic/7500-security/7502-PII-Redaction.md)


---

## Next Steps

- Continue with: **[../5400-distributed-training/5401-Data-Parallelism.md](./../5400-distributed-training/5401-Data-Parallelism.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Status:** ✅ Complete
