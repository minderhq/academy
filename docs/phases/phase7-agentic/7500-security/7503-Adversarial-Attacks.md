---
Document ID: 7503
Title: Adversarial Attacks & Defense
Phase: 7
Module: 7500
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'security', 'prompt-injection', 'pii', 'adversarial']
---

# 7503: Adversarial Attacks & Defense

**Project:** PROJECT-OMEGA
**Phase:** [7500] Security
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2 hours

---

## Abstract

Adversarial attacks attempt to fool AI systems through carefully crafted inputs. This document covers attack vectors, defense strategies, and robustness testing for production AI systems.

---

## Adversarial Attack Types

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   Adversarial Attack Taxonomy                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  WHITE-BOX ATTACKS (Model Known)                                 │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Gradient-based attacks                                       │   │
│  │  • FGSM (Fast Gradient Sign Method)                             │   │
│  │  • PGD (Projected Gradient Descent)                             │   │
│  │  • Carlini & Wagner attack                                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  BLACK-BOX ATTACKS (Model Unknown)                               │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Transfer attacks (use surrogate model)                       │   │
│  │  • Query-based attacks                                          │   │
│  │  • Evolutionary attacks                                         │   │
│  │  • Score-based attacks                                          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  ATTACK DOMAINS                                                   │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Image Classification: Perturb pixels                          │   │
│  │  • NLP: Word substitution, character changes                     │   │
│  │  • Audio: Add noise, frequency manipulation                      │   │
│  │  • Tabular: Feature perturbation                                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Common Attack Methods

### FGSM (Fast Gradient Sign Method)

```python
# fgsm_attack.py
import torch
import torch.nn as nn
from typing import Tuple
import numpy as np

class FGSMAttack:
    """Fast Gradient Sign Method attack"""

    def __init__(self, model: nn.Module, epsilon: float = 0.01):
        self.model = model
        self.model.eval()
        self.epsilon = epsilon

    def attack(
        self,
        input_tensor: torch.Tensor,
        target: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Generate adversarial example using FGSM"""

        # Clone input and require gradient
        input_tensor = input_tensor.clone().detach().requires_grad = True)
        target = target.clone().detach()

        # Forward pass
        output = self.model(input_tensor)

        # Calculate loss
        loss = nn.CrossEntropyLoss()(output, target)

        # Zero gradients, backward pass
        self.model.zero_grad()
        loss.backward()

        # Collect gradient of input
        data_grad = input_tensor.grad.data

        # Create perturbation
        perturbed_data = self.fgsm_attack(input_tensor, data_grad)

        return perturbed_data, data_grad

    def fgsm_attack(
        self,
        input_tensor: torch.Tensor,
        data_grad: torch.Tensor
    ) -> torch.Tensor:
        """Apply FGSM perturbation"""

        # Collect sign of gradient
        sign_data_grad = data_grad.sign()

        # Create perturbation by multiplying with epsilon
        perturbed = input_tensor + self.epsilon * sign_data_grad

        # Clip to maintain valid range [0, 1]
        perturbed = torch.clamp(perturbed, 0, 1)

        return perturbed

    def attack_batch(
        self,
        inputs: torch.Tensor,
        targets: torch.Tensor
    ) -> torch.Tensor:
        """Attack a batch of inputs"""

        adversarial_inputs = []

        for i in range(len(inputs)):
            adv_input, _ = self.attack(
                inputs[i:i+1],
                targets[i:i+1]
            )
            adversarial_inputs.append(adv_input)

        return torch.cat(adversarial_inputs, dim=0)
```

### TextAdversarial Attacks

```python
# text_attacks.py
import torch
from typing import List, Tuple
import random

class TextAttacker:
    """Adversarial attacks for NLP models"""

    def __init__(self, model, tokenizer, max_iterations: int = 50):
        self.model = model
        self.tokenizer = tokenizer
        self.max_iterations = max_iterations

    def word_substitution_attack(
        self,
        text: str,
        target_class: int
    ) -> Tuple[str, List[str]]:
        """Word substitution attack"""

        # Tokenize text
        tokens = text.split()
        adversarial_tokens = tokens.copy()
        substitutions = []

        # Get original prediction
        original_probs = self._predict(text)
        original_class = original_probs.argmax()

        if original_class != target_class:
            return text, []  # Already misclassified

        # Try substituting each word
        for i, word in enumerate(tokens):
            if len(substitutions) >= 5:
                break

            # Get synonyms
            synonyms = self._get_synonyms(word)

            for synonym in synonyms:
                # Create adversarial example
                adversarial_tokens[i] = synonym
                adversarial_text = " ".join(adversarial_tokens)

                # Check if successful
                probs = self._predict(adversarial_text)
                adv_class = probs.argmax()

                if adv_class == target_class:
                    substitutions.append(f"{word} -> {synonym}")
                    tokens[i] = synonym  # Keep substitution
                    break
                else:
                    # Revert if not successful
                    adversarial_tokens[i] = tokens[i]

        adversarial_text = " ".join(adversarial_tokens)

        return adversarial_text, substitutions

    def _get_synonyms(self, word: str, top_k: int = 5) -> List[str]:
        """Get synonyms for word"""

        # Use WordNet or embedding similarity
        # Simplified: return common typos/substitutions

        common_substitutions = {
            'the': ['a', 'an', 'this'],
            'and': ['or', 'but', 'plus'],
            'very': ['really', 'quite', 'extremely'],
            'good': ['great', 'excellent', 'fine'],
            'bad': ['terrible', 'awful', 'poor'],
            # ... more mappings
        }

        return common_substitutions.get(word.lower(), [])

    def _predict(self, text: str) -> np.ndarray:
        """Get model predictions"""

        inputs = self.tokenizer(text, return_tensors="pt")

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

        return probs[0].cpu().numpy()
```

### Universal Adversarial Perturbations

```python
# universal_perturbation.py

class UniversalPerturbation:
    """Generate universal adversarial perturbations"""

    def __init__(self, model, delta: float = 0.1, max_iter: int = 10):
        self.model = model
        self.delta = delta
        self.max_iter = max_iter
        self.universal_perturbation = None

    def generate(
        self,
        data_loader,
        num_samples: int = 100
    ) -> torch.Tensor:
        """Generate universal perturbation"""

        # Initialize perturbation
        self.universal_perturbation = torch.zeros(
            next(iter(data_loader))[0][0].shape[1:]
        )

        for iteration in range(self.max_iter):
            print(f"Iteration {iteration + 1}/{self.max_iter}")

            for batch_idx, (inputs, targets) in enumerate(data_loader):
                if batch_idx >= num_samples:
                    break

                # Find adversarial direction
                direction = self._find_direction(inputs, targets)

                if direction is None:
                    continue

                # Update universal perturbation
                self.universal_perturbation += self.delta * direction
                self.universal_perturbation = torch.clamp(
                    self.universal_perturbation,
                    -self.delta,
                    self.delta
                )

        return self.universal_perturbation

    def _find_direction(
        self,
        inputs: torch.Tensor,
        targets: torch.Tensor
    ) -> torch.Tensor:
        """Find direction for perturbation"""

        worst_direction = None
        worst_success_rate = 0

        # Try random directions
        for _ in range(10):
            direction = torch.randn_like(self.universal_perturbation)
            direction = direction / direction.norm()

            # Apply perturbation
            perturbed_inputs = inputs + self.delta * direction
            perturbed_inputs = torch.clamp(perturbed_inputs, 0, 1)

            # Check success rate
            with torch.no_grad():
                outputs = self.model(perturbed_inputs)
                predictions = outputs.argmax(dim=1)
                success_rate = (predictions != targets).float().mean().item()

            if success_rate > worst_success_rate:
                worst_success_rate = success_rate
                worst_direction = direction

        return worst_direction
```

---

## Defense Strategies

### Adversarial Training

```python
# adversarial_training.py

class AdversarialTraining:
    """Adversarial training for robustness"""

    def __init__(self, model, device="cuda"):
        self.model = model.to(device)
        self.device = device
        self.fgsm = FGSMAttack(model, epsilon=0.01)

    def train_epoch(
        self,
        data_loader,
        optimizer,
        adversarial_ratio: float = 0.5
    ):
        """Train one epoch with adversarial examples"""

        self.model.train()
        total_loss = 0
        correct = 0
        total = 0

        for batch_idx, (inputs, targets) in enumerate(data_loader):
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Generate adversarial examples for some samples
            batch_size = inputs.size(0)
            adv_count = int(batch_size * adversarial_ratio)

            if adv_count > 0:
                adv_inputs, _ = self.fgsm.attack_batch(
                    inputs[:adv_count],
                    targets[:adv_count]
                )
                # Mix clean and adversarial
                inputs = torch.cat([adv_inputs, inputs[adv_count:]], dim=0)
                targets = torch.cat([targets[:adv_count], targets[adv_count:]], dim=0)

            # Forward pass
            optimizer.zero_grad()
            outputs = self.model(inputs)

            # Calculate loss
            loss = nn.CrossEntropyLoss()(outputs, targets)

            # Backward pass
            loss.backward()
            optimizer.step()

            # Metrics
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

        avg_loss = total_loss / len(data_loader)
        accuracy = 100. * correct / total

        return avg_loss, accuracy
```

### Input Preprocessing

```python
# input_defense.py

class InputDefense:
    """Input preprocessing defenses"""

    @staticmethod
    def jpeg_compression(image: np.ndarray, quality: int = 75) -> np.ndarray:
        """JPEG compression defense"""

        from PIL import Image
        import io

        # Convert to PIL Image
        pil_image = Image.fromarray((image * 255).astype(np.uint8))

        # Compress and decompress
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)

        decompressed = Image.open(buffer)
        result = np.array(decompressed).astype(np.float32) / 255.0

        return result

    @staticmethod
    def random_resize(image: np.ndarray, ratio_range=(0.9, 1.1)) -> np.ndarray:
        """Random resize defense"""

        from PIL import Image
        import random

        pil_image = Image.fromarray((image * 255).astype(np.uint8))

        # Random resize ratio
        ratio = random.uniform(*ratio_range)
        new_size = tuple(int(dim * ratio) for dim in pil_image.size)

        resized = pil_image.resize(new_size, Image.BILINEAR)
        # Resize back to original
        restored = resized.resize(pil_image.size, Image.BILINEAR)

        result = np.array(restored).astype(np.float32) / 255.0

        return result

    @staticmethod
    def bit_reduction(image: np.ndarray, bits: int = 6) -> np.ndarray:
        """Bit depth reduction defense"""

        # Reduce color depth
        max_val = 2 ** bits - 1
        quantized = np.floor(image * max_val) / max_val

        return quantized

    @staticmethod
    def total_variance_denoising(
        image: np.ndarray,
        tv_weight: float = 0.1,
        iterations: int = 10
    ) -> np.Tensor:
        """Total variation denoising"""

        from torch.autograd import Variable

        # Convert to tensor
        tensor = torch.from_numpy(image).permute(2, 0, 1).unsqueeze(0).float()

        # Optimize
        denoised = Variable(tensor, requires_grad=True)

        optimizer = torch.optim.LBFGS([denoised])

        for _ in range(iterations):
            def closure():
                optimizer.zero_grad()

                # TV loss
                tv_loss = (
                    torch.mean(torch.abs(denoised[:, :, :, :-1] - denoised[:, :, :, 1:])) +
                    torch.mean(torch.abs(denoised[:, :, :-1, :] - denoised[:, :, 1:, :]))
                )

                # Fidelity loss
                fidelity = torch.mean((denoised - tensor) ** 2)

                loss = tv_loss * tv_weight + fidelity
                loss.backward()

                return loss

            optimizer.step(closure)

        # Convert back to numpy
        result = denoised.squeeze(0).permute(1, 2, 0).detach().numpy()

        return result
```

### Detection-Based Defense

```python
# adversarial_detector.py

class AdversarialDetector:
    """Detect adversarial examples"""

    def __init__(self, model, threshold: float = 0.5):
        self.model = model
        self.threshold = threshold
        self.model.eval()

    def detect(
        self,
        input_tensor: torch.Tensor,
        method: str = "gradient"
    ) -> Tuple[bool, float]:
        """Detect if input is adversarial"""

        if method == "gradient":
            return self._gradient_detection(input_tensor)
        elif method == "prediction_confidence":
            return self._confidence_detection(input_tensor)
        elif method == "ensemble":
            return self._ensemble_detection(input_tensor)

    def _gradient_detection(
        self,
        input_tensor: torch.Tensor
    ) -> Tuple[bool, float]:
        """Detect using gradient statistics"""

        input_tensor = input_tensor.clone().detach().requires_grad = True)

        # Forward pass
        output = self.model(input_tensor)
        prediction = output.argmax().item()

        # Backward pass
        self.model.zero_grad()
        output[0, prediction].backward()

        # Calculate gradient statistics
        grad = input_tensor.grad.data
        grad_norm = grad.norm().item()

        # Adversarial examples have larger gradients
        is_adversarial = grad_norm > self.threshold

        return is_adversarial, grad_norm

    def _confidence_detection(
        self,
        input_tensor: torch.Tensor
    ) -> Tuple[bool, float]:
        """Detect using prediction confidence"""

        with torch.no_grad():
            output = self.model(input_tensor)
            probs = torch.softmax(output, dim=1)
            confidence = probs.max().item()

        # Adversarial examples often have lower confidence
        is_adversarial = confidence < (1 - self.threshold)

        return is_adversarial, confidence

    def _ensemble_detection(
        self,
        input_tensor: torch.Tensor
    ) -> Tuple[bool, float]:
        """Detect using ensemble disagreement"""

        # Add noise multiple times and check consistency
        predictions = []

        for _ in range(10):
            noisy_input = input_tensor + 0.01 * torch.randn_like(input_tensor)

            with torch.no_grad():
                output = self.model(noisy_input)
                prediction = output.argmax().item()
                predictions.append(prediction)

        # Check variance
        unique_predictions = len(set(predictions))
        disagreement = unique_predictions / len(predictions)

        # High disagreement suggests adversarial
        is_adversarial = disagreement > 0.3

        return is_adversarial, disagreement
```

---

## Robustness Evaluation

### Comprehensive Testing

```python
# robustness_test.py

class RobustnessTester:
    """Test model robustness against adversarial attacks"""

    def __init__(self, model, device="cuda"):
        self.model = model.to(device)
        self.device = device
        self.model.eval()

    def test_robustness(
        self,
        test_loader,
        attack_methods: List[str],
        epsilons: List[float] = [0.01, 0.02, 0.03, 0.05, 0.1]
    ) -> Dict:
        """Test robustness against multiple attacks"""

        results = {}

        for attack in attack_methods:
            print(f"\nTesting {attack}...")
            results[attack] = {}

            for epsilon in epsilons:
                print(f"  Epsilon: {epsilon}")

                if attack == "fgsm":
                    acc = self._test_fgsm(test_loader, epsilon)
                elif attack == "pgd":
                    acc = self._test_pgd(test_loader, epsilon)
                elif attack == "deepfool":
                    acc = self._test_deepfool(test_loader)

                results[attack][epsilon] = acc
                print(f"    Accuracy: {acc:.2f}%")

        return results

    def _test_fgsm(
        self,
        test_loader,
        epsilon: float
    ) -> float:
        """Test against FGSM attack"""

        fgsm = FGSMAttack(self.model, epsilon=epsilon)
        correct = 0
        total = 0

        for inputs, targets in test_loader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Generate adversarial examples
            adv_inputs, _ = fgsm.attack_batch(inputs, targets)

            # Test
            with torch.no_grad():
                outputs = self.model(adv_inputs)
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        accuracy = 100. * correct / total

        return accuracy

    def _test_pgd(
        self,
        test_loader,
        epsilon: float,
        num_iter: int = 10
    ) -> float:
        """Test against PGD attack"""

        correct = 0
        total = 0

        for inputs, targets in test_loader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Initialize with FGSM
            adv_inputs = inputs + 0.01 * torch.randn_like(inputs)
            adv_inputs = torch.clamp(adv_inputs, 0, 1)

            # PGD iterations
            for _ in range(num_iter):
                adv_inputs = adv_inputs.clone().detach().requires_grad = True)

                outputs = self.model(adv_inputs)
                loss = nn.CrossEntropyLoss()(outputs, targets)

                self.model.zero_grad()
                loss.backward()

                # Gradient step
                data_grad = adv_inputs.grad.data
                perturbed = adv_inputs + epsilon * data_grad.sign()

                # Project to epsilon ball
                perturbed = torch.max(
                    torch.min(perturbed, inputs + epsilon),
                    inputs - epsilon
                )

                # Clip to valid range
                adv_inputs = torch.clamp(perturbed, 0, 1)

            # Test
            with torch.no_grad():
                outputs = self.model(adv_inputs)
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        accuracy = 100. * correct / total

        return accuracy
```

---

## Production Deployment

### Secure Inference Pipeline

```python
# secure_inference.py

class SecureInferencePipeline:
    """Secure inference pipeline with adversarial defense"""

    def __init__(self, model):
        self.model = model
        self.detector = AdversarialDetector(model)
        self.defense = InputDefense()

    def predict(self, input_tensor: torch.Tensor) -> Dict:
        """Make prediction with security checks"""

        # Step 1: Detect adversarial input
        is_adversarial, score = self.detector.detect(input_tensor)

        if is_adversarial:
            print(f"⚠️ Adversarial input detected (score: {score:.3f})")

            # Step 2: Apply defense
            input_np = input_tensor.cpu().numpy()
            cleaned_input = self.defense.jpeg_compression(input_np)
            cleaned_input = self.defense.bit_reduction(cleaned_input)
            input_tensor = torch.from_numpy(cleaned_input)

        # Step 3: Make prediction
        with torch.no_grad():
            output = self.model(input_tensor)
            probs = torch.softmax(output, dim=1)

        return {
            'prediction': probs.argmax().item(),
            'confidence': probs.max().item(),
            'adversarial_detected': is_adversarial,
            'defense_applied': is_adversarial
        }
```

---

## Related Resources

- **Previous:** [7502: PII Redaction](./7502-PII-Redaction.md)
- **Related:** [6501: ML Lifecycle Management](../phase6-rag/6500-mlops-pipelines/6501-ML-Lifecycle-Management.md)
- **Experiment:** [EXP_7501: Prompt Injection](../../experiments/EXP_7501_PROMPT_INJECTION.md)


---

## Next Steps

- 🎉 **Phase 7 Complete!** You've mastered the entire PROJECT-OMEGA curriculum!
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Status:** ✅ Complete
**Next Steps:** Implement advanced monitoring systems
