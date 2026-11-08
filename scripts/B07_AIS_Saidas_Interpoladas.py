"""B.7 — Execução das seis rotinas mensais de saídas AIS (abril a setembro de 2014).

Uso:
 python B07_AIS_Saidas_Interpoladas.py --listar
 python B07_AIS_Saidas_Interpoladas.py --mes 201404 --base "DIRETORIO_DOS_DADOS"
 python B07_AIS_Saidas_Interpoladas.py --todos --base "DIRETORIO_DOS_DADOS"

O corte de lacunas AIS >72 horas NÃO é aplicado nesta etapa; pertence ao B.8.
Os módulos preservam a lógica dos processamentos 10–15 já auditados.
"""
import argparse
from pathlib import Path
import subprocess
import sys

PASTA = Path(__file__).resolve().parent / "B07_mensal"
ROTINAS = {
    "201404": "B07_10_Saidas_201404.py",
    "201405": "B07_11_Saidas_201405.py",
    "201406": "B07_12_Saidas_201406.py",
    "201407": "B07_13_Saidas_201407.py",
    "201408": "B07_14_Saidas_201408.py",
    "201409": "B07_15_Saidas_201409.py",
}

def main():
    parser = argparse.ArgumentParser(description="B.7 - saídas AIS por mês")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--listar", action="store_true")
    grupo.add_argument("--todos", action="store_true")
    grupo.add_argument("--mes", choices=sorted(ROTINAS))
    parser.add_argument("--base", type=Path, help="Diretório contendo Input/ e Output_VF/")
    args = parser.parse_args()
    if args.listar:
        for mes, nome in ROTINAS.items():
            print(f"{mes}: {nome}")
        return
    if args.base is None:
        parser.error("--base é obrigatório para executar as rotinas")
    base = args.base.expanduser().resolve()
    meses = list(ROTINAS) if args.todos else [args.mes]
    for mes in meses:
        arquivo = PASTA / ROTINAS[mes]
        print(f"Executando saídas {mes}: {arquivo.name}", flush=True)
        subprocess.run([sys.executable, str(arquivo), "--base", str(base)], check=True)

if __name__ == "__main__":
    main()
