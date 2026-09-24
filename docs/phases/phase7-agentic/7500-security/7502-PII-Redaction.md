---
Document ID: 7502
Title: PII Redaction & Privacy Filtering
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

# 7502: PII Redaction & Privacy Filtering

**Project:** AI Engineering Curriculum
**Phase:** [7500] Security
**Last Updated:** 2026-02-04
**Status:** Complete
**Estimated Time:** 2 hours

---

## Abstract

Personally Identifiable Information (PII) redaction is critical for privacy compliance (GDPR, CCPA, HIPAA). This document covers detection, redaction, and secure handling of sensitive data in AI systems.

---

## PII Categories

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PII Classification Matrix                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  DIRECT IDENTIFIERS (High Risk)                                  │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Full Name          • Email Address                             │   │
│  │  • Phone Number       • SSN / Tax ID                              │   │
│  │  • Home Address       • Credit Card Number                        │   │
│  │  • Driver's License   • Passport Number                          │   │
│  │  • Bank Account       • IP Address (sometimes)                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  INDIRECT IDENTIFIERS (Medium Risk)                              │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • First/Last Name    • Date of Birth                            │   │
│  │  • Zip Code + City    • Job Title + Workplace                   │   │
│  │  • Vehicle Plate      • Medical Conditions                       │   │
│  │  • Race/Ethnicity     • Religious Affiliation                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  SENSITIVE CONTEXT (Low-Medium Risk)                            │   │
│  ├──────────────────────────────────────────────────────────────────┤   │
│  │  • Financial Data      • Health Records                          │   │
│  │  • Education Records  • Employment History                       │   │
│  │  • Criminal Records   • Biometric Data                           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PII Detection

### Pattern-Based Detection

```python
# pii_detector.py
import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class PIIType(Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    BANK_ACCOUNT = "bank_account"

@dataclass
class PIIEntity:
    """Detected PII entity"""
    type: PIIType
    text: str
    start: int
    end: int
    confidence: float
    redacted_text: str

class PIIDetector:
    """Detect PII in text using pattern matching"""

    def __init__(self):
        self.patterns = self._load_patterns()

    def _load_patterns(self) -> Dict[PIIType, List[re.Pattern]]:
        """Load regex patterns for PII detection"""

        return {
            PIIType.EMAIL: [
                re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
            ],

            PIIType.PHONE: [
                re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),  # US format
                re.compile(r'\b\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')  # International
            ],

            PIIType.SSN: [
                re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # 123-45-6789
                re.compile(r'\b\d{3}\s\d{2}\s\d{4}\b')  # 123 45 6789
            ],

            PIIType.CREDIT_CARD: [
                re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # 1234 5678 9012 3456
                re.compile(r'\b\d{16}\b')  # 1234567890123456
            ],

            PIIType.IP_ADDRESS: [
                re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
            ],

            PIIType.DATE_OF_BIRTH: [
                re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b', re.IGNORECASE),
                re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b')
            ],

            PIIType.ADDRESS: [
                re.compile(r'\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd)\b', re.IGNORECASE),
                re.compile(r'\d+\s+[A-Z][a-z]+,\s+[A-Z]{2}\s+\d{5}\b', re.IGNORECASE)
            ],

            PIIType.PASSPORT: [
                re.compile(r'\b[A-Z]{1,2}\d{6,9}\b')  # US: A1234567
            ],

            PIIType.DRIVER_LICENSE: [
                re.compile(r'\b[A-Z]{1}-\d{4}-\d{4}-\d{4}-\d{4}\b'),  # California format
                re.compile(r'\b\d{8,9}\b')  # Generic numeric
            ],

            PIIType.BANK_ACCOUNT: [
                re.compile(r'\b\d{10,12}\b'),  # US account numbers
                re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2}\b')  # IBAN partial
            ]
        }

    def detect(self, text: str) -> List[PIIEntity]:
        """Detect all PII in text"""

        entities = []

        for pii_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text)

                for match in matches:
                    entity = PIIEntity(
                        type=pii_type,
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        confidence=self._calculate_confidence(match.group(), pii_type),
                        redacted_text=self._get_redaction(match.group(), pii_type)
                    )

                    entities.append(entity)

        # Remove overlaps (keep longest match)
        entities = self._remove_overlaps(entities)

        return entities

    def _calculate_confidence(self, text: str, pii_type: PIIType) -> float:
        """Calculate confidence score for detection"""

        base_confidence = 0.8

        # Adjust based on type
        if pii_type == PIIType.EMAIL:
            return 0.95  # Email is very reliable
        elif pii_type == PIIType.SSN:
            return 0.90  # SSN pattern is specific
        elif pii_type == PIIType.PHONE:
            return 0.85  # Phone can have false positives
        elif pii_type == PIIType.CREDIT_CARD:
            return 0.95 if self._luhn_check(text) else 0.70

        return base_confidence

    def _luhn_check(self, card_number: str) -> bool:
        """Luhn algorithm for credit card validation"""

        digits = re.sub(r'\D', '', card_number)

        if len(digits) < 13:
            return False

        total = 0
        reverse_digits = digits[::-1]

        for i, digit in enumerate(reverse_digits):
            n = int(digit)

            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9

            total += n

        return total % 10 == 0

    def _get_redaction(self, text: str, pii_type: PIIType) -> str:
        """Get redacted version of text"""

        # Common redaction strategies
        if pii_type == PIIType.EMAIL:
            # john.doe@example.com -> j***@example.com
            username, domain = text.split('@')
            return f"{username[0]}***@{domain}"

        elif pii_type in [PIIType.PHONE, PIIType.SSN, PIIType.CREDIT_CARD]:
            # Show last 4 digits only
            return '*' * (len(text) - 4) + text[-4:]

        elif pii_type == PIIType.ADDRESS:
            return "[ADDRESS REDACTED]"

        else:
            return "[REDACTED]"

    def _remove_overlaps(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Remove overlapping entities, keep longest"""

        if not entities:
            return []

        # Sort by start position, then by length (descending)
        entities.sort(key=lambda e: (e.start, -(e.end - e.start)))

        filtered = [entities[0]]

        for entity in entities[1:]:
            last = filtered[-1]

            # Check for overlap
            if entity.start < last.end:
                # Keep the longer one
                if (entity.end - entity.start) > (last.end - last.start):
                    filtered[-1] = entity
            else:
                filtered.append(entity)

        return filtered
```

### NLP-Based Detection

```python
# pii_nlp_detector.py
import spacy
from typing import List, Set

class NLPPIIDetector:
    """PII detection using NLP models"""

    def __init__(self):
        # Load spaCy model
        self.nlp = spacy.load("en_core_web_lg")

        # PII-related entity labels
        self.pii_labels = {
            'PERSON',      # Names
            'ORG',         # Organizations (workplace)
            'GPE',         # Geopolitical entities (locations)
            'DATE',        # Dates (DOB)
            'TIME',        # Times
            'CARDINAL',    # Numbers (account numbers)
            'EMAIL',       # Emails (if model supports)
            'PHONE',       # Phones (if model supports)
        }

    def detect(self, text: str) -> List[PIIEntity]:
        """Detect PII using NLP"""

        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            if ent.label_ in self.pii_labels:
                pii_type = self._map_spacy_to_pii(ent.label_)
                confidence = self._calculate_confidence(ent)

                entity = PIIEntity(
                    type=pii_type,
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=confidence,
                    redacted_text=self._get_redaction(ent.text, pii_type)
                )

                entities.append(entity)

        return entities

    def _map_spacy_to_pii(self, spacy_label: str) -> PIIType:
        """Map spaCy labels to PII types"""

        mapping = {
            'PERSON': PIIType.ADDRESS,  # Use as indirect identifier
            'ORG': PIIType.ADDRESS,
            'GPE': PIIType.ADDRESS,
            'DATE': PIIType.DATE_OF_BIRTH,
            'EMAIL': PIIType.EMAIL,
            'PHONE': PIIType.PHONE
        }

        return mapping.get(spacy_label, PIIType.ADDRESS)

    def _calculate_confidence(self, ent) -> float:
        """Calculate confidence based on NLP confidence"""

        # Base confidence from NLP model
        base = 0.70

        # Adjust based on context
        # If entity is in quotes or capitalized, higher confidence
        text = ent.text

        if text[0].isupper() and text[-1].isupper():
            base += 0.10  # Acronym-like

        if ent.label_ == 'PERSON' and len(text.split()) >= 2:
            base += 0.15  # Full name

        return min(base, 0.95)

    def _get_redaction(self, text: str, pii_type: PIIType) -> str:
        """Get redacted version"""

        if pii_type == PIIType.DATE_OF_BIRTH:
            return "[DATE REDACTED]"

        # Show first letter for names
        return text[0] + '*' * (len(text) - 1)
```

---

## PII Redaction

### Redaction Strategies

```python
# pii_redactor.py
from typing import List, Literal
import re

RedactionStrategy = Literal[
    'full',           # Complete redaction: [REDACTED]
    'partial',        # Partial redaction: j***@example.com
    'mask',           # Masking: ****-****-****-1234
    'hash',           # Hash replacement: [HASH:abc123]
    'placeholder'     # Generic placeholder: [EMAIL]
]

class PIIRedactor:
    """Redact PII from text"""

    def __init__(
        self,
        detector: PIIDetector,
        default_strategy: RedactionStrategy = 'partial'
    ):
        self.detector = detector
        self.default_strategy = default_strategy

    def redact(
        self,
        text: str,
        strategy: Optional[RedactionStrategy] = None,
        custom_placeholders: Optional[Dict[PIIType, str]] = None
    ) -> Tuple[str, List[PIIEntity]]:
        """Redact PII from text"""

        # Detect PII
        entities = self.detector.detect(text)

        if not entities:
            return text, []

        # Sort by position (reverse order for replacement)
        entities.sort(key=lambda e: e.start, reverse=True)

        # Apply redaction
        redacted_text = text

        for entity in entities:
            redaction_strategy = strategy or self.default_strategy
            redacted_value = self._apply_redaction(
                entity,
                redaction_strategy,
                custom_placeholders
            )

            # Replace in text
            redacted_text = (
                redacted_text[:entity.start] +
                redacted_value +
                redacted_text[entity.end:]
            )

        return redacted_text, entities

    def _apply_redaction(
        self,
        entity: PIIEntity,
        strategy: RedactionStrategy,
        custom_placeholders: Optional[Dict[PIIType, str]]
    ) -> str:

        if custom_placeholders and entity.type in custom_placeholders:
            return custom_placeholders[entity.type]

        if strategy == 'full':
            return "[REDACTED]"

        elif strategy == 'partial':
            return entity.redacted_text

        elif strategy == 'mask':
            # Show only last 4
            return '*' * (len(entity.text) - 4) + entity.text[-4:]

        elif strategy == 'hash':
            import hashlib
            hash_value = hashlib.md5(entity.text.encode()).hexdigest()[:6]
            return f"[HASH:{hash_value}]"

        elif strategy == 'placeholder':
            return f"[{entity.type.value.upper()}]"

        return entity.redacted_text
```

### Presidio Integration

```python
# presidio_redactor.py
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import Dict

class PresidioPIIRedactor:
    """PII redaction using Microsoft Presidio"""

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def redact(
        self,
        text: str,
        operators: Optional[Dict[str, str]] = None
    ) -> str:
        """Redact PII using Presidio"""

        # Default operators
        if operators is None:
            operators = {
                "EMAIL": "mask",
                "PHONE_NUMBER": "mask",
                "SSN": "replace",
                "CREDIT_CARD": "mask",
                "IP_ADDRESS": "hash",
                "PERSON": "redact",
                "LOCATION": "anonymize"
            }

        # Analyze text
        results = self.analyzer.analyze(
            text=text,
            language='en'
        )

        # Anonymize
        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )

        return anonymized.text
```

---

## Secure Data Handling

### Encryption at Rest

```python
# secure_storage.py
from cryptography.fernet import Fernet
from typing import Dict
import json

class SecurePIIStorage:
    """Securely store PII data with encryption"""

    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        self.storage = {}

    def store(
        self,
        user_id: str,
        pii_data: Dict[str, str],
        redacted_text: str
    ) -> str:
        """Store encrypted PII"""

        # Encrypt PII data
        pii_json = json.dumps(pii_data)
        encrypted_pii = self.cipher.encrypt(pii_json.encode())

        # Store reference
        reference_id = f"{user_id}_{hash(encrypted_pii)}"
        self.storage[reference_id] = {
            'encrypted_pii': encrypted_pii,
            'redacted_text': redacted_text
        }

        return reference_id

    def retrieve(self, reference_id: str) -> Dict[str, str]:
        """Retrieve and decrypt PII"""

        if reference_id not in self.storage:
            raise ValueError("Reference not found")

        data = self.storage[reference_id]
        decrypted_pii = self.cipher.decrypt(data['encrypted_pii'])
        pii_data = json.loads(decrypted_pii.decode())

        return pii_data

    def delete(self, reference_id: str) -> bool:
        """Delete PII (GDPR right to be forgotten)"""

        if reference_id in self.storage:
            del self.storage[reference_id]
            return True

        return False
```

### Compliance Logging

```python
# compliance_logger.py
import logging
from datetime import datetime
from typing import List
import json

class ComplianceLogger:
    """Log PII access for compliance"""

    def __init__(self, log_file: str = "pii_access.log"):
        self.logger = logging.getLogger("pii_compliance")
        self.logger.setLevel(logging.INFO)

        # File handler
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        self.logger.addHandler(handler)

    def log_detection(
        self,
        pii_entities: List[PIIEntity],
        user_id: str,
        document_id: str
    ):
        """Log PII detection event"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'pii_detection',
            'user_id': user_id,
            'document_id': document_id,
            'pii_count': len(pii_entities),
            'pii_types': [e.type.value for e in pii_entities],
            'action': 'redacted'
        }

        self.logger.info(json.dumps(log_entry))

    def log_access(
        self,
        reference_id: str,
        user_id: str,
        purpose: str
    ):
        """Log PII access event"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'pii_access',
            'reference_id': reference_id,
            'user_id': user_id,
            'purpose': purpose
        }

        self.logger.info(json.dumps(log_entry))

    def log_deletion(
        self,
        reference_id: str,
        user_id: str,
        reason: str
    ):
        """Log PII deletion event (GDPR)"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'pii_deletion',
            'reference_id': reference_id,
            'user_id': user_id,
            'reason': reason,
            'gdpr_request': True
        }

        self.logger.info(json.dumps(log_entry))
```

---

## Production Implementation

### End-to-End Pipeline

```python
# pii_pipeline.py

class PIIPipeline:
    """End-to-end PII handling pipeline"""

    def __init__(self):
        self.detector = PIIDetector()
        self.nlp_detector = NLPPIIDetector()
        self.redactor = PIIRedactor(self.detector)
        self.storage = SecurePIIStorage(Fernet.generate_key())
        self.logger = ComplianceLogger()

    def process_input(
        self,
        text: str,
        user_id: str,
        store_pii: bool = False
    ) -> Dict:
        """Process input containing potential PII"""

        # Detect PII using multiple methods
        pattern_entities = self.detector.detect(text)
        nlp_entities = self.nlp_detector.detect(text)

        # Merge results
        all_entities = self._merge_entities(pattern_entities, nlp_entities)

        # Redact PII
        redacted_text, _ = self.redactor.redact(text)

        result = {
            'original_text': text,
            'redacted_text': redacted_text,
            'pii_count': len(all_entities),
            'pii_types': list(set(e.type for e in all_entities))
        }

        # Optionally store encrypted PII
        if store_pii and all_entities:
            pii_data = {e.type.value: e.text for e in all_entities}
            reference_id = self.storage.store(user_id, pii_data, redacted_text)
            result['reference_id'] = reference_id

        # Log for compliance
        self.logger.log_detection(
            all_entities,
            user_id,
            f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        return result

    def _merge_entities(
        self,
        entities1: List[PIIEntity],
        entities2: List[PIIEntity]
    ) -> List[PIIEntity]:
        """Merge entities from multiple detectors"""

        # Combine all entities
        all_entities = entities1 + entities2

        # Remove duplicates
        seen = set()
        unique = []

        for entity in all_entities:
            key = (entity.start, entity.end, entity.type)
            if key not in seen:
                seen.add(key)
                unique.append(entity)

        # Remove overlaps
        return self.detector._remove_overlaps(unique)
```

---

## Testing & Validation

### Accuracy Metrics

```python
# pii_validator.py

PII_TEST_CASES = [
    {
        'text': 'Contact John Doe at john.doe@example.com or 555-123-4567',
        'expected_pii': [
            {'type': 'email', 'text': 'john.doe@example.com'},
            {'type': 'phone', 'text': '555-123-4567'},
            {'type': 'person', 'text': 'John Doe'}
        ]
    },
    {
        'text': 'SSN: 123-45-6789, DOB: Jan 15, 1985',
        'expected_pii': [
            {'type': 'ssn', 'text': '123-45-6789'},
            {'type': 'date_of_birth', 'text': 'Jan 15, 1985'}
        ]
    }
]

class PIIValidator:
    """Validate PII detection accuracy"""

    def __init__(self, pipeline: PIIPipeline):
        self.pipeline = pipeline
        self.results = []

    def run_all_tests(self):
        """Run all test cases"""

        for i, test_case in enumerate(PII_TEST_CASES, 1):
            print(f"\nTest Case {i}")

            result = self.pipeline.process_input(
                test_case['text'],
                'test_user'
            )

            # Calculate metrics
            metrics = self._calculate_metrics(
                test_case['expected_pii'],
                result
            )

            self.results.append({
                'test_case': i,
                'metrics': metrics
            })

            print(f"Precision: {metrics['precision']:.2f}")
            print(f"Recall: {metrics['recall']:.2f}")
            print(f"F1: {metrics['f1']:.2f}")

        self._print_summary()

    def _calculate_metrics(self, expected, result):
        """Calculate precision, recall, F1"""

        # Simplified metrics
        expected_count = len(expected)
        detected_count = result['pii_count']

        # True positives (simplified)
        tp = min(expected_count, detected_count)

        precision = tp / detected_count if detected_count > 0 else 0
        recall = tp / expected_count if expected_count > 0 else 0

        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1
        }

    def _print_summary(self):
        """Print test summary"""

        avg_precision = sum(r['metrics']['precision'] for r in self.results) / len(self.results)
        avg_recall = sum(r['metrics']['recall'] for r in self.results) / len(self.results)
        avg_f1 = sum(r['metrics']['f1'] for r in self.results) / len(self.results)

        print(f"\n{'='*50}")
        print(f"AVERAGE METRICS")
        print(f"{'='*50}")
        print(f"Precision: {avg_precision:.3f}")
        print(f"Recall: {avg_recall:.3f}")
        print(f"F1 Score: {avg_f1:.3f}")
```

---

## Related Resources

- **Previous:** [7501: Prompt Injection Defense](./7501-Prompt-Injection-Defense.md)
- **Next:** [7503: Adversarial Attacks](./7503-Adversarial-Attacks.md)
- **Experiment:** [EXP_7501: Prompt Injection](../../../../experiments/EXP_7501_PROMPT_INJECTION.md)


---

## Next Steps

- Continue with: **[7503: Next Document](./7503-Adversarial-Attacks.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Status:** ✅ Complete
**Next Steps:** Implement adversarial attack defenses
