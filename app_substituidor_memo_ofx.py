import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime, timedelta
import io

# --- Configuração da Página ---
st.set_page_config(page_title="Conversor Excel para OFX", page_icon="💰", layout="wide")

# --- Funções de Apoio ---
def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

def excel_date_to_dt(serial):
    try:
        return datetime(1899, 12, 30) + timedelta(days=float(serial))
    except:
        return datetime.now()

# --- Layout ---
st.title("💰 Conversor Excel para OFX Inteligente")
uploaded_file = st.file_uploader("📥 Envie seu arquivo (XLS, XLSX ou CSV)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # LÓGICA DE LEITURA CORRIGIDA:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xls'):
            # Para arquivos .xls antigos, precisamos do engine 'xlrd'
            df = pd.read_excel(uploaded_file, engine='xlrd')
        else:
            # Para .xlsx modernos
            df = pd.read_excel(uploaded_file)

        st.success("📄 Arquivo lido com sucesso!")

        # --- Processamento do OFX (Regras de MEMO) ---
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
                dt = excel_date_to_dt(row['Data'])
                dt_str = dt.strftime('%Y%m%d%H%M%S')
                amount = str(row['Valor']).replace(',', '.')
                fitid = str(row['Código']) if pd.notnull(row['Código']) else f"TRN{index}"
                
                hist = str(row['Histórico']) if pd.notnull(row['Histórico']) else ""
                nome_cli = str(row['Nome Cliente']).strip() if pd.notnull(row['Nome Cliente']) else ""
                
                # Aplicação das Regras solicitadas
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

                memo_final = remover_acentos(memo_final)

                transactions.append("<STMTTRN>")
                transactions.append("<TRNTYPE>OTHER")
                transactions.append(f"<DTPOSTED>{dt_str}")
                transactions.append(f"<TRNAMT>{amount}")
                transactions.append(f"<FITID>{fitid}")
                transactions.append(f"<MEMO>{memo_final}")
                transactions.append("</STMTTRN>")
            except:
                continue

        last_bal = str(df.iloc[-1]['Saldo Final']).replace(',', '.')
        ofx_footer = [
            "</BANKTRANLIST>", "<LEDGERBAL>",
            f"<BALAMT>{last_bal}", f"<DTASOF>{now_str}",
            "</LEDGERBAL>", "</STMTRS>", "</STMTTRNRS>",
            "</BANKMSGSRSV1>", "</OFX>"
        ]

        full_ofx = "\n".join(ofx_header + transactions + ofx_footer)

        st.download_button(
            label="📥 Baixar Arquivo OFX",
            data=full_ofx,
            file_name=f"Extrato_{datetime.now().strftime('%Y%m%d')}.ofx",
            mime="text/plain"
        )

    except Exception as e:
        st.error(f"Erro de compatibilidade: {e}")
        st.warning("Dica: Se o arquivo for um .xls gerado por sistemas antigos, tente salvá-lo como 'Pasta de Trabalho do Excel (.xlsx)' e envie novamente.")
