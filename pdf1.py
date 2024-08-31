import PyPDF2

# Open the PDF file
with open('cctobtc.pdf', 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        print(page.extract_text())
