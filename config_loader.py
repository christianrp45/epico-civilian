from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).parent / "config.yaml"
_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    global _config
    if _config is None:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def get_feriados() -> list[str]:
    return get_config().get("feriados", [])


def get_setores_noturnos() -> list[str]:
    return get_config().get("setores_noturnos", [])


def get_distancias_aterro() -> dict[str, float]:
    setores = get_config().get("setores", {})
    return {s: float(info["distancia_aterro_km"]) for s, info in setores.items()}


def get_mapa_turnos() -> dict[str, str]:
    setores = get_config().get("setores", {})
    return {s: info["turno"] for s, info in setores.items()}


def get_mapa_frequencia() -> dict[str, str]:
    setores = get_config().get("setores", {})
    return {s: info["frequencia"] for s, info in setores.items()}


def get_capacidades_caminhoes() -> dict[str, float]:
    return {k: float(v) for k, v in get_config().get("caminhoes", {"Toco": 9.5, "Trucado": 13.5}).items()}


def get_operacional(chave: str, padrao: float) -> float:
    return float(get_config().get("operacional", {}).get(chave, padrao))


def get_dias_uteis_mes() -> int:
    return int(get_config().get("operacional", {}).get("dias_uteis_mes", 26))
