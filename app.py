import streamlit as st
import os
import tempfile
from PIL import Image
import asyncio
from datetime import datetime

# Import our Agent and DB
from agent import create_patho_bot, Part, Content
from google.adk.runners import InMemoryRunner
# Switch to Firestore for Cloud Deployment
import patient_db_firestore as patient_db

# Page Config
st.set_page_config(
    page_title="Patho-Bot: AI Malaria Pathologist",
    page_icon="🔬",
    layout="wide"
)

# Initialize Agent Runner (Force Refresh for Debugging)
# if 'runner' not in st.session_state:
agent = create_patho_bot()
st.session_state['runner'] = InMemoryRunner(agent=agent, app_name="PathoBotApp")
runner = st.session_state['runner']

# --- UI Styling & Animations ---
def inject_custom_css():
    st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
            font-family: 'Helvetica Neue', sans-serif;
        }
        .stButton>button {
            width: 100%;
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .stButton>button:hover {
            transform: scale(1.02);
            background-color: #45a049;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .fade-in {
            animation: fadeIn 1.5s;
        }
        @keyframes fadeIn {
            0% { opacity: 0; }
            100% { opacity: 1; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# Title and Intro
st.markdown('<div class="fade-in"><h1>🔬 Patho-Bot: The Low-Resource AI Pathologist</h1></div>', unsafe_allow_html=True)
st.markdown("""
**Mission**: To provide expert-level malaria quantification and treatment advice in rural/underserved areas using edge-optimized AI.
""")
st.markdown("---")

# --- Step 1: Patient Login (Compulsory) ---
st.sidebar.header("1. Patient Identification")
username = st.sidebar.text_input("Patient ID / Username", placeholder="Required to proceed")

current_patient = None
default_age = 25
default_weight = 60

if not username:
    st.info("👋 **Welcome!** Please enter a **Patient ID** in the sidebar to begin triage.")
    st.stop()  # Stop execution here until username is provided

# Initialize Session for this Patient (Required for both new and existing)
session_id = f"session_{username}"

# Ensure session exists
# We use the robust try-create pattern later, but we can try to ensure it here too
# or just rely on the lazy creation in the run loop. 
# For now, let's just define the variables so they are available.
try:
    runner.session_service.create_session(
        session_id=session_id,
        app_name="PathoBotApp",
        user_id=username
    )
except Exception:
    pass # It might already exist, or we handle it later

# Load Profile if exists
current_patient = patient_db.get_patient(username)
if current_patient:
    st.sidebar.success(f"✅ Profile Loaded: {username}")
    default_age = current_patient.get("age", 25)
    default_weight = current_patient.get("weight", 60)
else:
    st.sidebar.info("🆕 New Patient Profile")

# History Summary (Animated)
if current_patient and "history" in current_patient and current_patient["history"]:
    with st.sidebar.expander("📜 Patient History", expanded=True):
        summary_key = f"summary_{username}_{len(current_patient['history'])}"
        if summary_key not in st.session_state:
            with st.spinner("Summarizing history..."):
                history_text = "\n".join(current_patient["history"])
                summary_prompt = (
                    f"System Update: Patient '{username}' loaded.\n"
                    f"Past Medical History Records:\n{history_text}\n\n"
                    f"INSTRUCTION: Provide an ULTRA-SUMMARIZED (max 2 sentences) clinical summary."
                )
                msg = Content(role='user', parts=[Part(text=summary_prompt)])
                events = runner.run(user_id=username, session_id=session_id, new_message=msg)
                summary_text = ""
                for event in events:
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts'):
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    summary_text += part.text
                        elif hasattr(event.content, 'text') and event.content.text:
                             summary_text += event.content.text
                st.session_state[summary_key] = summary_text
        st.info(st.session_state[summary_key])

# --- Step 2: Demographics (Compulsory) ---
st.sidebar.header("2. Demographics")
patient_age = st.sidebar.number_input("Age (Years) *", min_value=0, max_value=120, value=default_age)
patient_weight = st.sidebar.number_input("Weight (kg)", min_value=0, max_value=200, value=default_weight)

if patient_age == 0:
    st.warning("⚠️ Please enter a valid **Age** in the sidebar to proceed.")
    st.stop()

# --- Step 3: Symptoms (Compulsory) ---
st.sidebar.header("3. Symptoms")
st.sidebar.markdown("*Select at least one*")

with st.sidebar.expander("Uncomplicated Signs", expanded=True):
    symptoms_uncomplicated = []
    if st.checkbox("Fever"): symptoms_uncomplicated.append("Fever")
    if st.checkbox("Headache"): symptoms_uncomplicated.append("Headache")
    if st.checkbox("Chills/Sweats"): symptoms_uncomplicated.append("Chills/Sweats")
    if st.checkbox("Muscle/Joint Pain"): symptoms_uncomplicated.append("Muscle/Joint Pain")
    if st.checkbox("Nausea/Vomiting"): symptoms_uncomplicated.append("Nausea/Vomiting")

with st.sidebar.expander("Severe Signs (Red Flags)", expanded=False):
    symptoms_severe = []
    if st.checkbox("Impaired Consciousness"): symptoms_severe.append("Impaired Consciousness")
    if st.checkbox("Prostration"): symptoms_severe.append("Prostration")
    if st.checkbox("Convulsions"): symptoms_severe.append("Multiple Convulsions")
    if st.checkbox("Deep Breathing"): symptoms_severe.append("Deep Breathing")
    if st.checkbox("Jaundice"): symptoms_severe.append("Jaundice")
    if st.checkbox("Dark Urine"): symptoms_severe.append("Dark Urine")
    if st.checkbox("Severe Bleeding"): symptoms_severe.append("Severe Bleeding")

all_symptoms = symptoms_uncomplicated + symptoms_severe
if not all_symptoms:
    st.warning("⚠️ Please select at least one **Symptom** in the sidebar to proceed.")
    st.stop()

# Save Profile Button (Optional update)
if st.sidebar.button("Update Profile"):
    patient_db.save_patient(username, patient_age, patient_weight)
    st.sidebar.success("Saved!")

# --- Step 4: AI Settings & Upload ---
st.sidebar.markdown("---")
st.sidebar.subheader("AI Settings")
model_choice = st.sidebar.radio("Vision Model", ["Large (Accurate)", "Nano (Fast)"])
selected_model = "Large" if "Large" in model_choice else "Nano"
debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)

# Main Area
st.markdown(f"### 🏥 Case: {username} ({patient_age}y, {patient_weight}kg)")
st.markdown(f"**Symptoms**: {', '.join(all_symptoms)}")

st.header("4. Upload Blood Smear")
uploaded_file = st.file_uploader("Drop a microscopy image here...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])
    with col1:
        image = Image.open(uploaded_file)
        st.image(image, caption='Uploaded Slide', use_container_width=True)
    
    with col2:
        st.info("Ready for Analysis")
        if st.button("🚀 Analyze Case Now"):
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                image.save(tmp_file.name)
                tmp_file_path = tmp_file.name

            with st.spinner('🤖 Patho-Bot is analyzing...'):
                try:
                    # Construct Prompt
                    symptom_text = f"Uncomplicated: {', '.join(symptoms_uncomplicated)}. " if symptoms_uncomplicated else ""
                    symptom_text += f"Severe: {', '.join(symptoms_severe)}." if symptoms_severe else ""
                    
                    user_prompt = (
                        f"Patient Details: Age {patient_age}, Weight {patient_weight}kg.\n"
                        f"Reported Symptoms: {symptom_text}\n"
                        f"Please analyze this image: {tmp_file_path}\n"
                        f"IMPORTANT: Use the '{selected_model}' model for analysis."
                    )
                    
                    # 4. Run Agent
                    # Create Content object
                    new_message = Content(role='user', parts=[Part(text=user_prompt)])
                    
                    try:
                        events = runner.run(
                            user_id=username,
                            session_id=session_id,
                            new_message=new_message
                        )
                    except ValueError as e:
                        # Handle "Session not found" by creating it and retrying
                        # st.warning(f"Session expired or missing. Re-creating... ({e})") # Optional debug
                        runner.session_service.create_session(
                            session_id=session_id,
                            app_name="PathoBotApp",
                            user_id=username
                        )
                        # Retry run
                        events = runner.run(
                            user_id=username,
                            session_id=session_id,
                            new_message=new_message
                        )
                
                    # Collect response
                    full_response = ""
                    for event in events:
                        if debug_mode:
                            st.write(f"DEBUG Event Type: {type(event)}")
                            st.write(event)
                            
                        # 1. Direct Text (Common)
                        if hasattr(event, 'text') and event.text:
                            full_response += event.text
                        
                        # 2. Content Object (Structured)
                        elif hasattr(event, 'content') and event.content:
                            if hasattr(event.content, 'parts'):
                                for part in event.content.parts:
                                    # Check for text attribute
                                    if hasattr(part, 'text') and part.text:
                                        full_response += part.text
                                    # Fallback for dict (if applicable)
                                    elif isinstance(part, dict) and 'text' in part:
                                        full_response += part['text']
                                    # Fallback for string parts
                                    elif isinstance(part, str):
                                        full_response += part
                            elif hasattr(event.content, 'text') and event.content.text:
                                 full_response += event.content.text
                    
                    if not full_response:
                        event_types = [type(e).__name__ for e in events] if 'events' in locals() else []
                        st.warning(f"⚠️ No text response received from Agent. (Events seen: {event_types})")
                        if debug_mode:
                            st.write("DEBUG: Event loop finished but full_response is empty.")
                    
                    # Display Results
                    st.success("Analysis Complete")
                    st.markdown("### 🩺 Diagnosis & Plan")
                    st.markdown(full_response)
                    
                    # Save to History (Timestamped & Contextualized)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    history_entry = (
                        f"--- CLINICAL ENCOUNTER: {timestamp} ---\n"
                        f"Patient presented with: {', '.join(all_symptoms)}.\n"
                        f"AI Diagnosis:\n{full_response}"
                    )
                    patient_db.add_history(username, history_entry)
                    patient_db.save_patient(username, patient_age, patient_weight)
                    
                    # Cleanup
                    os.remove(tmp_file_path)
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.exception(e)
