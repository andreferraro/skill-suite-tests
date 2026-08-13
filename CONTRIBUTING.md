# Contribuindo

Contribuições devem melhorar a utilidade, a precisão ou a capacidade de validação da skill.

## Antes de começar

- Procure uma issue ou pull request existente sobre o tema.
- Abra uma issue para mudanças de contrato, suporte, evals ou arquitetura.
- Mantenha a alteração pequena e focada.
- Preserve compatibilidade com a invocação `$skill-suite-tests`.

## Desenvolvimento

```bash
git clone https://github.com/andreferraro/skill-suite-tests.git
cd skill-suite-tests
git switch develop
git pull --ff-only
git switch -c feature/nome-curto
```

Valide antes de enviar:

```bash
python -m unittest discover -s tests -v
python scripts/validate_repository.py
python evals/validate_fixtures.py
```

Os comandos acima são determinísticos e não consomem créditos de API.

## Escopo da mudança

Mudanças em `SKILL.md`, `agents/`, `scripts/`, `schemas/` ou `references/` alteram o runtime distribuído. Elas exigem revisão do benchmark e podem exigir nova certificação.

Mudanças somente em documentação, arquivos de comunidade ou CI gratuito dispensam eval pago quando o runtime permanece idêntico. Registre essa condição no pull request.

Mudanças em fixtures, graders, mutantes, pontuação ou harness exigem validação completa de fixtures e justificativa para preservar a comparabilidade histórica.

## Pull request

- Use Conventional Commits.
- Explique o problema e a mudança realizada.
- Liste comandos executados e resultados reais.
- Declare impacto no runtime, nos evals, na segurança e no custo.
- Não inclua credenciais, artefatos temporários, dependências instaladas ou resultados inventados.
- Aguarde todos os checks obrigatórios e resolva as conversas de revisão.

Os evals com agentes são pagos e manuais. Execute somente com autorização explícita, escopo escolhido e teto de chamadas confirmado.
