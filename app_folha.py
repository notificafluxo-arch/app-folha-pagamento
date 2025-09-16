import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="📊 App Folha de Pagamento", layout="wide")

st.title("📊 App Folha de Pagamento")

# Upload do arquivo
uploaded_file = st.file_uploader("Carregue a planilha da folha (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Lê a primeira aba da planilha (já que só terá uma)
    base = pd.read_excel(uploaded_file)

    # === Folha de Pagamento ===
    folha_pagamento = (
        base.groupby("FONTE FINAL")
        .apply(lambda g: pd.Series({
            "Proventos": g.loc[g["TIPO P/D"] == "P", "VALOR ORIGINAL"].sum(),
            "Descontos": g.loc[g["TIPO P/D"] == "D", "VALOR ORIGINAL"].sum(),
            "Auxilio_Alimentacao": g.loc[g["NOME EVENTO"].str.contains("AUXILIO ALIMENTACAO", case=False, na=False), "VALOR ORIGINAL"].sum()
        }))
        .reset_index()
    )

    folha_pagamento["Liquido"] = (
        folha_pagamento["Proventos"]
        - folha_pagamento["Descontos"]
        - folha_pagamento["Auxilio_Alimentacao"]
    )

    folha_pagamento["Total Liquido com Vale"] = (
        folha_pagamento["Proventos"] - folha_pagamento["Descontos"]
    )

    # === Retenções ===
    retencoes = (
        base[base["TIPO P/D"] == "D"]
        .pivot_table(
            index="NOME EVENTO",
            columns="FONTE FINAL",
            values="VALOR ORIGINAL",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    # === Previdência ===
    previdencia_filtros = [
        "CONTRIBUICAO SIMPAS",
        "CONTRIBUIÇÃO SIMPAS 13º SALÁRIO",
        "Previdência Municipal - Patronal Fundo"
    ]
    previdencia = (
        base[base["NOME EVENTO"].isin(previdencia_filtros)]
        .pivot_table(
            index="NOME EVENTO",
            columns="FONTE FINAL",
            values="VALOR ORIGINAL",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    # === Conferência RH ===
    conferencia_rh = (
        base.pivot_table(
            index=["NOME VINCULO", "NOME EVENTO", "ORGANOGRAMA"],
            columns="FONTE",
            values="VALOR ORIGINAL",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    # Exibição em abas
    aba1, aba2, aba3, aba4 = st.tabs([
        "📑 Folha de Pagamento",
        "💰 Retenções",
        "🏦 Previdência",
        "🧾 Conferência RH"
    ])

    with aba1:
        st.dataframe(folha_pagamento, use_container_width=True)

    with aba2:
        st.dataframe(retencoes, use_container_width=True)

    with aba3:
        st.dataframe(previdencia, use_container_width=True)

    with aba4:
        st.dataframe(conferencia_rh, use_container_width=True)

    # Botão de download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        folha_pagamento.to_excel(writer, sheet_name="Folha de Pagamento", index=False)
        retencoes.to_excel(writer, sheet_name="Retenções", index=False)
        previdencia.to_excel(writer, sheet_name="Previdência", index=False)
        conferencia_rh.to_excel(writer, sheet_name="Conferência RH", index=False)

    st.download_button(
        label="📥 Baixar resultado em Excel",
        data=output.getvalue(),
        file_name="resultado_folha.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
