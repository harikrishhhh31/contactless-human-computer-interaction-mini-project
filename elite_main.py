import cv2
import time
import queue
import sys
from elite_system.vision_core import VisionCore
from elite_system.voice_core import VoiceCore
from elite_system.gesture_arbiter import GestureArbiter
from elite_system.action_dispatcher import ActionDispatcher
from elite_system.speaker_core import SpeakerCore
from elite_system.brain_core import BrainCore

def main():
    print("=========================================")
    print("   INITIATING ELITE INTERACTION SYSTEM   ")
    print("=========================================")
    
    # 1. Setup Comms
    command_queue = queue.Queue()
    
    # 2. Start Subsystems
    try:
        # Voice Output (Speaker)
        speaker = SpeakerCore()
        speaker.start()
        speaker.speak("Heisenberg Online.")

        vision = VisionCore()
        brain = BrainCore() # New Intelligence Layer
        arbiter = GestureArbiter()
        dispatcher = ActionDispatcher(speaker=speaker) # Pass speaker
        hud = HudRenderer()
        
        # Threaded Voice Input
        voice_thread = VoiceCore(command_queue)
        voice_thread.start()
        
    except Exception as e:
        print(f"CRITICAL ERROR during startup: {e}")
        return

    # 3. Start Camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("SYSTEM LIVE. Press 'ESC' to abort.")
    
    last_voice_command = ""
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            continue

        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        
        # A. VOICE PROCESS (Check Mailbox)
        try:
            while not command_queue.empty():
                msg = command_queue.get_nowait()
                if msg['type'] == "VOICE_COMMAND":
                    last_voice_command = msg['payload']
                    print(f"MAIN: Received Voice -> {last_voice_command}")
        except queue.Empty:
            pass

        # B. VISION PROCESS
        vision_data = vision.process_frame(frame)
        
        # C. DECISION (Arbiter)
        voice_ctx = {'last_command': last_voice_command}
        decision, confidence = arbiter.decide(vision_data, {}, voice_ctx) 
        
        # Merge voice for dispatch
        vision_data['voice_command'] = last_voice_command
        
        # INTELLIGENCE INTERCEPT
        if decision == "ACTION_QUERY":
             # Ask the Brain
             print("🧠 CONSULTING BRAIN CORE...")
             answer = brain.get_knowledge(last_voice_command)
             vision_data['brain_response'] = answer
        
        # D. ACTION (Muscles)
        dispatcher.execute(decision, vision_data)
        
        # Clear command after execution (if it was an impulsive action)
        if "ACTION_" in decision and decision != "ACTION_MOUSE_MOVE":
             last_voice_command = "" # Reset to prevent spamming the same command
        
        # E. RENDER (Skin)
        frame = hud.render(frame, vision_data, decision)
        
        # Display
        cv2.imshow('Elite HCI System (Heisenberg)', frame)
        
        if cv2.waitKey(5) & 0xFF == 27:
            break
            
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    voice_thread.stop()
    print("SYSTEM SHUTDOWN.")

if __name__ == "__main__":
    main()
