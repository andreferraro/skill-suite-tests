# Guia de ecossistemas e ferramentas

Usar este guia quando o projeto deixar a escolha aberta. Preservar ferramentas, convenções, fixtures e infraestrutura existentes sempre que elas atenderem ao risco.

## Ordem de decisão

1. Ler manifests, lockfiles, configuração, CI e testes existentes.
2. Identificar runner, browser automation, clientes, fixtures e containers adotados.
3. Verificar suporte ao nível, superfície e oráculo necessários.
4. Adicionar dependência somente diante de lacuna real.
5. Fixar versão, atualizar lockfile e integrar o comando ao fluxo do projeto.

## Frontend web

### JavaScript e TypeScript

- **Unidade e componente:** Vitest, Jest, Node test runner, Testing Library e ferramentas do framework.
- **Browser e E2E:** Playwright ou Cypress conforme adoção do projeto.
- **Acessibilidade:** axe-core, jest-axe, Playwright accessibility integrations ou verificação nativa disponível.
- **Visual:** snapshots do runner de browser com baseline, viewport e tolerância controlados.
- **Property-based:** fast-check quando compatível.
- **Performance do browser:** Lighthouse CI ou Web Vitals coletados no fluxo representativo.

Usar o navegador real quando layout, integração, compatibilidade ou comportamento nativo fizer parte do risco.

### Frameworks

- React, Vue, Angular, Svelte e similares: preferir renderização e interação próximas do usuário.
- SSR e full stack: cobrir hidratação, navegação, cache, erros de servidor e transições cliente/servidor.
- Design systems: testar estados, acessibilidade, tokens e regressão visual de componentes críticos.

## Backend e serviços

- **JavaScript/TypeScript:** Vitest, Jest, Node test runner, Supertest, Testcontainers, Pact, fast-check, k6.
- **Python:** pytest, unittest, Hypothesis, Playwright, Testcontainers, Schemathesis, Locust.
- **Java/Kotlin:** JUnit, Spring Test, REST Assured, Testcontainers, Pact JVM, jqwik, Gatling ou JMeter.
- **.NET:** xUnit, NUnit, MSTest, `WebApplicationFactory`, Testcontainers, PactNet, FsCheck, NBomber.
- **Go:** `testing`, `httptest`, fuzzing nativo, testcontainers-go, k6.
- **Ruby:** RSpec, Capybara, Rack::Test, Pact, Rantly.
- **PHP:** PHPUnit, Pest e clientes de teste do framework adotado.

## Mobile e desktop

- **iOS:** XCTest e XCUITest.
- **Android:** JUnit, Robolectric, Espresso e UI Automator.
- **Multiplataforma:** ferramentas nativas do framework; Appium apenas quando o projeto já utiliza ou quando a cobertura cross-platform justificar o custo.
- **Desktop:** harness do framework, automação de UI compatível e testes de integração do processo.

Cobrir permissões, lifecycle, rede, background, armazenamento local, orientação e dispositivos suportados quando materiais.

## APIs e protocolos

### HTTP e REST

- Usar test host do framework para componente e integração em processo.
- Usar cliente HTTP real para sistema e ponta a ponta.
- Validar OpenAPI com ferramenta compatível com a versão adotada.
- Separar conformidade de schema de expectativas do consumidor.

### GraphQL

- Usar cliente e test utilities do servidor adotado.
- Validar schema, breaking changes, nullability, erros e autorização.
- Medir operações nomeadas e custos representativos em performance.

### gRPC

- Usar stubs gerados a partir do `.proto`.
- Testar unary e streaming separadamente.
- Cobrir deadlines, cancelamento, metadata, status e compatibilidade.

### Eventos, filas e streaming

- Usar broker real containerizado quando ordering, retry ou delivery semantics forem o risco.
- Validar Avro, Protobuf, JSON Schema ou AsyncAPI conforme adoção real.
- Cobrir produtor, consumidor, DLQ, replay, deduplicação, outbox e inbox.

### Webhooks

- Criar receiver controlado para payload, headers, tentativas e timestamps.
- Testar assinatura, replay, timeout, retry, duplicação e idempotência.
- Usar destinos controlados pelo ambiente de teste.

## Dados e infraestrutura

- Preferir containers, bancos efêmeros ou schemas isolados para integração.
- Usar a mesma engine e versão materialmente compatível com produção.
- Aplicar migrations no setup quando essa for a jornada real.
- Testar cache, locks, filas, storage e arquivos com implementação realista quando a garantia estiver no escopo.
- Usar doubles determinísticos para falhas específicas em nível de componente.

## Por objetivo

- **Unidade e componente:** runner principal e harness do framework.
- **Contrato:** schema para conformidade; Pact ou equivalente para expectativas do consumidor.
- **Integração:** Testcontainers, compose ou infraestrutura adotada.
- **Ponta a ponta:** browser ou cliente real, ambiente representativo e correlação observável.
- **Acessibilidade:** verificações automatizadas mais interação por teclado e revisão dirigida do fluxo crítico.
- **Visual:** ferramenta do runner com baseline revisada.
- **Segurança:** testes determinísticos no runner; DAST somente em ambiente autorizado.
- **Performance:** ferramenta capaz de modelar VUs ou arrival rate, thresholds e métricas.
- **Resiliência:** doubles para componente; proxy, fault injector ou infraestrutura controlada para integração e sistema.

## Convenções de implementação

- Colocar testes na suíte correspondente e seguir nomenclatura existente.
- Reutilizar factories, fixtures, page objects, helpers e data builders.
- Parametrizar base URL, browser, dispositivo, identidade, taxa, duração, seed e ambiente.
- Manter defaults de baixa carga e curta duração.
- Criar jobs separados para testes longos, destrutivos ou dependentes de ambiente.
- Gerar artefatos de falha em diretórios ignorados pelo Git quando contiverem dados da execução.
- Manter segredos fora de arquivos versionados e comandos registrados.

## Sinais de ferramenta inadequada

- Reimplementa infraestrutura que o projeto já possui.
- Mascara a fronteira que precisa ser provada.
- Suporta apenas uma asserção superficial diante de risco composto.
- Exige selectors frágeis ou sleeps como mecanismo principal.
- Oculta seed, retries, erros, screenshots ou contraexemplos.
- Depende de SaaS, credencial ou ambiente fora do escopo autorizado.
- Torna execução e diagnóstico mais caros que o risco justifica.
