import pdfplumber

# Open the PDF file
with pdfplumber.open("pap.pdf") as pdf:
    # Loop through all pages
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()

        print(f"\n--- Page {i + 1} ---")
        print(text)