import calendar
from datetime import date

import requests
import pandas as pd
import streamlit as st

lat = 39.36
lon = -8.48

START_YEAR = 1985
END_YEAR = 2025

months = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

today = date.today()

st.set_page_config(
    page_title="Temperaturas Chamusca - NASA API",
    layout="wide"
)

st.title("Dados retirados da API da NASA")
st.caption("Disponível até 2025")

st.markdown("""
Temperaturas estimadas para a vila da **Chamusca**, com base na API NASA POWER.
""")

with st.form("date_form"):
    col1, col2 = st.columns(2)

    with col1:
        selected_day = st.selectbox(
            "Dia",
            options=list(range(1, 32)),
            index=today.day - 1
        )

    with col2:
        selected_month = st.selectbox(
            "Mês",
            options=list(months.keys()),
            format_func=lambda month: months[month],
            index=today.month - 1
        )

    submitted = st.form_submit_button("Submeter")

# Validate selected day/month
max_days_in_month = calendar.monthrange(END_YEAR, selected_month)[1]

if selected_day > max_days_in_month:
    st.error(f"O mês de {months[selected_month]} não tem dia {selected_day}.")
    st.stop()

selected_month_padded = f"{selected_month:02d}"
selected_day_padded = f"{selected_day:02d}"

selected_date_label = f"{selected_day} {months[selected_month]}"

start_date = f"{START_YEAR}{selected_month_padded}{selected_day_padded}"
end_date = f"{END_YEAR}{selected_month_padded}{selected_day_padded}"

st.markdown(f"""
A analisar temperaturas estimadas para a vila da **Chamusca**, no dia **{selected_date_label}**, entre **{START_YEAR}** e **{END_YEAR}**.
""")

url = "https://power.larc.nasa.gov/api/temporal/daily/point"

params = {
    "parameters": "T2M_MAX,T2M_MIN,T2M",
    "community": "AG",
    "longitude": lon,
    "latitude": lat,
    "start": start_date,
    "end": end_date,
    "format": "JSON",
    "units": "metric",
}

try:
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()["properties"]["parameter"]

    rows = []

    for year in range(START_YEAR, END_YEAR + 1):
        key = f"{year}{selected_month_padded}{selected_day_padded}"

        max_temp = data["T2M_MAX"].get(key)
        min_temp = data["T2M_MIN"].get(key)
        mean_temp = data["T2M"].get(key)

        # Skip unavailable dates, useful for 29 February in non-leap years
        if max_temp is None or min_temp is None or mean_temp is None:
            continue

        rows.append({
            "Ano": year,
            "Data": f"{selected_day} {months[selected_month]} {year}",
            "Máxima ºC": max_temp,
            "Mínima ºC": min_temp,
            "Média ºC": mean_temp,
        })

    df = pd.DataFrame(rows)

    if df.empty:
        st.warning("Não foram encontrados dados para a data selecionada.")
        st.stop()

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