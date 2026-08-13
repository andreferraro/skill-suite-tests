# Taxonomia e seleção de testes de sistemas

Classificar o trabalho em até quatro eixos. Um cenário pode ser `regressão + integração + concorrência + tabela de decisão`.

## Sumário

- [Eixo 1: propósito](#eixo-1-propósito)
- [Eixo 2: nível](#eixo-2-nível)
- [Eixo 3: atributo de qualidade](#eixo-3-atributo-de-qualidade)
- [Eixo 4: técnica ou perfil](#eixo-4-técnica-ou-perfil)
- [Padrões de seleção](#padrões-de-seleção)

## Eixo 1: propósito

### Smoke

Confirmar rapidamente que build, deploy, configuração e capacidades críticas estão operacionais.

- Manter poucos cenários, execução curta e alta estabilidade.
- Exercitar uma capacidade representativa, além de health checks superficiais.
- Separar smoke funcional de smoke de performance.

### Confirmação

Comprovar que um defeito específico foi corrigido.

- Reproduzir o cenário original ou o menor equivalente.
- Demonstrar a sensibilidade do teste à falha corrigida.
- Registrar a relação com bug, incidente ou commit.

### Regressão

Detectar efeitos adversos causados por uma mudança.

- Fazer análise de impacto antes de selecionar casos.
- Cobrir o comportamento alterado e fronteiras materialmente afetadas.
- Evitar congelar detalhes incidentais por snapshots amplos.

### Aceitação

Demonstrar prontidão contra critérios de negócio, operação, contrato ou regulação.

- Derivar cenários de critérios rastreáveis.
- Usar linguagem observável pelo stakeholder.
- Separar aceite funcional, operacional, contratual e regulatório quando as evidências diferirem.

## Eixo 2: nível

### Unidade

Exercitar uma regra, função, classe, hook, reducer ou transformação em isolamento.

- Adequado para lógica determinística, limites e combinações numerosas.
- Substituir apenas colaboradores externos à unidade escolhida.
- Manter feedback rápido e diagnóstico preciso.

### Componente

Exercitar um componente de UI, controller, handler, serviço ou módulo com sua colaboração local.

- Frontend: renderização, eventos, estado, acessibilidade e chamadas controladas.
- Backend: validação, mapeamento, regra e integração em processo.
- Usar doubles na borda externa ao componente.

### Contrato

Verificar entendimento compartilhado entre consumidor e provedor.

- Schema e protocolo: OpenAPI, GraphQL, Protobuf, AsyncAPI ou JSON Schema.
- Expectativas do consumidor: contratos executáveis contra o provedor.
- Evolução: diff semântico entre versões.

Schema válido é apenas uma dimensão. Incluir semântica e expectativas reais quando o risco exigir.

### Integração

Exercitar colaboração entre componentes, banco, cache, browser, broker ou serviço externo dentro de uma fronteira declarada.

- Listar participantes reais e simulados.
- Verificar efeitos, transações, eventos, retries e cleanup.
- Usar infraestrutura realista para a garantia em teste.

### Sistema e ponta a ponta

Validar uma jornada crítica através do sistema completo ou de sistemas conectados.

- Selecionar poucos fluxos de alto valor.
- Usar ambiente representativo e verificar resultado final de negócio.
- Correlacionar etapas e produzir diagnóstico por fronteira.

### Sintético em ambiente

Executar uma jornada pequena e recorrente para detectar indisponibilidade ou degradação após deploy.

- Usar identidade e dados próprios.
- Limitar mutações e limpar recursos.
- Integrar com observabilidade e alertas quando aplicável.

## Eixo 3: atributo de qualidade

### Funcional

Validar regras, estados, permissões, entradas, saídas e erros previstos.

### Experiência e interface

Validar comportamento percebido pelo usuário:

- loading, vazio, sucesso, erro e retry;
- foco, teclado, ordem de leitura e acessibilidade;
- navegação, feedback, responsividade e compatibilidade de browser;
- layout e regressão visual contra baseline aprovada.

### Protocolo e compatibilidade

Validar semântica HTTP, GraphQL, gRPC, mensageria ou contrato de arquivos, além de evolução entre versões.

### Segurança e privacidade

Validar autenticação, autorização, isolamento de tenant, entrada, saída, segredos, dados, abuso de recursos e fluxos sensíveis.

Cada cenário deve ligar ameaça, ativo, precondição, controle esperado e ausência de efeito indevido.

### Performance e escalabilidade

Avaliar latência, throughput, erros, concorrência e recursos sob perfil definido.

- Medir percentis e saturação.
- Verificar corretude sob carga.
- Separar gargalo do sistema, dependência e gerador.

### Resiliência e recuperação

Avaliar timeout, falha, latência, indisponibilidade, degradação e retorno ao steady state.

### Concorrência e consistência

Avaliar interleavings, idempotência, atomicidade, ordering, deduplicação e convergência.

### Observabilidade e operabilidade

Validar traces, correlation IDs, métricas, logs, health, readiness e sinais necessários ao diagnóstico.

### Portabilidade e compatibilidade

Validar browsers, dispositivos, sistemas operacionais, resoluções, versões de runtime e configurações suportadas.

## Eixo 4: técnica ou perfil

### Técnicas baseadas em exemplos

- Particionamento de equivalência.
- Valores limite.
- Tabelas de decisão.
- Transição de estado.
- Casos de uso e jornadas.
- Pairwise e combinatório.

### Property-based

Gerar dados a partir de propriedades e invariantes.

- Definir a propriedade antes do gerador.
- Preservar seed e menor contraexemplo.
- Transformar falhas corrigidas em regressões estáveis.

### Fuzz

Explorar entradas malformadas, extremas ou inesperadas com orçamento controlado.

- Definir oráculos além da ausência de crash.
- Limitar tamanho, tempo, taxa e paralelismo.
- Separar fuzz local de exploração contra sistema externo.

### Regressão visual

Comparar renderização atual com baseline aprovada.

- Fixar viewport, browser, fontes, dados, animações e relógio.
- Definir tolerância e regiões dinâmicas.
- Revisar diferenças materiais antes de atualizar baseline.

### Injeção de falhas e chaos

- Definir steady state, hipótese, falha, blast radius e abort conditions.
- Observar degradação e recuperação.
- Preferir injeção determinística quando ela produzir evidência suficiente.

### Perfis de performance

- **Smoke:** carga mínima para validar script e ambiente.
- **Baseline:** tráfego típico para verificar metas e comparar versões.
- **Carga:** volume esperado sustentado.
- **Estresse:** volume elevado para observar degradação.
- **Pico:** aumento súbito e retorno rápido.
- **Endurance:** carga prolongada para detectar degradação lenta.
- **Breakpoint:** rampa até o limite aprovado.
- **Escalabilidade:** resposta ao aumento ou redução de recursos.

Usar `<definir>` para carga, duração ou threshold ausente e preparar o teste antes da execução.

## Padrões de seleção

- “A aplicação abriu após deploy?”: smoke + sistema + funcional.
- “O botão segue acessível por teclado?”: componente ou E2E + acessibilidade.
- “O layout mudou?”: regressão + sistema + visual.
- “O bug foi corrigido?”: confirmação + menor nível capaz de reproduzir.
- “A alteração afetou outros fluxos?”: regressão + análise de impacto.
- “O consumidor funciona com a nova versão?”: contrato + compatibilidade.
- “Dois clientes compram o último item?”: integração + concorrência e consistência.
- “O checkout aguenta o tráfego esperado?”: sistema + performance + carga.
- “Payments ficou indisponível?”: integração ou sistema + resiliência + fault injection.
- “Quero entradas inesperadas”: funcional ou segurança + property-based ou fuzz.
