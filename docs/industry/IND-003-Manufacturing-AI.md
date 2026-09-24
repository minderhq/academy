---
Document ID: IND-003
Title: Manufacturing AI Applications
Category: Industry Solutions
Last Updated: 2026-02-05
Status: Review
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: 6100, 7100
Related: IND-001, IND-002
Tags: ['manufacturing', 'industry', 'ai', 'iot']
---

# IND-003: Manufacturing AI Applications

## Overview

AI is transforming manufacturing through predictive maintenance, quality control, supply chain optimization, and smart factory automation.

## Key Applications

### 1. Predictive Maintenance

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd

class PredictiveMaintenance:
    """AI-driven predictive maintenance system."""

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.scaler = StandardScaler()

    def prepare_features(self, sensor_data):
        """
        Features from IoT sensors:
        - Vibration frequency
        - Temperature
        - Pressure
        - Acoustic emissions
        - Motor current
        """
        features = pd.DataFrame()

        # Time-based features
        features['vibration_rms'] = sensor_data['vibration'].apply(lambda x: np.sqrt(np.mean(x**2)))
        features['vibration_peak'] = sensor_data['vibration'].apply(np.max)
        features['temperature_mean'] = sensor_data['temperature']
        features['temperature_trend'] = sensor_data['temperature'].diff()

        # Frequency domain features
        features['dominant_freq'] = sensor_data['vibration'].apply(
            lambda x: np.fft.fft(x).argmax()
        )

        return self.scaler.fit_transform(features)

    def train(self, historical_data, failure_labels):
        """Train on historical equipment data."""
        X = self.prepare_features(historical_data)
        self.model.fit(X, failure_labels)

    def predict_failure(self, current_sensor_data):
        """Predict probability of failure in next 24 hours."""
        features = self.prepare_features(current_sensor_data)
        probability = self.model.predict_proba(features)[0][1]

        if probability > 0.7:
            return "CRITICAL: Schedule maintenance immediately"
        elif probability > 0.4:
            return "WARNING: Monitor closely, plan maintenance"
        else:
            return "NORMAL: No action needed"

# Integration with LLM for natural language reports
def generate_maintenance_report(equipment_id, sensor_data, predictions):
    """Generate natural language maintenance report."""
    prompt = f"""
    Equipment: {equipment_id}
    Current Status:
    - Vibration: {sensor_data['vibration_mean']:.2f} mm/s
    - Temperature: {sensor_data['temperature']:.1f}°C
    - Pressure: {sensor_data['pressure']:.1f} bar

    AI Prediction: {predictions}

    Generate a maintenance report with:
    1. Summary of current condition
    2. Risk assessment
    3. Recommended actions
    4. Timeline for maintenance
    """

    # Use LLM to generate report
    from transformers import pipeline
    generator = pipeline("text-generation", model="gpt-4")
    report = generator(prompt, max_length=500)

    return report[0]['generated_text']
```

### 2. Computer Vision for Quality Control

```python
import cv2
import torch
from transformers import AutoModelForObjectDetection

class QualityInspection:
    """AI-powered visual quality inspection."""

    def __init__(self):
        # Load pre-trained defect detection model
        self.model = torch.hub.load('pytorch/vision', 'fasterrcnn_resnet50_fpn', pretrained=True)
        self.model.eval()

        # Define defect classes
        self.defect_classes = {
            0: 'scratch',
            1: 'dent',
            2: 'crack',
            3: 'color_variation',
            4: 'misalignment'
        }

    def inspect_product(self, image_path):
        """Inspect product image for defects."""
        # Load and preprocess image
        image = cv2.imread(image_path)
        image_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0

        # Detect defects
        with torch.no_grad():
            predictions = self.model([image_tensor])

        # Process results
        defects = []
        for i, score in enumerate(predictions[0]['scores']):
            if score > 0.7:  # Confidence threshold
                label = predictions[0]['labels'][i].item()
                box = predictions[0]['boxes'][i].tolist()

                defects.append({
                    'type': self.defect_classes.get(label, 'unknown'),
                    'confidence': score.item(),
                    'location': box
                })

        return {
            'passed': len(defects) == 0,
            'defects': defects,
            'timestamp': datetime.now().isoformat()
        }

    def generate_inspection_summary(self, inspection_results):
        """Generate human-readable summary using LLM."""
        prompt = f"""
        Quality Inspection Results:
        - Total inspected: {len(inspection_results)}
        - Passed: {sum(1 for r in inspection_results if r['passed'])}
        - Failed: {sum(1 for r in inspection_results if not r['passed'])}

        Common defect types:
        {self._analyze_defect_patterns(inspection_results)}

        Generate a quality report with recommendations.
        """

        # Use LLM to generate summary
        summary = llm.generate(prompt)
        return summary
```

### 3. Production Line Optimization

```python
class ProductionOptimizer:
    """Optimize production line using RL."""

    def __init__(self, num_machines, num_products):
        self.num_machines = num_machines
        self.num_products = num_products
        self.state_dim = num_machines * 3  # status, load, queue
        self.action_dim = num_machines * num_products

        # RL agent (simplified)
        from stable_baselines3 import PPO
        self.model = PPO("MlpPolicy", self.env, verbose=1)

    def optimize_schedule(self, orders, machine_status):
        """Generate optimal production schedule."""
        # Current state
        state = self._encode_state(orders, machine_status)

        # Get optimal actions from RL model
        actions, _ = self.model.predict(state)

        # Decode actions to schedule
        schedule = self._decode_actions(actions)

        return schedule

    def _encode_state(self, orders, machine_status):
        """Encode current production state."""
        state = []

        for machine in machine_status:
            state.extend([
                machine['status'],  # 0=idle, 1=running, 2=maintenance
                machine['load'],
                len(machine['queue'])
            ])

        return np.array(state)

    def decode_to_schedule(self, actions):
        """Convert RL actions to production schedule."""
        schedule = []

        for i, action in enumerate(actions):
            machine_id = i // self.num_products
            product_id = i % self.num_products

            if action > 0.5:  # Threshold for action
                schedule.append({
                    'machine': machine_id,
                    'product': product_id,
                    'priority': action
                })

        return sorted(schedule, key=lambda x: x['priority'], reverse=True)
```

### 4. Supply Chain Optimization with LLMs

```python
class SupplyChainAgent:
    """AI agent for supply chain management."""

    def __init__(self):
        self.vector_db = QdrantClient()
        self.llm = Ollama(model="llama2")

    def analyze_supply_chain_risks(self, current_state):
        """Analyze supply chain for potential risks."""
        prompt = f"""
        Current Supply Chain Status:
        - Inventory levels: {current_state['inventory']}
        - Supplier lead times: {current_state['lead_times']}
        - Demand forecast: {current_state['demand']}
        - Shipping delays: {current_state['delays']}

        Analyze for:
        1. Potential stockouts
        2. Overstock situations
        3. Supplier reliability issues
        4. Logistics bottlenecks

        Provide recommendations for mitigation.
        """

        response = self.llm.generate(prompt)
        return response

    def optimize_inventory(self, demand_forecast, supplier_data):
        """Optimize inventory levels using AI."""
        # RAG for similar historical situations
        similar_situations = self.vector_db.search(
            collection="supply_chain_history",
            query=demand_forecast,
            limit=5
        )

        # Use LLM to synthesize recommendations
        prompt = f"""
        Based on similar situations:
        {similar_situations}

        Current demand forecast: {demand_forecast}
        Supplier capabilities: {supplier_data}

        Recommend:
        1. Optimal reorder points
        2. Safety stock levels
        3. Diversification strategy
        """

        recommendations = self.llm.generate(prompt)
        return recommendations
```

### 5. Digital Twin with AI

```python
class DigitalTwin:
    """AI-powered digital twin of manufacturing facility."""

    def __init__(self):
        self.simulation_model = None
        self.predictor = None

    def create_from_real_data(self, sensor_data, production_logs):
        """Create digital twin from real-world data."""
        # Train simulation model
        from sklearn.neural_network import MLPRegressor

        self.simulation_model = MLPRegressor(
            hidden_layer_sizes=(128, 64, 32),
            max_iter=1000
        )

        # Prepare training data
        X = self._extract_features(sensor_data)
        y = self._extract_outcomes(production_logs)

        self.simulation_model.fit(X, y)

    def simulate_scenario(self, scenario_config):
        """Simulate what-if scenarios."""
        # Scenario: What if machine X fails?
        # Scenario: What if demand increases by 50%?

        features = self._encode_scenario(scenario_config)
        outcome = self.simulation_model.predict([features])[0]

        return {
            'predicted_output': outcome['output'],
            'predicted_quality': outcome['quality'],
            'predicted_downtime': outcome['downtime'],
            'recommendations': self._generate_recommendations(outcome)
        }

    def real_time_monitoring(self, live_sensor_data):
        """Compare real facility with digital twin."""
        # Get prediction from digital twin
        predicted = self.simulation_model.predict(
            self._extract_features(live_sensor_data)
        )

        # Compare with actual
        actual = live_sensor_data['actual_metrics']

        # Detect anomalies
        anomalies = self._detect_anomalies(predicted, actual)

        if anomalies:
            return self._generate_alerts(anomalies)

        return {"status": "normal", "deviation": "low"}
```

## Implementation Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Manufacturing AI Platform                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   IoT      │  │  Computer  │  │  Sensor    │            │
│  │  Sensors   │→│  Vision    │→│  Analytics  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│         ↓                                    │              │
│         └────────────┬───────────────────────┘              │
│                      ↓                                       │
│              ┌───────────────┐                                │
│              │  Data Lake    │                                │
│              └───────────────┘                                │
│                      ↓                                       │
│      ┌───────────────┼───────────────┐                      │
│      ↓               ↓               ↓                      │
│  ┌────────┐    ┌────────┐    ┌────────┐                    │
│  │  LLM   │    │   ML   │    │   RL   │                    │
│  │ Agents │    │Models  │    │Agents  │                    │
│  └────────┘    └────────┘    └────────┘                    │
│      ↓               ↓               ↓                      │
│      └───────────────┼───────────────┘                      │
│                      ↓                                       │
│              ┌───────────────┐                                │
│              │  Dashboard    │                                │
│              │  & Alerts     │                                │
│              └───────────────┘                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Use Case: End-to-End Implementation

```python
class SmartFactoryAI:
    """Complete AI system for smart manufacturing."""

    def __init__(self):
        self.predictive_maintenance = PredictiveMaintenance()
        self.quality_inspection = QualityInspection()
        self.production_optimizer = ProductionOptimizer(
            num_machines=10,
            num_products=5
        )
        self.supply_chain_agent = SupplyChainAgent()
        self.digital_twin = DigitalTwin()

    def run_real_time_monitoring(self):
        """Main monitoring loop."""
        while True:
            # Collect sensor data
            sensor_data = self._collect_sensor_data()

            # Predictive maintenance
            maintenance_alerts = self.predictive_maintenance.predict_failure(
                sensor_data
            )

            # Quality inspection
            if self._new_product_produced():
                inspection_results = self.quality_inspection.inspect_product(
                    latest_image
                )

            # Production optimization
            if self._need_rescheduling():
                new_schedule = self.production_optimizer.optimize_schedule(
                    current_orders,
                    machine_status
                )

            # Digital twin comparison
            twin_comparison = self.digital_twin.real_time_monitoring(
                sensor_data
            )

            # Generate comprehensive report
            report = self._generate_status_report({
                'maintenance': maintenance_alerts,
                'quality': inspection_results,
                'schedule': new_schedule,
                'digital_twin': twin_comparison
            })

            # Send alerts if needed
            if self._has_critical_issues(report):
                self._send_alerts(report)

            time.sleep(60)  # Check every minute

    def _generate_status_report(self, data):
        """Generate natural language status report."""
        prompt = f"""
        Generate a factory status report:

        Maintenance Alerts: {data['maintenance']}
        Quality Inspection: {data['quality']}
        Production Schedule: {data['schedule']}
        Digital Twin Status: {data['digital_twin']}

        Report format:
        1. Executive Summary
        2. Critical Issues
        3. Recommendations
        4. Next Shift Preview
        """

        # Use LLM to generate report
        report = self.llm.generate(prompt)
        return report
```

## Key Technologies

| Technology | Use Case |
|------------|----------|
| **IoT Sensors** | Real-time data collection |
| **Computer Vision** | Quality inspection |
| **Time Series ML** | Predictive maintenance |
| **Reinforcement Learning** | Production optimization |
| **LLMs + RAG** | Decision support, reporting |
| **Digital Twins** | Simulation, what-if analysis |
| **Edge Computing** | Low-latency inference |

## Best Practices

1. **Start with Predictive Maintenance**
   - Highest ROI
   - Reduces downtime
   - Easy to implement

2. **Use Edge AI for Quality Control**
   - Low latency decisions
   - Reduced bandwidth
   - Privacy-preserving

3. **Implement Digital Twins**
   - Test scenarios safely
   - Optimize processes
   - Train operators

4. **Combine Multiple AI Techniques**
   - LLMs for decision support
   - ML for prediction
   - RL for optimization

---

**Next:** [IND-001: Healthcare AI](./IND-001-Healthcare-AI-Applications.md)

**Last Updated:** 2026-02-05
