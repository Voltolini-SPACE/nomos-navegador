"""Localização do Chrome e preparação de perfil — sem tocar no navegador em uso.

O caso real que motivou este módulo: o Chrome do dono rodava de um DMG montado
(`/Volumes/...`), o que faz o macOS executá-lo por *AppTranslocation*; fechar o
navegador derrubou as abas abertas. Aqui a cópia do perfil é o padrão, e o
perfil real é uma decisão explícita — nunca um efeito colateral.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

#: Perfil do Chrome do usuário (macOS, Linux e Windows, nesta ordem).
PERFIS_POSSIVEIS = (
    Path.home() / "Library/Application Support/Google/Chrome",  # macOS
    Path.home() / ".config/google-chrome",                      # Linux
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/User Data",  # Windows
)

#: Onde as cópias de trabalho vivem. Fora de /tmp de propósito: o /tmp é limpo e
#: já custou evidência perdida nesta casa.
DIR_TRABALHO = Path.home() / ".nomos" / "navegador"

#: Pastas de cache que não influenciam sessão e pesam centenas de MB.
_CACHES = (
    "Cache", "Code Cache", "GPUCache", "Service Worker", "DawnGraphiteCache",
    "DawnWebGPUCache", "GrShaderCache", "ShaderCache", "component_crx_cache",
    "extensions_crx_cache",
)

#: Caminhos onde o Chrome costuma estar instalado.
_CANDIDATOS_CHROME = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
)


def achar_chrome() -> str | None:
    """Devolve o executável do Chrome instalado, ou None (nunca baixa nada).

    Procura primeiro os caminhos fixos, depois algo montado em `/Volumes`
    (caso de DMG) e, por último, o processo em execução — foi assim que o
    Chrome translocado apareceu neste Mac.
    """
    candidatos = list(_CANDIDATOS_CHROME)
    candidatos += sorted(glob.glob(
        "/Volumes/*/Google Chrome.app/Contents/MacOS/Google Chrome"))
    for caminho in candidatos:
        if caminho and Path(caminho).is_file():
            return caminho
    try:
        saida = subprocess.run(["ps", "-Ao", "comm="], capture_output=True,
                               text=True, timeout=30, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for linha in saida.splitlines():
        if linha.strip().endswith("Google Chrome.app/Contents/MacOS/Google Chrome"):
            return linha.strip()
    return None


def perfil_do_usuario() -> Path | None:
    """Perfil real do Chrome, se existir."""
    for caminho in PERFIS_POSSIVEIS:
        if str(caminho) and caminho.is_dir():
            return caminho
    return None


def copiar_perfil(origem: Path | None = None, destino: Path | None = None) -> Path:
    """Copia o perfil para um diretório de trabalho e devolve o destino.

    A cópia é o que permite operar sem fechar o navegador do dono. Caches são
    excluídos (não carregam sessão e pesam centenas de MB).
    """
    origem = Path(origem) if origem else perfil_do_usuario()
    if origem is None or not origem.is_dir():
        raise FileNotFoundError("perfil do Chrome não encontrado")
    destino = Path(destino) if destino else DIR_TRABALHO / "perfil-copia"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)

    def ignorar(_dir, nomes):
        return [n for n in nomes if n in _CACHES]

    shutil.copytree(origem / "Default", destino / "Default",
                    ignore=ignorar, dirs_exist_ok=True)
    estado = origem / "Local State"
    if estado.is_file():
        shutil.copy2(estado, destino / "Local State")
    limpar_locks(destino)
    return destino


def limpar_locks(perfil: Path) -> list:
    """Remove os arquivos de trava do perfil. Devolve o que foi removido.

    Um perfil copiado herda `SingletonLock`/`SingletonSocket`; sem removê-los o
    navegador acredita que já há instância dona do perfil e recusa abrir.
    """
    removidos = []
    for nome in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        alvo = Path(perfil) / nome
        try:
            if alvo.is_symlink() or alvo.exists():
                alvo.unlink(missing_ok=True)
                removidos.append(nome)
        except OSError:
            continue
    return removidos


def preparar_perfil(modo: str = "copia") -> Path:
    """Prepara o perfil de trabalho. `copia` (padrão) ou `real` (explícito).

    `real` aponta para o perfil do dono e **exige o navegador fechado** — por
    isso não é o padrão: fechar o navegador de alguém é decisão dele.
    """
    if modo == "real":
        perfil = perfil_do_usuario()
        if perfil is None:
            raise FileNotFoundError("perfil do Chrome não encontrado")
        return perfil
    if modo == "copia":
        return copiar_perfil()
    raise ValueError(f"modo de perfil desconhecido: {modo!r} (use 'copia' ou 'real')")


def dominio_permitido(url: str, allowlist) -> bool:
    """Allowlist de domínios, quando declarada. Vazia = sem restrição."""
    if not allowlist:
        return True
    host = (urlparse(url).hostname or "").lower()
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in allowlist)
