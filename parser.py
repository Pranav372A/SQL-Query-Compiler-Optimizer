
from sql_ast import SelectQuery, Condition, LogicalCondition


class Parser:
    """Recursive-descent parser for the supported SQL SELECT subset."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def consume(self):
        token = self.current()
        if token is not None:
            self.position += 1
        return token

    def expect(self, token_type, value=None):
        token = self.current()

        if token is None:
            raise SyntaxError(
                f"Expected {value or token_type}, "
                "but reached end of query"
            )

        if token[0] != token_type:
            raise SyntaxError(
                f"Expected {value or token_type}, got {token}"
            )

        if value is not None and token[1].upper() != value.upper():
            raise SyntaxError(
                f"Expected {value}, got {token[1]}"
            )

        return self.consume()

    def parse(self):
        self.expect("KEYWORD", "SELECT")

        columns = [self.expect("IDENTIFIER")[1]]

        while self.current() and self.current()[0] == "COMMA":
            self.consume()
            columns.append(self.expect("IDENTIFIER")[1])

        self.expect("KEYWORD", "FROM")
        table = self.expect("IDENTIFIER")[1]

        condition = None

        if self._is_keyword("WHERE"):
            self.consume()
            condition = self.parse_or_condition()

        # Allow one optional trailing semicolon.
        if self.current() and self.current()[0] == "SEMICOLON":
            self.consume()

        if self.current() is not None:
            raise SyntaxError(
                f"Unexpected token: {self.current()}"
            )

        return SelectQuery(columns, table, condition)

    def parse_or_condition(self):
        """OR has lower precedence than AND."""
        left = self.parse_and_condition()

        while self._is_keyword("OR"):
            self.consume()
            right = self.parse_and_condition()
            left = LogicalCondition(left, "OR", right)

        return left

    def parse_and_condition(self):
        left = self.parse_primary_condition()

        while self._is_keyword("AND"):
            self.consume()
            right = self.parse_primary_condition()
            left = LogicalCondition(left, "AND", right)

        return left

    def parse_primary_condition(self):
        token = self.current()

        if token and token[0] == "LPAREN":
            self.consume()
            condition = self.parse_or_condition()
            self.expect("RPAREN")
            return condition

        column = self.expect("IDENTIFIER")[1]
        operator = self.expect("OPERATOR")[1]
        value_token = self.consume()

        if value_token is None or value_token[0] not in (
            "NUMBER",
            "STRING",
            "IDENTIFIER",
        ):
            raise SyntaxError(
                "Expected a number, string, or identifier "
                "as the WHERE condition value"
            )

        return Condition(column, operator, value_token[1])

    def _is_keyword(self, keyword):
        token = self.current()

        return (
            token is not None
            and token[0] == "KEYWORD"
            and token[1].upper() == keyword
        )
