import streamlit as st
import re
import unicodedata
from datetime import datetime

# --- Configuração da Página e Tema ---
st.set_page_config(
    page_title="Tratamento e Padronização de OFX",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- CSS Personalizado para um Design Avançado ---
st.markdown("""
<style>
    /* Esconde o menu e o rodapé padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Define o estilo principal da página */
    .main-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        padding: 20px;
    }

    /* Estilo do card principal */
    .st-emotion-cache-1g0b5a3 {
        background-color: #ffffff;
        border-radius: 15px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        padding: 40px;
        max-width: 600px;
        width: 100%;
        text-align: center;
    }
    
    /* Estilo para títulos */
    h1 {
        color: #2e415a;
        font-family: 'Segoe UI', sans-serif;
    }
    h3 {
        color: #5d6d7e;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Estilo para o botão de download */
    .st-emotion-cache-12fmw13 button {
        background-color: #2c944d;
        color: white;
        border-radius: 8px;
        padding: 12px 25px;
        font-size: 18px;
        font-weight: bold;
        transition: background-color 0.3s, transform 0.3s;
        box-shadow: 0 4px 10px rgba(44, 148, 77, 0.4);
    }
    .st-emotion-cache-12fmw13 button:hover {
        background-color: #3cb863;
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# --- Barra Lateral (Sidebar) com um Visual Mais Limpo ---
st.sidebar.title("Sobre o App ℹ️")
st.sidebar.info(
    "Este aplicativo é uma ferramenta para **limpar arquivos OFX**, "
    "garantindo que os MEMOs estejam padronizados e sem acentos."
)
st.sidebar.markdown("---")
st.sidebar.subheader("Como Funciona 🛠️")
st.sidebar.markdown(
    "1. **Substituição Inteligente**: Transforma descrições longas, como "
    "`<MEMO>Tarifa fatura: ...</MEMO>`, em `Tarifa de Fatura`.\n\n"
    "2. **Normalização de Texto**: Remove **acentos** de **todos** os "
    "campos `<MEMO>`, garantindo compatibilidade entre sistemas."
)

# --- Funções de Processamento (Sem Alterações) ---
def remover_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

def substituir_e_normalizar(content):
    # Substituição específica
    content = re.sub(r"<MEMO>Tarifa fatura:.*?</MEMO>", "<MEMO>Tarifa de Fatura</MEMO>", content)
    
    # Remoção de acentos em todos os MEMOs
    def normalizar_memo(match):
        texto_original = match.group(1)
        texto_sem_acentos = remover_acentos(texto_original)
        return f"<MEMO>{texto_sem_acentos}</MEMO>"

    content = re.sub(r"<MEMO>(.*?)</MEMO>", normalizar_memo, content)
    return content

# --- Layout Principal da Página em um único container centralizado ---
with st.container():
    st.title("📝 Tratamento e Padronização de OFX")
    st.markdown("---")
    st.markdown("Faça o upload do seu arquivo `.ofx` para iniciar o processo de limpeza.")
    
    # Colocando o uploader no centro
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader("📥 **Envie seu arquivo .ofx**", type="ofx", help="Apenas arquivos OFX em formato TXT")

    if uploaded_file is not None:
        st.info("📄 Arquivo carregado com sucesso. Iniciando o processamento...")

        with st.spinner("Aplicando substituição e remoção de acentos..."):
            content = uploaded_file.read().decode("latin1")
            new_content = substituir_e_normalizar(content)

        st.success("🎉 **Arquivo processado com sucesso!**")
        
        # Gerando o nome do arquivo dinâmico
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        nome_arquivo = f"OFX_Tratado_{data_hoje}.ofx"

        st.download_button(
            label="📥 **Baixar OFX Tratado**",
            data=new_content,
            file_name=nome_arquivo,
            mime="text/plain"
        )
