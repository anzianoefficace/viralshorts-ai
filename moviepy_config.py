"""
Configurazione MoviePy per ImageMagick su macOS
"""

import os

def configure_imagemagick():
    """Configura ImageMagick per MoviePy"""
    try:
        # Path predefiniti per ImageMagick su macOS con Homebrew
        imagemagick_paths = [
            '/opt/homebrew/bin/magick',  # M1/M2 Mac
            '/usr/local/bin/magick',     # Intel Mac
            '/opt/homebrew/bin/convert', # Fallback
            '/usr/local/bin/convert',    # Fallback
        ]
        
        for path in imagemagick_paths:
            if os.path.exists(path):
                os.environ['IMAGEMAGICK_BINARY'] = path
                print(f"[INFO] ImageMagick configurato: {path}")
                
                # Imposta anche la variabile per MoviePy 1.0.3
                try:
                    from moviepy.config import IMAGEMAGICK_BINARY
                    # Per versioni diverse di MoviePy
                    import moviepy.config as mp_config
                    if hasattr(mp_config, 'IMAGEMAGICK_BINARY'):
                        mp_config.IMAGEMAGICK_BINARY = path
                except:
                    pass
                
                return True
        
        print("[WARNING] ImageMagick non trovato")
        return False
        
    except Exception as e:
        print(f"[ERROR] Errore configurazione ImageMagick: {e}")
        return False

if __name__ == "__main__":
    configure_imagemagick()
