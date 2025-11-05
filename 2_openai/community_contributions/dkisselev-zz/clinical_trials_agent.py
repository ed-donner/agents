from agents import Agent, function_tool
import requests
from typing import Dict


@function_tool
def search_clinical_trials(query: str, max_results: int = 10) -> Dict[str, any]:
    """
    Search ClinicalTrials.gov for relevant clinical trials.
    
    Args:
        query: Search query (e.g., "NSCLC EGFR T790M")
        max_results: Maximum number of results to return (default 10)
    
    Returns:
        Dictionary containing clinical trial information
    """
    try:
        # ClinicalTrials.gov API v2
        base_url = "https://clinicaltrials.gov/api/v2/studies"
        
        params = {
            "query.term": query,
            "pageSize": max_results,
            "format": "json",
            "fields": "NCTId,BriefTitle,OverallStatus,Phase,Condition,InterventionName,PrimaryOutcomeMeasure,StudyFirstPostDate"
        }
        
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        studies = data.get("studies", [])
        
        if not studies:
            return {
                "success": True,
                "count": 0,
                "trials": [],
                "message": "No clinical trials found for this query"
            }
        
        trials = []
        for study in studies:
            protocol_section = study.get("protocolSection", {})
            identification = protocol_section.get("identificationModule", {})
            status = protocol_section.get("statusModule", {})
            design = protocol_section.get("designModule", {})
            conditions = protocol_section.get("conditionsModule", {})
            interventions = protocol_section.get("armsInterventionsModule", {})
            outcomes = protocol_section.get("outcomesModule", {})
            
            nct_id = identification.get("nctId", "")
            
            trials.append({
                "nct_id": nct_id,
                "title": identification.get("briefTitle", ""),
                "status": status.get("overallStatus", ""),
                "phase": design.get("phases", ["N/A"]),
                "conditions": conditions.get("conditions", []),
                "interventions": [
                    interv.get("name", "") 
                    for interv in interventions.get("interventions", [])
                ][:5],  # Limit to 5 interventions
                "primary_outcome": outcomes.get("primaryOutcomes", [{}])[0].get("measure", "") if outcomes.get("primaryOutcomes") else "",
                "first_posted": status.get("studyFirstPostDate", ""),
                "url": f"https://clinicaltrials.gov/study/{nct_id}"
            })
        
        return {
            "success": True,
            "count": len(trials),
            "trials": trials,
            "query": query
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"ClinicalTrials.gov API error: {str(e)}",
            "count": 0,
            "trials": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "count": 0,
            "trials": []
        }


INSTRUCTIONS = """You are a clinical trials research specialist.

Given a search term and reason for searching, use the search_clinical_trials tool to find relevant ongoing or completed clinical trials.
After retrieving the results, synthesize a concise summary (2-3 paragraphs, max 300 words) that:
- Highlights the most relevant active or recently completed trials
- Notes the trial phase, interventions/drugs being tested
- Identifies key outcome measures when available
- Groups trials by intervention type or phase when appropriate
- Cites specific NCT IDs for important trials

Focus on actionable clinical information. If no trials are found, clearly state this.
"""

clinical_trials_agent = Agent(
    name="ClinicalTrialsAgent",
    instructions=INSTRUCTIONS,
    tools=[search_clinical_trials],
    model="gpt-4o-mini",
)

