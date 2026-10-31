
import re

KEYWORDS = {
    "SELECT",
    "FROM",
    "WHERE",
    "AND",
    "OR",
}

TOKEN_SPECIFICATION = [
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("STRING", r"'(?:''|[^'])*'"),
    ("OPERATOR", r"<=|>=|<>|!=|=|<|>"),
    ("COMMA", r","),
    ("SEMICOLON", r";"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("IDENTIFIER", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("SKIP", r"\s+"),
    ("MISMATCH", r"."),
]

pattern = re.compile(
    "|".join(
        f"(?P<{name}>{regex})"
        for name, regex in TOKEN_SPECIFICATION
    )
)


def tokenize(sql):
    if not isinstance(sql, str):
        raise TypeError("SQL input must be a string.")

    tokens = []

    for match in pattern.finditer(sql):
        token_type = match.lastgroup
        value = match.group()

        if token_type == "SKIP":
            continue

        if token_type == "MISMATCH":
            raise SyntaxError(
                f"Unexpected character {value!r} "
                f"at position {match.start()}."
            )

        if token_type == "IDENTIFIER":
            if value.upper() in KEYWORDS:
                token_type = "KEYWORD"

        tokens.append((token_type, value))

    return tokens


if __name__ == "__main__":
    sql = """
    SELECT name, age
    FROM Student
    WHERE age > 20;
    """

    print("TOKENS:")
    print("-" * 40)

    for token in tokenize(sql):
        print(token)
