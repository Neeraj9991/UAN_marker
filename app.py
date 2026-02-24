import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import os
from tempfile import NamedTemporaryFile

# ──────────────────────────── Page Config ────────────────────────────
st.set_page_config(
    page_title="UAN & ESIC Marker",
    page_icon="🔍",
    layout="centered",
)

# ──────────────────────────── Custom CSS ─────────────────────────────
st.markdown("""
<style>
    /* ── Hide Streamlit boilerplate & sidebar ── */
    #MainMenu, footer, header {visibility: hidden;}
    section[data-testid="stSidebar"],
    button[data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {display: none !important;}

    /* ── Global ── */
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}

    /* ── Hero Header ── */
    .hero {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white;
    }
    .hero img {
        width: 90px;
        height: 90px;
        border-radius: 12px;
        object-fit: contain;
        background: #fff;
        padding: 6px;
    }
    .hero-text h1 {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0 0 0.15rem 0;
        letter-spacing: -0.5px;
    }
    .hero-text p {
        font-size: 0.9rem;
        opacity: 0.88;
        margin: 0;
    }

    /* ── Section Labels ── */
    .section-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #888;
        margin-bottom: 0.5rem;
    }

    /* ── Upload Cards ── */
    [data-testid="stFileUploader"] {
        border: 2px dashed #d0d5dd;
        border-radius: 12px;
        padding: 0.8rem;
        background: #fafbfc;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #2c5364;
    }

    /* ── Metric Cards ── */
    [data-testid="stMetric"] {
        background: #f8f9fb;
        border: 1px solid #e8ecf1;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #203a43;
    }

    /* ── Download Buttons ── */
    .stDownloadButton > button {
        width: 100%;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white;
        border: none;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(15, 32, 39, 0.4);
        color: white;
    }

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────── Constants ──────────────────────────────
HIGHLIGHT_COLORS = {
    "🟡 Yellow": (1, 1, 0),
    "🔴 Red": (1, 0, 0),
    "🟢 Green": (0, 1, 0),
    "🔵 Light Blue": (0.68, 0.85, 0.9),
    "🔷 Dark Blue": (0, 0, 0.55),
}

# Color will be selected inline in the upload section


# ──────────────────────────── Core Logic ─────────────────────────────
def highlight_numbers(pdf_path, numbers, output_path, number_type, highlight_color):
    """Search for numbers in a PDF, highlight them, and return stats."""
    pdf_document = fitz.open(pdf_path)

    pages_to_keep = [0]
    total_matches = 0
    not_found_numbers = set(numbers)
    found_numbers = set()

    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text()
        contains_number = False
        page_matches = 0

        for number in numbers:
            start = 0
            while True:
                idx = page_text.find(number, start)
                if idx == -1:
                    break
                matches = page.search_for(number)
                if matches:
                    contains_number = True
                    page_matches += len(matches)
                    not_found_numbers.discard(number)
                    found_numbers.add(number)
                    for match in matches:
                        highlight = page.add_highlight_annot(match)
                        highlight.set_colors(stroke=highlight_color)
                        highlight.update()
                    break
                start = idx + 1

        if contains_number:
            pages_to_keep.append(page_number)
        total_matches += page_matches

    # Save trimmed PDF
    new_pdf = fitz.open()
    for page_number in pages_to_keep:
        new_pdf.insert_pdf(pdf_document, from_page=page_number, to_page=page_number)
    new_pdf.save(output_path)
    new_pdf.close()
    pdf_document.close()

    return total_matches, sorted(found_numbers), sorted(not_found_numbers)


# ──────────────────────────── Header ─────────────────────────────────
import base64

logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
if os.path.exists(logo_path):
    with open(logo_path, "rb") as img_f:
        logo_b64 = base64.b64encode(img_f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="Logo">'
else:
    logo_html = '<span style="font-size:2.5rem">🔍</span>'

st.markdown(
    f"""
    <div class="hero">
        {logo_html}
        <div class="hero-text">
            <h1>UAN & ESIC Number Marker</h1>
            <p>Upload your PDFs and Excel sheet — matching numbers will be highlighted automatically.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────── File Upload ────────────────────────────
st.markdown('<p class="section-label">📂 Upload Files</p>', unsafe_allow_html=True)

# Highlight color picker — inline
selected_color_name = st.selectbox(
    "Highlight Color",
    options=list(HIGHLIGHT_COLORS.keys()),
    index=3,
    help="Choose the color used to highlight matching numbers in the PDFs.",
)
selected_color = HIGHLIGHT_COLORS[selected_color_name]

col_pdf1, col_pdf2 = st.columns(2)
with col_pdf1:
    uan_pdf_file = st.file_uploader(
        "PF PDF File",
        type=["pdf"],
        help="The PF statement PDF to search for UAN numbers."
    )
with col_pdf2:
    esic_pdf_file = st.file_uploader(
        "ESIC PDF File",
        type=["pdf"],
        help="The ESIC statement PDF to search for ESI numbers."
    )

excel_file = st.file_uploader(
    "Excel File (.xlsx)",
    type=["xlsx"],
    help="Excel sheet containing 'UAN No.' and 'ESI No' columns (data starts at row 7)."
)

st.divider()

# ──────────────────────────── Processing ─────────────────────────────
if uan_pdf_file and esic_pdf_file and excel_file:
    # Save uploaded files to temp
    with (
        NamedTemporaryFile(delete=False, suffix=".pdf") as uan_tmp,
        NamedTemporaryFile(delete=False, suffix=".pdf") as esic_tmp,
        NamedTemporaryFile(delete=False, suffix=".xlsx") as xl_tmp,
    ):
        uan_tmp.write(uan_pdf_file.getbuffer())
        esic_tmp.write(esic_pdf_file.getbuffer())
        xl_tmp.write(excel_file.getbuffer())
        uan_pdf_path = uan_tmp.name
        esic_pdf_path = esic_tmp.name
        xl_path = xl_tmp.name

    base_name = os.path.basename(excel_file.name)[:3]
    output_uan = os.path.join(os.path.dirname(uan_pdf_path), f"{base_name}_PF_highlighted.pdf")
    output_esic = os.path.join(os.path.dirname(esic_pdf_path), f"{base_name}_ESIC_highlighted.pdf")

    # Read Excel
    df = pd.read_excel(xl_path, skiprows=6)

    # Column preview (collapsed by default)
    with st.expander("📋 Excel Column Preview", expanded=False):
        st.code(", ".join(df.columns.tolist()))

    uan_column = "UAN No."
    esic_column = "ESI No"

    if uan_column not in df.columns or esic_column not in df.columns:
        st.error(
            f"❌ Required columns **'{uan_column}'** or **'{esic_column}'** not found in the Excel file. "
            f"Please check your file and try again."
        )
        st.stop()

    # Prepare number lists
    df_uan = df[df[uan_column].notna() & (df[uan_column] != "EXEMPTED")]
    df_uan[uan_column] = df_uan[uan_column].astype(float).astype(int).astype(str).str.strip()
    uan_numbers = df_uan[uan_column].tolist()

    df_esic = df[df[esic_column].notna() & (df[esic_column] != "EXEMPTED")]
    df_esic[esic_column] = df_esic[esic_column].astype(float).astype(int).astype(str).str.strip()
    esic_numbers = df_esic[esic_column].tolist()

    # Process with progress feedback
    with st.spinner("🔄 Processing PDFs — this may take a moment…"):
        uan_matches, uan_found, uan_not_found = highlight_numbers(
            uan_pdf_path, uan_numbers, output_uan, "UAN", selected_color
        )
        esic_matches, esic_found, esic_not_found = highlight_numbers(
            esic_pdf_path, esic_numbers, output_esic, "ESIC", selected_color
        )

    st.success("✅ Processing complete!")

    # ──────────────────────── Results ────────────────────────────
    st.markdown('<p class="section-label">📊 Results</p>', unsafe_allow_html=True)

    # Summary Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("UAN Found", len(uan_found))
    m2.metric("UAN Missing", len(uan_not_found))
    m3.metric("ESIC Found", len(esic_found))
    m4.metric("ESIC Missing", len(esic_not_found))

    st.write("")  # spacing

    # Tabbed details
    tab_uan, tab_esic = st.tabs(["📄 UAN Results", "📄 ESIC Results"])

    with tab_uan:
        st.markdown(f"**Total highlight matches in PDF:** {uan_matches}")
        if uan_found:
            st.dataframe(
                pd.DataFrame(uan_found, columns=["Found UAN Numbers"]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No UAN numbers were found in the PDF.")

        if uan_not_found:
            with st.expander(f"⚠️ {len(uan_not_found)} UAN numbers not found", expanded=False):
                st.dataframe(
                    pd.DataFrame(uan_not_found, columns=["Not Found UAN Numbers"]),
                    use_container_width=True,
                    hide_index=True,
                )

    with tab_esic:
        st.markdown(f"**Total highlight matches in PDF:** {esic_matches}")
        if esic_found:
            st.dataframe(
                pd.DataFrame(esic_found, columns=["Found ESIC Numbers"]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No ESIC numbers were found in the PDF.")

        if esic_not_found:
            with st.expander(f"⚠️ {len(esic_not_found)} ESIC numbers not found", expanded=False):
                st.dataframe(
                    pd.DataFrame(esic_not_found, columns=["Not Found ESIC Numbers"]),
                    use_container_width=True,
                    hide_index=True,
                )

    # ──────────────────────── Downloads ──────────────────────────
    st.divider()
    st.markdown('<p class="section-label">⬇️ Download Highlighted PDFs</p>', unsafe_allow_html=True)

    dl1, dl2 = st.columns(2)
    with dl1:
        with open(output_uan, "rb") as f:
            st.download_button(
                "⬇ Download UAN PDF",
                f,
                file_name=os.path.basename(output_uan),
                use_container_width=True,
            )
    with dl2:
        with open(output_esic, "rb") as f:
            st.download_button(
                "⬇ Download ESIC PDF",
                f,
                file_name=os.path.basename(output_esic),
                use_container_width=True,
            )
else:
    # Friendly empty state
    st.info("👆 Upload all three files above to get started.")
