#!/usr/bin/env python3
"""
L6: Federated Learning - Federation Framework
AXIOM Layer 6: 聯邦學習 - 聯邦框架

Responsibilities:
- Distributed model training coordination
- Privacy-preserving aggregation
- Client management and synchronization
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import asyncio
import random


class AggregationMethod(Enum):
    """Model aggregation methods."""
    FED_AVG = "fed_avg"  # Federated Averaging
    FED_PROX = "fed_prox"  # Federated Proximal
    FED_ADAM = "fed_adam"  # Federated Adam
    WEIGHTED = "weighted"  # Weighted by data size


class ClientStatus(Enum):
    """Federated client status."""
    IDLE = "idle"
    TRAINING = "training"
    UPLOADING = "uploading"
    DISCONNECTED = "disconnected"


@dataclass
class ModelUpdate:
    """Model update from a client."""
    client_id: str
    round_id: int
    weights: Dict[str, List[float]]
    metrics: Dict[str, float]
    data_size: int
    timestamp: datetime


@dataclass
class FederatedClient:
    """Federated learning client."""
    id: str
    name: str
    status: ClientStatus = ClientStatus.IDLE
    data_size: int = 0
    last_round: int = 0
    last_seen: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FederationConfig:
    """Federation configuration."""
    min_clients: int = 2
    max_clients: int = 100
    rounds: int = 10
    local_epochs: int = 5
    aggregation_method: AggregationMethod = AggregationMethod.FED_AVG
    client_fraction: float = 1.0  # Fraction of clients per round
    differential_privacy: bool = True
    noise_multiplier: float = 0.1


@dataclass
class RoundResult:
    """Result of a federation round."""
    round_id: int
    participants: int
    aggregated_weights: Dict[str, List[float]]
    metrics: Dict[str, float]
    duration: float


class FederationFramework:
    """
    Federated learning framework for L6 Federated Learning layer.

    Coordinates distributed model training while preserving data privacy.
    """

    VERSION = "2.0.0"
    LAYER = "L6_federated_learning"

    def __init__(self, config: Optional[FederationConfig] = None):
        self.config = config or FederationConfig()
        self._clients: Dict[str, FederatedClient] = {}
        self._global_weights: Dict[str, List[float]] = {}
        self._current_round = 0
        self._round_updates: List[ModelUpdate] = []
        self._history: List[RoundResult] = []

    def register_client(self, client: FederatedClient) -> bool:
        """Register a federated client."""
        if len(self._clients) >= self.config.max_clients:
            return False
        client.last_seen = datetime.now(timezone.utc)
        self._clients[client.id] = client
        return True

    def unregister_client(self, client_id: str) -> bool:
        """Unregister a federated client."""
        if client_id in self._clients:
            del self._clients[client_id]
            return True
        return False

    def set_initial_model(self, weights: Dict[str, List[float]]) -> None:
        """Set the initial global model weights."""
        self._global_weights = weights

    async def run_federation(self) -> List[RoundResult]:
        """Run the complete federation process."""
        results = []

        for round_id in range(1, self.config.rounds + 1):
            self._current_round = round_id
            result = await self._run_round(round_id)
            results.append(result)
            self._history.append(result)

        return results

    async def _run_round(self, round_id: int) -> RoundResult:
        """Run a single federation round."""
        start_time = datetime.now(timezone.utc)

        # Select clients for this round
        selected = self._select_clients()
        if len(selected) < self.config.min_clients:
            raise ValueError(f"Not enough clients: {len(selected)} < {self.config.min_clients}")

        # Distribute model to clients
        for client_id in selected:
            await self._send_model_to_client(client_id)

        # Wait for client updates
        self._round_updates = []
        await self._collect_updates(selected, round_id)

        # Aggregate updates
        aggregated = self._aggregate_updates()
        self._global_weights = aggregated

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Calculate round metrics
        metrics = self._calculate_round_metrics()

        return RoundResult(
            round_id=round_id,
            participants=len(selected),
            aggregated_weights=aggregated,
            metrics=metrics,
            duration=duration,
        )

    def _select_clients(self) -> List[str]:
        """Select clients for the current round."""
        available = [
            cid for cid, c in self._clients.items()
            if c.status != ClientStatus.DISCONNECTED
        ]

        num_to_select = max(
            self.config.min_clients,
            int(len(available) * self.config.client_fraction)
        )
        num_to_select = min(num_to_select, len(available))

        return random.sample(available, num_to_select)

    async def _send_model_to_client(self, client_id: str) -> None:
        """Send global model to a client."""
        client = self._clients.get(client_id)
        if client:
            client.status = ClientStatus.TRAINING
            # In real implementation, would send model via network
            await asyncio.sleep(0.01)  # Simulate network delay

    async def _collect_updates(self, client_ids: List[str], round_id: int) -> None:
        """Collect model updates from clients."""
        for client_id in client_ids:
            client = self._clients.get(client_id)
            if client:
                client.status = ClientStatus.UPLOADING
                # Simulate receiving update
                update = self._simulate_client_update(client_id, round_id)
                self._round_updates.append(update)
                client.status = ClientStatus.IDLE
                client.last_round = round_id
                client.last_seen = datetime.now(timezone.utc)

    def _simulate_client_update(self, client_id: str, round_id: int) -> ModelUpdate:
        """Simulate a client model update (for testing)."""
        # In real implementation, client would train and send actual weights
        weights = {}
        for layer, w in self._global_weights.items():
            # Simulate local training with small perturbation
            weights[layer] = [v + random.gauss(0, 0.01) for v in w]

        return ModelUpdate(
            client_id=client_id,
            round_id=round_id,
            weights=weights,
            metrics={"loss": random.uniform(0.1, 0.5), "accuracy": random.uniform(0.7, 0.95)},
            data_size=self._clients[client_id].data_size,
            timestamp=datetime.now(timezone.utc),
        )

    def _aggregate_updates(self) -> Dict[str, List[float]]:
        """Aggregate model updates using configured method."""
        if self.config.aggregation_method == AggregationMethod.FED_AVG:
            return self._fed_avg()
        elif self.config.aggregation_method == AggregationMethod.WEIGHTED:
            return self._weighted_avg()
        else:
            return self._fed_avg()

    def _fed_avg(self) -> Dict[str, List[float]]:
        """Federated averaging aggregation."""
        if not self._round_updates:
            return self._global_weights

        aggregated = {}
        num_updates = len(self._round_updates)

        for layer in self._global_weights.keys():
            layer_weights = [update.weights.get(layer, []) for update in self._round_updates]
            if layer_weights and layer_weights[0]:
                avg_weights = []
                for i in range(len(layer_weights[0])):
                    avg = sum(w[i] for w in layer_weights) / num_updates
                    # Add differential privacy noise if enabled
                    if self.config.differential_privacy:
                        avg += random.gauss(0, self.config.noise_multiplier)
                    avg_weights.append(avg)
                aggregated[layer] = avg_weights

        return aggregated

    def _weighted_avg(self) -> Dict[str, List[float]]:
        """Weighted average aggregation by data size."""
        if not self._round_updates:
            return self._global_weights

        total_data = sum(u.data_size for u in self._round_updates)
        if total_data == 0:
            return self._fed_avg()

        aggregated = {}
        for layer in self._global_weights.keys():
            avg_weights = [0.0] * len(self._global_weights[layer])
            for update in self._round_updates:
                weight = update.data_size / total_data
                for i, v in enumerate(update.weights.get(layer, [])):
                    avg_weights[i] += v * weight
            aggregated[layer] = avg_weights

        return aggregated

    def _calculate_round_metrics(self) -> Dict[str, float]:
        """Calculate aggregated metrics for the round."""
        if not self._round_updates:
            return {}

        metrics = {}
        for key in self._round_updates[0].metrics.keys():
            values = [u.metrics.get(key, 0) for u in self._round_updates]
            metrics[key] = sum(values) / len(values)

        return metrics

    def get_global_model(self) -> Dict[str, List[float]]:
        """Get current global model weights."""
        return self._global_weights

    def get_clients(self) -> List[FederatedClient]:
        """Get all registered clients."""
        return list(self._clients.values())

    def get_history(self) -> List[RoundResult]:
        """Get federation history."""
        return self._history


# Module exports
__all__ = [
    "FederationFramework",
    "FederationConfig",
    "FederatedClient",
    "ModelUpdate",
    "RoundResult",
    "AggregationMethod",
    "ClientStatus",
]
