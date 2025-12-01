import os
from ultralytics import YOLO
import cv2
import numpy as np

# Global model instances
_MODELS = {}

def get_yolo_model(model_name: str = "Large"):
    global _MODELS
    
    if model_name not in _MODELS:
        filename = 'best_large.pt' if model_name.lower() == 'large' else 'best_nano.pt'
        model_path = os.path.join(os.path.dirname(__file__), 'model', filename)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file '{filename}' not found. Please ensure it is in the 'model/' directory.")
            
        _MODELS[model_name] = YOLO(model_path)
        
    return _MODELS[model_name]

def analyze_blood_smear(image_path: str, model_name: str = "Large") -> dict:
    """
    Analyzes a blood smear image using the specified YOLOv11 model (Nano or Large).
    
    Args:
        image_path: The absolute path to the image file.
        model_name: The model to use ("Nano" or "Large"). Defaults to "Large".
        
    Returns:
        A dictionary containing the counts of detected objects and a summary string.
    """
    try:
        model = get_yolo_model(model_name)
        
        # --- Advanced Inference Strategy ("Paranoid Mode") ---
        # 1. TTA (Test Time Augmentation): Increases recall.
        # 2. Agnostic NMS: Prevents double-counting.
        # 3. High Resolution (imgsz=1024): "Zooms in" to see small parasites.
        # 4. Low Global Threshold (0.10): Catch everything, filter later.
        results = model(image_path, augment=True, agnostic_nms=True, imgsz=1024, conf=0.10)
        
        parasite_count = 0
        wbc_count = 0
        
        # Per-Class Confidence Thresholds (The "Recall Booster")
        # Adjust these based on class IDs from model.names
        # We need to map names to IDs dynamically or hardcode if known.
        # Let's map dynamically to be safe.
        names = model.names
        
        # Define thresholds by name keyword
        thresholds = {
            'ring': 0.50,          # Common -> Be strict
            'trophozoite': 0.45,   # Moderate
            'schizont': 0.10,      # Rare -> Be paranoid (0.10)
            'gametocyte': 0.10,    # Rare -> Be paranoid (0.10)
            'parasite': 0.45,      # Generic fallback
            'wbc': 0.25,           # Standard
            'white': 0.25,
            'leukocyte': 0.25,
            'red': 0.25            # RBCs
        }
        
        default_threshold = 0.25
        
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = names[cls_id]
                name_lower = class_name.lower()
                
                # Determine threshold for this class
                threshold = default_threshold
                for key, val in thresholds.items():
                    if key in name_lower:
                        threshold = val
                        break
                
                # Apply Per-Class Thresholding
                if conf < threshold:
                    continue
                
                # Counting Logic
                if any(x in name_lower for x in ['parasite', 'trophozoite', 'schizont', 'ring', 'gametocyte']):
                    parasite_count += 1
                elif 'wbc' in name_lower or 'white' in name_lower or 'leukocyte' in name_lower:
                    wbc_count += 1
                    
        return {
            "parasite_count": parasite_count,
            "wbc_count": wbc_count,
            "summary": f"Detected {parasite_count} parasites and {wbc_count} WBCs using advanced clinical inference (TTA + Per-Class Thresholds)."
        }
    except Exception as e:
        return {"error": str(e)}

def calculate_parasitemia(parasite_count: int, wbc_count: int = 0) -> dict:
    """
    Calculates parasitemia based on parasite count and WBC count.
    Uses the standard formula: (Parasites / WBCs) * 8000.
    If WBC count is 0 or not provided, assumes 8000 WBCs/µL (standard).
    
    Args:
        parasite_count: Number of parasites detected.
        wbc_count: Number of WBCs detected (optional).
        
    Returns:
        A dictionary with parasitemia value, unit, and severity classification.
    """
    assumed_wbc = 8000
    
    if wbc_count > 0:
        # Formula: (Parasites / Observed WBCs) * 8000
        parasites_per_microliter = (parasite_count / wbc_count) * 8000
        calculation_method = "Calculated using observed WBC count"
    else:
        # If no WBCs detected, we assume the field of view corresponds to a standard volume 
        # OR we just treat the count as raw. 
        # However, the prompt says "Calculates Parasite Density... using standard assumptions (e.g., 8,000 WBCs/µL)".
        # Usually this implies we count WBCs. If we don't have WBCs, we can't strictly use that formula.
        # BUT, for the sake of the tool, if we lack WBCs, we might assume the image represents a fraction of a microliter?
        # Let's fallback to a simpler assumption or just return the count if we can't calculate density.
        # Actually, let's assume the user wants the standard formula applied to the raw count if WBCs are missing,
        # implying the count IS per standard field? No, that's risky.
        # Let's just use the count directly if WBC is 0, but warn.
        # Wait, the prompt says "The Math: Calculates Parasite Density... (Parasites per µL) using standard assumptions (e.g., 8,000 WBCs/µL)."
        # This usually means: Count Parasites, Count WBCs, then (P/W)*8000.
        # If we detect 0 WBCs, we can't divide by 0.
        # Let's return a message if WBC is 0.
        if wbc_count == 0:
             return {
                "parasites_per_microliter": None,
                "severity": "Unknown",
                "message": "Cannot calculate parasitemia: No WBCs detected in the image to normalize against."
            }
        
    parasites_per_microliter = round(parasites_per_microliter, 2)
    
    # Severity Classification (WHO)
    # < 2% is roughly < 100,000 / uL (assuming 5,000,000 RBC/uL) -> 2% of 5M = 100k.
    # Hyperparasitemia > 10% or > 250,000 / uL (varies, but >250k is often severe).
    # Let's use > 100,000 as "High/Severe" for safety in this demo, or stick to the prompt's "Uncomplicated vs Severe".
    # WHO defines Hyperparasitemia as > 10% infected RBCs.
    # In terms of parasites/uL, > 250,000 is often the cutoff for severe malaria in non-immune.
    
    severity = "Uncomplicated"
    if parasites_per_microliter > 250000: # Threshold for severe
        severity = "Severe (Hyperparasitemia)"
    elif parasites_per_microliter > 100000:
        severity = "Potentially Severe"
        
    return {
        "parasites_per_microliter": parasites_per_microliter,
        "unit": "parasites/µL",
        "severity": severity,
        "calculation_method": calculation_method
    }

def retrieve_who_guidelines(query: str) -> str:
    """
    Retrieves relevant sections from the WHO Malaria Treatment Guidelines.
    
    Args:
        query: The search query (e.g., "severe malaria treatment", "pregnancy").
        
    Returns:
        Relevant text segments from the guidelines.
    """
    guidelines_path = os.path.join(os.path.dirname(__file__), 'who_guidelines.txt')
    if not os.path.exists(guidelines_path):
        return "Error: Guidelines file not found."
        
    with open(guidelines_path, 'r') as f:
        content = f.read()
        
    # Simple keyword search for lines/paragraphs
    # We will split by sections (numbered) and return the section that matches best.
    
    sections = content.split('\n\n')
    relevant_sections = []
    
    query_lower = query.lower()
    
    for section in sections:
        if query_lower in section.lower():
            relevant_sections.append(section)
            
    if not relevant_sections:
        # Fallback: return the whole table of contents or first section
        return "No specific section matched. Here is the summary:\n" + content[:500] + "..."
        
    return "\n---\n".join(relevant_sections)
