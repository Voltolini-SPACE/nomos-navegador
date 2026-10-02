"""Driver do Playwright — a única parte que fala com um navegador de verdade.

Import preguiçoso: sem o extra `[browser]` instalado, o resto do componente
(CLI, políticas, evidência) continua importável e testável.
"""
from __future__ import annotations

from pathlib import Path


class DriverIndisponivel(Exception):
    """O extra de navegador não está instalado, ou o Chrome não foi encontrado."""


class DriverPlaywright:
    """Abre o Chrome instalado com um perfil persistente e expõe o mínimo usado."""

    def __init__(self, executavel: str, perfil: str | Path, headless: bool = False,
                 timeout_ms: int = 90_000):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - depende do ambiente
            raise DriverIndisponivel(
                "Playwright não instalado. Instale com: pip install 'nomos-navegador[browser]'"
            ) from exc
        self._timeout = timeout_ms
        self._pw = sync_playwright().start()
        self._ctx = self._pw.chromium.launch_persistent_context(
            str(perfil), executable_path=executavel, headless=headless,
            args=["--no-first-run", "--no-default-browser-check"],
        )
        self._page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        self._page.set_default_timeout(timeout_ms)

    def goto(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded", timeout=self._timeout)

    def url(self) -> str:
        return self._page.url

    def titulo(self) -> str:
        return self._page.title()

    def texto(self, seletor: str | None = None) -> str:
        if seletor:
            return self._page.inner_text(seletor, timeout=self._timeout)
        return self._page.inner_text("body", timeout=self._timeout)

    def tipo_do_campo(self, seletor: str) -> str:
        try:
            elemento = self._page.query_selector(seletor)
            return (elemento.get_attribute("type") or "") if elemento else ""
        except Exception:  # noqa: BLE001 - seletor inválido não derruba o mapa
            return ""

    def preencher(self, seletor: str, valor: str) -> None:
        self._page.fill(seletor, valor, timeout=self._timeout)

    def clicar(self, seletor: str) -> None:
        self._page.click(seletor, timeout=self._timeout)

    def screenshot(self, caminho: Path) -> None:
        self._page.screenshot(path=str(caminho), full_page=True)

    def fechar(self) -> None:
        try:
            self._ctx.close()
        finally:
            self._pw.stop()
