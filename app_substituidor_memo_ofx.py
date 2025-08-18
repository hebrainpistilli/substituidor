
import streamlit as st

st.set_page_config(
    page_title="Substituidor IUGU",
    page_icon="📝",
    layout="centered"
)

st.title("📝 Substituidor IUGU OFX")
st.markdown("""
Este app substitui MEMOs nos arquivos OFX (formato SGML) com as seguintes regras:

- `<MEMO>Tarifa fatura: ...</MEMO>` → `Tarifa de Fatura`
- `<MEMO>Tarifa de Antecipação...` → `Tarifa de Antecipacao`
""")

uploaded_file = st.file_uploader("📤 Envie seu arquivo .ofx", type="ofx")

def substituir_memos(lines):
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('<MEMO>Tarifa fatura:'):
            new_lines.append('<MEMO>Tarifa de Fatura</MEMO>\n')
        elif stripped.startswith('<MEMO>Tarifa de Antecipação'):
            new_lines.append('<MEMO>Tarifa de Antecipacao</MEMO>\n')
        else:
            new_lines.append(line)
    return ''.join(new_lines)

if uploaded_file is not None:
    st.info("📄 Arquivo carregado com sucesso. Processando substituições...")

    with st.spinner("Substituindo MEMOs..."):
        content = uploaded_file.read().decode("latin1")
        lines = content.splitlines(keepends=True)
        new_content = substituir_memos(lines)

    st.success("✅ Substituições concluídas!")

    st.download_button("📥 Baixar OFX com MEMOs substituídos", new_content, file_name="extrato_editado.ofx", mime="text/plain")
    
