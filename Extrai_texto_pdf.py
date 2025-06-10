import os
import unicodedata
import fitz  # PyMuPDF
import re

pasta_pdfs = r""
pasta_saida = os.path.join(pasta_pdfs, "textos_extraidos")
os.makedirs(pasta_saida, exist_ok=True)

def remover_acentos(texto):
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')

def formatar_texto(texto):
    # Converte o texto todo para maiúscula
    texto = texto.upper()  
    
    # Remove espaços duplicados (um espaço entre palavras)
    texto = re.sub(r'\s+', ' ', texto)
    
    # Remove quebras de linha extras e espaços antes/depois delas
    texto = re.sub(r'\n\s*\n', '\n', texto)
    
    # Remove espaços desnecessários no início e fim
    texto = texto.strip()  
    
    # Remove qualquer caractere de tabulação
    texto = re.sub(r'\t+', '', texto) 
    
    # Opcional: garantir que todos os campos chave estejam no formato "chave: valor"
    texto = re.sub(r'(\w+)(:)', r'\1\2 ', texto)

    return texto

total_pdfs = [i for i in os.listdir(pasta_pdfs) if i.lower().endswith(".pdf")]
arquivos_processados = 0

for arquivo in total_pdfs:
    caminho_pdf = os.path.join(pasta_pdfs, arquivo)
    nome_arquivo = os.path.splitext(arquivo)[0]

    try:
        doc = fitz.open(caminho_pdf)
        texto_total = ""
        for pagina in doc:
            texto_total += pagina.get_text()

        texto_sem_acentos = remover_acentos(texto_total)
        texto_formatado = formatar_texto(texto_sem_acentos)

        caminho_txt = os.path.join(pasta_saida, nome_arquivo + ".txt")
        with open(caminho_txt, "w", encoding="utf-8") as f:
            f.write(texto_formatado)

        arquivos_processados += 1
    except Exception as e:
        print(f"Erro ao processar {arquivo}: {e}")

if arquivos_processados == len(total_pdfs):
    exit(0)
else:
    exit(1)
