import os
import sys
import threading

# Import winsound only on Windows
if sys.platform.startswith('win'):
    import winsound
else:
    winsound = None

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
            if winsound:
                if custom_sound_path and os.path.exists(custom_sound_path) and custom_sound_path.lower().endswith('.wav'):
                    # Play custom WAV file
                    winsound.PlaySound(custom_sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    # Play default Windows system sound
                    winsound.PlaySound("SystemDefault", winsound.SND_ALIAS | winsound.SND_ASYNC)
            else:
                # Linux fallback: try using available command line audio players
                if custom_sound_path and os.path.exists(custom_sound_path):
                    import shutil
                    for player in ['paplay', 'aplay', 'play', 'canberra-gtk-play']:
                        if shutil.which(player):
                            if player == 'canberra-gtk-play':
                                os.system(f"{player} -f \"{custom_sound_path}\" &")
                            else:
                                os.system(f"{player} \"{custom_sound_path}\" &")
                            return
                # Standalone system bell alert fallback
                print('\a', end='', flush=True)
        except Exception as e:
            print(f"Error playing sound: {e}")
                
    # Run in a separate thread to prevent any UI blocking
    threading.Thread(target=play_thread, daemon=True).start()
