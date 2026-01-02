import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

# --- Inicializar Firestore ---
cred_dict = dict(st.secrets["firestore"])
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()
coleccion = db.collection("pedidos")

# --- Cargar pedidos actuales desde la app ---
# ⚠️ Ajusta si cargas df_pedidos de otro sitio
from utils.firestore_utils import load_dataframes_firestore

data = load_dataframes_firestore()
df_pedidos = data.get("df_pedidos")

if df_pedidos is None or df_pedidos.empty:
    print("❌ No hay pedidos para resincronizar.")
    exit()

# --- BORRAR Firestore ---
for doc in coleccion.stream():
    coleccion.document(doc.id).delete()

# --- VOLVER A CREAR ---
for _, row in df_pedidos.iterrows():
    record = row.drop("id_documento_firestore", errors="ignore").to_dict()
    doc_ref = coleccion.document()
    doc_ref.set(record)
    df_pedidos.loc[row.name, "id_documento_firestore"] = doc_ref.id

print("✅ Firestore resincronizado correctamente")
