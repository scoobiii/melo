import sqlite3
import tempfile
import os

import pytest

from packages.catalog.partners import (
    init_partners_schema,
    create_partner,
    update_partner_status,
    list_partners,
)


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_partners_schema(path)
    yield path
    os.unlink(path)


def test_create_partner_default_status(db_path):
    pid = create_partner(db_path, "Gravadora X", "gravadora")
    partners = list_partners(db_path)
    assert len(partners) == 1
    assert partners[0]["status"] == "lead"
    assert partners[0]["id"] == pid


def test_update_status_valid(db_path):
    pid = create_partner(db_path, "Produtor Y", "produtor_independente")
    update_partner_status(db_path, pid, "em_negociacao")
    partners = list_partners(db_path)
    assert partners[0]["status"] == "em_negociacao"


def test_update_status_invalid_raises(db_path):
    pid = create_partner(db_path, "Plataforma Z", "plataforma")
    with pytest.raises(ValueError):
        update_partner_status(db_path, pid, "status_que_nao_existe")


def test_list_partners_filter_by_status(db_path):
    create_partner(db_path, "A", "gravadora")
    pid_b = create_partner(db_path, "B", "produtor_independente")
    update_partner_status(db_path, pid_b, "ativo")

    ativos = list_partners(db_path, status="ativo")
    assert len(ativos) == 1
    assert ativos[0]["nome"] == "B"


def test_tipo_invalido_e_rejeitado_pelo_check_constraint(db_path):
    conn = sqlite3.connect(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO parceiros_negocio (nome, tipo) VALUES (?, ?)",
            ("X", "tipo_invalido"),
        )
        conn.commit()
    conn.close()
