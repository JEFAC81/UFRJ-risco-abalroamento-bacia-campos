"""B.4 — Unificação dos arquivos AIS mensais (abril a setembro de 2014).

Adaptação do código original '02 - AIS_Unificado_ID_DATAHORA_V00.py'.
Mantém todas as linhas, reúne os seis meses e ordena por ID_EMB/DATAHORA_EMB.
Não aplica filtros cinemáticos, geográficos ou de lacunas AIS.

Uso:
    python B04_AIS_Unificar_Arquivos.py --entrada "C:/.../Input" --saida "C:/.../Output_VF"
"""
from pathlib import Path
import argparse
import pandas as pd

ARQUIVOS = [f"2014{mes:02d}.ldr" for mes in range(4, 10)]
NOME_SAIDA = "02 - AIS_Unificado_ID_DATAHORA_V00.ldr"


def executar(diretorio_entrada: Path, diretorio_saida: Path) -> Path:
    fontes = [diretorio_entrada / nome for nome in ARQUIVOS]
    faltantes = [str(f) for f in fontes if not f.is_file()]
    if faltantes:
        raise FileNotFoundError("Arquivos mensais não encontrados:\n" + "\n".join(faltantes))

    tabelas = []
    colunas = None
    for fonte in fontes:
        df = pd.read_csv(fonte, sep="|", dtype=str, keep_default_na=False)
        if colunas is None:
            colunas = df.columns.tolist()
            for campo in ("ID_EMB", "DATAHORA_EMB"):
                if campo not in colunas:
                    raise ValueError(f"Coluna obrigatória ausente: {campo}")
        elif df.columns.tolist() != colunas:
            raise ValueError(f"Cabeçalho diferente no arquivo: {fonte.name}")
        print(f"{fonte.name}: {len(df):,} registros")
        tabelas.append(df)

    unificada = pd.concat(tabelas, ignore_index=True)
    unificada.sort_values(["ID_EMB", "DATAHORA_EMB"], kind="stable", inplace=True)
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    destino = diretorio_saida / NOME_SAIDA
    if destino.exists():
        raise FileExistsError(f"Saída já existe; não será sobrescrita: {destino}")
    unificada.to_csv(destino, sep="|", index=False)
    print(f"Total de registros unificados: {len(unificada):,}")
    print(f"Arquivo gerado: {destino}")
    return destino


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", type=Path, required=True, help="Pasta dos seis arquivos AAAAMM.ldr")
    parser.add_argument("--saida", type=Path, required=True, help="Pasta de destino da base unificada")
    args = parser.parse_args()
    executar(args.entrada, args.saida)
