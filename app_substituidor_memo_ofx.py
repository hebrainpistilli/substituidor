
import streamlit as st

st.set_page_config(
    page_title="Substituidor IUGU",
    page_icon="📝",
    layout="centered"
)

st.title("📝 Substituidor IUGU OFX")
st.markdown("""
Este app processa arquivos `.OFX` (formato SGML) com duas funções principais:

1. **Substituição específica**:
   - `<MEMO>Tarifa fatura: ...</MEMO>` → `Tarifa de Fatura`

2. **Remoção de acentos em todos os MEMOs** para evitar problemas de encoding
""")

uploaded_file = st.file_uploader("📤 Envie seu arquivo .ofx", type="ofx")

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

if uploaded_file is not None:
    st.info("📄 Arquivo carregado com sucesso. Iniciando processamento...")

    with st.spinner("Aplicando substituição e remoção de acentos..."):
        content = uploaded_file.read().decode("latin1")
        new_content = substituir_e_normalizar(content)

    st.success("✅ Arquivo processado com sucesso!")

    st.download_button("📥 Baixar OFX tratado", new_content, file_name="extrato_ofx_tratado.ofx", mime="text/plain")
