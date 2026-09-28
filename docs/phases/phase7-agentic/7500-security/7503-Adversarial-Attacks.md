---
Document ID: 7503
Title: Adversarial Attacks & Defense
Phase: 7
Module: 7500
Last Updated: 2026-09-28
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'security', 'prompt-injection', 'pii', 'adversarial']
---

# 7503: Adversarial Attacks & Defense

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Adversarial Attack Types](#adversarial-attack-types)
- [Common Attack Methods](#common-attack-methods)
- [Defense Strategies](#defense-strategies)
- [Robustness Evaluation](#robustness-evaluation)
- [Production Deployment](#production-deployment)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Trigger an FGSM attack on a linear classifier and predict the gradient sign pattern it exploits
- Compute the epsilon at which a sample flips class with the d − 4ε flip rule and match it against the sweep table
- Strip epsilon-scale perturbations with bit-depth reduction and measure the JPEG defense's own error floor
- Tune detector thresholds so confidence and ensemble methods flag the adversarial sample without flagging the clean one
- Run the epsilon sweep and read the accuracy collapse out of the robustness table
- Quarantine a flagged input in the secure pipeline and state what the 2-bit defense does and does not repair

---

## Abstract

Adversarial attacks move an input a hair's width — bounded by ε in the L∞ norm — along the gradient of the model's own loss until the prediction flips. This lesson runs that story end to end on a fixed-weight linear classifier with real torch: FGSM flips the sample at ε = 0.35 exactly where the hand-derived flip rule says it must, the ε-sweep collapses accuracy 100% → 87.5% → 0% on schedule, and the defense stack shows its honest boundaries — bit-depth reduction erases ε-scale noise completely but cannot undo a large gradient-aligned perturbation, the gradient-norm detector flags everything at its default threshold, and the secure pipeline's real win is the quarantine flag, not a repaired prediction. Five of the eight code fences execute in this repo with verified output; three (the HF text classifier, the universal perturbation that streams a training set, and full adversarial training epochs) are compile-checked.

---

## Adversarial Attack Types

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                     Adversarial Attack Landscape                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  BY SCOPE            BY KNOWLEDGE        BY TARGET                       │
│                                                                          │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────────────┐      │
│  │ Per-input     │   │ White-box:    │   │ Untargeted: any       │      │
│  │ (FGSM, PGD)   │   │ gradients     │   │ wrong class is a win  │      │
│  └───────────────┘   │ available     │   └───────────────────────┘      │
│                      └───────────────┘                                  │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────────────┐      │
│  │ Universal     │   │ Black-box:    │   │ Targeted: force a     │      │
│  │ (one noise,   │   │ queries only  │   │ chosen wrong class    │      │
│  │ many inputs)  │   └───────────────┘   └───────────────────────┘      │
│  └───────────────┘                                                         │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ Defenses: adversarial training | input preprocessing | detection │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

An adversarial example is an input perturbed by the smallest change that changes the model's mind. The attack is not noise — it is the gradient of the model's loss with respect to its input, sign-quantized and scaled by ε. Every defense in this lesson is measured against that fact.

### Modern Context (2026)

- **The LLM-era surface is bigger than pixels.** FGSM/PGD remain the standard attacks on vision classifiers, but an agentic system's attack surface adds prompt-level manipulation (covered in [7501: Prompt Injection Defense](7501-Prompt-Injection-Defense.md)) and data-layer privacy attacks (covered in [7502: PII Redaction & Privacy Filtering](7502-PII-Redaction.md)). Adversarial robustness is one layer of the security stack, not the whole story.
- **Feature squeezing is the canonical cheap defense.** Bit-depth reduction and median smoothing (Xu et al.) cost almost nothing at inference time and work by collapsing the input's precision — this lesson measures exactly where that trick stops working.
- **Adversarial training is still the strongest empirical defense.** PGD-based training (Madry et al., 2018) remains the reference point; randomized smoothing is the certified-robustness baseline for guarantees.
- **Packaged tooling exists.** Foolbox, torchattacks, and IBM's Adversarial Robustness Toolbox implement these attacks and defenses; install with uv: `uv pip install adversarial-robustness-toolbox`. This lesson builds the primitives by hand first so the library calls are not magic.

---

## Common Attack Methods

### 1. FGSM — Fast Gradient Sign Method

The attack stack needs torch — already installed in this repo (`uv pip install torch`). The target model is a 4-feature, 2-class linear classifier with fixed weights so every number in the lesson is reproducible and hand-checkable. One fix from the original draft matters: marking the input as the optimization variable is a method call, `input_tensor.requires_grad_(True)` — the chained-assignment form in the original code was a syntax error.

```python
# fgsm_attack.py
import torch
import torch.nn as nn


class TinyClassifier(nn.Module):
    """Fixed-weight linear classifier: the attack target."""

    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(4, 2)
        with torch.no_grad():
            self.fc.weight.copy_(torch.tensor([[1.0, -1.0, 2.0, 0.0],
                                               [-1.0, 1.0, -2.0, 0.0]]))
            self.fc.bias.zero_()

    def forward(self, x):
        return self.fc(x)


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
    ) -> tuple:
        """Generate adversarial example using FGSM"""

        # Clone input and mark it as the variable being attacked
        input_tensor = input_tensor.clone().detach().requires_grad_(True)
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

        sign_data_grad = data_grad.sign()
        perturbed = input_tensor + self.epsilon * sign_data_grad
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
            adv_input, _ = self.attack(inputs[i:i+1], targets[i:i+1])
            adversarial_inputs.append(adv_input)
        return torch.cat(adversarial_inputs, dim=0)


victim = TinyClassifier()
x_clean = torch.tensor([[0.6, 0.4, 0.5, 0.8]])
y0 = torch.tensor([0])
fgsm = FGSMAttack(victim, epsilon=0.35)
x_adv, data_grad = fgsm.attack(x_clean, y0)
clean_conf = torch.softmax(victim(x_clean), dim=1).max().item()
adv_conf = torch.softmax(victim(x_adv), dim=1).max().item()
print("grad sign:", data_grad.sign().tolist())
print(f"clean: class {victim(x_clean).argmax().item()} (confidence {clean_conf:.3f})")
print(f"adversarial: class {victim(x_adv).argmax().item()} (confidence {adv_conf:.3f})")
print(f"Linf perturbation: {(x_adv - x_clean).abs().max().item():.4f} (epsilon {fgsm.epsilon})")
print(f"prediction flipped: {victim(x_clean).argmax().item() != victim(x_adv).argmax().item()}")
print("x_adv =", [[round(v, 2) for v in row] for row in x_adv.tolist()])
# Output: grad sign: [[-1.0, 1.0, -1.0, 0.0]]
# Output: clean: class 0 (confidence 0.917)
# Output: adversarial: class 1 (confidence 0.599)
# Output: Linf perturbation: 0.3500 (epsilon 0.35)
# Output: prediction flipped: True
# Output: x_adv = [[0.25, 0.75, 0.15, 0.8]]
```

Read the sign pattern off the weights. With `w0 = [1, −1, 2, 0]` and `w1 = −w0`, zero bias, the class-0 logit is `l0 = x0 − x1 + 2·x2` and the gap between the classes is `g = 2·d` with `d = x0 − x1 + 2·x2`. The loss gradient with respect to the input is `−2·p1·w0`, so the attack pushes `x0` and `x2` down and `x1` up — exactly the printed sign vector `[-1, +1, -1, 0]` (feature 3 has zero weight, sign zero). Each step moves `d` by `−ε − ε − 2ε = −4ε`, giving the **flip rule: the sample flips when `d < 4ε`**. Here `d = 0.6 − 0.4 + 2·0.5 = 1.2` and `4ε = 1.4 > 1.2` — flip. At ε = 0.05, `4ε = 0.2 < 1.2` — the same attack barely dents it, which the pipeline demo at the end of the lesson confirms. The attack moved every feature at most 0.35 and doubled the model's error for free.

### 2. Text-Space Attacks

On text classifiers (toxicity, spam, sentiment), the same idea runs through embeddings: swap synonyms until the prediction flips while a human reads the same sentence. This fence is compile-checked only — it needs a trained HF text classifier.

```python
# text_attacker.py
# Not executed in this repo: needs a trained HF text classifier.
# Compile-checked only.
import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class TextAttacker:
    """Synonym-swap attacks against a text classifier"""

    def __init__(self, model_name: str, attack_budget: int = 3):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()
        self.attack_budget = attack_budget

    def _tokenize(self, text: str) -> torch.Tensor:
        return self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=256
        ).input_ids

    def _predict(self, input_ids: torch.Tensor) -> np.ndarray:
        with torch.no_grad():
            logits = self.model(input_ids).logits
        return torch.softmax(logits, dim=-1).cpu().numpy()

    def synonym_swap(self, text: str, synonym_map: dict) -> str:
        words = text.split()
        swapped = 0
        for i, word in enumerate(words):
            if swapped >= self.attack_budget:
                break
            if word.lower() in synonym_map:
                words[i] = synonym_map[word.lower()]
                swapped += 1
        return " ".join(words)

    def attack(self, text: str, synonym_map: dict) -> dict:
        input_ids = self._tokenize(text)
        original_probs = self._predict(input_ids)
        adversarial_text = self.synonym_swap(text, synonym_map)
        adversarial_probs = self._predict(self._tokenize(adversarial_text))
        return {
            "original_class": int(original_probs.argmax()),
            "adversarial_class": int(adversarial_probs.argmax()),
            "original_confidence": float(original_probs.max()),
            "adversarial_confidence": float(adversarial_probs.max()),
            "flipped": bool(original_probs.argmax() != adversarial_probs.argmax()),
        }
```

The defense-relevant observation: synonym swaps preserve the human reading but move the embedding far more than a 0.35 pixel nudge ever could. Text models have no "small perturbation" notion a human would recognize, so detection and adversarial training matter even more than input preprocessing on the text side.

### 3. Universal Perturbations

A per-input attack crafts noise per image; a universal perturbation is *one* noise tensor that fools the model on most of a dataset. This fence is compile-checked only — generating it streams a training set through the model.

```python
# universal_perturbation.py
# Not executed in this repo: streams a training set through the model.
# Compile-checked only.
import torch
import torch.nn as nn


class UniversalPerturbation:
    """One perturbation that fools the model on many inputs"""

    def __init__(self, model: nn.Module, epsilon: float = 0.1,
                 max_epochs: int = 10):
        self.model = model
        self.model.eval()
        self.epsilon = epsilon
        self.max_epochs = max_epochs
        self.delta = None

    def _fooling_rate(self, data_loader) -> float:
        fooled = total = 0
        for inputs, _targets in data_loader:
            with torch.no_grad():
                clean_pred = self.model(inputs).argmax(dim=1)
                adv_pred = self.model(inputs + self.delta).argmax(dim=1)
            fooled += (adv_pred != clean_pred).sum().item()
            total += _targets.size(0)
        return fooled / total

    def generate(self, data_loader, target_rate: float = 0.8) -> torch.Tensor:
        sample_inputs, _ = next(iter(data_loader))
        self.delta = torch.zeros_like(sample_inputs[0:1])
        for _epoch in range(self.max_epochs):
            for inputs, _targets in data_loader:
                inputs = inputs.clone().detach().requires_grad_(True)
                adv = inputs + self.delta
                # Maximize loss toward the clean prediction: push every
                # input off its own class
                loss = nn.CrossEntropyLoss()(
                    self.model(adv), self.model(inputs).argmax(dim=1)
                )
                self.model.zero_grad()
                loss.backward()
                with torch.no_grad():
                    self.delta += inputs.grad.data.mean(dim=0, keepdim=True)
                    self.delta.clamp_(-self.epsilon, self.epsilon)
            if self._fooling_rate(data_loader) >= target_rate:
                break
        return self.delta
```

Universal perturbations are the deployable nightmare: the noise is a single artifact that can be printed as a sticker or appended to a URL, and it keeps working against every input the model sees until the model is patched.

---

## Defense Strategies

### 1. Adversarial Training

Train on the worst case instead of the average case: for each batch, build PGD adversarial examples and fit the model on those. This fence is compile-checked only — it runs full training epochs.

```python
# adversarial_training.py
# Not executed in this repo: runs full training epochs.
# Compile-checked only.
import torch
import torch.nn as nn


class AdversarialTrainer:
    """PGD-based adversarial training (Madry et al., 2018)"""

    def __init__(self, model: nn.Module, epsilon: float = 0.3,
                 alpha: float = 0.01, num_steps: int = 10,
                 device: str = "cpu"):
        self.model = model
        self.epsilon = epsilon
        self.alpha = alpha
        self.num_steps = num_steps
        self.device = device
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-3)
        self.criterion = nn.CrossEntropyLoss()

    def _pgd_batch(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        delta = torch.zeros_like(inputs, requires_grad=True)
        for _step in range(self.num_steps):
            loss = self.criterion(self.model(inputs + delta), targets)
            loss.backward()
            with torch.no_grad():
                delta += self.alpha * delta.grad.sign()
                delta.clamp_(-self.epsilon, self.epsilon)
            delta.grad.zero_()
        return (inputs + delta.detach()).clamp(0.0, 1.0)

    def train_epoch(self, data_loader) -> float:
        self.model.train()
        total_loss = 0.0
        batches = 0
        for inputs, targets in data_loader:
            inputs = inputs.to(self.device)
            targets = targets.to(self.device)
            adv_inputs = self._pgd_batch(inputs, targets)
            self.optimizer.zero_grad()
            loss = self.criterion(self.model(adv_inputs), targets)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
            batches += 1
        return total_loss / max(batches, 1)
```

The trade is explicit: clean accuracy drops a few points, and the accuracy-vs-ε curve flattens dramatically — the model has seen worst-case inputs during training, so the ε sweep below stops falling off a cliff. Note the training ε (0.3) should match the threat model you actually face; training at the wrong ε defends the wrong radius.

### 2. Input Preprocessing

The cheapest model-agnostic defense: destroy the perturbation before the model sees it. Bit-depth reduction quantizes each value to fewer bits — high-frequency perturbation energy falls between the grid points. JPEG compression does the same in the frequency domain.

```python
# input_defense.py
import io
import random

import numpy as np
from PIL import Image


class InputDefense:
    """Input preprocessing defenses"""

    @staticmethod
    def jpeg_compression(image: np.ndarray, quality: int = 75) -> np.ndarray:
        """JPEG compression defense"""

        pil_image = Image.fromarray((image * 255).astype(np.uint8))
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        decompressed = Image.open(buffer)
        result = np.array(decompressed).astype(np.float32) / 255.0
        return result

    @staticmethod
    def random_resize(image: np.ndarray, ratio_range=(0.9, 1.1)) -> np.ndarray:
        """Random resize defense"""

        pil_image = Image.fromarray((image * 255).astype(np.uint8))
        ratio = random.uniform(*ratio_range)
        new_size = tuple(int(dim * ratio) for dim in pil_image.size)
        resized = pil_image.resize(new_size, Image.Resampling.BILINEAR)
        restored = resized.resize(pil_image.size, Image.Resampling.BILINEAR)
        result = np.array(restored).astype(np.float32) / 255.0
        return result

    @staticmethod
    def bit_reduction(image: np.ndarray, bits: int = 6) -> np.ndarray:
        """Bit depth reduction defense (round to nearest quantization level)"""

        max_val = 2 ** bits - 1
        quantized = np.round(image * max_val) / max_val
        return quantized


defense = InputDefense()
rng = np.random.default_rng(7)
img = np.round(rng.uniform(0.25, 0.75, (16, 16, 3)) * 15) / 15  # grid-aligned (4-bit)

for label, sigma in [("epsilon-scale (sigma=0.01)", 0.01),
                     ("FGSM-scale  (sigma=0.15)", 0.15)]:
    noise = rng.normal(0.0, sigma, (16, 16, 3)).astype(np.float32)
    adv_img = np.clip(img + noise, 0.0, 1.0)
    before = np.abs(adv_img - img).mean()
    after_bit = np.abs(defense.bit_reduction(adv_img, bits=4) - img).mean()
    after_jpg = np.abs(defense.jpeg_compression(adv_img, quality=75) - img).mean()
    print(f"{label}: noise energy before {before:.4f} "
          f"-> 4-bit {after_bit:.4f}, JPEG75 {after_jpg:.4f}")

clean_damage = np.abs(defense.bit_reduction(img, bits=4) - img).mean()
print(f"clean-image damage: 4-bit {clean_damage:.4f}")
# Output: epsilon-scale (sigma=0.01): noise energy before 0.0082 -> 4-bit 0.0000, JPEG75 0.0946
# Output: FGSM-scale  (sigma=0.15): noise energy before 0.1208 -> 4-bit 0.1209, JPEG75 0.1263
# Output: clean-image damage: 4-bit 0.0000
```

Three honest readings of that table. First, bit-depth reduction is *perfect* in its regime: a grid-aligned clean image is untouched (`0.0000` damage) and ε-scale noise falls entirely between quantization levels. Second, it does nothing at FGSM scale — a 0.15-magnitude perturbation is many grid steps wide; quantization cannot undo it (the pipeline demo will show the same for the real attack). Third, JPEG made things *worse* here: its own q=75 reconstruction error on a 16×16 synthetic is ≈0.09, ten times the ε-scale noise. That error floor shrinks on full-resolution photos, where JPEG is a useful high-frequency scrubber — but a defense whose own distortion exceeds the attack is not a defense, and this table is how you find out. Also note two modernization details: `Image.Resampling.BILINEAR` replaces the legacy module-level resampling constant, and rounding (`np.round`) quantizes to the *nearest* level — a floor-based quantizer biases every value downward and inflates the residual.

### 3. Detection-Based Defense

When you cannot remove the perturbation, detect it and refuse. Three signals, one lesson about thresholds:

```python
# adversarial_detector.py
import torch


class AdversarialDetector:
    """Detect adversarial examples"""

    def __init__(self, model, threshold: float = 0.5):
        self.model = model
        self.threshold = threshold
        self.model.eval()

    def detect(self, input_tensor: torch.Tensor, method: str = "gradient",
               noise_scale: float = 0.01) -> tuple:
        """Detect if input is adversarial"""

        if method == "gradient":
            return self._gradient_detection(input_tensor)
        elif method == "confidence":
            return self._confidence_detection(input_tensor)
        elif method == "ensemble":
            return self._ensemble_detection(input_tensor, noise_scale)
        raise ValueError(f"unknown detection method: {method}")

    def _gradient_detection(self, input_tensor: torch.Tensor) -> tuple:
        """Detect using gradient statistics"""

        input_tensor = input_tensor.clone().detach().requires_grad_(True)
        output = self.model(input_tensor)
        prediction = output.argmax().item()
        self.model.zero_grad()
        output[0, prediction].backward()
        grad = input_tensor.grad.data
        grad_norm = grad.norm().item()
        is_adversarial = grad_norm > self.threshold
        return is_adversarial, grad_norm

    def _confidence_detection(self, input_tensor: torch.Tensor) -> tuple:
        """Detect using prediction confidence"""

        with torch.no_grad():
            output = self.model(input_tensor)
            probs = torch.softmax(output, dim=1)
            confidence = probs.max().item()
        is_adversarial = confidence < (1 - self.threshold)
        return is_adversarial, confidence

    def _ensemble_detection(self, input_tensor: torch.Tensor,
                            noise_scale: float = 0.01) -> tuple:
        """Detect using ensemble disagreement with the original prediction"""

        with torch.no_grad():
            original = self.model(input_tensor).argmax().item()
        changed = 0
        for _i in range(10):
            noisy_input = input_tensor + noise_scale * torch.randn_like(input_tensor)
            with torch.no_grad():
                if self.model(noisy_input).argmax().item() != original:
                    changed += 1
        disagreement = changed / 10
        is_adversarial = disagreement > 0.3
        return is_adversarial, disagreement


det_gradient = AdversarialDetector(victim, threshold=0.5)
det_confidence = AdversarialDetector(victim, threshold=0.25)
g_clean, norm_clean = det_gradient.detect(x_clean, method="gradient")
g_adv, norm_adv = det_gradient.detect(x_adv, method="gradient")
c_clean, conf_clean = det_confidence.detect(x_clean, method="confidence")
c_adv, conf_adv = det_confidence.detect(x_adv, method="confidence")
print("grad norms:", round(norm_clean, 3), round(norm_adv, 3))
print(f"gradient   (thr 0.50): clean={g_clean} adversarial={g_adv}")
print(f"confidence (thr 0.25): clean={c_clean} adversarial={c_adv}")
torch.manual_seed(7)
e_clean, dis_clean = det_gradient.detect(x_clean, method="ensemble", noise_scale=0.15)
torch.manual_seed(7)
e_adv, dis_adv = det_gradient.detect(x_adv, method="ensemble", noise_scale=0.15)
print(f"ensemble   (noise 0.15, seed 7): clean disagreement {dis_clean:.1f} "
      f"adversarial {dis_adv:.1f}")
# Output: grad norms: 2.449 2.449
# Output: gradient   (thr 0.50): clean=True adversarial=True
# Output: confidence (thr 0.25): clean=False adversarial=True
# Output: ensemble   (noise 0.15, seed 7): clean disagreement 0.0 adversarial 0.6
```

The gradient method flags *both* inputs — and it must: with `w1 = −w0` the gradient magnitude is symmetric across classes, so both norms are identically √6 ≈ 2.449 and any threshold either flags everything or nothing. A detector that flags everything is a no-op; this is what an uncalibrated threshold looks like. The confidence signal separates cleanly — 0.917 versus 0.599 straddles the `confidence < 0.75` gate — and the ensemble signal is the most dramatic: under noise the clean prediction never wavers (0.0 disagreement) while the adversarial one flips in 6 of 10 noisy copies (0.6), because the attack already sits on the decision boundary the noise is shaking. Thresholds are per-model constants: calibrate each signal on your own clean traffic before trusting a single flag.

---

## Robustness Evaluation

The number you ship is not a single attack success rate — it is the accuracy-vs-ε curve.

```python
# robustness_tester.py
import torch
import torch.nn as nn


class RobustnessTester:
    """Test model robustness against adversarial attacks"""

    def __init__(self, model):
        self.model = model
        self.model.eval()

    def test_robustness(self, inputs: torch.Tensor, targets: torch.Tensor,
                        attack_methods: list, epsilons: list) -> dict:
        """Test robustness against multiple attacks"""

        results = {}
        for attack in attack_methods:
            print(f"testing {attack}...")
            results[attack] = {}
            for epsilon in epsilons:
                if attack == "fgsm":
                    acc = self._test_fgsm(inputs, targets, epsilon)
                elif attack == "pgd":
                    acc = self._test_pgd(inputs, targets, epsilon)
                else:
                    raise ValueError(f"unknown attack method: {attack}")
                results[attack][epsilon] = acc
                print(f"  epsilon {epsilon}: accuracy {acc:.2f}%")
        return results

    def _test_fgsm(self, inputs: torch.Tensor, targets: torch.Tensor,
                   epsilon: float) -> float:
        """Test against FGSM attack"""

        fgsm = FGSMAttack(self.model, epsilon=epsilon)
        correct = 0
        total = 0
        adv_inputs = fgsm.attack_batch(inputs, targets)
        with torch.no_grad():
            outputs = self.model(adv_inputs)
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
        return 100. * correct / total

    def _test_pgd(self, inputs: torch.Tensor, targets: torch.Tensor,
                  epsilon: float, num_iter: int = 10) -> float:
        """Test against PGD attack"""

        correct = 0
        total = 0
        adv_inputs = inputs + 0.01 * torch.randn_like(inputs)
        adv_inputs = torch.clamp(adv_inputs, 0, 1)
        for _step in range(num_iter):
            adv_inputs = adv_inputs.clone().detach().requires_grad_(True)
            outputs = self.model(adv_inputs)
            loss = nn.CrossEntropyLoss()(outputs, targets)
            self.model.zero_grad()
            loss.backward()
            data_grad = adv_inputs.grad.data
            perturbed = adv_inputs + epsilon * data_grad.sign()
            perturbed = torch.max(torch.min(perturbed, inputs + epsilon),
                                  inputs - epsilon)
            adv_inputs = torch.clamp(perturbed, 0, 1).detach()
        with torch.no_grad():
            outputs = self.model(adv_inputs)
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
        return 100. * correct / total


rng_batch = np.random.default_rng(7)
batch = torch.tensor(rng_batch.uniform(0.4, 0.6, (8, 4)), dtype=torch.float32)
targets8 = torch.zeros(8, dtype=torch.long)
tester = RobustnessTester(victim)
tester.test_robustness(batch, targets8, attack_methods=["fgsm"],
                       epsilons=[0.01, 0.2, 0.35])
# Output: testing fgsm...
# Output:   epsilon 0.01: accuracy 100.00%
# Output:   epsilon 0.2: accuracy 87.50%
# Output:   epsilon 0.35: accuracy 0.00%
```

The theory from the FGSM section predicts this table before you run it. All eight samples have gap values `d = x0 − x1 + 2·x2` between 0.69 and 1.09, so the flip rule `d < 4ε` gives: at ε = 0.01, `4ε = 0.04` — zero flips, 100.00%. At ε = 0.2, `4ε = 0.8` — exactly one sample (`d ≈ 0.69`) flips, 87.50%. At ε = 0.35, `4ε = 1.4` exceeds every gap — all eight flip, 0.00%. When a sweep table matches a derivation sample-for-sample, you have both a result and a way to notice when a future model change silently breaks one of them. One contract detail in the class: an unimplemented attack raises `ValueError` from the dispatcher instead of the original draft's call to a DeepFool tester that was never defined — an explicit failure at the top of the stack beats an `AttributeError` from inside a test run. Extend the tester by implementing a DeepFool-backed method behind the same signature.

---

## Production Deployment

### Secure Inference Pipeline

Detection and preprocessing compose into a policy: flag, then defend, then serve — with the flag recorded either way.

```python
# secure_pipeline.py
import torch


class SecureInferencePipeline:
    """Secure inference pipeline with adversarial defense"""

    def __init__(self, model, detector_threshold: float = 0.25,
                 defense_bits: int = 2):
        self.model = model
        self.detector = AdversarialDetector(model, threshold=detector_threshold)
        self.defense = InputDefense()
        self.defense_bits = defense_bits

    def predict(self, input_tensor: torch.Tensor) -> dict:
        """Make prediction with security checks"""

        is_adversarial, score = self.detector.detect(input_tensor,
                                                     method="confidence")
        defense_applied = False

        if is_adversarial:
            # Attack outputs carry autograd state; detach before numpy
            input_np = input_tensor.detach().cpu().numpy()
            cleaned = self.defense.bit_reduction(input_np, bits=self.defense_bits)
            input_tensor = torch.from_numpy(cleaned).float()
            defense_applied = True

        with torch.no_grad():
            output = self.model(input_tensor)
            probs = torch.softmax(output, dim=1)

        return {
            'prediction': probs.argmax().item(),
            'confidence': probs.max().item(),
            'adversarial_detected': is_adversarial,
            'defense_applied': defense_applied
        }


pipeline = SecureInferencePipeline(victim)
for label, tensor in [("clean input", x_clean),
                      ("FGSM eps=0.35", x_adv),
                      ("FGSM eps=0.05", torch.tensor([[0.55, 0.45, 0.45, 0.8]]))]:
    result = pipeline.predict(tensor)
    print(f"{label}: pred {result['prediction']} conf {result['confidence']:.3f} "
          f"flagged {result['adversarial_detected']} defended {result['defense_applied']}")
# Output: clean input: pred 0 conf 0.917 flagged False defended False
# Output: FGSM eps=0.35: pred 1 conf 0.661 flagged True defended True
# Output: FGSM eps=0.05: pred 0 conf 0.881 flagged False defended False
```

Look at the middle row without flinching: the defense fired and the prediction is *still class 1*. Two-bit quantization cannot reverse a 0.35-magnitude gradient-aligned perturbation — the preprocessing table already said why. The pipeline's real wins are the two booleans: `adversarial_detected: True` routes the request to quarantine and human review, and the confidence drop (0.917 → 0.661) is itself evidence the input sits on the boundary. The third row is the other half of the story: a weak attack (ε = 0.05, `4ε = 0.2` far below the sample's gap of 1.2) never flips anything and sails through clean. The production posture this supports: preprocessing for ε-scale noise, detection and quarantine for everything larger, adversarial training as the model-side fix that shrinks the vulnerable radius — and logging of every flag, because the flag stream is the sensor that tells you your model is under attack.

### Deployment Checklist

- [ ] Robustness sweep (accuracy vs ε) run before each model release, tracked over time
- [ ] Threat model ε chosen explicitly and matched to the training/preprocessing regime
- [ ] Preprocessing layer in place; its own distortion measured against the attack scale
- [ ] Detector thresholds calibrated on clean traffic; false-positive rate monitored
- [ ] Adversarial flags logged, alerted on, and routed to quarantine — not silently dropped
- [ ] Adversarial training budgeted for models in adversarially exposed environments
- [ ] Model gradient access restricted where the deployment allows (APIs hide gradients)

---

## References

### Related Documents

- [7501: Prompt Injection Defense](7501-Prompt-Injection-Defense.md)
- [7502: PII Redaction & Privacy Filtering](7502-PII-Redaction.md)
- [6501: ML Model Lifecycle Management](../../phase6-rag/6500-mlops-pipelines/6501-ML-Lifecycle-Management.md)
- **Module Experiment:** [EXP_7501: Prompt Injection Experiments](../../../../experiments/EXP_7501_PROMPT_INJECTION.md)

---

## Next Steps

- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Return to: **[Module README](./README.md)**
- Curriculum checkpoint: **[Progress Checkpoint: Phase 7 - Agentic Systems](../CHECKPOINT.md)** — this lesson closes Module 7500 and Phase 7, the final phase of the curriculum.
