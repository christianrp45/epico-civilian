from __future__ import annotations
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

COLUMN_MAP = {
    "Setor": "Setor",
    "Toneladas": "Toneladas",
    "Viagens": "Viagens",
    "Qtd. Viagens": "Viagens",
    "Qtd Viagens": "Viagens",
    "Km Produtivo": "Km Produtivo",
    "Km Improdutivo": "Km Improdutivo",
    "Km Total": "Km Total",
    "Combústivel": "Combustível",
    "Combustivel": "Combustível",
    "Horas Trabalhadas": "Horas Trabalhadas",
    "Horas Produtivas": "Horas Produtivas",
    "Horas Improdutivas": "Horas Improdutivas",
    "Horas Extras": "Horas Extras",
    "Data Execucao": "Data Execucao",
    "Dia da Semana": "Dia da Semana",
    "Turno": "Turno",
    "Unidade": "Unidade",
    "Operação": "Operação",
    "Identificador": "Identificador",
}

REQUIRED_CANONICAL = [
    "Setor",
    "Toneladas",
    "Viagens",
    "Km Produtivo",
    "Km Improdutivo",
    "Km Total",
    "Combustível",
    "Horas Trabalhadas",
    "Horas Produtivas",
    "Horas Improdutivas",
    "Horas Extras",
]

def format_number_br(value: Any, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "-"
    txt = f"{value:,.{digits}f}"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

def format_horas_hhmmss(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "-"
    total_seconds = int(round(float(value) * 3600))
    sign = "-" if total_seconds < 0 else ""
    total_seconds = abs(total_seconds)
    horas = total_seconds // 3600
    minutos = (total_seconds % 3600) // 60
    segundos = total_seconds % 60
    return f"{sign}{horas:02d}:{minutos:02d}:{segundos:02d}"

def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = (
        out.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.replace("\u00a0", " ", regex=False)
        .str.strip()
    )
    return out.rename(columns={c: COLUMN_MAP.get(c, c) for c in out.columns})

def _to_float_ptbr(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    s = series.astype(str).str.strip()
    s = s.replace({"nan": np.nan, "None": np.nan, "": np.nan})

    has_comma = s.str.contains(",", regex=False, na=False)

    s = pd.Series(
        np.where(
            has_comma,
            s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
            s,
        ),
        index=series.index,
    )

    return pd.to_numeric(s, errors="coerce")

def _to_hours(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    s = series.astype(str).str.strip()
    s = s.replace({"nan": np.nan, "None": np.nan, "": np.nan})

    numeric_try = pd.to_numeric(s.str.replace(",", ".", regex=False), errors="coerce")
    if numeric_try.notna().mean() > 0.8:
        return numeric_try.astype(float)

    td = pd.to_timedelta(s, errors="coerce")
    return td.dt.total_seconds() / 3600.0

def _normalize_ton_scale(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    med = s.dropna().median() if s.notna().any() else np.nan

    # Corrige casos em que a tonelada vem 1000x maior
    if pd.notna(med) and med > 100:
        return s / 1000.0
    return s

def load_dataset(file_obj: Any) -> pd.DataFrame:
    if isinstance(file_obj, (str, Path)):
        path = Path(file_obj)
        if path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(path)
        elif path.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(path, sep=";", encoding="latin1")
            except Exception:
                df = pd.read_csv(path)
        else:
            raise ValueError("Formato nao suportado.")
    else:
        name = getattr(file_obj, "name", "").lower()
        if name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_obj)
        else:
            try:
                df = pd.read_csv(file_obj, sep=";", encoding="latin1")
            except Exception:
                file_obj.seek(0)
                df = pd.read_csv(file_obj)

    return _normalize_headers(df)

def prepare_base(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    missing = [c for c in REQUIRED_CANONICAL if c not in out.columns]
    if missing:
        raise ValueError(f"Colunas obrigatorias ausentes: {missing}")

    setor_num = pd.to_numeric(out["Setor"], errors="coerce")
    out = out[setor_num.notna()].copy()
    setor_num = pd.to_numeric(out["Setor"], errors="coerce")
    out = out[setor_num > 0].copy()
    out["Setor"] = pd.to_numeric(out["Setor"], errors="coerce").astype(int).astype(str).str.zfill(4)

    for col in ["Toneladas", "Viagens", "Km Produtivo", "Km Improdutivo", "Km Total", "Combustível"]:
        out[col] = _to_float_ptbr(out[col])

    # CORREÇÃO PRINCIPAL
    out["Toneladas"] = _normalize_ton_scale(out["Toneladas"])

    for col in ["Horas Trabalhadas", "Horas Produtivas", "Horas Improdutivas", "Horas Extras"]:
        out[col] = _to_hours(out[col])

    out["Toneladas"] = out["Toneladas"].round(3)
    out["Produtividade (t/h)"] = out["Toneladas"] / out["Horas Trabalhadas"].replace(0, np.nan)
    out["% Km Improdutivo"] = out["Km Improdutivo"] / out["Km Total"].replace(0, np.nan)
    out["L/ton"] = out["Combustível"] / out["Toneladas"].replace(0, np.nan)
    out["Km/L calc"] = out["Km Total"] / out["Combustível"].replace(0, np.nan)
    out["Ton/Viagem calc"] = out["Toneladas"] / out["Viagens"].replace(0, np.nan)

    out["Linha válida"] = (
        (out["Toneladas"].fillna(0) > 0)
        & (out["Km Total"].fillna(0) > 0)
        & (out["Horas Trabalhadas"].fillna(0) > 0)
    )

    return out

def compute_dashboard_data(df: pd.DataFrame, jornada_meta: float = 7.33) -> dict[str, Any]:
    base = prepare_base(df)
    consolidavel = base[base["Linha válida"]].copy()

    if "Data Execucao" in consolidavel.columns:
        consolidavel["_chave_dia"] = consolidavel["Data Execucao"].astype(str).str.strip()
    elif "Dia da Semana" in consolidavel.columns:
        consolidavel["_chave_dia"] = consolidavel["Dia da Semana"].astype(str).str.strip()
    else:
        consolidavel["_chave_dia"] = "DIA_UNICO"

    rotas = consolidavel.groupby("Setor", dropna=False).agg(
        Toneladas=("Toneladas", "sum"),
        Viagens=("Viagens", "sum"),
        **{
            "Km Produtivo": ("Km Produtivo", "sum"),
            "Km Improdutivo": ("Km Improdutivo", "sum"),
            "Km Total": ("Km Total", "sum"),
            "Combustível": ("Combustível", "sum"),
            "Horas Trabalhadas": ("Horas Trabalhadas", "sum"),
            "Horas Produtivas": ("Horas Produtivas", "sum"),
            "Horas Improdutivas": ("Horas Improdutivas", "sum"),
            "Horas Extras": ("Horas Extras", "sum"),
            "Dias Encontrados": ("_chave_dia", "nunique"),
        },
    ).reset_index()

    rotas["Dias Encontrados"] = rotas["Dias Encontrados"].fillna(1)
    rotas.loc[rotas["Dias Encontrados"] <= 0, "Dias Encontrados"] = 1

    for col in [
        "Toneladas", "Viagens", "Km Produtivo", "Km Improdutivo", "Km Total",
        "Combustível", "Horas Trabalhadas", "Horas Produtivas", "Horas Improdutivas", "Horas Extras"
    ]:
        rotas[col] = rotas[col] / rotas["Dias Encontrados"]

    rotas["Toneladas"] = rotas["Toneladas"].round(3)
    rotas["Produtividade (t/h)"] = rotas["Toneladas"] / rotas["Horas Trabalhadas"].replace(0, np.nan)
    rotas["% Km Improdutivo"] = rotas["Km Improdutivo"] / rotas["Km Total"].replace(0, np.nan)
    rotas["L/ton"] = rotas["Combustível"] / rotas["Toneladas"].replace(0, np.nan)
    rotas["Km/L"] = rotas["Km Total"] / rotas["Combustível"].replace(0, np.nan)
    rotas["Ton/Viagem"] = rotas["Toneladas"] / rotas["Viagens"].replace(0, np.nan)

    def classificar(h):
        if pd.isna(h):
            return "Sem dado"
        if h < jornada_meta - 0.5:
            return "Abaixo da meta"
        if h > jornada_meta + 0.5:
            return "Acima da meta"
        return "Equilibrada"

    rotas["Classificação Jornada"] = rotas["Horas Trabalhadas"].apply(classificar)

    toneladas_total = rotas["Toneladas"].sum()
    horas_total = rotas["Horas Trabalhadas"].sum()
    km_total = rotas["Km Total"].sum()
    combustivel_total = rotas["Combustível"].sum()

    kpis = {
        "toneladas_total": toneladas_total,
        "horas_total": horas_total,
        "produtividade_media": toneladas_total / horas_total if horas_total else np.nan,
        "km_total": km_total,
        "combustivel_total": combustivel_total,
        "litros_por_ton": combustivel_total / toneladas_total if toneladas_total else np.nan,
        "km_por_litro": km_total / combustivel_total if combustivel_total else np.nan,
        "rotas_necessarias": horas_total / jornada_meta if jornada_meta else np.nan,
        "amplitude_rotas": rotas["Horas Trabalhadas"].max() - rotas["Horas Trabalhadas"].min() if len(rotas) else np.nan,
        "ton_viagem_media": rotas["Ton/Viagem"].mean() if len(rotas) else np.nan,
        "horas_extras_total": rotas["Horas Extras"].sum() if len(rotas) else np.nan,
        "km_improdutivo_pct_total": rotas["Km Improdutivo"].sum() / rotas["Km Total"].sum() if rotas["Km Total"].sum() else np.nan,
    }

    medias = {
        "media_toneladas": rotas["Toneladas"].mean() if len(rotas) else np.nan,
        "media_horas": rotas["Horas Trabalhadas"].mean() if len(rotas) else np.nan,
        "media_produtividade": rotas["Produtividade (t/h)"].mean() if len(rotas) else np.nan,
        "media_km_total": rotas["Km Total"].mean() if len(rotas) else np.nan,
        "media_combustivel": rotas["Combustível"].mean() if len(rotas) else np.nan,
        "media_l_ton": rotas["L/ton"].mean() if len(rotas) else np.nan,
        "media_km_improd_pct": rotas["% Km Improdutivo"].mean() if len(rotas) else np.nan,
        "media_ton_viagem": rotas["Ton/Viagem"].mean() if len(rotas) else np.nan,
        "media_viagens": rotas["Viagens"].mean() if len(rotas) else np.nan,
    }

    diagnostico = []
    if not rotas.empty:
        pesada = rotas.sort_values("Horas Trabalhadas", ascending=False).iloc[0]
        leve = rotas.sort_values("Horas Trabalhadas", ascending=True).iloc[0]
        diagnostico.append(f"Rota mais pesada: setor {pesada['Setor']} com {format_horas_hhmmss(pesada['Horas Trabalhadas'])} por dia.")
        diagnostico.append(f"Rota mais leve: setor {leve['Setor']} com {format_horas_hhmmss(leve['Horas Trabalhadas'])} por dia.")
        diagnostico.append("Médias calculadas por setor com base nos dias efetivamente encontrados para cada rota.")

    return {"base": base, "rotas": rotas.sort_values("Horas Trabalhadas", ascending=False), "kpis": kpis, "medias": medias, "diagnostico": diagnostico}

def get_filter_options(df: pd.DataFrame):
    unidades = sorted(df["Unidade"].dropna().astype(str).unique()) if "Unidade" in df.columns else []
    turnos = sorted(df["Turno"].dropna().astype(str).unique()) if "Turno" in df.columns else []
    dias = sorted(df["Dia da Semana"].dropna().astype(str).unique()) if "Dia da Semana" in df.columns else []
    setores = []
    if "Setor" in df.columns:
        s = pd.to_numeric(df["Setor"], errors="coerce")
        s = s.dropna()
        s = s[s > 0]
        setores = sorted(s.astype(int).astype(str).str.zfill(4).unique())
    return unidades, turnos, dias, setores

def apply_filters(df: pd.DataFrame, sel_unidades, sel_turnos, sel_dias, sel_setores) -> pd.DataFrame:
    out = df.copy()
    if "Setor" in out.columns:
        setor_num = pd.to_numeric(out["Setor"], errors="coerce")
        out = out[setor_num.notna()]
        out = out[pd.to_numeric(out["Setor"], errors="coerce") > 0].copy()
        out["Setor"] = pd.to_numeric(out["Setor"], errors="coerce").astype(int).astype(str).str.zfill(4)
    if sel_unidades and "Unidade" in out.columns:
        out = out[out["Unidade"].astype(str).isin(sel_unidades)]
    if sel_turnos and "Turno" in out.columns:
        out = out[out["Turno"].astype(str).isin(sel_turnos)]
    if sel_dias and "Dia da Semana" in out.columns:
        out = out[out["Dia da Semana"].astype(str).isin(sel_dias)]
    if sel_setores and "Setor" in out.columns:
        out = out[out["Setor"].astype(str).isin(sel_setores)]
    return out