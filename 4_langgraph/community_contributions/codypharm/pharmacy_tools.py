"""
Prescription Validation Tools for LangGraph Agents
Clean, focused functions - LangGraph will handle tool definitions automatically
"""

import requests
from typing import Dict, List, Optional
import re
from functools import lru_cache


@lru_cache(maxsize=None)
def normalize_drug_name(drug_name: str) -> Dict:
    """
    Normalize drug name using RxNorm API.
    Returns RxCUI, preferred name, ingredients, brand names, ATC classes, etc.
    """
    base_url = "https://rxnav.nlm.nih.gov/REST"
    
    try:
        # Step 1: Find RxCUI
        url = f"{base_url}/drugs?name={requests.utils.quote(drug_name)}"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        
        concept_group = data.get("drugGroup", {}).get("conceptGroup", [])
        if not concept_group:
            return {"success": False, "error": "No match found in RxNorm", "raw_name": drug_name}
        
        # Prefer SCD/SBD/BN/IN
        best = next(
            (c for c in concept_group if c.get("tty") in ["SCD", "SBD", "BN", "IN", "PIN"]),
            concept_group[0]
        )
        rxcui = best.get("rxcui")
        if not rxcui:
            return {"success": False, "error": "No RxCUI found", "raw_name": drug_name}
        
        # Step 2: Get properties
        detail_url = f"{base_url}/rxcui/{rxcui}/properties.json"
        detail_resp = requests.get(detail_url, timeout=6)
        props = detail_resp.json().get("propConceptGroup", {}).get("propConcept", [])
        
        result = {
            "success": True,
            "rxcui": rxcui,
            "input_name": drug_name,
            "preferred_name": next((p["propValue"] for p in props if p["propName"] == "RxNorm Preferred Name"), drug_name),
            "generic_name": next((p["propValue"] for p in props if p["propName"] == "RxNorm Generic Name"), None),
            "ingredients": [],
            "brand_names": [],
            "atc_classes": [],
        }
        
        # Step 3: Related concepts (ingredients, brands)
        rel_url = f"{base_url}/rxcui/{rxcui}/related.json?tty=IN+MIN+PIN+BN"
        rel_resp = requests.get(rel_url, timeout=6)
        rel_data = rel_resp.json().get("relatedGroup", {}).get("conceptGroup", [])
        
        for group in rel_data:
            tty = group.get("tty")
            concepts = group.get("conceptProperties", [])
            if tty == "IN":
                result["ingredients"] = [c["name"] for c in concepts]
            elif tty == "BN":
                result["brand_names"] = [c["name"] for c in concepts]
        
        # Step 4: ATC classification (via RxClass)
        atc_url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={rxcui}&classTypes=ATC"
        atc_resp = requests.get(atc_url, timeout=6)
        atc_data = atc_resp.json().get("rxclassDrugInfoList", {}).get("rxclassDrugInfo", [])
        result["atc_classes"] = [item["classId"] for item in atc_data] if atc_data else []
        
        return result
    
    except Exception as e:
        return {"success": False, "error": str(e), "raw_name": drug_name}

# ============================================================================
# CRITICAL SAFETY CHECKS
# ============================================================================

def check_drug_allergy(
    drug_name: str,
    patient_allergies: List[str],
    normalized: Optional[Dict] = None
) -> Dict:
    """
    Check for direct allergy or cross-reactivity.
    Enhanced with RxNorm ingredients when available.
    """
    norm = normalized or normalize_drug_name(drug_name)
    generic_lower = ""
    ingredients_lower = []

    if norm.get("success"):
        generic_lower = (norm.get("generic_name") or "").lower()
        ingredients_lower = [ing.lower() for ing in norm.get("ingredients", [])]
    else:
        label = get_drug_label_info(drug_name)
        generic_lower = (label.get('generic_name') or '').lower()

    for allergy in [a.lower() for a in patient_allergies]:
        if allergy in generic_lower or any(allergy in ing for ing in ingredients_lower):
            return {
                'has_allergy': True,
                'allergen': allergy,
                'recommendation': "CRITICAL: Documented allergy. DO NOT DISPENSE. Contact prescriber."
            }

        # Basic cross-reactivity examples (expand as needed)
        cross_reactions = {
            'penicillin': ['amoxicillin', 'ampicillin', 'piperacillin'],
            'sulfa': ['sulfamethoxazole', 'sulfasalazine'],
            'statin': ['atorvastatin', 'simvastatin', 'rosuvastatin']
        }
        for allergen_class, related in cross_reactions.items():
            if allergen_class in allergy:
                if any(r in generic_lower or r in ingredients_lower for r in related):
                    return {
                        'has_allergy': True,
                        'allergy_type': 'cross-reactivity',
                        'recommendation': f"Possible cross-reactivity with {allergy}. Verify with prescriber."
                    }

    return {
        'has_allergy': False,
        'recommendation': "No allergy or cross-reactivity detected."
    }



def check_drug_recall(drug_name: str, lot_number: Optional[str] = None) -> Dict:
    """Check FDA recalls (your original function - kept mostly unchanged)"""
    base_url = "https://api.fda.gov/drug/enforcement.json"
    search = f'product_description:"{drug_name}"'
    if lot_number:
        search += f'+AND+code_info:"{lot_number}"'

    try:
        url = f"{base_url}?search={search}&limit=10"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])

        active = [r for r in results if r.get('status', '').lower() in ['ongoing', 'pending']]

        if active:
            return {
                'has_recall': True,
                'active_recalls': active,
                'recommendation': "ACTIVE RECALL DETECTED. DO NOT DISPENSE."
            }
        return {
            'has_recall': False,
            'recommendation': f"No active recalls. {len(results)} historical recalls found."
        }
    except Exception as e:
        return {'has_recall': None, 'recommendation': f"Recall check failed: {str(e)}"}

# ============================================================================
# PATIENT-SPECIFIC CHECKS
# ============================================================================

def check_pregnancy_safety(drug_name: str, trimester: Optional[int] = None) -> Dict:
    """
    Check if drug is safe during pregnancy.
    Use for any pregnant patient.
    
    Returns dict with pregnancy_category, is_safe, risks, recommendation
    """

    print("Pregnancy checker called")
    
    # Normalize to generic for better label match
    norm = normalize_drug_name(drug_name)
    search_name = norm.get("generic_name") or drug_name
    
    label = get_drug_label_info(search_name)
    
    if not label or not label.get('pregnancy_info'):
        return {
            'pregnancy_category': None,
            'is_safe': None,
            'risks': "Pregnancy information not available in FDA label",
            'recommendation': "Consult additional resources (Lexicomp, Micromedex)"
        }
    
    pregnancy_text = label['pregnancy_info'].lower()
    
    # Extract category
    category = None
    for cat in ['category x', 'category d', 'category c', 'category b', 'category a']:
        if cat in pregnancy_text:
            category = cat.replace('category ', '').upper()
            break
    
    # Determine safety
    is_safe = True
    if any(word in pregnancy_text for word in ['contraindicated', 'category x', 'not recommended', 'avoid']):
        is_safe = False
    elif any(word in pregnancy_text for word in ['risk', 'category d', 'adverse']):
        is_safe = None
    
    # Extract risks
    sentences = pregnancy_text.split('.')
    risks = '. '.join(sentences[:3])
    
    recommendation = "Safe to use"
    if is_safe == False:
        recommendation = "CONTRAINDICATED - Do not dispense. Contact prescriber immediately."
    elif is_safe is None:
        recommendation = "Risk present - Review with prescriber. Consider risk-benefit ratio."
    
    return {
        'pregnancy_category': category,
        'is_safe': is_safe,
        'risks': risks,
        'recommendation': recommendation,
        'trimester_note': f"Information applies to trimester {trimester}" if trimester else None
    }


def check_renal_dosing(drug_name: str, creatinine_clearance: float) -> Dict:
    """
    Check if renal dose adjustment is needed.
    Use when patient has CrCl < 60 mL/min.
    
    Returns dict with requires_adjustment, severity, guidance, recommendation
    """
    label = get_drug_label_info(drug_name)
    
    # Normalize to generic for better label match
    norm = normalize_drug_name(drug_name)
    search_name = norm.get("generic_name") or drug_name
    label = get_drug_label_info(search_name)
    
    print("Renal checker called")
    if not label:
        return {
            'requires_adjustment': None,
            'severity': None,
            'guidance': "Drug information not found",
            'recommendation': "Consult renal dosing reference"
        }
    
    dosage_info = (label.get('dosage_info') or '').lower()
    warnings = (label.get('warnings') or '').lower()
    
    search_text = dosage_info + ' ' + warnings
    
    # Check for renal mentions
    renal_keywords = ['renal', 'kidney', 'creatinine clearance', 'renal impairment', 'renal insufficiency']
    has_renal_info = any(keyword in search_text for keyword in renal_keywords)
    
    if not has_renal_info:
        return {
            'requires_adjustment': False,
            'severity': None,
            'guidance': "No renal dosing information in label",
            'recommendation': "Consider consulting additional renal dosing resources"
        }
    
    # Extract relevant text
    sentences = search_text.split('.')
    relevant = [s for s in sentences if any(kw in s for kw in renal_keywords)]
    guidance = '. '.join(relevant[:3])
    
    # Determine severity
    severity = "moderate"
    if creatinine_clearance < 30:
        severity = "severe"
    elif creatinine_clearance < 15:
        severity = "critical"
    
    return {
        'requires_adjustment': True,
        'severity': severity,
        'guidance': guidance,
        'creatinine_clearance': creatinine_clearance,
        'recommendation': f"Renal dose adjustment required (CrCl: {creatinine_clearance} mL/min). Verify appropriate dose."
    }


def check_pediatric_dosing(drug_name: str, patient_age: int, weight_kg: Optional[float] = None) -> Dict:
    """
    Check if pediatric dosing is appropriate.
    Use for patients under 18 years old.
    
    Returns dict with approved_for_age, dosing_info, weight_based, recommendation
    """
    # Normalize to generic for better label match
    norm = normalize_drug_name(drug_name)
    search_name = norm.get("generic_name") or drug_name
    
    label = get_drug_label_info(search_name)
    
    print("Pediatric checker called")
    if not label:
        return {
            'approved_for_age': None,
            'dosing_info': "Drug information not found",
            'weight_based': None,
            'recommendation': "Verify pediatric dosing with reference"
        }
    
    pediatric_info = (label.get('pediatric_use') or '').lower()
    dosage_info = (label.get('dosage_info') or '').lower()
    
    if not pediatric_info and not dosage_info:
        return {
            'approved_for_age': None,
            'dosing_info': "No pediatric information in FDA label",
            'weight_based': None,
            'recommendation': "Verify pediatric use is appropriate."
        }
    
    # Check if approved
    approved = True
    if any(phrase in pediatric_info for phrase in ['not established', 'not recommended', 'contraindicated', 'not approved']):
        approved = False
    
    # Check weight-based dosing
    weight_based = 'mg/kg' in dosage_info or 'weight' in dosage_info
    
    # Extract guidance
    sentences = (pediatric_info + ' ' + dosage_info).split('.')
    relevant = [s for s in sentences if 'pediatric' in s or 'child' in s or 'mg/kg' in s]
    dosing_info_text = '. '.join(relevant[:3]) if relevant else "See full label for pediatric dosing"
    
    recommendation = "Verify dose is appropriate for age and weight"
    if not approved:
        recommendation = "NOT APPROVED for pediatric use. Contact prescriber."
    elif weight_based and weight_kg:
        recommendation = f"Weight-based dosing required (patient: {weight_kg} kg). Calculate mg/kg dose."
    
    return {
        'approved_for_age': approved,
        'patient_age': patient_age,
        'dosing_info': dosing_info_text,
        'weight_based': weight_based,
        'recommendation': recommendation
    }


def check_geriatric_considerations(drug_name: str, patient_age: int) -> Dict:
    """
    Check for special considerations in elderly patients (65+).
    Use for patients 65 years or older.
    
    Returns dict with requires_adjustment, beers_criteria, considerations, recommendation
    """
    # Normalize to generic for better label match
    norm = normalize_drug_name(drug_name)
    search_name = norm.get("generic_name") or drug_name
    
    label = get_drug_label_info(search_name)
    
    print("Geriatric checker called")
    if not label:
        return {
            'requires_adjustment': None,
            'beers_criteria': None,
            'considerations': "Drug information not found",
            'recommendation': "Verify geriatric appropriateness"
        }
    
    geriatric_info = (label.get('geriatric_use') or '').lower()
    warnings = (label.get('warnings') or '').lower()
    
    search_text = geriatric_info + ' ' + warnings
    
    # Check for dose adjustment needs
    requires_adjustment = any(phrase in search_text for phrase in ['lower dose', 'reduce', 'adjust', 'start low'])
    
    # Beers Criteria check (simplified)
    beers_drugs = [
        'diphenhydramine', 'diazepam', 'promethazine', 'hydroxyzine',
        'amitriptyline', 'cyclobenzaprine', 'indomethacin'
    ]
    generic = (label.get('generic_name') or '').lower()
    on_beers = any(drug in generic for drug in beers_drugs)
    
    # Extract considerations
    sentences = search_text.split('.')
    relevant = [s for s in sentences if 'elderly' in s or 'geriatric' in s or 'older' in s]
    considerations = '. '.join(relevant[:3]) if relevant else "See label for geriatric considerations"
    
    recommendation = "Standard dosing appropriate"
    if on_beers:
        recommendation = "HIGH RISK in elderly (Beers Criteria). Consider alternative therapy."
    elif requires_adjustment:
        recommendation = "Dose adjustment recommended for elderly. Start with lower dose."
    
    return {
        'requires_adjustment': requires_adjustment,
        'beers_criteria': on_beers,
        'patient_age': patient_age,
        'considerations': considerations,
        'recommendation': recommendation
    }


# ============================================================================
# INTERACTION & CONTRAINDICATION CHECKS
# ============================================================================

def check_drug_interaction(drug1: str, drug2: str) -> Dict:
    """
    Check if two drugs have a known interaction.
    
    Returns dict with has_interaction, severity, description, recommendation
    """
    label = get_drug_label_info(drug1)
    
    print("Interaction checker called")
    if not label or not label.get('drug_interactions'):
        return {
            'has_interaction': False,
            'severity': None,
            'description': None,
            'recommendation': "Unable to verify - check additional resources"
        }
    
    interactions = label['drug_interactions'].lower()
    drug2_lower = drug2.lower()
    
    # Normalize drug2 to get generic name (labels usually list generics)
    drug2_norm = normalize_drug_name(drug2)
    drug2_generic = (drug2_norm.get("generic_name") or drug2).lower()
    
    # Check if drug2 (brand or generic) mentioned in interactions
    if drug2_lower in interactions or drug2_generic in interactions:
        # Determine severity
        severity = "moderate"
        if any(word in interactions for word in ['contraindicated', 'avoid', 'serious', 'severe']):
            severity = "major"
        elif any(word in interactions for word in ['caution', 'monitor', 'consider']):
            severity = "moderate"
        
        # Extract relevant portion
        sentences = interactions.split('.')
        relevant = [s for s in sentences if drug2_lower in s or drug2_generic in s]
        description = '. '.join(relevant[:2]) if relevant else interactions[:500]
        
        return {
            'has_interaction': True,
            'severity': severity,
            'description': description,
            'recommendation': f"Review interaction between {drug1} and {drug2} ({drug2_generic}). Consider alternative or enhanced monitoring."
        }
    
    return {
        'has_interaction': False,
        'severity': None,
        'description': None,
        'recommendation': f"No interaction found in {drug1} label for {drug2}"
    }


def check_contraindication(drug_name: str, patient_condition: str) -> Dict:
    """
    Check if drug is contraindicated for a specific patient condition.
    
    Returns dict with is_contraindicated, reason, recommendation
    """
    label = get_drug_label_info(drug_name)
    
    print("Contraindication checker called")
    if not label:
        return {
            'is_contraindicated': None,
            'reason': "Drug information not found",
            'recommendation': "Verify with additional resources"
        }
    
    # Check contraindications and warnings
    contraindications = (label.get('contraindications') or '').lower()
    warnings = (label.get('warnings') or '').lower()
    condition_lower = patient_condition.lower()
    
    search_text = contraindications + ' ' + warnings
    
    if condition_lower in search_text:
        # Check if actually contraindicated or just warning
        is_ci = 'contraindicated' in search_text and condition_lower in contraindications
        
        # Extract relevant text
        sentences = search_text.split('.')
        relevant = [s for s in sentences if condition_lower in s][:2]
        reason = '. '.join(relevant) if relevant else f"Concern found regarding {patient_condition}"
        
        return {
            'is_contraindicated': is_ci,
            'reason': reason,
            'recommendation': "DO NOT DISPENSE - Contact prescriber" if is_ci else "Exercise caution - review with pharmacist"
        }
    
    return {
        'is_contraindicated': False,
        'reason': f"No contraindication found for {patient_condition}",
        'recommendation': "Safe to proceed"
    }


def check_duplicate_therapy(medications: List[Dict]) -> List[Dict]:
    """
    Check for duplicate medications in a prescription.
    
    Args:
        medications: List of dicts with 'drug_name' and optionally 'generic_name'
    
    Returns:
        List of duplicate issues found
    """
    duplicates = []
    
    print("Duplicate checker called")
    # Track by generic name
    generic_map = {}
    
    for i, med in enumerate(medications):
        drug_name = med.get('drug_name', '').lower()
        generic_name = med.get('generic_name', '').lower() if med.get('generic_name') else None
        
        # Check generic duplicates
        if generic_name:
            if generic_name in generic_map:
                duplicates.append({
                    'drug1': generic_map[generic_name]['drug_name'],
                    'drug2': med.get('drug_name'),
                    'issue': f"Duplicate therapy: Both contain {generic_name}",
                    'recommendation': "MAJOR: Remove duplicate or verify both intended by prescriber."
                })
            else:
                generic_map[generic_name] = med
        
        # Check brand name duplicates
        for j in range(i + 1, len(medications)):
            other_drug = medications[j].get('drug_name', '').lower()
            if drug_name == other_drug:
                duplicates.append({
                    'drug1': med.get('drug_name'),
                    'drug2': medications[j].get('drug_name'),
                    'issue': "Exact duplicate medication",
                    'recommendation': "CRITICAL: Remove duplicate entry."
                })
    
    return duplicates


# ============================================================================
# DOSING VALIDATION
# ============================================================================
@lru_cache(maxsize=None)
def calculate_daily_dose(dose_per_administration: str, frequency: str) -> Dict:
    """
    Calculate total daily dose from single dose and frequency.
    
    Returns dict with daily_dose_mg, doses_per_day, frequency_parsed, warning
    """
    print("Dosing checker called")
    # Frequency mappings
    freq_map = {
        'qd': 1, 'daily': 1, 'once daily': 1, 'once a day': 1,
        'bid': 2, 'twice daily': 2, 'twice a day': 2, 'q12h': 2,
        'tid': 3, 'three times daily': 3, 'q8h': 3,
        'qid': 4, 'four times daily': 4, 'q6h': 4,
        'q4h': 6, 'q3h': 8, 'q2h': 12,
        'qhs': 1, 'at bedtime': 1, 'hs': 1
    }
    
    freq_lower = frequency.lower().strip()
    doses_per_day = freq_map.get(freq_lower, 0)
    
    if doses_per_day == 0:
        return {
            'daily_dose_mg': None,
            'doses_per_day': None,
            'frequency_parsed': None,
            'warning': f"Unable to parse frequency: {frequency}"
        }
    
    # Extract dose amount
    dose_match = re.search(r'(\d+\.?\d*)', dose_per_administration)
    if not dose_match:
        return {
            'daily_dose_mg': None,
            'doses_per_day': doses_per_day,
            'frequency_parsed': freq_lower,
            'warning': f"Unable to parse dose: {dose_per_administration}"
        }
    
    dose_mg = float(dose_match.group(1))
    daily_dose = dose_mg * doses_per_day
    
    # Check for unusual frequency
    warning = None
    if doses_per_day > 6:
        warning = f"Unusually high frequency: {doses_per_day} times per day. Verify with prescriber."
    
    return {
        'daily_dose_mg': daily_dose,
        'dose_per_administration_mg': dose_mg,
        'doses_per_day': doses_per_day,
        'frequency_parsed': freq_lower,
        'warning': warning
    }

# ============================================================================
# REGIMEN-LEVEL CHECKS 
# ============================================================================

def check_multi_drug_interactions(drugs: List[str]) -> Dict:
    """
    Basic multi-drug interaction scan (label-based pairwise).
    Production recommendation: replace with DrugBank / FDB / Medi-Span API.
    """
    issues = []
    seen_pairs = set()

    for i, drug1 in enumerate(drugs):
        label = get_drug_label_info(drug1)
        interactions_text = (label.get('drug_interactions') or '').lower()

        for j, drug2 in enumerate(drugs[i+1:], start=i+1):
            pair = tuple(sorted([drug1.lower(), drug2.lower()]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            drug2_norm = normalize_drug_name(drug2)
            drug2_generic = (drug2_norm.get("generic_name") or drug2).lower()

            if drug2.lower() in interactions_text or drug2_generic in interactions_text:
                severity = "major" if any(w in interactions_text for w in ['contraindicated', 'avoid', 'serious']) else "moderate"
                issues.append({
                    'pair': (drug1, drug2),
                    'severity': severity,
                    'source': 'fda_label'
                })

    if issues:
        return {
            'has_interactions': True,
            'issues': issues,
            'recommendation': "Potential drug-drug interactions detected - urgent review required."
        }
    return {
        'has_interactions': False,
        'recommendation': "No interactions found in available labels."
    }


def check_therapeutic_duplication(medications: List[Dict]) -> List[Dict]:
    """
    Detect exact duplicates and therapeutic class duplication using ATC codes.
    Expects medications = [{'drug_name': str, 'normalized': Dict (optional)}, ...]
    """
    duplicates = []
    class_seen: Dict[str, List[str]] = {}  # atc_level_4/5 → drug list
    generic_seen = set()

    for med in medications:
        drug_name = med.get('drug_name', '')
        norm = med.get('normalized') or normalize_drug_name(drug_name)

        if not norm.get("success"):
            continue

        generic = (norm.get("generic_name") or drug_name).lower()
        atc_list = norm.get("atc_classes", [])

        # Exact generic duplicate
        if generic in generic_seen:
            duplicates.append({
                'type': 'exact_duplicate',
                'generic': generic,
                'drugs': [drug_name],
                'recommendation': "Duplicate therapy - same active ingredient"
            })
        generic_seen.add(generic)

        # Therapeutic class duplication (ATC level 4 or 5)
        for atc in atc_list:
            atc_key = atc[:5]  # typically level 4 or 5
            if atc_key in class_seen:
                duplicates.append({
                    'type': 'therapeutic_duplication',
                    'atc_class': atc_key,
                    'drugs': class_seen[atc_key] + [drug_name],
                    'recommendation': f"Therapeutic class duplication (ATC {atc_key})"
                })
            class_seen.setdefault(atc_key, []).append(drug_name)

    return duplicates


def get_controlled_substance_info(drug_name: str, rxcui: Optional[str] = None) -> Dict:
    """Determine DEA schedule via openFDA NDC data"""
    try:
        if rxcui:
            url = f"https://api.fda.gov/drug/ndc.json?search=openfda.rxcui:{rxcui}&limit=3"
        else:
            url = f"https://api.fda.gov/drug/ndc.json?search=openfda.brand_name:\"{drug_name}\"&limit=3"

        resp = requests.get(url, timeout=8)
        data = resp.json()
        results = data.get('results', [])

        if not results:
            return {'is_controlled': False, 'schedule': 'Unknown', 'recommendation': "No NDC/schedule data found"}

        sched = results[0].get('openfda', {}).get('dea_schedule', ['Not controlled'])[0]

        if sched in ['2', '3', '4', '5']:
            return {
                'is_controlled': True,
                'schedule': f"Schedule {sched}",
                'recommendation': f"Controlled substance (DEA Sch {sched}) — PDMP query recommended"
            }
        return {
            'is_controlled': False,
            'schedule': sched,
            'recommendation': "Non-controlled substance"
        }

    except Exception:
        return {'is_controlled': None, 'recommendation': "Unable to determine controlled status"}

# ============================================================================
# DRUG INFORMATION
# ============================================================================
@lru_cache(maxsize=None)
def get_drug_label_info(drug_name: str) -> Dict:
    """
    Get comprehensive FDA drug label information.
    
    Returns dict with drug details including indications, contraindications,
    warnings, interactions, dosing, pregnancy info, etc.
    """
    base_url = "https://api.fda.gov/drug/label.json"
    
    print("Label checker called")
    # Try brand name first
    try:
        url = f"{base_url}?search=openfda.brand_name:\"{drug_name}\"&limit=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results'):
            return _extract_label_info(data['results'][0])
    except:
        pass
    
    # Try generic name
    try:
        url = f"{base_url}?search=openfda.generic_name:\"{drug_name}\"&limit=1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results'):
            return _extract_label_info(data['results'][0])
    except:
        pass
    
    return {}


def _extract_label_info(label: Dict) -> Dict:
    """Helper to extract key fields from FDA label"""
    def get_text(field):
        data = label.get(field, [])
        if isinstance(data, list) and data:
            return " ".join(str(x) for x in data)
        return None
    
    openfda = label.get('openfda', {})
    
    return {
        'drug_name': openfda.get('brand_name', [None])[0],
        'generic_name': openfda.get('generic_name', [None])[0],
        'brand_names': openfda.get('brand_name', []),
        'manufacturer': openfda.get('manufacturer_name', [None])[0],
        'indications': get_text('indications_and_usage'),
        'contraindications': get_text('contraindications'),
        'warnings': get_text('warnings_and_cautions') or get_text('warnings'),
        'adverse_reactions': get_text('adverse_reactions'),
        'drug_interactions': get_text('drug_interactions'),
        'dosage_info': get_text('dosage_and_administration'),
        'pregnancy_info': get_text('pregnancy'),
        'pediatric_use': get_text('pediatric_use'),
        'geriatric_use': get_text('geriatric_use'),
        'storage': get_text('storage_and_handling')
    }


# ============================================================================
# EXAMPLE USAGE (for testing)
# ============================================================================

if __name__ == "__main__":
    print("=== Testing Prescription Validation Tools ===\n")
    
    # Test 1: Allergy check
    print("1. Checking allergy...")
    result = check_drug_allergy("Amoxicillin", ["penicillin"])
    print(f"   Has allergy: {result['has_allergy']}")
    print(f"   Recommendation: {result['recommendation']}\n")
    
    # Test 2: Drug interaction
    print("2. Checking interaction...")
    result = check_drug_interaction("Warfarin", "Aspirin")
    print(f"   Has interaction: {result['has_interaction']}")
    print(f"   Severity: {result.get('severity')}\n")
    
    # Test 3: Pregnancy safety
    print("3. Checking pregnancy safety...")
    result = check_pregnancy_safety("Lisinopril", trimester=1)
    print(f"   Is safe: {result['is_safe']}")
    print(f"   Category: {result.get('pregnancy_category')}\n")
    
    # Test 4: Calculate daily dose
    print("4. Calculating daily dose...")
    result = calculate_daily_dose("500mg", "TID")
    print(f"   Daily dose: {result['daily_dose_mg']}mg")
    print(f"   Doses per day: {result['doses_per_day']}\n")
    
    # Test 5: Renal dosing
    print("5. Checking renal dosing...")
    result = check_renal_dosing("Gabapentin", creatinine_clearance=30)
    print(f"   Requires adjustment: {result['requires_adjustment']}")
    print(f"   Severity: {result.get('severity')}\n")