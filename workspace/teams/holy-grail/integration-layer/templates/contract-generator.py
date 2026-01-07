#!/usr/bin/env python3
"""
==============================================================================
INTELLIGENT CONTRACT GENERATOR
==============================================================================
Version: 2.0.0
Purpose: Generate behavior contracts from natural language descriptions
Features: AI-powered intent analysis, template-based generation, validation
==============================================================================
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

@dataclass
class ContractTemplate:
    """Template for contract generation"""
    template_id: str
    name: str
    category: str
    priority: str
    base_structure: Dict[str, Any]
    required_fields: List[str]
    optional_fields: List[str]
    validation_rules: Dict[str, Any]


@dataclass
class GeneratedContract:
    """Generated contract with metadata"""
    contract_id: str
    contract_definition: Dict[str, Any]
    generation_method: str
    confidence_score: float
    validation_status: str
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


# ============================================================================
# CONTRACT GENERATOR
# ============================================================================

class ContractGenerator:
    """
    Intelligent contract generator with AI-powered intent analysis
    
    Capabilities:
    - Natural language to contract conversion
    - Template-based generation
    - Validation and optimization
    - YAML/JSON export
    """
    
    def __init__(self, templates_path: str = "./templates"):
        """Initialize contract generator"""
        self.templates_path = Path(templates_path)
        self.templates: Dict[str, ContractTemplate] = {}
        self._load_templates()
        
        # Contract ID counter
        self.contract_counter = 1000
    
    def _load_templates(self):
        """Load contract templates"""
        # Define standard templates
        self.templates = {
            "deployment": self._create_deployment_template(),
            "monitoring": self._create_monitoring_template(),
            "optimization": self._create_optimization_template(),
            "security": self._create_security_template(),
            "backup": self._create_backup_template()
        }
    
    def _create_deployment_template(self) -> ContractTemplate:
        """Create deployment automation template"""
        return ContractTemplate(
            template_id="TPL-DEPLOY-001",
            name="Automated Deployment",
            category="ci-cd",
            priority="HIGH",
            base_structure={
                "id": "",
                "name": "",
                "version": "1.0.0",
                "priority": "HIGH",
                "intent": "automate_deployment",
                "conditions": {
                    "triggers": [],
                    "prerequisites": []
                },
                "actions": [],
                "validation_requirements": {
                    "layers": ["L-A", "L-B", "L-C", "L-E"],
                    "gates": []
                },
                "metadata": {
                    "owner": "",
                    "category": "deployment",
                    "tags": []
                }
            },
            required_fields=["name", "intent", "actions"],
            optional_fields=["approval_workflow", "rollback_strategy"],
            validation_rules={}
        )
    
    def _create_monitoring_template(self) -> ContractTemplate:
        """Create monitoring automation template"""
        return ContractTemplate(
            template_id="TPL-MON-001",
            name="Intelligent Monitoring",
            category="observability",
            priority="NORMAL",
            base_structure={
                "id": "",
                "name": "",
                "version": "1.0.0",
                "priority": "NORMAL",
                "intent": "monitor_system_health",
                "conditions": {
                    "triggers": [
                        {"type": "schedule", "cron": "*/5 * * * *"}
                    ],
                    "prerequisites": []
                },
                "actions": [],
                "validation_requirements": {
                    "layers": ["L-A", "L-D", "L-E"],
                    "gates": []
                },
                "metadata": {}
            },
            required_fields=["name", "metrics"],
            optional_fields=["alerting", "dashboards"],
            validation_rules={}
        )
    
    def _create_optimization_template(self) -> ContractTemplate:
        """Create resource optimization template"""
        return ContractTemplate(
            template_id="TPL-OPT-001",
            name="Resource Optimization",
            category="performance",
            priority="NORMAL",
            base_structure={
                "id": "",
                "name": "",
                "version": "1.0.0",
                "priority": "NORMAL",
                "intent": "optimize_resources",
                "conditions": {
                    "triggers": [],
                    "prerequisites": []
                },
                "actions": [],
                "validation_requirements": {
                    "layers": ["L-A", "L-D", "L-E", "L-F"],
                    "gates": []
                },
                "metadata": {}
            },
            required_fields=["name", "optimization_targets"],
            optional_fields=["constraints", "cost_model"],
            validation_rules={}
        )
    
    def _create_security_template(self) -> ContractTemplate:
        """Create security automation template"""
        return ContractTemplate(
            template_id="TPL-SEC-001",
            name="Security Automation",
            category="security",
            priority="CRITICAL",
            base_structure={
                "id": "",
                "name": "",
                "version": "1.0.0",
                "priority": "CRITICAL",
                "intent": "enforce_security",
                "conditions": {
                    "triggers": [],
                    "prerequisites": []
                },
                "actions": [],
                "validation_requirements": {
                    "layers": ["L-A", "L-B", "L-C"],
                    "gates": []
                },
                "metadata": {}
            },
            required_fields=["name", "security_controls"],
            optional_fields=["compliance_frameworks", "audit_trail"],
            validation_rules={}
        )
    
    def _create_backup_template(self) -> ContractTemplate:
        """Create backup automation template"""
        return ContractTemplate(
            template_id="TPL-BACKUP-001",
            name="Automated Backup",
            category="data-protection",
            priority="HIGH",
            base_structure={
                "id": "",
                "name": "",
                "version": "1.0.0",
                "priority": "HIGH",
                "intent": "backup_data",
                "conditions": {
                    "triggers": [
                        {"type": "schedule", "cron": "0 2 * * *"}
                    ],
                    "prerequisites": []
                },
                "actions": [],
                "validation_requirements": {
                    "layers": ["L-A", "L-B", "L-D"],
                    "gates": []
                },
                "metadata": {}
            },
            required_fields=["name", "backup_targets"],
            optional_fields=["retention_policy", "encryption"],
            validation_rules={}
        )
    
    # ------------------------------------------------------------------------
    # GENERATION METHODS
    # ------------------------------------------------------------------------
    
    def generate_from_description(
        self,
        description: str,
        category: Optional[str] = None
    ) -> GeneratedContract:
        """
        Generate contract from natural language description
        
        Args:
            description: Natural language description of desired behavior
            category: Optional category hint (deployment, monitoring, etc.)
        
        Returns:
            GeneratedContract with contract definition
        """
        # Analyze intent
        intent_analysis = self._analyze_intent(description)
        template_id = intent_analysis.get("template", "deployment")
        
        # Get template
        template = self.templates.get(template_id)
        if not template:
            template = self.templates["deployment"]
        
        # Generate contract
        contract_def = self._build_contract_from_template(
            template,
            description,
            intent_analysis
        )
        
        # Validate
        validation = self._validate_contract(contract_def)
        
        # Generate contract ID
        contract_id = self._generate_contract_id(template_id)
        contract_def["id"] = contract_id
        
        return GeneratedContract(
            contract_id=contract_id,
            contract_definition=contract_def,
            generation_method="ai_analysis",
            confidence_score=intent_analysis.get("confidence", 0.8),
            validation_status=validation["status"],
            warnings=validation.get("warnings", []),
            suggestions=validation.get("suggestions", [])
        )
    
    def generate_from_template(
        self,
        template_id: str,
        parameters: Dict[str, Any]
    ) -> GeneratedContract:
        """
        Generate contract from template with parameters
        
        Args:
            template_id: ID of template to use
            parameters: Parameters to populate template
        
        Returns:
            GeneratedContract with contract definition
        """
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Clone base structure
        contract_def = self._deep_copy(template.base_structure)
        
        # Populate with parameters
        contract_def = self._populate_template(contract_def, parameters)
        
        # Generate contract ID
        contract_id = self._generate_contract_id(template_id)
        contract_def["id"] = contract_id
        
        # Validate
        validation = self._validate_contract(contract_def)
        
        return GeneratedContract(
            contract_id=contract_id,
            contract_definition=contract_def,
            generation_method="template",
            confidence_score=1.0,
            validation_status=validation["status"],
            warnings=validation.get("warnings", []),
            suggestions=validation.get("suggestions", [])
        )
    
    def _analyze_intent(self, description: str) -> Dict[str, Any]:
        """
        Analyze intent from natural language description
        
        This is a simplified version. In production, this would use
        Claude or another LLM for sophisticated intent analysis.
        """
        description_lower = description.lower()
        
        # Simple keyword-based classification
        if any(word in description_lower for word in ["deploy", "release", "rollout"]):
            return {
                "template": "deployment",
                "confidence": 0.85,
                "intent": "automate_deployment",
                "actions": ["build", "test", "deploy"]
            }
        elif any(word in description_lower for word in ["monitor", "observe", "track"]):
            return {
                "template": "monitoring",
                "confidence": 0.82,
                "intent": "monitor_system_health",
                "actions": ["collect_metrics", "alert"]
            }
        elif any(word in description_lower for word in ["optimize", "improve", "performance"]):
            return {
                "template": "optimization",
                "confidence": 0.80,
                "intent": "optimize_resources",
                "actions": ["analyze", "optimize"]
            }
        elif any(word in description_lower for word in ["secure", "protect", "harden"]):
            return {
                "template": "security",
                "confidence": 0.88,
                "intent": "enforce_security",
                "actions": ["scan", "enforce"]
            }
        elif any(word in description_lower for word in ["backup", "snapshot", "archive"]):
            return {
                "template": "backup",
                "confidence": 0.90,
                "intent": "backup_data",
                "actions": ["snapshot", "store"]
            }
        else:
            return {
                "template": "deployment",
                "confidence": 0.60,
                "intent": "generic_automation",
                "actions": []
            }
    
    def _build_contract_from_template(
        self,
        template: ContractTemplate,
        description: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build contract from template and analysis"""
        contract = self._deep_copy(template.base_structure)
        
        # Set basic fields
        contract["name"] = self._generate_contract_name(description)
        contract["intent"] = analysis.get("intent", "automate_task")
        
        # Generate actions
        actions = []
        for action_type in analysis.get("actions", []):
            actions.append({
                "type": action_type,
                "parameters": {}
            })
        contract["actions"] = actions
        
        # Add metadata
        contract["metadata"]["generated_at"] = datetime.utcnow().isoformat()
        contract["metadata"]["source_description"] = description[:200]
        contract["metadata"]["tags"] = self._extract_tags(description)
        
        return contract
    
    def _populate_template(
        self,
        contract: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Populate template with parameters"""
        for key, value in parameters.items():
            if key in contract:
                contract[key] = value
            elif "." in key:
                # Handle nested keys like "metadata.owner"
                self._set_nested_value(contract, key, value)
        
        return contract
    
    def _set_nested_value(self, obj: Dict, key: str, value: Any):
        """Set nested dictionary value"""
        keys = key.split(".")
        for k in keys[:-1]:
            obj = obj.setdefault(k, {})
        obj[keys[-1]] = value
    
    def _validate_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated contract"""
        warnings = []
        suggestions = []
        
        # Check required fields
        if not contract.get("name"):
            warnings.append("Contract name is missing")
        
        if not contract.get("intent"):
            warnings.append("Contract intent is not defined")
        
        if not contract.get("actions"):
            warnings.append("No actions defined")
        
        # Check validation requirements
        if not contract.get("validation_requirements", {}).get("gates"):
            suggestions.append("Consider adding validation gates")
        
        # Check metadata
        if not contract.get("metadata", {}).get("owner"):
            suggestions.append("Consider specifying contract owner")
        
        status = "valid" if not warnings else "warning"
        
        return {
            "status": status,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    # ------------------------------------------------------------------------
    # UTILITY METHODS
    # ------------------------------------------------------------------------
    
    def _generate_contract_id(self, template_id: str) -> str:
        """Generate unique contract ID"""
        self.contract_counter += 1
        prefix = template_id.split("-")[1][:3].upper()
        return f"AC-{prefix}-{self.contract_counter:04d}"
    
    def _generate_contract_name(self, description: str) -> str:
        """Generate contract name from description"""
        # Take first few words, clean, and kebab-case
        words = description.split()[:5]
        name = "-".join(words)
        name = re.sub(r'[^a-z0-9-]', '', name.lower())
        return name
    
    def _extract_tags(self, description: str) -> List[str]:
        """Extract tags from description"""
        tags = []
        description_lower = description.lower()
        
        tag_keywords = {
            "automation": ["automate", "automatic"],
            "deployment": ["deploy", "release"],
            "monitoring": ["monitor", "observe"],
            "security": ["secure", "protect"],
            "performance": ["optimize", "improve"],
            "compliance": ["comply", "regulation"],
            "backup": ["backup", "snapshot"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in description_lower for kw in keywords):
                tags.append(tag)
        
        return tags
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy dictionary/list"""
        return json.loads(json.dumps(obj))
    
    # ------------------------------------------------------------------------
    # EXPORT METHODS
    # ------------------------------------------------------------------------
    
    def export_to_yaml(
        self,
        contract: GeneratedContract,
        output_path: Path
    ):
        """Export contract to YAML file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(
                {"contracts": [contract.contract_definition]},
                f,
                default_flow_style=False,
                sort_keys=False
            )
    
    def export_to_json(
        self,
        contract: GeneratedContract,
        output_path: Path
    ):
        """Export contract to JSON file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(
                {"contracts": [contract.contract_definition]},
                f,
                indent=2
            )


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for contract generation"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate intelligent behavior contracts"
    )
    parser.add_argument(
        "description",
        help="Natural language description of desired behavior"
    )
    parser.add_argument(
        "--output", "-o",
        default="./generated-contract.yaml",
        help="Output file path"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format"
    )
    parser.add_argument(
        "--template", "-t",
        help="Template to use (optional)"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = ContractGenerator()
    
    # Generate contract
    if args.template:
        # Extract parameters from description (simplified)
        parameters = {"name": args.description}
        contract = generator.generate_from_template(args.template, parameters)
    else:
        contract = generator.generate_from_description(args.description)
    
    # Export
    output_path = Path(args.output)
    if args.format == "yaml":
        generator.export_to_yaml(contract, output_path)
    else:
        generator.export_to_json(contract, output_path)
    
    # Display summary
    print(f"\n{'='*70}")
    print(f"Contract Generated Successfully")
    print(f"{'='*70}")
    print(f"Contract ID: {contract.contract_id}")
    print(f"Method: {contract.generation_method}")
    print(f"Confidence: {contract.confidence_score:.1%}")
    print(f"Status: {contract.validation_status}")
    print(f"Output: {output_path}")
    
    if contract.warnings:
        print(f"\nWarnings:")
        for warning in contract.warnings:
            print(f"  ⚠ {warning}")
    
    if contract.suggestions:
        print(f"\nSuggestions:")
        for suggestion in contract.suggestions:
            print(f"  💡 {suggestion}")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
