class SelectQuery:

    def __init__(self, columns, table, condition=None):
        self.columns = columns
        self.table = table
        self.condition = condition

    def __repr__(self):
        return (
            "SelectQuery("
            f"columns={self.columns}, "
            f"table={self.table}, "
            f"condition={self.condition}"
            ")"
        )


class Condition:

    def __init__(self, column, operator, value):
        self.column = column
        self.operator = operator
        self.value = value

    def __repr__(self):
        return (
            f"Condition("
            f"{self.column} "
            f"{self.operator} "
            f"{self.value}"
            ")"
        )


class LogicalCondition:

    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator.upper()
        self.right = right

    def __repr__(self):
        return (
            f"LogicalCondition("
            f"{self.left} {self.operator} {self.right}"
            ")"
        )
