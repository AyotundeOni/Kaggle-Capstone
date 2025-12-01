from agent import create_patho_bot, Part, Content
from google.adk.runners import InMemoryRunner
import os

def debug_run():
    print("Initializing Agent...")
    agent = create_patho_bot()
    runner = InMemoryRunner(agent=agent, app_name="DebugApp")
    session_id = "debug_session"
    
    runner.session_service.create_session(
        session_id=session_id,
        app_name="DebugApp",
        user_id="debug_user"
    )
    
    print("Sending message...")
    msg = Content(role='user', parts=[Part(text="Hello, who are you?")])
    
    events = runner.run(
        user_id="debug_user",
        session_id=session_id,
        new_message=msg
    )
    
    with open("debug_log.txt", "w") as f:
        f.write("--- Events ---\n")
        for event in events:
            f.write(f"Type: {type(event)}\n")
            f.write(f"Dir: {dir(event)}\n")
            if hasattr(event, 'text'):
                f.write(f"Text: {event.text}\n")
            if hasattr(event, 'content'):
                f.write(f"Content: {event.content}\n")
            f.write("-" * 20 + "\n")

if __name__ == "__main__":
    debug_run()
