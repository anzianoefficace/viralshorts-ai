#!/bin/zsh

# ViralShortsAI - Startup Script
# Questo script avvia l'applicazione ViralShortsAI con le opzioni appropriate

# Colori per output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
MAGENTA="\033[0;35m"
CYAN="\033[0;36m"
RESET="\033[0m"

# Ottieni il percorso di questo script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [ -z "$SCRIPT_DIR" ]; then
    SCRIPT_DIR="$( cd "$( dirname "$0" )" &> /dev/null && pwd )"
fi

# Vai alla directory dell'app
cd "$SCRIPT_DIR" || { 
    echo "${RED}Errore: Impossibile cambiare directory in $SCRIPT_DIR${RESET}"
    exit 1
}

# Funzione per verificare i requisiti
check_requirements() {
    echo "${BLUE}Verifica requisiti...${RESET}"
    
    # Controlla se Python è installato
    if ! command -v python3 &> /dev/null; then
        echo "${RED}Errore: Python 3 non trovato. Installa Python 3.10 o superiore.${RESET}"
        exit 1
    fi
    
    # Verifica la versione di Python
    PY_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "Python versione: $PY_VERSION"
    
    # Controlla se il file requirements.txt esiste
    if [ ! -f "requirements.txt" ]; then
        echo "${YELLOW}Attenzione: File requirements.txt non trovato.${RESET}"
    else
        echo "File requirements.txt trovato."
    fi
    
    # Controlla l'esistenza dei file principali
    for file in main.py config.json
    do
        if [ ! -f "$file" ]; then
            echo "${RED}Errore: File $file non trovato.${RESET}"
            exit 1
        fi
    done
    
    echo "${GREEN}Requisiti di base verificati.${RESET}"
}

# Funzione per avviare l'app normalmente
start_normal() {
    echo "${GREEN}Avvio di ViralShortsAI in modalità normale...${RESET}"
    python3 main.py
}

# Funzione per avviare l'app in modalità debug
start_debug() {
    echo "${YELLOW}Avvio di ViralShortsAI in modalità debug...${RESET}"
    python3 main.py --debug
}

# Funzione per avviare l'app con diagnostica
start_diagnostic() {
    echo "${MAGENTA}Avvio di ViralShortsAI in modalità diagnostica...${RESET}"
    python3 diagnostic.py
}

# Funzione per gestire l'autenticazione YouTube
manage_youtube_auth() {
    echo "${CYAN}Avvio del gestore di autenticazione YouTube...${RESET}"
    python3 youtube_auth_manager.py
}

# Funzione per gestire il database
manage_database() {
    echo "${CYAN}Avvio dell'utilità database...${RESET}"
    python3 db_utility.py
}

# Funzione per mostrare il menu
show_menu() {
    clear
    echo "${MAGENTA}=========================================================${RESET}"
    echo "${MAGENTA}           ViralShortsAI - Menu di avvio                ${RESET}"
    echo "${MAGENTA}=========================================================${RESET}"
    echo ""
    echo "1. Avvia l'applicazione (modalità normale)"
    echo "2. Avvia l'applicazione (modalità debug)"
    echo "3. Avvia la diagnostica"
    echo "4. Gestione autenticazione YouTube"
    echo "5. Gestione database"
    echo "6. Esci"
    echo ""
    echo -n "Seleziona un'opzione (1-6): "
    read choice
    
    case $choice in
        1) start_normal ;;
        2) start_debug ;;
        3) start_diagnostic ;;
        4) manage_youtube_auth ;;
        5) manage_database ;;
        6) echo "${GREEN}Arrivederci!${RESET}"; exit 0 ;;
        *) echo "${RED}Opzione non valida.${RESET}" ;;
    esac
    
    echo ""
    echo -n "Premi Enter per continuare..."
    read dummy
    show_menu
}

# Verifica dei requisiti all'avvio
check_requirements

# Se ci sono argomenti, li processiamo
if [ $# -gt 0 ]; then
    case $1 in
        --normal|-n) start_normal ;;
        --debug|-d) start_debug ;;
        --diagnostic|-D) start_diagnostic ;;
        --youtube-auth|-y) manage_youtube_auth ;;
        --database|-db) manage_database ;;
        --help|-h)
            echo "Uso: $0 [opzione]"
            echo "Opzioni:"
            echo "  --normal, -n       Avvia l'app in modalità normale"
            echo "  --debug, -d        Avvia l'app in modalità debug"
            echo "  --diagnostic, -D   Avvia l'app in modalità diagnostica"
            echo "  --youtube-auth, -y Gestione autenticazione YouTube"
            echo "  --database, -db    Gestione database"
            echo "  --help, -h         Mostra questo help"
            exit 0
            ;;
        *)
            echo "${RED}Opzione non valida: $1${RESET}"
            echo "Usa '$0 --help' per vedere le opzioni disponibili."
            exit 1
            ;;
    esac
else
    # Mostra il menu interattivo
    show_menu
fi
