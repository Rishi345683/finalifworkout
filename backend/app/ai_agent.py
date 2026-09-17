import json
import os
from typing import List, Optional, Tuple
from urllib import request

from .models import ResourceAnalysis


def _fallback_summary(analyses: List[ResourceAnalysis]) -> str:
    underutilized = [item for item in analyses if item.underutilized]
    total_savings = sum(item.estimated_monthly_savings_inr for item in underutilized)
    resource_names = ", ".join(item.resource_name for item in underutilized)
    return (
        f"Found {len(underutilized)} underutilized resources: {resource_names}. "
        f"Estimated combined monthly savings are Rs. {total_savings:,.2f}. "
        "Request approval before applying any simulated optimization."
    )


def _llm_summary(analyses: List[ResourceAnalysis]) -> Optional[str]:
    api_url = os.getenv("LLM_API_URL")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "cloud-cost-optimizer-demo")
    if not api_url or not api_key:
        return None

    prompt = (
        "Summarize these simulated cloud cost findings in three concise sentences. "
        "Mention the highest-value savings and remind the user that approval is required.\n"
        f"{json.dumps([item.model_dump() for item in analyses])}"
    )
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    http_request = request.Request(
        api_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=10) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        return response_data["choices"][0]["message"]["content"]
    except (KeyError, OSError, TypeError, ValueError):
        return None


def generate_summary(analyses: List[ResourceAnalysis]) -> Tuple[str, str]:
    """Generate an explanation without requiring an external LLM service."""
    llm_summary = _llm_summary(analyses)
    if llm_summary:
        return llm_summary, "llm"
    return _fallback_summary(analyses), "fallback"