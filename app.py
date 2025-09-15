import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import os
from tempfile import NamedTemporaryFile

# Define available colors with RGB normalized format (values between 0 and 1)
HIGHLIGHT_COLORS = {
    "Yellow": (1, 1, 0),
    "Red": (1, 0, 0),
    "Green": (0, 1, 0),
    "Light Blue": (0.68, 0.85, 0.9),  # LightSkyBlue approximation
    "Dark Blue": (0, 0, 0.55)
}

def highlight_numbers(pdf_path, numbers, output_path, number_type, highlight_color):
    pdf_document = fitz.open(pdf_path)

    pages_to_keep = []
    total_matches = 0
    not_found_numbers = set(numbers)
    found_numbers = set()

    first_page = pdf_document.load_page(0)
    first_page_matches = 0
    for number in numbers:
        matches = first_page.search_for(number)
        if matches:
            first_page_matches += len(matches)
            not_found_numbers.discard(number)
            found_numbers.add(number)
            for match in matches:
                highlight = first_page.add_highlight_annot(match)
                highlight.set_colors(stroke=highlight_color)  # Dynamic Highlight Colour
                highlight.update()

    pages_to_keep.append(0)
    total_matches += first_page_matches

    for page_number in range(1, len(pdf_document)):
        page = pdf_document.load_page(page_number)
        contains_number = False
        page_matches = 0
        for number in numbers:
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

        if contains_number:
            pages_to_keep.append(page_number)

        total_matches += page_matches

    st.subheader(f"Results for {number_type} Numbers")
    st.write(f"**Total {number_type} matches found:** {total_matches}")

    found_df = pd.DataFrame(sorted(found_numbers), columns=[f"Found {number_type} Numbers"])
    not_found_df = pd.DataFrame(sorted(not_found_numbers), columns=[f"Not Found {number_type} Numbers"])

    st.write(f"### {number_type} Numbers Found")
    st.table(found_df)

    st.write(f"### {number_type} Numbers Not Found")
    st.table(not_found_df)

    new_pdf = fitz.open()
    for page_number in pages_to_keep:
        new_pdf.insert_pdf(pdf_document, from_page=page_number, to_page=page_number)

    new_pdf.save(output_path)
    new_pdf.close()
    pdf_document.close()

st.title("UAN & ESIC Number Marker")

# Highlight color selector with default Yellow
selected_color_name = st.selectbox(
    "Select Highlight Color",
    options=list(HIGHLIGHT_COLORS.keys()),
    index=0  # Default Yellow
)
selected_color = HIGHLIGHT_COLORS[selected_color_name]

uan_pdf_file = st.file_uploader("Upload PF PDF File", type=["pdf"])
esic_pdf_file = st.file_uploader("Upload ESIC PDF File", type=["pdf"])
excel_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uan_pdf_file and esic_pdf_file and excel_file:
    with NamedTemporaryFile(delete=False, suffix=".pdf") as uan_pdf_temp, NamedTemporaryFile(delete=False, suffix=".pdf") as esic_pdf_temp, NamedTemporaryFile(delete=False, suffix=".xlsx") as excel_temp:
        uan_pdf_temp.write(uan_pdf_file.getbuffer())
        esic_pdf_temp.write(esic_pdf_file.getbuffer())
        excel_temp.write(excel_file.getbuffer())
        uan_pdf_temp_path = uan_pdf_temp.name
        esic_pdf_temp_path = esic_pdf_temp.name
        excel_temp_path = excel_temp.name

    excel_basename = os.path.basename(excel_file.name)
    base_name = excel_basename[:3]

    output_uan_path = os.path.join(os.path.dirname(uan_pdf_temp_path), f"{base_name}_PF_highlighted.pdf")
    output_esic_path = os.path.join(os.path.dirname(esic_pdf_temp_path), f"{base_name}_ESIC_highlighted.pdf")

    df = pd.read_excel(excel_temp_path, skiprows=6)

    st.write("Columns in the Excel file:", df.columns.tolist())

    uan_column = "UAN No."
    esic_column = "ESI No"
    if uan_column not in df.columns or esic_column not in df.columns:
        st.error(f"Columns '{uan_column}' or '{esic_column}' not found in the Excel file.")
        raise Exception(f"Columns '{uan_column}' or '{esic_column}' not found in the Excel file.")

    df = df[df[uan_column].notna() & (df[uan_column] != "EXEMPTED")]
    df[uan_column] = df[uan_column].astype(float).astype(int).astype(str).str.strip()
    uan_numbers = df[uan_column].tolist()

    df = df[df[esic_column].notna() & (df[esic_column] != "EXEMPTED")]
    df[esic_column] = df[esic_column].astype(float).astype(int).astype(str).str.strip()
    esic_numbers = df[esic_column].tolist()

    highlight_numbers(uan_pdf_temp_path, uan_numbers, output_uan_path, "UAN", selected_color)
    highlight_numbers(esic_pdf_temp_path, esic_numbers, output_esic_path, "ESIC", selected_color)

    st.subheader("Download Processed PDFs")
    col1, col2 = st.columns(2)
    with col1:
        with open(output_uan_path, "rb") as f:
            st.download_button("Download UAN Processed PDF", f, file_name=os.path.basename(output_uan_path))

    with col2:
        with open(output_esic_path, "rb") as f:
            st.download_button("Download ESIC Processed PDF", f, file_name=os.path.basename(output_esic_path))
