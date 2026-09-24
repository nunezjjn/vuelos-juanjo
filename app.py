import streamlit as st
import pandas as pd
from PIL import Image
import easyocr
import numpy as np
from pathlib import Path
from datetime import datetime
import plotly.express as px

# ==========================
# CONFIGURACIÓN
# ==========================

st.set_page_config(
    page_title="Vuelos Juanjo",
    page_icon="✈️",
    layout="wide"
)

ARCHIVO_HISTORIAL = "historial_juanjo.xlsx"

# ==========================
# OCR
# ==========================

@st.cache_resource
def cargar_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = cargar_ocr()

# ==========================
# HISTORIAL
# ==========================

def cargar_historial():

    if Path(ARCHIVO_HISTORIAL).exists():
        return pd.read_excel(ARCHIVO_HISTORIAL)

    return pd.DataFrame(
        columns=[
            "fecha",
            "vuelo",
            "destino",
            "supervisor"
        ]
    )

def guardar_historial(df_nuevo):

    historial = cargar_historial()

    historial = pd.concat(
        [historial, df_nuevo],
        ignore_index=True
    )

    historial.drop_duplicates(
        subset=["fecha", "vuelo"],
        inplace=True
    )

    historial.to_excel(
        ARCHIVO_HISTORIAL,
        index=False
    )

# ==========================
# OCR IMAGEN
# ==========================

def obtener_texto(imagen):

    imagen_np = np.array(imagen)

    resultados = reader.readtext(
        imagen_np,
        detail=0
    )

    return resultados

# ==========================
# BUSCAR VUELOS JUANJO
# ==========================

def detectar_vuelos(textos):

    fecha = datetime.today().strftime(
        "%d/%m/%Y"
    )

    vuelos = []

    codigos_destino = [
        "PMI","MAD","AMS","OTP",
        "SOF","KRK","PRG","MXP",
        "CDG","ORY","BUD","RIX",
        "RTM","EIN","FCO","TRN",
        "CPH","VCE","AGP"
    ]

    for i, texto in enumerate(textos):

        if "juanjo" in texto.lower():

            vuelo = ""
            destino = ""

            inicio = max(0, i - 10)
            fin = min(len(textos), i + 10)

            zona = textos[inicio:fin]

            for elemento in zona:

                if any(c.isdigit() for c in elemento):

                    if len(elemento) >= 4:
                        vuelo = elemento

                if elemento.upper() in codigos_destino:
                    destino = elemento.upper()

            vuelos.append({
                "fecha": fecha,
                "vuelo": vuelo,
                "destino": destino,
                "supervisor": "JUANJO"
            })

    return pd.DataFrame(vuelos)

# ==========================
# INTERFAZ
# ==========================

st.title("✈️ Registro de vuelos de Juanjo")

st.write(
    "Sube una foto de la planificación recibida por WhatsApp."
)

foto = st.file_uploader(
    "Selecciona una imagen",
    type=["jpg", "jpeg", "png"]
)

if foto:

    imagen = Image.open(foto)

    st.image(
        imagen,
        caption="Imagen subida",
        use_container_width=True
    )

    with st.spinner("Leyendo la imagen..."):

        textos = obtener_texto(imagen)

    st.subheader("Texto detectado")

    st.write(textos)

    df_vuelos = detectar_vuelos(textos)

    st.subheader("Vuelos encontrados")

    st.dataframe(
        df_vuelos,
        use_container_width=True
    )

    if not df_vuelos.empty:

        if st.button("Guardar en histórico"):

            guardar_historial(df_vuelos)

            st.success(
                "Vuelos guardados correctamente"
            )

# ==========================
# HISTÓRICO
# ==========================

historico = cargar_historial()

if not historico.empty:

    st.header("📊 Histórico")

    st.dataframe(
        historico,
        use_container_width=True
    )

    historico["fecha"] = pd.to_datetime(
        historico["fecha"],
        dayfirst=True,
        errors="coerce"
    )

    # Estadística mensual

    mensual = (
        historico.groupby(
            historico["fecha"].dt.strftime("%Y-%m")
        )
        .size()
        .reset_index(name="vuelos")
    )

    st.subheader("Resumen mensual")

    fig1 = px.bar(
        mensual,
        x="fecha",
        y="vuelos",
        title="Vuelos por mes"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    # Estadística anual

    anual = (
        historico.groupby(
            historico["fecha"].dt.year
        )
        .size()
        .reset_index(name="vuelos")
    )

    st.subheader("Resumen anual")

    fig2 = px.bar(
        anual,
        x="fecha",
        y="vuelos",
        title="Vuelos por año"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # Destinos

    destinos = (
        historico.groupby("destino")
        .size()
        .reset_index(name="vuelos")
        .sort_values(
            "vuelos",
            ascending=False
        )
    )

    st.subheader("Destinos más frecuentes")

    fig3 = px.pie(
        destinos,
        values="vuelos",
        names="destino"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    with open(
        ARCHIVO_HISTORIAL,
        "rb"
    ) as archivo:

        st.download_button(
            label="📥 Descargar Excel",
            data=archivo,
            file_name=ARCHIVO_HISTORIAL,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
