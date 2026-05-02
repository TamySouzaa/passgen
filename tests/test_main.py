"""
Suíte de Testes — passgen
Executar: pytest tests/ -v --cov=main --cov-report=term-missing
"""

import json
import re
import string
import sys
from unittest.mock import patch

import pytest

# Importa diretamente do módulo raiz
from main import (
    AMBIGUOUS_CHARS,
    DEFAULT_SYMBOLS,
    MAX_LENGTH,
    PasswordCriteria,
    StrengthReport,
    analyze_strength,
    generate_password,
    main,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def default_criteria():
    return PasswordCriteria()


@pytest.fixture
def digits_only():
    return PasswordCriteria(
        length=12,
        use_uppercase=False,
        use_lowercase=False,
        use_digits=True,
        use_symbols=False,
    )


@pytest.fixture
def all_minimums():
    return PasswordCriteria(
        length=20,
        min_uppercase=2,
        min_lowercase=2,
        min_digits=2,
        min_symbols=2,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PasswordCriteria — construção e defaults
# ══════════════════════════════════════════════════════════════════════════════

class TestPasswordCriteriaDefaults:
    def test_default_length(self, default_criteria):
        assert default_criteria.length == 16

    def test_all_sets_enabled(self, default_criteria):
        assert all([
            default_criteria.use_uppercase,
            default_criteria.use_lowercase,
            default_criteria.use_digits,
            default_criteria.use_symbols,
        ])

    def test_no_exclusions(self, default_criteria):
        assert not default_criteria.exclude_ambiguous
        assert default_criteria.exclude_chars == ""

    def test_all_minimums_zero(self, default_criteria):
        for attr in ("min_uppercase", "min_lowercase", "min_digits", "min_symbols"):
            assert getattr(default_criteria, attr) == 0


# ══════════════════════════════════════════════════════════════════════════════
# PasswordCriteria — validação
# ══════════════════════════════════════════════════════════════════════════════

class TestPasswordCriteriaValidation:

    @pytest.mark.parametrize("bad_length", [-5, 0, -1])
    def test_non_positive_length_raises(self, bad_length):
        with pytest.raises(ValueError, match="'length'"):
            PasswordCriteria(length=bad_length)

    def test_exceeds_max_length_raises(self):
        with pytest.raises(ValueError, match=str(MAX_LENGTH)):
            PasswordCriteria(length=MAX_LENGTH + 1)

    def test_max_length_exact_ok(self):
        c = PasswordCriteria(length=MAX_LENGTH)
        assert c.length == MAX_LENGTH

    def test_no_charset_raises(self):
        with pytest.raises(ValueError, match="Pelo menos um"):
            PasswordCriteria(
                use_uppercase=False,
                use_lowercase=False,
                use_digits=False,
                use_symbols=False,
            )

    @pytest.mark.parametrize("attr", [
        "min_uppercase", "min_lowercase", "min_digits", "min_symbols"
    ])
    def test_negative_minimum_raises(self, attr):
        with pytest.raises(ValueError, match=f"'{attr}'"):
            PasswordCriteria(**{attr: -1})

    def test_minimums_exceed_length_raises(self):
        with pytest.raises(ValueError, match="Soma dos mínimos"):
            PasswordCriteria(length=8, min_uppercase=5, min_lowercase=5)

    @pytest.mark.parametrize("min_attr,flag", [
        ("min_uppercase", "use_uppercase"),
        ("min_lowercase", "use_lowercase"),
        ("min_digits",    "use_digits"),
        ("min_symbols",   "use_symbols"),
    ])
    def test_min_requires_charset_enabled(self, min_attr, flag):
        with pytest.raises(ValueError, match=f"'{min_attr}'"):
            PasswordCriteria(**{min_attr: 1, flag: False})

    def test_multiple_errors_reported_together(self):
        with pytest.raises(ValueError) as exc_info:
            PasswordCriteria(length=-1, use_uppercase=False,
                             use_lowercase=False, use_digits=False,
                             use_symbols=False)
        msg = str(exc_info.value)
        assert "'length'" in msg
        assert "Pelo menos um" in msg


# ══════════════════════════════════════════════════════════════════════════════
# PasswordCriteria — alphabet
# ══════════════════════════════════════════════════════════════════════════════

class TestAlphabet:

    def test_uppercase_only(self):
        c = PasswordCriteria(use_lowercase=False, use_digits=False, use_symbols=False)
        assert all(ch in string.ascii_uppercase for ch in c.alphabet)

    def test_digits_only(self, digits_only):
        assert all(ch in string.digits for ch in digits_only.alphabet)

    def test_custom_symbols(self):
        c = PasswordCriteria(
            use_uppercase=False, use_lowercase=False, use_digits=False,
            custom_symbols="!@#"
        )
        assert set(c.alphabet) == set("!@#")

    def test_exclude_ambiguous_removes_chars(self):
        c = PasswordCriteria(exclude_ambiguous=True)
        for ch in AMBIGUOUS_CHARS:
            assert ch not in c.alphabet

    def test_exclude_custom_chars(self):
        c = PasswordCriteria(exclude_chars="aeiou")
        for ch in "aeiou":
            assert ch not in c.alphabet

    def test_empty_alphabet_after_exclusions_raises(self):
        with pytest.raises(ValueError, match="Alfabeto vazio"):
            PasswordCriteria(
                use_uppercase=False, use_lowercase=False,
                use_symbols=False,
                exclude_chars=string.digits,
            ).alphabet

    def test_no_duplicates_in_alphabet(self, default_criteria):
        alph = default_criteria.alphabet
        assert len(alph) == len(set(alph))


# ══════════════════════════════════════════════════════════════════════════════
# generate_password
# ══════════════════════════════════════════════════════════════════════════════

class TestGeneratePassword:

    def test_correct_length(self, default_criteria):
        pw = generate_password(default_criteria)
        assert len(pw) == default_criteria.length

    @pytest.mark.parametrize("length", [1, 8, 16, 64, 128, MAX_LENGTH])
    def test_various_lengths(self, length):
        c = PasswordCriteria(length=length)
        assert len(generate_password(c)) == length

    def test_only_digits(self, digits_only):
        pw = generate_password(digits_only)
        assert all(ch in string.digits for ch in pw)

    def test_no_ambiguous_chars(self):
        c = PasswordCriteria(exclude_ambiguous=True, length=200)
        pw = generate_password(c)
        assert all(ch not in AMBIGUOUS_CHARS for ch in pw)

    def test_excluded_chars_absent(self):
        c = PasswordCriteria(exclude_chars="aeiou", length=100)
        pw = generate_password(c)
        assert all(ch not in "aeiou" for ch in pw)

    def test_min_uppercase_satisfied(self):
        c = PasswordCriteria(length=20, min_uppercase=5)
        pw = generate_password(c)
        assert sum(1 for ch in pw if ch.isupper()) >= 5

    def test_min_lowercase_satisfied(self):
        c = PasswordCriteria(length=20, min_lowercase=5)
        pw = generate_password(c)
        assert sum(1 for ch in pw if ch.islower()) >= 5

    def test_min_digits_satisfied(self):
        c = PasswordCriteria(length=20, min_digits=5)
        pw = generate_password(c)
        assert sum(1 for ch in pw if ch.isdigit()) >= 5

    def test_min_symbols_satisfied(self):
        sym = DEFAULT_SYMBOLS
        c = PasswordCriteria(length=20, min_symbols=5)
        pw = generate_password(c)
        assert sum(1 for ch in pw if ch in sym) >= 5

    def test_all_minimums_satisfied(self, all_minimums):
        sym = DEFAULT_SYMBOLS
        for _ in range(50):     # repete para detectar falhas de aleatoriedade
            pw = generate_password(all_minimums)
            assert sum(1 for c in pw if c.isupper()) >= 2
            assert sum(1 for c in pw if c.islower()) >= 2
            assert sum(1 for c in pw if c.isdigit()) >= 2
            assert sum(1 for c in pw if c in sym)    >= 2

    def test_uses_secrets_not_random(self, default_criteria):
        """Garante uso de secrets.choice (via aleatoriedade real)."""
        pws = {generate_password(default_criteria) for _ in range(100)}
        assert len(pws) > 90, "Senhas parecem repetitivas — checar fonte de aleatoriedade"

    def test_custom_symbols_only(self):
        c = PasswordCriteria(
            use_uppercase=False, use_lowercase=False, use_digits=False,
            custom_symbols="!@#", length=50,
        )
        pw = generate_password(c)
        assert all(ch in "!@#" for ch in pw)

    def test_empty_alphabet_propagates_error(self):
        c = PasswordCriteria(length=10)
        # Força erro pós-construção removendo todo o alfabeto
        with pytest.raises(ValueError):
            object.__setattr__(c, "exclude_chars", string.printable)
            generate_password(c)


# ══════════════════════════════════════════════════════════════════════════════
# analyze_strength
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeStrength:

    def test_returns_strength_report(self):
        assert isinstance(analyze_strength("Password1!"), StrengthReport)

    def test_very_weak_short_lowercase(self):
        r = analyze_strength("abc")
        assert r.score < 20

    def test_strong_long_mixed(self):
        r = analyze_strength("P@ssW0rd!Xyz2024#Secure")
        assert r.score >= 60

    def test_score_range(self):
        for pw in ["a", "password", "P@ssw0rd!", "X" * 32 + "9!aA"]:
            r = analyze_strength(pw)
            assert 0 <= r.score <= 100

    def test_missing_uppercase_suggests(self):
        r = analyze_strength("password123!")
        assert any("maiúsculas" in s for s in r.suggestions)

    def test_missing_lowercase_suggests(self):
        r = analyze_strength("PASSWORD123!")
        assert any("minúsculas" in s for s in r.suggestions)

    def test_missing_digits_suggests(self):
        r = analyze_strength("Password!")
        assert any("dígitos" in s for s in r.suggestions)

    def test_missing_symbols_suggests(self):
        r = analyze_strength("Password123")
        assert any("símbolos" in s for s in r.suggestions)

    def test_short_password_suggests_length(self):
        r = analyze_strength("Ab1!")
        assert any("caracteres" in s for s in r.suggestions)

    def test_repeated_chars_penalized(self):
        r_plain  = analyze_strength("Abcdefg1!XyZ")
        r_repeat = analyze_strength("Aaabbbccc1!X")
        assert r_plain.entropy_bits >= r_repeat.entropy_bits

    def test_sequential_pattern_penalized(self):
        r_plain = analyze_strength("Xk9!mQzPwL")
        r_seq   = analyze_strength("Abc123defG!")
        assert r_plain.entropy_bits >= r_seq.entropy_bits

    @pytest.mark.parametrize("pw,expected_label_fragment", [
        ("a",               "Muito Fraca"),
        ("password",        "Fraca"),
        ("Password123",     "Média"),
        ("P@ssw0rd!XyZ",    "Forte"),
        ("P@ssW0rd!2024#SecureXyZ", "Muito Forte"),
    ])
    def test_label_tiers(self, pw, expected_label_fragment):
        r = analyze_strength(pw)
        assert expected_label_fragment in r.label

    def test_entropy_positive_for_valid_password(self):
        r = analyze_strength("Hello World 123!")
        assert r.entropy_bits > 0

    def test_no_suggestions_for_strong_password(self):
        pw = generate_password(PasswordCriteria(
            length=20, min_uppercase=2, min_lowercase=2,
            min_digits=2, min_symbols=2,
        ))
        r = analyze_strength(pw)
        assert not any("maiúsculas" in s or "minúsculas" in s
                       or "dígitos" in s or "símbolos" in s
                       for s in r.suggestions)


# ══════════════════════════════════════════════════════════════════════════════
# CLI — main()
# ══════════════════════════════════════════════════════════════════════════════

class TestCLI:

    def test_default_run_exits_zero(self, capsys):
        rc = main([])
        assert rc == 0

    def test_outputs_one_line_quiet(self, capsys):
        main(["-q"])
        out = capsys.readouterr().out.strip()
        assert len(out) > 0

    def test_quiet_output_length_matches(self, capsys):
        main(["-q", "-l", "24"])
        out = capsys.readouterr().out.strip()
        assert len(out) == 24

    def test_count_generates_multiple(self, capsys):
        main(["-q", "-n", "5"])
        lines = [l for l in capsys.readouterr().out.strip().splitlines() if l]
        assert len(lines) == 5

    def test_json_output_structure(self, capsys):
        main(["--json", "-l", "20"])
        data = json.loads(capsys.readouterr().out)
        assert "password" in data
        assert "strength" in data
        assert len(data["password"]) == 20

    def test_json_multiple_is_list(self, capsys):
        main(["--json", "-n", "3"])
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
        assert len(data) == 3

    def test_invalid_length_returns_1(self, capsys):
        rc = main(["-l", "-5"])
        assert rc == 1
        assert capsys.readouterr().err  # deve haver mensagem de erro

    def test_no_symbols_flag(self, capsys):
        main(["-q", "--no-symbols", "-l", "50"])
        pw = capsys.readouterr().out.strip()
        assert all(ch not in DEFAULT_SYMBOLS for ch in pw)

    def test_no_digits_flag(self, capsys):
        main(["-q", "--no-digits", "-l", "50"])
        pw = capsys.readouterr().out.strip()
        assert not any(ch.isdigit() for ch in pw)

    def test_no_ambiguous_flag(self, capsys):
        main(["-q", "--no-ambiguous", "-l", "200"])
        pw = capsys.readouterr().out.strip()
        assert all(ch not in AMBIGUOUS_CHARS for ch in pw)

    def test_all_sets_disabled_returns_error(self, capsys):
        rc = main(["--no-uppercase", "--no-lowercase",
                   "--no-digits", "--no-symbols"])
        assert rc == 1

    def test_custom_symbols(self, capsys):
        main(["-q", "--no-uppercase", "--no-lowercase",
              "--no-digits", "--symbols", "!@#", "-l", "30"])
        pw = capsys.readouterr().out.strip()
        assert all(ch in "!@#" for ch in pw)

    def test_min_flags(self, capsys):
        main(["--json", "-l", "20",
              "--min-uppercase", "3",
              "--min-digits", "3",
              "--min-symbols", "3"])
        data = json.loads(capsys.readouterr().out)
        pw = data["password"]
        assert sum(1 for c in pw if c.isupper()) >= 3
        assert sum(1 for c in pw if c.isdigit()) >= 3
        assert sum(1 for c in pw if c in DEFAULT_SYMBOLS) >= 3

    def test_exclude_flag(self, capsys):
        main(["-q", "--exclude", "aeiou", "-l", "100"])
        pw = capsys.readouterr().out.strip()
        assert all(ch not in "aeiou" for ch in pw)

    def test_copy_pyperclip_unavailable(self, capsys):
        """Não deve travar se pyperclip não estiver disponível."""
        with patch.dict(sys.modules, {"pyperclip": None}):
            rc = main(["--copy"])
        assert rc == 0

    def test_no_strength_flag_suppresses_analysis(self, capsys):
        main(["--no-strength"])
        out = capsys.readouterr().out
        assert "Força" not in out

    def test_strength_shown_by_default(self, capsys):
        main([])
        out = capsys.readouterr().out
        assert "Força" in out

    @pytest.mark.parametrize("length", ["1", "12", "64", "256"])
    def test_valid_lengths_via_cli(self, capsys, length):
        rc = main(["-q", "-l", length])
        out = capsys.readouterr().out.strip()
        assert rc == 0
        assert len(out) == int(length)
