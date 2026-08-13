# Bases técnicas

Usar estas fontes como referência conceitual. O requisito, o contrato e a versão adotada pelo projeto continuam autoritativos para a implementação. Verificar a documentação oficial quando uma versão exata afetar a decisão.

## Engenharia de testes

- [ISTQB Certified Tester Foundation Level](https://www.istqb.org/certifications/certified-tester-foundation-level): níveis, tipos, técnicas, confirmação e regressão.

## Frontend e acessibilidade

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/): critérios de acessibilidade para conteúdo web.
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/): padrões de interação, roles, nomes e estados acessíveis.
- [Playwright Best Practices](https://playwright.dev/docs/best-practices): locators, isolamento, assertions e práticas de E2E.
- [Web Vitals](https://web.dev/articles/vitals): métricas de experiência e performance percebida.

Automação de acessibilidade cobre parte dos critérios. Fluxos críticos também podem exigir interação por teclado, tecnologias assistivas e revisão humana dirigida.

## HTTP e descrição de APIs

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html): métodos, safety, idempotência, caching, headers e status.
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html): formato de detalhes de erro quando adotado.
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html): descrição de interfaces HTTP e base para tooling de contrato.

## Protocolos e integrações

- [GraphQL Specification](https://spec.graphql.org/): execução, validação, tipos, nullability e erros.
- [gRPC Core Concepts](https://grpc.io/docs/what-is-grpc/core-concepts/): unary, streaming, metadata, deadlines e cancelamento.
- [AsyncAPI Specification](https://www.asyncapi.com/docs/reference/specification/latest): canais, mensagens, operações e bindings.
- [Pact Contract Testing](https://docs.pact.io/): contratos orientados ao consumidor.

## Segurança

- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/): requisitos verificáveis de segurança de aplicações.
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/): técnicas de teste de segurança web.
- [OWASP API Security Top 10](https://owasp.org/API-Security/): riscos frequentes em APIs.

Usar taxonomias como apoio ao threat modeling e ao risco concreto do sistema.

## Performance

- [Grafana k6 Test Types](https://grafana.com/docs/k6/latest/testing-guides/test-types/): smoke, baseline, carga, estresse, pico, breakpoint e soak.
- [Lighthouse Performance Audits](https://developer.chrome.com/docs/lighthouse/performance/): auditoria de performance no browser.

Os perfis são conceitos reutilizáveis mesmo quando outra ferramenta for adotada.

## Resiliência

- [Principles of Chaos Engineering](https://principlesofchaos.org/): steady state, hipótese, variáveis realistas e redução de blast radius.

Chaos é uma técnica possível. Injeção determinística e de menor risco costuma ser suficiente em muitos cenários.
