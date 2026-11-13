# Patho-Bot: The Low-Resource AI Pathologist

## Project Identity
**Track**: Agents for Good (Healthcare)
**Mission**: To provide expert-level malaria quantification and treatment advice in rural/underserved areas using edge-optimized AI.

## Architecture
1.  **The Model**: Fine-tuned YOLOv11 Nano (`model/best_nano.pt`) for parasite detection.
2.  **The Vision Tool**: Wraps the model to count parasites and WBCs.
3.  **The Clinical Agent**: Powered by Google Gemini (via ADK), acting as a WHO-trained Pathologist.
4.  **The Report Writer**: Formats diagnoses and referrals.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo_url>
    cd Patho-Bot
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup API Key**:
    Ensure you have a Google Gen AI API Key.
    Export it as an environment variable: `export GOOGLE_API_KEY=...` (never commit it).

4.  **Run the Agent**:
    ```bash
    python agent.py
    ```

## Usage
- Start the agent.
- Describe symptoms or upload a blood smear image path.
- The agent will analyze the image, calculate parasitemia, and recommend treatment based on WHO guidelines.

## Directory Structure
- `agent.py`: Main application logic (ADK Agent).
- `tools.py`: Custom tools (Vision, Calculator, RAG).
- `model/`: Contains the YOLO model (`best_nano.pt`).
- `who_guidelines.txt`: Local knowledge base for RAG.
- `requirements.txt`: Project dependencies.

## Technical Highlights
- **On-Device Efficiency**: Uses YOLOv11 Nano for fast inference.
- **Agentic Workflow**: Orchestrates Vision, Math, and Retrieval tools.
- **RAG**: Retrieves exact dosage from WHO guidelines.
