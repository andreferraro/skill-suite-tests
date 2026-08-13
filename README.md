# Skill Suite Tests

[![Quality](https://github.com/andreferraro/skill-suite-tests/actions/workflows/quality.yml/badge.svg)](https://github.com/andreferraro/skill-suite-tests/actions/workflows/quality.yml)
[![Certification: v0.3.0 passed](https://img.shields.io/badge/certification-v0.3.0%20passed-2ea44f)](evals/results/v0.3.0-certification.json)
[![Release](https://img.shields.io/github/v/release/andreferraro/skill-suite-tests)](https://github.com/andreferraro/skill-suite-tests/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Skill para orientar Codex e Cursor na criação de testes automatizados guiados por risco. Você informa a parte do sistema e o risco relevante. O agente inspeciona a stack, escolhe a menor fronteira capaz de provar o comportamento, implementa os testes, executa a suíte e relata evidências.

[Ver apresentação](https://docs.google.com/presentation/d/10icBAwszr-oIcf-SeNOB2QKGF9NQE1qs7TGqt0nVeQY/edit?usp=sharing)

![Diagrama dos tipos de teste organizados por propósito, nível, qualidade e técnica](assets/linkedin-tipos-de-testes-diagrama.png)

## Comece em 2 minutos

Você precisa de Git e do Codex ou Cursor. Chaves de API e configuração no GitHub ficam fora do uso comum.

No Codex, envie:

```text
Use $skill-installer para instalar a skill deste repositório:
https://github.com/andreferraro/skill-suite-tests
```

Depois, faça um pedido com alvo e risco:

```text
Use $skill-suite-tests no checkout. Cubra cálculo do total, idempotência do pagamento e rollback quando a persistência falhar.
```

No Cursor, abra **Customize > Rules > Add Rule > Remote Rule (GitHub)**, informe a URL do repositório e use:

```text
/skill-suite-tests Teste a recuperação de senha. Cubra loading, erro, teclado, acessibilidade e respostas assíncronas obsoletas.
```

Veja a [instalação detalhada](#instalação-pelo-repositório) e os [exemplos de uso](#como-usar).

## Como a skill prova que ajuda

A certificação é um experimento pareado. Baseline e tratamento recebem o mesmo agente, modelo, pedido, projeto e contrato de evidência. A única diferença é o uso explícito da skill. A release passa quando essa diferença produz testes melhores de forma repetível.

| Proteção | Critério aplicado |
| --- | --- |
| Comparação justa | Mesmo agente, modelo, pedido, fixture e schema nos dois modos |
| Avaliação cega | Riscos esperados, graders e mutantes ficam fora do workspace do agente |
| Sensibilidade real | Os testes passam na implementação correta e precisam detectar defeitos conhecidos |
| Segurança da mudança | Código de produção e manifests permanecem intactos |
| Evidência reproduzível | Comandos, resultados, riscos e limitações precisam formar um relatório válido |
| Repetibilidade | Três repetições por agente e caso, com aprovação crítica em pelo menos duas |
| Ganho comprovado | Mediana mínima de 85, ganho mínimo de 8 pontos e melhora em dois dos três casos por agente |
| Isolamento e custo | Contêiner descartável, graders ocultos e execução paga somente manual, com teto de chamadas |

Falhas individuais permanecem nos artefatos e participam da consolidação. Um baseline perfeito pode empatar em um caso, mas a release ainda precisa demonstrar ganho agregado sem regressão relevante.

Leia a [metodologia completa](evals/README.md#integridade-da-certificação) e consulte o [relatório auditável da v0.3.0](evals/results/v0.3.0-certification.json).

## Estado da v0.3.0

A versão `v0.3.0` foi certificada no commit [`7da3f5c`](https://github.com/andreferraro/skill-suite-tests/commit/7da3f5c243c80b259c330335fe29adab9e80da0f) e publicada pelo [PR #9](https://github.com/andreferraro/skill-suite-tests/pull/9). O [relatório consolidado](evals/results/v0.3.0-certification.json) preserva as medianas, os gates e os links para as execuções reais.

A `v0.3.1` reúne os ajustes de documentação, segurança e governança necessários para distribuição pública. O runtime da skill permanece igual ao certificado na `v0.3.0`, por isso a patch não repete os evals pagos.

| Evidência | Resultado |
| --- | --- |
| Projetos de referência | [3 implementados e aprovados](evals/results/fixture-validation.json) |
| Mutantes conhecidos | [12 implementados e 12 detectados](evals/results/fixture-validation.json) |
| Validação local dos scripts | 55 testes unitários aprovados |
| CI de qualidade | [Aprovada no Linux e Windows](https://github.com/andreferraro/skill-suite-tests/actions/workflows/quality.yml) |
| Certificação Codex | 3 repetições por caso, gate agregado aprovado |
| Certificação Cursor | 3 repetições por caso, gate agregado aprovado |
| Mediana da skill | 100/100 |
| Ganho mediano sobre baseline | 16,875 pontos |
| Certificação técnica | `v0.3.0`, aprovada e publicada pelo PR #9 |
| Release pública atual | `v0.3.1`, sem alteração no runtime certificado |

### Baseline versus skill

| Agente | Caso | Baseline | Com a skill | Ganho |
| --- | --- | ---: | ---: | ---: |
| Codex | Pagamento | 87,5 | 100 | +12,5 |
| Codex | Consumidor de pedidos | 100 | 100 | 0 |
| Codex | Recuperação de senha | 31,25 | 96,25 | +65 |
| Cursor | Pagamento | 78,75 | 100 | +21,25 |
| Cursor | Consumidor de pedidos | 96,25 | 100 | +3,75 |
| Cursor | Recuperação de senha | 27,5 | 96,25 | +68,75 |

Os valores são medianas de três repetições por agente, caso e modo. A certificação exige aprovação crítica em pelo menos duas repetições. As falhas individuais continuam disponíveis nos artefatos dos runs e participam da mediana.

## O que esta skill é

- Um guia operacional para agentes com acesso ao código, terminal e ferramentas do projeto.
- Um processo de seleção de testes por risco, arquitetura, fronteira e oráculo.
- Uma matriz de rastreabilidade entre risco, mecanismo protetivo, estado, cenário e oráculo.
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

O suporte validado cobre as três fixtures, os 12 mutantes e os evals pareados da `v0.3.0`. Outros ecossistemas continuam como suporte adaptável, sem benchmark publicado.

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

Em fluxos assíncronos, a skill separa estados que possuem proteções diferentes. Cancelamento durante parsing, processamento ou espera entre lotes vira cenários distintos quando cada fase pode falhar de uma forma própria. O teste confirma o estado cancelado antes de liberar callbacks obsoletos, usando payload capaz de causar um efeito proibido caso o guard falhe. Erros fatais e erros parciais retornados com os dados também recebem oráculos distintos. A prova de sensibilidade remove temporariamente cada proteção relevante e confirma que o cenário correspondente detecta a falha.

## Instalação pelo repositório

Instalar e usar a skill no Codex ou no Cursor não exige `OPENAI_API_KEY`, `CURSOR_API_KEY` nem configuração no GitHub. Essas credenciais pertencem somente aos benchmarks automatizados mantidos neste repositório.

Codex e Cursor reconhecem skills em `.agents/skills`. Escolha um dos métodos abaixo.

### Codex com Skill Installer

No Codex, envie:

```text
Use $skill-installer para instalar a skill deste repositório:
https://github.com/andreferraro/skill-suite-tests
```

Esse fluxo foi validado instalando o conteúdo da raiz do repositório, incluindo `SKILL.md`, metadados, scripts, schema e referências.

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
- [`scripts/analyze_test_target.py`](scripts/analyze_test_target.py): inventário focado de estados, ações de ciclo de vida, fronteiras assíncronas e guards protetivos do alvo.
- [`scripts/prove_test_sensitivity.py`](scripts/prove_test_sensitivity.py): mutação temporária restaurável, incluindo seleção por ocorrência para guards repetidos.
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

Leia o [guia de contribuição](CONTRIBUTING.md), a [política de segurança](SECURITY.md) e o [código de conduta](CODE_OF_CONDUCT.md) antes de abrir uma contribuição.

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

### Certificação da v0.3.0

Configuração atual em **Settings > Secrets and variables > Actions**:

| Tipo | Nome | Estado |
| --- | --- | --- |
| Secret | `OPENAI_API_KEY` | Validado na certificação Codex |
| Secret | `CURSOR_API_KEY` | Validado na certificação Cursor |
| Variable | `CODEX_EVAL_MODEL` | Validada na certificação Codex |
| Variable | `CURSOR_EVAL_MODEL` | Validada na certificação Cursor |

As chaves devem ser cadastradas diretamente no GitHub. Evite colocá-las em arquivos, comandos com valor literal, commits ou mensagens do PR.

Execuções que compõem a certificação:

- Codex: [repetição 1](https://github.com/andreferraro/skill-suite-tests/actions/runs/31648288379), [repetição 2](https://github.com/andreferraro/skill-suite-tests/actions/runs/31648786954) e [repetição 3](https://github.com/andreferraro/skill-suite-tests/actions/runs/31649260230).
- Cursor: [repetição 1](https://github.com/andreferraro/skill-suite-tests/actions/runs/31649784413), [repetição 2](https://github.com/andreferraro/skill-suite-tests/actions/runs/31650136006) e [repetição 3](https://github.com/andreferraro/skill-suite-tests/actions/runs/31650494601).

Os runs foram executados no commit certificado e consolidados pelo mesmo agregador usado no gate de release. Repetir a certificação exige uma nova decisão explícita de custo. Os critérios e os tetos de chamadas estão em [`evals/README.md`](evals/README.md).

## Referências

- [Skills no Codex](https://developers.openai.com/codex/skills)
- [Codex em modo não interativo](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Agent Skills no Cursor](https://cursor.com/docs/skills)
- [Cursor CLI em modo headless](https://docs.cursor.com/en/cli/headless)
- [Apresentação da Skill Suite Tests](https://docs.google.com/presentation/d/10icBAwszr-oIcf-SeNOB2QKGF9NQE1qs7TGqt0nVeQY/edit?usp=sharing)
