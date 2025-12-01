from google.cloud import firestore
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firestore Client
# This works automatically in Cloud Run.
# Locally, run: gcloud auth application-default login
try:
    db = firestore.Client()
    logger.info("Firestore Client Initialized Successfully")
except Exception as e:
    db = None
    logger.warning(f"Firestore Connection Failed: {e}. Database features will not work.")

COLLECTION_NAME = "patients"

def get_patient(username):
    """Retrieves patient data from Firestore."""
    if not db: 
        return {}
    
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(username)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return {}
    except Exception as e:
        logger.error(f"Error getting patient {username}: {e}")
        return {}

def save_patient(username, age, weight):
    """Saves or updates patient demographics."""
    if not db: return

    try:
        doc_ref = db.collection(COLLECTION_NAME).document(username)
        # Use merge=True to update fields without overwriting the whole document (preserving history)
        doc_ref.set({
            "age": age,
            "weight": weight
        }, merge=True)
        logger.info(f"Saved patient {username}")
    except Exception as e:
        logger.error(f"Error saving patient {username}: {e}")

def add_history(username, diagnosis_entry):
    """Appends a diagnosis entry to the patient's history."""
    if not db: return

    try:
        doc_ref = db.collection(COLLECTION_NAME).document(username)
        # Check if doc exists to decide between set or update
        # Actually, set(..., merge=True) with ArrayUnion works for both creation and update
        doc_ref.set({
            "history": firestore.ArrayUnion([diagnosis_entry])
        }, merge=True)
        logger.info(f"Added history for {username}")
    except Exception as e:
        logger.error(f"Error adding history for {username}: {e}")
