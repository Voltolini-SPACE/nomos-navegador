#!/usr/bin/env python3
"""CLI do NOMOS Navegador — navegação governada, com evidência.

    nomos-navegador abrir URL [--texto] [--screenshot DIR]
    nomos-navegador extrair URL [--seletor CSS]
    nomos-navegador preencher URL --campo "seletor=valor" [--enviar SELETOR]
    nomos-navegador perfis

Comuns: `--perfil copia|real` (padrão copia), `--headless`, `--allowlist`,
`--evidencia DIR`, `--json`.
"""
from __future__ import annotations

import argparse
import json
import sys

from nomos_navegador import NOME_EXIBICAO, VERSAO
from nomos_navegador.driver import DriverIndisponivel, DriverPlaywright
from nomos_navegador.pagina import Pagina, Recusa, Resultado
from nomos_navegador.perfis import (
    DIR_TRABALHO,
    achar_chrome,
    perfil_do_usuario,
    preparar_perfil,
)


def _comuns(p: argparse.ArgumentParser) -> None:
    p.add_argument("--perfil", choices=("copia", "real"), default="copia",
                   help="copia (padrão, não toca no navegador em uso) ou real "
                        "(exige o navegador fechado)")
    p.add_argument("--headless", action="store_true",
                   help="sem janela (padrão é visível, para você ver o que acontece)")
    p.add_argument("--allowlist", default="",
                   help="domínios permitidos, separados por vírgula (vazio = sem restrição)")
    p.add_argument("--evidencia", metavar="DIR",
                   default=str(DIR_TRABALHO / "evidence"),
                   help="diretório de screenshot/evidência")
    p.add_argument("--json", action="store_true", help="saída em JSON")
    p.add_argument("--executavel", default=None,
                   help="caminho do Chrome (padrão: detecta o instalado)")


def _pagina(args) -> Pagina:
    executavel = args.executavel or achar_chrome()
    if not executavel:
        raise DriverIndisponivel(
            "Chrome não encontrado. Instale o Chrome (o NOMOS Navegador não baixa "
            "navegador por conta própria).")
    perfil = preparar_perfil(args.perfil)
    driver = DriverPlaywright(executavel, perfil, headless=args.headless)
    allowlist = [d.strip() for d in (args.allowlist or "").split(",") if d.strip()]
    return Pagina(driver, evidencia_dir=args.evidencia, allowlist=allowlist,
                  permitir_senha=getattr(args, "permitir_senha", False))


def _saida(resultado: Resultado, args) -> int:
    if args.json:
        print(json.dumps(resultado.__dict__, ensure_ascii=False, indent=2))
    else:
        print(f"url: {resultado.url}")
        print(f"título: {resultado.titulo}")
        if resultado.texto is not None:
            print(f"texto ({len(resultado.texto)} caracteres):")
            print(resultado.texto[:2000])
        if resultado.screenshot:
            print(f"screenshot: {resultado.screenshot}")
        if resultado.preenchidos:
            print("preenchidos: " + ", ".join(resultado.preenchidos))
        if resultado.cliques:
            print("cliques: " + ", ".join(resultado.cliques))
    return 0


def _executar(fn) -> int:
    """Roda a ação tratando recusa e indisponibilidade com código próprio."""
    pag = None
    try:
        pag, args = fn()
        resultado = _acao(pag, args)
        return _saida(resultado, args)
    except Recusa as exc:
        print(f"RECUSADO: {exc}", file=sys.stderr)
        return 2
    except DriverIndisponivel as exc:
        print(f"INDISPONÍVEL: {exc}", file=sys.stderr)
        return 3
    except FileNotFoundError as exc:
        print(f"SEM PERFIL: {exc}", file=sys.stderr)
        return 3
    finally:
        if pag is not None:
            pag.fechar()


def _acao(pag: Pagina, args) -> Resultado:
    if args.cmd == "abrir":
        return pag.abrir(args.url, texto=args.texto, screenshot=bool(args.screenshot))
    if args.cmd == "extrair":
        return pag.extrair(args.url, args.seletor)
    campos = []
    for item in args.campo:
        if "=" not in item:
            raise Recusa(f"--campo precisa ser 'seletor=valor': {item!r}")
        seletor, valor = item.split("=", 1)
        campos.append((seletor.strip(), valor))
    return pag.preencher(args.url, campos, enviar=args.enviar,
                         screenshot=bool(args.screenshot))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nomos-navegador",
        description=f"{NOME_EXIBICAO} — navegação governada, sem tocar no navegador em uso.",
    )
    parser.add_argument("--version", action="version",
                        version=f"{NOME_EXIBICAO} {VERSAO}")
    sub = parser.add_subparsers(dest="cmd")

    a = sub.add_parser("abrir", help="abre a URL e devolve url/título (e evidência)")
    a.add_argument("url")
    a.add_argument("--texto", action="store_true", help="inclui o texto da página")
    a.add_argument("--screenshot", metavar="DIR", nargs="?", const=True,
                   help="grava screenshot (DIR opcional)")
    _comuns(a)
    a.set_defaults(fn="abrir")

    e = sub.add_parser("extrair", help="abre a URL e extrai o texto (ou um seletor)")
    e.add_argument("url")
    e.add_argument("--seletor", default=None, help="seletor CSS opcional")
    _comuns(e)
    e.set_defaults(fn="extrair")

    p = sub.add_parser("preencher", help="preenche campos e opcionalmente envia")
    p.add_argument("url")
    p.add_argument("--campo", action="append", required=True,
                   metavar="SELETOR=VALOR", help="repetível")
    p.add_argument("--enviar", default=None, metavar="SELETOR",
                   help="seletor do botão de envio")
    p.add_argument("--screenshot", metavar="DIR", nargs="?", const=True)
    p.add_argument("--permitir-senha", action="store_true",
                   help="autoriza preencher campo de credencial (recusado por padrão)")
    _comuns(p)
    p.set_defaults(fn="preencher")

    pf = sub.add_parser("perfis", help="mostra o Chrome detectado e os perfis")
    pf.add_argument("--json", action="store_true", help="saída em JSON")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cmd = getattr(args, "cmd", None)

    if cmd == "perfis":
        chrome = achar_chrome()
        perfil = perfil_do_usuario()
        dados = {
            "chrome": chrome or "NÃO ENCONTRADO",
            "perfil_do_usuario": str(perfil) if perfil else "NÃO ENCONTRADO",
            "dir_trabalho": str(DIR_TRABALHO),
            "baixa_navegador": False,
        }
        if getattr(args, "json", False):
            print(json.dumps(dados, ensure_ascii=False, indent=2))
        else:
            for chave, valor in dados.items():
                print(f"{chave}: {valor}")
        return 0 if chrome else 3

    if cmd is None:
        build_parser().print_help()
        return 1

    def preparar():
        return _pagina(args), args

    return _executar(preparar)


if __name__ == "__main__":
    sys.exit(main())
