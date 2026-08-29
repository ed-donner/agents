"""Rule data for educational triage only — not medical advice."""

from __future__ import annotations

# (label, keywords, lay_summary) — keywords matched case-insensitively as substrings
CONDITION_HINTS: list[tuple[str, tuple[str, ...], str]] = [
    (
        "Common cold / viral upper respiratory infection",
        ("runny nose", "nasal congestion", "sneezing", "sore throat", "mild cough", "low grade fever"),
        "Often self-limited; rest, fluids, and monitoring are typical. Seek care if high fever, trouble breathing, or symptoms worsen.",
    ),
    (
        "Influenza (flu)",
        ("high fever", "body aches", "chills", "fatigue", "headache", "sudden onset"),
        "Can be similar to a cold but often more intense. High-risk groups should consider clinical evaluation, especially early in illness.",
    ),
    (
        "COVID-19 or other viral respiratory illness",
        ("loss of smell", "loss of taste", "covid", "positive test", "exposure"),
        "Overlaps with other respiratory infections; testing and isolation guidance depend on local protocols and risk factors.",
    ),
    (
        "Acute gastroenteritis (stomach bug)",
        ("vomiting", "diarrhea", "nausea", "stomach cramps", "food poisoning"),
        "Hydration is key. Seek urgent care for blood in stool, severe dehydration, or inability to keep fluids down.",
    ),
    (
        "Migraine or tension-type headache",
        ("throbbing headache", "one-sided headache", "light sensitivity", "sound sensitivity", "aura", "tension headache"),
        "Many headaches are benign; sudden severe or new neurological symptoms need urgent evaluation.",
    ),
    (
        "Urinary tract infection",
        ("burning urination", "frequent urination", "urgency", "cloudy urine", "suprapubic pain", "flank pain"),
        "Simple UTIs are common; fever, back pain, or systemic symptoms may suggest kidney involvement — clinical assessment advised.",
    ),
    (
        "Allergic rhinitis / allergies",
        ("itchy eyes", "seasonal", "pollen", "clear nasal discharge", "sneezing fits"),
        "Often responsive to antihistamines or avoidance; anaphylaxis (throat swelling, wheeze) is an emergency.",
    ),
    (
        "Reflux / dyspepsia",
        ("heartburn", "acid reflux", "burning chest after eating", "indigestion"),
        "Lifestyle changes and OTC options help many; chest pain with exertion is not assumed to be reflux.",
    ),
    (
        "Musculoskeletal strain",
        ("after lifting", "muscle strain", "localized pain", "better with rest", "worse with movement"),
        "Often improves with rest and gradual return to activity; numbness, weakness, or trauma warrants evaluation.",
    ),
    (
        "Anxiety or panic-related symptoms",
        ("panic", "anxiety", "racing heart", "tingling", "feeling of doom", "hyperventilation"),
        "Can mimic serious illness; first episode or atypical symptoms should be medically evaluated to rule out other causes.",
    ),
]

# phrase -> (severity, message)
RED_FLAGS: list[tuple[str, str, str]] = [
    ("chest pain", "emergency", "Chest pain can indicate heart or lung emergencies — seek emergency care now."),
    ("crushing chest", "emergency", "Possible cardiac emergency — call emergency services immediately."),
    ("can't breathe", "emergency", "Severe breathing difficulty — emergency care immediately."),
    ("cannot breathe", "emergency", "Severe breathing difficulty — emergency care immediately."),
    ("shortness of breath at rest", "emergency", "Resting shortness of breath may be serious — seek urgent or emergency care."),
    ("face drooping", "emergency", "Possible stroke — emergency services immediately."),
    ("slurred speech", "emergency", "Possible stroke or serious neurological event — emergency care immediately."),
    ("sudden weakness", "emergency", "Sudden weakness can be stroke or other emergency — seek immediate care."),
    ("worst headache of my life", "emergency", "Thunderclap headache needs urgent evaluation — emergency department."),
    ("thunderclap headache", "emergency", "Sudden severe headache — emergency evaluation."),
    ("coughing up blood", "emergency", "Hemoptysis — urgent medical evaluation."),
    ("blood in stool", "urgent", "Blood in stool needs prompt medical assessment (especially if black/tarry or large volume)."),
    ("black stool", "urgent", "Black tarry stools may indicate bleeding — urgent evaluation."),
    ("severe abdominal pain", "urgent", "Severe or worsening abdominal pain — urgent in-person evaluation."),
    ("stiff neck and fever", "emergency", "Meningitis must be ruled out — emergency care."),
    ("confusion", "urgent", "New confusion or altered mental status — urgent evaluation."),
    ("suicidal", "emergency", "Mental health crisis — contact local crisis line or emergency services immediately."),
    ("kill myself", "emergency", "Mental health crisis — emergency services or crisis hotline now."),
    ("anaphylaxis", "emergency", "Possible severe allergic reaction — use epinephrine if prescribed and emergency services."),
    ("throat closing", "emergency", "Possible airway emergency — emergency services immediately."),
    ("fainting", "urgent", "Syncope with injury, recurrence, or cardiac symptoms needs urgent evaluation."),
    ("pregnancy and severe pain", "urgent", "Pregnancy with severe pain or bleeding — urgent obstetric evaluation."),
    ("testicular pain sudden", "urgent", "Sudden severe testicular pain — urgent evaluation (possible torsion)."),
    ("vision loss sudden", "emergency", "Sudden vision loss — emergency ophthalmology / ED."),
    ("paralysis", "emergency", "Sudden paralysis — emergency services."),
]
