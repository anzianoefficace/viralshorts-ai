"""
Patch temporanea per forzare l'uso del sistema di fallback OpenAI
"""

import os

def force_openai_fallback():
    """Forza l'uso del sistema di fallback disabilitando temporaneamente l'API OpenAI"""
    try:
        # Salva la chiave originale
        original_key = os.environ.get('OPENAI_API_KEY')
        if original_key:
            os.environ['OPENAI_API_KEY_BACKUP'] = original_key
            # Rimuove temporaneamente la chiave per forzare il fallback
            os.environ['OPENAI_API_KEY'] = ''
            print("[INFO] Sistema di fallback OpenAI attivato")
            return True
    except Exception as e:
        print(f"[ERROR] Errore nell'attivazione del fallback: {e}")
        return False

def restore_openai_key():
    """Ripristina la chiave API originale"""
    try:
        backup_key = os.environ.get('OPENAI_API_KEY_BACKUP')
        if backup_key:
            os.environ['OPENAI_API_KEY'] = backup_key
            del os.environ['OPENAI_API_KEY_BACKUP']
            print("[INFO] Chiave API OpenAI ripristinata")
            return True
    except Exception as e:
        print(f"[ERROR] Errore nel ripristino della chiave: {e}")
        return False

if __name__ == "__main__":
    force_openai_fallback()
