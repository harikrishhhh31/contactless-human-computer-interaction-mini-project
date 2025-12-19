import time
import pyautogui

# text = input("Enter the string to type: ")
text = "Hello, this is an automated typing test."

print("You have 5 seconds. Place your cursor in the target application...")
time.sleep(5)

pyautogui.write(text, interval=0.02)
print("Typing completed.")
