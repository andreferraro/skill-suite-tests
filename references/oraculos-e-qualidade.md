# Oráculos e qualidade dos testes

Um teste precisa falhar diante do risco que afirma detectar. Construir o oráculo a partir da base de teste, da fronteira e do impacto esperado.

## Hierarquia da base de teste

Usar, em ordem de autoridade contextual:

1. requisito, critério de aceite ou regra aprovada;
2. contrato versionado e decisão arquitetural vigente;
3. expectativa executável de consumidores suportados;
4. comportamento codificado e testes aceitos;
5. comportamento observado como baseline provisória.

Registrar conflitos entre fontes e pedir decisão quando eles mudarem o resultado esperado.

## Oráculo composto

Selecionar as dimensões que distinguem sucesso real da falha relevante:

- **Interface:** conteúdo, visibilidade, habilitação, foco, navegação, acessibilidade, layout e feedback.
- **Resposta:** status, código, headers, metadata, schema, payload e semântica.
- **Estado:** store, banco, cache, arquivos, sessão, versão, transição, commit e rollback.
- **Eventos:** conteúdo, key, headers, ordering, quantidade, deduplicação e causalidade.
- **Efeitos:** chamadas externas, notificações, arquivos e recursos criados.
- **Ausência de efeitos:** nenhuma mutação, mensagem, cobrança ou exposição indevida.
- **Tempo:** deadline, latência, expiração, debounce, retry e janela de convergência.
- **Recursos:** filas, pools, CPU, memória, conexões, quotas e saturação.
- **Observabilidade:** trace, correlation ID, logs e métricas necessários ao diagnóstico.

## Oráculos por superfície

### Frontend

Combinar asserções de comportamento com as dimensões aplicáveis:

- conteúdo e controles disponíveis para o estado atual;
- eventos de mouse, teclado, touch e formulário;
- foco, nome acessível, papel, estado e ordem de leitura;
- loading, vazio, sucesso, erro, retry e timeout;
- navegação, URL, histórico e preservação de estado;
- request disparada, parâmetros e tratamento da resposta;
- estado local, cache do cliente e persistência no browser;
- responsividade, overflow e elementos cobertos;
- screenshot comparativa quando houver baseline aprovada.

Evitar testes presos à estrutura interna do componente. Preferir consultas e interações próximas da experiência do usuário.

### HTTP e REST

- semântica do método, safety e idempotência;
- status e formato de erro;
- `Content-Type`, `Location`, `Allow`, `Retry-After`, validators e cache;
- paginação, filtros, ordenação e links;
- efeito persistido e ausência de efeito em rejeições.

Aplicar apenas capacidades exigidas pelo contrato do produto.

### GraphQL

- data parcial, array `errors` e paths;
- nullability e propagação de `null`;
- validação de query e variables;
- autorização por campo, objeto e operação;
- paginação, aliases, fragments e directives suportadas;
- compatibilidade de schema, remoção e depreciação.

### gRPC

- serviço, método e mensagens Protobuf;
- status codes e metadata;
- deadlines, cancelamento e retries;
- streaming, ordem, backpressure, half-close e encerramento;
- compatibilidade de campos e números reservados.

### Eventos, filas e webhooks

- schema, key, headers, assinatura e IDs de correlação;
- delivery semantics adotada;
- idempotência, deduplicação, ordering e replay;
- retry, backoff, DLQ e recuperação;
- consistência final dentro de janela explícita.

### Jobs e schedulers

- seleção correta de itens e janela de execução;
- idempotência, checkpoint, lock e retomada;
- efeito por item, falha parcial e reprocessamento;
- métricas, logs e status operacional;
- relógio e timezone controlados.

### Dados

- invariantes antes e depois da operação;
- transação, atomicidade e isolamento;
- integridade referencial e constraints;
- ordering, versionamento e concorrência otimista;
- migração, rollback e compatibilidade de leitura;
- convergência em modelos eventualmente consistentes.

## Qualidade do desenho

### Isolamento

- Gerar namespace e dados únicos por execução.
- Controlar relógio e aleatoriedade quando influenciam o resultado.
- Separar setup, exercício, verificação e cleanup.
- Tornar cleanup idempotente e restrito aos dados criados pelo teste.
- Preservar independência de ordem e paralelismo.

### Determinismo assíncrono

- Aguardar condição observável com polling ou mecanismo nativo e timeout.
- Correlacionar o efeito ao estímulo do cenário.
- Falhar com diagnóstico do último estado observado.
- Usar relógio virtual para debounce, expiração e timers quando adequado.

### Sensibilidade

Provar a capacidade de detectar a falha por uma estratégia segura:

- executar contra versão anterior que contém o defeito;
- introduzir mutação local temporária e restaurá-la;
- dirigir fixture ou double para produzir a quebra;
- verificar falha antes da correção;
- usar controle negativo adequado.

Manter mutações artificiais fora do código final.

### Estabilidade de frontend

- Preferir roles, labels, textos e test IDs estáveis a selectors estruturais.
- Fixar timezone, locale, viewport, animações, fontes e dados em testes visuais.
- Aguardar estados da aplicação e requests relevantes.
- Manter page objects focados em interação e linguagem de domínio.
- Registrar trace, screenshot e vídeo em falha quando o runner suportar.

### Diagnóstico

Nomear testes pelo comportamento e condição. Em falha, distinguir:

- defeito do produto;
- erro no teste;
- configuração ou indisponibilidade do ambiente;
- dado ou precondição inválida;
- threshold pendente;
- instabilidade causada por sincronização ou isolamento.

## Matriz mínima do cenário

| Campo | Conteúdo |
| --- | --- |
| Nome | comportamento legível |
| Base | requisito, contrato, bug ou risco |
| Classificação | propósito, nível, atributo e técnica |
| Precondições | estado, identidade e dependências |
| Estímulo | interação, chamada, evento, concorrência ou falha |
| Oráculo | interface, resposta, estado e efeitos aplicáveis |
| Isolamento | dados, relógio, seed, browser e namespace |
| Cleanup | recursos criados pelo cenário |
| Evidência | resultado e diagnóstico esperados |

## Critérios de conclusão

- Teste executável com comando documentável.
- Base e risco rastreáveis.
- Oráculo sensível à quebra pretendida.
- Fronteira preservada.
- Execução reproduzível e isolada.
- Falhas preservadas e diagnosticadas.
- Limitações e partes preparadas registradas.
