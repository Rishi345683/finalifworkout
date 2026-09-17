from typing import Optional

from pydantic import BaseModel


class SimulatedVirtualMachine(BaseModel):
    id: str
    name: str
    vcpus: int
    ram_gb: int
    cpu_utilization_percent: float
    ram_utilization_percent: float
    monthly_cost_inr: float
    environment: str
    status: str
    disk_gb: int = 0
    disk_utilization_percent: float = 0.0
    network_utilization_percent: float = 0.0
    requests_per_minute: int = 0
    error_rate_percent: float = 0.0
    average_latency_ms: float = 0.0
    idle_hours_per_day: float = 0.0
    criticality: str = "low"


class ResourceMetric(BaseModel):
    resource_id: str
    day: int
    cpu_utilization_percent: float
    ram_utilization_percent: float


class ResourceAnalysis(BaseModel):
    resource_id: str
    resource_name: str
    average_cpu_utilization_percent: float
    average_ram_utilization_percent: float
    monthly_cost_inr: float
    underutilized: bool
    estimated_monthly_savings_inr: float
    recommendation: str
    disk_utilization_percent: float = 0.0
    network_utilization_percent: float = 0.0
    requests_per_minute: int = 0
    error_rate_percent: float = 0.0
    average_latency_ms: float = 0.0
    idle_hours_per_day: float = 0.0
    criticality: str = "low"


class Recommendation(BaseModel):
    id: str
    resource_id: str
    resource_name: str
    action: str
    estimated_monthly_savings_inr: float
    waiting_period_hours: int
    status: str
    decision_note: Optional[str] = None
    approval_deadline: Optional[str] = None


class RecommendationDecision(BaseModel):
    note: Optional[str] = None


class OptimizationResult(BaseModel):
    recommendation_id: str
    resource_id: str
    status: str
    message: str
    health_check_passed: bool
    monthly_cost_inr: float
    estimated_monthly_savings_inr: float


class AuditLogEntry(BaseModel):
    recommendation_id: str
    resource_id: str
    action: str
    status: str
    message: str


class AgentSummary(BaseModel):
    summary: str
    source: str
