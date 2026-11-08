"""Código B.3 — Contagem de registros dos arquivos AIS mensais.

Conta linhas de dados, excluindo a primeira linha (cabeçalho), em cada arquivo
mensal de abril a setembro de 2014. Não altera os arquivos de entrada.

Antes de executar, configure 'diretorio_entrada' para a pasta que contém os
arquivos AIS autorizados no seu ambiente local.
"""

import os

# Diretório dos arquivos mensais AIS (configurar somente no ambiente local).
diretorio_entrada = r"caminho/para/dados_ais_mensais"

# Arquivos mensais analisados.
arquivos = [
    "201404.ldr",
    "201405.ldr",
    "201406.ldr",
    "201407.ldr",
    "201408.ldr",
    "201409.ldr",
]

# Dicionário para armazenar resultados.
contagem_linhas = {}
total_linhas = 0

for arquivo in arquivos:
    caminho = os.path.join(diretorio_entrada, arquivo)

    with open(caminho, "r", encoding="utf-8") as f:
        num_linhas = sum(1 for linha in f) - 1  # Desconsidera o cabeçalho.

    contagem_linhas[arquivo] = num_linhas
    total_linhas += num_linhas

print("\nContagem de linhas por arquivo:")
for nome, qtd in contagem_linhas.items():
    print(f"{nome}: {qtd:,} linhas")

print(f"\nTotal geral: {total_linhas:,} linhas")
