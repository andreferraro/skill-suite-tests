# Evals da Skill Suite Tests

O benchmark mede se a skill melhora testes gerados por Codex e Cursor. Os graders e mutantes ficam fora do workspace entregue ao agente.

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

- `codex` para Codex;
- `cursor-agent` para Cursor;
- `OPENAI_API_KEY` ou `CURSOR_API_KEY` no ambiente;
- Node.js, Python e Docker.
- nome exato do modelo passado por `--model`.

Codex em um caso:

```bash
python evals/run_eval.py \
  --agent codex \
  --case web-password-reset \
  --repetitions 1 \
  --model <modelo-codex> \
  --enforce-gate
```

Release completa:

```bash
python evals/run_eval.py \
  --agent codex \
  --repetitions 3 \
  --model <modelo-codex> \
  --artifacts evals/artifacts/codex

python evals/run_eval.py \
  --agent cursor \
  --repetitions 3 \
  --model <modelo-cursor> \
  --artifacts evals/artifacts/cursor

python evals/aggregate_reports.py \
  --input evals/artifacts \
  --output evals/artifacts/release-summary.json \
  --repetitions 3 \
  --enforce-gate
```

Use `--dry-run` para conferir comandos e isolamento sem consumir APIs.

## GitHub Actions

- `quality.yml`: estrutura, scripts, schema, links, segredos, fixtures e mutantes.
- `agent-evals.yml`: Codex em todo pull request, uma repetição por caso.
- `release-evals.yml`: Codex e Cursor, três repetições por caso, em pull requests para `main` e por execução manual.

Configure `OPENAI_API_KEY` e `CURSOR_API_KEY` em **Settings > Secrets and variables > Actions**. Crie também as variáveis `CODEX_EVAL_MODEL` e `CURSOR_EVAL_MODEL` com os nomes exatos dos modelos. Os workflows entregam cada chave somente ao job do agente correspondente e publicam logs, resultados individuais e o resumo consolidado como artefatos.
