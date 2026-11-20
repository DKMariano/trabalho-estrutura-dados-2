
import json
from pathlib import Path
from datetime import datetime

CAMINHO_HISTORICO = Path(__file__).resolve().parent / "historico.json"


def carregar_historico():
    if not CAMINHO_HISTORICO.exists():
        return []

    with CAMINHO_HISTORICO.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def registrar_consulta(cliente_id, resultado):
    historico = carregar_historico()
    rota = resultado["rota"]

    registro = {
        "id": max((item["id"] for item in historico), default=0) + 1,
        "cliente_id": int(cliente_id),
        "data": datetime.now().isoformat(timespec="seconds"),
        "origem": resultado["origem"]["codigo"],
        "origem_nome": resultado["origem"]["nome"],
        "destino": resultado["cobertura"]["codigo"],
        "destino_nome": resultado["cobertura"]["pais"],
        "criterio": rota["criterio"],
        "caminho": rota["caminho"],
        "latencia_total_ms": rota["latencia_total_ms"],
        "custo_total_usd": rota["custo_total_usd"],
        "demonstrativo": True
    }

    historico.append(registro)

    with CAMINHO_HISTORICO.open("w", encoding="utf-8") as arquivo:
        json.dump(historico, arquivo, ensure_ascii=False, indent=4)

    return registro
