
"""Logical-plan analysis for the SQL Query Compiler and Optimizer.

This module identifies output columns and all columns required to evaluate
WHERE conditions, including nested AND/OR expressions.

Note:
This is a logical analysis pass, not a cost-based physical optimizer.
"""


class QueryOptimizer:
    def __init__(self, ast):
        self.ast = ast
        self.optimizations = []
        self.required_columns = []
        self.output_columns = list(ast.columns)

    def _collect_condition_columns(self, condition):
        """Collect columns referenced by simple or logical conditions."""
        if condition is None:
            return []

        # Simple comparison: Condition(column, operator, value)
        if hasattr(condition, "column"):
            return [condition.column]

        # Logical expression: LogicalCondition(left, operator, right)
        if hasattr(condition, "left") and hasattr(condition, "right"):
            return (
                self._collect_condition_columns(condition.left)
                + self._collect_condition_columns(condition.right)
            )

        return []

    def optimize(self):
        """Return unique internal columns without altering output columns."""
        self.optimizations = []
        self.output_columns = list(self.ast.columns)

        # Preserve duplicates in SELECT output, as SQL permits them.
        required_columns = list(dict.fromkeys(self.output_columns))

        if len(required_columns) < len(self.output_columns):
            self.optimizations.append(
                "Preserved duplicate SELECT columns while removing "
                "duplicates from internal column requirements"
            )

        condition_columns = self._collect_condition_columns(
            self.ast.condition
        )

        for column in condition_columns:
            if column not in required_columns:
                required_columns.append(column)
                self.optimizations.append(
                    f"Retained predicate column '{column}' "
                    "for WHERE evaluation"
                )

        if self.ast.condition is not None:
            self.optimizations.append(
                "Evaluate the WHERE filter before the final projection"
            )

        if not self.optimizations:
            self.optimizations.append(
                "No additional logical optimization rule was applicable"
            )

        self.required_columns = required_columns
        return list(self.required_columns)

    def get_optimization_report(self):
        """Return a copy of the optimization messages."""
        return list(self.optimizations)

    def get_output_columns(self):
        """Return output columns, preserving their original order and duplicates."""
        return list(self.output_columns)
