from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .ai_agent import generate_summary
from .models import (
    AgentSummary,
    AuditLogEntry,
    OptimizationResult,
    Recommendation,
    RecommendationDecision,
    ResourceAnalysis,
    ResourceMetric,
    SimulatedVirtualMachine,
)
from .simulator import (
    advance_simulation_tick,
    analyze_resources,
    decide_recommendation,
    execute_recommendation,
    list_audit_log,
    list_metrics,
    list_recommendations,
    list_virtual_machines,
    ensure_demo_recommendation,
    process_due_recommendations,
)


async def _approval_monitor() -> None:
    while True:
        process_due_recommendations()
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_demo_recommendation()
    monitor = asyncio.create_task(_approval_monitor())
    yield
    monitor.cancel()
    await asyncio.gather(monitor, return_exceptions=True)


app = FastAPI(
    title="AI Cloud Cost Optimizer",
    description="Hackathon API backed by a simulated cloud environment.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):(\d+)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def read_root() -> Dict[str, str]:
    return {"message": "AI Cloud Cost Optimizer backend is running"}


@app.get(
    "/resources",
    response_model=List[SimulatedVirtualMachine],
    tags=["resources"],
)
def get_resources() -> List[SimulatedVirtualMachine]:
    advance_simulation_tick()
    return list_virtual_machines()


@app.get("/metrics", response_model=List[ResourceMetric], tags=["metrics"])
def get_metrics() -> List[ResourceMetric]:
    return list_metrics()


@app.get("/analysis", response_model=List[ResourceAnalysis], tags=["analysis"])
def get_analysis() -> List[ResourceAnalysis]:
    return analyze_resources()


@app.get("/agent/summary", response_model=AgentSummary, tags=["ai-agent"])
def get_agent_summary() -> AgentSummary:
    summary, source = generate_summary(analyze_resources())
    return AgentSummary(summary=summary, source=source)


@app.get(
    "/recommendations",
    response_model=List[Recommendation],
    tags=["recommendations"],
)
def get_recommendations() -> List[Recommendation]:
    return list_recommendations()


@app.post(
    "/recommendations/{recommendation_id}/approve",
    response_model=Recommendation,
    tags=["recommendations"],
)
def approve_recommendation(
    recommendation_id: str,
    decision: Optional[RecommendationDecision] = None,
) -> Recommendation:
    recommendation = decide_recommendation(
        recommendation_id,
        "approved",
        decision.note if decision else None,
    )
    if recommendation is None:
        raise HTTPException(
            status_code=409,
            detail="Recommendation does not exist or was already decided",
        )
    return recommendation


@app.post(
    "/recommendations/{recommendation_id}/reject",
    response_model=Recommendation,
    tags=["recommendations"],
)
def reject_recommendation(
    recommendation_id: str,
    decision: Optional[RecommendationDecision] = None,
) -> Recommendation:
    recommendation = decide_recommendation(
        recommendation_id,
        "rejected",
        decision.note if decision else None,
    )
    if recommendation is None:
        raise HTTPException(
            status_code=409,
            detail="Recommendation does not exist or was already decided",
        )
    return recommendation


@app.post(
    "/recommendations/{recommendation_id}/execute",
    response_model=OptimizationResult,
    tags=["optimizations"],
)
def execute_approved_recommendation(recommendation_id: str) -> OptimizationResult:
    result = execute_recommendation(recommendation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Recommendation does not exist")
    if isinstance(result, str):
        messages = {
            "recommendation_not_approved": "Recommendation must be approved before execution",
            "production_change_blocked": "Safety policy blocks simulated production changes",
            "resource_not_found": "Simulated resource does not exist",
        }
        raise HTTPException(status_code=409, detail=messages[result])

    recommendation, virtual_machine, health_check_passed, message = result
    return OptimizationResult(
        recommendation_id=recommendation.id,
        resource_id=virtual_machine.id,
        status=recommendation.status,
        message=message,
        health_check_passed=health_check_passed,
        monthly_cost_inr=virtual_machine.monthly_cost_inr,
        estimated_monthly_savings_inr=recommendation.estimated_monthly_savings_inr,
    )


@app.get("/audit-logs", response_model=List[AuditLogEntry], tags=["audit"])
def get_audit_logs() -> List[AuditLogEntry]:
    return list_audit_log()
