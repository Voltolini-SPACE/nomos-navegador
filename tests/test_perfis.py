"""Testes de perfil e descoberta do Chrome — sem abrir navegador."""
from __future__ import annotations

from pathlib import Path

import pytest

from nomos_navegador import perfis
from nomos_navegador.perfis import (
    achar_chrome,
    copiar_perfil,
    dominio_permitido,
    limpar_locks,
    perfil_do_usuario,
    preparar_perfil,
)


def test_achar_chrome_so_devolve_caminho_existente():
    """A promessa central: o componente não baixa navegador."""
    caminho = achar_chrome()
    if caminho is not None:
        assert Path(caminho).is_file(), "devolveu caminho que não existe"


def test_dominio_permitido_sem_allowlist_libera_tudo():
    assert dominio_permitido("https://qualquer.test/", []) is True


def test_dominio_permitido_exige_casa_ou_subdominio():
    lista = ["permitido.test"]
    assert dominio_permitido("https://permitido.test/a", lista) is True
    assert dominio_permitido("https://api.permitido.test/a", lista) is True
    assert dominio_permitido("https://naopermitido.test/a", lista) is False
    # sufixo parecido NÃO passa (permitido.test.evil.com)
    assert dominio_permitido("https://permitido.test.evil.com/", lista) is False


def test_limpar_locks_remove_arquivos_de_trava(tmp_path):
    for nome in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        (tmp_path / nome).write_text("x")
    removidos = limpar_locks(tmp_path)
    assert set(removidos) == {"SingletonLock", "SingletonSocket", "SingletonCookie"}
    assert not list(tmp_path.glob("Singleton*"))


def _origem_falsa(base: Path) -> Path:
    origem = base / "origem"
    (origem / "Default").mkdir(parents=True)
    (origem / "Default" / "Cookies").write_bytes(b"cookie")
    (origem / "Default" / "Cache").mkdir()
    (origem / "Default" / "Cache" / "grande").write_bytes(b"x" * 1024)
    (origem / "Local State").write_text("{}")
    (origem / "SingletonLock").write_text("trava")
    return origem


def test_copiar_perfil_traz_sessao_e_descarta_cache(tmp_path):
    origem = _origem_falsa(tmp_path)
    destino = copiar_perfil(origem=origem, destino=tmp_path / "copia")

    assert (destino / "Default" / "Cookies").is_file(), "não copiou a sessão"
    assert (destino / "Local State").is_file()
    assert not (destino / "Default" / "Cache").exists(), "copiou cache (peso inútil)"
    assert not list(destino.glob("Singleton*")), "herdou trava do perfil"


def test_copiar_perfil_sem_origem_falha_alto(tmp_path):
    with pytest.raises(FileNotFoundError):
        copiar_perfil(origem=tmp_path / "nao-existe", destino=tmp_path / "d")


def test_preparar_perfil_modo_desconhecido_recusa():
    with pytest.raises(ValueError, match="modo de perfil desconhecido"):
        preparar_perfil("qualquer")


def test_preparar_perfil_real_aponta_para_o_perfil_do_usuario():
    perfil = perfil_do_usuario()
    if perfil is None:
        pytest.skip("sem perfil de Chrome nesta máquina")
    assert preparar_perfil("real") == perfil


def test_diretorio_de_trabalho_nao_e_tmp():
    """Evidência em /tmp já se perdeu nesta casa; o padrão é durável."""
    assert not str(perfis.DIR_TRABALHO).startswith("/tmp")
