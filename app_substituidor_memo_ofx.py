import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime, timedelta
import io

# --- Configuração da Página ---
st.set_page_config(
    page_title="Tratamento e Padronização de OFX",
    page_icon="📝",
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
        return datetime(1899, 12, 30) + timedelta(days=float(serial))
    except:
        return datetime.now()

# --- Barra Lateral (Sidebar) ---
st.sidebar.title("Sobre o App ℹ️")
st.sidebar.info("Ferramenta para **gerar arquivos OFX** com padronização de MEMO e remoção de acentos.")
st.sidebar.markdown("---")
st.sidebar.subheader("Como Funciona 🛠️")
st.sidebar.markdown(
    "1. **Conversão**: Transforma planilhas em OFX.\n\n"
    "2. **Regras de MEMO**: Define o nome do cliente ou tarifa baseado no histórico.\n\n"
    "3. **Compatibilidade**: Remove acentos para evitar erros em bancos."
)

# --- Layout Principal ---
with st.container():
    st.title("📝 Tratamento e Padronização de OFX")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader("📥 **Envie seu arquivo (XLS, XLSX ou CSV)**", type=["xls", "xlsx", "csv"])

    if uploaded_file is not None:
        try:
            df = None
            file_bytes = uploaded_file.read()
            
            # Tenta ler como Excel primeiro (XLSX ou XLS)
            try:
                # Tenta motor moderno
                df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
            except:
                try:
                    # Tenta motor antigo (XLS binário)
                    df = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
                except:
                    # Se falhar Excel, tenta CSV com detecção de encoding
                    encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
                    for enc in encodings:
                        try:
                            df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python', encoding=enc, on_bad_lines='skip')
                            if 'Data' in [str(c).strip() for c in df.columns]:
                                break
                        except:
                            continue
            
            if df is not None:
                # Limpeza rigorosa das colunas
                df.columns = [str(c).strip() for c in df.columns]

                if 'Data' not in df.columns:
                    st.error(f"Coluna 'Data' não encontrada. Colunas detectadas: {list(df.columns)}")
                else:
                    st.info("📄 Arquivo processado com sucesso!")

                    with st.spinner("Gerando OFX..."):
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
                            "<BANKID>999", "<ACCTID>EXTRATO", "<ACCTTYPE>CHECKING",
                            "</BANKACCTFROM>", "<BANKTRANLIST>"
                        ]

                        transactions = []
                        for index, row in df.iterrows():
                            try:
                                # Data
                                dt_val = row['Data']
                                if isinstance(dt_val, (int, float)):
                                    dt = excel_date_to_dt(dt_val)
                                else:
                                    dt = pd.to_datetime(dt_val, dayfirst=True)
                                
                                dt_str = dt.strftime('%Y%m%d%H%M%S')
                                
                                # Valor
                                val_raw = str(row['Valor']).replace('.', '').replace(',', '.')
                                amount = float(val_raw)
                                
                                fitid = str(row['Código']) if 'Código' in df.columns and pd.notnull(row['Código']) else f"TRN{index}"
                                hist = str(row['Histórico']) if 'Histórico' in df.columns else ""
                                nome_cli = str(row['Nome Cliente']).strip() if 'Nome Cliente' in df.columns and pd.notnull(row['Nome Cliente']) else ""
                                
                                # Regras de MEMO
                                if "Tarifas" in hist and "Fatura" in hist:
                                    memo = "Tarifa de Fatura"
                                elif "Fatura" in hist and "Tarifas" not in hist:
                                    memo = nome_cli if nome_cli else "Fatura"
                                elif "Tarifas" in hist and "Antecipação de Recebíveis" in hist:
                                    memo = "Tarifa de Antecipação de Recebíveis"
                                elif "Pedido de Saque" in hist:
                                    memo = "Pedido de Saque"
                                else:
                                    memo = str(row['Tipo de Movimentação']) if 'Tipo de Movimentação' in df.columns else hist

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

                        last_bal = str(df.iloc[-1]['Saldo Final']).replace(',', '.') if 'Saldo Final' in df.columns else "0.00"
                        
                        ofx_footer = [
                            "</BANKTRANLIST>", "<LEDGERBAL>",
                            f"<BALAMT>{last_bal}", f"<DTASOF>{now_str}",
                            "</LEDGERBAL>", "</STMTRS>", "</STMTTRNRS>",
                            "</BANKMSGSRSV1>", "</OFX>"
                        ]

                        full_content = "\n".join(ofx_header + transactions + ofx_footer)

                    st.success("🎉 **Arquivo OFX gerado!**")
                    st.download_button(
                        label="📥 **Baixar OFX Tratado**",
                        data=full_content,
                        file_name=f"Extrato_{datetime.now().strftime('%Y%m%d')}.ofx",
                        mime="text/plain"
                    )
            else:
                st.error("Não foi possível decodificar o arquivo. Tente salvá-lo como XLSX no Excel antes de subir.")

        except Exception as e:
            st.error(f"Erro fatal: {e}")
