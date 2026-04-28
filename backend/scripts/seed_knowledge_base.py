#!/usr/bin/env python3
"""
Seed FAISS knowledge base with starter medical documents.

This script ingests a curated set of medical guidelines, symptoms guides,
drug interaction information, and vital sign reference ranges into the
FAISS vector database so the Clinical Agent can provide evidence-based,
context-aware medical responses.

Usage:
    cd backend
    python scripts/seed_knowledge_base.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.clinical_agent import get_clinical_agent
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Medical Documents Database
# ============================================================================

MEDICAL_DOCUMENTS = [
    # ==== SYMPTOM GUIDES ====
    {
        "content": """
CHEST PAIN: A Clinical Guide

Chest pain is a common presentation in clinical practice. The differential diagnosis
is broad and includes both life-threatening and benign conditions.

CARDIAC CAUSES (LIFE-THREATENING):
- Acute Coronary Syndrome (ACS): Unstable angina, NSTEMI, STEMI
  Characteristics: Substernal pressure, radiates to left arm/jaw, diaphoresis, dyspnea
  Risk factors: Age >40, smoking, diabetes, hypertension, family history
  Management: ECG, troponin, aspirin, anticoagulation, consider PCI

- Pulmonary Embolism: Blood clot in pulmonary arteries
  Characteristics: Pleuritic chest pain, dyspnea, tachycardia, hypoxia
  Risk factors: Immobility, recent surgery, malignancy, hypercoagulable states
  Management: CT pulmonary angiography, anticoagulation

- Aortic Dissection: Tear in aortic wall
  Characteristics: Sudden onset, severe, tearing pain in back, hypertension, pulse differential
  Management: URGENT imaging (CT or TEE), blood pressure control, surgery

PULMONARY CAUSES:
- Pneumonia: Infection of lung parenchyma
  Characteristics: Pleuritic chest pain, fever, cough, dyspnea, consolidation on CXR
  Management: Antibiotics, oxygen, supportive care

- Pleurisy: Inflammation of pleura
  Characteristics: Sharp, pleuritic pain, worse with deep breathing/cough
  Management: NSAIDs, treat underlying cause

GASTROINTESTINAL CAUSES:
- GERD: Acid reflux from stomach
  Characteristics: Burning substernal pain, worse after meals/lying down, responds to antacids
  Management: Proton pump inhibitors, lifestyle modifications

- Esophageal spasm: Uncoordinated contractions
  Characteristics: Substernal chest pain, dysphagia
  Management: Smooth muscle relaxants, treatment of GERD

MUSCULOSKELETAL CAUSES:
- Costochondritis: Inflammation of costal cartilage
  Characteristics: Sharp pain at costochondral junctions, reproducible with palpation
  Management: NSAIDs, rest, physical therapy

RED FLAGS REQUIRING IMMEDIATE EVALUATION:
- Acute onset severe chest pain
- Associated dyspnea, diaphoresis, syncope
- Hemodynamic instability
- ECG changes
- Prior cardiac history
- Risk factors for ACS (age, smoking, diabetes, hypertension)

EMERGENCY CONTACT: Call 911 for severe chest pain, shortness of breath, or loss of consciousness.
        """.strip(),
        "source_type": "text",
        "source_name": "chest_pain_clinical_guide.txt",
        "metadata": {"category": "symptom_guide", "body_system": "cardiovascular"}
    },

    {
        "content": """
HEADACHE: Differential Diagnosis and Management

Headaches are one of the most common chief complaints in clinical practice.

PRIMARY HEADACHES (70% of cases):
- Tension Headache: Most common type (38% of population)
  Characteristics: Bilateral, pressing/tightness, gradual onset, mild-moderate intensity
  Duration: 30 minutes to 7 days
  Associated symptoms: Muscle tension in neck/shoulders
  Triggers: Stress, poor posture, fatigue
  Management: Rest, NSAIDs, stress reduction, physical therapy

- Migraine: Recurrent headaches with neurological symptoms
  Characteristics: Unilateral, throbbing, moderate-severe intensity, 4-72 hours
  Associated symptoms: Nausea, vomiting, photophobia, phonophobia
  Triggers: Hormonal changes, foods (MSG, caffeine), sleep disruption, stress
  Aura: 20% have visual symptoms (flashing lights, zigzag lines) 20-60 minutes before
  Management: Triptans (sumatriptan), NSAIDs, preventive agents (beta-blockers, amitriptyline)

- Cluster Headache: Severe, unilateral orbital pain
  Characteristics: Excruciating intensity, 15-180 minutes duration, 1-8 attacks per day
  Associated symptoms: Lacrimation, nasal congestion, Horner's syndrome
  Pattern: Episodic (weeks-months) with remission periods
  Management: Oxygen, triptans, preventive agents (verapamil)

SECONDARY HEADACHES (RED FLAGS):
- Meningitis: Infection of meninges
  Red flags: High fever, neck stiffness, photophobia, altered mental status, rash
  Management: URGENT - CT if focal neurological signs, lumbar puncture, antibiotics

- Intracranial Hemorrhage (Subdural/Subarachnoid):
  Red flags: Sudden "worst headache of life", focal neurological signs, altered consciousness
  Management: URGENT - CT head, neurosurgical consultation

- Temporal Arteritis (Giant Cell Arteritis):
  Risk: Age >50, ESR elevated, jaw claudication
  Red flags: Vision loss (amaurosis fugax), scalp tenderness
  Management: ESR/CRP, temporal artery biopsy, corticosteroids

- Space-Occupying Lesion (Brain tumor):
  Red flags: Progressive headache, focal neurological signs, vomiting, papilledema
  Management: Imaging (MRI), neurosurgical consultation

WHEN TO SEEK IMMEDIATE CARE:
- Sudden onset severe headache (thunderclap pattern)
- Headache with fever, stiff neck, rash
- Headache with focal neurological symptoms
- Change in pattern of chronic headaches
- Headache after head trauma
- Vision changes or weakness

EVALUATION:
- History: Onset, location, character, duration, frequency, triggers, associated symptoms
- Physical exam: Vital signs, neurological exam, meningeal signs, palpation
- Imaging: CT or MRI only if concerning features present
- Lab: ESR/CRP for temporal arteritis, consider lumbar puncture if meningitis suspected
        """.strip(),
        "source_type": "text",
        "source_name": "headache_differential_diagnosis.txt",
        "metadata": {"category": "symptom_guide", "body_system": "neurological"}
    },

    {
        "content": """
FEVER: Causes, Evaluation, and Management

Fever is defined as body temperature ≥38.0°C (100.4°F).

COMMON INFECTIOUS CAUSES:
- Upper Respiratory Infection (URI): Most common viral infection
  Characteristics: Sore throat, cough, nasal congestion, malaise, fever 38-39°C
  Duration: 3-7 days, usually self-limited
  Management: Supportive care, fluids, antipyretics

- Influenza (Flu): Viral respiratory infection
  Characteristics: Sudden onset fever, myalgia, headache, cough, dyspnea
  Incubation: 1-4 days, contagious 1 day before to 5-7 days after fever onset
  Management: Oseltamivir (Tamiflu) within 48 hours, supportive care, annual vaccine

- Urinary Tract Infection (UTI) / Pyelonephritis:
  Characteristics: Dysuria, frequency, urgency ± flank pain/CVA tenderness
  Urinalysis: Pyuria, bacteriuria, nitrites, leukocyte esterase
  Management: Antibiotics (fluoroquinolone or trimethoprim-sulfamethoxazole)

- Bacterial Pneumonia:
  Characteristics: Fever, cough, dyspnea, pleuritic chest pain, rusty sputum
  CXR: Lobar consolidation, alveolar infiltrates
  Management: Antibiotics based on severity and risk factors

- Gastroenteritis: Viral or bacterial infection of GI tract
  Characteristics: Fever, nausea, vomiting, diarrhea, abdominal cramps
  Management: Fluid/electrolyte replacement, supportive care, antiemetics

NON-INFECTIOUS CAUSES:
- Inflammatory conditions: Rheumatoid arthritis, inflammatory bowel disease
- Malignancy: Lymphoma, leukemia, solid tumors (fever of unknown origin)
- Drug reactions: Antibiotics, NSAIDs, allopurinol
- Autoimmune diseases: Lupus, vasculitis

FEVER OF UNKNOWN ORIGIN (FUO):
Definition: Fever ≥38.3°C for ≥3 weeks without diagnosis despite workup
Causes: Infections (30%), neoplasm (30%), autoimmune (10%), other/unknown (30%)
Workup: CBC, CMP, ESR/CRP, blood cultures, imaging (CT chest/abdomen), consider biopsy

WHEN TO SEEK CARE:
- Fever ≥40°C (104°F)
- High fever with meningeal signs, severe headache, altered mental status
- Fever in infants <3 months
- Fever with immunosuppression
- Fever lasting >5-7 days without improvement
- Fever with confusion, difficulty breathing, severe weakness

FEVER MANAGEMENT:
- Antipyretics: Acetaminophen 650-1000 mg Q4-6H (max 4000 mg/day)
              Ibuprofen 400-600 mg Q4-6H (max 2400 mg/day)
- Hydration: Encourage fluids, oral rehydration solution
- Rest: Allow adequate sleep
- Avoid: Aspirin in children (Reye syndrome risk)
        """.strip(),
        "source_type": "text",
        "source_name": "fever_evaluation_guide.txt",
        "metadata": {"category": "symptom_guide", "body_system": "general"}
    },

    # ==== VITAL SIGNS REFERENCE ====
    {
        "content": """
VITAL SIGNS: Normal Ranges and Clinical Interpretation

HEART RATE (Pulse):
- Normal: 60-100 bpm at rest
- Bradycardia: <60 bpm
  Causes: Athletes, hypothyroidism, beta-blockers, heart block, increased intracranial pressure
  Clinical significance: If symptomatic (dizziness, syncope) or very low (<40), needs evaluation

- Tachycardia: >100 bpm
  Causes: Fever, anxiety, pain, anemia, hyperthyroidism, dehydration, shock, arrhythmias
  Calculation: Rough estimate of fever-induced increase: 10 bpm per 1°C rise in temperature
  Clinical significance: Persistent tachycardia warrants investigation

BLOOD PRESSURE:
- Normal: <120/<80 mmHg
- Elevated: 120-129/<80 mmHg (asymptomatic, lifestyle modifications)
- Hypertension Stage 1: 130-139/80-89 mmHg
- Hypertension Stage 2: ≥140/≥90 mmHg (requires treatment)
- Hypertensive Urgency: SBP ≥180 mmHg without end-organ damage
- Hypertensive Emergency: SBP ≥180 mmHg with end-organ damage (chest pain, vision changes, seizure)

RESPIRATORY RATE:
- Normal: 12-20 breaths per minute
- Tachypnea: >20 breaths/min
  Causes: Fever, pain, anxiety, respiratory disease, metabolic acidosis, sepsis
  Clinical significance: One of earliest signs of deterioration

- Bradypnea: <12 breaths/min
  Causes: CNS depression (drugs, head injury), severe COPD exacerbation
  Clinical significance: Concerning; may indicate respiratory failure

OXYGEN SATURATION (SpO2):
- Normal: ≥95% on room air at sea level
- Mild hypoxia: 90-94% (monitor, supplemental O2 if trending down)
- Moderate hypoxia: 80-89% (requires supplemental oxygen)
- Severe hypoxia: <80% (respiratory emergency)
- NOTE: Pulse oximetry may underestimate hypoxia in severe anemia, carbon monoxide poisoning

TEMPERATURE:
- Normal: 36.5-37.5°C (97.7-99.5°F) oral
  Variations: Lower in morning, higher in evening; lower peripherally than core
- Hypothermia: <36.0°C (96.8°F)
- Fever: ≥38.0°C (100.4°F) oral
- High fever: ≥39.5°C (103.1°F)
- Hyperthermia: >40.5°C (104.9°F) - consider heat stroke

CLINICAL CORRELATIONS:
- Fever + Tachycardia + Tachypnea: Infection, sepsis (assess for infection source)
- Hypertension + Tachycardia: Pain, anxiety, hyperthyroidism, shock
- Hypotension + Tachycardia: Shock (cardiogenic, septic, hypovolemic)
- Bradycardia + Hypotension: Heart block, severe bradycardia, hypothermia
        """.strip(),
        "source_type": "text",
        "source_name": "vital_signs_reference.txt",
        "metadata": {"category": "reference", "body_system": "general"}
    },

    # ==== DRUG INTERACTIONS ====
    {
        "content": """
COMMON DRUG INTERACTIONS: Safety Guidelines

MAJOR INTERACTIONS (Contraindicated Combinations):

1. ACE Inhibitors + Potassium-Sparing Diuretics
   Risk: Severe hyperkalemia
   Examples: Lisinopril + Spironolactone, Enalapril + Triamterene
   Management: Monitor K+ levels monthly; avoid combination if possible

2. Warfarin + NSAIDs
   Risk: Increased bleeding, GI hemorrhage
   Mechanism: NSAIDs displace warfarin from protein binding and inhibit platelet function
   Examples: Warfarin + Ibuprofen, Warfarin + Naproxen
   Management: Use acetaminophen for pain instead; if NSAID necessary, monitor INR closely

3. Macrolide Antibiotics + Statins
   Risk: Severe myopathy, rhabdomyolysis
   Examples: Erythromycin/Clarithromycin + Simvastatin/Lovastatin
   Mechanism: Inhibition of CYP3A4 metabolism
   Management: Use alternative antibiotic (azithromycin safer) or temporarily hold statin

4. SSRIs + Tramadol
   Risk: Serotonin syndrome (agitation, confusion, rapid HR, hyperthermia, muscle rigidity)
   Examples: Sertraline + Tramadol, Paroxetine + Tramadol
   Management: Avoid combination; use alternative analgesic

5. Lithium + NSAIDs
   Risk: Lithium toxicity (tremor, confusion, arrhythmias)
   Mechanism: NSAIDs reduce renal lithium clearance
   Management: Use acetaminophen; if NSAID necessary, increase hydration, monitor lithium levels

MODERATE INTERACTIONS (Monitor/Adjust):

- Beta-blockers + Calcium channel blockers: Risk of bradycardia, AV block
  Management: Monitor heart rate and conduction; may need dose reduction

- SSRIs + Warfarin: Increased bleeding risk (lesser than NSAIDs)
  Management: Monitor INR; may need warfarin dose reduction

- Metformin + Contrast dye: Risk of contrast-induced nephropathy + lactic acidosis
  Management: Hold metformin 48 hours before and after contrast imaging

SUBSTANCE INTERACTIONS:

- Alcohol + Sedatives/Opioids: Profound CNS depression, respiratory depression
  Management: Avoid alcohol completely with these medications

- Grapefruit juice + CYP3A4 substrate drugs: Increased drug levels
  Examples: Grapefruit + Atorvastatin, Simvastatin, Diltiazem
  Management: Avoid grapefruit juice or use alternative medication

SPECIAL POPULATIONS:

Pregnancy:
- ACE inhibitors/ARBs: Contraindicated (teratogenic, especially 2nd/3rd trimester)
- NSAIDs: Avoid, especially 3rd trimester (premature ductus closure)
- Most antibiotics safe: Penicillins, cephalosporins OK; avoid tetracyclines, fluoroquinolones

Breastfeeding:
- Most medications pass into breast milk in small amounts
- Generally compatible: Acetaminophen, penicillins, most SSRIs
- Avoid: Lithium, methotrexate, radioactive iodine

ALWAYS CONSULT PHARMACIST OR PHYSICIAN BEFORE COMBINING MEDICATIONS
        """.strip(),
        "source_type": "text",
        "source_name": "drug_interactions_guide.txt",
        "metadata": {"category": "pharmacology", "body_system": "general"}
    },

    # ==== TRIAGE PROTOCOLS ====
    {
        "content": """
EMERGENCY TRIAGE: Red Flags and Urgency Assessment

ESI (Emergency Severity Index) Scale: 1 (Highest) - 5 (Lowest)

RED FLAGS REQUIRING IMMEDIATE EMERGENCY EVALUATION (ESI-1 or ESI-2):

AIRWAY/BREATHING:
- Severe dyspnea, stridor, difficulty swallowing
- Respiratory distress (use of accessory muscles, RR >30)
- Oxygen saturation <90% on room air
- Acute onset severe chest pain with dyspnea
- Suspected foreign body aspiration

CARDIOVASCULAR:
- Chest pain or pressure with dyspnea, diaphoresis, nausea
- Severe hypertension (SBP >180 with end-organ symptoms)
- Hypotension with altered mental status
- Syncope with ECG abnormality
- Signs of shock (pale, cool, clammy, tachycardic, confused)

NEUROLOGICAL:
- Altered mental status, confusion, disorientation
- Severe headache (thunderclap pattern, worst of life)
- Focal neurological deficits (weakness, speech difficulty, vision loss)
- Seizures (active or post-ictal)
- Severe trauma with head injury

TRAUMA:
- Head injury with altered consciousness
- Unstable vital signs after trauma
- Severe bleeding uncontrolled by pressure
- Penetrating wound to head, chest, or abdomen
- Mechanism suggesting major injury

SEVERE PAIN:
- Acute severe abdominal pain
- Severe extremity pain with limb-threatening injury
- Uncontrolled pain affecting breathing or consciousness

SIGNS OF SEPSIS (Requires Rapid Evaluation):
- Fever + hypotension or altered mental status
- Fever + severe tachycardia (>120) or tachypnea (>20)
- Rash or petechiae with fever

URGENT (ESI-3) - Should be Evaluated Within 30-60 minutes:
- Moderate chest pain (non-acute MI pattern but needs evaluation)
- Fever with focal infectious signs (ear pain, cough, dysuria)
- Moderate to severe pain not affecting airway/breathing
- Significant trauma without life threats
- New neurological symptoms not severe
- Unstable chronic condition exacerbation

NON-URGENT (ESI-4 to ESI-5) - Can Tolerate Waiting:
- Mild pain (minor injuries, muscle strain)
- Common cold symptoms
- Minor rashes without systemic symptoms
- Stable chronic condition management

CALL 911 / GO TO EMERGENCY ROOM FOR:
✓ Severe or worsening shortness of breath
✓ Chest pain or pressure
✓ Severe persistent abdominal or back pain
✓ Serious injury or trauma
✓ Sudden severe headache
✓ Weakness or numbness on one side
✓ Severe allergic reaction
✓ Poisoning or overdose
✓ Inability to speak coherently
✓ Vision loss
✓ Uncontrolled bleeding

COMFORT CARE AT HOME (Appropriate for Non-Urgent):
- Fever: Rest, fluids, acetaminophen/ibuprofen
- Minor pain: Rest, ice/heat, OTC pain relievers
- Mild cough: Fluids, cough drops, humidifier
- Sore throat: Warm fluids, throat lozenges, rest
- Minor cuts: Clean, apply pressure, bandage
        """.strip(),
        "source_type": "text",
        "source_name": "emergency_triage_protocols.txt",
        "metadata": {"category": "triage", "body_system": "general"}
    },

    # ==== GENERAL MEDICAL GUIDELINES ====
    {
        "content": """
GENERAL MEDICAL CARE: Best Practices and Safety

WHEN TO CONTACT YOUR HEALTHCARE PROVIDER:
Same day or next business day:
- New rash without fever
- Mild to moderate pain
- Persistent cough >2 weeks
- Persistent diarrhea >5 days
- Significant constipation >3 days
- Sleep disturbances
- Mood changes
- Questions about medications

Within 1-2 weeks:
- Routine follow-ups
- Prescription refills
- Non-urgent medication side effects
- Questions about diet/exercise

HEALTHY LIFESTYLE RECOMMENDATIONS:
- Exercise: 150 minutes moderate activity or 75 minutes vigorous activity per week
- Sleep: 7-9 hours per night for adults
- Nutrition: Balanced diet with fruits, vegetables, whole grains, lean proteins
- Weight: Maintain BMI 18.5-24.9
- Stress: Regular relaxation, meditation, or counseling if needed
- Avoid: Smoking, excessive alcohol, recreational drugs

MEDICATION SAFETY:
- Always take medications as prescribed
- Don't stop medications without consulting doctor
- Report all side effects
- Keep medication list updated
- Store medications properly (cool, dry place, away from children)
- Discard expired medications at pharmacy

INFECTION PREVENTION:
- Hand hygiene: Wash hands 20 seconds with soap and water
- Respiratory: Cover cough/sneeze with tissue or elbow
- Vaccination: Keep immunizations current
- Antimicrobial use: Take antibiotics as prescribed, complete full course
- Food safety: Cook to proper temperatures, avoid cross-contamination

PREVENTIVE CARE:
Adults 18-39:
- Blood pressure: Check at least every 5 years
- Cholesterol: Screen at least once starting at age 20
- Diabetes: Screen if overweight or other risk factors
- Cancer screening: Discuss with doctor (cervical, colorectal, breast, prostate)

Adults 40-49:
- Blood pressure: Annually
- Cholesterol: Every 1-5 years based on risk
- Diabetes: Screen if overweight or risk factors
- Cancer screening: Age-specific (colonoscopy at 45-50)

Adults 50+:
- Blood pressure: Annually
- Cholesterol: Annually
- Diabetes: Screen annually if risk factors
- Cancer screening: Colorectal (50+), breast (mammogram 40-50+), prostate (50+)

CARDIOVASCULAR RISK REDUCTION:
- Control blood pressure (<130/80)
- Manage cholesterol (LDL <100 mg/dL)
- Regular exercise and weight management
- Mediterranean diet
- Stress reduction
- Smoking cessation
- Limit alcohol
- Manage diabetes if present

DISCLAIMER:
This information is for educational purposes only and should not replace professional
medical advice. Always consult with a healthcare provider for diagnosis, treatment, and
medical decision-making.
        """.strip(),
        "source_type": "text",
        "source_name": "general_medical_guidelines.txt",
        "metadata": {"category": "general", "body_system": "general"}
    },
]


def main():
    """Seed the FAISS knowledge base with medical documents."""
    logger.info("=" * 70)
    logger.info("SEEDING FAISS MEDICAL KNOWLEDGE BASE")
    logger.info("=" * 70)

    try:
        agent = get_clinical_agent()
        total_docs = len(MEDICAL_DOCUMENTS)
        successful = 0
        failed = 0

        for i, doc_data in enumerate(MEDICAL_DOCUMENTS, 1):
            try:
                logger.info(f"\n[{i}/{total_docs}] Ingesting: {doc_data['source_name']}")

                result = agent.ingest_medical_document(
                    content=doc_data["content"],
                    source_type=doc_data["source_type"],
                    source_name=doc_data["source_name"],
                    metadata=doc_data.get("metadata", {})
                )

                if result["success"]:
                    logger.info(f"  ✓ Document ID {result['document_id']}: {result['message']}")
                    successful += 1
                else:
                    logger.error(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
                    failed += 1

            except Exception as e:
                logger.error(f"  ✗ Exception: {str(e)}")
                failed += 1

        # Get final stats
        logger.info("\n" + "=" * 70)
        logger.info("SEEDING COMPLETE")
        logger.info("=" * 70)
        stats = agent.get_knowledge_base_stats()

        logger.info(f"\nResults:")
        logger.info(f"  Documents Ingested: {successful}/{total_docs}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"\nKnowledge Base Stats:")
        logger.info(f"  Total Documents: {stats.get('total_documents', 0)}")
        logger.info(f"  Document Types: {stats.get('document_types', {})}")
        logger.info(f"  Index Size: {stats.get('knowledge_base_size_mb', 0):.2f} MB")

        if stats.get('recent_documents'):
            logger.info(f"\nRecent Documents:")
            for doc in stats['recent_documents'][:5]:
                logger.info(f"  - {doc['name']} ({doc['type']}) - ID {doc['id']}")

        logger.info("\n✓ Knowledge base is ready for use!")
        logger.info("  Try asking the AI about symptoms, medications, or vital signs.")

        return 0 if failed == 0 else 1

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
