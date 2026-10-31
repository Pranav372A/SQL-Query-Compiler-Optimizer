class Scan:

    def __init__(self, table):
        self.table = table

    def __str__(self):
        return f"SCAN {self.table}"


class Filter:

    def __init__(self, condition, child):
        self.condition = condition
        self.child = child

    def __str__(self):
        return f"FILTER {self.condition}"


class Project:

    def __init__(self, columns, child):
        self.columns = columns
        self.child = child

    def __str__(self):
        return f"PROJECT {', '.join(self.columns)}"


class IRBuilder:

    def __init__(self, ast):
        self.ast = ast

    def build(self):

        # Start with table scan
        plan = Scan(self.ast.table)

        # Add WHERE condition
        if self.ast.condition is not None:

            plan = Filter(
                self.ast.condition,
                plan
            )

        # Add SELECT projection
        plan = Project(
            self.ast.columns,
            plan
        )

        return plan