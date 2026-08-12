# Skill Suite Tests

[![Quality](https://github.com/andreferraro/skill-suite-tests/actions/workflows/quality.yml/badge.svg)](https://github.com/andreferraro/skill-suite-tests/actions/workflows/quality.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Skill para orientar Codex e Cursor na criação de testes automatizados guiados por risco. Você informa a parte do sistema e o risco relevante. O agente inspeciona a stack, escolhe a menor fronteira capaz de provar o comportamento, implementa os testes, executa a suíte e relata evidências.

[Ver apresentação](https://docs.google.com/presentation/d/10icBAwszr-oIcf-SeNOB2QKGF9NQE1qs7TGqt0nVeQY/edit?usp=sharing)

![Diagrama dos tipos de teste organizados por propósito, nível, qualidade e técnica](assets/linkedin-tipos-de-testes-diagrama.png)

## Estado da v0.3.0

A implementação foi integrada em `develop` pelo [PR #8](https://github.com/andreferraro/skill-suite-tests/pull/8). A release candidate está no [PR #9](https://github.com/andreferraro/skill-suite-tests/pull/9). A tag `v0.3.0` será criada depois que Codex e Cursor passarem os gates definidos para a release.

| Evidência | Estado atual |
| --- | --- |
| Projetos de referência | [3 implementados e aprovados](evals/results/fixture-validation.json) |
| Mutantes conhecidos | [12 implementados e 12 detectados](evals/results/fixture-validation.json) |
| Validação local dos scripts | 51 testes unitários aprovados |
| CI de qualidade | [Aprovada no Linux e Windows](https://github.com/andreferraro/skill-suite-tests/actions/workflows/quality.yml) |
| Configuração do GitHub | Os dois secrets e as duas variáveis estão cadastrados; saldo não é inferido dessa configuração |
| Eval pareado Codex | [Seis execuções concluídas, gate de eficácia reprovado](https://github.com/andreferraro/skill-suite-tests/actions/runs/31635717298) |
| Eval pareado Cursor | Configurado e pendente do gate de release |
| Ganho mediano sobre baseline | 0 ponto na última execução |
| Release `v0.3.0` | [PR #9](https://github.com/andreferraro/skill-suite-tests/pull/9) em draft, pendente de certificação manual |

A [execução 31635717298](https://github.com/andreferraro/skill-suite-tests/actions/runs/31635717298) comprovou o helper de sensibilidade, mas ainda reprovou o gate. Eventos manteve 100. API ficou em 91,25 porque duas chamadas concorrentes não detectaram a serialização enfraquecida. Web ficou em 83,75 porque cobriu a resposta obsoleta e deixou o estado loading sem cenário sensível. A skill passou a exigir contenção real e prova por mecanismo protetivo de alto impacto; o detector também passou a sinalizar estados assíncronos pendentes.

A tentativa seguinte falhou por falta de créditos antes de produzir uma medição válida. Esse incidente revelou o acionamento automático indevido dos benchmarks. Os workflows pagos agora são exclusivamente manuais e limitados.

## O que esta skill é

- Um guia operacional para agentes com acesso ao código, terminal e ferramentas do projeto.
- Um processo de seleção de testes por risco, arquitetura, fronteira e oráculo.
- Um pacote com detector de contexto, schema de evidência, validador e referências técnicas.
- Uma skill agnóstica no núcleo, com benchmark inicial em Web, API e eventos.

Framework de testes autônomo, runner e infraestrutura própria ficam fora do escopo. A skill reutiliza o que existe no projeto e pede uma decisão quando falta requisito, baseline, contrato ou ambiente autorizado.

## Suporte

| Status | Stack | Caso de referência |
| --- | --- | --- |
| Validado por fixture e mutações | React, TypeScript, Vitest, Testing Library e Playwright | Recuperação de senha |
| Validado por fixture e mutações | FastAPI, Python, pytest e SQLite | Criação de pagamento |
| Validado por fixture e mutações | Node.js, TypeScript, Vitest, RabbitMQ, PostgreSQL e Testcontainers | Consumidor de pedidos |
| Adaptável | Outros frameworks, linguagens e plataformas | Sem benchmark publicado |

O status validado nesta tabela cobre os fixtures e os 12 mutantes. A eficácia do agente com a skill será comprovada quando os evals pareados superarem o baseline.

## O que pode ser testado

- Frontend: componentes, telas, navegação, estado, teclado, acessibilidade e comportamento visual.
- Backend: regras de domínio, serviços, jobs, banco, cache, transações e concorrência.
- APIs: HTTP, REST, GraphQL, gRPC, contratos, protocolo e versionamento.
- Integrações: webhooks, filas, eventos, retries, DLQ, ordering e idempotência.
- Jornadas: interface, serviços, dados e efeitos observáveis de ponta a ponta.
- Qualidade: segurança, performance, resiliência, observabilidade e experiência.

A classificação usa quatro eixos:

| Eixo | Pergunta | Exemplos |
| --- | --- | --- |
| Propósito | Por que testar? | smoke, confirmação, regressão, aceitação |
| Nível | Onde observar? | unidade, componente, contrato, integração, ponta a ponta |
| Qualidade | Qual risco medir? | funcional, segurança, performance, acessibilidade, resiliência |
| Técnica | Como gerar os casos? | limites, tabela de decisão, property-based, combinatório, fuzz |

## Instalação pelo repositório

Instalar e usar a skill no Codex ou no Cursor não exige `OPENAI_API_KEY`, `CURSOR_API_KEY` nem configuração no GitHub. Essas credenciais pertencem somente aos benchmarks automatizados mantidos neste repositório.

Codex e Cursor reconhecem skills em `.agents/skills`. Escolha um dos métodos abaixo.

### Codex com Skill Installer

No Codex, envie:

```text
Use $skill-installer para instalar a skill deste repositório:
https://github.com/andreferraro/skill-suite-tests
```

### Cursor pela interface

1. Abra **Customize**.
2. Entre em **Rules** e clique em **Add Rule**.
3. Selecione **Remote Rule (GitHub)**.
4. Informe `https://github.com/andreferraro/skill-suite-tests`.
5. Confira `skill-suite-tests` em **Customize > Skills**.

### Clone global no Windows

```powershell
$skillsRoot = Join-Path $env:USERPROFILE ".agents\skills"
$skillPath = Join-Path $skillsRoot "skill-suite-tests"
New-Item -ItemType Directory -Force $skillsRoot | Out-Null
git clone https://github.com/andreferraro/skill-suite-tests.git $skillPath
```

### Clone global no macOS ou Linux

```bash
mkdir -p "$HOME/.agents/skills"
git clone \
  https://github.com/andreferraro/skill-suite-tests.git \
  "$HOME/.agents/skills/skill-suite-tests"
```

### Somente em um projeto

Execute na raiz do projeto que será testado:

```bash
git clone \
  https://github.com/andreferraro/skill-suite-tests.git \
  .agents/skills/skill-suite-tests
```

Para compartilhar a mesma versão com a equipe, use um submódulo:

```bash
git submodule add \
  https://github.com/andreferraro/skill-suite-tests.git \
  .agents/skills/skill-suite-tests
git commit -m "build: add skill-suite-tests"
```

### Conferência

Windows:

```powershell
Test-Path "$env:USERPROFILE\.agents\skills\skill-suite-tests\SKILL.md"
```

macOS ou Linux:

```bash
test -f "$HOME/.agents/skills/skill-suite-tests/SKILL.md" && echo "Skill instalada"
```

Codex detecta alterações automaticamente. Se a skill ainda estiver ausente, reinicie a ferramenta. No Cursor, abra **Customize**, entre em **Skills** e confira `skill-suite-tests`.

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

No Codex, mencione a skill com `$`:

```text
Use $skill-suite-tests na criação de pagamentos. Prove idempotência sob chamadas concorrentes e rollback após falha no insert.
```

No Cursor, selecione a skill com `/`:

```text
/skill-suite-tests Teste a recuperação de senha. Cubra loading, anúncio de erro, teclado, acessibilidade e respostas assíncronas obsoletas.
```

O pedido funciona melhor com estas informações:

1. Alvo: tela, componente, endpoint, serviço, job, evento ou jornada.
2. Comportamento: regra, critério de aceite, contrato ou bug conhecido.
3. Risco: falha e impacto que precisam ser detectados.
4. Ambiente: local, CI, staging, browser, banco ou broker disponível.
5. Restrições: dados, serviços externos, carga, duração e permissões.
6. Entrega: criar, executar, diagnosticar ou preparar os testes.

Exemplo para uma jornada:

```text
Use $skill-suite-tests no checkout. Cubra UI, API, persistência, evento de pedido criado e confirmação ao cliente. Reutilize a stack atual e execute o conjunto mínimo capaz de provar esses riscos.
```

Exemplo para performance:

```text
Use $skill-suite-tests na busca. Prepare smoke, carga e pico. Marque thresholds ausentes como <definir> e execute somente no ambiente autorizado.
```

## Entrega do agente

A resposta humana apresenta:

- suporte validado ou adaptável;
- classificação nos quatro eixos;
- base de teste e riscos rastreáveis;
- fronteiras, cenários, dados e oráculos;
- arquivos alterados;
- comandos executados e resultados;
- prova de sensibilidade;
- limitações e itens `<definir>`.

Automações também podem exigir `test-evidence.json`. O contrato está em [`schemas/test-evidence.v1.json`](schemas/test-evidence.v1.json) e há um [`exemplo validado`](examples/test-evidence.example.json).

```bash
python scripts/validate_test_evidence.py test-evidence.json
```

## Credenciais e custo

O uso comum acontece dentro do Codex ou do Cursor instalado pelo usuário e segue o plano ou provedor configurado nessa ferramenta.

Os secrets `OPENAI_API_KEY` e `CURSOR_API_KEY` aparecem apenas nos benchmarks de manutenção. Quem instala a skill para testar um sistema não precisa cadastrar esses secrets.

Os benchmarks pagos nunca são acionados por push, pull request, merge ou release. A execução exige abertura manual do workflow, escolha do escopo, confirmação do teto de chamadas e autorização explícita. Com a autorização desmarcada, o workflow mostra o plano e encerra sem chamar agentes. O runner também rejeita a execução sem `--max-agent-calls`.

| Execução manual | Teto sem cache | Com todos os baselines válidos em cache |
| --- | ---: | ---: |
| Codex, um caso, uma repetição | 2 chamadas | 1 chamada |
| Codex, três casos, uma repetição | 6 chamadas | 3 chamadas |
| Codex e Cursor, três casos, uma repetição | 12 chamadas | 6 chamadas |
| Codex e Cursor, três casos, três repetições | 36 chamadas | 18 chamadas |

Uma chamada não tem preço fixo. O valor depende do modelo e dos tokens processados. O teto controla a quantidade de chamadas e evita execuções acidentais; o consumo em moeda deve ser acompanhado nos provedores.

## Evals

Os evals comparam o mesmo agente, projeto e pedido em dois modos: baseline sem a skill e tratamento com invocação explícita. Os dois modos recebem o mesmo schema e validador do relatório, evitando vantagem artificial de formato. Os testes gerados precisam passar na implementação correta, detectar os mutantes, cobrir os riscos, preservar produção e manifests e gerar evidência válida. O gate também rejeita agente, caso, modo ou repetição ausente ou duplicada.

Consulte [`evals/README.md`](evals/README.md) para casos, mutações, pontuação, comandos e gates.

Validação determinística local:

```bash
python -m unittest discover -s tests -v
python scripts/validate_repository.py
python evals/validate_fixtures.py
```

Essa validação não usa agentes nem consome créditos de API.

## Estrutura

- [`SKILL.md`](SKILL.md): contrato e fluxo do agente.
- [`scripts/detect_test_context.py`](scripts/detect_test_context.py): inventário determinístico da stack e de sinais de risco confirmáveis no código.
- [`scripts/prove_test_sensitivity.py`](scripts/prove_test_sensitivity.py): mutação local de uma ocorrência, execução do teste e restauração garantida do arquivo.
- [`scripts/validate_test_evidence.py`](scripts/validate_test_evidence.py): validação semântica do relatório.
- [`schemas/test-evidence.v1.json`](schemas/test-evidence.v1.json): contrato JSON Schema.
- [`references/`](references): taxonomia, oráculos, ecossistemas e bases técnicas.
- [`evals/`](evals): fixtures, graders, mutantes, runner e agregador.
- [`tests/`](tests): testes unitários dos scripts e do harness.

## Segurança operacional

- Credenciais dos benchmarks entram somente por variáveis de ambiente ou GitHub Actions secrets.
- O runner remove tokens e credenciais alheias antes de iniciar agentes.
- Cada execução usa um contêiner descartável com raiz somente leitura.
- O agente recebe somente a fixture e um home temporário. Graders, mutantes, repositório e credenciais de produção ficam fora do contêiner.
- Carga, estresse, fuzz externo e injeção de falhas exigem ambiente autorizado.
- Cleanup fica restrito aos recursos criados pelo teste.

## Contribuição e release

O repositório usa Gitflow:

- `main`: versões publicadas.
- `develop`: integração.
- `feature/*`: mudanças em desenvolvimento.
- `release/*`: preparação da versão.
- `hotfix/*`: correções originadas de `main`.

Commits seguem Conventional Commits. Uma release exige qualidade estrutural, fixtures verdes e aprovação manual do benchmark de release com Codex e Cursor.

As branches estão protegidas no GitHub:

- `develop` exige pull request atualizado, checks de qualidade e conversas resolvidas;
- `main` exige os mesmos controles de qualidade;
- as regras também valem para administradores e bloqueiam force push e exclusão das branches.

Os evals pagos ficaram fora dos checks automáticos obrigatórios. O gate de eficácia continua sendo critério de publicação da versão, executado uma única vez quando a release estiver pronta.

### Publicação da v0.3.0

Configuração atual em **Settings > Secrets and variables > Actions**:

| Tipo | Nome | Estado |
| --- | --- | --- |
| Secret | `OPENAI_API_KEY` | Cadastrado; crédito disponível precisa ser conferido no provedor antes de uma execução autorizada |
| Secret | `CURSOR_API_KEY` | Cadastrado, validação pendente do eval de release |
| Variable | `CODEX_EVAL_MODEL` | Cadastrada |
| Variable | `CURSOR_EVAL_MODEL` | Cadastrada |

As chaves devem ser cadastradas diretamente no GitHub. Evite colocá-las em arquivos, comandos com valor literal, commits ou mensagens do PR.

Fluxo de publicação:

1. Faça o merge da feature em `develop` depois dos checks gratuitos de qualidade.
2. Crie `release/0.3.0` a partir de `develop` e abra um PR para `main`.
3. Execute **Manual release evals** com uma repetição para diagnóstico somente quando o código estiver pronto.
4. Corrija localmente e repita apenas o agente ou caso necessário em **Manual agent evals**.
5. Execute a certificação final com três repetições por caso para Codex e Cursor uma única vez.
6. Depois do gate aprovado, faça o merge em `main`, crie a tag `v0.3.0` e sincronize `main` com `develop`.

A release permanece pendente se o tratamento não superar o baseline. Os critérios e os tetos de chamadas estão em [`evals/README.md`](evals/README.md).

## Referências

- [Skills no Codex](https://developers.openai.com/codex/skills)
- [Codex em modo não interativo](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Agent Skills no Cursor](https://cursor.com/docs/skills)
- [Cursor CLI em modo headless](https://docs.cursor.com/en/cli/headless)
- [Apresentação da Skill Suite Tests](https://docs.google.com/presentation/d/10icBAwszr-oIcf-SeNOB2QKGF9NQE1qs7TGqt0nVeQY/edit?usp=sharing)
