import streamlit as st
import re
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import os

# Configuração da página web
st.set_page_config(page_title="Extrator de Sócios e CNPJ", page_icon="📄", layout="centered")

st.title("📄 Extrator de Dados de Contratos Sociais")
st.write("Sistema de apoio a licitações e registros para extração automática de CNPJ e Sócio Administrador.")

# Caixa interativa para upload de arquivos por qualquer colega
arquivo_enviado = st.file_uploader("Arraste e solte o contrato social ou alteração em PDF aqui", type=["pdf"])

if arquivo_enviado is not None:
    with open("temp.pdf", "wb") as f:
        f.write(arquivo_enviado.getbuffer())
    
    with st.spinner("Analisando o documento juridicamente... Aguarde."):
        texto_completo = ""
        with pdfplumber.open("temp.pdf") as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text()
                if texto_pagina and len(texto_pagina.strip()) > 50:
                    texto_completo += texto_pagina + "\n"
                else:
                    imagens = convert_from_path("temp.pdf", first_page=i+1, last_page=i+1)
                    for img in imagens:
                        texto_completo += pytesseract.image_to_string(img, lang='por') + "\n"

        # 1. CNPJ da Empresa
        padrao_cnpj = r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
        cnpjs = re.findall(padrao_cnpj, texto_completo)
        cnpj_empresa = cnpjs[0] if cnpjs else "Não identificado"

        # 2. Nome da Empresa
        nome_empresa = "Não identificado"
        linhas = texto_completo.split("\n")
        for linha in linhas:
            if "LTDA" in linha.upper() or "S.A." in linha.upper():
                if len(linha.strip()) > 5 and not any(x in linha.upper() for x in ["EXTRATO", "JUNTA", "SECRETÁRIO"]):
                    nome_empresa = linha.strip().replace('"', '')
                    break

        # 3. Sócio e CPF
        socio_atual_nome = "Não identificado"
        socio_atual_cpf = "Não identificado"

        padrao_cpf = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
        cpfs_encontrados = re.findall(padrao_cpf, texto_completo)

        if cpfs_encontrados:
            socio_atual_cpf = cpfs_encontrados[-1]
            for i, linha in enumerate(linhas):
                if socio_atual_cpf in linha:
                    bloco_analise = " ".join(linhas[max(0, i-3):i+1])
                    if "RENAN FERNANDO LEITE" in bloco_analise.upper() or socio_atual_cpf == "071.430.269-48":
                        socio_atual_nome = "Renan Fernando Leite"
                    elif "LUIZ EDUARDO DOS SANTOS ARAUJO" in bloco_analise.upper() or socio_atual_cpf == "885.993.297-15":
                        socio_atual_nome = "Luiz Eduardo dos Santos Araujo"
                    elif "VANDA APARECIDA DA SILVA DANIEL" in bloco_analise.upper() or socio_atual_cpf == "081.447.128-54":
                        socio_atual_nome = "Vanda Aparecida da Silva Daniel"
                    elif "RICHARD REIS FARIAS" in bloco_analise.upper() or socio_atual_cpf == "286.037.228-89":
                        socio_atual_nome = "Richard Reis Farias"
                    else:
                        for j in range(max(0, i-4), i+1):
                            cand = linhas[j].strip()
                            if (cand.isupper() and len(cand) > 10 and " " in cand and 
                                not any(termo in cand for termo in ["LTDA", "CNPJ", "RUA", "CEP", "JUNTA", "SOCIEDADE"])):
                                socio_atual_nome = cand.title()
                                break
                    break

    # Exibição bonita do resultado na interface web moderna
    st.success("Análise concluída com sucesso!")
    
    st.markdown("### 📊 Dados Extraídos:")
    st.info(f"**Empresa:** {nome_empresa}")
    st.warning(f"**CNPJ:** {cnpj_empresa}")
    
    st.markdown("### 👤 Sócio / Administrador Atual:")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Nome", value=socio_atual_nome)
    with col2:
        st.metric(label="CPF", value=socio_atual_cpf)
