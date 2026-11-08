"""B.5 — Conferência quantitativa da base AIS unificada.

Adaptação do código original '03 - AIS_Contar_Linhas_Arquivo_Unificado_V00.py'.
Compara a contagem da saída do B04 com os seis arquivos mensais, sem alterá-los.

Uso:
    python B05_AIS_Contar_Linhas_Unificado.py --entrada "C:/.../Input" --saida "C:/.../Output_VF"
"""
from pathlib import Path
import argparse

ARQUIVOS = [f"2014{mes:02d}.ldr" for mes in range(4, 10)]
NOME_UNIFICADO = "02 - AIS_Unificado_ID_DATAHORA_V00.ldr"


def contar_dados(caminho: Path) -> int:
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        cabecalho = next(arquivo, None)
        if cabecalho is None:
            raise ValueError(f"Arquivo vazio: {caminho}")
        return sum(1 for _ in arquivo)


def executar(entrada: Path, saida: Path) -> None:
    total_mensal = 0
    for nome in ARQUIVOS:
        n = contar_dados(entrada / nome)
        print(f"{nome}: {n:,} registros")
        total_mensal += n
    total_unificado = contar_dados(saida / NOME_UNIFICADO)
    print(f"Total mensal: {total_mensal:,}")
    print(f"Base unificada: {total_unificado:,}")
    if total_mensal != total_unificado:
        raise SystemExit(f"DIVERGÊNCIA: {total_unificado-total_mensal:+,} registros")
    print("CONFERÊNCIA APROVADA: totais coincidentes; sem perda quantitativa de linhas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, required=True, help="Pasta dos arquivos mensais")
    parser.add_argument("--saida", type=Path, required=True, help="Pasta com o arquivo gerado pelo B04")
    args = parser.parse_args()
    executar(args.entrada, args.saida)
