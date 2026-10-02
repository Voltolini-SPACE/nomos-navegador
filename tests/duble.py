"""Dublê de driver — registra chamadas e responde o combinado.

Permite provar o contrato de segurança (recusa de credencial, allowlist,
evidência) sem abrir navegador nenhum.
"""
from __future__ import annotations

from pathlib import Path


class DriverFalso:
    def __init__(self, url_inicial: str = "https://exemplo.test/pagina",
                 titulo: str = "Exemplo", texto: str = "conteúdo da página",
                 tipos: dict | None = None, redirecionar_para: str | None = None):
        self._url = url_inicial
        self._titulo = titulo
        self._texto = texto
        self._tipos = tipos or {}
        self._redirecionar = redirecionar_para
        self.chamadas: list = []
        self.fechado = False

    def goto(self, url: str) -> None:
        self.chamadas.append(("goto", url))
        self._url = self._redirecionar or url

    def url(self) -> str:
        return self._url

    def titulo(self) -> str:
        return self._titulo

    def texto(self, seletor: str | None = None) -> str:
        self.chamadas.append(("texto", seletor))
        return self._texto

    def tipo_do_campo(self, seletor: str) -> str:
        return self._tipos.get(seletor, "")

    def preencher(self, seletor: str, valor: str) -> None:
        self.chamadas.append(("preencher", seletor, valor))

    def clicar(self, seletor: str) -> None:
        self.chamadas.append(("clicar", seletor))

    def screenshot(self, caminho: Path) -> None:
        Path(caminho).write_bytes(b"\x89PNG\r\n\x1a\n")
        self.chamadas.append(("screenshot", str(caminho)))

    def fechar(self) -> None:
        self.fechado = True
        self.chamadas.append(("fechar",))
