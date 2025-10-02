from fpdf import FPDF
import streamlit as st
import pandas as pd
import numpy as np
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

def genera_pdf(db_Pasto, df_alimento, db_daticorporei):
        pdf = FPDF(orientation="L",unit="mm", format="A4")
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Report Diario", ln=True, align="C")
        pdf.ln(10)

        col_width = pdf.w / (len(db_Pasto.columns) + 1)

        # Intestazioni
        pdf.set_font("Arial", style="B", size=10)
        for col in db_Pasto.columns:
            pdf.cell(col_width, 10, col, border=1, align="C")
        pdf.ln()

        # Righe
        pdf.set_font("Arial", size=9)
        for i in range(len(db_Pasto)):
            for col in db_Pasto.columns:
                val = str(db_Pasto.iloc[i][col])
                pdf.cell(col_width, 10, val, border=1, align="C")
            pdf.ln()

        # Larghezza colonna proporzionale
        col_width = pdf.w / (len(df_alimento.columns) + 1)

        # Intestazioni
        pdf.set_font("Arial", style="B", size=10)
        for col in df_alimento.columns:
            pdf.cell(col_width, 10, col, border=1, align="C")
        pdf.ln()

        # Righe
        pdf.set_font("Arial", size=9)
        for i in range(len(df_alimento)):
            for col in df_alimento.columns:
                val = str(df_alimento.iloc[i][col])
                pdf.cell(col_width, 10, val, border=1, align="C")
            pdf.ln()

        return bytes(pdf.output(dest="S"))# ritorna come bytes

st.title("Diario del Diabete")

st.header("Diario Smart")
view_diario= st.selectbox("Scegli cosa Visualizzare\n",["DiarioPasti","AlimentoConsumato",
                                                        "DatiCorporei","MediaGlicemia",
                                                        "TotKcal","TotInsulina",
                                                        "Media Peso Corporeo","Media Massa Corporea",
                                                        "Lista Alimenti","PDF Completo"])
if st.button("Esegui"):
    if view_diario == "DiarioPasti":
        db_Pasto=({
            "Glicemia": db_Pasto["glicemia"],
            "tipoPasto": db_Pasto["tipoPasto"],
            "orario": db_Pasto["orario"],
            "data":db_Pasto["data"],
            "note": db_Pasto["note"]
        })
        st.dataframe(db_Pasto)

    elif view_diario == "AlimentoConsumato":
        db_alimento=({
            "Alimento": db_alimento["nomeAlimento"],
            "TotPeso": db_alimento["totPeso"],
            "TotCho": db_alimento["totCho"],
            "TotKcal": db_alimento["totKcal"],
            "Insulina": db_alimento["insulina"]
        })

        st.dataframe(db_alimento)

    elif view_diario == "DatiCorporei":

        db_pesoPersonale=({
            "PesoCorporeo": db_pesoPersonale["pesoPersonale"],
            "MassaCorporea": db_pesoPersonale["massaCorporea"],
            "Data": db_pesoPersonale["data"]
        })

        st.dataframe(db_pesoPersonale)
    elif view_diario == "MediaGlicemia":

        valori_glicemia= db_Pasto["glicemia"]
        try:
            glicemia=np.mean(valori_glicemia)
            
            db_valoriGlicemia=({
                "Media Glicemia": glicemia
            })
            st.dataframe(db_valoriGlicemia)
        except Exception as e:
            st.error(f"Riprovare. Valori glicemici non presenti nel db\nInserisci nei pasti e riprova\n{e}")

    elif view_diario == "TotKcal":

        valori_Kcal= db_alimento["totKcal"]
        try:
            
            # Converto sempre tutto in float, scartando ciò che non si può convertire
            valori_Kcal_float = []
            for v in valori_Kcal:
                try:
                    valori_Kcal_float.append(float(v))
                except (ValueError, TypeError):
                    # ignora stringhe vuote, None o cose non numeriche
                    continue
            
            totKcal=float(sum(valori_Kcal_float))
            
            db_valoreKcal=({
                "Totale Kcal": [totKcal]
            })
            st.dataframe(db_valoreKcal)
        except Exception as e:
            st.error(f"Riprovare. Valori kcal non presenti nel db\nInserisci nei alimenti e riprova\n{e}")

    elif view_diario == "TotInsulina":

        valori_insulina= db_alimento["insulina"]
        try:
            
            # Converto sempre tutto in float, scartando ciò che non si può convertire
            valori_insulina_float = []
            for v in valori_insulina:
                try:
                    valori_insulina_float.append(float(v))
                except (ValueError, TypeError):
                    # ignora stringhe vuote, None o cose non numeriche
                    continue
            
            totinsulina=float(sum(valori_insulina_float))
            
            db_valoreInsulina=({
                "Totale Insulina": [totinsulina]
            })
            st.dataframe(db_valoreInsulina)
        except Exception as e:
            st.error(f"Riprovare. Valori Insulina non presenti nel db\nInserisci nei alimenti e riprova\n{e}")

    elif view_diario == "Media Peso Corporeo":

        valori_pesocorporeo= db_pesoPersonale["pesoPersonale"]
        try:
            pesiCorporei=np.mean(valori_pesocorporeo)
            
            db_valoriPC=({
                "Media P.C\nPesoCorporeo": pesiCorporei
            })
            st.dataframe(db_valoriPC)

        except Exception as e:
            st.error(f"Riprovare. Valori del peso corporeo non presenti nel db\nInserisci nei pesi e riprova\n{e}")
    
    elif view_diario == "Media Massa Corporea":

        valori_MC= db_pesoPersonale["massaCorporea"]
        try:
            massaCorporea=np.mean(valori_MC)
            
            db_valoriMC=({
                "Media M.C\nMassaCorporea":  massaCorporea
            })
            st.dataframe(db_valoriMC)

        except Exception as e:
            st.error(f"Riprovare. Valori della massa corporea non presenti nel db\nInserisci nei pesi e riprova\n{e}")
    elif view_diario == "Lista Alimenti":
        
        listaAlimenti= db_alimento["nomeAlimento"]
        if listaAlimenti is not db_alimento:
            db_alimento=({
                "Alimento": listaAlimenti,
                "TotPeso": db_alimento["totPeso"],
                "TotCho": db_alimento["totCho"],
                "TotKcal": db_alimento["totKcal"],
                "Insulina": db_alimento["insulina"]
            })
        st.dataframe(db_alimento)
    
    elif view_diario == "PDF Completo":

        db_Pasto=pd.DataFrame(({
            "Glicemia": db_Pasto.get("glicemia", []),
            "TipoPasto": db_Pasto.get("tipoPasto", []),
            "Orario": db_Pasto.get("orario", []),
            "Data": db_Pasto.get("data", []),
            "Note": db_Pasto.get("note", [])
        }))
        # --- dentro la tua app ---
        df_alimenti=pd.DataFrame(({
            "Alimento": db_alimento.get("nomeAlimento", []),
            "TotPeso": db_alimento.get("totPeso", []),
            "TotCho": db_alimento.get("totCho", []),
            "TotKcal": db_alimento.get("totKcal", []),
            "Insulina": db_alimento.get("insulina", [])
        }))

        
        pdf_bytes = genera_pdf(db_Pasto, df_alimenti)
        st.download_button(
            label="📄 Scarica PDF",
            data=pdf_bytes,
            file_name="gabry23.pdf",
            mime="application/pdf"
        )
else:
    
    st.error("Riprovare.")


# --------------------- INSERIMENTO DATI ---------------------
st.write("Aggiunta Pasto")
st.subheader("Aggiungere il Pasto nel Db")
insert_diario = st.selectbox("Inserimento nel Db\n",["DiarioPasto","Alimento","PesoPersonale"])

if insert_diario == "DiarioPasto":
    with st.form("form_pasto"):
        glicemia = st.number_input("Glicemia", max_value=1000)
        tipoPasto = st.selectbox("TipoPasto",["PrimaDiColazione","Colazione","DopoColazione","Spuntino1",
                                              "DopoSpuntino1","Pranzo","DopoPranzo"
                                              "Spuntino2","DopoSpuntino2","PrimaDiCena",
                                              "Cena","DopoCena","Notte"])
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
            st.success(f"✅ Nuovo pasto salvato!\n{nuovoPasto}")

elif insert_diario == "Alimento":
    with st.form("form_alimento"):
        nomeAlimento = st.text_input("Alimento")
        totPeso = st.number_input("TotPeso",min_value=0.0,max_value=1000.0,format="%.2f")
        totCho = st.number_input("TotCho",min_value=0.0,max_value=1000.0,format="%.2f")
        totKcal = st.number_input("TotKcal",min_value=0.0,max_value=1000.0,format="%.2f")
        insulina = st.number_input("Insulina",min_value=0.0,max_value=1000.0,format="%.2f")
        

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
            
            invia_alimento = st.form_submit_button("Salva Alimento")
            if invia_alimento:
                nuovoAlimento = [id_alimento, nomeAlimento, totPeso, totCho, totKcal, insulina, id_pasto_sel]
                ws_alimento.append_row(nuovoAlimento)
                st.success(f"✅ Nuovo alimento salvato!\n{nuovoAlimento}")
           
        except Exception as e:
            st.error(f"Pasto Mancante.\nAggiungere prima il pasto la tabella è ancora vuota!\n{e}")

elif insert_diario == "PesoPersonale":
    with st.form("form_pesoPersonale"):
        pesoPersonale = st.number_input("Peso",max_value=100.0,format="%.2f")
        altezza = st.number_input("Altezza",max_value=2.40,format="%.2f")
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
            st.success(f"✅ Nuovo peso salvato!\n{nuovoPeso}")
