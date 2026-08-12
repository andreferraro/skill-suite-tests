# Evals da Skill Suite Tests

O benchmark mede se a skill melhora testes gerados por Codex e Cursor. Baseline e tratamento recebem o mesmo pedido curto, o mesmo projeto e o mesmo contrato de evidência. Os riscos esperados, graders e mutantes ficam fora do workspace entregue ao agente. Assim, o benchmark mede descoberta e tratamento de riscos, sem entregar a resposta no prompt.

## Certificação publicada

A `v0.3.0` foi certificada no commit [`7da3f5c`](https://github.com/andreferraro/skill-suite-tests/commit/7da3f5c243c80b259c330335fe29adab9e80da0f), com três repetições para Codex e Cursor em cada caso. O [relatório consolidado](results/v0.3.0-certification.json) passou o gate com mediana da skill de 100/100 e ganho mediano de 16,875 pontos.

| Agente | API | Eventos | Web | Aprovações críticas com a skill |
| --- | ---: | ---: | ---: | --- |
| Codex | 100 | 100 | 96,25 | 3/3, 2/3 e 2/3 |
| Cursor | 100 | 100 | 96,25 | 3/3, 3/3 e 3/3 |

As notas são medianas. O relatório contém os baselines, ganhos e links para todos os runs. Resultados individuais reprovados permanecem registrados e contam na consolidação.

## Integridade da certificação

O benchmark foi desenhado para medir a contribuição da skill, preservar resultados desfavoráveis e permitir auditoria por outra pessoa.

### Comparação pareada

Baseline e tratamento usam o mesmo agente, modelo, pedido curto, fixture e schema de evidência. O tratamento acrescenta somente a invocação da skill. A impressão digital do cache inclui agente, modelo, fixture, prompt, contrato, grader, mutantes, harness e imagem das CLIs. Qualquer mudança relevante invalida o baseline armazenado.

### Avaliação cega

O workspace entregue ao agente contém apenas o projeto e a solicitação. Riscos obrigatórios, graders, implementações de referência e mutantes permanecem no host. O agente precisa descobrir os riscos pelo comportamento e pelo código disponível.

### Prova de sensibilidade

Cada suíte gerada é executada na implementação correta e contra quatro mutações conhecidas do caso. A pontuação considera execução, mutation score, cobertura dos riscos, integração com a stack e validade das evidências. Cobertura de linhas isolada não substitui a detecção do defeito.

### Preservação das falhas

Execuções reprovadas continuam nos artefatos e entram na mediana. A certificação exige três repetições por agente e caso e aprovação crítica em pelo menos duas. Uma amostra ruim não é descartada nem substituída por uma nova tentativa conveniente.

### Isolamento e segurança

Cada agente roda em contêiner descartável, com raiz somente leitura, capacidades removidas e mounts explícitos. O repositório do benchmark, os graders e os mutantes ficam fora do alcance do agente. Hashes calculados antes e depois da execução fazem o gate rejeitar mudanças em código de produção ou manifests, além de relatórios sem comandos ou riscos rastreáveis.

### Gate de publicação

A release exige matriz completa, mediana da skill de pelo menos 85/100, ganho mediano mínimo de 8 pontos, melhoria em dois dos três casos por agente e nenhuma regressão maior que 5 pontos. Um caso com baseline perfeito pode terminar empatado, desde que o tratamento preserve a qualidade e o ganho agregado permaneça comprovado.

### Reprodutibilidade e custo

O relatório consolidado registra commit, agente, caso, modo, repetição, notas e links para os runs. Evals pagos exigem acionamento manual, autorização explícita e teto de chamadas. Pull requests, merges e tags executam somente as validações determinísticas gratuitas.

## Casos

| Caso | Stack | Riscos obrigatórios |
| --- | --- | --- |
| `web-password-reset` | React, TypeScript, Vitest, Testing Library e Playwright | loading, anúncio de erro, teclado e acessibilidade, resposta obsoleta |
| `api-payment` | FastAPI, Python, pytest e SQLite | idempotência, concorrência, validação e rollback |
| `events-order-consumer` | Node.js, TypeScript, Vitest, RabbitMQ, PostgreSQL e Testcontainers | deduplicação, retry, DLQ, ordering e correlação |

## Mutantes

| Caso | Mutante | Defeito |
| --- | --- | --- |
| Web | `loading-not-disabled` | Permite novo envio durante loading |
| Web | `error-not-announced` | Remove o papel de alerta do erro |
| Web | `input-without-accessible-name` | Remove a associação do label |
| Web | `stale-response-wins` | Aceita uma resposta assíncrona antiga |
| API | `unstable-idempotent-response` | Retorna novo ID para a mesma chave |
| API | `deferred-concurrent-transaction` | Enfraquece a aquisição do lock transacional |
| API | `zero-amount-accepted` | Aceita pagamento com valor zero |
| API | `failed-insert-committed` | Persiste o insert depois da falha simulada |
| Eventos | `deduplication-disabled` | Processa novamente uma mensagem conhecida |
| Eventos | `retry-attempt-not-incremented` | Republica sem incrementar a tentativa |
| Eventos | `dlq-one-attempt-late` | Atrasa o envio para a DLQ |
| Eventos | `correlation-id-lost` | Remove o correlation ID na republicação |

## Pontuação

| Critério | Pontos |
| --- | ---: |
| Testes passam na implementação correta | 30 |
| Mutation score | 35 |
| Cobertura dos riscos obrigatórios | 15 |
| Integração sem mudanças em produção ou manifests | 10 |
| Relatório de evidência válido | 10 |

Gate por execução:

- suíte executável;
- produção preservada;
- mutation score mínimo de 80%;
- `test-evidence.json` válido;
- nota mínima de 80/100.

Gate agregado:

- matriz completa para todos os agentes, casos, modos e repetições esperados;
- mediana da skill mínima de 85/100;
- ganho mediano mínimo de 8 pontos sobre o baseline;
- melhoria em pelo menos dois dos três casos por agente;
- regressão máxima de 5 pontos;
- aprovação crítica em duas das três repetições de release.

## Validação dos fixtures

Executa os testes de referência na implementação correta e aplica os 12 mutantes:

```bash
python evals/validate_fixtures.py \
  --output evals/results/fixture-validation.json
```

Inclui o smoke real de RabbitMQ e PostgreSQL via Testcontainers:

```bash
python evals/validate_fixtures.py \
  --infrastructure \
  --output evals/results/fixture-validation.json
```

## Eval pareado local

Pré-requisitos:

- `OPENAI_API_KEY` ou `CURSOR_API_KEY` no ambiente;
- projeto de API com acesso e créditos disponíveis para as chamadas executadas;
- Node.js, Python e Docker;
- nome exato do modelo passado por `--model`.

Construa a imagem isolada usada pela CI:

```bash
docker build \
  --file evals/agent.Dockerfile \
  --tag skill-suite-tests-eval-agent:local \
  .
```

A imagem fixa as versões do Codex CLI e do Cursor Agent CLI. O pacote do Cursor também é verificado por SHA-256. O agente recebe dois mounts graváveis: a fixture e um diretório home descartável. Dependências Python exclusivas da execução ficam no home, fora da árvore analisada. O repositório, os graders e os mutantes ficam fora do contêiner.

Codex em um caso:

```bash
python evals/run_eval.py \
  --agent codex \
  --case web-password-reset \
  --repetitions 1 \
  --max-agent-calls 2 \
  --model <modelo-codex> \
  --agent-container-image skill-suite-tests-eval-agent:local \
  --enforce-gate
```

Release completa:

```bash
python evals/run_eval.py \
  --agent codex \
  --repetitions 3 \
  --max-agent-calls 18 \
  --model <modelo-codex> \
  --agent-container-image skill-suite-tests-eval-agent:local \
  --artifacts evals/artifacts/codex

python evals/run_eval.py \
  --agent cursor \
  --repetitions 3 \
  --max-agent-calls 18 \
  --model <modelo-cursor> \
  --agent-container-image skill-suite-tests-eval-agent:local \
  --artifacts evals/artifacts/cursor

python evals/aggregate_reports.py \
  --input evals/artifacts \
  --output evals/artifacts/release-summary.json \
  --repetitions 3 \
  --agent codex \
  --agent cursor \
  --case web-password-reset \
  --case api-payment \
  --case events-order-consumer \
  --enforce-gate
```

Use `--dry-run` para conferir comandos e isolamento sem consumir APIs.

Use `--repetition-start 2` ou `--repetition-start 3` para continuar uma certificação interrompida sem repetir amostras anteriores. O número é gravado nos resultados e validado na consolidação final.

Uma execução real exige `--max-agent-calls`. O runner calcula o total antes de iniciar qualquer agente e encerra se ultrapassar o teto. Sem cache, cada par baseline e skill usa duas chamadas por agente, caso e repetição.

Use `--baseline-cache evals/baseline-cache` para reaproveitar o baseline quando agente, modelo, fixture, prompt, contrato, grader, mutantes, harness e imagem das CLIs continuarem equivalentes. A impressão digital invalida o cache quando qualquer um desses elementos muda. Alterações exclusivas na skill preservam o baseline e reduzem o próximo par a uma chamada de tratamento.

No GitHub Actions, cada repetição usa uma chave de cache própria. Isso permite continuar as amostras 2 e 3 sem misturar resultados e sem recalcular um baseline já salvo para a mesma impressão digital.

Sem `--agent-container-image`, o runner usa as CLIs instaladas no host. Esse modo serve para diagnóstico local e exige `codex` ou `cursor-agent` no `PATH`.

## GitHub Actions

- `quality.yml`: estrutura, scripts, schema, links, segredos, fixtures e mutantes.
- `agent-evals.yml`: execução manual e seletiva de Codex ou Cursor, com um caso ou os três.
- `release-evals.yml`: execução manual de Codex, Cursor ou ambos, com uma ou três repetições.

Pushes, pull requests, merges e tags executam somente `quality.yml`. As proteções de `develop` e `main` dependem dos cinco checks gratuitos de qualidade. Os evals pagos são um gate manual de publicação, separado do CI cotidiano.

### Tetos de chamadas

| Escopo | Primeira execução | Com todos os baselines válidos em cache |
| --- | ---: | ---: |
| Um agente, um caso, uma repetição | até 2 | 1 |
| Um agente, três casos, uma repetição | até 6 | 3 |
| Dois agentes, três casos, uma repetição | até 12 | 6 |
| Um agente, três casos, três repetições | até 18 | 9 |
| Dois agentes, três casos, três repetições | até 36 | 18 |

O formulário do workflow mostra e valida o teto antes de liberar os jobs. Deixe a autorização desmarcada para executar somente a prévia gratuita. O runner aplica uma segunda trava. Esses números representam chamadas, não dólares. O custo varia conforme modelo e tokens.

Cada job de caso exige execução válida e gate técnico aprovado. A comparação de ganho fica no job agregado, porque um caso pode ter baseline perfeito e ganho zero sem representar regressão da skill.

### Configuração do repositório

Configure em **Settings > Secrets and variables > Actions**:

- secrets: `OPENAI_API_KEY` e `CURSOR_API_KEY`;
- variables: `CODEX_EVAL_MODEL` e `CURSOR_EVAL_MODEL`.

Essa configuração é exclusiva da manutenção do benchmark no GitHub Actions. Instalar ou usar a skill no Codex ou Cursor não depende desses secrets e variables.

Os modelos devem usar os nomes exatos aceitos pelas respectivas CLIs. Os workflows entregam cada chave somente ao job do agente correspondente e publicam logs, resultados individuais e o resumo consolidado como artefatos.

Cada resultado preserva em `workspace-output` os testes gerados e o `test-evidence.json`. Isso permite auditar a nota sem expor o workspace temporário, os graders ou os mutantes ao agente.

Cada execução cria um home descartável dentro do contêiner. O Codex autentica com `codex login --with-api-key`; a chave entra pela entrada padrão e fica fora do comando e dos artefatos. O Cursor recebe somente `CURSOR_API_KEY`. Ausência de crédito, autenticação inválida ou falha da CLI são registradas como falhas de execução e bloqueiam o gate.

O Codex usa `danger-full-access` somente dentro desse contêiner controlado, conforme a orientação oficial para automação isolada. O contêiner usa raiz somente leitura, capacidades removidas, `no-new-privileges` e mounts explícitos. O grader continua no host e avalia a fixture depois que o agente termina.

Também é possível cadastrar pela GitHub CLI. Os comandos de secret solicitam o valor de forma interativa:

```bash
gh secret set OPENAI_API_KEY
gh secret set CURSOR_API_KEY
gh variable set CODEX_EVAL_MODEL --body "<modelo-codex>"
gh variable set CURSOR_EVAL_MODEL --body "<modelo-cursor>"
```

Não coloque chaves em `--body`, arquivos versionados, logs ou mensagens do pull request.

### Fluxo da v0.3.0

1. Use os checks gratuitos em cada pull request para validar scripts, fixtures, mutantes, links e segredos.
2. Faça uma execução manual de diagnóstico somente quando a release estiver pronta.
3. Se houver falha, ajuste localmente e execute apenas o caso ou agente afetado.
4. Rode três repetições para Codex e Cursor uma única vez como certificação final.
5. Publique a tag somente depois da aprovação do resumo agregado.
6. Sincronize a release de `main` para `develop`.

Ausência de credencial ou modelo encerra o workflow no preflight. Falha em score, mutation score, cobertura de risco, preservação do código ou evidência válida bloqueia a release.
