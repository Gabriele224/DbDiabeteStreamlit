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

st.header("Diario Smart")
view_diario= st.selectbox("Scegli cosa Visualizzare\n",["DiarioPasti", "AlimentoConsumato", "DatiCorporei"])
if view_diario == "DiarioPasti":
    if db_Pasto.empty:
        st.info("Nessun pasto registrato.")
    else:
        # Ordino per data decrescente
        db_Pasto = db_Pasto.sort_values("data", ascending=False)
        for _, row in db_Pasto.iterrows():
            with st.container():
                st.subheader(f"{row['data']} - {row['tipoPasto']}")
                st.write(f"🩸 Glicemia: **{row['glicemia']} mg/dl**")
                st.write(f"⏰ Orario: {row['orario']}")
                if row["note"]:
                    st.write(f"📝 {row['note']}")
                st.markdown("---")
elif view_diario == "AlimentoConsumato":
    if db_alimento.empty:
        st.info("Nessun alimento registrato.")
    else:
        for _, row in db_alimento.iterrows():
            with st.container():
                st.subheader(row["nomeAlimento"])
                st.write(f"Peso: **{row['totPeso']} g**")
                st.write(f"CHO: {row['totCho']} g")
                st.write(f"Kcal: {row['totKcal']}")
                st.write(f"Insulina: {row['insulina']}")
                st.markdown("---")

elif view_diario == "DatiCorporei":

    if db_pesoPersonale.empty:
        st.info("Nessun peso registrato.")
    else:
        db_pesoPersonale = db_pesoPersonale.sort_values("data", ascending=False)
        for _, row in db_pesoPersonale.iterrows():
            st.write(f"📅 {row['data']} → {row['pesoPersonale']} kg (BMI: {row['massaCorporea']:.2f})")
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
        totPeso = st.number_input("TotPeso",min_value=0.5,max_value=1000.0)
        totCho = st.number_input("TotCho",min_value=0.5,max_value=1000.0)
        totKcal = st.number_input("TotKcal",min_value=0.5,max_value=1000.0)
        insulina = st.number_input("Insulina",min_value=0.5,max_value=1000.0)
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
