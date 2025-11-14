from fpdf import FPDF
import streamlit as st
import pandas as pd
import numpy as np
import gspread
import json

# 🔑 Carico credenziali dal secrets
sa_info = json.loads(st.secrets["gcp_service_account"])
gc = gspread.service_account_from_dict(sa_info)

# 📒 Apri i 3 fogli separati
SPREADSHEET_ID_UTENTE="1M2bQ9bHz9zBmeF61frL_26GbuKuWKZM9Hx3DdVk7_IY"    # <--- sostituisci con ID foglio UtenteCentro
SPREADSHEET_ID_PASTI = "1ntm0KHnKr1-314PXXL3-sRhdkFXjtwjg4QY9k4Kkl78"              # <--- sostituisci con ID foglio DiarioPasti
SPREADSHEET_ID_ALIMENTO = "1yWr0_ZL8ke1S7QTBsr6hKTw6VLGxXyo8IdzaNYpraYc"     # <--- sostituisci con ID foglio AlimentoConsumato
SPREADSHEET_ID_PESO = "1IFJOXtK4M4e4r5OET1DE7XlisBauhiAbiCjat2sAE5Y"             # <--- sostituisci con ID foglio Peso E Massa
SPREADSHEET_ID_HEALTHSMART= "1N0sdRsoC-EB5hYBfjjQ0Qil59j1LJ56R8B_wjTJ1SHU"  # ID foglio HealthSmart
SPREADSHEET_ID_PROFILEMICRO= "1uwNQYab5Y-i9X30dYw9wlQp4HLkxJ3Dzt6ruTxYBKvI"  # ID foglio ProfileMicro

ws_utente= gc.open_by_key(SPREADSHEET_ID_UTENTE).sheet1
ws_pasti = gc.open_by_key(SPREADSHEET_ID_PASTI).sheet1
ws_alimento = gc.open_by_key(SPREADSHEET_ID_ALIMENTO).sheet1
ws_peso = gc.open_by_key(SPREADSHEET_ID_PESO).sheet1
ws_healthsmart= gc.open_by_key(SPREADSHEET_ID_HEALTHSMART).sheet1
ws_profilemicro= gc.open_by_key(SPREADSHEET_ID_PROFILEMICRO).sheet1

# Funzione helper per leggere worksheet → DataFrame
def ws_to_df(ws):
    data = ws.get_all_records()
    return pd.DataFrame(data)

# Carica dati iniziali
db_utente= ws_to_df(ws_utente)
db_Pasto = ws_to_df(ws_pasti)
db_alimento = ws_to_df(ws_alimento)
db_pesoPersonale = ws_to_df(ws_peso)
db_healthsmart= ws_to_df(ws_healthsmart)
db_profile= ws_to_df(ws_profilemicro)

def genera_pdf(df_combined):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page("landscape")
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Report Diario", ln=True, align="C")
    pdf.ln(10)

    pdf.set_fill_color(255, 100, 0)  # Colore di riempimento intestazione
    pdf.set_text_color(255, 255, 255)  # Colore testo intestazione
    col_widths = [20, 25, 25, 15, 45, 35, 25, 25, 25, 15]  # Larghezze delle colonne
    headers = ["Data", "glicemia", "Pasto", "orario", "note", "Alimento", "TotPeso", "TotCho", "TotKcal", "Insulina"]

    # Raggruppa per data
    gruppi = df_combined.groupby("data")

    for data, gruppo in gruppi:
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(0, 0, 128)
        pdf.cell(0, 10, f"Data: {data}", ln=True)
        pdf.set_text_color(0, 0, 0)
        # Aggiungi i dati alla tabella
        pdf.set_font("Helvetica", "", 5)
        pdf.set_text_color(0, 0, 0)  # Colore testo dati
        pdf.set_fill_color(224, 235, 255)  # Colore delle celle alternate
        # Intestazioni
        pdf.set_font("Arial", style="B", size=10)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 5, header, border="L", align="C", fill=True)
        pdf.ln()

    
        # Riga dei dati
        pdf.set_font("Helvetica", size=8)
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(224, 235, 255)  # Colore delle celle alternate
        fill = False
        gruppo["totKcal"] = pd.to_numeric(gruppo["totKcal"], errors="coerce")
        gruppo["totPeso"] = pd.to_numeric(gruppo["totPeso"], errors="coerce")
        gruppo["totCho"] = pd.to_numeric(gruppo["totCho"], errors="coerce")
        gruppo["insulina"]= pd.to_numeric(gruppo["insulina"], errors="coerce")
        gruppo["glicemia"] = pd.to_numeric(gruppo["glicemia"], errors="coerce")

        totKcal= gruppo["totKcal"].sum()

        totPeso= gruppo["totPeso"].sum()

        totCho= gruppo["totCho"].sum()
        
        totInsulina=gruppo["insulina"].sum()

        mediaGlicemia = gruppo["glicemia"].mean()

        emogloglicata = (mediaGlicemia + 47.6) / 27.6 if not np.isnan(mediaGlicemia) else 0
        
        for idx, record in gruppo.iterrows():
            pdf.cell(col_widths[0], 8, str(record.get("data", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[1], 8, str(record.get("glicemia", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[2], 8, str(record.get("tipoPasto", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[3], 8, str(record.get("orario", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[4], 8, str(record.get("note", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[5], 8, str(record.get("nomeAlimento", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[6], 8, str(record.get("totPeso", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[7], 8, str(record.get("totCho", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[8], 8, str(record.get("totKcal", "")), border=1, align="C", fill=fill)
            pdf.cell(col_widths[9], 8, str(record.get("insulina", "")), border=1, align="C", fill=fill)
            pdf.ln()
            fill = not fill
        
        pdf.cell(col_widths[6], 8, f"Tot Kcal:{totKcal:.0f}",border=1,align="L",fill=fill)
        pdf.cell(col_widths[7], 8, f"Tot Peso:{totPeso:.0f}",border=1,align="L",fill=fill)
        pdf.cell(col_widths[8], 8, f"Tot Cho:{totCho:.0f}",border=1,align="L",fill=fill)
        pdf.cell(col_widths[9], 8, f"Insulina:{totInsulina:.0f}",border=1,align="L",fill=fill)
        pdf.cell(col_widths[1], 8, f"M.Glicemia:{mediaGlicemia:.0f}",border=1,align="L",fill=fill)
        pdf.cell(col_widths[0], 8, f"HBA1C:{emogloglicata:.0f}",border=1,align="L",fill=fill)
        pdf.ln(10)

    return bytes(pdf.output(dest="S"))



st.title("Diario del Diabete")

view_diario= st.selectbox("Scegli cosa Visualizzare\n",["UtenteCentro","DiarioPasti","AlimentoConsumato",
                                                        "DatiCorporei","MediaGlicemia","EmogloGlicata",
                                                        "TotKcal","TotCho","TotInsulina","Lista Alimenti",
                                                        "Media DCorporei","HealthSmart","PDF Completo"])
if st.button("Esegui Ricerca"):
    if view_diario=="UtenteCentro":

        db_utente=({
            "Username": db_utente["username"],
            "Nome": db_utente["NomeUtente"],
            "Cognome": db_utente["CognomeUtente"],
            "Data":db_utente["dataNascita"],
            "Citta": db_utente["CittaUtente"],
            "CfUtente":db_utente["CfUtente"],
            "Centro": db_utente["CentroDiabetologico"]
        })
        st.dataframe(db_utente)
        
    elif view_diario == "DiarioPasti":
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

    elif view_diario == "EmogloGlicata":

        valori_glicemia= db_Pasto["glicemia"]
        try:
            mediaGlicemia= np.mean(valori_glicemia)
            emogloglicata= (mediaGlicemia + 47.6) / 27.6
            
            db_EmogloGlicata=({
                "Media Glicemia": mediaGlicemia,
                "EmoglobiGlicata": emogloglicata
            })
            st.dataframe(db_EmogloGlicata)
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

    elif view_diario == "TotCho":

        valori_cho= db_alimento["totCho"]
        try:
            
            # Converto sempre tutto in float, scartando ciò che non si può convertire
            valori_cho_float = []
            for v in valori_cho:
                try:
                    valori_cho_float.append(float(v))
                except (ValueError, TypeError):
                    # ignora stringhe vuote, None o cose non numeriche
                    continue
            
            totcho=float(sum(valori_cho_float))
            
            db_valorecho=({
                "Totale Cho": [totcho]
            })
            st.dataframe(db_valorecho)
        except Exception as e:
            st.error(f"Riprovare. Valori Cho non presenti nel db\nInserisci nei alimenti e riprova\n{e}")

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

    elif view_diario == "Lista Alimenti":
        
        listaAlimenti= db_alimento["nomeAlimento"]
        if listaAlimenti is not db_alimento:
            db_alimento=({
                "Alimento": listaAlimenti,
                "TotPeso": db_alimento["totPeso"],
                "TotCho": db_alimento["totCho"],
                "TotKcal": db_alimento["totKcal"]
            })
        st.dataframe(db_alimento)

    elif view_diario == "Media DCorporei":

        valori_pesocorporeo= db_pesoPersonale["pesoPersonale"]

        valori_MC= db_pesoPersonale["massaCorporea"]

        try:
            pesiCorporei=np.mean(valori_pesocorporeo)
            
            massaCorporea=np.mean(valori_MC)

            db_valoriPC=({
                "Media P.C\nPesoCorporeo": pesiCorporei,
                "Media M.C\nMassaCorporea":  massaCorporea
            })
            st.dataframe(db_valoriPC)

        except Exception as e:
            st.error(f"Riprovare. Valori del peso e massa corporea non presenti nel db\nInserisci nei pesi e riprova\n{e}")
    
    elif view_diario == "HealthSmart":

        valori_health= db_healthsmart["health"]

        valori_oxygen= db_healthsmart["oxygen"]

        try:
            
            # Converto sempre tutto in float, scartando ciò che non si può convertire
            valori_health_float = []
            valori_oxygen_float=[]
            for v in valori_health:
                try:
                    valori_health_float.append(float(v))
                except (ValueError, TypeError):
                    # ignora stringhe vuote, None o cose non numeriche
                    continue

            tothealth=float(np.mean(valori_health_float))


            for v in valori_oxygen:
                try:
                    valori_oxygen_float.append(float(v))
                except (ValueError, TypeError):
                    # ignora stringhe vuote, None o cose non numeriche
                    continue

            totoxygen=float(np.mean(valori_oxygen_float))

            db_valorehealth=({
                "Media Cuore": [tothealth],
                "Media Ossigeno": [totoxygen]
            })
            st.dataframe(db_valorehealth)
        except Exception as e:
            st.error(f"Riprovare. Valori cuore e ossigeno non presenti nel db\nInserisci e riprova\n{e}")
     
    elif view_diario == "PDF Completo":

        # Controlliamo che le colonne chiave esistano
        if "id_pasto" not in db_Pasto.columns:
            st.warning("⚠️ La tabella 'DiarioPasti' non contiene 'id_pasto'. Controlla il Google Sheet.")
        if "id_pasto_sel" not in db_alimento.columns:
            st.warning("⚠️ La tabella 'AlimentoConsumato' non contiene 'id_pasto_sel'. Controlla il Google Sheet.")
    
        # Rinomina id_pasto_sel → id_pasto per la join
        if "id_pasto_sel" in db_alimento.columns:
            db_alimento = db_alimento.rename(columns={"id_pasto_sel": "id_pasto"})
    
        # Esegui join tra DiarioPasti e AlimentoConsumato
        try:
            df_combined = pd.merge(db_Pasto, db_alimento, on="id_pasto", how="outer")
        except Exception as e:
            st.error(f"❌ Errore nella join: {e}")
            st.stop()
    
        pdf_bytes = genera_pdf(df_combined)
        st.download_button(
            label="📄 Scarica PDF",
            data=pdf_bytes,
            file_name=f"dashboard.pdf",
            mime="application/pdf"
        )
else:
    
    st.error("Riprovare.")


# --------------------- INSERIMENTO DATI ---------------------

st.subheader("Aggiungere Le Informazioni nel Db")
insert_diario = st.selectbox("Inserimento nel Db\n",["UtenteCentro","DiarioPasto","Alimento","PesoPersonale","HealthSmart"])

if insert_diario == "UtenteCentro":

    with st.form("form_utente"):
        username = st.text_input("Username")
        NomeUtente = st.text_input("NomeUtente")
        CognomeUtente = st.text_input("Cognome")
        dataNascita = st.date_input("Data")
        CittaUtente= st.text_input("CittaUtente")
        CfUtente= st.text_input("CfUtente")
        CentroDiabetologico= st.text_input("CentroDiabetologico")

        try:

            invia_utente = st.form_submit_button("Salva Utente")
            if invia_utente:
                nuovoUtente = [username, NomeUtente, CognomeUtente, dataNascita.strftime("%Y-%m-%d"), CittaUtente, CfUtente, CentroDiabetologico]
                ws_utente.append_row(nuovoUtente)
                st.success(f"✅ Nuovo Utente salvato!\n{nuovoUtente}")
           
        except Exception as e:
            st.error(f"Utente Mancante.\nAggiungere prima l'utente la tabella è ancora vuota!\n{e}")

elif insert_diario == "DiarioPasto":
    with st.form("form_pasto"):
        glicemia = st.number_input("Glicemia", max_value=1000)
        tipoPasto = st.selectbox("TipoPasto",["PrimaDiColazione","Colazione","DopoColazione","Spuntino1",
                                              "DopoSpuntino1","Pranzo","DopoPranzo",
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
            data_scelta = st.date_input("Seleziona data pasto")
            data_scelta = data_scelta.strftime("%Y-%m-%d")
            db_filtrato = db_Pasto[db_Pasto["data"] == data_scelta]

            if db_filtrato.empty:
               st.warning("⚠️ Nessun pasto per la data selezionata.")
            else:
                opzioni_pasto = (
                  db_filtrato["id_pasto"].astype(str)
                  + " - " + db_filtrato["tipoPasto"]
                  + " (" + db_filtrato["data"] + ")"
                )
            scelta = st.selectbox("Scegli il pasto", opzioni_pasto)
            id_pasto_sel = int(scelta.split(" - ")[0])

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

elif insert_diario == "HealthSmart":
    with st.form("form_healthsmart"):
        
        ora = st.text_input("Orario")
        data = st.date_input("Data")
        health = st.number_input("Cuore")
        oxygen= st.number_input("Ossigeno")
        stress= st.text_input("Stress")
        note = st.text_input("Note")
        username=st.text_input("Username")

        # esempio per DiarioPasti
        if len(db_healthsmart) == 0:
            id_health = 1
        else:
            id_health = max(db_healthsmart["id_health"].astype(int)) + 1

        invia_healthsmart = st.form_submit_button("Salva Health")
        if invia_healthsmart:
            nuovoHealth = [id_health, ora, data.strftime("%Y-%m-%d"), health, oxygen, stress, note, username]
            ws_healthsmart.append_row(nuovoHealth)
            st.success(f"✅ Nuovo HealthSmart salvato!\n{nuovoHealth}")

st.title("DashBoard Control-IQ")
insert_prova = st.selectbox("Inserimento nel Db\n",["ProfileMicro","DiarioMicro"])
if insert_prova == "ProfileMicro":

    with st.form("form_profile"):
        
        basale = st.number_input("Basale")
        fsi = st.number_input("FSI")
        ic= st.number_input("IC")
        target= st.number_input("Target")
        username=st.text_input("Username")
        ora=st.text_input("Orario Rapporto")
        data = st.date_input("Data")

        # esempio per ProfileMicro
        if len(db_profile) == 0:
            id_profile = 1
        else:
            id_profile = max(db_profile["id_profile"].astype(int)) + 1

        invia_profile = st.form_submit_button("Salva Profile")
        if invia_profile:
            nuovoProfilo = [id_profile, basale, fsi, ic, target, username, ora, data.strftime("%Y-%m-%d")]
            ws_profilemicro.append_row(nuovoProfilo)
            st.success(f"✅ Nuovo Profile Micro salvato!\n{nuovoProfilo}")

