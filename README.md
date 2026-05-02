# 🔐 PassGen — Gerador de Senhas Seguras
> MVP de uma ferramenta CLI em Python para geração de senhas aleatórias, seguras e personalizáveis.

---

## Problema e Solução

A criação de senhas seguras é uma necessidade constante para proteger contas e dados, mas muitos usuários têm dificuldade em gerar senhas fortes e únicas.

O **PassGen** resolve isso com uma interface de linha de comando simples e direta, permitindo ao usuário configurar tamanho, tipos de caracteres e garantindo robustez por meio de validações e testes automatizados.

---

## Arquitetura

O projeto segue uma arquitetura modular:

- **API**: Interface REST construída com FastAPI.
- **Core**: Lógica de geração e validação de senhas.
- **Testes**: Cobertura automatizada com pytest.

---

## Requisitos

- Python 3.8+
- Dependências: ver `requirements.txt`

---

## Instalação

```bash
pip install -r requirements.txt
```

---

## Uso Básico

```bash
python main.py --length 12 --uppercase --lowercase --numbers --specials
```

**Parâmetros disponíveis:**

| Parâmetro | Descrição |
|---|---|
| `--length` | Tamanho da senha (máx. 1.000.000) |
| `--uppercase` | Incluir letras maiúsculas |
| `--lowercase` | Incluir letras minúsculas |
| `--numbers` | Incluir números |
| `--specials` | Incluir caracteres especiais |

A senha gerada é copiada automaticamente para a área de transferência.

---

## Exemplos

```bash
# Senha com números e minúsculas, tamanho 20
python main.py --length 20 --no-uppercase --lowercase --numbers --no-specials

# Apenas caracteres especiais, tamanho 8
python main.py --length 8 --no-uppercase --no-lowercase --no-numbers --specials

# Senha longa com todos os tipos
python main.py --length 1000 --uppercase --lowercase --numbers --specials

# Exibir ajuda
python main.py --help
```

---

## Testes

```bash
# Rodar os testes
python -m pytest tests/

# Rodar com relatório de cobertura
python -m pytest --cov=. --cov-report=html:docs/cov_html tests/
```

O relatório em HTML estará disponível em `docs/cov_html/index.html` após a execução.

> **Nota:** recomenda-se adicionar `docs/cov_html/` ao `.gitignore`.

---

## Roadmap

- [x] Geração de senhas configuráveis (MVP)
- [ ] Validação de senhas contra base de vazamentos (Have I Been Pwned)
- [ ] Interface web

---

## Storytelling: Como a IA Acelerou Este Projeto

Este projeto foi desenvolvido com a ajuda de ferramentas de IA como Claude (Anthropic), que permitiram:

✨ Geração rápida da estrutura base do CLI em Python  
✨ Automação de testes unitários com pytest  
✨ Validação robusta de critérios com mensagens descritivas  
✨ Sugestões de boas práticas e refatoração  

## Limitações Identificadas

⚠️ A IA gerou lógica de entropia sem considerar todos os padrões fracos  
⚠️ Faltou validação de entrada em alguns casos extremos  
⚠️ O teste `test_repeated_chars_penalized` precisou de ajuste manual  
⚠️ Segurança: variáveis sensíveis devem ser mantidas no `.env`