"""Ações de página sobre um driver injetável — o que permite testar sem navegador.

O driver é uma fronteira explícita: em produção é o Playwright; nos testes é um
dublê que registra chamadas. Assim o contrato de segurança (não digitar senha,
respeitar allowlist, registrar evidência) é provado sem abrir navegador nenhum.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from nomos_navegador.perfis import dominio_permitido

#: Nomes de campo que denunciam credencial, mesmo sem `type=password`.
_SUSPEITOS = re.compile(r"pass|senha|secret|token|otp|codigo|code", re.I)


class Recusa(Exception):
    """Ação recusada por política — nunca por falha do navegador."""


@dataclass
class Resultado:
    """O que a ação produziu, pronto para virar evidência."""

    url: str
    titulo: str
    texto: str | None = None
    screenshot: str | None = None
    preenchidos: list = field(default_factory=list)
    cliques: list = field(default_factory=list)


class Driver(Protocol):
    """O mínimo que a página exige de um navegador."""

    def goto(self, url: str) -> None: ...
    def url(self) -> str: ...
    def titulo(self) -> str: ...
    def texto(self, seletor: str | None = None) -> str: ...
    def tipo_do_campo(self, seletor: str) -> str: ...
    def preencher(self, seletor: str, valor: str) -> None: ...
    def clicar(self, seletor: str) -> None: ...
    def screenshot(self, caminho: Path) -> None: ...
    def fechar(self) -> None: ...


def _agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


class Pagina:
    """Executa ações governadas numa página, registrando evidência."""

    def __init__(self, driver: Driver, evidencia_dir: str | Path | None = None,
                 allowlist=None, permitir_senha: bool = False):
        self.driver = driver
        self.evidencia_dir = Path(evidencia_dir).expanduser() if evidencia_dir else None
        self.allowlist = tuple(allowlist or ())
        self.permitir_senha = permitir_senha
        self.acoes: list = []

    # -- navegação ---------------------------------------------------------

    def abrir(self, url: str, *, texto: bool = False,
              screenshot: bool = False) -> Resultado:
        self._validar_url(url)
        self.driver.goto(url)
        atual = self.driver.url() or url
        self._validar_url(atual, redirecionada=True)
        resultado = Resultado(url=atual, titulo=self.driver.titulo())
        if texto:
            resultado.texto = self.driver.texto()
        if screenshot:
            resultado.screenshot = self.screenshot(f"abrir-{_agora()}")
        self.acoes.append(("abrir", url))
        return resultado

    def extrair(self, url: str, seletor: str | None = None) -> Resultado:
        self._validar_url(url)
        self.driver.goto(url)
        atual = self.driver.url() or url
        self._validar_url(atual, redirecionada=True)
        conteudo = self.driver.texto(seletor)
        self.acoes.append(("extrair", url, seletor))
        return Resultado(url=atual, titulo=self.driver.titulo(), texto=conteudo)

    def preencher(self, url: str, campos, *, enviar: str | None = None,
                  screenshot: bool = False) -> Resultado:
        """Preenche campos `seletor=valor`. Recusa credencial sem autorização."""
        self._validar_url(url)
        self.driver.goto(url)
        atual = self.driver.url() or url
        self._validar_url(atual, redirecionada=True)
        resultado = Resultado(url=atual, titulo=self.driver.titulo())
        for seletor, valor in campos:
            self._recusar_credencial(seletor)
            self.driver.preencher(seletor, valor)
            resultado.preenchidos.append(seletor)
        if enviar:
            self.driver.clicar(enviar)
            resultado.cliques.append(enviar)
        if screenshot:
            resultado.screenshot = self.screenshot(f"preencher-{_agora()}")
        self.acoes.append(("preencher", url, [c[0] for c in campos]))
        return resultado

    def screenshot(self, nome: str) -> str | None:
        if self.evidencia_dir is None:
            return None
        self.evidencia_dir.mkdir(parents=True, exist_ok=True)
        seguro = re.sub(r"[^A-Za-z0-9._-]", "-", nome)[:80]
        destino = self.evidencia_dir / f"{seguro}.png"
        self.driver.screenshot(destino)
        self.acoes.append(("screenshot", str(destino)))
        return str(destino)

    def fechar(self) -> None:
        self.driver.fechar()
        self.acoes.append(("fechar",))

    # -- políticas ---------------------------------------------------------

    def _validar_url(self, url: str, *, redirecionada: bool = False) -> None:
        if not isinstance(url, str) or not url.lower().startswith(("http://", "https://")):
            raise Recusa(f"url não permitida: {url!r}")
        if not dominio_permitido(url, self.allowlist):
            origem = "redirecionado para" if redirecionada else "alvo"
            raise Recusa(f"domínio fora da allowlist ({origem}): {url}")

    def _recusar_credencial(self, seletor: str) -> None:
        if self.permitir_senha:
            return
        tipo = (self.driver.tipo_do_campo(seletor) or "").lower()
        if tipo == "password" or _SUSPEITOS.search(seletor or ""):
            raise Recusa(
                f"campo de credencial recusado por padrão: {seletor!r} "
                "(use --permitir-senha se for mesmo isso que você quer)"
            )
