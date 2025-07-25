"""
Script per testare le importazioni dei moduli richiesti.
"""
import sys
import traceback

print("Versione Python:", sys.version)
print("\nTest importazioni:\n")

modules_to_test = [
    "PyQt5.QtWidgets", 
    "PyQt5.QtCore",
    "openai",
    "whisper",
    "moviepy",
    "ffmpeg",
    "google.oauth2",
    "apscheduler",
    "dotenv",
    "pandas"
]

for module in modules_to_test:
    try:
        print(f"Importazione di {module}... ", end="")
        __import__(module)
        print("OK")
    except Exception as e:
        print("ERRORE")
        print(f"  - {e}")
        traceback.print_exc()
        print()

print("\nTest completato.")
