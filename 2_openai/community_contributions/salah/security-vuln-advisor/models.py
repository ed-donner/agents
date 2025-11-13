from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ExploitabilityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EffortLevel(str, Enum):
    QUICK = "QUICK"
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    MINIMAL = "MINIMAL"


class Vulnerability(BaseModel):
    cve_id: str = Field(description="CVE identifier")
    package_name: str = Field(description="Affected package/library name")
    installed_version: str = Field(description="Currently installed version")
    severity: SeverityLevel = Field(description="Severity level from Trivy")
    type: str = Field(description="Type: OS Package, Library, etc.")
    description: str = Field(description="Vulnerability description")
    cvss_score: Optional[float] = Field(default=None, description="CVSS score if available")


class AnalyzedVulnerability(BaseModel):
    cve_id: str = Field(description="CVE identifier")
    package_name: str = Field(description="Affected package")
    severity: SeverityLevel = Field(description="Original severity")
    risk_score: int = Field(description="Risk score 0-100")
    exploitability: ExploitabilityLevel = Field(description="Exploitability assessment")
    affected_component: str = Field(description="Component affected (OS, dependency, etc)")
    description: str = Field(description="What the vulnerability is")
    why_risky: str = Field(description="Business impact if not fixed")
    priority_rank: int = Field(description="1=highest priority")
    is_critical: bool = Field(description="True if needs immediate attention")


class VulnerabilityAnalysis(BaseModel):
    total_found: int = Field(description="Total vulnerabilities found")
    critical_count: int = Field(description="Number of critical issues")
    high_count: int = Field(description="Number of high severity issues")
    medium_count: int = Field(description="Number of medium severity issues")
    low_count: int = Field(description="Number of low severity issues")
    analysis: List[AnalyzedVulnerability] = Field(description="Analyzed vulnerabilities")
    summary: str = Field(description="Executive summary of findings")
    key_risks: List[str] = Field(description="Top 3-5 key risks")


class RemediationStep(BaseModel):
    step_number: int = Field(description="Step sequence number")
    action: str = Field(description="Action to take (e.g., 'Update base image')")
    package_name: str = Field(description="Package/component to update")
    current_version: str = Field(description="Current version")
    recommended_version: str = Field(description="Recommended upgrade version")
    command: str = Field(description="Shell command to execute")
    effort_level: EffortLevel = Field(description="Estimated effort")
    effort_hours: float = Field(description="Estimated hours to implement")
    risk_of_not_fixing: RiskLevel = Field(description="Business risk if not fixed")
    confidence: ConfidenceLevel = Field(description="Confidence in recommendation")
    notes: str = Field(description="Additional context")
    potential_breaking_changes: List[str] = Field(description="Possible breaking changes")
    alternatives: List[str] = Field(description="Alternative solutions if this doesn't work")


class RemediationPlan(BaseModel):
    cve_id: str = Field(description="CVE being addressed")
    package_name: str = Field(description="Package name")
    severity: SeverityLevel = Field(description="Severity level")
    summary: str = Field(description="Quick summary of remediation approach")
    steps: List[RemediationStep] = Field(description="Ordered remediation steps")
    total_effort_hours: float = Field(description="Total estimated effort")
    total_effort_level: EffortLevel = Field(description="Overall effort classification")
    can_auto_fix: bool = Field(description="True if can be auto-fixed")
    requires_testing: bool = Field(description="True if requires testing")
    estimated_cost: str = Field(description="'FREE', 'LOW', 'MEDIUM'")
    dockerfile_snippet: str = Field(description="Example Dockerfile changes")
    priority: int = Field(description="Priority 1=highest")
    time_to_fix_days: float = Field(description="Recommended days to implement")


class RemediationPlans(BaseModel):
    total_remediation_plans: int = Field(description="Number of vulnerability fixes")
    critical_plans: int = Field(description="Critical remediation plans")
    plans: List[RemediationPlan] = Field(description="All remediation plans")
    overall_effort_hours: float = Field(description="Total effort across all fixes")
    implementation_timeline: str = Field(description="Suggested timeline (days)")
    quick_wins: List[str] = Field(description="Easy fixes to do first")


class SecurityReport(BaseModel):
    image_name: str = Field(description="Docker image scanned")
    scan_timestamp: str = Field(description="When scan was performed")
    overall_risk_level: RiskLevel = Field(description="Overall risk assessment")

    executive_summary: str = Field(description="High-level findings for executives")
    key_findings: List[str] = Field(description="Top findings")

    vulnerabilities_summary: Dict[str, int] = Field(description="Count by severity")
    critical_issues: List[str] = Field(description="Critical items needing immediate action")

    remediation_roadmap: str = Field(description="Timeline and action plan (markdown)")
    immediate_actions: List[str] = Field(description="Do these today")
    weekly_actions: List[str] = Field(description="Do these this week")
    monthly_actions: List[str] = Field(description="Do this within a month")

    estimated_total_effort_hours: float = Field(description="Total effort estimate")
    implementation_priority: List[str] = Field(description="Priority order")

    next_steps: List[str] = Field(description="What to do after remediation")
    rescan_recommendation_days: int = Field(description="Days until next scan")

    detailed_findings: str = Field(description="Full report in markdown")


class ScanResult(BaseModel):
    image_name: str
    vulnerabilities: List[Vulnerability]
    analysis: VulnerabilityAnalysis
    remediation_plans: RemediationPlans
    report: SecurityReport
