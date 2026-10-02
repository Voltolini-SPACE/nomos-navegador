# NOMOS Navegador

**Navegação governada.** Abre páginas, extrai conteúdo, preenche formulários e deixa **evidência** — sem tocar no
navegador que você está usando.

- **Nome de exibição:** NOMOS Navegador
- **Comando:** `nomos-navegador`
- **Licença:** MIT
- **Dependência de navegador:** opcional (`[browser]` = Playwright), usando o **Chrome já instalado**

## Por que ele existe

Automatizar navegador é fácil; fazer isso **sem estragar o ambiente de quem trabalha** é o problema real. Este
componente nasceu de um caso concreto: para cadastrar uma chave no GitHub, uma automação fechou o Chrome do dono —
que rodava de um DMG montado — e as abas abertas se perderam.

Aqui, isso não acontece por construção:

| Promessa | Como é garantida |
|---|---|
| **Nunca toca no navegador em uso** | Por padrão trabalha sobre uma **cópia** do perfil (sem caches). O perfil real exige `--perfil real`, uma decisão explícita, porque exige fechar o navegador |
| **Não faz login** | Campos de senha são **recusados**; `--permitir-senha` é autorização explícita e consciente |
| **Toda ação deixa evidência** | Screenshot + URL + título em diretório **durável** (`~/.nomos/navegador/evidence/`) — nunca em `/tmp` |
| **Você vê o que acontece** | Janela **visível** por padrão; `--headless` é opt-in declarado |
| **Sem JavaScript arbitrário** | O componente não expõe execução de JS |
| **Não baixa navegador** | Usa o Chrome instalado; sem ele, **recusa** com instrução |
| **Domínio sob controle** | `--allowlist` restringe a navegação, inclusive contra **redirecionamento** para fora |
| **Fail-closed** | Esquema não-HTTP, alvo ausente, perfil inválido e credencial suspeita são recusas, não avisos |

## Uso

```bash
nomos-navegador abrir https://exemplo.test --texto --screenshot
nomos-navegador extrair https://exemplo.test --seletor "#conteudo"
nomos-navegador preencher https://exemplo.test --campo "#nome=Voltolini" --enviar "#ok"
nomos-navegador perfis            # mostra o Chrome detectado e os perfis
```

Comuns a todos: `--perfil copia|real`, `--headless`, `--allowlist a.test,b.test`,
`--evidencia DIR`, `--json`, `--executavel CAMINHO`.

Instalação a partir do código:

```bash
pip install ".[browser]"     # com navegador
pip install .                # só as políticas e a evidência (sem Playwright)
```

## Descoberta do Chrome

O componente procura, nesta ordem: caminhos fixos (`/Applications`, `/usr/bin`), **`/Volumes/*`** (caso de DMG
montado, que foi o achado real neste Mac) e o **processo em execução**. Ele **nunca** baixa um navegador: se não
encontrar, diz o que fazer.

## Testes

```bash
PYTHONPATH=src python -m pytest tests -q     # 34 testes
python -m ruff check .
```

O contrato de segurança é provado com um **driver dublê**: recusa de credencial, allowlist, bloqueio de
redirecionamento, evidência em disco e ausência de escrita fora do alvo são testados **sem abrir navegador**.

## Licença

MIT — ver [LICENSE](LICENSE).
