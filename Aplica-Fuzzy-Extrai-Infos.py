import os
import re
from unidecode import unidecode
from thefuzz import fuzz

# Função fuzzy para comparar textos
def fuzzy_match(linha, termos, threshold=90):
    for termo in termos:
        if fuzz.partial_ratio(unidecode(linha).upper(), unidecode(termo).upper()) >= threshold:
            return True
    return False

# Função para extrair as informações da nota
def extrair_info_nota(texto_ocr):
    texto = unidecode(texto_ocr).upper()
    linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]

    info = {
        "nome_prestador": None,
        "cnpj_prestador": None,
        "numero_nota": None,
        "data_emissao": None,
        "valor_total": None,
        "descricao_nota": None,
        "vencimento": None
    }

    # Dicionário de possíveis rótulos para cada campo
    rótulos = {
        "nome_prestador": [
            'NOME EMPRESARIAL', 'PRESTADOR DE SERVIÇOS', 'NOME PRESTADOR', 'NOME FANTASIA', 'NOME/RAZAO SOCIAL',
            'RAZAO SOCIAL', 'NOME DO PRESTADOR', 'PRESTADOR', 'EMPRESA PRESTADORA', 'EMITENTE', 'FORNECEDOR',
            'NOME DA EMPRESA', 'EMPRESA CONTRATADA'
        ],
        "cnpj_prestador": [
            'CNPJ', 'CPF/CNPJ', 'CNPJ PRESTADOR', 'CNPJ EMITENTE', 'CNPJ DA EMPRESA', 'DOCUMENTO DO PRESTADOR',
            'NUMERO DO CNPJ', 'CNPJ DO FORNECEDOR'
        ],
        "numero_nota": [
            'NUMERO / SERIE', 'NOTA FISCAL ELETRONICA', 'RPS Nº', 'NUMERO DA NOTA', 'NUMERO DA NF-E', 'NF-E Nº',
            'NUMERO DO DOCUMENTO', 'NUM. NOTA', 'NR. DO DOCUMENTO'
        ],
        "data_emissao": [
            'DATA E HORA DA EMISSAO', 'EMISSAO', 'DATA DE EMISSAO', 'DATA DO DOCUMENTO', 'DATA DA NOTA',
            'EMISSAO DA NOTA'
        ],
        "valor_total": [
            'VALOR TOTAL DO SERVICO', 'VALOR LIQUIDO R$', 'VALOR R$', 'VALOR DO DOCUMENTO R$', 'VALOR TOTAL',
            'VALOR LIQUIDO', 'VALOR PAGO', 'VALOR BRUTO', 'VALOR DA NOTA', 'TOTAL DA NOTA FISCAL'
        ],
        "descricao_nota": [
            'DISCRIMINACAO DO SERVICO', 'DISCRIMINACAO', 'DESCRICAO', 'DESCRICAO DO PRODUTO', 'DESCRICAO DO SERVICO',
            'DESCRICAO DOS PRODUTOS/SERVICOS', 'TEXTO DE RESPONSABILIDADE DO CEDENTE', 'DESCRICAO DOS SERVICOS',
            'DESCRICAO DOS PRODUTOS', 'TOTAL DA NOTA FISCAL'
        ],
        "vencimento": [
            'VENCIMENTO:', 'VENCIMENTO: ', 'VENCIMENTO', 'VENCTO.', 'VENCTO: ',
            'VENCTO:', 'VENCTO. '
        ]
    }

    # Percorrendo as linhas e fazendo o match fuzzy para cada campo
    for i, linha in enumerate(linhas):
        if fuzzy_match(linha, rótulos["nome_prestador"]) and not info["nome_prestador"]:
            for rotulo in rótulos["nome_prestador"]:
                if rotulo in linha:
                    partes = linha.split(rotulo, 1)
                    if len(partes) > 1:
                        nome_bruto = partes[1].strip()
                        nome_limpo = re.split(r'\b(endereco|bairro|municipio|cpf/cnpj|cnpj|nota fiscal|nome fantasia)\b', nome_bruto, flags=re.IGNORECASE)[0]
                        info["nome_prestador"] = nome_limpo.strip(" -:\n")
                        break
            if not info["nome_prestador"] and i+1 < len(linhas):
                info["nome_prestador"] = linhas[i+1].strip()

        cnpj_match = re.search(r'\d{2}[.\s]?\d{3}[.\s]?\d{3}[\/\s]?\d{4}[-\s]?\d{2}', linha)
        if cnpj_match and not info["cnpj_prestador"]:
            info["cnpj_prestador"] = cnpj_match.group().replace(" ", "")

        if fuzzy_match(linha, rótulos["numero_nota"]) and not info["numero_nota"]:
            numero_match = re.search(r'\d{6,12}', linha)
            if numero_match:
                info["numero_nota"] = numero_match.group()
            elif i+1 < len(linhas):
                numero_match = re.search(r'\d{6,12}', linhas[i+1])
                if numero_match:
                    info["numero_nota"] = numero_match.group()

        if fuzzy_match(linha, rótulos["data_emissao"]) and not info["data_emissao"]:
            data_match = re.search(r'\d{2}/\d{2}/\d{4}', linha)
            if data_match:
                info["data_emissao"] = data_match.group()

        if fuzzy_match(linha, rótulos["valor_total"]) and not info["valor_total"]:
            valor_match = re.search(r'R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?', linha)
            if valor_match:
                info["valor_total"] = valor_match.group()

        if fuzzy_match(linha, rótulos["vencimento"]) and not info["vencimento"]:
            venc_match = re.search(r'\d{2}/\d{2}/\d{4}', linha)
            if venc_match:
                info["vencimento"] = venc_match.group()
            elif i+1 < len(linhas):
                venc_match = re.search(r'\d{2}/\d{2}/\d{4}', linhas[i+1])
                if venc_match:
                    info["vencimento"] = venc_match.group()

        if fuzzy_match(linha, rótulos["descricao_nota"]) and not info["descricao_nota"]:
            descricao = []

            # Se tiver conteúdo na mesma linha do rótulo
            for rotulo in rótulos["descricao_nota"]:
                if rotulo in linha:
                    partes = linha.split(rotulo, 1)
                    if len(partes) > 1:
                        linha_inicio = partes[1].strip()
                        descricao.append(linha_inicio)
                        

            # Termos que indicam o fim da descrição
            delimitadores_fim = [
                "VALOR TOTAL", "INSS", "IRRF", "CSLL", "COFINS", "PIS", "CÓDIGO DO SERVIÇO",
                "BASE DE CÁLCULO", "ALIQUOTA", "VALOR DO ISS", "DESCONTO", "MUNICIPIO", 
                "OUTRAS INFORMACOES", "FORMA DE PAGAMENTO", "HTTPS", "NATUREZA DE OPERACAO"
            ]

            # Continuar buscando nas próximas linhas
            for j in range(i+1, len(linhas)):
                linha_atual = linhas[j].strip()
                if any(delim in linha_atual.upper() for delim in delimitadores_fim):
                    break
                descricao.append(linha_atual)

            # Junta tudo e faz um corte se ainda assim for muito longo
            descricao_final = ' '.join(descricao).strip()
            
            # Corta a descrição se pegar muito lixo no final
            for delim in delimitadores_fim:
                index = descricao_final.upper().find(delim)
                if index != -1:
                    descricao_final = descricao_final[:index].strip()
                    break

            info["descricao_nota"] = descricao_final


    return info

# Função para limpar os ":" do conteúdo extraído, trocando por "-" para não dar conflito no AE
def limpar_conteudo(texto):
    return texto.replace(":", " - ") if texto else texto

# Função para gerar texto estruturado
def gerar_texto_estruturado(info, original):
    partes = [
        f"prestadorNome: {limpar_conteudo(info.get('nome_prestador')) or 'Não encontrado'}",
        f"CNPJ: {limpar_conteudo(info.get('cnpj_prestador')) or 'Não encontrado'}",
        f"NrNota: {limpar_conteudo(info.get('numero_nota')) or 'Não encontrado'}",
        f"dataEmissao: {limpar_conteudo(info.get('data_emissao')) or 'Não encontrada'}",
        f"vencimento: {limpar_conteudo(info.get('vencimento')) or 'Não encontrada'}",
        f"valor: {limpar_conteudo(info.get('valor_total')) or 'Não encontrado'}",
        f"discriminacao: {limpar_conteudo(info.get('descricao_nota')) or 'Não encontrada'}",
        "\n--- Conteúdo Original Abaixo ---\n",
        original
    ]
    return "\n".join(partes)

def processar_pasta(pasta_txt):
    for nome_arquivo in os.listdir(pasta_txt):
        # só .txt e que NÃO sejam _tratado.txt
        if (not nome_arquivo.lower().endswith('.txt')
            or nome_arquivo.lower().endswith('_tratado.txt')):
            continue

        caminho_entrada = os.path.join(pasta_txt, nome_arquivo)
        with open(caminho_entrada, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        infos = extrair_info_nota(conteudo)
        novo_conteudo = gerar_texto_estruturado(infos, conteudo)

        nome_base, _ = os.path.splitext(nome_arquivo)
        nome_tratado = f"{nome_base}_tratado.txt"
        caminho_tratado = os.path.join(pasta_txt, nome_tratado)

        # 'w' cria se não existir, ou sobrescreve se existir
        with open(caminho_tratado, 'w', encoding='utf-8') as f:
            f.write(novo_conteudo)

        print(f"Arquivo salvo: {nome_tratado}")

# Caminho da pasta com os arquivos .txt
pasta = r'N:\RPA\RPA Unimed\Projetos\GTIF\NUGO\PROJETO-NOTAS-NUGO\Notas_Extraidas_email\PDFs_Nao_pesquisaveis\pdfs_transformados_pesquisaveis\textos_extraidos'
processar_pasta(pasta)
