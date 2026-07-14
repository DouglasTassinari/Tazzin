"""Limpeza do working-set na sessão — o que o botão "Restaurar base" faz.

``clear_state`` recebe um mapa comum (em produção é o ``st.session_state``), então
dá para verificar sem runtime do Streamlit que ela apaga o snapshot **e** o estado
dos widgets da página, sem levar junto o que é de outros módulos.
"""
from app.core import comp_workset


def test_clear_state_drops_the_snapshot_and_the_page_widgets():
    state = {
        "comp_workset": "<snapshot>",
        "comp_position_pick": 7,
        "comp_sim_level": 19,
        "comp_flash": "mensagem",
    }

    comp_workset.clear_state(state)

    assert state == {}


def test_clear_state_leaves_other_modules_alone():
    state = {"comp_workset": "<snapshot>", "people_filter": "ativos", "sales_range": 90}

    comp_workset.clear_state(state)

    assert state == {"people_filter": "ativos", "sales_range": 90}


def test_clear_state_is_a_no_op_when_the_session_never_loaded_the_module():
    state = {"sales_range": 90}

    comp_workset.clear_state(state)

    assert state == {"sales_range": 90}
