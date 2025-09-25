import streamlit as st
import pandas as pd
import datetime
import gspread
import json

# 🔑 Carico credenziali dal secrets
sa_info = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(sa_info)

# 📒 Apri i 3 fogli separati
SPREADSHEET_ID_PASTI = "1ntm0KHnKr1-314PXXL3-sRhdkFXjtwjg4QY9k4Kkl78"              # <--- sostituisci con ID foglio DiarioPasti
SPREADSHEET_ID_ALIMENTO = "1yWr0_ZL8ke1S7QTBsr6hKTw6VLGxXyo8IdzaNYpraYc"     # <--- sostituisci con ID foglio AlimentoConsumato
SPREADSHEET_ID_PESO = "1IFJOXtK4M4e4r5OET1DE7XlisBauhiAbiCjat2sAE5Y"             # <--- sostituisci con ID foglio PesoPersonale

ws_pasti = gc.open_by_key(SPREADSHEET_ID_PASTI).sheet1
ws_alimento = gc.open_by_key(SPREADSHEET_ID_ALIMENTO).sheet1
ws_peso = gc.open_by_key(SPREADSHEET_ID_PESO).sheet1

# Funzione helper per leggere worksheet → DataFrame
def ws_to_df(ws):
    data = ws.get_all_records()
    return pd.DataFrame(data)

# Carica dati iniziali
db_Pasto = ws_to_df(ws_pasti)
db_alimento = ws_to_df(ws_alimento)
db_pesoPersonale = ws_to_df(ws_peso)

st.title("Diario del Diabete")

# --------------------- SELEZIONE TABELLE ---------------------
st.write("Ricerca Tabella")
select_diario = st.selectbox(
    "Seleziona tra le seguenti\n",
    ["DiarioPasti","Alimento","PesoPersonale",
     "Pasto + Alimento","MediaGlicemia",
     "AlimentoPeso","SumCho","SumKcal",
     "Insulina"]
)

if select_diario == "DiarioPasti":
    st.dataframe(db_Pasto)

elif select_diario == "Alimento":
    st.dataframe(db_alimento)

elif select_diario == "PesoPersonale":
    st.dataframe(db_pesoPersonale)

elif select_diario == "Pasto + Alimento":
    st.subheader("Vista Tabella Pasto e Alimento")

    df_unione = pd.merge(
        db_alimento,
        db_Pasto,
        left_on="pastoId",
        right_on="id_pasto",
        how="left"
    )

    df_unione["data"] = pd.to_datetime(df_unione["data"], errors='coerce').dt.date
    data_selezionata = st.date_input("Seleziona una data", value=datetime.date.today())
    df_filtrato = df_unione[df_unione["data"] == data_selezionata]

    if st.button("Esegui data"):
        df_unione = df_unione[[
            "data", "tipoPasto", "glicemia", "nomeAlimento",
            "totPeso", "totCho", "totKcal", "insulina", "note"
        ]]
        st.write(f"📅 Risultati per la data: {data_selezionata}")
        st.dataframe(df_filtrato)

elif select_diario == "MediaGlicemia":
    media_glicemia = db_Pasto["glicemia"].mean()
    st.metric("Media Glicemica", value=f"{media_glicemia:.2f} mg/dl")

elif select_diario == "AlimentoPeso":
    somma_peso = db_alimento["totPeso"].sum()
    st.metric("Tot Peso Alimento", value=f"{somma_peso:.2f} kg")

elif select_diario == "SumCho":
    somma_cho = db_alimento["totCho"].sum()
    st.metric("Tot Cho Alimento", value=f"{somma_cho:.2f} cho")

elif select_diario == "SumKcal":
    somma_kcal = db_alimento["totKcal"].sum()
    st.metric("Tot Kcal Alimento", value=f"{somma_kcal:.2f} kcal")

elif select_diario == "Insulina":
    somma_Insulina = db_alimento["insulina"].sum()
    st.metric("Tot Insulina", value=f"{somma_Insulina:.2f} U")

# --------------------- INSERIMENTO DATI ---------------------
st.write("Aggiunta Pasto")
st.subheader("Aggiungere il Pasto nel Db")
insert_diario = st.selectbox("Inserimento nel Db\n",["DiarioPasto","Alimento","PesoPersonale"])

if insert_diario == "DiarioPasto":
    with st.form("form_pasto"):
        glicemia = st.number_input("Glicemia",min_value=30, max_value=1000)
        tipoPasto = st.selectbox("TipoPasto",["Colazione","Spuntino1","Pranzo", "Spuntino2","Cena"])
        orario = st.text_input("Orario")
        data = st.date_input("Data")
        note = st.text_input("Note")

        # esempio per DiarioPasti
        if len(db_Pasto) == 0:
            id_pasto = 1
        else:
            id_pasto = max(db_Pasto["id_pasto"].astype(int)) + 1

        invia = st.form_submit_button("Salva Pasto")
        if invia:
            nuovoPasto = [id_pasto, glicemia, tipoPasto, orario, data.strftime("%Y-%m-%d"), note]
            ws_pasti.append_row(nuovoPasto)
            st.success("✅ Nuovo pasto salvato!")

elif insert_diario == "Alimento":
    with st.form("form_alimento"):
        nomeAlimento = st.text_input("Alimento")
        totPeso = st.number_input("TotPeso",min_value=0,max_value=1000)
        totCho = st.number_input("TotCho",min_value=0,max_value=1000)
        totKcal = st.number_input("TotKcal",min_value=0,max_value=1000)
        insulina = st.number_input("Insulina",min_value=0,max_value=1000)
        invia_alimento = st.form_submit_button("Salva Alimento")

        try:
            db_Pasto["id_pasto"] = db_Pasto["id_pasto"].astype(str)
            db_Pasto["data"] = db_Pasto["data"].astype(str)
            opzioni_pasto = db_Pasto["id_pasto"] + " - " + db_Pasto["tipoPasto"] + " (" + db_Pasto["data"] + ")"
            scelta = st.selectbox("Scegli il pasto", opzioni_pasto)
            id_raw = scelta.split(" - ")[0]
            id_pasto_sel = int(float(id_raw))

            # esempio per DiarioPasti
            if len(db_alimento) == 0:
                id_alimento = 1
            else:
                id_alimento = max(db_alimento["id_alimento"].astype(int)) + 1
            
            
            if invia_alimento:
                nuovoAlimento = [id_alimento, nomeAlimento, totPeso, totCho, totKcal, insulina, id_pasto_sel]
                ws_alimento.append_row(nuovoAlimento)
                st.success("✅ Nuovo alimento salvato!")
           
        except Exception as e:
            st.error(f"Pasto Mancante.\nAggiungere prima il pasto la tabella è ancora vuota!\n{e}")

elif insert_diario == "PesoPersonale":
    with st.form("form_pesoPersonale"):
        pesoPersonale = st.number_input("Peso",max_value=100.0)
        altezza = st.number_input("Altezza",max_value=2.40)
        data = st.date_input("Data")

        try:
            altezza=float(altezza)
            massaCorporea= pesoPersonale / (altezza ** 2)
            st.success(f"Massa Corporea Calcolata:{massaCorporea:.2f}")

        except ZeroDivisionError as e:
            st.error(f"Impossibile dividere per zero!\n{e}")

        if len(db_pesoPersonale) == 0:
            id_peso = 1
        else:
            id_peso = max(db_pesoPersonale["id_peso"].astype(int)) + 1

        invia_PesoPersonale = st.form_submit_button("Salva Peso")
        if invia_PesoPersonale:
            nuovoPeso = [id_peso, pesoPersonale, massaCorporea, data.strftime("%Y-%m-%d")]
            ws_peso.append_row(nuovoPeso)
            st.success("✅ Nuovo peso salvato!")
