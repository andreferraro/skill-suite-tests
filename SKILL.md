---
name: skill-suite-tests
description: Analisa riscos e cria, adapta, executa e valida testes automatizados em projetos existentes. Use quando o usuário pedir testes para uma tela, fluxo, regra, serviço, API, banco, evento, integração, bug ou atributo de qualidade e esperar código integrado à stack, execução e evidências reais.
---

# Criar testes de sistemas guiados por risco

Transformar o alvo e o risco descritos pelo usuário em testes executáveis, integrados ao projeto e limitados pela evidência produzida.

Esta skill orienta um agente que possui ferramentas de leitura, edição e execução. Ela não é um framework de testes autônomo e não substitui requisitos, ambientes, runners ou infraestrutura do projeto.

## Entrada mínima

Aceitar:

- `alvo`: tela, componente, fluxo, módulo, serviço, endpoint, contrato, job, evento ou comportamento;
- `intenção`: falha a evitar, requisito a provar, risco a investigar ou tipo de teste desejado.

Preservar a intenção do usuário. Corrigir classificações tecnicamente inadequadas, explicar o ajuste e manter o tipo solicitado quando ele ainda produzir evidência útil.

Perguntar somente quando faltar uma decisão material impossível de obter no projeto, como regra esperada, baseline visual aprovada, identidade de teste, contrato autoritativo ou ambiente autorizado.

## Suporte comprovado

O núcleo é agnóstico de stack. A matriz automatizada do repositório comprova atualmente:

- React e TypeScript para frontend;
- FastAPI e Python para APIs e persistência SQLite;
- Node.js e TypeScript para consumidores assíncronos com RabbitMQ e PostgreSQL via Testcontainers.

Tratar outros ecossistemas como **adaptáveis**. Reutilizar a stack encontrada e declarar que ela ainda não pertence à matriz de evals da skill. Nunca converter ausência de benchmark em afirmação de incompatibilidade.

## Fluxo obrigatório

1. **Descobrir o sistema.** Examinar implementação, contratos, testes, fixtures, CI e infraestrutura. Inventariar os comandos canônicos de teste e checks definidos em manifests e CI, separando suítes obrigatórias de suítes opt-in. Se Python estiver disponível, resolver o diretório desta skill a partir do `SKILL.md` carregado e executar `python <skill-root>/scripts/detect_test_context.py --root <projeto> --json` como inventário inicial. Tratar `risk_signals` como candidatos e confirmar cada ocorrência no código.
2. **Fixar a base.** Registrar requisito, critério de aceite, contrato, bug, risco ou comportamento aceito que sustenta cada cenário. Marcar lacunas como `<definir>`.
3. **Classificar o pedido.** Escolher propósito, nível, atributo e técnica. Ler [tipos-de-teste.md](references/tipos-de-teste.md) quando houver dúvida real entre abordagens.
4. **Delimitar a fronteira.** Declarar navegador, processo, serviço, banco, broker e dependências reais, containerizados, virtualizados ou simulados. Preservar real a fronteira que precisa ser provada.
5. **Definir oráculos.** Cobrir interface, resposta, estado, eventos, efeitos, ausência de efeitos, tempo, recursos e observabilidade conforme o risco. Ler [oraculos-e-qualidade.md](references/oraculos-e-qualidade.md).
6. **Escolher ferramentas.** Reutilizar runner, harness, fixtures e infraestrutura existentes. Ler [guia-de-ecossistemas.md](references/guia-de-ecossistemas.md) somente quando a escolha estiver aberta.
7. **Projetar o conjunto mínimo.** Para cada cenário, definir risco, precondições, estímulo, dados, oráculo, isolamento, cleanup e evidência esperada. Rastrear guards, validações, locks, transações, deduplicação, ordering, retry e mecanismos equivalentes encontrados no alvo para um cenário sensível ou justificar por que estão fora do recorte.
8. **Implementar.** Seguir convenções locais e manter a mudança pequena. Adicionar dependência somente diante de lacuna comprovada.
9. **Provar sensibilidade.** Partir de uma execução verde. Para cada guard, validação, lock, transação, deduplicação, retry ou mecanismo protetivo de alto impacto coberto, executar uma mutação local temporária, exigir que o teste falhe, restaurar o arquivo byte a byte e executar verde novamente. "Não altere código de produção" impede mudança no resultado entregue e continua permitindo essa prova transitória restaurada; deixar de mutar somente quando o usuário proibir explicitamente mutações temporárias ou quando elas forem inseguras. Nesses casos, registrar o motivo e executar um controle negativo equivalente. Uma descrição de que o teste falharia não é evidência. Quando ajudar, usar `python <skill-root>/scripts/prove_test_sensitivity.py --root <projeto> --file <arquivo> --search <texto-exato> --replace <mutação> -- <comando-do-teste>`; o helper aceita uma ocorrência, não usa shell e restaura o arquivo mesmo após erro.
10. **Executar em camadas.** Rodar o teste criado, o comando canônico que inclui a suíte alterada, a suíte mais ampla configurada e os checks estáticos aplicáveis. Não substituir um comando obrigatório por outro mais estreito. Tratar falha, timeout, hook pendente e `no tests found` como resultado incompleto a diagnosticar e corrigir. Quando uma suíte vazia fizer parte do comando canônico e sua infraestrutura estiver executável no projeto, criar o menor teste pertinente capaz de exercitar essa fronteira e repetir o comando completo. Registrar pendência somente quando faltar uma dependência material que o projeto não forneça, como ambiente, serviço, identidade ou requisito. Executar cenários intensivos, destrutivos ou externos somente com autorização adequada.
11. **Relatar evidências.** Informar classificação, base, arquivos, cenários, comandos, resultados, limitações e pendências.

Consultar [bases-tecnicas.md](references/bases-tecnicas.md) quando protocolo, acessibilidade, segurança, performance ou resiliência depender de norma externa.

## Regras por superfície

### Frontend

- Testar comportamento observável, interação, navegação, estado, acessibilidade e integração.
- Preferir componente para lógica local e browser real para jornada, layout e comportamento nativo.
- Quando o comando canônico incluir uma suíte de browser executável, manter essa suíte válida. Se ela terminar com `no tests found`, criar e executar ao menos um cenário pertinente ao alvo, mesmo quando a maior parte do risco já estiver coberta no nível de componente. Não declarar o browser desnecessário depois de aceitar o comando como gate do projeto.
- Para ações assíncronas com estado pending/loading, manter a operação pendente por uma Promise controlada e verificar feedback, bloqueio do controle, supressão de duplicidade e recuperação após sucesso e erro.
- Em corridas assíncronas, controlar cada operação separadamente. Resolver a operação mais nova, confirmar seu resultado, resolver a antiga por último, aguardar sua liquidação e afirmar que o resultado novo permaneceu. Em React, liquidar a Promise antiga dentro de `await act(async () => ...)` antes da asserção final. Uma asserção ou um `waitFor` satisfeito imediatamente após chamar o resolver pode passar antes da atualização defeituosa e não comprova proteção contra resposta obsoleta.
- Manter asserções funcionais junto de screenshots, vídeos ou traces.
- Exigir baseline aprovada e tolerância explícita para regressão visual.

### Backend, APIs e dados

- Cobrir regras, validações, erros, persistência, transações, cache e efeitos externos.
- Validar contratos, protocolo e expectativas de consumidores quando aplicáveis.
- Verificar commit, rollback, idempotência, concorrência, ordering e convergência conforme o risco.
- Testar cada validação na camada que a implementa. Para um guard no serviço ou domínio, incluir uma chamada direta nessa camada mesmo quando UI, schema ou controller também rejeitarem a entrada. Provar a sensibilidade enfraquecendo temporariamente o guard interno; uma resposta 4xx da camada externa não basta.
- Tratar lock, transação serializada, constraint única e chave de idempotência como sinais de concorrência. Criar contenção real com barreira ou vários workers, sem depender de duas chamadas oportunistas, e verificar identidade, quantidade de criações e estado final. Em SQLite local, usar ao menos oito operações concorrentes quando o projeto não definir outro limite. Provar que o teste falha ao enfraquecer temporariamente o mecanismo de serialização.

### Eventos e processos assíncronos

- Correlacionar estímulo e efeito por identificadores estáveis.
- Aguardar condição observável com timeout e diagnóstico do último estado.
- Verificar schema, ordering, retry, deduplicação, replay, DLQ e recuperação conforme o contrato.
- Preservar o gate opt-in das suítes com containers ou serviços. O comando unitário não deve iniciar infraestrutura por efeito colateral.
- Em falhas dirigidas de integração, substituir somente a operação que deve falhar e manter reais as fronteiras que precisam ser observadas. Não derrubar tabelas, filas ou serviços quando isso puder quebrar uma leitura anterior ao ponto de injeção.
- Encerrar consumers, clientes, canais, conexões e containers sequencialmente, em ordem de dependência, com cleanup idempotente e tempo limitado. Não fechar recursos dependentes em paralelo. Confirmar que o processo de teste termina sem hooks pendentes.

## Gates de qualidade

Concluir somente quando os gates aplicáveis passarem:

- **G0 Base:** comportamento esperado sustentado por fonte rastreável.
- **G1 Fronteira:** nível declarado realmente exercitado.
- **G2 Oráculo:** asserções capazes de detectar a falha relevante, com prova de sensibilidade executada quando a mutação local for segura.
- **G3 Isolamento:** dados, relógio, aleatoriedade, paralelismo e cleanup controlados.
- **G4 Segurança:** ambiente, identidade, carga, duração e blast radius adequados.
- **G5 Reprodutibilidade:** comandos, configuração, seed e dependências explícitos.
- **G6 Validação:** comandos canônicos executados, processo encerrado e zero falhas, timeouts ou suítes vazias sem diagnóstico.

## Regras de projeto

- Usar o nível mais baixo que detecte a falha e adicionar níveis superiores quando a fronteira exigir.
- Separar defeito do produto, falha do teste, problema de ambiente e dado inválido.
- Evitar snapshots amplos, sleeps fixos, ordem compartilhada, dados globais, selectors frágeis e mocks permissivos.
- Preservar mensagens de erro, traces, seeds e contraexemplos úteis ao diagnóstico.
- Nomear cada propriedade comprovada com precisão no relatório. Trocar rótulos amplos por mecanismos observáveis, como nome acessível, operação por teclado, anúncio de erro, rollback, deduplicação ou correlação, quando realmente testados.
- Usar `<definir>` em vez de inventar thresholds, carga ou regra de negócio.

## Segurança operacional

- Manter credenciais em variáveis de ambiente ou cofres e dados sensíveis fora de código, fixtures e logs.
- Exigir autorização explícita antes de carga, estresse, fuzz externo, exploração automatizada ou injeção de falhas.
- Restringir cleanup aos recursos criados pelo teste e torná-lo idempotente.
- Interpretar autorização para implementar como separada da autorização para executar em sistemas externos.

## Saída obrigatória

Entregar código executável integrado ao projeto e responder com:

- alvo, suporte comprovado ou adaptável e classificação nos quatro eixos;
- base de teste e riscos cobertos;
- arquivos, cenários, fronteiras e oráculos;
- comandos executados e resultados reais;
- evidências, limitações e itens `<definir>`;
- execução preparada e motivo da pendência, quando aplicável.

Quando o usuário ou a automação pedir saída estruturada, gerar `test-evidence.json` compatível com [test-evidence.v1.json](schemas/test-evidence.v1.json) e validar com `python <skill-root>/scripts/validate_test_evidence.py <projeto>/test-evidence.json`.

Limitar conclusões ao que a evidência produzida comprova.
