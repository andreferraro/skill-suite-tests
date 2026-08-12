# Skill Suite Tests

Skill para planejar, criar, executar e validar testes automatizados a partir do risco real do sistema.

Você explica o fluxo, o comportamento esperado e o impacto da falha. A skill analisa o projeto, escolhe a estratégia de teste, implementa na stack existente e entrega evidências.

[Ver apresentação completa](https://docs.google.com/presentation/d/10icBAwszr-oIcf-SeNOB2QKGF9NQE1qs7TGqt0nVeQY/edit?usp=sharing)

## O que pode ser testado

- Frontend: componentes, telas, navegação, estados de UI, acessibilidade e responsividade.
- Backend: regras de domínio, serviços, jobs, schedulers, banco e cache.
- APIs: HTTP/REST, GraphQL, gRPC, contratos e compatibilidade.
- Integrações: webhooks, filas, eventos, mensageria e serviços externos.
- Dados: persistência, transições de estado, consistência e concorrência.
- Jornadas completas: interface, serviços, dados e efeitos do início ao fim.
- Atributos de qualidade: segurança, performance, resiliência, observabilidade e experiência.

## Conteúdo do repositório

- [`SKILL.md`](SKILL.md): fluxo operacional, gates de qualidade e contrato de saída.
- [`agents/openai.yaml`](agents/openai.yaml): nome, descrição e prompt exibidos no Codex.
- [`references/tipos-de-teste.md`](references/tipos-de-teste.md): taxonomia e seleção por risco.
- [`references/oraculos-e-qualidade.md`](references/oraculos-e-qualidade.md): oráculos, isolamento, sensibilidade e critérios de conclusão.
- [`references/guia-de-ecossistemas.md`](references/guia-de-ecossistemas.md): ferramentas para frontend, backend, mobile, dados e integrações.
- [`references/bases-tecnicas.md`](references/bases-tecnicas.md): normas e referências oficiais.

## Como a estratégia é definida

A classificação combina quatro eixos:

| Eixo | Pergunta | Exemplos |
| --- | --- | --- |
| Propósito | Por que testar? | smoke, confirmação, regressão, aceitação |
| Nível | Onde observar? | unidade, componente, contrato, integração, ponta a ponta |
| Qualidade | Qual risco medir? | funcional, segurança, performance, acessibilidade, resiliência |
| Técnica | Como gerar casos? | limites, tabela de decisão, property-based, combinatório, fuzz |

O tipo de teste nasce do risco, da arquitetura e da evidência necessária.

## Instalação

### Pré-requisitos

- Git instalado.
- Codex ou Cursor com suporte a Agent Skills.

Codex e Cursor carregam skills globais de `~/.agents/skills`. Um único clone atende as duas ferramentas.

### Windows com PowerShell

```powershell
$skills = "$env:USERPROFILE\.agents\skills"
New-Item -ItemType Directory -Force $skills | Out-Null
Set-Location $skills
git clone https://github.com/andreferraro/skill-suite-tests.git
```

### macOS ou Linux

```bash
mkdir -p "$HOME/.agents/skills"
git clone \
  https://github.com/andreferraro/skill-suite-tests.git \
  "$HOME/.agents/skills/skill-suite-tests"
```

### Instalação apenas no projeto

Execute na raiz do projeto:

```powershell
New-Item -ItemType Directory -Force .agents\skills | Out-Null
git clone `
  https://github.com/andreferraro/skill-suite-tests.git `
  .agents\skills\skill-suite-tests
```

### Importação pela interface do Cursor

1. Abra **Customize**.
2. Entre em **Rules** e escolha **Add Rule**.
3. Selecione **Remote Rule (GitHub)**.
4. Informe `https://github.com/andreferraro/skill-suite-tests`.

### Validação

No Windows:

```powershell
Test-Path "$env:USERPROFILE\.agents\skills\skill-suite-tests\SKILL.md"
```

No macOS ou Linux:

```bash
test -f "$HOME/.agents/skills/skill-suite-tests/SKILL.md" && echo "Skill instalada"
```

Abra um novo chat no Codex ou no Cursor após a instalação.

### Atualização

Windows:

```powershell
git -C "$env:USERPROFILE\.agents\skills\skill-suite-tests" pull --ff-only
```

macOS ou Linux:

```bash
git -C "$HOME/.agents/skills/skill-suite-tests" pull --ff-only
```

## Como usar

### Codex

```text
Use $skill-suite-tests no checkout. Foque no risco de pedidos duplicados e valide a jornada completa.
```

### Cursor

```text
/skill-suite-tests Valide o login. Cubra loading, erro, navegação, acessibilidade e expiração da sessão.
```

A skill também pode ser escolhida automaticamente quando o pedido combina com a descrição do `SKILL.md`.

### Contexto recomendado

Informe o que souber:

1. **Alvo:** tela, componente, endpoint, serviço, job, integração ou fluxo.
2. **Comportamento:** resultado esperado ou regra documentada.
3. **Risco:** falha e impacto que precisam de cobertura.
4. **Ambiente:** local, CI, staging, browser ou dispositivo.
5. **Restrições:** dados, integrações externas, janela e limites de execução.
6. **Entrega:** criar, executar ou apenas preparar os testes.

## Exemplos

### Frontend

```text
Use $skill-suite-tests na tela de recuperação de senha. Teste validação, loading, mensagens de erro, acessibilidade e navegação após sucesso.
```

### Backend e concorrência

```text
Use $skill-suite-tests na criação do pagamento. Prove idempotência sob requisições simultâneas e valide o estado final no banco.
```

### Ponta a ponta

```text
Use $skill-suite-tests no checkout. Cubra UI, API, banco, evento de pedido criado e confirmação apresentada ao cliente.
```

### Performance

```text
Use $skill-suite-tests na busca. Prepare perfis de smoke, carga e pico com thresholds marcados como <definir>. Entregue o plano antes da execução.
```

## Entrega esperada

- Classificação do teste e risco coberto.
- Código integrado aos padrões do projeto.
- Cenários, dados, oráculos e fronteiras utilizados.
- Arquivos criados ou alterados.
- Comandos executados e resultados reais.
- Evidências como logs, métricas, traces, screenshots ou vídeos, quando aplicáveis.
- Limitações, bloqueios e riscos residuais.

## Segurança operacional

- Credenciais entram por variáveis de ambiente ou cofres de segredo.
- Dados sensíveis ficam fora de fixtures, logs, commits e exemplos.
- Carga, estresse, fuzz, exploração automatizada e injeção de falhas exigem ambiente autorizado.
- Execução em produção exige aprovação explícita, observabilidade, critérios de parada e blast radius controlado.
- Cada resultado deve refletir a evidência produzida na execução.

## Fluxo de contribuição

O repositório usa Gitflow:

- `main`: versões publicadas.
- `develop`: integração das próximas mudanças.
- `feature/*`: documentação, funcionalidades e melhorias.
- `release/*`: preparação de versão.
- `hotfix/*`: correções urgentes originadas de `main`.

Os commits seguem Conventional Commits:

```text
docs: improve installation guide
feat: add frontend testing workflow
fix: correct skill discovery path
```

## Referências

- [Agent Skills no Codex](https://learn.chatgpt.com/docs/build-skills)
- [Agent Skills no Cursor](https://cursor.com/docs/skills)
