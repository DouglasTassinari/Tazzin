from datetime import date, timedelta

from app.domain import opportunity_rules as orr


def test_faixa_status_por_idade():
    assert orr.faixa_status(0) == "Quente"
    assert orr.faixa_status(10) == "Quente"
    assert orr.faixa_status(11) == "Morna"
    assert orr.faixa_status(20) == "Morna"
    assert orr.faixa_status(21) == "Fria"
    assert orr.faixa_status(30) == "Fria"
    assert orr.faixa_status(31) == "Vencida"
    assert orr.faixa_status(None) == "Vencida"


def test_cor_faixa():
    assert orr.cor_faixa("Quente").startswith("#")
    assert orr.cor_faixa("Vencida").startswith("#")


def test_classificar_propostas_ordena_vencidas_primeiro():
    hoje = date(2026, 7, 10)
    propostas = [
        {"numero": "A", "valor": 100.0, "data_criacao": hoje - timedelta(days=5)},    # Quente
        {"numero": "B", "valor": 100.0, "data_criacao": hoje - timedelta(days=40)},   # Vencida antiga
        {"numero": "C", "valor": 500.0, "data_criacao": hoje - timedelta(days=35)},   # Vencida, maior valor
    ]
    ordenadas = orr.classificar_propostas(propostas, hoje)
    # Vencidas primeiro; entre elas, a mais antiga (B, 40 dias) antes de C (35).
    assert [p["numero"] for p in ordenadas] == ["B", "C", "A"]
    assert ordenadas[2]["faixa"] == "Quente"


def test_pipeline_inflado():
    hoje = date(2026, 7, 10)
    propostas = [
        {"numero": "A", "valor": 300.0, "data_criacao": hoje - timedelta(days=5)},   # Quente
        {"numero": "B", "valor": 100.0, "data_criacao": hoje - timedelta(days=50)},  # Vencida
    ]
    classificadas = orr.classificar_propostas(propostas, hoje)
    assert orr.pipeline_inflado(classificadas) == 25.0  # 100 / 400


def test_pipeline_inflado_sem_propostas():
    assert orr.pipeline_inflado([]) == 0.0
