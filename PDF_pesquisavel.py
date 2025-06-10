import os
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfMerger
from io import BytesIO

# Caminhos
pasta_pdfs = r""
pasta_saida = r""
poppler_path = r""
pytesseract.pytesseract.tesseract_cmd = r""

# Garante que a pasta de saída exista
os.makedirs(pasta_saida, exist_ok=True)

# Lista arquivos PDF
arquivos_pdf = [arq for arq in os.listdir(pasta_pdfs) if arq.lower().endswith(".pdf")]

for arquivo in arquivos_pdf:
    caminho_pdf = os.path.join(pasta_pdfs, arquivo)
    nome_base = os.path.splitext(arquivo)[0]

    try:
        paginas = convert_from_path(caminho_pdf, dpi=300, poppler_path=poppler_path)
    except Exception as e:
        print(f"Erro ao converter {arquivo}: {e}")
        continue

    merger = PdfMerger()
    for i, pagina in enumerate(paginas):
        # OCR na imagem e retorno em PDF
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(pagina, extension='pdf', lang='por')
        pdf_stream = BytesIO(pdf_bytes)
        merger.append(pdf_stream)

    # Salva PDF final pesquisável
    caminho_saida_pdf = os.path.join(pasta_saida, f"{nome_base}.pdf")
    with open(caminho_saida_pdf, "wb") as f_out:
        merger.write(f_out)
        merger.close()

    print(f"PDF pesquisável criado: {arquivo}")
