"""
Ponto 13 - Testes com rotas escritas à mão (dados reais do dataset tiny).

Rotas testadas com o verificar_rota do model.py (ponto 12):
  1) uma rota válida
  2) uma rota que excede a capacidade
  3) uma rota fora da janela (recolha tardia e entrega tardia)
  + um teste extra de fluxo (entregar sem carregar no armazém)

Como correr:
  - terminal:  python test_rotas_mao.py
  - notebook:  import test_rotas_mao; test_rotas_mao.correr_todos()

Ids usados (location_id): produtores 1, 2, 3 | centro de recolha 4 (armazém) |
entregas 5 a 9. Veículos: 1 (150 kg, refrigerado) e 2 (200 kg), ambos no centro 4.
"""
import os
import pandas as pd

from model import read_csv_files, loadProblem, verificar_rota

CAMINHO = os.environ.get("DADOS_TINY", "./data/data_tiny_20261020/")


# --------------------------------------------------------------------------
# Constrói o dicionário `dados` que o verificar_rota espera, a partir dos CSV
# (se já tiveres uma função que o constrói no notebook, usa essa e apaga esta)
# --------------------------------------------------------------------------
def construir_dados(problem):
    loc = problem.locations
    tipo = dict(zip(loc["location_id"], loc["location_type"]))
    # (tipo, ref_id) -> location_id (as tabelas usam ref_id, as rotas usam location_id)
    ref_para_local = {(r.location_type, r.ref_id): r.location_id for r in loc.itertuples()}

    itens = {}
    for r in problem.requests:
        itens[r.orderItemId] = {
            "producer": (ref_para_local[("producer", r.producerId)],
                         pd.Timestamp(r.availabilityStart), pd.Timestamp(r.availabilityEnd)),
            "delivery_location": (ref_para_local[("delivery_location", r.deliveryLocationId)],
                                  pd.Timestamp(r.deliveryStart), pd.Timestamp(r.deliveryEnd)),
            "peso": r.weightKg,
        }

    veiculos = {v.vehicleId: (v.capacityKg, ref_para_local[("collection_center", v.centerId)])
                for v in problem.vehicles}

    dm = problem.distanceMatrix
    viagem = {(o, d): pd.Timedelta(minutes=m)
              for o, d, m in zip(dm["origin_location_id"], dm["destination_location_id"], dm["duration_min"])}

    regras = dict(zip(problem.rules["rule"], problem.rules["value"]))

    return {
        "itens": itens,
        "veiculos": veiculos,
        "viagem": viagem,
        "tipo": tipo,
        "manuseio": pd.Timedelta(minutes=float(regras["warehouse_handling_min"])),
        "servico": pd.Timedelta(minutes=float(regras["stop_service_min"])),
        "max_armazem": pd.Timedelta(hours=float(regras["max_warehouse_dwell_h"])),
    }


def carregar_dados(caminho=CAMINHO):
    ficheiros = sorted(os.listdir(caminho))
    problem = loadProblem(read_csv_files(caminho, ficheiros))
    return construir_dados(problem)


DADOS = carregar_dados()


# --------------------------------------------------------------------------
# TESTES  (rota = lista de paragens (location_id, [order_item_id, ...]))
# --------------------------------------------------------------------------
def test_rota_valida():
    """
    Encomenda 4 (itens 11, 12, 13 = 26,3 kg) com o veículo 2 (200 kg), a partir das 08:00 de 30/10.
    Recolhe nos produtores 3, 2 e 1, passa pelo armazém (4) e entrega na Casa 3 (local 7).
    Esperado: viável, sem erros.
    """
    rota = [
        (3, [11]),
        (2, [12]),
        (1, [13]),
        (4, [11, 12, 13]),
        (7, [11, 12, 13]),
    ]
    erros = verificar_rota(DADOS, 2, rota, "2026-10-30 08:00")
    assert erros == [], f"era para ser válida, mas: {erros}"


def test_excede_capacidade():
    """
    Veículo 1 (150 kg) recolhe TODOS os 24 itens com recolha a 30/10 (166,9 kg):
    produtor 3 (37,3 kg) -> produtor 1 (52,0 kg) -> produtor 2 (77,6 kg) -> armazém.
    Esperado: inviável só por capacidade (166,9 kg > 150 kg na paragem 3).
    """
    rota = [
        (3, [6, 11, 22, 24, 26, 29, 35]),
        (1, [5, 13, 25, 31, 32, 34, 37, 40]),
        (2, [12, 23, 27, 28, 30, 33, 36, 38, 39]),
        (4, []),
    ]
    erros = verificar_rota(DADOS, 1, rota, "2026-10-30 07:00")
    assert len(erros) == 1, f"devia haver só 1 erro, mas: {erros}"
    assert "166.9 kg a bordo" in erros[0] and "150 kg" in erros[0], erros


def test_fora_da_janela_recolha():
    """
    Encomenda 2 (itens 5 e 6) com o veículo 2, partida às 09:30 de 30/10.
    O item 6 (produtor 3) só pode ser recolhido até às 09:45, mas o veículo chega às 10:08.
    O item 5 (produtor 1, até às 11:15) ainda vai a tempo.
    Esperado: inviável só porque o item 6 chega fora da janela, na paragem 1.
    """
    rota = [
        (3, [6]),
        (1, [5]),
        (4, [5, 6]),
        (8, [5, 6]),
    ]
    erros = verificar_rota(DADOS, 2, rota, "2026-10-30 09:30")
    assert len(erros) == 1, f"devia haver só 1 erro, mas: {erros}"
    assert "Paragem 1" in erros[0] and "item 6" in erros[0] and "fora da janela" in erros[0], erros


def test_fora_da_janela_entrega():
    """
    Item 12 (10,3 kg; produtor 2 -> Casa 3, local 7) com o veículo 2, partida às 11:00 de 30/10.
    A recolha ainda é feita a tempo (11:50, janela até 12:00), mas a entrega só chega por volta
    das 13:51 e a janela de entrega fecha às 13:45.
    Esperado: inviável só porque o item 12 chega fora da janela na entrega (paragem 3).
    """
    rota = [
        (2, [12]),
        (4, [12]),
        (7, [12]),
    ]
    erros = verificar_rota(DADOS, 2, rota, "2026-10-30 11:00")
    assert len(erros) == 1, f"devia haver só 1 erro, mas: {erros}"
    assert "Paragem 3" in erros[0] and "item 12" in erros[0] and "fora da janela" in erros[0], erros


def test_extra_fluxo_sem_armazem():
    """
    Extra: tentar entregar o item 11 sem o ter recolhido nem carregado no armazém.
    Esperado: inviável, o item não foi carregado no armazém.
    """
    rota = [(7, [11])]
    erros = verificar_rota(DADOS, 2, rota, "2026-10-30 08:00")
    assert any("não foi carregado no armazém" in e for e in erros), erros


# --------------------------------------------------------------------------
def correr_todos():
    """Corre todos os testes e imprime um resumo (útil no notebook, sem pytest)."""
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"OK    {t.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"FALHA {t.__name__}: {e}")
    print(f"\n{len(testes) - falhas}/{len(testes)} testes passaram")
    return falhas == 0


if __name__ == "__main__":
    raise SystemExit(0 if correr_todos() else 1)
