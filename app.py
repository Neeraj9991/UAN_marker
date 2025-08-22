import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import os
from tempfile import NamedTemporaryFile

def highlight_numbers(pdf_path, numbers, output_path, number_type):
    pdf_document = fitz.open(pdf_path)

    pages_to_keep = []
    total_matches = 0
    not_found_numbers = set(numbers)  # Track numbers that are not found
    found_numbers = set()  # Track numbers that are found

    # Process the first page separately to ensure it's highlighted and included
    first_page = pdf_document.load_page(0)
    first_page_matches = 0
    for number in numbers:
        matches = first_page.search_for(number)
        if matches:
            first_page_matches += len(matches)
            not_found_numbers.discard(number)  # Remove found number from the not_found_numbers set
            found_numbers.add(number)  # Add found number to the found_numbers set
            for match in matches:
                highlight = first_page.add_highlight_annot(match)
                highlight.set_colors(stroke=(1, 0, 0)) # RED Highlight Colour
                highlight.update()

    pages_to_keep.append(0)  # Always keep the first page
    total_matches += first_page_matches

    # Process the remaining pages
    for page_number in range(1, len(pdf_document)):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text()

        contains_number = False
        page_matches = 0
        for number in numbers:
            matches = page.search_for(number)
            if matches:
                contains_number = True
                page_matches += len(matches)
                not_found_numbers.discard(number)  # Remove found number from the not_found_numbers set
                found_numbers.add(number)  # Add found number to the found_numbers set
                for match in matches:
                    highlight = page.add_highlight_annot(match)
                    highlight.set_colors(stroke=(1, 0, 0)) # RED Highlight Colour
                    highlight.update()

        if contains_number:
            pages_to_keep.append(page_number)

        total_matches += page_matches

    st.subheader(f"Results for {number_type} Numbers")
    st.write(f"**Total {number_type} matches found:** {total_matches}")
    
    # Display found and not found numbers in tables
    found_df = pd.DataFrame(sorted(found_numbers), columns=[f"Found {number_type} Numbers"])
    not_found_df = pd.DataFrame(sorted(not_found_numbers), columns=[f"Not Found {number_type} Numbers"])

    st.write(f"### {number_type} Numbers Found")
    st.table(found_df)  # Display found numbers as a table
    
    st.write(f"### {number_type} Numbers Not Found")
    st.table(not_found_df)  # Display not found numbers as a table

    new_pdf = fitz.open()
    for page_number in pages_to_keep:
        new_pdf.insert_pdf(pdf_document, from_page=page_number, to_page=page_number)

    new_pdf.save(output_path)
    new_pdf.close()
    pdf_document.close()

st.title("UAN & ESIC Number Marker")

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

    # Get the first 3 characters of the Excel file name
    excel_basename = os.path.basename(excel_file.name)
    base_name = excel_basename[:3]

    output_uan_path = os.path.join(os.path.dirname(uan_pdf_temp_path), f"{base_name}_PF_highlighted.pdf")
    output_esic_path = os.path.join(os.path.dirname(esic_pdf_temp_path), f"{base_name}_ESIC_highlighted.pdf")

    df = pd.read_excel(excel_temp_path, skiprows=6)
    
    st.write("Columns in the Excel file:", df.columns.tolist())
    
    # Ensure correct column names
    uan_column = "UAN No."
    esic_column = "ESI No"
    if uan_column not in df.columns or esic_column not in df.columns:
        st.error(f"Columns '{uan_column}' or '{esic_column}' not found in the Excel file.")
        raise Exception(f"Columns '{uan_column}' or '{esic_column}' not found in the Excel file.")
    
    # Filter and process UAN numbers
    df = df[df[uan_column].notna() & (df[uan_column] != "EXEMPTED")]
    df[uan_column] = df[uan_column].astype(float).astype(int).astype(str).str.strip()
    uan_numbers = df[uan_column].tolist()

    # Filter and process ESIC numbers
    df = df[df[esic_column].notna() & (df[esic_column] != "EXEMPTED")]
    df[esic_column] = df[esic_column].astype(float).astype(int).astype(str).str.strip()
    esic_numbers = df[esic_column].tolist()

    # Highlight UAN numbers
    highlight_numbers(uan_pdf_temp_path, uan_numbers, output_uan_path, "UAN")

    # Highlight ESIC numbers
    highlight_numbers(esic_pdf_temp_path, esic_numbers, output_esic_path, "ESIC")

    # Download buttons for the processed PDFs
    st.subheader("Download Processed PDFs")
    col1, col2 = st.columns(2)
    with col1:
        with open(output_uan_path, "rb") as f:
            st.download_button("Download UAN Processed PDF", f, file_name=os.path.basename(output_uan_path))
    
    with col2:
        with open(output_esic_path, "rb") as f:
            st.download_button("Download ESIC Processed PDF", f, file_name=os.path.basename(output_esic_path))

