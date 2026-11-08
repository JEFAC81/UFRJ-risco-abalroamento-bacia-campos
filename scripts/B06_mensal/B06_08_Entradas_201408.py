"""Script 08 - entradas AIS no polígono da Bacia de Campos (201408).

Critérios: Apêndice A (vértices, domínio/imagem, segmentos e fração alfa).
Processamento por embarcação e mês. A vizinhança temporal é calculada ANTES
 do recorte espacial, para preservar o último ponto fora e o primeiro dentro.
Registros AIS originais não são modificados nem eliminados da base de entrada.

Qualificação operacional: coordenadas geográficas válidas; tempo crescente;
SOG observada e deslocamento mínimo implícito <= 30 nós; COG em [0,360).
O limite de 30 nós é um filtro operacional a validar na dissertação; NÃO
reconstrói a trajetória real e não representa prova de erro de medição.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd

PREFIXO = "08"
MES = "201408"
LIMITE_NOS = 30.0
TOL = 1e-10

# Longitude x latitude, sequência P1-P6, conforme tabela de vértices do Apêndice A.
VERTICES = np.array([
    [-39.2250, -21.9083], [-39.5750, -21.5916],
    [-40.3750, -22.1200], [-40.9400, -22.7000],
    [-41.0550, -23.0417], [-40.2400, -22.9500],
], dtype=float)


def interioridade(lon, lat):
    """Determina limites inferior/superior na longitude (domínio/imagem)."""
    lon, lat = np.asarray(lon, dtype=float), np.asarray(lat, dtype=float)
    inferior = np.full(lon.shape, np.inf)
    superior = np.full(lon.shape, -np.inf)
    for i in range(6):
        xa, ya = VERTICES[i]
        xb, yb = VERTICES[(i + 1) % 6]
        aplicavel = (np.isfinite(lon) & (lon >= min(xa, xb) - TOL)
                     & (lon <= max(xa, xb) + TOL))
        y_aresta = ya + (yb - ya) * (lon - xa) / (xb - xa)
        inferior = np.where(aplicavel, np.minimum(inferior, y_aresta), inferior)
        superior = np.where(aplicavel, np.maximum(superior, y_aresta), superior)
    return (np.isfinite(lat) & np.isfinite(inferior)
            & (lat >= inferior - TOL) & (lat <= superior + TOL))


def intersecao_segmentos(xa, ya, xb, yb):
    """Interseção entre segmento AIS AB e aresta R, com alfa/beta em [0,1]."""
    dx, dy = xb - xa, yb - ya
    solucoes = []
    for i in range(6):
        xr, yr = VERTICES[i]
        xs, ys = VERTICES[(i + 1) % 6]
        ex, ey = xs - xr, ys - yr
        det = dx * ey - dy * ex
        if abs(det) <= TOL:
            continue
        qx, qy = xr - xa, yr - ya
        alfa = (qx * ey - qy * ex) / det
        beta = (qx * dy - qy * dx) / det
        if -TOL <= alfa <= 1 + TOL and -TOL <= beta <= 1 + TOL:
            solucoes.append((float(np.clip(alfa, 0, 1)), f"R{i + 1}"))
    if not solucoes:
        return None
    # Em vértices pode haver duas interseções equivalentes: menor alfa.
    return min(solucoes, key=lambda item: item[0])


def rumo_circular(inicial, final, alfa):
    delta = ((final - inicial + 180.0) % 360.0) - 180.0
    return (inicial + alfa * delta) % 360.0


def velocidade_implicita_nos(lat0, lon0, lat1, lon1, segundos):
    """Menor velocidade média compatível com as posições: distância ortodrômica/tempo."""
    a0, o0, a1, o1 = np.radians([lat0, lon0, lat1, lon1])
    h = np.sin((a1-a0)/2)**2 + np.cos(a0)*np.cos(a1)*np.sin((o1-o0)/2)**2
    distancia_m = 2 * 6371008.8 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))
    return distancia_m / segundos * (3600 / 1852)


def main(base: Path):
    ENTRADA = base / "Input" / "201408.ldr"
    SAIDA = base / "Output_VF"
    if not ENTRADA.is_file():
        raise FileNotFoundError(f"Arquivo AIS não encontrado: {ENTRADA}")
    SAIDA.mkdir(exist_ok=True, parents=True)
    df = pd.read_csv(ENTRADA, sep="|", dtype=str, encoding="utf-8-sig", low_memory=False)
    originais = df.columns.tolist()
    obrigatorias = ["ID_EMB", "TIPO_EMB", "LONGITUDE_EMB", "LATITUDE_EMB",
                    "DATAHORA_EMB", "VELOCIDADE_EMB", "RUMO_EMB"]
    faltantes = [c for c in obrigatorias if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes: {faltantes}")

    for c in ["LONGITUDE_EMB", "LATITUDE_EMB", "VELOCIDADE_EMB", "RUMO_EMB"]:
        df[c] = pd.to_numeric(df[c].str.replace(",", ".", regex=False), errors="coerce")
    df["DATAHORA_EMB"] = pd.to_datetime(df["DATAHORA_EMB"], dayfirst=True, errors="coerce")
    df.sort_values(["ID_EMB", "DATAHORA_EMB"], kind="stable", inplace=True)

    # NÃO recortar os pontos externos: obter pares consecutivos primeiro.
    # Ponto inválido permanece como vizinho e REPROVA o par, sem unir pontos não consecutivos.
    pareados = ["LATITUDE_EMB", "LONGITUDE_EMB", "VELOCIDADE_EMB", "RUMO_EMB", "DATAHORA_EMB"]
    for c in pareados:
        df[c + "_Prox"] = df.groupby("ID_EMB", sort=False)[c].shift(-1)

    df["DentroPoligono"] = interioridade(df["LONGITUDE_EMB"].to_numpy(), df["LATITUDE_EMB"].to_numpy())
    df["DentroPoligono_Prox"] = interioridade(df["LONGITUDE_EMB_Prox"].to_numpy(), df["LATITUDE_EMB_Prox"].to_numpy())
    candidatos = df.loc[(~df["DentroPoligono"]) & df["DentroPoligono_Prox"]].copy()
    candidatos["EVENTO"] = "ENTRADA"

    aceitos, auditoria = [], []
    for _, row in candidatos.iterrows():
        r = row.to_dict()
        motivo = None
        coords = [r["LATITUDE_EMB"], r["LONGITUDE_EMB"], r["LATITUDE_EMB_Prox"], r["LONGITUDE_EMB_Prox"]]
        vel = [r["VELOCIDADE_EMB"], r["VELOCIDADE_EMB_Prox"]]
        rumos = [r["RUMO_EMB"], r["RUMO_EMB_Prox"]]
        t0, t1 = r["DATAHORA_EMB"], r["DATAHORA_EMB_Prox"]
        vel_implicita = np.nan
        if any(pd.isna(v) for v in coords + vel + rumos + [t0, t1]):
            motivo = "CAMPOS_AIS_AUSENTES_OU_INVALIDOS"
        elif not (abs(coords[0]) <= 90 and abs(coords[2]) <= 90
                  and abs(coords[1]) <= 180 and abs(coords[3]) <= 180):
            motivo = "COORDENADAS_FORA_DOS_LIMITES_GEOGRAFICOS"
        elif t1 <= t0:
            motivo = "TEMPO_NAO_CRESCENTE"
        elif not all(0 <= v <= LIMITE_NOS for v in vel):
            motivo = "VELOCIDADE_AIS_FORA_DE_0_30_NOS"
        elif not all(0 <= v < 360 for v in rumos):
            motivo = "RUMO_AIS_FORA_DE_0_360_GRAUS"
        else:
            dt_s = (t1 - t0).total_seconds()
            vel_implicita = velocidade_implicita_nos(
                coords[0], coords[1], coords[2], coords[3], dt_s)
            if vel_implicita > LIMITE_NOS:
                motivo = "VELOCIDADE_IMPLICITA_SUPERIOR_30_NOS"
            else:
                inter = intersecao_segmentos(coords[1], coords[0], coords[3], coords[2])
                if inter is None:
                    motivo = "INTERSECAO_NAO_ENCONTRADA"

        if motivo is None:
            alfa, aresta = inter
            r["DATAHORA_ENTRADA"] = (t0 + pd.to_timedelta(alfa * dt_s, unit="s")).strftime("%d-%m-%Y %H:%M:%S")
            r["VELOCIDADE_ENTRADA"] = round(vel[0] + alfa * (vel[1] - vel[0]), 2)
            r["RUMO_ENTRADA"] = int(round(rumo_circular(rumos[0], rumos[1], alfa))) % 360
            r["ARESTAS"] = aresta
            aceitos.append(r)
            situacao = "ACEITO"
        else:
            situacao = motivo

        auditoria.append({"ID_EMB": r["ID_EMB"], "DATAHORA_EMB": str(t0),
                          "DATAHORA_EMB_Prox": str(t1), "SITUACAO": situacao,
                          "VELOCIDADE_IMPLICITA_NOS": round(vel_implicita, 2) if np.isfinite(vel_implicita) else ""})

    colunas = originais + [c + "_Prox" for c in pareados] + [
        "DentroPoligono", "DentroPoligono_Prox", "EVENTO", "DATAHORA_ENTRADA",
        "VELOCIDADE_ENTRADA", "RUMO_ENTRADA", "ARESTAS"]
    out = pd.DataFrame(aceitos, columns=colunas)
    caminho_ldr = SAIDA / f"{PREFIXO} - Entradas_Interpoladas_{MES}_V00.ldr"
    caminho_csv = SAIDA / f"{PREFIXO} - Entradas_Interpoladas_{MES}_V00.csv"
    caminho_auditoria = SAIDA / f"{PREFIXO} - Auditoria_Entradas_{MES}_V00.ldr"
    out.to_csv(caminho_ldr, sep=";", index=False, encoding="utf-8-sig")
    out.to_csv(caminho_csv, sep=";", index=False, encoding="utf-8-sig")
    audit = pd.DataFrame(auditoria, columns=["ID_EMB", "DATAHORA_EMB", "DATAHORA_EMB_Prox", "SITUACAO", "VELOCIDADE_IMPLICITA_NOS"])
    audit.to_csv(caminho_auditoria, sep=";", index=False, encoding="utf-8-sig")
    print("Registros AIS de entrada:", len(df))
    print("Candidatos fora -> dentro:", len(candidatos))
    print("Entradas válidas:", len(out))
    print("Rejeições por critério:")
    print(audit.loc[audit["SITUACAO"] != "ACEITO", "SITUACAO"].value_counts().to_string())
    print("Arquivos de saída:", caminho_ldr, caminho_csv, caminho_auditoria, sep="\n")
    print("NOTA: pares que cruzam a fronteira entre meses requerem conferência complementar.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interpolação mensal de entradas AIS")
    parser.add_argument("--base", required=True, type=Path,
                        help="Diretório de trabalho contendo Input/ e Output_VF/")
    args = parser.parse_args()
    main(args.base.expanduser().resolve())
