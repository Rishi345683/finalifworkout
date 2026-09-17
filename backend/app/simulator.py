from datetime import datetime, timedelta, timezone
import math
import random
from typing import List, Optional

from .database import (
    APPROVAL_WAIT_MINUTES,
    DEMO_RECOMMENDATION_COUNT,
    initialize_database,
    list_saved_audit_logs,
    list_saved_recommendations,
    save_audit_log,
    save_recommendation,
    update_recommendation,
)
from .models import (
    AuditLogEntry,
    Recommendation,
    ResourceAnalysis,
    ResourceMetric,
    SimulatedVirtualMachine,
)


_SIMULATED_VIRTUAL_MACHINES = [
    SimulatedVirtualMachine(
        id="vm-001",
        name="Development API",
        vcpus=16,
        ram_gb=64,
        cpu_utilization_percent=8.0,
        ram_utilization_percent=12.0,
        monthly_cost_inr=40000.0,
        environment="Development",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-002",
        name="Production Web",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=62.0,
        ram_utilization_percent=58.0,
        monthly_cost_inr=28000.0,
        environment="Production",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-003",
        name="Staging Database",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=18.0,
        ram_utilization_percent=24.0,
        monthly_cost_inr=30000.0,
        environment="Staging",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-004",
        name="Development Worker",
        vcpus=4,
        ram_gb=16,
        cpu_utilization_percent=5.0,
        ram_utilization_percent=9.0,
        monthly_cost_inr=12000.0,
        environment="Development",
        status="Stopped",
    ),
    SimulatedVirtualMachine(
        id="vm-005",
        name="Production Database",
        vcpus=16,
        ram_gb=64,
        cpu_utilization_percent=71.0,
        ram_utilization_percent=68.0,
        monthly_cost_inr=45000.0,
        environment="Production",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-006",
        name="QA Test Runner",
        vcpus=4,
        ram_gb=16,
        cpu_utilization_percent=14.0,
        ram_utilization_percent=19.0,
        monthly_cost_inr=14000.0,
        environment="QA",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-007",
        name="Analytics Batch",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=36.0,
        ram_utilization_percent=41.0,
        monthly_cost_inr=26000.0,
        environment="Development",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-008",
        name="Documentation Server",
        vcpus=2,
        ram_gb=8,
        cpu_utilization_percent=3.0,
        ram_utilization_percent=7.0,
        monthly_cost_inr=7000.0,
        environment="Development",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-009",
        name="Development Reports",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=11.0,
        ram_utilization_percent=16.0,
        monthly_cost_inr=22000.0,
        environment="Development",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-010",
        name="QA Integration Server",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=16.0,
        ram_utilization_percent=22.0,
        monthly_cost_inr=24000.0,
        environment="QA",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-011",
        name="Development Cache",
        vcpus=4,
        ram_gb=16,
        cpu_utilization_percent=7.0,
        ram_utilization_percent=11.0,
        monthly_cost_inr=11000.0,
        environment="Development",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-012",
        name="Production Payments",
        vcpus=16,
        ram_gb=64,
        cpu_utilization_percent=66.0,
        ram_utilization_percent=61.0,
        monthly_cost_inr=52000.0,
        environment="Production",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-013",
        name="Staging API",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=20.0,
        ram_utilization_percent=27.0,
        monthly_cost_inr=21000.0,
        environment="Staging",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-014",
        name="QA Automation Worker",
        vcpus=4,
        ram_gb=16,
        cpu_utilization_percent=12.0,
        ram_utilization_percent=17.0,
        monthly_cost_inr=13000.0,
        environment="QA",
        status="Stopped",
    ),
    SimulatedVirtualMachine(
        id="vm-015",
        name="Production Search",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=48.0,
        ram_utilization_percent=52.0,
        monthly_cost_inr=32000.0,
        environment="Production",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-016",
        name="Development Scheduler",
        vcpus=4,
        ram_gb=16,
        cpu_utilization_percent=9.0,
        ram_utilization_percent=14.0,
        monthly_cost_inr=15000.0,
        environment="Development",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-017",
        name="Analytics Warehouse",
        vcpus=16,
        ram_gb=64,
        cpu_utilization_percent=39.0,
        ram_utilization_percent=44.0,
        monthly_cost_inr=48000.0,
        environment="Development",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-018",
        name="Documentation Preview",
        vcpus=2,
        ram_gb=8,
        cpu_utilization_percent=4.0,
        ram_utilization_percent=8.0,
        monthly_cost_inr=8000.0,
        environment="Development",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-019",
        name="QA Mobile Runner",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=17.0,
        ram_utilization_percent=23.0,
        monthly_cost_inr=19000.0,
        environment="QA",
        status="Running",
    ),
    SimulatedVirtualMachine(
        id="vm-020",
        name="Production Notifications",
        vcpus=8,
        ram_gb=32,
        cpu_utilization_percent=58.0,
        ram_utilization_percent=55.0,
        monthly_cost_inr=27000.0,
        environment="Production",
        status="Running",
    ),
]

_OPERATIONAL_PROFILES = {
    "vm-001": (256, 18.0, 7.0, 18, 0.4, 180.0, 16.0, "low"),
    "vm-002": (256, 64.0, 58.0, 420, 1.2, 210.0, 3.0, "high"),
    "vm-003": (512, 24.0, 12.0, 35, 0.8, 240.0, 12.0, "medium"),
    "vm-004": (128, 9.0, 2.0, 4, 0.0, 0.0, 24.0, "low"),
    "vm-005": (1024, 72.0, 68.0, 680, 2.4, 260.0, 2.0, "high"),
    "vm-006": (128, 15.0, 8.0, 22, 0.6, 190.0, 14.0, "low"),
    "vm-007": (256, 38.0, 31.0, 110, 0.9, 230.0, 8.0, "medium"),
    "vm-008": (64, 6.0, 3.0, 3, 0.0, 120.0, 22.0, "low"),
    "vm-009": (256, 13.0, 9.0, 15, 0.2, 160.0, 18.0, "low"),
    "vm-010": (256, 19.0, 14.0, 28, 0.5, 205.0, 13.0, "low"),
    "vm-011": (128, 12.0, 5.0, 12, 0.2, 150.0, 18.0, "low"),
    "vm-012": (1024, 76.0, 71.0, 720, 1.8, 280.0, 2.0, "high"),
    "vm-013": (512, 28.0, 16.0, 48, 1.1, 310.0, 9.0, "medium"),
    "vm-014": (128, 10.0, 4.0, 6, 0.0, 0.0, 22.0, "low"),
    "vm-015": (512, 55.0, 49.0, 260, 1.0, 220.0, 5.0, "high"),
    "vm-016": (128, 14.0, 6.0, 10, 0.3, 170.0, 17.0, "low"),
    "vm-017": (1024, 44.0, 38.0, 140, 0.7, 250.0, 7.0, "medium"),
    "vm-018": (64, 8.0, 3.0, 5, 0.0, 110.0, 21.0, "low"),
    "vm-019": (256, 21.0, 13.0, 32, 0.4, 200.0, 12.0, "low"),
    "vm-020": (256, 62.0, 54.0, 390, 1.5, 230.0, 4.0, "high"),
}

for _virtual_machine in _SIMULATED_VIRTUAL_MACHINES:
    (
        _virtual_machine.disk_gb,
        _virtual_machine.disk_utilization_percent,
        _virtual_machine.network_utilization_percent,
        _virtual_machine.requests_per_minute,
        _virtual_machine.error_rate_percent,
        _virtual_machine.average_latency_ms,
        _virtual_machine.idle_hours_per_day,
        _virtual_machine.criticality,
    ) = _OPERATIONAL_PROFILES[_virtual_machine.id]

initialize_database()


_SIMULATION_TICK = 0


def advance_simulation_tick() -> None:
    """Advance the live simulation clock without changing the baseline analysis state."""
    global _SIMULATION_TICK
    _SIMULATION_TICK += 1


def _live_virtual_machine_snapshot(virtual_machine: SimulatedVirtualMachine) -> SimulatedVirtualMachine:
    """Create a low-noise live view that updates the display while preserving baseline analytics."""
    idx = int(virtual_machine.id.split("-")[-1])
    phase = (_SIMULATION_TICK * 0.8) + (idx * 0.7)
    cpu_variation = math.sin(phase) * 2.5
    ram_variation = math.cos(phase * 1.2) * 2.0

    live = virtual_machine.model_copy(deep=True)
    live.cpu_utilization_percent = max(
        0.0,
        min(100.0, live.cpu_utilization_percent + cpu_variation),
    )
    live.ram_utilization_percent = max(
        0.0,
        min(100.0, live.ram_utilization_percent + ram_variation),
    )
    if live.environment != "Production":
        live.monthly_cost_inr = round(
            max(3000.0, live.monthly_cost_inr * (1 + (math.sin(phase) * 0.003))),
            2,
        )
    return live


def list_virtual_machines() -> List[SimulatedVirtualMachine]:
    """Return a live snapshot of all resources in the simulated cloud."""
    return [_live_virtual_machine_snapshot(item) for item in _SIMULATED_VIRTUAL_MACHINES]


def list_metrics() -> List[ResourceMetric]:
    """Return deterministic seven-day utilization history for each VM."""
    metrics = []
    for virtual_machine in _SIMULATED_VIRTUAL_MACHINES:
        for day in range(1, 8):
            cpu_change = ((day % 3) - 1) * 2
            ram_change = ((day % 2) - 0.5) * 2
            metrics.append(
                ResourceMetric(
                    resource_id=virtual_machine.id,
                    day=day,
                    cpu_utilization_percent=max(
                        0.0,
                        min(100.0, virtual_machine.cpu_utilization_percent + cpu_change),
                    ),
                    ram_utilization_percent=max(
                        0.0,
                        min(100.0, virtual_machine.ram_utilization_percent + ram_change),
                    ),
                )
            )
    return metrics


def analyze_resources() -> List[ResourceAnalysis]:
    """Identify VMs whose average utilization is low enough to review."""
    metrics_by_resource = {}
    for metric in list_metrics():
        metrics_by_resource.setdefault(metric.resource_id, []).append(metric)

    analyses = []
    for virtual_machine in _SIMULATED_VIRTUAL_MACHINES:
        resource_metrics = metrics_by_resource[virtual_machine.id]
        average_cpu = round(
            sum(metric.cpu_utilization_percent for metric in resource_metrics)
            / len(resource_metrics),
            2,
        )
        average_ram = round(
            sum(metric.ram_utilization_percent for metric in resource_metrics)
            / len(resource_metrics),
            2,
        )
        underutilized = average_cpu < 20 and average_ram < 30
        operationally_idle = (
            virtual_machine.disk_utilization_percent < 30
            and virtual_machine.network_utilization_percent < 20
            and virtual_machine.requests_per_minute < 50
            and virtual_machine.idle_hours_per_day >= 8
        )
        safe_to_review = (
            virtual_machine.error_rate_percent < 5
            and virtual_machine.average_latency_ms < 500
            and virtual_machine.criticality != "high"
        )
        underutilized = underutilized and operationally_idle and safe_to_review
        savings = round(virtual_machine.monthly_cost_inr * 0.3, 2) if underutilized else 0.0
        recommendation = (
            "Review for rightsizing or scheduled shutdown"
            if underutilized
            else "No immediate optimization suggested"
        )
        analyses.append(
            ResourceAnalysis(
                resource_id=virtual_machine.id,
                resource_name=virtual_machine.name,
                average_cpu_utilization_percent=average_cpu,
                average_ram_utilization_percent=average_ram,
                monthly_cost_inr=virtual_machine.monthly_cost_inr,
                underutilized=underutilized,
                estimated_monthly_savings_inr=savings,
                recommendation=recommendation,
                disk_utilization_percent=virtual_machine.disk_utilization_percent,
                network_utilization_percent=virtual_machine.network_utilization_percent,
                requests_per_minute=virtual_machine.requests_per_minute,
                error_rate_percent=virtual_machine.error_rate_percent,
                average_latency_ms=virtual_machine.average_latency_ms,
                idle_hours_per_day=virtual_machine.idle_hours_per_day,
                criticality=virtual_machine.criticality,
            )
        )
    return analyses


def list_recommendations() -> List[Recommendation]:
    """Return recommendations generated from underutilized resources."""
    ensure_demo_recommendation()
    process_due_recommendations()
    recommendations = list_saved_recommendations()
    existing_resource_ids = {item.resource_id for item in recommendations}
    next_id = len(recommendations) + 1
    missing_analyses = (
        item
        for item in analyze_resources()
        if item.underutilized and item.resource_id not in existing_resource_ids
    )
    for analysis in missing_analyses:
        recommendation = Recommendation(
            id=f"rec-{next_id:03d}",
            resource_id=analysis.resource_id,
            resource_name=analysis.resource_name,
            action=analysis.recommendation,
            estimated_monthly_savings_inr=analysis.estimated_monthly_savings_inr,
            waiting_period_hours=APPROVAL_WAIT_MINUTES,
            status="pending_approval",
            approval_deadline=(
                datetime.now(timezone.utc)
                + timedelta(minutes=APPROVAL_WAIT_MINUTES)
            ).isoformat(),
        )
        save_recommendation(recommendation)
        next_id += 1
    recommendations = list_saved_recommendations()
    process_due_recommendations()
    recommendations = list_saved_recommendations()
    return recommendations


def _recommendation_number(item_id: str) -> Optional[int]:
    prefix = "rec-"
    if not item_id.startswith(prefix):
        return None
    suffix = item_id[len(prefix) :]
    if not suffix.isdigit():
        return None
    return int(suffix)


def _demo_recommendation_candidates() -> List[ResourceAnalysis]:
    """Return the normal low-utilization candidates and a fallback pool for demo continuity."""
    analyses = analyze_resources()
    underutilized = [item for item in analyses if item.underutilized]
    if underutilized:
        return underutilized

    fallback = []
    for virtual_machine in _SIMULATED_VIRTUAL_MACHINES:
        if virtual_machine.environment == "Production":
            continue
        if virtual_machine.status not in {"Running", "Stopped"}:
            continue
        if (
            virtual_machine.cpu_utilization_percent < 25
            and virtual_machine.ram_utilization_percent < 35
        ):
            fallback.append(
                ResourceAnalysis(
                    resource_id=virtual_machine.id,
                    resource_name=virtual_machine.name,
                    average_cpu_utilization_percent=virtual_machine.cpu_utilization_percent,
                    average_ram_utilization_percent=virtual_machine.ram_utilization_percent,
                    monthly_cost_inr=virtual_machine.monthly_cost_inr,
                    underutilized=True,
                    estimated_monthly_savings_inr=round(virtual_machine.monthly_cost_inr * 0.3, 2),
                    recommendation="Review for rightsizing or scheduled shutdown",
                )
            )
    return fallback


def ensure_demo_recommendation() -> None:
    """Ensure the demo starts with a fresh batch of pending recommendations."""
    recommendations = list_saved_recommendations()
    pending_resource_ids = {
        item.resource_id
        for item in recommendations
        if item.status == "pending_approval"
    }
    if len(pending_resource_ids) >= DEMO_RECOMMENDATION_COUNT:
        return

    candidates = _demo_recommendation_candidates()
    if not candidates:
        return

    recommendation_ids = [
        recommendation_number
        for item in recommendations
        for recommendation_number in [ _recommendation_number(item.id) ]
        if recommendation_number is not None
    ]
    next_id = max(recommendation_ids, default=0) + 1
    existing_by_resource = {item.resource_id: item for item in recommendations}
    selected_candidates = random.sample(
        [candidate for candidate in candidates if candidate.resource_id not in pending_resource_ids],
        min(
            max(0, DEMO_RECOMMENDATION_COUNT - len(pending_resource_ids)),
            len(candidates) - len(pending_resource_ids),
        ),
    )
    for candidate in selected_candidates:
        deadline_seconds = random.randint(
            max(30, APPROVAL_WAIT_MINUTES * 30),
            max(30, APPROVAL_WAIT_MINUTES * 60),
        )
        approval_deadline = (
            datetime.now(timezone.utc) + timedelta(seconds=deadline_seconds)
        ).isoformat()
        existing = existing_by_resource.get(candidate.resource_id)
        if existing is None:
            save_recommendation(
                Recommendation(
                    id=f"rec-{next_id:03d}",
                    resource_id=candidate.resource_id,
                    resource_name=candidate.resource_name,
                    action=candidate.recommendation,
                    estimated_monthly_savings_inr=candidate.estimated_monthly_savings_inr,
                    waiting_period_hours=APPROVAL_WAIT_MINUTES,
                    status="pending_approval",
                    approval_deadline=approval_deadline,
                )
            )
            next_id += 1
        else:
            existing.status = "pending_approval"
            existing.decision_note = None
            existing.waiting_period_hours = APPROVAL_WAIT_MINUTES
            existing.approval_deadline = approval_deadline
            update_recommendation(existing)


def process_due_recommendations() -> None:
    """Auto-approve and execute recommendations whose response window expired."""
    now = datetime.now(timezone.utc)
    for recommendation in list_saved_recommendations():
        if recommendation.status != "pending_approval" or not recommendation.approval_deadline:
            continue
        deadline = datetime.fromisoformat(recommendation.approval_deadline)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if deadline <= now:
            recommendation.status = "auto_approved"
            recommendation.decision_note = "No response received before the approval deadline"
            update_recommendation(recommendation)
            execute_recommendation(recommendation.id)


def decide_recommendation(
    recommendation_id: str,
    status: str,
    note: Optional[str] = None,
) -> Optional[Recommendation]:
    """Record an approval or rejection for a pending recommendation."""
    for recommendation in list_recommendations():
        if recommendation.id == recommendation_id:
            if recommendation.status != "pending_approval":
                return None
            recommendation.status = status
            recommendation.decision_note = note
            update_recommendation(recommendation)
            decision_message = f"Recommendation manually {status} by the user."
            if status == "approved":
                virtual_machine = next(
                    (
                        item
                        for item in _SIMULATED_VIRTUAL_MACHINES
                        if item.id == recommendation.resource_id
                    ),
                    None,
                )
                if virtual_machine is not None:
                    decision_message += (
                        f" Planned optimization: {virtual_machine.vcpus} vCPU/"
                        f"{virtual_machine.ram_gb} GB RAM to "
                        f"{max(1, virtual_machine.vcpus // 2)} vCPU/"
                        f"{max(1, virtual_machine.ram_gb // 2)} GB RAM."
                    )
            if note:
                decision_message += f" Note: {note}"
            save_audit_log(
                AuditLogEntry(
                    recommendation_id=recommendation.id,
                    resource_id=recommendation.resource_id,
                    action="approval_decision",
                    status=status,
                    message=decision_message,
                )
            )
            if status == "approved":
                execute_recommendation(recommendation.id)
                recommendation = next(
                    item
                    for item in list_saved_recommendations()
                    if item.id == recommendation.id
                )
            return recommendation
    return None


def execute_recommendation(recommendation_id: str):
    """Apply an approved non-production recommendation in the simulator."""
    recommendation = next(
        (item for item in list_saved_recommendations() if item.id == recommendation_id),
        None,
    )
    if recommendation is None:
        return None

    virtual_machine = next(
        (item for item in _SIMULATED_VIRTUAL_MACHINES if item.id == recommendation.resource_id),
        None,
    )
    if virtual_machine is None:
        return "resource_not_found"
    if recommendation.status not in {"approved", "auto_approved"}:
        return "recommendation_not_approved"
    if virtual_machine.environment == "Production":
        return "production_change_blocked"

    was_auto_approved = recommendation.status == "auto_approved"
    original = virtual_machine.model_copy(deep=True)
    virtual_machine.vcpus = max(1, virtual_machine.vcpus // 2)
    virtual_machine.ram_gb = max(1, virtual_machine.ram_gb // 2)
    virtual_machine.monthly_cost_inr = round(virtual_machine.monthly_cost_inr * 0.7, 2)

    health_check_passed = (
        virtual_machine.status in {"Running", "Stopped"}
        and virtual_machine.cpu_utilization_percent < 90
        and virtual_machine.ram_utilization_percent < 90
    )
    if health_check_passed:
        recommendation.status = "optimized"
        resize_details = (
            f"Resized {original.vcpus} vCPU/{original.ram_gb} GB RAM to "
            f"{virtual_machine.vcpus} vCPU/{virtual_machine.ram_gb} GB RAM; "
            f"monthly cost changed from Rs. {original.monthly_cost_inr:,.2f} to "
            f"Rs. {virtual_machine.monthly_cost_inr:,.2f}."
        )
        message = (
            "No response received; recommendation was automatically approved and "
            f"the simulated resize passed its health check. {resize_details}"
            if was_auto_approved
            else f"Simulated resize completed and health check passed. {resize_details}"
        )
        result_status = "optimized"
    else:
        virtual_machine.__dict__.update(original.__dict__)
        recommendation.status = "rollback_completed"
        message = "Health check failed; simulated changes were rolled back"
        result_status = "rolled_back"

    audit_entry = AuditLogEntry(
        recommendation_id=recommendation.id,
        resource_id=virtual_machine.id,
        action="simulated_resize",
        status=result_status,
        message=message,
    )
    save_audit_log(audit_entry)
    update_recommendation(recommendation)
    return recommendation, virtual_machine, health_check_passed, message


def list_audit_log() -> List[AuditLogEntry]:
    """Return simulated optimization actions persisted in SQLite."""
    return list_saved_audit_logs()
