from typing import Dict, Optional

MEDICATION_DATABASE: Dict[str, Dict[str, str]] = {
    "cetirizine": {
        "name": "Cetirizine",
        "class": "Second-generation Antihistamine",
        "uses": "Relief of allergy symptoms including allergic rhinitis (sneezing, runny nose, itchy/watery eyes) and chronic urticaria (hives/itching).",
        "mechanism": "Selectively blocks peripheral H1 histamine receptors to prevent allergic responses with minimal sedation.",
        "precaution": "May cause mild drowsiness in some individuals. Avoid alcohol during use.",
        "department": "General Medicine / ENT",
    },
    "citrazine": {
        "name": "Cetirizine (Brand names: Zyrtec, Cetzine, Alerid)",
        "class": "Second-generation Antihistamine",
        "uses": "Relief of allergy symptoms including allergic rhinitis (sneezing, runny nose, itchy/watery eyes) and chronic urticaria (hives/itching).",
        "mechanism": "Selectively blocks peripheral H1 histamine receptors to prevent allergic responses with minimal sedation.",
        "precaution": "May cause mild drowsiness in some individuals. Avoid alcohol during use.",
        "department": "General Medicine / ENT",
    },
    "cetrizine": {
        "name": "Cetirizine (Brand names: Zyrtec, Cetzine, Alerid)",
        "class": "Second-generation Antihistamine",
        "uses": "Relief of allergy symptoms including allergic rhinitis (sneezing, runny nose, itchy/watery eyes) and chronic urticaria (hives/itching).",
        "mechanism": "Selectively blocks peripheral H1 histamine receptors to prevent allergic responses with minimal sedation.",
        "precaution": "May cause mild drowsiness in some individuals. Avoid alcohol during use.",
        "department": "General Medicine / ENT",
    },
    "crocin": {
        "name": "Crocin (Paracetamol / Acetaminophen)",
        "class": "Analgesic and Antipyretic",
        "uses": "Fever reduction and relief from headaches, body pain, toothaches.",
        "mechanism": "Inhibits prostaglandin synthesis in the central nervous system.",
        "precaution": "Do not exceed maximum daily limits (4000mg/day). Avoid alcohol.",
        "department": "General Medicine",
    },
    "dolo": {
        "name": "Dolo 650 (Paracetamol 650mg)",
        "class": "Analgesic and Antipyretic",
        "uses": "Treatment of fever and body pain.",
        "mechanism": "Inhibits prostaglandin synthesis in the CNS.",
        "precaution": "Avoid combining with other paracetamol-containing drugs.",
        "department": "General Medicine",
    },

    "paracetamol": {
        "name": "Paracetamol (Acetaminophen)",
        "class": "Analgesic and Antipyretic",
        "uses": "Treatment of mild-to-moderate pain (headaches, muscle aches, toothaches) and reduction of fever.",
        "mechanism": "Inhibits prostaglandin synthesis in the central nervous system.",
        "precaution": "Do not exceed maximum daily limits to prevent hepatotoxicity (liver damage).",
        "department": "General Medicine",
    },
    "acetaminophen": {
        "name": "Acetaminophen (Paracetamol)",
        "class": "Analgesic and Antipyretic",
        "uses": "Treatment of mild-to-moderate pain and reduction of fever.",
        "mechanism": "Inhibits prostaglandin synthesis in the CNS.",
        "precaution": "Avoid consuming with alcohol or combining multiple acetaminophen-containing products.",
        "department": "General Medicine",
    },
    "ibuprofen": {
        "name": "Ibuprofen",
        "class": "Nonsteroidal Anti-inflammatory Drug (NSAID)",
        "uses": "Relief of pain, inflammation, swelling, and fever (e.g., arthritis, dental pain, menstrual cramps).",
        "mechanism": "Non-selectively inhibits COX-1 and COX-2 enzymes, reducing inflammatory prostaglandin synthesis.",
        "precaution": "Take with food or milk to minimize gastrointestinal upset. Not recommended for active peptic ulcers.",
        "department": "General Medicine / Orthopedics",
    },
    "amoxicillin": {
        "name": "Amoxicillin",
        "class": "Beta-lactam Antibiotic (Penicillin group)",
        "uses": "Treatment of bacterial infections such as ear, nose, throat, respiratory tract, and urinary tract infections.",
        "mechanism": "Inhibits bacterial cell wall synthesis during active multiplication.",
        "precaution": "Strictly requires a physician prescription. Complete full prescribed course. Contraindicated in penicillin allergy.",
        "department": "General Medicine / ENT",
    },
    "azithromycin": {
        "name": "Azithromycin",
        "class": "Macrolide Antibiotic",
        "uses": "Bacterial respiratory infections, skin infections, sinusitis, and certain sexually transmitted infections.",
        "mechanism": "Binds to the 50S ribosomal subunit of susceptible microorganisms, interfering with protein synthesis.",
        "precaution": "Prescription only. Take as instructed by your doctor.",
        "department": "General Medicine / Pulmonology",
    },
    "metformin": {
        "name": "Metformin",
        "class": "Biguanide Antidiabetic Agent",
        "uses": "First-line medication for the management of Type 2 Diabetes Mellitus.",
        "mechanism": "Decreases hepatic glucose production and improves insulin sensitivity.",
        "precaution": "Take with meals. Regular kidney function and blood glucose monitoring recommended.",
        "department": "General Medicine / Endocrinology",
    },
    "pantoprazole": {
        "name": "Pantoprazole",
        "class": "Proton Pump Inhibitor (PPI)",
        "uses": "Gastroesophageal reflux disease (GERD), acid reflux, heartburn, and stomach ulcers.",
        "mechanism": "Inhibits the H+/K+ ATPase enzyme system in gastric parietal cells, reducing stomach acid production.",
        "precaution": "Typically taken before morning meals.",
        "department": "General Medicine / Gastroenterology",
    },
    "montelukast": {
        "name": "Montelukast",
        "class": "Leukotriene Receptor Antagonist",
        "uses": "Maintenance treatment of asthma and relief of seasonal/perennial allergic rhinitis symptoms.",
        "mechanism": "Blocks the action of leukotrienes to decrease airway inflammation and bronchoconstriction.",
        "precaution": "Use consistently as prescribed. Not intended for the reversal of acute asthma attacks.",
        "department": "Pulmonology / Allergy",
    },
    "atorvastatin": {
        "name": "Atorvastatin",
        "class": "HMG-CoA Reductase Inhibitor (Statin)",
        "uses": "Lowering elevated total cholesterol, LDL cholesterol, and triglycerides; reducing cardiovascular risk.",
        "mechanism": "Competitively inhibits HMG-CoA reductase, the rate-limiting enzyme in hepatic cholesterol biosynthesis.",
        "precaution": "Prescription only. Periodic liver enzyme testing recommended.",
        "department": "Cardiology / General Medicine",
    },
    "amlodipine": {
        "name": "Amlodipine",
        "class": "Dihydropyridine Calcium Channel Blocker",
        "uses": "Management of essential hypertension (high blood pressure) and chronic stable angina.",
        "mechanism": "Inhibits calcium ion influx across vascular smooth muscle and cardiac muscle cells, causing vasodilation.",
        "precaution": "Monitor blood pressure regularly. May cause mild ankle edema.",
        "department": "Cardiology",
    },
}


def lookup_medication(query: str) -> Optional[Dict[str, str]]:
    q = query.lower()
    for key, data in MEDICATION_DATABASE.items():
        if key in q:
            return data
    return None
