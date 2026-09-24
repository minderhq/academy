# 2200: Frameworks - Practice

## Exercises

### Exercise 1: Create a Simple Neural Network

**Objective:** Implement a neural network with specific architecture.

**Solution:**

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SimpleNet(nn.Module):
    """
    Simple neural network with:
    - Input: 10 features
    - Hidden layer: 20 neurons, ReLU activation
    - Output: 5 classes
    """

    def __init__(self):
        super(SimpleNet, self).__init__()

        # Define layers
        self.fc1 = nn.Linear(10, 20)  # Input: 10, Hidden: 20
        self.fc2 = nn.Linear(20, 5)   # Hidden: 20, Output: 5

        # Optional: Initialize weights
        self._init_weights()

    def _init_weights(self):
        """Initialize network weights."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x):
        """
        Forward pass through the network.

        Args:
            x: Input tensor of shape (batch_size, 10)

        Returns:
            Output tensor of shape (batch_size, 5)
        """
        # Hidden layer with ReLU activation
        x = self.fc1(x)
        x = F.relu(x)

        # Output layer (no activation for raw scores)
        x = self.fc2(x)

        return x

# Test the network
print("=== Testing SimpleNet ===\n")

# Create model
model = SimpleNet()
print("Model architecture:")
print(model)

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"\nTotal parameters: {total_params}")
print(f"Trainable parameters: {trainable_params}")

# Test forward pass
batch_size = 4
x = torch.randn(batch_size, 10)  # Batch of 4, 10 features
output = model(x)

print(f"\nInput shape: {x.shape}")
print(f"Output shape: {output.shape}")
print(f"Expected output shape: torch.Size([{batch_size}, 5])")

# Expected output:
# Output shape: torch.Size([4, 5])

# Troubleshooting Tips:
# - If shape mismatch: Check input features (10) and output classes (5)
# - If no gradients: Ensure requires_grad=True for parameters
# - If nan values: Check learning rate and initialization
```

### Exercise 2: Complete Training Loop

**Objective:** Implement a complete training loop with all necessary components.

**Solution:**

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np

# Set random seed for reproducibility
torch.manual_seed(42)
np.random.seed(42)

# Create model
model = SimpleNet()

# Define loss function
criterion = nn.CrossEntropyLoss()

# Define optimizer
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Create dummy data
inputs = torch.randn(100, 10)
labels = torch.randint(0, 5, (100,))

# Create dataset and dataloader
dataset = TensorDataset(inputs, labels)
dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

# Training loop
print("=== Training SimpleNet ===\n")

num_epochs = 5

for epoch in range(num_epochs):
    model.train()  # Set model to training mode

    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (batch_inputs, batch_labels) in enumerate(dataloader):
        # Forward pass
        outputs = model(batch_inputs)
        loss = criterion(outputs, batch_labels)

        # Backward pass
        optimizer.zero_grad()  # Clear gradients
        loss.backward()        # Compute gradients
        optimizer.step()       # Update parameters

        # Statistics
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += batch_labels.size(0)
        correct += (predicted == batch_labels).sum().item()

    # Compute epoch statistics
    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total

    print(f"Epoch [{epoch+1}/{num_epochs}]")
    print(f"  Loss: {epoch_loss:.4f}")
    print(f"  Accuracy: {epoch_acc:.2f}%")
    print()

# Expected output:
# Epoch 1-5 with decreasing loss and increasing accuracy
# Final accuracy should be > 80% (since data is random, actual may vary)

print("Training complete!")

# Test evaluation
model.eval()  # Set model to evaluation mode
with torch.no_grad():
    test_input = torch.randn(1, 10)
    test_output = model(test_input)
    _, predicted_class = torch.max(test_output, 1)
    print(f"\nTest prediction: Class {predicted_class.item()}")
```

### Exercise 3: GPU Training

**Objective:** Modify training loop to work on GPU when available.

**Solution:**

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Additional GPU info if available
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Create model and move to device
model = SimpleNet().to(device)

# Define loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Create data
inputs = torch.randn(100, 10)
labels = torch.randint(0, 5, (100,))

# Create dataset and dataloader
dataset = TensorDataset(inputs, labels)
dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

# Training loop with GPU support
print("\n=== Training with GPU Support ===\n")

num_epochs = 5

for epoch in range(num_epochs):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_inputs, batch_labels in dataloader:
        # Move data to device
        batch_inputs = batch_inputs.to(device)
        batch_labels = batch_labels.to(device)

        # Forward pass
        outputs = model(batch_inputs)
        loss = criterion(outputs, batch_labels)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Statistics
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += batch_labels.size(0)
        correct += (predicted == batch_labels).sum().item()

    epoch_loss = running_loss / len(dataloader)
    epoch_acc = 100 * correct / total

    print(f"Epoch [{epoch+1}/{num_epochs}]")
    print(f"  Loss: {epoch_loss:.4f}")
    print(f"  Accuracy: {epoch_acc:.2f}%")

# Evaluation
print("\n=== Evaluation ===")
model.eval()

with torch.no_grad():
    # Create test data
    test_input = torch.randn(10, 10).to(device)

    # Forward pass
    test_output = model(test_input)
    _, predicted = torch.max(test_output, 1)

    print(f"Predictions: {predicted.cpu().numpy()}")

# Expected output:
# If GPU available: Training runs on GPU
# If no GPU: Training runs on CPU with warning
# Predictions for 10 test samples
```

### Exercise 4: Save and Load Models

**Objective:** Implement model checkpointing and loading.

**Solution:**

```python
import os

# Create directory for checkpoints
os.makedirs('checkpoints', exist_ok=True)

# 1. Save entire model
print("=== Saving and Loading Models ===\n")

# Save model
model_path = 'checkpoints/simplenet.pth'
torch.save(model, model_path)
print(f"Saved entire model to {model_path}")

# Load model
loaded_model = torch.load(model_path)
loaded_model.eval()
print("Loaded entire model")

# 2. Save only state dictionary (recommended)
state_dict_path = 'checkpoints/simplenet_state_dict.pth'
torch.save(model.state_dict(), state_dict_path)
print(f"\nSaved state dictionary to {state_dict_path}")

# Load state dictionary
new_model = SimpleNet()
new_model.load_state_dict(torch.load(state_dict_path))
new_model.eval()
print("Loaded state dictionary into new model")

# 3. Save checkpoint with additional information
checkpoint_path = 'checkpoints/simplenet_checkpoint.pth'
checkpoint = {
    'epoch': 5,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': 0.1234,
}
torch.save(checkpoint, checkpoint_path)
print(f"\nSaved checkpoint to {checkpoint_path}")

# Load checkpoint
loaded_checkpoint = torch.load(checkpoint_path)
print(f"Loaded checkpoint from epoch {loaded_checkpoint['epoch']}")
print(f"Checkpoint loss: {loaded_checkpoint['loss']:.4f}")

# Restore model and optimizer from checkpoint
restored_model = SimpleNet()
restored_optimizer = optim.Adam(restored_model.parameters(), lr=0.001)

restored_model.load_state_dict(loaded_checkpoint['model_state_dict'])
restored_optimizer.load_state_dict(loaded_checkpoint['optimizer_state_dict'])

print("Restored model and optimizer from checkpoint")

# Expected output:
# Model saved and loaded successfully
# Checkpoint contains epoch, model, optimizer, and loss
```

### Exercise 5: Evaluation Metrics

**Objective:** Implement comprehensive evaluation metrics.

**Solution:**

```python
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def evaluate_model(model, dataloader, device):
    """
    Comprehensive model evaluation.

    Args:
        model: Trained model
        dataloader: Test data loader
        device: Device to run evaluation on

    Returns:
        Dictionary of metrics
    """
    model.eval()

    all_predictions = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)

            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # Convert to numpy arrays
    all_predictions = np.array(all_predictions)
    all_labels = np.array(all_labels)

    # Compute metrics
    metrics = {
        'accuracy': accuracy_score(all_labels, all_predictions),
        'precision_macro': precision_score(all_labels, all_predictions, average='macro', zero_division=0),
        'recall_macro': recall_score(all_labels, all_predictions, average='macro', zero_division=0),
        'f1_macro': f1_score(all_labels, all_predictions, average='macro', zero_division=0),
        'confusion_matrix': confusion_matrix(all_labels, all_predictions)
    }

    return metrics

# Create test dataset
test_inputs = torch.randn(50, 10)
test_labels = torch.randint(0, 5, (50,))
test_dataset = TensorDataset(test_inputs, test_labels)
test_dataloader = DataLoader(test_dataset, batch_size=10, shuffle=False)

# Evaluate model
print("=== Model Evaluation ===\n")

metrics = evaluate_model(model, test_dataloader, device)

print("Performance Metrics:")
print(f"  Accuracy:    {metrics['accuracy']:.4f}")
print(f"  Precision:   {metrics['precision_macro']:.4f}")
print(f"  Recall:      {metrics['recall_macro']:.4f}")
print(f"  F1 Score:    {metrics['f1_macro']:.4f}")

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(metrics['confusion_matrix'], annot=True, fmt='d', cmap='Blues')
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('Confusion Matrix')
plt.savefig('confusion_matrix.png', dpi=100, bbox_inches='tight')
print("\nConfusion matrix saved to confusion_matrix.png")

# Expected output:
# Accuracy, precision, recall, and F1 scores
# Confusion matrix visualization

# Troubleshooting Tips:
# - If zero_division warning: Use zero_division=0 parameter
# - If poor metrics: Model needs more training or better architecture
# - If confusion matrix is diagonal: Good predictions
```

### Exercise 6: Batch Normalization

**Objective:** Add batch normalization to improve training stability.

**Solution:**

```python
class SimpleNetWithBN(nn.Module):
    """SimpleNet with batch normalization."""

    def __init__(self):
        super(SimpleNetWithBN, self).__init__()

        # Define layers with batch normalization
        self.fc1 = nn.Linear(10, 20)
        self.bn1 = nn.BatchNorm1d(20)  # Batch norm after first layer
        self.fc2 = nn.Linear(20, 5)

    def forward(self, x):
        # Hidden layer: Linear -> BatchNorm -> ReLU
        x = self.fc1(x)
        x = self.bn1(x)
        x = F.relu(x)

        # Output layer
        x = self.fc2(x)

        return x

# Compare models
print("=== Comparing Models with and without Batch Normalization ===\n")

# Train model without batch norm
model_no_bn = SimpleNet().to(device)
optimizer_no_bn = optim.Adam(model_no_bn.parameters(), lr=0.001)

# Train model with batch norm
model_with_bn = SimpleNetWithBN().to(device)
optimizer_with_bn = optim.Adam(model_with_bn.parameters(), lr=0.001)

# Training function
def train_model(model, optimizer, dataloader, epochs=5):
    """Train model and return loss history."""
    losses = []
    criterion = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0

        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(dataloader)
        losses.append(avg_loss)
        print(f"Epoch {epoch+1}: Loss = {avg_loss:.4f}")

    return losses

# Train both models
print("Training without Batch Normalization:")
losses_no_bn = train_model(model_no_bn, optimizer_no_bn, dataloader)

print("\nTraining with Batch Normalization:")
losses_with_bn = train_model(model_with_bn, optimizer_with_bn, dataloader)

# Plot comparison
plt.figure(figsize=(10, 5))
plt.plot(losses_no_bn, 'o-', label='Without Batch Norm')
plt.plot(losses_with_bn, 's-', label='With Batch Norm')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Loss Comparison')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('batch_norm_comparison.png', dpi=100)
print("\nComparison plot saved to batch_norm_comparison.png")

# Expected output:
# Model with batch norm typically trains faster and more stably
# Loss curves show smoother convergence with batch norm
```

---

## Summary

This practice guide covers:

1. **Network Architecture:** Creating neural networks with specific layers and activations
2. **Training Loop:** Complete training with forward/backward passes and optimization
3. **GPU Training:** Utilizing GPU acceleration for faster training
4. **Model Persistence:** Saving and loading models and checkpoints
5. **Evaluation Metrics:** Computing accuracy, precision, recall, and F1 scores
6. **Batch Normalization:** Improving training stability and convergence

**Expected Learning Outcomes:**
- Design and implement neural network architectures
- Write complete training loops with PyTorch
- Utilize GPU acceleration when available
- Save and load trained models
- Evaluate model performance comprehensively
- Apply batch normalization for better training

**Last Updated:** 2026-02-05
**Status:** ✅ Complete
