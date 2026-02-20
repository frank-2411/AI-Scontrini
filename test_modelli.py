import google.generativeai as genai

CHIAVE_API = "AIzaSyCBtXGjooxHiVPQjaw0k1S_5qN6fN059Lc"
genai.configure(api_key=CHIAVE_API)

print("Sto chiedendo a Google i modelli disponibili per la tua chiave...\n")

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Modello supportato: {m.name}")
except Exception as e:
    print(f"Errore di connessione: {e}")