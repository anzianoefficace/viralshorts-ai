# ViralShortsAI - Creatore Automatico di Video Virali

ViralShortsAI è un'applicazione desktop completa in Python che automatizza la creazione e la pubblicazione di video virali per YouTube Shorts. L'app si occupa di trovare contenuti popolari, elaborarli e ripubblicarli con ottimizzazioni per massimizzare la visibilità e l'engagement.

![ViralShortsAI Logo](https://i.imgur.com/pLj9Go0.png)

## 🌟 Caratteristiche Principali

- **Ricerca Intelligente** - Trova automaticamente YouTube Shorts virali usando l'API YouTube
- **Filtraggio Avanzato** - Seleziona solo video con licenze compatibili per il riutilizzo
- **Elaborazione Video** - Crea clip ottimizzate da 15s, 30s e 60s
- **Sottotitoli Automatici** - Trascrive e sincronizza l'audio con Whisper
- **Ottimizzazione con AI** - Genera titoli, descrizioni e hashtag virali con GPT-4
- **Pubblicazione Automatica** - Carica video su YouTube negli orari di massimo engagement
- **Analisi Performance** - Monitora metriche e adatta la strategia in base ai risultati

## 🛠️ Installazione

### Prerequisiti

- Python 3.10+
- ffmpeg (richiesto per l'elaborazione video)
- Account YouTube con API abilitata
- Account OpenAI per accesso a GPT-4 e Whisper

### Passaggi

1. Clona il repository:
```bash
git clone https://github.com/tuonome/ViralShortsAI.git
cd ViralShortsAI
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Crea un file `.env` nella directory principale copiando `.env.example`:
```bash
cp .env.example .env
```

4. Modifica il file `.env` con le tue API keys:
```
YOUTUBE_API_KEY=your_youtube_api_key
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_REFRESH_TOKEN=your_refresh_token
OPENAI_API_KEY=your_openai_api_key
```

## 🚀 Utilizzo

### Avvio dell'Applicazione

```bash
python main.py
```

### Configurazione Iniziale

1. Vai alla scheda **Parametri** e configura:
   - Categorie di video da cercare
   - Durate delle clip da generare
   - Numero massimo di video al giorno
   - Lingua principale
   - Hashtag personalizzati

2. Vai alla scheda **Dashboard** e fai clic su **Avvia ora** per eseguire il processo manualmente.

3. Abilita l'opzione **Esegui ogni giorno alle 10:00** per pianificare l'esecuzione quotidiana.

### Monitoraggio dei Risultati

La scheda **Risultati** mostra le metriche di performance per tutti i video caricati:
- Views
- Like
- Commenti
- Viral Score (punteggio di viralità calcolato)
- Retention (percentuale di visualizzazione media)

## 📁 Struttura del Progetto

```
ViralShortsAI/
│
├── main.py                  # Avvio applicazione e coordinamento
├── config.json              # Configurazione salvata
├── requirements.txt         # Dipendenze Python
├── database.py              # Gestione database SQLite
├── utils.py                 # Utilità e logging
│
├── /data/                   # Video scaricati e metadati
│   └── downloader.py        # Modulo ricerca e download video
│
├── /processing/             # Elaborazione video
│   └── editor.py            # Creazione clip e sottotitoli
│
├── /ai/                     # Integrazione AI
│   ├── whisper_transcriber.py  # Trascrizione audio
│   └── gpt_captioner.py     # Generazione testi con GPT-4
│
├── /upload/                 # Upload su YouTube
│   └── youtube_uploader.py  # Gestione autenticazione e upload
│
├── /monitoring/             # Analisi performance
│   └── analyzer.py          # Monitoraggio e ottimizzazione
│
├── /gui/                    # Interfaccia grafica
│   └── app_gui.py           # GUI in PyQt5
│
└── /logs/                   # File di log
```

## ⚙️ Configurazione YouTube API

1. Vai alla [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto
3. Abilita le YouTube Data API v3
4. Crea credenziali OAuth 2.0:
   - Tipo: Applicazione Desktop
   - Aggiungi gli scope necessari per l'upload video

5. Per generare il refresh token, usa questo script:
```python
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',  # Scaricato dalla Console Google
    scopes=['https://www.googleapis.com/auth/youtube.upload']
)

credentials = flow.run_local_server(port=0)
print(f"Refresh token: {credentials.refresh_token}")
```

## 🔍 Risoluzione Problemi

### Problema con le Quote API di YouTube
YouTube ha limiti giornalieri per le chiamate API. Se vedi errori "quotaExceeded":
- Riduci il numero massimo di video al giorno
- Crea più progetti Google Cloud e alterna tra diverse API keys

### Errori ffmpeg
Se riscontri problemi con l'elaborazione video:
- Verifica che ffmpeg sia installato correttamente: `ffmpeg -version`
- Installa ffmpeg se necessario:
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: Scarica da [ffmpeg.org](https://ffmpeg.org/download.html)

### Errori di Autenticazione YouTube
- Verifica che le credenziali nel file .env siano corrette
- Il refresh token potrebbe essere scaduto: rigeneralo seguendo la procedura sopra

## 📈 Ottimizzazione delle Performance

L'applicazione impara automaticamente quali tipi di video hanno le migliori performance e adatta la propria strategia nel tempo. Per ottenere risultati migliori:

1. Lascia che l'app raccolga dati per almeno 1-2 settimane
2. Verifica regolarmente la scheda "Risultati" per identificare tendenze
3. Aggiusta manualmente le categorie e durate video in base ai dati raccolti

## 📄 Licenza

Questo progetto è distribuito con licenza MIT. Vedi il file `LICENSE` per ulteriori dettagli.

## ⚠️ Disclaimer

Assicurati di utilizzare questa applicazione solo per contenuti che hai il diritto di ripubblicare. L'app è progettata per lavorare solo con video con licenze appropriate (Creative Commons) o che permettono esplicitamente il remix. L'uso improprio di contenuti protetti da copyright è responsabilità dell'utente.
