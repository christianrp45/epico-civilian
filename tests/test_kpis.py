"""Testes unitários para kpis.py."""
import numpy as np
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kpis import (
    _to_float_ptbr,
    _normalize_ton_scale,
    _to_hours,
    format_horas_hhmmss,
    prepare_base,
    compute_dashboard_data,
)


# ---------------------------------------------------------------------------
# _to_float_ptbr
# ---------------------------------------------------------------------------
class TestToFloatPtbr:
    def test_numero_americano(self):
        s = pd.Series(["1.5", "2.3", "0.0"])
        result = _to_float_ptbr(s)
        assert list(result) == pytest.approx([1.5, 2.3, 0.0])

    def test_numero_brasileiro(self):
        s = pd.Series(["1.234,56", "7.890,00"])
        result = _to_float_ptbr(s)
        assert list(result) == pytest.approx([1234.56, 7890.00])

    def test_ja_numerico(self):
        s = pd.Series([1.5, 2.3, np.nan])
        result = _to_float_ptbr(s)
        assert result[0] == pytest.approx(1.5)
        assert np.isnan(result[2])

    def test_vazio_retorna_nan(self):
        s = pd.Series(["", "nan", "None"])
        result = _to_float_ptbr(s)
        assert result.isna().all()

    def test_misto_virgula_ponto(self):
        s = pd.Series(["3,14", "2.72"])
        result = _to_float_ptbr(s)
        assert result[0] == pytest.approx(3.14)
        assert result[1] == pytest.approx(2.72)


# ---------------------------------------------------------------------------
# _normalize_ton_scale
# ---------------------------------------------------------------------------
class TestNormalizeTonScale:
    def test_escala_correta_nao_altera(self):
        s = pd.Series([5.0, 8.0, 7.5, 6.2])
        result = _normalize_ton_scale(s)
        assert list(result) == pytest.approx([5.0, 8.0, 7.5, 6.2])

    def test_escala_em_kg_divide_por_1000(self):
        s = pd.Series([5000.0, 8000.0, 7500.0])
        result = _normalize_ton_scale(s)
        assert list(result) == pytest.approx([5.0, 8.0, 7.5])

    def test_serie_vazia(self):
        s = pd.Series([], dtype=float)
        result = _normalize_ton_scale(s)
        assert len(result) == 0

    def test_todos_nan(self):
        s = pd.Series([np.nan, np.nan])
        result = _normalize_ton_scale(s)
        assert result.isna().all()


# ---------------------------------------------------------------------------
# _to_hours
# ---------------------------------------------------------------------------
class TestToHours:
    def test_formato_hh_mm_ss(self):
        s = pd.Series(["07:20:00", "09:00:00"])
        result = _to_hours(s)
        assert result[0] == pytest.approx(7 + 20 / 60, abs=1e-4)
        assert result[1] == pytest.approx(9.0, abs=1e-4)

    def test_decimal_direto(self):
        s = pd.Series(["7.5", "9.0"])
        result = _to_hours(s)
        assert result[0] == pytest.approx(7.5)

    def test_ja_numerico(self):
        s = pd.Series([7.33, 9.0])
        result = _to_hours(s)
        assert result[0] == pytest.approx(7.33)


# ---------------------------------------------------------------------------
# format_horas_hhmmss
# ---------------------------------------------------------------------------
class TestFormatHoras:
    def test_zero(self):
        assert format_horas_hhmmss(0.0) == "00:00:00"

    def test_7h20(self):
        assert format_horas_hhmmss(7 + 20 / 60) == "07:20:00"

    def test_negativo(self):
        resultado = format_horas_hhmmss(-1.5)
        assert resultado.startswith("-")

    def test_nan(self):
        assert format_horas_hhmmss(float("nan")) == "-"

    def test_none(self):
        assert format_horas_hhmmss(None) == "-"


# ---------------------------------------------------------------------------
# prepare_base / compute_dashboard_data
# ---------------------------------------------------------------------------
def _df_minimo():
    """DataFrame mínimo com colunas obrigatórias."""
    return pd.DataFrame({
        "Setor":               ["1001", "1002", "1003"],
        "Toneladas":           [8.0,     6.0,    10.0],
        "Viagens":             [2,       2,       3],
        "Km Produtivo":        [30.0,   25.0,   40.0],
        "Km Improdutivo":      [5.0,     4.0,    6.0],
        "Km Total":            [35.0,   29.0,   46.0],
        "Combustível":         [20.0,   16.0,   25.0],
        "Horas Trabalhadas":   [7.5,     6.0,    9.0],
        "Horas Produtivas":    [5.5,     4.5,    7.0],
        "Horas Improdutivas":  [2.0,     1.5,    2.0],
        "Horas Extras":        [0.0,     0.0,    1.67],
        "Turno":               ["DIURNO", "DIURNO", "NOTURNO"],
        "Dia da Semana":       ["Segunda-feira"] * 3,
    })


class TestPrepareBase:
    def test_colunas_derivadas_criadas(self):
        df = prepare_base(_df_minimo())
        assert "Produtividade (t/h)" in df.columns
        assert "L/ton" in df.columns
        assert "Linha válida" in df.columns

    def test_setor_zfill4(self):
        df = prepare_base(_df_minimo())
        assert all(df["Setor"].str.len() == 4)

    def test_colunas_obrigatorias_faltando_levanta_erro(self):
        df = _df_minimo().drop(columns=["Toneladas"])
        with pytest.raises(ValueError, match="ausentes"):
            prepare_base(df)

    def test_linhas_validas_detectadas(self):
        df = prepare_base(_df_minimo())
        assert df["Linha válida"].sum() == 3


class TestComputeDashboardData:
    def test_retorna_chaves_esperadas(self):
        result = compute_dashboard_data(_df_minimo())
        assert set(result.keys()) == {"base", "rotas", "kpis", "medias", "diagnostico"}

    def test_produtividade_positiva(self):
        result = compute_dashboard_data(_df_minimo())
        assert (result["rotas"]["Produtividade (t/h)"].dropna() > 0).all()

    def test_classificacao_jornada(self):
        result = compute_dashboard_data(_df_minimo(), jornada_meta=7.33)
        assert "Classificação Jornada" in result["rotas"].columns
        valores = result["rotas"]["Classificação Jornada"].unique()
        assert all(v in {"Abaixo da meta", "Equilibrada", "Acima da meta", "Sem dado"} for v in valores)
