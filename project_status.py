
from pathlib import Path
import ast
import subprocess
import sys

PROJECT_FILES = [
    "lexer.py",
    "parser.py",
    "sql_ast.py",
    "semantic.py",
    "ir.py",
    "optimizer.py",
    "database.py",
    "main.py",
    "test_compiler.py",
]


def check_syntax():
    print("\n1. PYTHON SYNTAX CHECK")
    print("=" * 55)

    passed = 0
    missing = 0
    failed = 0

    for filename in PROJECT_FILES:
        path = Path(filename)

        if not path.is_file():
            print(f"[MISSING] {filename}")
            missing += 1
            continue

        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=filename)
            print(f"[OK]      {filename}")
            passed += 1
        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"[ERROR]   {filename}: {error}")
            failed += 1

    print("-" * 55)
    print(f"Syntax valid: {passed}/{len(PROJECT_FILES)}")
    print(f"Missing files: {missing}")
    print(f"Syntax errors: {failed}")

    return missing == 0 and failed == 0


def run_tests():
    print("\n2. FUNCTIONAL TESTS")
    print("=" * 55)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "test_compiler.py",
        ],
        check=False,
    )

    if result.returncode == 0:
        print("\n[OK] All functional tests passed.")
        return True

    print("\n[ERROR] Functional tests failed.")
    return False


def check_project():
    print("=" * 55)
    print("       SQL QUERY COMPILER - PROJECT STATUS")
    print("=" * 55)

    syntax_ok = check_syntax()
    tests_ok = run_tests()

    print("\n3. OVERALL STATUS")
    print("=" * 55)
    print("Syntax checks:", "PASS" if syntax_ok else "FAIL")
    print("Functional tests:", "PASS" if tests_ok else "FAIL")

    if syntax_ok and tests_ok:
        print("Result: CURRENT CHECKS PASSED")
    else:
        print("Result: ISSUES REQUIRE ATTENTION")

    print("=" * 55)

    return syntax_ok and tests_ok


if __name__ == "__main__":
    sys.exit(0 if check_project() else 1)
