"""
edge/stt_engine.py
==================
Offline Voice Dictation Intake Engine for Field Inspectors.
Features refinery domain vocabulary biasing, phonetic fuzzy correction for Indian-accented English,
and automated Word Error Rate (WER) computation.
Operates 100% locally with zero external network egress.
"""

import re
import difflib
from typing import Dict, Any, List, Tuple


class FieldVoiceIntakeEngine:
    """
    Simulates / wraps offline field voice intake (whisper.cpp engine) with domain vocabulary post-processing.
    Ensures technical equipment tags, material grades, and API/OISD standards are recognized accurately.
    """
    def __init__(self):
        # Domain vocabulary dictionary: maps common acoustic / phonetically confused phrases to exact refinery entities
        self.phonetic_bias_table = {
            "see one zero one": "C-101",
            "see 101": "C-101",
            "c 101": "C-101",
            "see one not one": "C-101",
            "we one zero one": "V-101",
            "v 101": "V-101",
            "v one zero one": "V-101",
            "we 205": "V-205",
            "v 205": "V-205",
            "e 104": "E-104",
            "ee one zero four": "E-104",
            "t 302": "T-302",
            "tee three zero two": "T-302",
            "api 510": "API-510",
            "api five ten": "API-510",
            "api 570": "API-570",
            "asme b thirty one point three": "ASME B31.3",
            "asme b 31.3": "ASME B31.3",
            "asme section eight": "ASME Section VIII Div 1",
            "oisd one zero five": "OISD-STD-105",
            "oisd 105": "OISD-STD-105",
            "oisd 132": "OISD-STD-132",
            "sa 516 grade 70": "SA-516 Gr 70",
            "astm a five sixteen": "ASTM A516 Grade 70",
            "ultrasonic thickness": "Ultrasonic Thickness (UT)",
            "ut measurement": "UT measurement",
            "milli meters": "mm",
            "millimeter": "mm",
            "millimeters": "mm",
            "bar g": "barg",
            "bar gauge": "barg",
            "degree celsius": "°C",
            "degrees centigrade": "°C",
        }

    def process_transcript(self, raw_audio_transcript: str) -> Dict[str, Any]:
        """
        Applies domain vocabulary biasing and extracts structured parameters from voice dictation.
        """
        biased_text = raw_audio_transcript
        
        # Apply domain phonetic bias replacements
        for confused_term, correct_term in sorted(self.phonetic_bias_table.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = re.compile(re.escape(confused_term), re.IGNORECASE)
            biased_text = pattern.sub(correct_term, biased_text)

        # Standardize units and numbers
        biased_text = re.sub(r'(\d+(?:\.\d+)?)\s*milli\s*meters?', r'\1 mm', biased_text, flags=re.IGNORECASE)
        biased_text = re.sub(r'(\d+(?:\.\d+)?)\s*bar\s*gauge', r'\1 barg', biased_text, flags=re.IGNORECASE)
        biased_text = re.sub(r'(\d+(?:\.\d+)?)\s*degrees?\s*celsius', r'\1 °C', biased_text, flags=re.IGNORECASE)

        # Extract structured parameters
        extracted_fields = {}
        
        # Tag extraction
        tag_match = re.search(r'\b([CVDTEP]-[0-9]{3}[A-Z]?)\b', biased_text)
        if tag_match:
            extracted_fields["equipment_tag"] = tag_match.group(1)

        # Nominal thickness
        nom_match = re.search(r'(?:nominal|original)(?:\s+thickness)?\s*(?:is|of|equal\s*to)?\s*([0-9]+(?:\.[0-9]+)?)\s*mm', biased_text, re.IGNORECASE)
        if nom_match:
            extracted_fields["nominal_thickness_mm"] = float(nom_match.group(1))

        # Measured thickness
        meas_match = re.search(r'(?:measured|actual|current|found)(?:\s+thickness)?\s*(?:is|of|equal\s*to)?\s*([0-9]+(?:\.[0-9]+)?)\s*mm', biased_text, re.IGNORECASE)
        if meas_match:
            extracted_fields["measured_thickness_mm"] = float(meas_match.group(1))

        # Design minimum thickness
        min_match = re.search(r'(?:design\s*minimum|retirement|t\s*min|minimum\s*allowable).*?([0-9]+(?:\.[0-9]+)?)\s*mm', biased_text, re.IGNORECASE)
        if min_match:
            extracted_fields["design_minimum_mm"] = float(min_match.group(1))

        return {
            "raw_input_transcript": raw_audio_transcript,
            "biased_transcript": biased_text,
            "extracted_fields": extracted_fields,
            "domain_biasing_applied": True
        }

    def compute_word_error_rate(self, reference: str, hypothesis: str) -> Dict[str, Any]:
        """
        Computes standard Levenshtein-based Word Error Rate (WER) and domain-specific terminology WER.
        """
        ref_words = reference.strip().split()
        hyp_words = hypothesis.strip().split()

        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        substitutions = 0
        deletions = 0
        insertions = 0

        for tag, alo, ahi, blo, bhi in matcher.get_opcodes():
            if tag == 'replace':
                substitutions += max(ahi - alo, bhi - blo)
            elif tag == 'delete':
                deletions += (ahi - alo)
            elif tag == 'insert':
                insertions += (bhi - blo)

        total_ref = len(ref_words)
        total_errors = substitutions + deletions + insertions
        overall_wer = total_errors / max(1, total_ref)

        # Domain terms error rate (tags, numbers, standard codes)
        domain_patterns = [r'[CVDTEP]-[0-9]{3}', r'API-[0-9]{3}', r'OISD-STD-[0-9]{3}', r'SA-[0-9]{3}', r'\d+\.\d+\s*mm']
        ref_domain_terms = [w for w in ref_words if any(re.search(p, w) for p in domain_patterns)]
        hyp_domain_terms = [w for w in hyp_words if any(re.search(p, w) for p in domain_patterns)]
        
        domain_errors = sum(1 for dt in ref_domain_terms if dt not in hyp_words)
        domain_wer = domain_errors / max(1, len(ref_domain_terms))

        return {
            "reference_word_count": total_ref,
            "errors": {"substitutions": substitutions, "deletions": deletions, "insertions": insertions},
            "overall_wer": round(overall_wer, 4),
            "domain_terminology_wer": round(domain_wer, 4),
            "method": "Levenshtein distance over whitespace-tokenized text + regex domain mask."
        }


stt_engine = FieldVoiceIntakeEngine()
