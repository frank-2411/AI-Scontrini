import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- 1. CONFIGURAZIONE AI ---
CHIAVE_API = "AIzaSyCBtXGjooxHiVPQjaw0k1S_5qN6fN059Lc" 
genai.configure(api_key=CHIAVE_API)

model = genai.GenerativeModel('gemini-2.5-flash')

def leggi_scontrini_in_blocco(lista_file):
    """Analizza i file e restituisce i dati strutturati."""
    istruzioni = """
    Sei un analista contabile. Analizza i documenti allegati.
    Restituisci SOLO un file JSON valido con questa struttura esatta:
    {
        "scontrini": [
            {
                "negozio": "Nome del negozio",
                "totale": 0.00,
                "articoli": [{"nome": "Prodotto 1", "prezzo": 0.00}]
            }
        ]
    }
    Non inserire formattazione markdown, solo il JSON puro.
    """
    
    payload_da_inviare = [istruzioni]
    for file in lista_file:
        if file.type == "application/pdf":
            payload_da_inviare.append({"mime_type": "application/pdf", "data": file.getvalue()})
        else:
            payload_da_inviare.append(Image.open(file))
            
    risposta = model.generate_content(payload_da_inviare)
    testo_pulito = risposta.text.replace("```json", "").replace("```", "").strip()
    return json.loads(testo_pulito)


# --- 2. INIZIALIZZAZIONE DELLA MEMORIA (Session State) ---
if 'persone' not in st.session_state:
    st.session_state.persone = {}  
if 'persona_attiva' not in st.session_state:
    st.session_state.persona_attiva = None

st.set_page_config(page_title="Gestione Spese AI", page_icon="👥", layout="wide")

# --- 3. BARRA LATERALE (I Nuovi Bottoni a Box) ---
with st.sidebar:
    st.header("👥 Persone")
    
    # Input per nuova persona
    nuovo_nome = st.text_input("Nome:")
    if st.button("➕ Aggiungi", use_container_width=True):
        if nuovo_nome and nuovo_nome not in st.session_state.persone:
            st.session_state.persone[nuovo_nome] = {
                "scontrini": [],
                "limite": 100.0,
                "nessun_limite": False
            }
            st.session_state.persona_attiva = nuovo_nome
            st.rerun() 
        elif nuovo_nome in st.session_state.persone:
            st.warning("Esiste già!")
            
    st.divider()
    st.subheader("Seleziona Scheda")
    
    # La nuova UI a Box Selezionabili
    if not st.session_state.persone:
        st.info("👈 Aggiungi una persona per iniziare.")
    else:
        for p in st.session_state.persone:
            # Se è la persona attiva, il bottone si colora per dare feedback visivo
            stile_bottone = "primary" if p == st.session_state.persona_attiva else "secondary"
            
            if st.button(f"👤 {p}", key=f"btn_sel_{p}", use_container_width=True, type=stile_bottone):
                st.session_state.persona_attiva = p
                st.rerun()

# --- 4. AREA PRINCIPALE (Scheda Persona Attiva) ---
if st.session_state.persona_attiva:
    nome = st.session_state.persona_attiva
    dati_persona = st.session_state.persone[nome]
    
    st.title(f"Scheda Spese di: {nome}")
    
    # -- Impostazioni Budget (ORA 100% ISOLATE GRAZIE ALLE CHIAVI) --
    st.write("### ⚙️ Impostazioni Budget")
    col1, col2 = st.columns([1, 2])
    with col1:
        senza_limite = st.checkbox(
            "♾️ Nessun limite", 
            value=dati_persona["nessun_limite"], 
            key=f"check_limite_{nome}"  # FONDAMENTALE: Lega il widget a questa persona
        )
        dati_persona["nessun_limite"] = senza_limite
        
        if not senza_limite:
            nuovo_limite = st.number_input(
                "Budget (€):", 
                min_value=0.0, 
                value=float(dati_persona["limite"]), 
                step=10.0, 
                key=f"val_limite_{nome}" # FONDAMENTALE: Lega il widget a questa persona
            )
            dati_persona["limite"] = nuovo_limite
            
    st.divider()
    
    # -- Caricamento Scontrini --
    st.subheader("📥 Carica nuovi scontrini")
    file_caricati = st.file_uploader(
        f"Aggiungi scontrini (JPG / PNG / PDF)", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=True,
        key=f"uploader_{nome}" 
    )
    
    if file_caricati and st.button("🚀 Elabora e Salva", key=f"btn_elab_{nome}"):
        with st.spinner("L'AI sta leggendo i file..."):
            try:
                nuovi_dati = leggi_scontrini_in_blocco(file_caricati)
                if "scontrini" in nuovi_dati:
                    dati_persona["scontrini"].extend(nuovi_dati["scontrini"])
                st.success("✅ Salvati!")
                st.rerun() 
            except Exception as e:
                st.error(f"Errore: {e}")
                
    st.divider()
    
    # -- Visualizzazione Scontrini --
    st.subheader("📂 Scontrini in archivio")
    totale_speso = 0.0
    
    if not dati_persona["scontrini"]:
        st.info("Nessuno scontrino salvato per questa persona.")
    else:
        for i, scontrino in enumerate(dati_persona["scontrini"]):
            negozio = scontrino.get("negozio", "Sconosciuto")
            totale_scontrino = scontrino.get("totale", 0.0)
            totale_speso += totale_scontrino
            
            col_exp, col_btn = st.columns([8, 1])
            with col_exp:
                with st.expander(f"🧾 {negozio} - € {totale_scontrino:.2f}"):
                    for articolo in scontrino.get('articoli', []):
                        st.write(f"- {articolo['nome']}: € {articolo['prezzo']:.2f}")
            with col_btn:
                if st.button("❌", key=f"del_{nome}_{i}"):
                    dati_persona["scontrini"].pop(i)
                    st.rerun() 
                    
    # -- Resoconto Finale --
    st.divider()
    st.header("💰 Resoconto")
    st.metric(label="Totale Speso", value=f"€ {totale_speso:.2f}")
    
    if not dati_persona["nessun_limite"]:
        differenza = dati_persona["limite"] - totale_speso
        if differenza >= 0:
            st.success(f"DENTRO IL BUDGET: Rimangono **€ {differenza:.2f}**.")
        else:
            st.error(f"FUORI BUDGET: Hai sforato di **€ {abs(differenza):.2f}**!")