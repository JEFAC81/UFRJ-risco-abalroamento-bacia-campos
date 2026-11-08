"""B.6 — Execução das seis rotinas mensais de entradas AIS (abril a setembro de 2014).

Uso:
 python B06_AIS_Entradas_Interpoladas.py --listar
 python B06_AIS_Entradas_Interpoladas.py --mes 201404 --base "DIRETORIO_DOS_DADOS"
 python B06_AIS_Entradas_Interpoladas.py --todos --base "DIRETORIO_DOS_DADOS"

O corte de lacunas AIS >72 horas NÃO é aplicado nesta etapa; pertence ao B.8.
Os módulos preservam o processamento 04–09 já auditado.
"""
import argparse
from pathlib import Path
import subprocess
import sys

PASTA = Path(__file__).resolve().parent / "B06_mensal"
ROTINAS = {
    "201404": "B06_04_Entradas_201404.py",
    "201405": "B06_05_Entradas_201405.py",
    "201406": "B06_06_Entradas_201406.py",
    "201407": "B06_07_Entradas_201407.py",
    "201408": "B06_08_Entradas_201408.py",
    "201409": "B06_09_Entradas_201409.py",
}

def main():
    parser = argparse.ArgumentParser(description="B.6 - entradas AIS por mês")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--listar", action="store_true")
    group.add_argument("--todos", action="store_true")
    group.add_argument("--mes", choices=sorted(ROTINAS))
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
        print(f"Executando entradas {mes}: {arquivo.name}", flush=True)
        subprocess.run([sys.executable, str(arquivo), "--base", str(base)], check=True)

if __name__ == "__main__":
    main()
