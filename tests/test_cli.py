"""Testes do CLI — parser, recusas e comando de diagnóstico."""
from __future__ import annotations

import json

import pytest

from nomos_navegador.cli import _acao, build_parser, main
from nomos_navegador.pagina import Pagina, Recusa

from tests.duble import DriverFalso


def test_parser_reconhece_os_comandos():
    p = build_parser()
    assert p.parse_args(["abrir", "https://x.test"]).cmd == "abrir"
    assert p.parse_args(["extrair", "https://x.test"]).cmd == "extrair"
    assert p.parse_args(["perfis"]).cmd == "perfis"
    args = p.parse_args(["preencher", "https://x.test", "--campo", "#a=1"])
    assert args.campo == ["#a=1"]


def test_perfil_padrao_e_copia():
    """O padrão nunca é o perfil em uso — essa é a promessa do componente."""
    args = build_parser().parse_args(["abrir", "https://x.test"])
    assert args.perfil == "copia"
    assert args.headless is False, "janela visível é o padrão"


def test_preencher_exige_campo():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["preencher", "https://x.test"])


def test_campo_malformado_recusa():
    args = build_parser().parse_args(
        ["preencher", "https://x.test", "--campo", "sem-igual"])
    pag = Pagina(DriverFalso())
    with pytest.raises(Recusa, match="seletor=valor"):
        _acao(pag, args)


def test_acao_preencher_traduz_campos():
    args = build_parser().parse_args(
        ["preencher", "https://exemplo.test/", "--campo", "#nome=Voltolini",
         "--enviar", "#ok"])
    driver = DriverFalso()
    resultado = _acao(Pagina(driver), args)
    assert resultado.preenchidos == ["#nome"]
    assert ("preencher", "#nome", "Voltolini") in driver.chamadas


def test_comando_perfis_em_json(capsys):
    codigo = main(["perfis", "--json"])
    dados = json.loads(capsys.readouterr().out)
    assert "chrome" in dados
    assert dados["baixa_navegador"] is False
    assert codigo in (0, 3)  # 3 quando não há Chrome instalado


def test_version_imprime_o_nome_de_exibicao(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    saida = capsys.readouterr().out
    assert "NOMOS Navegador" in saida


def test_sem_comando_mostra_ajuda(capsys):
    assert main([]) == 1
    assert "NOMOS Navegador" in capsys.readouterr().out
