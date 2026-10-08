---
Document ID: SOLUTION-LAB-006
Title: "SOLUTION-LAB-006: Train Model From Scratch"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Tags: ['solution', 'pytorch', 'pretraining']
---

# SOLUTION-LAB-006: Train Model From Scratch

## Overview
Complete solution for training neural networks from scratch using PyTorch.

---

## Prerequisites

```bash
uv pip install torch torchvision matplotlib numpy tensorboard
```

---

## Solution 1: Basic Neural Network

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
import numpy as np


class SimpleNN(nn.Module):
    """Simple feedforward neural network."""

    def __init__(self, input_size=784, hidden_sizes=None, num_classes=10):
        if hidden_sizes is None:
            hidden_sizes = [256, 128]
        super().__init__()

        # Build layers
        layers = []
        prev_size = input_size

        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.BatchNorm1d(hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_size = hidden_size

        # Output layer
        layers.append(nn.Linear(prev_size, num_classes))

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        # Flatten input
        x = x.view(x.size(0), -1)
        return self.network(x)


def create_synthetic_data(n_samples=1000):
    """Create synthetic training data."""

    # Generate random data
    X = torch.randn(n_samples, 784)

    # Generate random labels
    y = torch.randint(0, 10, (n_samples,))

    # Create dataset
    dataset = TensorDataset(X, y)

    return dataset


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""

    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (data, target) in enumerate(dataloader):
        data, target = data.to(device), target.to(device)

        # Zero gradients
        optimizer.zero_grad()

        # Forward pass
        output = model(data)
        loss = criterion(output, target)

        # Backward pass
        loss.backward()

        # Update weights
        optimizer.step()

        # Metrics
        running_loss += loss.item()
        _, predicted = output.max(1)
        total += target.size(0)
        correct += predicted.eq(target).sum().item()

    avg_loss = running_loss / len(dataloader)
    accuracy = 100. * correct / total

    return avg_loss, accuracy


def evaluate(model, dataloader, criterion, device):
    """Evaluate model."""

    model.eval()
    test_loss = 0
    correct = 0
    total = 0

    with torch.no_grad():
        for data, target in dataloader:
            data, target = data.to(device), target.to(device)

            output = model(data)
            test_loss += criterion(output, target).item()

            _, predicted = output.max(1)
            total += target.size(0)
            correct += predicted.eq(target).sum().item()

    test_loss /= len(dataloader)
    accuracy = 100. * correct / total

    return test_loss, accuracy


def train_model(model, train_loader, test_loader, epochs=20):
    """Complete training loop."""

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3
    )

    history = {
        'train_loss': [],
        'train_acc': [],
        'test_loss': [],
        'test_acc': []
    }

    best_acc = 0

    for epoch in range(epochs):
        # Train
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device
        )

        # Evaluate
        test_loss, test_acc = evaluate(
            model, test_loader, criterion, device
        )

        # Update learning rate
        scheduler.step(test_loss)

        # Save best model
        if test_acc > best_acc:
            best_acc = test_acc
            torch.save(model.state_dict(), 'best_model.pth')

        # Record history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['test_loss'].append(test_loss)
        history['test_acc'].append(test_acc)

        print(f'Epoch {epoch+1}/{epochs}:')
        print(f'  Train - Loss: {train_loss:.4f}, Acc: {train_acc:.2f}%')
        print(f'  Test  - Loss: {test_loss:.4f}, Acc: {test_acc:.2f}%')
        print(f'  LR: {optimizer.param_groups[0]["lr"]:.6f}')

    return history


# Usage
if __name__ == "__main__":
    # Create model
    model = SimpleNN(input_size=784, hidden_sizes=[256, 128], num_classes=10)

    # Create data
    train_dataset = create_synthetic_data(1000)
    test_dataset = create_synthetic_data(200)

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # Train
    history = train_model(model, train_loader, test_loader, epochs=20)
```

---

## Solution 2: CNN for Image Classification

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms


class SimpleCNN(nn.Module):
    """Convolutional Neural Network for image classification."""

    def __init__(self, num_classes=10):
        super().__init__()

        # Convolutional layers
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)

        # Batch normalization
        self.bn1 = nn.BatchNorm2d(32)
        self.bn2 = nn.BatchNorm2d(64)
        self.bn3 = nn.BatchNorm2d(128)

        # Pooling
        self.pool = nn.MaxPool2d(2, 2)

        # Fully connected layers
        self.fc1 = nn.Linear(128 * 3 * 3, 256)
        self.fc2 = nn.Linear(256, num_classes)

        # Dropout
        self.dropout = nn.Dropout(0.3)

    def forward(self, x):
        # Conv block 1: 28x28 -> 14x14
        x = self.pool(F.relu(self.bn1(self.conv1(x))))

        # Conv block 2: 14x14 -> 7x7
        x = self.pool(F.relu(self.bn2(self.conv2(x))))

        # Conv block 3: 7x7 -> 3x3
        x = self.pool(F.relu(self.bn3(self.conv3(x))))

        # Flatten
        x = x.view(x.size(0), -1)

        # FC layers
        x = self.dropout(F.relu(self.fc1(x)))
        x = self.fc2(x)

        return x


def load_mnist_data(batch_size=64):
    """Load and preprocess MNIST dataset."""

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    train_dataset = datasets.MNIST(
        './data', train=True, download=True, transform=transform
    )
    test_dataset = datasets.MNIST(
        './data', train=False, download=True, transform=transform
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, test_loader


def train_cnn(model, train_loader, test_loader, epochs=10):
    """Train CNN with early stopping."""

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    best_test_acc = 0
    patience = 3
    patience_counter = 0

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()

        train_acc = 100. * train_correct / train_total

        # Evaluation
        model.eval()
        test_loss = 0
        test_correct = 0
        test_total = 0

        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)

                outputs = model(images)
                test_loss += criterion(outputs, labels).item()

                _, predicted = outputs.max(1)
                test_total += labels.size(0)
                test_correct += predicted.eq(labels).sum().item()

        test_acc = 100. * test_correct / test_total

        print(f'Epoch {epoch+1}:')
        print(f'  Train Acc: {train_acc:.2f}%')
        print(f'  Test Acc: {test_acc:.2f}%')

        # Early stopping
        if test_acc > best_test_acc:
            best_test_acc = test_acc
            patience_counter = 0
            torch.save(model.state_dict(), 'best_cnn.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f'Early stopping at epoch {epoch+1}')
                break

    return model
```

---

## Solution 3: Training with TensorBoard

```python
from torch.utils.tensorboard import SummaryWriter
import torch.nn.functional as F


class TensorBoardTrainer:
    """Trainer with TensorBoard logging."""

    def __init__(self, model, log_dir='./runs'):
        self.model = model
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(model.parameters(), lr=0.001)

        self.writer = SummaryWriter(log_dir)
        self.global_step = 0

    def train_step(self, data, target):
        """Single training step."""

        self.model.train()
        data, target = data.to(self.device), target.to(self.device)

        self.optimizer.zero_grad()
        output = self.model(data)
        loss = self.criterion(output, target)
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def log_metrics(self, loss, accuracy, prefix='train'):
        """Log metrics to TensorBoard."""

        self.writer.add_scalar(f'{prefix}/loss', loss, self.global_step)
        self.writer.add_scalar(f'{prefix}/accuracy', accuracy, self.global_step)

    def log_gradients(self):
        """Log gradient histograms."""

        for name, param in self.model.named_parameters():
            if param.grad is not None:
                self.writer.add_histogram(
                    f'gradients/{name}',
                    param.grad,
                    self.global_step
                )

    def log_weights(self):
        """Log weight histograms."""

        for name, param in self.model.named_parameters():
            self.writer.add_histogram(
                f'weights/{name}',
                param,
                self.global_step
            )

    def train(self, train_loader, test_loader, epochs=10):
        """Train with logging."""

        for epoch in range(epochs):
            # Training
            train_loss = 0
            train_correct = 0
            train_total = 0

            for batch_idx, (data, target) in enumerate(train_loader):
                loss = self.train_step(data, target)

                train_loss += loss
                _, predicted = self.model(data).max(1)
                train_total += target.size(0)
                train_correct += predicted.eq(target).sum().item()

                # Log every 100 batches
                if batch_idx % 100 == 0:
                    avg_loss = train_loss / (batch_idx + 1)
                    avg_acc = 100. * train_correct / train_total

                    self.log_metrics(avg_loss, avg_acc, 'train')
                    self.log_gradients()

                    self.global_step += 1

            # Log weights at end of epoch
            self.log_weights()

            # Validation
            test_loss, test_acc = self.evaluate(test_loader)
            self.log_metrics(test_loss, test_acc, 'test')

            print(f'Epoch {epoch+1}: Train Acc: {100. * train_correct / train_total:.2f}%, Test Acc: {test_acc:.2f}%')

        self.writer.close()

    def evaluate(self, dataloader):
        """Evaluate model."""

        self.model.eval()
        test_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for data, target in dataloader:
                data, target = data.to(self.device), target.to(self.device)

                output = self.model(data)
                test_loss += self.criterion(output, target).item()

                _, predicted = output.max(1)
                total += target.size(0)
                correct += predicted.eq(target).sum().item()

        return test_loss / len(dataloader), 100. * correct / total
```

---

## Solution 4: Custom Training Loop with Mixup

```python
import numpy as np


def mixup_data(x, y, alpha=0.2):
    """Apply mixup augmentation."""

    if alpha > 0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1

    batch_size = x.size(0)
    index = torch.randperm(batch_size).to(x.device)

    mixed_x = lam * x + (1 - lam) * x[index, :]
    y_a, y_b = y, y[index]

    return mixed_x, y_a, y_b, lam


def mixup_criterion(criterion, pred, y_a, y_b, lam):
    """Mixup loss criterion."""

    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)


def train_with_mixup(model, train_loader, test_loader, epochs=20, mixup_alpha=0.2):
    """Train with mixup augmentation."""

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.1, momentum=0.9, weight_decay=5e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_acc = 0

    for epoch in range(epochs):
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            # Apply mixup
            images, labels_a, labels_b, lam = mixup_data(images, labels, mixup_alpha)

            # Forward
            outputs = model(images)

            # Mixup loss
            loss = mixup_criterion(criterion, outputs, labels_a, labels_b, lam)

            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)

            # For mixup, use hard labels for accuracy
            train_correct += (lam * predicted.eq(labels_a).sum().item() +
                             (1 - lam) * predicted.eq(labels_b).sum().item())

        # Scheduler step
        scheduler.step()

        # Evaluate
        model.eval()
        test_correct = 0
        test_total = 0

        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                test_total += labels.size(0)
                test_correct += predicted.eq(labels).sum().item()

        test_acc = 100. * test_correct / test_total

        if test_acc > best_acc:
            best_acc = test_acc
            torch.save(model.state_dict(), 'best_mixup_model.pth')

        print(f'Epoch {epoch+1}: Test Acc: {test_acc:.2f}%, Best: {best_acc:.2f}%')

    return model
```

---

## Solution 5: Learning Rate Finder

```python
class LRFinder:
    """Learning rate finder for optimal LR selection."""

    def __init__(self, model, optimizer, criterion, device=None):
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.history = {'lr': [], 'loss': []}

    def range_test(self, train_loader, start_lr=1e-7, end_lr=10, num_iter=100):
        """Find optimal learning rate range."""

        model = self.model.to(self.device)
        model.train()

        start_log_lr = np.log10(start_lr)
        end_log_lr = np.log10(end_lr)

        lr_factor = (end_log_lr - start_log_lr) / num_iter

        iteration = 0
        optimizer = self.optimizer

        for param_group in optimizer.param_groups:
            param_group['lr'] = start_lr

        for data, target in train_loader:
            if iteration >= num_iter:
                break

            data, target = data.to(self.device), target.to(self.device)

            optimizer.zero_grad()
            output = model(data)
            loss = self.criterion(output, target)

            loss.backward()
            optimizer.step()

            # Record
            lr = optimizer.param_groups[0]['lr']
            self.history['lr'].append(lr)
            self.history['loss'].append(loss.item())

            # Update learning rate
            for param_group in optimizer.param_groups:
                param_group['lr'] = 10 ** (np.log10(lr) + lr_factor)

            iteration += 1

        return self.history

    def plot(self):
        """Plot learning rate vs loss."""

        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 6))
        plt.plot(self.history['lr'], self.history['loss'])
        plt.xscale('log')
        plt.xlabel('Learning Rate')
        plt.ylabel('Loss')
        plt.title('Learning Rate Finder')
        plt.grid(True)
        plt.show()


def find_lr(model, train_loader):
    """Use LR finder to get optimal learning rate."""

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-7)

    lr_finder = LRFinder(model, optimizer, criterion)
    history = lr_finder.range_test(train_loader, start_lr=1e-7, end_lr=1, num_iter=100)

    lr_finder.plot()

    # Find LR with steepest descent
    losses = np.array(history['loss'])
    lrs = np.array(history['lr'])

    gradients = np.gradient(losses)
    steepest_idx = np.argmin(gradients)

    suggested_lr = lrs[steepest_idx]

    print(f"Suggested learning rate: {suggested_lr:.2e}")

    return suggested_lr
```

---

## Solution 6: Model Checkpointing and Resuming

```python
class CheckpointManager:
    """Manage model checkpoints during training."""

    def __init__(self, model, optimizer, save_dir='./checkpoints'):
        self.model = model
        self.optimizer = optimizer
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.best_acc = 0
        self.start_epoch = 0

    def save_checkpoint(self, epoch, acc, filename=None):
        """Save training checkpoint."""

        if filename is None:
            filename = self.save_dir / f'checkpoint_epoch_{epoch}.pth'

        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'accuracy': acc,
            'best_acc': self.best_acc
        }

        torch.save(checkpoint, filename)
        print(f'Checkpoint saved: {filename}')

    def save_best(self, epoch, acc):
        """Save best model."""

        if acc > self.best_acc:
            self.best_acc = acc
            self.save_checkpoint(epoch, acc, self.save_dir / 'best_model.pth')

    def load_checkpoint(self, filename):
        """Load training checkpoint."""

        checkpoint = torch.load(filename, weights_only=True)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.start_epoch = checkpoint['epoch'] + 1
        self.best_acc = checkpoint['best_acc']

        print(f'Checkpoint loaded: {filename}')
        print(f'Resuming from epoch {self.start_epoch}, best acc: {self.best_acc:.2f}%')

        return checkpoint['epoch'], checkpoint['accuracy']


def train_with_checkpointing(model, train_loader, test_loader, epochs=20):
    """Train with automatic checkpointing."""

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    checkpoint_manager = CheckpointManager(model, optimizer)

    start_epoch = 0

    # Try to load existing checkpoint
    checkpoint_path = Path('./checkpoints/best_model.pth')
    if checkpoint_path.exists():
        start_epoch, _ = checkpoint_manager.load_checkpoint(checkpoint_path)

    for epoch in range(start_epoch, epochs):
        # Training
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0

        for data, target in train_loader:
            data, target = data.to(device), target.to(device)

            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            _, predicted = output.max(1)
            train_total += target.size(0)
            train_correct += predicted.eq(target).sum().item()

        train_acc = 100. * train_correct / train_total

        # Evaluation
        model.eval()
        test_correct = 0
        test_total = 0

        with torch.no_grad():
            for data, target in test_loader:
                data, target = data.to(device), target.to(device)
                output = model(data)
                _, predicted = output.max(1)
                test_total += target.size(0)
                test_correct += predicted.eq(target).sum().item()

        test_acc = 100. * test_correct / test_total

        print(f'Epoch {epoch+1}: Train Acc: {train_acc:.2f}%, Test Acc: {test_acc:.2f}%')

        # Save checkpoint
        checkpoint_manager.save_best(epoch, test_acc)

        # Save every 5 epochs
        if (epoch + 1) % 5 == 0:
            checkpoint_manager.save_checkpoint(epoch, test_acc)

    return model
```

---

## Expected Results

### Training Metrics
- **Loss:** Should decrease steadily
- **Accuracy:** Should reach >95% on MNIST
- **Convergence:** Usually within 10-20 epochs

### Model Performance
- **Simple NN:** ~92-95% on MNIST
- **CNN:** ~98-99% on MNIST
- **With Mixup:** Slightly better generalization

---

**Difficulty:** ⭐⭐⭐ Advanced

**Lines of Code:** ~550
