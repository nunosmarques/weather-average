import requests
import pandas as pd
import streamlit as st

lat = 39.36
lon = -8.48

st.set_page_config(
    page_title="Temperaturas Chamusca - NASA API",
    layout="wide"
)

st.title("Dados retirados da API da NASA")
st.caption("Disponível até 2025")

st.markdown("""
Temperaturas estimadas para a vila da **Chamusca**, no dia **26 de maio**, com base na API NASA POWER.
""")

url = "https://power.larc.nasa.gov/api/temporal/daily/point"

params = {
    "parameters": "T2M_MAX,T2M_MIN,T2M",
    "community": "AG",
    "longitude": lon,
    "latitude": lat,
    "start": "19850526",
    "end": "20260526",
    "format": "JSON",
    "units": "metric",
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()["properties"]["parameter"]

    rows = []

    for year in range(1985, 2026):
        key = f"{year}0526"

        rows.append({
            "Ano": year,
            "Data": f"26 Maio {year}",
            "Máxima ºC": data["T2M_MAX"].get(key),
            "Mínima ºC": data["T2M_MIN"].get(key),
            "Média ºC": data["T2M"].get(key),
        })

    df = pd.DataFrame(rows)

    for column in ["Máxima ºC", "Mínima ºC", "Média ºC"]:
        df[column] = df[column].round(1)

    # General averages
    average_max = df["Máxima ºC"].mean()
    average_min = df["Mínima ºC"].mean()
    average_mean = df["Média ºC"].mean()

    # Find hottest and coldest years based on average temperature
    hottest_row = df.loc[df["Média ºC"].idxmax()]
    coldest_row = df.loc[df["Média ºC"].idxmin()]

    hottest_difference = hottest_row["Média ºC"] - average_mean
    coldest_difference = coldest_row["Média ºC"] - average_mean

    st.subheader("Resumo geral")

    col1, col2, col3 = st.columns(3)

    col1.metric("Média das máximas", f"{average_max:.1f} ºC")
    col2.metric("Média das mínimas", f"{average_min:.1f} ºC")
    col3.metric("Média geral", f"{average_mean:.1f} ºC")

    st.markdown(
        f"""
        <h3 style="color: orange;">
            Ano mais quente 
            <span style="font-size: 0.75em; font-weight: normal;">
                (diferença para a temperatura média geral: +{hottest_difference:.1f} ºC)
            </span>
        </h3>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Ano", int(hottest_row["Ano"]))
    col2.metric("Máxima", f"{hottest_row['Máxima ºC']:.1f} ºC")
    col3.metric("Mínima", f"{hottest_row['Mínima ºC']:.1f} ºC")
    col4.metric("Média", f"{hottest_row['Média ºC']:.1f} ºC")

    st.markdown(
        f"""
        <h3 style="color: #89CFF0;">
            Ano mais frio 
            <span style="font-size: 0.75em; font-weight: normal;">
                (diferença para a temperatura média geral: {coldest_difference:.1f} ºC)
            </span>
        </h3>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Ano", int(coldest_row["Ano"]))
    col2.metric("Máxima", f"{coldest_row['Máxima ºC']:.1f} ºC")
    col3.metric("Mínima", f"{coldest_row['Mínima ºC']:.1f} ºC")
    col4.metric("Média", f"{coldest_row['Média ºC']:.1f} ºC")

    st.subheader("Tabela completa")

    table_df = df.drop(columns=["Ano"])

    row_height = 35
    header_height = 38
    table_height = header_height + (len(table_df) * row_height)

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=table_height
    )

except requests.RequestException as e:
    st.error("Erro ao obter dados da API da NASA.")
    st.code(str(e))

except KeyError:
    st.error("A resposta da API não veio no formato esperado.")