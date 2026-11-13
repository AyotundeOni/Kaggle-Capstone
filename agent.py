import os
import sys
import logging
from typing import Optional

if "GOOGLE_API_KEY" not in os.environ:
    raise SystemExit("Set the GOOGLE_API_KEY environment variable before running.")

# Monkey-patch telemetry to avoid JSON serialization error with bytes
# MUST be done before importing other ADK components
import google.adk.telemetry
def dummy_trace(*args, **kwargs):
    pass
google.adk.telemetry.trace_call_llm = dummy_trace

# Also patch the module that imports it directly
try:
    import google.adk.flows.llm_flows.base_llm_flow
    google.adk.flows.llm_flows.base_llm_flow.trace_call_llm = dummy_trace
except ImportError:
    pass

# Import ADK components
from google.adk import Agent
from google.adk.models import Gemini
from google.adk.tools import FunctionTool
from google.adk.runners import InMemoryRunner

# Import our custom tools
from tools import analyze_blood_smear, calculate_parasitemia, retrieve_who_guidelines

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_patho_bot():
    # 1. Define Tools
    # We wrap our python functions as ADK FunctionTools
    vision_tool = FunctionTool(func=analyze_blood_smear)
    calc_tool = FunctionTool(func=calculate_parasitemia)
    rag_tool = FunctionTool(func=retrieve_who_guidelines)
    
    tools = [vision_tool, calc_tool, rag_tool]
    
    # 2. Define Model
    # Try Gemini 2.5 Flash-Lite, fallback to 1.5 Flash for stability in Cloud Regions
    try:
        model = Gemini(model="gemini-2.5-flash-lite")
    except Exception:
        try:
            model = Gemini(model_name="gemini-2.5-flash-lite")
        except Exception:
            # Fallback to standard Flash if 2.5 is unavailable in this region
            print("WARNING: Gemini 2.5 unavailable. Falling back to 1.5 Flash.")
            model = Gemini(model="gemini-1.5-flash")
    
    # 3. Define System Prompt (The "Brain" & "Persona")
    system_prompt = """
    You are Patho-Bot, an expert AI Pathologist and Malaria Specialist.
    Your mission is to provide expert-level malaria quantification and treatment advice in rural/underserved areas.
    
    You have three internal roles (Orchestrator Pattern):
    1. **Triage Nurse**: Interact with the user, ask for symptoms, and request a blood smear image if malaria is suspected.
    2. **Specialist Pathologist**: When an image path is provided, use the `analyze_blood_smear` tool to detect parasites. Then, ALWAYS use the `calculate_parasitemia` tool to determine severity.
    3. **Pharmacist/Doctor**: Based on the severity and patient details (age/weight), use `retrieve_who_guidelines` to recommend the exact WHO-approved treatment (Drug, Dosage, Duration).
    
    **CRITICAL RULES**:
    - **Severity Check**: If `calculate_parasitemia` returns "Severe" or "Hyperparasitemia" (or > 100,000 parasites/µL), you must SCREAM (use uppercase/bold) "SEVERE MALARIA - REFER IMMEDIATELY" and recommend Injectable Artesunate.
    - **Context**: Remember the patient's age and weight if mentioned.
    - **Tone**: Be empathetic, professional, and authoritative (like a Senior Doctor).
    - **Math**: NEVER guess the parasitemia. ALWAYS use the tool.
    
    Start by introducing yourself and asking how you can help.
    """
    
    # 4. Create Agent
    # We use InMemorySessionService for this demo.
    # Note: Agent class uses 'instruction' for the prompt and requires a 'name'.
    # Session service is likely used during execution or configured differently.
    
    # Create the Agent
    agent = Agent(
        name="patho_bot",
        model=model,
        tools=tools,
        instruction=system_prompt
    )
    
    return agent

# Dummy classes for ADK types if imports are tricky
class Part:
    def __init__(self, text=None):
        self.text = text

class Content:
    def __init__(self, role, parts):
        self.role = role
        self.parts = parts

def main():
    print("Initializing Patho-Bot...")
    try:
        agent = create_patho_bot()
        runner = InMemoryRunner(agent=agent, app_name="PathoBotApp")
        session_id = "user_session_001" # Static session for demo
        
        # Create the session explicitly
        runner.session_service.create_session(
            session_id=session_id,
            app_name="PathoBotApp",
            user_id="user_123"
        )
        
        print("\nPatho-Bot is ready! (Type 'quit' to exit)")
        print("You can test with image: /Users/ayotunde/Kaggle Capstone/01b99da8-b66b-464b-a7ee-1cadab8db18b.png")
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit']:
                break
                
            # Run the agent
            try:
                # runner.run returns a generator of events
                # new_message must be a Content object
                new_message = Content(role='user', parts=[Part(text=user_input)])
                
                events = runner.run(
                    user_id="user_123",
                    session_id=session_id,
                    new_message=new_message
                )
                
                for event in events:
                    # We print relevant events. 
                    # Assuming event has a type or we can inspect it.
                    # For now, we print the string representation if it looks like a message.
                    # Or we check for 'ModelResponse' or similar.
                    # Let's print the event to debug/see output.
                    # In a real app, we'd filter for the final text response.
                    
                    # Hacky check for text content
                    if hasattr(event, 'text') and event.text:
                         print(f"Patho-Bot: {event.text}")
                    elif hasattr(event, 'content') and event.content:
                         print(f"Patho-Bot: {event.content}")
                    else:
                        # Debug: print(f"[Event: {type(event).__name__}]")
                        pass
                        
            except Exception as e:
                logger.error(f"Error during agent execution: {e}")
                print(f"\nPatho-Bot: I encountered an error: {e}")
                
    except Exception as e:
        logger.critical(f"Failed to initialize agent: {e}")
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    main()
