import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime, timedelta
import io

# --- Configuração da Página e Tema ---
st.set_page_config(
    page_title="Tratamento e Padronização de OFX",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- CSS Personalizado para Design Avançado ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .st-emotion-cache-1g0b5a3 {
        background-color: #ffffff;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        padding: 40px;
        width: 100%;
        text-align: center;
    }
    
    h1 { color: #2e415a; font-family: 'Segoe UI', sans-serif; }
    
    .stDownloadButton button {
        background-color: #2c944d !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 12px 25px !important;
        font-size: 18px !important;
        font-weight: bold !important;
        transition: background-color 0.3s, transform 0.3s !important;
        box-shadow: 0 4px 10px rgba(44, 148, 77, 0.4) !important;
        width: 100%;
    }
    .stDownloadButton button:hover {
        background-color: #3cb863 !important;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# --- Funções de Processamento ---
def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

def excel_date_to_dt(serial):
    try:
        return datetime(1899, 12, 30) + timedelta(days=float(serial))
    except:
        return datetime.now()

# --- Barra Lateral (Sidebar) - Mantendo sua estrutura original ---
st.sidebar.title("Sobre o App ℹ️")
st.sidebar.info(
    "Este aplicativo é uma ferramenta para **gerar arquivos OFX**, "
    "garantindo que os MEMOs estejam padronizados e sem acentos."
)
st.sidebar.markdown("---")
st.sidebar.subheader("Como Funciona 🛠️")
st.sidebar.markdown(
    "1. **Conversão de Dados**: Transforma sua planilha Excel em formato OFX compatível com bancos.\n\n"
    "2. **Substituição Inteligente**: Analisa o histórico para definir se o MEMO será o Nome do Cliente ou o Tipo de Tarifa.\n\n"
    "3. **Normalização**: Remove acentos de todos os campos automaticamente."
)

# --- Layout Principal ---
with st.container():
    st.title("📝 Tratamento e Padronização de OFX")
    st.markdown("---")
    st.markdown("Faça o upload do seu arquivo de extrato para iniciar a geração do OFX.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader("📥 **Envie seu arquivo (XLS, XLSX ou CSV)**", type=["xls", "xlsx", "csv"])

    if uploaded_file is not None:
        df = None
        try:
            # Tenta ler como XLSX/XLS padrão
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            elif uploaded_file.name.endswith('.xls'):
                try:
                    df = pd.read_excel(uploaded_file, engine='xlrd')
                except:
                    # Se falhar o engine de Excel, tenta ler como CSV (comum em arquivos bancários .xls fake)
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=None, engine='python')
            else:
                df = pd.read_csv(uploaded_file, sep=None, engine='python')

            if df is not None:
                st.info("📄 Arquivo lido com sucesso. Processando regras...")

                with st.spinner("Gerando arquivo OFX..."):
                    now_str = datetime.now().strftime('%Y%m%d%H%M%S')
                    
                    # Estrutura do OFX
                    ofx_header = [
                        "OFXHEADER:100", "DATA:OFXSGML", "VERSION:102", "SECURITY:NONE",
                        "ENCODING:USASCII", "CHARSET:1252", "COMPRESSION:NONE",
                        "OLDFILEUID:NONE", "NEWFILEUID:NONE", "",
                        "<OFX>", "<SIGNONMSGSRSV1>", "<SONRS>", "<STATUS>", "<CODE>0",
                        "<SEVERITY>INFO", "</STATUS>", f"<DTSERVER>{now_str}",
                        "<LANGUAGE>POR", "</SONRS>", "</SIGNONMSGSRSV1>",
                        "<BANKMSGSRSV1>", "<STMTTRNRS>", "<TRNUID>1",
                        "<STATUS>", "<CODE>0", "<SEVERITY>INFO", "</STATUS>",
                        "<STMTRS>", "<CURDEF>BRL", "<BANKACCTFROM>",
                        "<BANKID>999", "<ACCTID>EXTRATO", "<ACCTTYPE>CHECKING",
                        "</BANKACCTFROM>", "<BANKTRANLIST>"
                    ]

                    transactions = []
                    for index, row in df.iterrows():
                        try:
                            # Tratar Data (aceita data real ou serial do excel)
                            dt_val = row['Data']
                            if isinstance(dt_val, (int, float)):
                                dt = excel_date_to_dt(dt_val)
                            else:
                                dt = pd.to_datetime(dt_val)
                            
                            dt_str = dt.strftime('%Y%m%d%H%M%S')
                            amount = str(row['Valor']).replace(',', '.')
                            fitid = str(row['Código']) if pd.notnull(row['Código']) else f"TRN{index}"
                            
                            hist = str(row['Histórico']) if pd.notnull(row['Histórico']) else ""
                            nome_cli = str(row['Nome Cliente']).strip() if pd.notnull(row['Nome Cliente']) else ""
                            
                            # Regras de Negócio para o MEMO
                            if "Tarifas" in hist and "Fatura" in hist:
                                memo = "Tarifa de Fatura"
                            elif "Fatura" in hist and "Tarifas" not in hist:
                                memo = nome_cli if nome_cli else "Fatura"
                            elif "Tarifas" in hist and "Antecipação de Recebíveis" in hist:
                                memo = "Tarifa de Antecipação de Recebíveis"
                            elif "Pedido de Saque" in hist:
                                memo = "Pedido de Saque"
                            else:
                                memo = str(row['Tipo de Movimentação']) if pd.notnull(row['Tipo de Movimentação']) else hist

                            memo = remover_acentos(memo)

                            transactions.append("<STMTTRN>")
                            transactions.append("<TRNTYPE>OTHER")
                            transactions.append(f"<DTPOSTED>{dt_str}")
                            transactions.append(f"<TRNAMT>{amount}")
                            transactions.append(f"<FITID>{fitid}")
                            transactions.append(f"<MEMO>{memo}")
                            transactions.append("</STMTTRN>")
                        except:
                            continue

                    # Finalização do arquivo
                    last_bal = str(df.iloc[-1]['Saldo Final']).replace(',', '.')
                    ofx_footer = [
                        "</BANKTRANLIST>", "<LEDGERBAL>",
                        f"<BALAMT>{last_bal}", f"<DTASOF>{now_str}",
                        "</LEDGERBAL>", "</STMTRS>", "</STMTTRNRS>",
                        "</BANKMSGSRSV1>", "</OFX>"
                    ]

                    full_content = "\n".join(ofx_header + transactions + ofx_footer)

                st.success("🎉 **Arquivo OFX gerado com sucesso!**")
                
                # Botão de Download
                st.download_button(
                    label="📥 **Baixar OFX Tratado**",
                    data=full_content,
                    file_name=f"Extrato_{datetime.now().strftime('%Y%m%d')}.ofx",
                    mime="text/plain"
                )
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")
            st.warning("Dica: Se este arquivo for uma exportação de sistema, tente salvá-lo como 'Pasta de Trabalho do Excel (.xlsx)' e tente novamente.")
