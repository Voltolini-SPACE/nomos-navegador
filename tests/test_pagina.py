"""Testes das políticas de página — o contrato de segurança, sem navegador."""
from __future__ import annotations

import pytest

from nomos_navegador.pagina import Pagina, Recusa
from tests.duble import DriverFalso


def _pagina(driver=None, **kw) -> tuple[Pagina, DriverFalso]:
    driver = driver or DriverFalso()
    return Pagina(driver, **kw), driver


# -- navegação ------------------------------------------------------------

def test_abrir_devolve_url_e_titulo():
    pag, driver = _pagina()
    r = pag.abrir("https://exemplo.test/")
    assert r.url == "https://exemplo.test/"
    assert r.titulo == "Exemplo"
    assert r.texto is None
    assert ("goto", "https://exemplo.test/") in driver.chamadas


def test_abrir_com_texto():
    pag, _ = _pagina()
    r = pag.abrir("https://exemplo.test/", texto=True)
    assert r.texto == "conteúdo da página"


def test_extrair_com_seletor():
    pag, driver = _pagina()
    r = pag.extrair("https://exemplo.test/", "#main")
    assert r.texto == "conteúdo da página"
    assert ("texto", "#main") in driver.chamadas


# -- allowlist ------------------------------------------------------------

def test_allowlist_bloqueia_dominio_fora():
    pag, driver = _pagina(allowlist=["permitido.test"])
    with pytest.raises(Recusa, match="fora da allowlist"):
        pag.abrir("https://proibido.test/")
    assert not [c for c in driver.chamadas if c[0] == "goto"], "navegou mesmo recusando"


def test_allowlist_permite_subdominio():
    pag, _ = _pagina(allowlist=["permitido.test"])
    assert pag.abrir("https://api.permitido.test/").url.startswith("https://api.")


def test_allowlist_vazia_nao_restringe():
    pag, _ = _pagina()
    assert pag.abrir("https://qualquer.test/").url


def test_redirecionamento_para_fora_da_allowlist_recusa():
    driver = DriverFalso(redirecionar_para="https://malicioso.test/")
    pag = Pagina(driver, allowlist=["permitido.test"])
    with pytest.raises(Recusa, match="redirecionado"):
        pag.abrir("https://permitido.test/")


# -- esquema de URL -------------------------------------------------------

@pytest.mark.parametrize("url", ["ftp://exemplo.test", "file:///etc/passwd", "javascript:alert(1)"])
def test_esquema_nao_http_e_recusado(url):
    pag, _ = _pagina()
    with pytest.raises(Recusa, match="url não permitida"):
        pag.abrir(url)


# -- credenciais ----------------------------------------------------------

def test_preencher_recusa_campo_de_senha():
    driver = DriverFalso(tipos={"#pwd": "password"})
    pag = Pagina(driver)
    with pytest.raises(Recusa, match="credencial"):
        pag.preencher("https://exemplo.test/", [("#pwd", "segredo")])
    assert not [c for c in driver.chamadas if c[0] == "preencher"], "digitou a senha"


def test_preencher_recusa_seletor_suspeito_por_nome():
    pag, _ = _pagina()
    with pytest.raises(Recusa, match="credencial"):
        pag.preencher("https://exemplo.test/", [("input[name=token]", "abc")])


def test_preencher_aceita_com_autorizacao_explicita():
    driver = DriverFalso(tipos={"#pwd": "password"})
    pag = Pagina(driver, permitir_senha=True)
    r = pag.preencher("https://exemplo.test/", [("#pwd", "segredo")])
    assert r.preenchidos == ["#pwd"]


def test_preencher_campo_comum_e_envia():
    pag, driver = _pagina()
    r = pag.preencher("https://exemplo.test/", [("#nome", "Voltolini")], enviar="#ok")
    assert r.preenchidos == ["#nome"]
    assert r.cliques == ["#ok"]
    assert ("clicar", "#ok") in driver.chamadas


# -- evidência ------------------------------------------------------------

def test_screenshot_vai_para_o_diretorio_de_evidencia(tmp_path):
    pag, _ = _pagina(evidencia_dir=tmp_path)
    r = pag.abrir("https://exemplo.test/", screenshot=True)
    assert r.screenshot is not None
    assert (tmp_path / "abrir.png").exists() or list(tmp_path.glob("abrir*.png"))


def test_sem_diretorio_de_evidencia_nao_grava_nada():
    pag, driver = _pagina()
    r = pag.abrir("https://exemplo.test/", screenshot=True)
    assert r.screenshot is None
    assert not [c for c in driver.chamadas if c[0] == "screenshot"]


def test_fechar_encaminha_ao_driver():
    pag, driver = _pagina()
    pag.fechar()
    assert driver.fechado is True
