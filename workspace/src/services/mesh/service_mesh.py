#!/usr/bin/env python3
"""
L3: Protocol Mesh - Service Mesh
AXIOM Layer 3: 協議網格 - 服務網格

Responsibilities:
- Service discovery and registration
- Load balancing and traffic management
- Circuit breaker and retry patterns
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import random


class ServiceStatus(Enum):
    """Service status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class LoadBalancerStrategy(Enum):
    """Load balancer strategies."""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"


@dataclass
class ServiceEndpoint:
    """Service endpoint."""
    id: str
    host: str
    port: int
    weight: int = 1
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceDefinition:
    """Service definition."""
    name: str
    version: str
    endpoints: List[ServiceEndpoint] = field(default_factory=list)
    health_check_path: str = "/health"
    timeout: int = 30
    retries: int = 3


class CircuitBreaker:
    """Circuit breaker for service calls."""

    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure: Optional[datetime] = None
        self.is_open = False

    def record_success(self) -> None:
        """Record successful call."""
        self.failures = 0
        self.is_open = False

    def record_failure(self) -> None:
        """Record failed call."""
        self.failures += 1
        self.last_failure = datetime.now(timezone.utc)
        if self.failures >= self.failure_threshold:
            self.is_open = True

    def can_execute(self) -> bool:
        """Check if circuit allows execution."""
        if not self.is_open:
            return True

        # Check if recovery timeout has passed
        if self.last_failure:
            elapsed = (datetime.now(timezone.utc) - self.last_failure).total_seconds()
            if elapsed >= self.recovery_timeout:
                self.is_open = False
                self.failures = 0
                return True
        return False


class ServiceMesh:
    """
    Service mesh implementation for L3 Protocol Mesh layer.

    Provides service discovery, load balancing, and resilience patterns.
    """

    VERSION = "2.0.0"
    LAYER = "L3_protocol_mesh"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._services: Dict[str, ServiceDefinition] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lb_strategy = LoadBalancerStrategy.ROUND_ROBIN
        self._round_robin_index: Dict[str, int] = {}

    def register_service(self, service: ServiceDefinition) -> None:
        """Register a service."""
        self._services[service.name] = service
        self._circuit_breakers[service.name] = CircuitBreaker()
        self._round_robin_index[service.name] = 0

    def deregister_service(self, service_name: str) -> None:
        """Deregister a service."""
        self._services.pop(service_name, None)
        self._circuit_breakers.pop(service_name, None)
        self._round_robin_index.pop(service_name, None)

    def add_endpoint(self, service_name: str, endpoint: ServiceEndpoint) -> bool:
        """Add endpoint to service."""
        if service_name not in self._services:
            return False
        self._services[service_name].endpoints.append(endpoint)
        return True

    def remove_endpoint(self, service_name: str, endpoint_id: str) -> bool:
        """Remove endpoint from service."""
        if service_name not in self._services:
            return False
        service = self._services[service_name]
        service.endpoints = [e for e in service.endpoints if e.id != endpoint_id]
        return True

    def get_endpoint(self, service_name: str) -> Optional[ServiceEndpoint]:
        """Get an endpoint using load balancing."""
        service = self._services.get(service_name)
        if not service or not service.endpoints:
            return None

        # Filter healthy endpoints
        healthy = [e for e in service.endpoints
                   if e.status in (ServiceStatus.HEALTHY, ServiceStatus.UNKNOWN)]
        if not healthy:
            return None

        # Check circuit breaker
        cb = self._circuit_breakers.get(service_name)
        if cb and not cb.can_execute():
            return None

        # Apply load balancing strategy
        return self._select_endpoint(service_name, healthy)

    def _select_endpoint(self, service_name: str,
                        endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """Select endpoint based on strategy."""
        if self._lb_strategy == LoadBalancerStrategy.RANDOM:
            return random.choice(endpoints)
        elif self._lb_strategy == LoadBalancerStrategy.WEIGHTED:
            weights = [e.weight for e in endpoints]
            return random.choices(endpoints, weights=weights)[0]
        else:  # Round robin
            idx = self._round_robin_index.get(service_name, 0)
            endpoint = endpoints[idx % len(endpoints)]
            self._round_robin_index[service_name] = idx + 1
            return endpoint

    async def call(self, service_name: str, path: str,
                   method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Call a service with resilience patterns."""
        service = self._services.get(service_name)
        if not service:
            raise ServiceNotFoundError(f"Service not found: {service_name}")

        cb = self._circuit_breakers.get(service_name)

        for attempt in range(service.retries + 1):
            endpoint = self.get_endpoint(service_name)
            if not endpoint:
                raise NoHealthyEndpointError(f"No healthy endpoint for: {service_name}")

            try:
                # Placeholder for actual HTTP call
                result = await self._make_request(endpoint, path, method, **kwargs)
                if cb:
                    cb.record_success()
                return result

            except Exception as e:
                if cb:
                    cb.record_failure()
                if attempt == service.retries:
                    raise

        raise ServiceCallError(f"Failed to call service: {service_name}")

    async def _make_request(self, endpoint: ServiceEndpoint, path: str,
                           method: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to endpoint."""
        # Placeholder - actual implementation would use aiohttp or similar
        return {
            "endpoint": f"{endpoint.host}:{endpoint.port}",
            "path": path,
            "method": method,
        }

    def set_endpoint_status(self, service_name: str, endpoint_id: str,
                           status: ServiceStatus) -> bool:
        """Update endpoint health status."""
        service = self._services.get(service_name)
        if not service:
            return False
        for endpoint in service.endpoints:
            if endpoint.id == endpoint_id:
                endpoint.status = status
                return True
        return False

    def get_services(self) -> List[str]:
        """Get list of registered services."""
        return list(self._services.keys())

    def get_service(self, name: str) -> Optional[ServiceDefinition]:
        """Get service definition."""
        return self._services.get(name)


class ServiceNotFoundError(Exception):
    """Service not found error."""
    pass


class NoHealthyEndpointError(Exception):
    """No healthy endpoint available."""
    pass


class ServiceCallError(Exception):
    """Service call failed."""
    pass


# Module exports
__all__ = [
    "ServiceMesh",
    "ServiceDefinition",
    "ServiceEndpoint",
    "ServiceStatus",
    "LoadBalancerStrategy",
    "CircuitBreaker",
    "ServiceNotFoundError",
    "NoHealthyEndpointError",
    "ServiceCallError",
]
