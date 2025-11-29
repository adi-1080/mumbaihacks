import re
from typing import Dict, Tuple
from datetime import datetime

class SymptomAnalyzer:
    def __init__(self):
        # Define symptom categories and their expected consultation times
        self.symptom_categories = {
            "routine_checkup": {
                "keywords": ["checkup", "routine", "physical", "annual", "preventive"],
                "base_time_mins": 12,
                "urgency": 1
            },
            "minor_illness": {
                "keywords": ["fever", "cold", "cough", "headache", "sore throat", "runny nose", "sneezing"],
                "base_time_mins": 8,
                "urgency": 2
            },
            "digestive_issues": {
                "keywords": ["stomach", "nausea", "vomiting", "diarrhea", "constipation", "indigestion"],
                "base_time_mins": 15,
                "urgency": 3
            },
            "pain_management": {
                "keywords": ["pain", "ache", "joint", "back", "muscle", "arthritis", "injury"],
                "base_time_mins": 18,
                "urgency": 4
            },
            "skin_conditions": {
                "keywords": ["rash", "itching", "skin", "allergy", "eczema", "acne"],
                "base_time_mins": 13,
                "urgency": 2
            },
            "respiratory": {
                "keywords": ["breathing", "asthma", "shortness", "chest", "wheezing"],
                "base_time_mins": 20,
                "urgency": 6
            },
            "serious_symptoms": {
                "keywords": ["severe", "intense", "unbearable", "chronic", "persistent", "blood"],
                "base_time_mins": 25,
                "urgency": 8
            },
            "emergency": {
                "keywords": ["emergency", "urgent", "critical", "severe pain", "heart", "stroke", "accident"],
                "base_time_mins": 30,
                "urgency": 10
            }
        }
    
    def analyze_symptoms(self, symptoms: str) -> Dict:
        """
        Analyze patient symptoms to predict consultation time and urgency.
        
        Args:
            symptoms: Patient's symptom description
            
        Returns:
            Dictionary with analysis results
        """
        symptoms_lower = symptoms.lower()
        
        # Find matching categories
        matches = []
        for category, data in self.symptom_categories.items():
            for keyword in data["keywords"]:
                if keyword in symptoms_lower:
                    matches.append((category, data))
                    break
        
        if not matches:
            # Default for unclassified symptoms
            category_name = "general_consultation"
            estimated_time = 15
            urgency_score = 3
        else:
            # Use the highest urgency match
            matches.sort(key=lambda x: x[1]["urgency"], reverse=True)
            category_name = matches[0][0]
            estimated_time = matches[0][1]["base_time_mins"]
            urgency_score = matches[0][1]["urgency"]
        
        # Apply modifiers based on symptom complexity
        complexity_factor = self._assess_complexity(symptoms_lower)
        estimated_time = int(estimated_time * complexity_factor)
        
        return {
            "category": category_name,
            "estimated_consultation_mins": estimated_time,
            "urgency_score": urgency_score,  # 1-10 scale
            "is_emergency": urgency_score >= 9,
            "complexity_factor": complexity_factor,
            "matched_symptoms": [m[0] for m in matches]
        }
    
    def _assess_complexity(self, symptoms: str) -> float:
        """Assess symptom complexity to adjust consultation time"""
        complexity_indicators = [
            "multiple", "several", "chronic", "persistent", "recurring",
            "severe", "intense", "unbearable", "worsening", "complicated"
        ]
        
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in symptoms)
        
        if complexity_count == 0:
            return 1.0  # Normal complexity
        elif complexity_count <= 2:
            return 1.3  # Moderate complexity
        else:
            return 1.6  # High complexity

# Global analyzer instance
symptom_analyzer = SymptomAnalyzer()

def analyze_patient_symptoms(symptoms: str) -> Dict:
    """
    Wrapper function for symptom analysis.
    
    Args:
        symptoms: Patient's symptom description
        
    Returns:
        Analysis results with consultation time prediction
    """
    print(f"[TOOL] [Symptom Analyzer] Analyzing: '{symptoms}'")
    
    analysis = symptom_analyzer.analyze_symptoms(symptoms)
    
    print(f"[OK] [Symptom Analyzer] Category: {analysis['category']}, "
          f"Time: {analysis['estimated_consultation_mins']}min, "
          f"Urgency: {analysis['urgency_score']}/10")
    
    return analysis

def get_consultation_time_estimate(symptoms: str) -> int:
    """
    Get estimated consultation time based on symptoms.
    
    Args:
        symptoms: Patient's symptom description
        
    Returns:
        Estimated consultation time in minutes
    """
    analysis = analyze_patient_symptoms(symptoms)
    return analysis['estimated_consultation_mins']

def check_emergency_status(symptoms: str) -> Tuple[bool, int]:
    """
    Check if symptoms indicate an emergency.
    
    Returns:
        Tuple of (is_emergency, urgency_score)
    """
    analysis = analyze_patient_symptoms(symptoms)
    return analysis['is_emergency'], analysis['urgency_score']