import pyautogui

class KeyboardInput:
    def __init__(self):
        pass

    def type_text(self, text):
        """Type text using keyboard"""
        try:
            pyautogui.write(text + " ")
        except Exception as e:
            print(f"Error typing: {e}")
