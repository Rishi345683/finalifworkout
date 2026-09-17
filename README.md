# AI Cloud Cost Optimizer

AI Cloud Cost Optimizer is a local hackathon demonstration of cloud cost analysis and approval-based optimization. It uses a simulated cloud-resource layer, a FastAPI backend, an Angular dashboard, and SQLite persistence. It does not connect to AWS, Azure, GCP, or real production infrastructure.

Repository: https://github.com/Rishi345683/lastbutone

## What The Demo Shows

The application scans simulated virtual machines and seven days of utilization history. It analyzes:

- CPU and RAM utilization
- Disk and network utilization
- Requests per minute
- Error rate and average latency
- Idle hours per day
- Environment and criticality
- Monthly cost

The system creates a recommendation only when a resource is underutilized, operationally idle, reliable, sufficiently inactive, and not high criticality. Estimated savings are calculated as 30% of the simulated monthly cost.

The workflow is:

```text
pending_approval -> approved -> optimized
pending_approval -> auto_approved -> optimized
pending_approval -> rejected
```

Approval is required before a simulated resize. The automatic path is used when the approval deadline expires.

## Project Structure

```text
backend/
	app/
		ai_agent.py       AI/LLM summary generation
		database.py       SQLite configuration and persistence
		main.py           FastAPI routes and approval monitor
		models.py         Pydantic API models
		simulator.py      Simulated VMs, analysis, decisions, and execution
	tests/
		test_backend.py   Backend workflow tests
frontend/
	src/app/
		app.ts            Dashboard state and API calls
		app.html          Dashboard layout and controls
		app.css           Dashboard styling
postman/
	AI-Cloud-Cost-Optimizer.postman_collection.json
```

## Run Locally

Install backend dependencies from the project root:

```powershell
cd backend
python -m pip install -r requirements.txt
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

In a second terminal, install and start the Angular dashboard:

```powershell
cd frontend
npm install
npm start
```

The dashboard runs at `http://localhost:4200`.

## Demo Configuration

The default demo approval window is three minutes:

```powershell
$env:COSTOPTI_APPROVAL_WAIT_MINUTES = "3"
```

At startup, the backend seeds up to three random eligible pending recommendations. Their deadlines are staggered randomly within approximately the configured approval window. Existing pending recommendations are preserved, and duplicate resource recommendations are not created.

The number of startup recommendations can be changed:

```powershell
$env:COSTOPTI_DEMO_RECOMMENDATION_COUNT = "3"
```

For a production-like approval period, use 24 hours instead:

```powershell
$env:COSTOPTI_APPROVAL_WAIT_MINUTES = "1440"
```

Restart the backend after changing environment variables. The background monitor in `backend/app/main.py` checks due recommendations every five seconds.

## Organizer Demonstration Flow

1. Start the backend and frontend.
2. Open `http://localhost:4200`.
3. Show the 20 virtual machines in the resource inventory.
4. Explain the AI readout and utilization-based analysis.
5. Show the recommendation cards, including:
	 - Received time
	 - Decision deadline
	 - Approval window
	 - Estimated monthly savings
6. Click **Approve** on one recommendation.
7. The card shows the planned resize, for example `8 vCPU / 32 GB RAM -> 4 vCPU / 16 GB RAM`.
8. Click **Execute simulation**.
9. Refresh the inventory and show the updated vCPU, RAM, and monthly cost.
10. Open **Recent Audit** and select **View resize details**.
11. Restart the backend for the automatic path.
12. Leave the new recommendations untouched.
13. After their deadlines expire, the monitor automatically approves and executes them.
14. Show the automatic audit message, health-check result, and before/after resize values.

The **Healthy resources** card is clickable. It opens a detail panel showing each resource's utilization, cost, idle time, criticality, and why no immediate optimization was suggested.

## API Endpoints

- `GET /` - backend health check
- `GET /resources` - current simulated VM inventory
- `GET /metrics` - seven days of simulated CPU and RAM metrics
- `GET /analysis` - utilization, safety, and savings analysis
- `GET /agent/summary` - AI or local fallback summary
- `GET /recommendations` - recommendations and their statuses
- `POST /recommendations/{id}/approve` - manual approval
- `POST /recommendations/{id}/reject` - manual rejection
- `POST /recommendations/{id}/execute` - execute an approved recommendation
- `GET /audit-logs` - persisted approval and execution history
- `GET /docs` - interactive Swagger documentation

The API uses CORS for the local Angular origins `localhost:4200` and `127.0.0.1:4200`.

## Persistence And Reset Behavior

Simulated VM data is stored in `_SIMULATED_VIRTUAL_MACHINES` in `backend/app/simulator.py`. The VM state is held in memory and resets when the backend restarts.

Recommendations and audit logs are stored in `backend/costopti.db`, which is excluded from Git by `.gitignore`.

- `recommendations` stores recommendation status, deadline, decision note, and savings estimate.
- `audit_logs` stores manual decisions, simulated executions, health-check outcomes, and resize details.

The startup seeding logic reuses existing recommendation rows where possible and fills the pending demo batch without creating duplicates.

## AI Summary

`backend/app/ai_agent.py` provides the `/agent/summary` response. Without external configuration, it uses a safe local fallback summary. An optional OpenAI-compatible service can be configured with:

```powershell
$env:LLM_API_URL = "https://example.com/v1/chat/completions"
$env:LLM_API_KEY = "your-key"
$env:LLM_MODEL = "your-model"
```

The AI component summarizes findings only. It cannot approve, execute, or modify simulator resources.

## Safety Behavior

- Production-resource changes are blocked.
- Non-production execution runs a health check.
- Failed health checks restore the original simulated VM state.
- Manual approval does not execute a resize by itself.
- Automatic approval runs the same safety and health checks.
- All decisions and executions are recorded in SQLite audit logs.

## Testing

Run all backend tests:

```powershell
cd backend
python -m unittest discover -s tests -p "test_*.py" -v
```

The suite covers:

- 20 simulated resources and 140 weekly metrics
- Underutilization analysis and recommendation creation
- Multiple randomized demo recommendations
- Pending-batch filling and duplicate prevention
- Manual approval and execution
- Automatic approval after expiry
- Audit persistence
- Resize details

Build the Angular dashboard:

```powershell
cd frontend
npm run build
```

Run an API smoke test manually through `http://127.0.0.1:8000/docs` or import the Postman collection from `postman/AI-Cloud-Cost-Optimizer.postman_collection.json`.
