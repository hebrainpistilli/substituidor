import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime, timedelta
import io

# --- Configuração da Página e Tema ---
st.set_page_config(
    page_title="Conversor Excel para OFX Bancário",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- CSS Personalizado ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-1g0b5a3 {
        background-color: #ffffff;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        padding: 40px;
    }
    h1 { color: #1E3A8A; font-family: 'Segoe UI', sans-serif; }
    h3 { color: #475569; }
    .stDownloadButton button {
        background-color: #059669 !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 12px 25px !important;
        font-weight: bold !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- Funções de Apoio ---
def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

def excel_date_to_dt(serial):
    try:
        # Excel base date is 1899-12-30
        return datetime(1899, 12, 30) + timedelta(days=float(serial))
    except:
        return datetime.now()

# --- Barra Lateral (Sidebar) ---
st.sidebar.title("Configurações do OFX ℹ️")
st.sidebar.info(
    "Este app transforma planilhas de extrato (Excel/XLS) em arquivos OFX prontos para importação em sistemas contábeis e financeiros."
)
st.sidebar.markdown("---")
st.sidebar.subheader("Regras de MEMO Aplicadas 🛠️")
st.sidebar.markdown(
    "- **Tarifa de Fatura**: Se o histórico tiver 'Tarifas' + 'Fatura'.\n"
    "- **Nome do Cliente**: Se o histórico tiver 'Fatura' (sem tarifas).\n"
    "- **Tarifa de Antecipação**: Se tiver 'Tarifas' + 'Antecipação'.\n"
    "- **Pedido de Saque**: Identificação direta pelo termo.\n"
    "- **Remoção de Acentos**: Aplicada automaticamente em todos os campos."
)

# --- Layout Principal ---
st.title("💰 Conversor Excel para OFX Inteligente")
st.markdown("Converta seu relatório de movimentação em um arquivo OFX padronizado com regras de negócio.")
st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    uploaded_file = st.file_uploader("📥 **Arraste seu arquivo Excel (.xls ou .xlsx)**", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # Carregamento do arquivo
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("📄 Arquivo lido com sucesso!")
        
        with st.spinner("Processando transações e aplicando regras de negócio..."):
            # Cabeçalho OFX
            now_str = datetime.now().strftime('%Y%m%d%H%M%S')
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
                "<BANKID>999", "<ACCTID>EXTRATO-STREAMLIT", "<ACCTTYPE>CHECKING",
                "</BANKACCTFROM>", "<BANKTRANLIST>"
            ]

            transactions = []
            for index, row in df.iterrows():
                try:
                    # Tratamento de Data
                    dt = excel_date_to_dt(row['Data'])
                    dt_str = dt.strftime('%Y%m%d%H%M%S')
                    
                    # Tratamento de Valor e ID
                    amount = str(row['Valor']).replace(',', '.')
                    fitid = str(row['Código']) if pd.notnull(row['Código']) else f"TRN{index}"
                    
                    # Lógica de MEMO Baseada no Histórico
                    hist = str(row['Histórico']) if pd.notnull(row['Histórico']) else ""
                    nome_cli = str(row['Nome Cliente']).strip() if pd.notnull(row['Nome Cliente']) else ""
                    
                    if "Tarifas" in hist and "Fatura" in hist:
                        memo_final = "Tarifa de Fatura"
                    elif "Fatura" in hist and "Tarifas" not in hist:
                        memo_final = nome_cli if nome_cli else "Fatura"
                    elif "Tarifas" in hist and "Antecipação de Recebíveis" in hist:
                        memo_final = "Tarifa de Antecipação de Recebíveis"
                    elif "Pedido de Saque" in hist:
                        memo_final = "Pedido de Saque"
                    else:
                        memo_final = str(row['Tipo de Movimentação']) if pd.notnull(row['Tipo de Movimentação']) else hist

                    # Normalização Final (Remover acentos)
                    memo_final = remover_acentos(memo_final)

                    # Montagem da Transação
                    transactions.append("<STMTTRN>")
                    transactions.append("<TRNTYPE>OTHER")
                    transactions.append(f"<DTPOSTED>{dt_str}")
                    transactions.append(f"<TRNAMT>{amount}")
                    transactions.append(f"<FITID>{fitid}")
                    transactions.append(f"<MEMO>{memo_final}")
                    transactions.append("</STMTTRN>")
                except:
                    continue

            # Rodapé OFX
            last_bal = str(df.iloc[-1]['Saldo Final']).replace(',', '.')
            ofx_footer = [
                "</BANKTRANLIST>", "<LEDGERBAL>",
                f"<BALAMT>{last_bal}", f"<DTASOF>{now_str}",
                "</LEDGERBAL>", "</STMTRS>", "</STMTTRNRS>",
                "</BANKMSGSRSV1>", "</OFX>"
            ]

            full_ofx = "\n".join(ofx_header + transactions + ofx_footer)

        st.balloons()
        st.success("🎉 **Processamento concluído!** Suas regras de histórico foram aplicadas.")
        
        # Nome do arquivo para download
        nome_saida = f"Extrato_Tratado_{datetime.now().strftime('%Y%m%d_%H%M')}.ofx"

        st.download_button(
            label="📥 **Baixar Arquivo OFX para Banco**",
            data=full_ofx,
            file_name=nome_saida,
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        st.info("Certifique-se que o arquivo possui as colunas: 'Data', 'Valor', 'Histórico', 'Tipo de Movimentação' e 'Nome Cliente'.")
