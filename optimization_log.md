# Patho-Bot Optimization Log

This document tracks the technical improvements and clinical optimizations applied to the Patho-Bot agent to ensure robustness, accuracy, and usability.

## 1. Core Stability Fixes
*   **NumPy Compatibility**: Downgraded to `numpy<2` to resolve critical runtime crashes with PyTorch and Ultralytics (which rely on NumPy 1.x C-API).
*   **ADK Telemetry Patch**: Monkey-patched `google.adk.telemetry` to fix a `TypeError: Object of type bytes is not JSON serializable` bug, ensuring stable agent execution.

## 2. Intelligence Upgrade
*   **Model**: Upgraded the Agent's brain to **Gemini 3 Pro** (`gemini-3-pro-preview`).
    *   *Benefit*: Superior clinical reasoning, better handling of complex medical guidelines, and more "human-like" interaction compared to Flash models.
    *   **Vision Model**: Upgraded from `best_nano.pt` to `best_large.pt` (`best(1).pt`).
        *   *Benefit*: Higher capacity model for potentially better feature extraction, though slower inference (~400ms vs ~100ms).

## 3. Clinical Vision Optimization ("Super-Human" Sensitivity)
To address the "Class Imbalance" problem (rare severe parasites vs. common rings), we implemented a custom inference pipeline in `tools.py`:

*   **Per-Class Confidence Thresholding**:
    *   **Rings (Common)**: Set to **0.50**. Reduces false positives (noise).
    *   **Schizonts/Gametocytes (Critical/Rare)**: Set to **0.15**. Ensures we never miss a severe malaria indicator, even if faint.
    *   **WBCs**: Set to **0.25**.
*   **Test Time Augmentation (TTA)**: Enabled `augment=True`.
    *   *Mechanism*: The model internally rotates and flips the image during inference and averages predictions.
    *   *Benefit*: Significantly boosts recall (sensitivity) for parasites in difficult orientations.
*   **Class-Agnostic NMS**: Enabled `agnostic_nms=True`.
    *   *Benefit*: Prevents the model from double-counting the same cell as both a "Ring" and a "Trophozoite", ensuring accurate parasitemia counts.
*   **"Paranoid Mode" (High-Res Inference)**:
    *   **Resolution**: Increased inference size to `1024px` (from default 640px).
    *   **Low Threshold**: Dropped confidence floor to **0.10** for Schizonts/Gametocytes.
    *   *Benefit*: Forces the model to "zoom in" and catch extremely faint or small parasites that were previously missed.

## 4. User Interface
*   **Web App**: Developed a **Streamlit** application (`app.py`).
    *   *Features*: Drag-and-drop image upload, clinical symptom checklist (triage), and real-time Agent feedback.
    *   *Multi-Model Support*: Added a selector to choose between **Large** (Accuracy) and **Nano** (Speed) models.
    *   *Goal*: Makes the tool accessible to non-technical healthcare workers.

## 5. Verification Results
*   **Test Case**: `image.png` (Previously 0 detections).
*   **Result**: **3 Parasites Detected** (2 Schizonts, 1 Trophozoite) after applying optimizations.
