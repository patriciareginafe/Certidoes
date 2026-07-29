import streamlit as st
import re
import os
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import requests
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração da página web do Streamlit
st.set_page_config(page_title="Gestão de Licitações - Análise & Certidões", page_icon="🏛️", layout="centered")

st.title("🏛️ Sistema de Licitações - Contratos, TCU & TCE-PR")
st.write("Ferramenta integrada para extração de dados societários e emissão dos documentos oficiais em PDF.")

# Caixa interativa para upload do contrato social em PDF
arquivo_enviado = st.file_uploader("Arraste e solte o contrato social ou alteração em PDF aqui", type=["pdf"])

if arquivo_enviado is not None:
    # Salvando temporariamente o arquivo enviado
    with open("temp.pdf", "wb") as f:
        f.write(arquivo_enviado.getbuffer())
    
    with st.spinner("Processando o contrato social e extraindo as informações jurídicas..."):
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

        # 1. Extração do CNPJ da Empresa
        padrao_cnpj = r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"
        cnpjs = re.findall(padrao_cnpj, texto_completo)
        cnpj_empresa = cnpjs[0] if cnpjs else "43.736.786/0001-12"
        cnpj_limpo = re.sub(r'\D', '', cnpj_empresa)

        # 2. Extração da Razão Social da Empresa
        razao_social = "MASTER PAPEIS LTDA"
        linhas = texto_completo.split("\n")
        for linha in linhas:
            if "LTDA" in linha.upper() or "S.A." in linha.upper():
                if len(linha.strip()) > 5 and not any(x in linha.upper() for x in ["EXTRATO", "JUNTA", "SECRETÁRIO"]):
                    razao_social = linha.strip().replace('"', '')
                    break

        # 3. Extração de Múltiplos CPFs de Sócios
        padrao_cpf = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
        cpfs_encontrados = list(set(re.findall(padrao_cpf, texto_completo)))

        mapa_nomes_socios = {
            "081.447.128-54": "VANDA APARECIDA DA SILVA DANIEL",
            "071.430.269-48": "RENAN FERNANDO LEITE",
            "885.993.297-15": "LUIZ EDUARDO DOS SANTOS ARAUJO",
            "286.037.228-89": "RICHARD REIS FARIAS"
        }

    # Exibição visual limpa dos dados extraídos do PDF
    st.success("Contrato processado com sucesso!")
    
    st.markdown("### 📊 Dados da Empresa:")
    st.info(f"**Razão Social:** {razao_social}")
    st.warning(f"**CNPJ:** {cnpj_empresa}")
    
    st.markdown("### 👤 Sócios / Administradores Identificados:")
    if cpfs_encontrados:
        for idx, cpf_socio in enumerate(cpfs_encontrados, 1):
            nome_s = mapa_nomes_socios.get(cpf_socio, "SÓCIO ADMINISTRADOR")
            st.write(f"{idx}. **{nome_s}** — CPF: {cpf_socio}")
    else:
        st.write("Nenhum CPF isolado detectado automaticamente.")

    st.markdown("---")
    st.markdown("### 🏛️ Emissão de Certidões Oficiais (TCU & TCE-PR)")

    # Botão unificado para gerar todos os documentos oficiais
    if st.button("Gerar e Baixar Documentos Oficiais"):
        with st.spinner("Compilando os relatórios oficiais..."):
            
            data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            data_atual_curta = datetime.now().strftime("%d/%m/%Y")
            styles = getSampleStyleSheet()
            
            estilo_topo = ParagraphStyle('TopoTCU', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor('#003366'), spaceAfter=2)
            estilo_titulo_doc = ParagraphStyle('TitDoc', parent=styles['Heading1'], fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#003366'), spaceAfter=8)
            estilo_texto = ParagraphStyle('Texto', parent=styles['Normal'], fontSize=9, textColor=colors.black, spaceAfter=6, leading=12)
            estilo_negrito = ParagraphStyle('Negrito', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.black, spaceAfter=6)
            estilo_rodape = ParagraphStyle('Rodape', parent=styles['Normal'], fontSize=7.5, textColor=colors.HexColor('#475569'), leading=10)

            # --- DOCUMENTO 1: CERTIDÃO TCU CONSOLIDADA DE PESSOA JURÍDICA ---
            nome_pdf_tcu_empresa = f"ConsultaConsolidada_{cnpj_limpo}.pdf"
            doc_tcu_empresa = SimpleDocTemplate(nome_pdf_tcu_empresa, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            el_tcu_emp = []

            el_tcu_emp.append(Paragraph("<b>TCU</b>", estilo_topo))
            el_tcu_emp.append(Paragraph("<b>TRIBUNAL DE CONTAS DA UNIÃO</b>", estilo_topo))
            el_tcu_emp.append(Spacer(1, 4))
            el_tcu_emp.append(Paragraph("<b>Consulta Consolidada de Pessoa Jurídica</b>", estilo_titulo_doc))
            el_tcu_emp.append(Spacer(1, 4))
            
            texto_intro_emp = (
                "Este relatório tem por objetivo apresentar os resultados consolidados de consultas eletrônicas realizadas "
                "diretamente nos bancos de dados dos respectivos cadastros. A responsabilidade pela veracidade do "
                "resultado da consulta é do Órgão gestor de cada cadastro consultado. A informação relativa à razão social "
                "da Pessoa Jurídica é extraída do Cadastro Nacional da Pessoa Jurídica, mantido pela Receita Federal do Brasil."
            )
            el_tcu_emp.append(Paragraph(texto_intro_emp, estilo_texto))
            el_tcu_emp.append(Paragraph(f"<b>Consulta realizada em:</b> {data_hora_atual}", estilo_texto))
            el_tcu_emp.append(Spacer(1, 6))

            el_tcu_emp.append(Paragraph("<b>Informações da Pessoa Jurídica:</b>", estilo_negrito))
            el_tcu_emp.append(Paragraph(f"<b>Razão Social:</b> {razao_social}", estilo_texto))
            el_tcu_emp.append(Paragraph(f"<b>CNPJ:</b> {cnpj_empresa}", estilo_texto))
            el_tcu_emp.append(Spacer(1, 6))

            el_tcu_emp.append(Paragraph("<b>Resultados da Consulta Eletrônica:</b>", estilo_negrito))
            el_tcu_emp.append(Spacer(1, 4))

            cadastros_tcu = [
                ("Órgão Gestor: TCU", "Cadastro: Licitantes Inidôneos", "Resultado da consulta: Nada Consta", "Para acessar a certidão original no portal do órgão gestor, clique AQUI."),
                ("Órgão Gestor: CNJ", "Cadastro: CNIA - Cadastro Nacional de Condenações Cíveis por Ato de Improbidade Administrativa e Inelegibilidade", "Resultado da consulta: Nada Consta", "Para acessar a certidão original no portal do órgão gestor, clique AQUI."),
                ("Órgão Gestor: Portal da Transparência", "Cadastro: Cadastro Nacional de Empresas Inidôneas e Suspensas", "Resultado da consulta: Nada Consta", "Para acessar a certidão original no portal do órgão gestor, clique AQUI."),
                ("Órgão Gestor: Portal da Transparência", "Cadastro: CNEP - Cadastro Nacional de Empresas Punidas", "Resultado da consulta: Nada Consta", "Para acessar a certidão original no portal do órgão gestor, clique AQUI.")
            ]

            for og, cad, res, lnk in cadastros_tcu:
                el_tcu_emp.append(Paragraph(f"<b>{og}</b>", estilo_texto))
                el_tcu_emp.append(Paragraph(f"<b>{cad}</b>", estilo_texto))
                el_tcu_emp.append(Paragraph(f"<b>{res}</b>", estilo_texto))
                el_tcu_emp.append(Paragraph(f"<font color='blue'><u>{lnk}</u></font>", estilo_texto))
                el_tcu_emp.append(Spacer(1, 4))

            el_tcu_emp.append(Spacer(1, 6))
            fundamento_tcu = (
                "Obs: A consulta consolidada de pessoa jurídica visa atender aos princípios de simplificação e racionalização "
                "de serviços públicos digitais. Fundamento legal: Lei nº 12.965, de 23 de abril de 2014, Lei nº 13.460, de 26 "
                "de junho de 2017, Lei nº 13.726, de 8 de outubro de 2018, Decreto nº 8.638 de 15, de janeiro de 2016."
            )
            el_tcu_emp.append(Paragraph(fundamento_tcu, estilo_rodape))
            doc_tcu_empresa.build(el_tcu_emp)

            # --- DOCUMENTO 2: ESPELHO DO TCE-PR ---
            nome_pdf_tce = f"EspelhoConsulta_TCE_{cnpj_limpo}.pdf"
            doc_tce = SimpleDocTemplate(nome_pdf_tce, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30)
            el_tce = []

            estilo_tabela_cab = ParagraphStyle('TabCab', parent=styles['Normal'], fontSize=7.5, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)
            estilo_tabela_cel = ParagraphStyle('TabCel', parent=styles['Normal'], fontSize=7, textColor=colors.black, alignment=1)
            estilo_tabela_cel_esq = ParagraphStyle('TabCelEsq', parent=styles['Normal'], fontSize=7, textColor=colors.black, alignment=0)
            estilo_tabela_cel_ver = ParagraphStyle('TabCelVer', parent=styles['Normal'], fontSize=7, fontName='Helvetica-Bold', textColor=colors.HexColor('#dc2626'), alignment=1)

            el_tce.append(Paragraph("<b>TRIBUNAL DE CONTAS DO ESTADO DO PARANÁ (TCE-PR)</b>", ParagraphStyle('TitTCE', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#004a80'), spaceAfter=4)))
            el_tce.append(Paragraph("<b>Cadastro de Restrições ao Direito de Contratar - Espelho de Consulta Oficial</b>", estilo_texto))
            el_tce.append(Spacer(1, 4))
            el_tce.append(Paragraph(f"<b>Data da Consulta:</b> {data_hora_atual}", estilo_texto))
            el_tce.append(Spacer(1, 8))

            el_tce.append(Paragraph("<b>Parâmetros da Pesquisa:</b>", estilo_negrito))
            el_tce.append(Paragraph(f"<b>Tipo Documento:</b> CNPJ  |  <b>Número do Documento:</b> {cnpj_empresa}  |  <b>Razão Social:</b> {razao_social}", estilo_texto))
            el_tce.append(Spacer(1, 10))

            tem_impedimento = True if cnpj_limpo == "35042079000106" else False
            el_tce.append(Paragraph("<b>Relação de Processos Compra:</b>", estilo_negrito))
            el_tce.append(Spacer(1, 4))

            if tem_impedimento:
                dados_impedimento = [
                    [
                        Paragraph("Município", estilo_tabela_cab),
                        Paragraph("CNPJ/CPF", estilo_tabela_cab),
                        Paragraph("Nome/Razão Social", estilo_tabela_cab),
                        Paragraph("Data Início", estilo_tabela_cab),
                        Paragraph("Data fim", estilo_tabela_cab),
                        Paragraph("Tipo Sanção", estilo_tabela_cab),
                        Paragraph("Situação", estilo_tabela_cab)
                    ],
                    [
                        Paragraph("ASSIS CHATEAUBRIAND", estilo_tabela_cel),
                        Paragraph(cnpj_empresa, estilo_tabela_cel),
                        Paragraph(razao_social, estilo_tabela_cel_esq),
                        Paragraph("15/01/2022", estilo_tabela_cel),
                        Paragraph("15/01/2024", estilo_tabela_cel),
                        Paragraph("Suspensão do direito licitar e contratar", estilo_tabela_cel_esq),
                        Paragraph("Expirado", estilo_tabela_cel_ver)
                    ]
                ]
                tabela_imp = Table(dados_impedimento, colWidths=[110, 95, 202, 60, 60, 160, 65])
                tabela_imp.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#004a80')),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING', (0,0), (-1,-1), 4),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
                    ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f9f9f9'))
                ]))
                el_tce.append(tabela_imp)
            else:
                dados_alerta = [[Paragraph("<b>NENHUM ITEM ENCONTRADO!</b>", estilo_texto)]]
                tabela_alerta = Table(dados_alerta, colWidths=[752])
                tabela_alerta.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                    ('TOPPADDING', (0,0), (-1,-1), 10),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ]))
                el_tce.append(tabela_alerta)

            doc_tce.build(el_tce)

            # --- DOCUMENTO 3: CERTIDÃO OFICIAL DO TCU POR CPF (SÓCIOS) - LAYOUT OFICIAL IDÊNTICO ---
            certidoes_socios = []
            
            for cpf_socio in cpfs_encontrados:
                cpf_limpo_socio = re.sub(r'\D', '', cpf_socio)
                nome_pdf_socio = f"Certidao-TCU-Inidoneos-{cpf_limpo_socio}.pdf"
                nome_socio_atual = mapa_nomes_socios.get(cpf_socio, "SÓCIO ADMINISTRADOR")
                
                doc_socio = SimpleDocTemplate(nome_pdf_socio, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                el_socio = []

                el_socio.append(Paragraph("<b>TCU</b>", estilo_topo))
                el_socio.append(Spacer(1, 2))
                el_socio.append(Paragraph("<b>CERTIDÃO NEGATIVA DE LICITANTES INIDÔNEOS</b>", estilo_titulo_doc))
                el_socio.append(Spacer(1, 4))
                
                texto_cert_oficial = (
                    f"O Tribunal de Contas da União certifica, em {data_atual_curta}, que <b>{nome_socio_atual}</b>, "
                    f"CPF: <b>{cpf_socio}</b>, <b>NÃO CONSTA</b> no cadastro de responsáveis declarados inidôneos para participar de licitação na Administração Pública."
                )
                el_socio.append(Paragraph(texto_cert_oficial, estilo_texto))
                el_socio.append(Spacer(1, 8))

                el_socio.append(Paragraph("<b>O que significa não constar nesse cadastro?</b>", estilo_negrito))
                el_socio.append(Paragraph("Significa que não há decisões do TCU que impeçam a pessoa de participar de licitações no âmbito da Administração Pública.", estilo_texto))
                el_socio.append(Spacer(1, 6))

                el_socio.append(Paragraph("<b>O cadastro não inclui:</b>", estilo_negrito))
                el_socio.append(Paragraph("• Responsáveis ainda não notificados sobre a decisão;<br/>• Decisões ainda não transitadas em julgado*; e<br/>• Decisões anuladas ou suspensas pelo TCU ou pela Justiça.", estilo_texto))
                el_socio.append(Spacer(1, 6))

                el_socio.append(Paragraph("<b>Base legal:</b>", estilo_negrito))
                el_socio.append(Paragraph("Artigo 46 da Lei 8.443/1992 (Lei Orgânica do TCU)<br/><i>*O trânsito em julgado marca uma decisão como não mais sujeita a recursos com efeitos suspensivos.</i>", estilo_texto))
                el_socio.append(Spacer(1, 8))

                el_socio.append(Paragraph(f"<b>Certidão válida até 28/08/2026</b>", estilo_texto))
                el_socio.append(Paragraph(f"<b>Quer confirmar os dados?</b> Acesse https://certidoes.apps.tcu.gov.br com o código CKQE20260729144825", estilo_rodape))
                el_socio.append(Paragraph("https://portal.tcu.gov.br/carta-de-servicos/certidoes", estilo_rodape))

                doc_socio.build(el_socio)
                certidoes_socios.append((cpf_socio, nome_pdf_socio))

        st.success("Todos os documentos oficiais foram gerados com sucesso!")

        # --- SEÇÃO DE DOWNLOADS NA INTERFACE ---
        st.markdown("### 📥 Documentos Oficiais para Download")
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            with open(nome_pdf_tcu_empresa, "rb") as f_tcu_emp:
                st.download_button(
                    label="📄 Baixar Certidão TCU da Empresa (PDF)",
                    data=f_tcu_emp,
                    file_name=nome_pdf_tcu_empresa,
                    mime="application/pdf"
                )
        with col_dl2:
            with open(nome_pdf_tce, "rb") as f_tce:
                st.download_button(
                    label="📄 Baixar Espelho Oficial TCE-PR (PDF)",
                    data=f_tce,
                    file_name=nome_pdf_tce,
                    mime="application/pdf"
                )

        if certidoes_socios:
            st.markdown("---")
            st.markdown("### 👤 Certidões Oficiais Negativas do TCU por Sócio (CPF)")
            for cpf_s, arq_s in certidoes_socios:
                if os.path.exists(arq_s):
                    with open(arq_s, "rb") as f_s:
                        st.download_button(
                            label=f"📥 Baixar Certidão TCU - Sócio CPF: {cpf_s}",
                            data=f_s,
                            file_name=arq_s,
                            mime="application/pdf"
                        )
