
import unittest

from lexer import tokenize
from parser import Parser
from semantic import SemanticAnalyzer
from optimizer import QueryOptimizer


class TestSQLCompiler(unittest.TestCase):

    def compile_query(self, sql):
        tokens = tokenize(sql)
        ast = Parser(tokens).parse()

        analyzer = SemanticAnalyzer(ast)
        is_valid = analyzer.analyze()

        return ast, is_valid, analyzer.errors

    # TEST 1: Valid query with WHERE condition
    def test_valid_query(self):
        sql = "SELECT name, age FROM Student WHERE age > 20"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)
        self.assertEqual(ast.table, "Student")
        self.assertEqual(ast.columns, ["name", "age"])

    # TEST 2: Invalid selected column
    def test_invalid_column(self):
        sql = "SELECT salary FROM Student"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertFalse(is_valid)
        self.assertTrue(
            any("salary" in error for error in errors),
            errors
        )

    # TEST 3: Invalid table
    def test_invalid_table(self):
        sql = "SELECT name FROM Employee"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertFalse(is_valid)
        self.assertTrue(
            any("Employee" in error for error in errors),
            errors
        )

    # TEST 4: Invalid SQL syntax
    def test_invalid_syntax(self):
        sql = "SELECT FROM Student"

        with self.assertRaises((SyntaxError, ValueError)):
            Parser(tokenize(sql)).parse()

    # TEST 5: Optimizer retains WHERE column internally
    def test_optimizer_keeps_filter_column(self):
        sql = "SELECT name FROM Student WHERE age > 20"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)

        optimizer = QueryOptimizer(ast)
        required_columns = optimizer.optimize()

        self.assertEqual(
            optimizer.get_output_columns(),
            ["name"]
        )
        self.assertEqual(
            required_columns,
            ["name", "age"]
        )

    # TEST 6: Preserve duplicate SELECT columns
    def test_optimizer_preserves_duplicate_output_columns(self):
        sql = "SELECT name, name FROM Student"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)

        optimizer = QueryOptimizer(ast)
        optimizer.optimize()

        self.assertEqual(
            optimizer.get_output_columns(),
            ["name", "name"]
        )

    # TEST 7: Valid query without WHERE
    def test_valid_query_without_where(self):
        sql = "SELECT name FROM Student"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)
        self.assertEqual(ast.columns, ["name"])
        self.assertIsNone(ast.condition)

    # TEST 8: Multiple selected columns
    def test_multiple_selected_columns(self):
        sql = "SELECT name, age, department FROM Student"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)
        self.assertEqual(
            ast.columns,
            ["name", "age", "department"]
        )

    # TEST 9: Invalid column in WHERE condition
    def test_invalid_where_column(self):
        sql = "SELECT name FROM Student WHERE salary > 50000"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertFalse(is_valid)
        self.assertTrue(
            any("salary" in error for error in errors),
            errors
        )

    # TEST 10: Do not add a selected WHERE column twice
    def test_filter_column_not_added_twice(self):
        sql = "SELECT age, name FROM Student WHERE age > 20"

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)

        optimizer = QueryOptimizer(ast)
        required_columns = optimizer.optimize()

        self.assertEqual(
            required_columns,
            ["age", "name"]
        )

    # TEST 11: AND condition
    def test_and_condition(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE age > 20 AND department = 'CSE'"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)
        self.assertEqual(ast.condition.operator, "AND")

    # TEST 12: OR condition
    def test_or_condition(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE age > 22 OR department = 'ECE'"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)
        self.assertEqual(ast.condition.operator, "OR")

    # TEST 13: Parenthesized condition
    def test_parenthesized_condition(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE (age > 20 OR name = 'Sneha') "
            "AND department = 'CSE'"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)
        self.assertEqual(ast.condition.operator, "AND")
        self.assertEqual(ast.condition.left.operator, "OR")

    # TEST 14: Optimizer collects logical-condition columns
    def test_optimizer_collects_logical_condition_columns(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE age > 20 AND department = 'CSE'"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)

        optimizer = QueryOptimizer(ast)
        required_columns = optimizer.optimize()

        self.assertEqual(
            required_columns,
            ["name", "age", "department"]
        )

    # TEST 15: Invalid column in a logical condition
    def test_invalid_column_in_logical_condition(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE age > 20 AND salary > 50000"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertFalse(is_valid)
        self.assertTrue(
            any("salary" in error for error in errors),
            errors
        )

    # TEST 16: AND has higher precedence than OR
    def test_and_has_higher_precedence_than_or(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE age > 20 OR department = 'ECE' "
            "AND age < 24"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)

        # Expected: age > 20 OR (department = 'ECE' AND age < 24)
        self.assertEqual(ast.condition.operator, "OR")
        self.assertEqual(ast.condition.left.column, "age")
        self.assertEqual(ast.condition.right.operator, "AND")

    # TEST 17: Nested parentheses
    def test_nested_parenthesized_conditions(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE (age > 20 OR name = 'Sneha') "
            "AND (department = 'CSE' OR age < 19)"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)
        self.assertEqual(ast.condition.operator, "AND")
        self.assertEqual(ast.condition.left.operator, "OR")
        self.assertEqual(ast.condition.right.operator, "OR")

    # TEST 18: Optimizer collects nested condition columns
    def test_optimizer_collects_nested_condition_columns(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE (age > 20 OR name = 'Sneha') "
            "AND department = 'CSE'"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)

        optimizer = QueryOptimizer(ast)
        required_columns = optimizer.optimize()

        self.assertEqual(
            required_columns,
            ["name", "age", "department"]
        )

    # TEST 19: Invalid column inside a nested condition
    def test_invalid_column_in_nested_condition(self):
        sql = (
            "SELECT name FROM Student "
            "WHERE (age > 20 OR salary > 50000) "
            "AND department = 'CSE'"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertFalse(is_valid)
        self.assertTrue(
            any("salary" in error for error in errors),
            errors
        )

    # TEST 20: Avoid duplicate columns in logical conditions
    def test_optimizer_does_not_duplicate_logical_columns(self):
        sql = (
            "SELECT age, name FROM Student "
            "WHERE age > 20 AND department = 'CSE'"
        )

        ast, is_valid, errors = self.compile_query(sql)

        self.assertTrue(is_valid, errors)

        optimizer = QueryOptimizer(ast)
        required_columns = optimizer.optimize()

        self.assertEqual(
            required_columns,
            ["age", "name", "department"]
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
