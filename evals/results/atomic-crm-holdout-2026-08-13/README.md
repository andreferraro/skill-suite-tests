# Holdout externo: Atomic CRM

Avaliação pareada executada em 13 de agosto de 2026 sobre o [`usePapaParse`](https://github.com/marmelab/atomic-crm/blob/167a4cdb652b1ab2b4b030831cfa7adcf2099321/src/components/atomic-crm/misc/usePapaParse.tsx) do Atomic CRM, no commit `167a4cdb652b1ab2b4b030831cfa7adcf2099321`.

Baseline e tratamento receberam o mesmo projeto, modelo `gpt-5.3-codex-low`, pedido e contrato de evidência. O tratamento acrescentou somente a invocação da Skill Suite Tests. O agente não recebeu os cinco mutantes nem o grader.

| Resultado | Baseline | Com a skill |
| --- | ---: | ---: |
| Testes gerados | 4 | 5 |
| Testes aprovados na implementação correta | Sim | Sim |
| Mutation score | 60% | 80% |
| Gate técnico | Reprovado | Aprovado |
| Alteração indevida em produção | 0 | 0 |
| Código alvo restaurado após mutações | Sim | Sim |

Ganho observado: **20 pontos percentuais**. A skill detectou quatro dos cinco defeitos ocultos. O mutante sobrevivente remove a proteção contra callback tardio após reset durante o parsing.

Este resultado comprova ganho em um projeto open source real e em uma execução pareada. Ele complementa a matriz sintética da `v0.3.0`; uma única execução não substitui a certificação completa de release com três repetições em Codex e Cursor.

## Artefatos

- `prompt.txt`: solicitação idêntica usada nos dois modos.
- `baseline-usePapaParse.test.tsx` e `skill-usePapaParse.test.tsx`: testes produzidos.
- `baseline-test-evidence.json` e `skill-test-evidence.json`: relatórios estruturados.
- `baseline-grade.json` e `skill-grade.json`: execução, mutações e resultados do grader.
- `baseline-run-meta.json` e `skill-run-meta.json`: modelo, duração, modo e código de saída.
- `comparison.json`: comparação final do par.

Os relatórios preservam comandos executados, saídas relevantes, caminhos alterados e o resultado individual de cada mutação.
