import { HttpClient } from '@angular/common/http';
import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, inject, signal, OnDestroy } from '@angular/core';
import { forkJoin } from 'rxjs';

@Component({
  imports: [DatePipe, DecimalPipe],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App implements OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://127.0.0.1:8000';
  private readonly refreshTimer = window.setInterval(() => {
    this.refresh();
  }, 5000);
  protected readonly loading = signal(true);
  protected readonly error = signal('');
  protected readonly resources = signal<VirtualMachine[]>([]);
  protected readonly analyses = signal<Analysis[]>([]);
  protected readonly recommendations = signal<Recommendation[]>([]);
  protected readonly auditLogs = signal<AuditLogEntry[]>([]);
  protected readonly agentSummary = signal<AgentSummary | null>(null);
  protected readonly lastUpdated = signal(new Date());
  protected readonly busyRecommendation = signal('');
  protected readonly executionMessage = signal('');
  protected readonly expandedAuditEntry = signal('');
  protected readonly healthyPanelOpen = signal(false);
  protected readonly selectedHealthyResource = signal<VirtualMachine | null>(null);

  protected readonly pendingRecommendations = () => this.recommendations().filter((item) => item.status === 'pending_approval');
  protected readonly reviewRecommendations = () => this.recommendations().filter((item) => ['pending_approval', 'approved'].includes(item.status));
  protected readonly activeRecommendations = () => this.pendingRecommendations();
  protected readonly totalMonthlyCost = () => this.resources().reduce((total, item) => total + item.monthly_cost_inr, 0);
  protected readonly totalSavings = () => this.activeRecommendations().reduce((total, item) => total + item.estimated_monthly_savings_inr, 0);
  protected readonly needsAttentionCount = () => this.activeRecommendations().length;
  protected readonly healthyResources = () => this.resources().filter((resource) => !this.activeRecommendations().some((recommendation) => recommendation.resource_id === resource.id));
  protected readonly healthyResourceCount = () => this.healthyResources().length;

  constructor() { this.refresh(true); }

  ngOnDestroy(): void {
    window.clearInterval(this.refreshTimer);
  }

  protected refresh(showLoader = false): void {
    if (showLoader) {
      this.loading.set(true);
    }
    this.error.set('');
    forkJoin({
      resources: this.http.get<VirtualMachine[]>(`${this.apiUrl}/resources`),
      analyses: this.http.get<Analysis[]>(`${this.apiUrl}/analysis`),
      recommendations: this.http.get<Recommendation[]>(`${this.apiUrl}/recommendations`),
      summary: this.http.get<AgentSummary>(`${this.apiUrl}/agent/summary`),
      auditLogs: this.http.get<AuditLogEntry[]>(`${this.apiUrl}/audit-logs`),
    }).subscribe({
      next: (data) => {
        this.resources.set(data.resources);
        this.analyses.set(data.analyses);
        this.recommendations.set(data.recommendations);
        this.auditLogs.set(data.auditLogs);
        this.agentSummary.set(data.summary);
        this.lastUpdated.set(new Date());
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Backend unavailable. Start FastAPI on port 8000 and refresh.');
        this.loading.set(false);
      },
    });
  }

  protected decide(recommendation: Recommendation, decision: 'approve' | 'reject'): void {
    this.busyRecommendation.set(recommendation.id);
    this.http.post<Recommendation>(`${this.apiUrl}/recommendations/${recommendation.id}/${decision}`, { note: `Dashboard decision: ${decision}` }).subscribe({
      next: () => { this.busyRecommendation.set(''); this.refresh(); },
      error: () => { this.busyRecommendation.set(''); this.error.set('This recommendation may already have a decision. Refresh and try again.'); },
    });
  }

  protected statusClass(status: string): string { return status.replaceAll('_', '-'); }

  protected toggleAuditDetails(recommendationId: string): void {
    this.expandedAuditEntry.update((current) => current === recommendationId ? '' : recommendationId);
  }

  protected showHealthyResources(): void {
    this.healthyPanelOpen.set(true);
    this.selectedHealthyResource.set(null);
  }

  protected inspectHealthyResource(resource: VirtualMachine): void {
    this.selectedHealthyResource.set(resource);
  }

  protected closeHealthyResources(): void {
    this.healthyPanelOpen.set(false);
    this.selectedHealthyResource.set(null);
  }

  protected analysisFor(resource: VirtualMachine): Analysis | undefined {
    return this.analyses().find((analysis) => analysis.resource_id === resource.id);
  }

  protected healthReason(resource: VirtualMachine): string {
    const analysis = this.analysisFor(resource);
    if (!analysis) {
      return 'The latest analysis did not flag this resource for immediate optimization.';
    }
    if (!analysis.underutilized) {
      return 'Utilization or activity is above the optimization threshold, so no rightsizing action was suggested.';
    }
    return 'No pending action is currently waiting for approval.';
  }

  protected resourceForRecommendation(recommendation: Recommendation): VirtualMachine | undefined {
    return this.resources().find((resource) => resource.id === recommendation.resource_id);
  }

  protected plannedVcpus(recommendation: Recommendation): number {
    const resource = this.resourceForRecommendation(recommendation);
    return resource ? Math.max(1, Math.floor(resource.vcpus / 2)) : 0;
  }

  protected plannedRam(recommendation: Recommendation): number {
    const resource = this.resourceForRecommendation(recommendation);
    return resource ? Math.max(1, Math.floor(resource.ram_gb / 2)) : 0;
  }

  protected recommendationReceivedAt(recommendation: Recommendation): Date | null {
    if (!recommendation.approval_deadline) {
      return null;
    }
    const deadline = new Date(recommendation.approval_deadline);
    deadline.setMinutes(deadline.getMinutes() - recommendation.waiting_period_hours);
    return deadline;
  }

}

interface VirtualMachine {
  id: string; name: string; vcpus: number; ram_gb: number; cpu_utilization_percent: number;
  ram_utilization_percent: number; monthly_cost_inr: number; environment: string; status: string;
  disk_utilization_percent: number; network_utilization_percent: number; idle_hours_per_day: number; criticality: string;
}

interface Analysis {
  resource_id: string; resource_name: string; average_cpu_utilization_percent: number;
  average_ram_utilization_percent: number; monthly_cost_inr: number; underutilized: boolean;
  estimated_monthly_savings_inr: number; recommendation: string;
}

interface Recommendation {
  id: string; resource_id: string; resource_name: string; action: string;
  estimated_monthly_savings_inr: number; waiting_period_hours: number; status: string; decision_note: string | null; approval_deadline: string | null;
}

interface AgentSummary { summary: string; source: string; }
interface AuditLogEntry { recommendation_id: string; resource_id: string; action: string; status: string; message: string; }
