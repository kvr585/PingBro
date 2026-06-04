import os
import winsound
import threading

def play_alert_sound(custom_sound_path=None, silent=False):
    """
    Plays an alert sound asynchronously.
    If silent is True, does nothing.
    If custom_sound_path is valid, plays the custom .wav file.
    Otherwise, plays a fallback system notification sound.
    """
    if silent:
        return
        
    def play_thread():
        try:
            if custom_sound_path and os.path.exists(custom_sound_path) and custom_sound_path.lower().endswith('.wav'):
                # Play custom WAV file
                winsound.PlaySound(custom_sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Play default Windows system sound
                winsound.PlaySound("SystemDefault", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception as e:
            print(f"Error playing sound: {e}")
            # Absolute fallback
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
                
    # Run in a separate thread to prevent any UI blocking
    threading.Thread(target=play_thread, daemon=True).start()
