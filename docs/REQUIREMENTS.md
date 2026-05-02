# Requisitos de Software — PassGen

## Requisitos Funcionais

| ID   | Descrição |
|------|-----------|
| RF01 | O sistema deve gerar senhas aleatórias com comprimento configurável pelo usuário. |
| RF02 | O sistema deve permitir a inclusão ou exclusão de letras maiúsculas na senha gerada. |
| RF03 | O sistema deve permitir a inclusão ou exclusão de letras minúsculas na senha gerada. |
| RF04 | O sistema deve permitir a inclusão ou exclusão de dígitos numéricos na senha gerada. |
| RF05 | O sistema deve permitir a inclusão ou exclusão de símbolos especiais na senha gerada. |
| RF06 | O sistema deve exibir a senha gerada na saída padrão (terminal). |
| RF07 | O sistema deve permitir a geração de múltiplas senhas em uma única execução. |
| RF08 | O sistema deve avaliar e exibir a força da senha gerada (Fraca, Média, Forte, Muito Forte). |
| RF09 | O sistema deve oferecer sugestões de melhoria quando a senha for considerada fraca. |
| RF10 | O sistema deve suportar modo silencioso (`-q`), exibindo apenas a senha sem informações adicionais. |

## Requisitos Não Funcionais

| ID    | Descrição |
|-------|-----------|
| RNF01 | O sistema deve ser desenvolvido em Python 3.11 ou superior. |
| RNF02 | O sistema deve funcionar via linha de comando (CLI), sem interface gráfica. |
| RNF03 | O sistema deve ser executado nos sistemas operacionais Windows, Linux e macOS. |
| RNF04 | O tempo de geração de uma senha não deve ultrapassar 1 segundo. |
| RNF05 | O código deve seguir as convenções de estilo PEP 8, verificadas pela ferramenta Ruff. |
| RNF06 | O sistema deve possuir cobertura de testes automatizados com pytest. |
| RNF07 | O sistema não deve depender de bibliotecas externas além das listadas em `requirements.txt`. |
| RNF08 | O projeto deve ser versionado com Git e hospedado no GitHub, com releases automáticos via GitHub Actions. |

## Ambiente de Execução

- **Linguagem:** Python 3.11+
- **Gerenciador de dependências:** pip
- **Dependências:** listadas em `requirements.txt`
- **Sistema operacional:** Windows, Linux ou macOS

## Como Instalar e Executar

```bash
git clone https://github.com/TamySouzaa/passgen.git
cd passgen
pip install -r requirements.txt
python main.py --help
```
