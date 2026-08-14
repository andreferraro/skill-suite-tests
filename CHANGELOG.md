# Changelog

## [Unreleased]

## [0.5.1] - 2026-08-13

### Corrigido

- Grader de concorrência da fixture de pagamentos sincroniza transações `DEFERRED` na fronteira de escrita, removendo dependência do escalonamento das threads.
- Documentação sincronizada com a release `v0.5.0`, os 62 testes atuais, o commit real do holdout, o fluxo dos caches e a política de versões suportadas.

## [0.5.0] - 2026-08-13

### Adicionado

- Manifesto de plugin para distribuição no ChatGPT e Codex.
- Marketplace Git instalável diretamente pelo repositório.
- Validação determinística de consistência entre plugin, marketplace e skill.

### Alterado

- Runtime movido, sem mudança de conteúdo, para `skills/skill-suite-tests`.
- Instalação atualizada para plugin no ChatGPT e Codex e skill remota no Cursor.
- Harness adaptado para instalar a skill a partir da fonte única do plugin.

### Certificação

- Conteúdo do runtime preservado em relação à `v0.4.0` certificada.
- Validação estrutural do plugin e da skill aprovada sem chamadas pagas de agentes.

## [0.4.0] - 2026-08-13

### Alterado

- Rastreabilidade explícita entre risco, mecanismo protetivo, estado ou fase, cenário e oráculo.
- Cobertura separada de cancelamento, reset, timeout, retry, desconexão e unmount em cada estado ativo relevante.
- Separação temporal entre a confirmação do cancelamento e a liquidação de callbacks obsoletos.
- Prova de sensibilidade por mecanismo e fase, evitando generalização a partir de uma única mutação.
- Saída do helper de mutação compatível com consoles Windows configurados com CP1252.
- Oráculos de callback obsoleto exigem payload capaz de produzir efeito proibido.
- Falhas fatais e erros parciais retornados com dados passam a exigir cenários distintos.

### Adicionado

- Analisador determinístico de estados, ações de ciclo de vida, fronteiras assíncronas e guards repetidos no arquivo alvo.
- Seleção `--occurrence` no helper de sensibilidade para mutar guards repetidos isoladamente.
- Holdout pareado no Atomic CRM, com artefatos publicados, ganho de 60% para 80% no mutation score e gate técnico aprovado.

### Certificação

- Três repetições aprovadas por caso no Cursor e duas de três ou mais no Codex.
- Mediana da skill de 96,25/100 e ganho mediano de 8,75 pontos.
- Baselines equivalentes reaproveitados por fingerprint; 18 chamadas de tratamento executadas.
- Uma falha individual do Codex em Web preservada nos artefatos e incluída na consolidação.

## [0.3.1] - 2026-08-12

### Adicionado

- Início rápido com instalação e primeira invocação no Codex e Cursor.
- Guia de contribuição, política de segurança, código de conduta e templates do GitHub.

### Alterado

- Documentação de instalação confirmada por uma instalação real a partir da raiz do repositório.
- Estado da release separado da certificação técnica da `v0.3.0`.
- Política de atualização deliberada para preservar a reprodutibilidade das fixtures certificadas.
- Check de links externos com retry limitado para tolerar falhas transitórias sem aceitar links quebrados.

### Certificação

- Runtime da skill inalterado em relação à `v0.3.0` certificada.
- Nenhuma execução paga necessária para esta patch documental.

## [0.3.0] - 2026-08-12

### Adicionado

- Detector determinístico de stack, runners, testes, fixtures, CI, banco, browser automation e infraestrutura.
- Schema e validador semântico para evidências de teste.
- Prova de sensibilidade por mutação controlada.
- Três projetos de referência para Web, API e eventos.
- Doze mutantes conhecidos e graders mantidos fora do workspace do agente.
- Evals pareados para Codex e Cursor em contêineres descartáveis.
- Gate de custo com execução paga exclusivamente manual e teto explícito de chamadas.

### Alterado

- Contrato da skill orientado por risco, fronteira, oráculo e evidência reproduzível.
- Suporte comprovado separado de suporte adaptável.
- Gate técnico por caso separado da comparação agregada com o baseline.

### Certificação

- 55 testes unitários aprovados em Linux e Windows.
- Três fixtures executáveis e 12 de 12 mutantes validados.
- Certificação pareada aprovada com Codex e Cursor.
- Mediana da skill de 100/100 e ganho mediano de 16,875 pontos.
