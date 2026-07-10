from datetime import date, timedelta

from app.domain import relationship_rules as rr


def test_dias_desde():
    hoje = date(2026, 7, 10)
    assert rr.dias_desde(date(2026, 7, 1), hoje) == 9
    assert rr.dias_desde(None, hoje) is None


def test_classe_economica_por_percentil():
    # 10 clientes: faturamentos 10..100
    vetor = sorted([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    assert rr.classe_economica(100, vetor) == "A+"   # top 10%
    assert rr.classe_economica(80, vetor) == "A"     # 20% seguintes
    assert rr.classe_economica(50, vetor) == "B"     # 30% seguintes
    assert rr.classe_economica(20, vetor) == "C"     # resto


def test_classe_economica_sem_faturamento_e_vetor_vazio():
    assert rr.classe_economica(0, [10, 20, 30]) == "C"
    assert rr.classe_economica(-5, [10, 20]) == "C"
    assert rr.classe_economica(100, []) == "C"


def test_status_sla_semaforo():
    # Classe A: SLA 90, limiar de atenção = round(60) = 60
    assert rr.status_sla("A", 30)[0] == "Dentro do prazo"
    assert rr.status_sla("A", 60)[0] == "Dentro do prazo"
    assert rr.status_sla("A", 61)[0] == "Atenção"
    assert rr.status_sla("A", 90)[0] == "Atenção"
    assert rr.status_sla("A", 91)[0] == "Vencido"


def test_status_sla_sem_interacao_vence():
    rotulo, cor = rr.status_sla("C", None)
    assert rotulo == "Vencido"
    assert cor.startswith("#")


def test_indice_saude():
    assert rr.indice_saude([]) == 0.0
    assert rr.indice_saude(["Dentro do prazo", "Dentro do prazo"]) == 100.0
    assert rr.indice_saude(["Dentro do prazo", "Vencido"]) == 50.0
    assert rr.indice_saude(["Atenção", "Atenção"]) == 50.0


def test_classificar_carteira_end_to_end():
    hoje = date(2026, 7, 10)
    # Carteira com faturamentos 10,20,...,100 para o percentil ser significativo.
    clientes = [
        {"cliente": f"C{v}", "faturamento_36m": float(v), "ultima_interacao": hoje - timedelta(days=10)}
        for v in range(10, 101, 10)
    ]
    # O maior (100) está atrasado 200 dias; um sem compra fica na fila.
    clientes[-1]["ultima_interacao"] = hoje - timedelta(days=200)
    clientes.append({"cliente": "Sem compra", "faturamento_36m": 0.0, "ultima_interacao": None})

    resultado = {c["cliente"]: c for c in rr.classificar_carteira(clientes, hoje)}
    assert resultado["C100"]["classe"] == "A+"
    assert resultado["C100"]["status"] == "Vencido"  # 200 dias > SLA 90
    assert resultado["C50"]["status"] == "Dentro do prazo"
    assert resultado["Sem compra"]["classe"] == "C"
    assert resultado["Sem compra"]["dias"] is None
    assert resultado["Sem compra"]["status"] == "Vencido"
