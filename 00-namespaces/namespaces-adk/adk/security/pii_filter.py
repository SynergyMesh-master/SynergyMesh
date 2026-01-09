"""
PII Filter: Detects and redacts personally identifiable information.

This module provides PII detection and redaction capabilities
for data privacy and compliance.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from ..observability.logging import Logger


class PIIType(Enum):
    """Types of PII."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    BANK_ACCOUNT = "bank_account"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"


@dataclass
class PIIMatch:
    """
    A PII match with a confidence score (0.0–1.0) and optional metadata
    describing match context (for example, the path of the matched field).
    """
    pii_type: PIIType
    start: int
    end: int
    value: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pii_type": self.pii_type.value,
            "start": self.start,
            "end": self.end,
            "value": self.value,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


class PIIFilter:
    """
    Detects and redacts PII from text.
    
    Features:
    - Pattern-based PII detection
    - Configurable redaction strategies
    - PII type classification
    - Confidence scoring
    """
    
    # PII patterns
    PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        PIIType.CREDIT_CARD: r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        PIIType.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        PIIType.BANK_ACCOUNT: r'\b\d{8,17}\b',
    }
    
    def __init__(self):
        self.logger = Logger(name="security.pii_filter")
        
        # Compile patterns
        self._compiled_patterns = {
            pii_type: re.compile(pattern)
            for pii_type, pattern in self.PATTERNS.items()
        }
        
        # Custom patterns
        self._custom_patterns: Dict[PIIType, re.Pattern] = {}
    
    def add_custom_pattern(self, pii_type: PIIType, pattern: str) -> None:
        """Add a custom PII pattern."""
        self._custom_patterns[pii_type] = re.compile(pattern)
    
    def detect_pii(self, text: str) -> List[PIIMatch]:
        """Detect PII in text."""
        matches = []
        
        all_patterns = {**self._compiled_patterns, **self._custom_patterns}
        
        for pii_type, pattern in all_patterns.items():
            for match in pattern.finditer(text):
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    start=match.start(),
                    end=match.end(),
                    value=match.group(),
                    confidence=0.8  # Default confidence
                ))
        
        # Sort by start position
        matches.sort(key=lambda m: m.start)
        
        return matches
    
    def redact(
        self,
        text: str,
        redaction_char: str = "*",
        pii_types: Optional[List[PIIType]] = None
    ) -> tuple[str, List[PIIMatch]]:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact
            redaction_char: Character to use for redaction
            pii_types: PII types to redact (None for all)
            
        Returns:
            Tuple of (redacted_text, matches)
        """
        matches = self.detect_pii(text)
        
        # Filter by type
        if pii_types:
            matches = [m for m in matches if m.pii_type in pii_types]
        
        # Build redacted text
        redacted = list(text)
        
        for match in reversed(matches):  # Reverse to preserve indices
            for i in range(match.start, match.end):
                redacted[i] = redaction_char
        
        redacted_text = "".join(redacted)
        
        return redacted_text, matches
    
    def redact_dict(
        self,
        data: Dict[str, Any],
        redaction_char: str = "*"
    ) -> Dict[str, Any]:
        """Redact PII from dictionary."""
        redacted = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted[key], _ = self.redact(value, redaction_char)
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value, redaction_char)
            elif isinstance(value, list):
                redacted[key] = [
                    self.redact(v, redaction_char)[0] if isinstance(v, str) else v
                    for v in value
                ]
            else:
                redacted[key] = value
        
        return redacted
    
    def scan_dict(self, data: Dict[str, Any]) -> List[PIIMatch]:
        """Scan dictionary for PII."""
        matches = []
        
        def scan_value(value: Any, path: str = ""):
            if isinstance(value, str):
                value_matches = self.detect_pii(value)
                for match in value_matches:
                    match.metadata = {"path": path}
                    matches.append(match)
            elif isinstance(value, dict):
                for k, v in value.items():
                    scan_value(v, f"{path}.{k}" if path else k)
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    scan_value(v, f"{path}[{i}]")
        
        scan_value(data)
        return matches
