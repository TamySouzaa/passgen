#!/usr/bin/env python3
"""
passgen — Gerador de Senhas CLI
Uso: python main.py [opções]
"""

import argparse
import json
import math
import re
import secrets
import string
import sys
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# Constantes
# ══════════════════════════════════════════════════════════════════════════════

AMBIGUOUS_CHARS   = "0O1lI"
DEFAULT_SYMBOLS   = "!@#$%^&*()-_=+[]{}|;:,.<>?"
MAX_LENGTH        = 1024


# ══════════════════════════════════════════════════════════════════════════════
# Critérios
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class PasswordCriteria:
    length:           int            = 16
    use_uppercase:    bool           = True
    use_lowercase:    bool           = True
    use_digits:       bool           = True
    use_symbols:      bool           = True
    exclude_ambiguous: bool          = False
    custom_symbols:   Optional[str]  = None   # sobrescreve DEFAULT_SYMBOLS
    exclude_chars:    str            = ""
    min_uppercase:    int            = 0
    min_lowercase:    int            = 0
    min_digits:       int            = 0
    min_symbols:      int            = 0

    def __post_init__(self) -> None:
        self._validate()

    # ── validação ─────────────────────────────────────────────────────────────

    def _validate(self) -> None:
        errors: list[str] = []

        if not isinstance(self.length, int) or self.length < 1:
            errors.append("'length' deve ser um inteiro positivo.")
        elif self.length > MAX_LENGTH:
            errors.append(f"'length' não pode exceder {MAX_LENGTH}.")

        if not any([self.use_uppercase, self.use_lowercase,
                    self.use_digits, self.use_symbols]):
            errors.append(
                "Pelo menos um conjunto de caracteres deve estar habilitado."
            )

        for attr in ("min_uppercase", "min_lowercase", "min_digits", "min_symbols"):
            val = getattr(self, attr)
            if not isinstance(val, int) or val < 0:
                errors.append(f"'{attr}' deve ser um inteiro não-negativo.")

        total_min = (self.min_uppercase + self.min_lowercase
                     + self.min_digits   + self.min_symbols)
        if total_min > self.length:
            errors.append(
                f"Soma dos mínimos ({total_min}) excede 'length' ({self.length})."
            )

        pairs = [
            ("min_uppercase", "use_uppercase"),
            ("min_lowercase", "use_lowercase"),
            ("min_digits",    "use_digits"),
            ("min_symbols",   "use_symbols"),
        ]
        for min_attr, flag in pairs:
            if getattr(self, min_attr) > 0 and not getattr(self, flag):
                errors.append(
                    f"'{min_attr}' > 0 mas '{flag}' está desabilitado."
                )

        if errors:
            raise ValueError("\n".join(f"  • {e}" for e in errors))

    # ── alfabeto ──────────────────────────────────────────────────────────────

    @property
    def alphabet(self) -> str:
        parts: list[str] = []
        if self.use_uppercase:
            parts.append(string.ascii_uppercase)
        if self.use_lowercase:
            parts.append(string.ascii_lowercase)
        if self.use_digits:
            parts.append(string.digits)
        if self.use_symbols:
            parts.append(
                self.custom_symbols if self.custom_symbols is not None
                else DEFAULT_SYMBOLS
            )

        pool = "".join(parts)

        if self.exclude_ambiguous:
            pool = "".join(c for c in pool if c not in AMBIGUOUS_CHARS)
        if self.exclude_chars:
            pool = "".join(c for c in pool if c not in self.exclude_chars)

        if not pool:
            raise ValueError(
                "Alfabeto vazio após aplicar exclusões. "
                "Revise --exclude e --no-ambiguous."
            )
        return pool


# ══════════════════════════════════════════════════════════════════════════════
# Geração
# ══════════════════════════════════════════════════════════════════════════════

def generate_password(criteria: PasswordCriteria) -> str:
    """Gera senha criptograficamente segura (usa `secrets`)."""
    alphabet = criteria.alphabet

    def _pick_from(charset: str, n: int) -> list[str]:
        available = "".join(c for c in charset if c in alphabet)
        if not available:
            raise ValueError(
                f"Nenhum caractere disponível do conjunto '{charset[:20]}' "
                "após exclusões."
            )
        return [secrets.choice(available) for _ in range(n)]

    # Obrigatórios
    mandatory: list[str] = []
    if criteria.min_uppercase:
        mandatory += _pick_from(string.ascii_uppercase, criteria.min_uppercase)
    if criteria.min_lowercase:
        mandatory += _pick_from(string.ascii_lowercase, criteria.min_lowercase)
    if criteria.min_digits:
        mandatory += _pick_from(string.digits, criteria.min_digits)
    if criteria.min_symbols:
        sym = criteria.custom_symbols if criteria.custom_symbols else DEFAULT_SYMBOLS
        mandatory += _pick_from(sym, criteria.min_symbols)

    # Complemento aleatório
    rest = [secrets.choice(alphabet) for _ in range(criteria.length - len(mandatory))]

    # Fisher-Yates com secrets
    combined = mandatory + rest
    for i in range(len(combined) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        combined[i], combined[j] = combined[j], combined[i]

    return "".join(combined)


# ══════════════════════════════════════════════════════════════════════════════
# Análise de força
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class StrengthReport:
    score:        int          # 0–100
    label:        str
    entropy_bits: float
    suggestions:  list[str]


def analyze_strength(password: str) -> StrengthReport:
    """Analisa força de qualquer senha via entropia + heurísticas."""
    length = len(password)
    pool   = 0
    suggestions: list[str] = []

    has_upper  = bool(re.search(r"[A-Z]", password))
    has_lower  = bool(re.search(r"[a-z]", password))
    has_digit  = bool(re.search(r"\d",    password))
    has_symbol = bool(re.search(r"[^A-Za-z0-9]", password))

    if has_upper:  pool += 26
    else:          suggestions.append("Adicione letras maiúsculas.")
    if has_lower:  pool += 26
    else:          suggestions.append("Adicione letras minúsculas.")
    if has_digit:  pool += 10
    else:          suggestions.append("Adicione dígitos numéricos.")
    if has_symbol: pool += 32
    else:          suggestions.append("Adicione símbolos especiais.")

    if length < 8:
        suggestions.append("Use pelo menos 8 caracteres.")
    elif length < 12:
        suggestions.append("Prefira 12+ caracteres.")
    elif length < 16:
        suggestions.append("16+ caracteres aumentam muito a segurança.")

    entropy = length * math.log2(pool) if pool else 0.0

    # Penalidades
    if re.search(r"(.)\1{2,}", password):
        entropy *= 0.85
        suggestions.append("Evite caracteres repetidos consecutivos.")
    if re.search(r"(012|123|234|345|456|567|678|789|abc|bcd|cde)", password.lower()):
        entropy *= 0.90
        suggestions.append("Evite sequências previsíveis (123, abc…).")

    score = min(100, int(entropy / 1.28))   # 128 bits ≈ 100 pts

    labels = [
        (20, "Muito Fraca 🔴"),
        (40, "Fraca 🟠"),
        (60, "Média 🟡"),
        (80, "Forte 🟢"),
        (101, "Muito Forte 💪"),
    ]
    label = next(l for threshold, l in labels if score < threshold)

    return StrengthReport(
        score=score,
        label=label,
        entropy_bits=round(entropy, 2),
        suggestions=suggestions,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

# Cores ANSI
R = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
GREEN = "\033[92m"
CYAN  = "\033[96m"
YELLOW= "\033[93m"
RED   = "\033[91m"
PURPLE= "\033[95m"


def _c(text: str, *codes: str) -> str:
    return "".join(codes) + text + R


def print_banner() -> None:
    print(_c(r"""
  ██████╗  █████╗ ███████╗███████╗ ██████╗ ███████╗███╗   ██╗
  ██╔══██╗██╔══██╗██╔════╝██╔════╝██╔════╝ ██╔════╝████╗  ██║
  ██████╔╝███████║███████╗███████╗██║  ███╗█████╗  ██╔██╗ ██║
  ██╔═══╝ ██╔══██║╚════██║╚════██║██║   ██║██╔══╝  ██║╚██╗██║
  ██║     ██║  ██║███████║███████║╚██████╔╝███████╗██║ ╚████║
  ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
    """, CYAN, BOLD))
    print(_c("  Gerador de Senhas Seguro — Python CLI  v1.0\n", DIM))


def print_password_block(password: str, index: int | None = None) -> None:
    prefix = f"  #{index}  " if index is not None else "  "
    print(f"\n{prefix}{_c(password, GREEN, BOLD)}\n")


def print_strength_block(password: str) -> None:
    report = analyze_strength(password)
    filled = int(report.score / 5)
    bar    = "█" * filled + "░" * (20 - filled)

    print(f"  {_c('Força :', BOLD)} {report.label}")
    print(f"  [{_c(bar, CYAN)}] {report.score}/100")
    print(f"  {_c('Entropia:', DIM)} {report.entropy_bits} bits\n")

    if report.suggestions:
        print(_c("  Sugestões:", YELLOW))
        for s in report.suggestions:
            print(f"    › {s}")
        print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="passgen",
        description="Gerador de senhas seguras e personalizáveis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py
  python main.py -l 24 --min-digits 2 --min-symbols 2
  python main.py -l 32 --no-symbols --no-ambiguous
  python main.py -l 16 -n 5 --json
  python main.py -l 20 --copy
        """,
    )

    p.add_argument("-l", "--length", type=int, default=16,
                   metavar="N", help="Comprimento da senha (padrão: 16)")

    ch = p.add_argument_group("Conjuntos de caracteres")
    ch.add_argument("--no-uppercase",  action="store_true")
    ch.add_argument("--no-lowercase",  action="store_true")
    ch.add_argument("--no-digits",     action="store_true")
    ch.add_argument("--no-symbols",    action="store_true")
    ch.add_argument("--symbols",       metavar="CHARS",
                    help='Símbolos personalizados (ex: "!@#")')
    ch.add_argument("--no-ambiguous",  action="store_true",
                    help="Excluir 0 O 1 l I")
    ch.add_argument("--exclude",       metavar="CHARS", default="",
                    help="Excluir caracteres específicos")

    mn = p.add_argument_group("Mínimos por categoria")
    mn.add_argument("--min-uppercase", type=int, default=0, metavar="N")
    mn.add_argument("--min-lowercase", type=int, default=0, metavar="N")
    mn.add_argument("--min-digits",    type=int, default=0, metavar="N")
    mn.add_argument("--min-symbols",   type=int, default=0, metavar="N")

    out = p.add_argument_group("Saída")
    out.add_argument("-n", "--count",       type=int, default=1, metavar="N",
                     help="Quantas senhas gerar (padrão: 1)")
    out.add_argument("--json",             action="store_true",
                     help="Saída em JSON")
    out.add_argument("--no-strength",      action="store_true",
                     help="Ocultar análise de força")
    out.add_argument("--copy",             action="store_true",
                     help="Copiar 1ª senha para área de transferência")
    out.add_argument("-q", "--quiet",      action="store_true",
                     help="Apenas as senhas, sem decoração")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args   = parser.parse_args(argv)

    try:
        criteria = PasswordCriteria(
            length           = args.length,
            use_uppercase    = not args.no_uppercase,
            use_lowercase    = not args.no_lowercase,
            use_digits       = not args.no_digits,
            use_symbols      = not args.no_symbols,
            exclude_ambiguous= args.no_ambiguous,
            custom_symbols   = args.symbols,
            exclude_chars    = args.exclude,
            min_uppercase    = args.min_uppercase,
            min_lowercase    = args.min_lowercase,
            min_digits       = args.min_digits,
            min_symbols      = args.min_symbols,
        )
    except ValueError as exc:
        print(_c(f"Erro nos critérios:\n{exc}", RED), file=sys.stderr)
        return 1

    try:
        passwords = [generate_password(criteria) for _ in range(args.count)]
    except ValueError as exc:
        print(_c(f"Erro na geração: {exc}", RED), file=sys.stderr)
        return 1

    # ── saída JSON ────────────────────────────────────────────────────────────
    if args.json:
        payload = []
        for pw in passwords:
            r = analyze_strength(pw)
            payload.append({
                "password":     pw,
                "length":       len(pw),
                "strength": {
                    "label":        r.label,
                    "score":        r.score,
                    "entropy_bits": r.entropy_bits,
                },
            })
        out = payload[0] if args.count == 1 else payload
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    # ── saída humana ──────────────────────────────────────────────────────────
    if not args.quiet:
        print_banner()

    for i, pw in enumerate(passwords):
        if args.quiet:
            print(pw)
        else:
            idx = i + 1 if args.count > 1 else None
            print_password_block(pw, index=idx)
            if not args.no_strength:
                print_strength_block(pw)

    # ── clipboard ─────────────────────────────────────────────────────────────
    if args.copy:
        try:
            import pyperclip
            pyperclip.copy(passwords[0])
            if not args.quiet:
                print(_c("  ✓ Senha copiada para a área de transferência.", GREEN))
        except Exception:
            if not args.quiet:
                print(_c("  ⚠  pyperclip indisponível — instale com: pip install pyperclip", YELLOW))

    return 0


if __name__ == "__main__":
    sys.exit(main())
