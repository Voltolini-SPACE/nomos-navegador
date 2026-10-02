"""NOMOS Navegador — navegação governada (abrir, extrair, preencher, evidenciar).

Contrato de segurança (verificado por testes):

- **Nunca toca no navegador em uso.** Por padrão trabalha sobre uma CÓPIA do
  perfil; o perfil real exige pedido explícito do humano (`--perfil real`),
  porque exige o navegador fechado.
- **Não faz login.** Campos de senha são recusados, salvo autorização explícita.
- **Toda ação gera evidência** (URL, título, screenshot) em diretório durável.
- **Janela visível por padrão**; headless é opt-in declarado.
- **Sem JavaScript arbitrário.**
- **Não baixa navegador:** usa o Chrome instalado; sem ele, recusa com instrução.
- **Fail-closed** em alvo ausente, perfil inválido e domínio fora de allowlist.
"""

from nomos_navegador.pagina import Recusa, Resultado, Pagina
from nomos_navegador.perfis import achar_chrome, copiar_perfil, preparar_perfil

VERSAO = "1.0.0"
NOME_EXIBICAO = "NOMOS Navegador"

__all__ = [
    "NOME_EXIBICAO", "VERSAO", "Pagina", "Recusa", "Resultado",
    "achar_chrome", "copiar_perfil", "preparar_perfil",
]
