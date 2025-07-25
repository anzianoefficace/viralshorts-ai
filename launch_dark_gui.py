#!/usr/bin/env python3
"""
🚀 ViralShortsAI - Dark Theme Launcher
Avvia l'interfaccia con il nuovo tema scuro minimalista moderno
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication, QMessageBox
from gui.app_gui import ViralShortsApp

def main():
    """Launcher principale con tema scuro"""
    app = QApplication(sys.argv)
    app.setApplicationName("🎨 ViralShortsAI - Dark Edition")
    app.setOrganizationName("ViralShortsAI")
    
    try:
        # Messaggio di benvenuto
        msg = QMessageBox()
        msg.setWindowTitle("🎨 ViralShortsAI - Dark Edition")
        msg.setText("🌟 Benvenuto nel nuovo tema SCURO MINIMALISTA!\n\n"
                   "✨ Caratteristiche:\n"
                   "• Design scuro moderno e minimalista\n"
                   "• Colori ottimizzati per l'uso notturno\n"
                   "• Interfaccia pulita e professionale\n"
                   "• Componenti Material Design\n\n"
                   "🚀 Avviamo l'interfaccia...")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
        
        # Avvia GUI principale
        window = ViralShortsApp()
        window.show()
        
        print("🎨 GUI avviata con tema scuro!")
        print("🌟 Enjoy the new dark minimal theme!")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ Errore avvio GUI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
