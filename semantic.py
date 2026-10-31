from sql_ast import Condition, LogicalCondition
from schema import SCHEMA


class SemanticAnalyzer:

    def __init__(self, ast):
        self.ast = ast
        self.errors = []

    def analyze(self):
        self.errors = []

        # Check whether the table exists.
        if self.ast.table not in SCHEMA:
            self.errors.append(
                f"Table '{self.ast.table}' does not exist."
            )
            return False

        table_schema = SCHEMA[self.ast.table]

        # Check columns selected by SELECT.
        for column in self.ast.columns:
            if column not in table_schema:
                self.errors.append(
                    f"Column '{column}' does not exist "
                    f"in table '{self.ast.table}'."
                )

        # Recursively validate the WHERE condition.
        if self.ast.condition is not None:
            self._validate_condition(
                self.ast.condition,
                table_schema
            )

        return len(self.errors) == 0

    def _validate_condition(self, condition, table_schema):
        if isinstance(condition, Condition):
            if condition.column not in table_schema:
                self.errors.append(
                    f"Column '{condition.column}' does not exist "
                    f"in table '{self.ast.table}'."
                )

        elif isinstance(condition, LogicalCondition):
            self._validate_condition(
                condition.left,
                table_schema
            )
            self._validate_condition(
                condition.right,
                table_schema
            )

        else:
            self.errors.append(
                "Unsupported condition type: "
                f"{type(condition).__name__}."
            )
