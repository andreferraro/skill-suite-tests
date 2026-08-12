---
name: skill-suite-tests
description: Analisa riscos e cria, adapta, executa e valida testes automatizados para sistemas, incluindo frontend, backend, APIs, bancos de dados, eventos, integrações e jornadas ponta a ponta. Cobre smoke, confirmação, regressão, aceitação, unidade, componente, contrato, integração, E2E, funcional, acessibilidade, compatibilidade visual e de browser, segurança, performance, resiliência, concorrência, observabilidade, property-based, combinatório e fuzz. Use quando o usuário indicar uma tela, componente, fluxo, serviço, endpoint, job, evento, requisito, bug ou risco que deseja testar, mesmo que desconheça o tipo de teste adequado.
---

# Criar testes de sistemas guiados por risco

Transformar uma descrição curta do alvo e do risco em testes executáveis, coerentes com o projeto e validados na medida permitida pelo ambiente.

## Entrada mínima

Aceitar:

- `alvo`: tela, componente, fluxo, módulo, serviço, endpoint, contrato, job, evento ou comportamento;
- `intenção`: tipo conhecido, falha a evitar, requisito a provar ou risco a investigar.

Preservar o tipo informado pelo usuário. Quando houver apenas um risco, selecionar e declarar a combinação adequada de propósito, nível, atributo de qualidade e técnica.

Perguntar somente quando faltar uma decisão material impossível de obter no projeto, como regra esperada, baseline visual aprovada, identidade de teste, contrato autoritativo ou ambiente autorizado.

## Fluxo obrigatório

1. **Descobrir o sistema.** Localizar implementação, arquitetura, interfaces, contratos, consumidores, testes, fixtures, page objects, manifests, CI, observabilidade e infraestrutura de teste.
2. **Fixar a base de teste.** Registrar requisito, critério de aceite, contrato, bug, risco ou comportamento aceito que sustenta cada cenário. Marcar lacunas como `<definir>`.
3. **Classificar o pedido.** Escolher propósito, nível, atributo e técnica. Ler [tipos-de-teste.md](references/tipos-de-teste.md) quando a seleção exigir comparação entre abordagens.
4. **Delimitar a fronteira.** Declarar navegador, processo, serviço, banco, broker e dependências que serão reais, containerizados, virtualizados ou simulados. Preservar real a fronteira que o teste precisa provar.
5. **Definir oráculos.** Cobrir interface, resposta, estado, eventos, efeitos, ausência de efeitos, tempo, recursos e observabilidade conforme o risco. Ler [oraculos-e-qualidade.md](references/oraculos-e-qualidade.md).
6. **Escolher ferramentas.** Reutilizar runner, browser automation, harness, fixtures e infraestrutura do projeto. Ler [guia-de-ecossistemas.md](references/guia-de-ecossistemas.md) somente quando a escolha estiver aberta.
7. **Projetar o conjunto mínimo.** Para cada cenário, definir risco, precondições, estímulo, dados, oráculo, isolamento, cleanup e evidência esperada.
8. **Implementar.** Seguir convenções locais, reutilizar helpers existentes e manter a mudança pequena. Adicionar dependência apenas diante de uma lacuna real.
9. **Provar sensibilidade.** Confirmar que o teste detecta a quebra declarada por reprodução anterior, controle negativo, fixture dirigida ou mutação local temporária e reversível.
10. **Executar em camadas.** Rodar primeiro o teste criado, depois a suíte relacionada e os checks estáticos. Executar cenários intensivos, destrutivos ou externos somente com autorização adequada.
11. **Relatar evidências.** Informar classificação, base, arquivos, cenários, comandos, resultados, limitações e itens pendentes.

Consultar [bases-tecnicas.md](references/bases-tecnicas.md) quando protocolo, acessibilidade, segurança, performance ou resiliência depender de norma ou referência externa.

## Regras por superfície

### Frontend

- Testar comportamento observável, interação, navegação, estado, acessibilidade e integração com serviços.
- Preferir testes de componente para lógica local e browser real para jornadas, compatibilidade, layout e integração.
- Tratar screenshot, vídeo e trace como evidência complementar. Manter asserções funcionais e de estado.
- Usar regressão visual apenas com baseline aprovada e tolerância explícita.
- Cobrir loading, vazio, erro, retry, permissão, responsividade e teclado quando materiais ao fluxo.

### Backend, APIs e dados

- Cobrir regras, validações, erros, persistência, transações, cache e efeitos externos.
- Validar contratos, semântica de protocolo e expectativas de consumidores quando aplicáveis.
- Verificar commit, rollback, idempotência, concorrência, ordering e convergência de estado.
- Usar banco, broker ou serviço realista quando a garantia dessa dependência fizer parte do risco.

### Eventos e processos assíncronos

- Correlacionar estímulo e efeito por identificadores estáveis.
- Aguardar condição observável com timeout e diagnóstico do último estado.
- Verificar schema, ordering, retry, deduplicação, replay, DLQ e recuperação conforme o contrato.
- Controlar relógio, seed, paralelismo, namespace e cleanup.

## Gates de qualidade

Concluir somente quando os gates aplicáveis passarem:

- **G0 Base:** comportamento esperado sustentado por fonte rastreável.
- **G1 Fronteira:** nível declarado realmente exercitado.
- **G2 Oráculo:** asserções capazes de detectar a falha relevante.
- **G3 Isolamento:** dados, relógio, aleatoriedade, paralelismo e cleanup controlados.
- **G4 Segurança operacional:** ambiente, identidades, carga, duração e blast radius adequados.
- **G5 Reprodutibilidade:** comandos, configuração, seed e dependências explícitos.
- **G6 Validação:** resultados executados registrados; falhas diagnosticadas e preservadas.

## Regras de projeto

- Priorizar risco e força da evidência.
- Usar o nível mais baixo que detecte a falha e adicionar níveis superiores quando a fronteira exigir.
- Separar defeito do produto, falha do teste, problema de ambiente e dado inválido.
- Tratar comportamento observado como baseline provisória quando faltar especificação.
- Evitar snapshots amplos, sleeps fixos, ordem compartilhada, dados globais, selectors frágeis e mocks permissivos.
- Preservar mensagens de erro, screenshots, traces, vídeos, seeds e contraexemplos úteis ao diagnóstico.
- Parametrizar valores desconhecidos como `<definir>` e evitar inventar thresholds, carga ou regra de negócio.

## Segurança operacional

- Manter credenciais em variáveis de ambiente ou cofres de segredo.
- Manter dados sensíveis fora de código, fixtures, logs, screenshots e relatórios.
- Exigir autorização explícita antes de carga, estresse, fuzz externo, exploração automatizada ou injeção de falhas.
- Preferir ambiente controlado. Produção exige aprovação explícita, observabilidade, abort conditions e blast radius limitado.
- Restringir cleanup aos recursos criados pelo teste e torná-lo idempotente.
- Interpretar autorização para implementar como separada da autorização para executar em sistemas externos.

## Saída obrigatória

Entregar código executável integrado ao projeto e responder ao final com:

- alvo e classificação nos quatro eixos aplicáveis;
- base de teste e riscos cobertos;
- arquivos criados ou alterados;
- cenários, fronteiras e oráculos implementados;
- comandos executados e resultados reais;
- evidências geradas;
- dependências, limitações e itens `<definir>`;
- execução preparada e motivo da pendência, quando aplicável.

Limitar conclusões ao que a evidência produzida comprova.
