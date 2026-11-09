"""Testes unitários para o algoritmo de equalização (5_Equalizacao_Automatica)."""
import math
import sys
import os
import importlib.util
import unittest.mock as mock

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_PAGE = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "pages", "5_Equalizacao_Automatica.py")


def _build_mock_st():
    """Monta um MagicMock que cobre as chamadas Streamlit do módulo."""
    st = mock.MagicMock()
    # st.columns(n) deve retornar n contextos
    def columns(n, **kw):
        return [mock.MagicMock() for _ in range(n)]
    st.columns.side_effect = columns
    st.session_state = {}
    st.sidebar = mock.MagicMock()
    st.sidebar.subheader = mock.MagicMock()
    st.sidebar.selectbox.return_value = "Todos"
    st.sidebar.number_input.return_value = 7.33
    st.sidebar.checkbox.return_value = False
    return st


# ------------------------------------------------------------------
# Carrega o módulo de página com mocks temporários de Streamlit/UI,
# depois restaura os módulos reais para não contaminar test_kpis.py
# ------------------------------------------------------------------
import importlib as _importlib

# Preserva estado real antes de mockar
_real_st      = sys.modules.get("streamlit")
_real_helpers = sys.modules.get("helpers")
_real_kpis    = sys.modules.get("kpis")

_st_mock = _build_mock_st()
_st_mock.stop.side_effect = SystemExit(0)
sys.modules["streamlit"] = _st_mock

_helpers_mock = mock.MagicMock()
_helpers_mock.upload_and_filter_page.return_value = (7.33, pd.DataFrame())
sys.modules["helpers"] = _helpers_mock

_kpis_mock = mock.MagicMock()
_kpis_mock.compute_dashboard_data.return_value = {
    "base": pd.DataFrame(), "rotas": pd.DataFrame(),
    "kpis": {}, "medias": {}, "diagnostico": [],
}
_kpis_mock.format_horas_hhmmss = lambda v: "-"
_kpis_mock.format_number_br    = lambda v, d=2: "0,00"
sys.modules["kpis"] = _kpis_mock

spec = importlib.util.spec_from_file_location("eq_auto", _PAGE)
eq = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(eq)
except SystemExit:
    pass  # st.stop() chamado ao detectar rotas vazias — comportamento esperado

# Restaura módulos reais (ou remove o mock se não havia nada antes)
def _restore(key, original):
    if original is None:
        sys.modules.pop(key, None)
    else:
        sys.modules[key] = original

_restore("streamlit", _real_st)
_restore("helpers",   _real_helpers)
_restore("kpis",      _real_kpis)

ceil_viagens      = eq.ceil_viagens
recomputar_fisica = eq.recomputar_fisica
equalizar_inteligente = eq.equalizar_inteligente
preparar          = eq.preparar
CAPACIDADES       = eq.CAPACIDADES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _frota_simples(horas=(8.0, 7.0, 6.0), tons=(10.0, 8.0, 6.0)):
    """DataFrame mínimo no formato esperado por preparar() / equalizar_inteligente()."""
    n = len(horas)
    setores = [str(2000 + i) for i in range(n)]
    tipo_map = {s: "Toco" for s in setores}
    cap_map  = {s: CAPACIDADES["Toco"] for s in setores}

    rotas = pd.DataFrame({
        "Setor":              setores,
        "Toneladas":          list(tons),
        "Viagens":            [math.ceil(t / 9.5) for t in tons],
        "Km Produtivo":       [30.0] * n,
        "Km Improdutivo":     [5.0]  * n,
        "Km Total":           [35.0] * n,
        "Combustível":        [18.0] * n,
        "Horas Trabalhadas":  list(horas),
        "Horas Produtivas":   [h * 0.75 for h in horas],
        "Horas Improdutivas": [h * 0.25 for h in horas],
        "Produtividade (t/h)": [t / h for t, h in zip(tons, horas)],
    })
    return preparar(rotas, tipo_map, cap_map)


# ---------------------------------------------------------------------------
# ceil_viagens
# ---------------------------------------------------------------------------
class TestCeilViagens:
    def test_exato(self):
        assert ceil_viagens(9.5, 9.5) == 1

    def test_arredonda_para_cima(self):
        assert ceil_viagens(10.0, 9.5) == 2

    def test_zero_tons(self):
        assert ceil_viagens(0.0, 9.5) == 0

    def test_nan(self):
        assert ceil_viagens(float("nan"), 9.5) == 0

    def test_capacidade_zero(self):
        assert ceil_viagens(5.0, 0.0) == 0


# ---------------------------------------------------------------------------
# recomputar_fisica
# ---------------------------------------------------------------------------
class TestRecomputarFisica:
    def test_colunas_criadas(self):
        df = _frota_simples()
        out = recomputar_fisica(df)
        assert "Horas Simulada (h)" in out.columns
        assert "Viagens Projetadas" in out.columns
        assert "Combustível Simulado" in out.columns

    def test_horas_positivas(self):
        df = _frota_simples()
        out = recomputar_fisica(df)
        assert (out["Horas Simulada (h)"] >= 0).all()

    def test_km_simulado_positivo(self):
        df = _frota_simples()
        out = recomputar_fisica(df)
        assert (out["Km Simulado"] >= 0).all()


# ---------------------------------------------------------------------------
# equalizar_inteligente
# ---------------------------------------------------------------------------
class TestEqualizarInteligente:
    def test_retorna_dataframe_e_plano(self):
        df = _frota_simples()
        sim, plano = equalizar_inteligente(df)
        assert isinstance(sim, pd.DataFrame)
        assert isinstance(plano, pd.DataFrame)

    def test_tonelagem_total_conservada(self):
        df = _frota_simples()
        ton_antes = df["Toneladas Simulada"].sum()
        sim, _ = equalizar_inteligente(df)
        ton_depois = sim["Toneladas Simulada"].sum()
        assert ton_depois == pytest.approx(ton_antes, abs=0.1)

    def test_reduz_amplitude(self):
        """Após equalização, amplitude de horas deve ser ≤ antes."""
        df = _frota_simples(horas=(10.0, 7.0, 4.0))
        amp_antes = df["Horas Simulada (h)"].max() - df["Horas Simulada (h)"].min()
        sim, _ = equalizar_inteligente(df)
        amp_depois = sim["Horas Simulada (h)"].max() - sim["Horas Simulada (h)"].min()
        assert amp_depois <= amp_antes + 0.01

    def test_frota_ja_equalizada_nao_move(self):
        """Se todos setores já têm a mesma carga, o plano deve ser vazio."""
        df = _frota_simples(horas=(7.0, 7.0, 7.0), tons=(9.5, 9.5, 9.5))
        _, plano = equalizar_inteligente(df, alvo_horas=7.0)
        assert plano.empty

    def test_convergencia_sem_loop_infinito(self):
        """Deve terminar mesmo com dados extremos."""
        df = _frota_simples(horas=(12.0, 1.0, 1.0), tons=(25.0, 1.0, 1.0))
        sim, _ = equalizar_inteligente(df)
        assert len(sim) == 3
