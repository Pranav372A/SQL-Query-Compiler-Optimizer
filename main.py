
import sqlite3

from lexer import tokenize
from parser import Parser
from semantic import SemanticAnalyzer
from ir import IRBuilder
from optimizer import QueryOptimizer

from database import (
    setup_database,
    execute_query,
    show_sqlite_query_plan,
    compare_index_performance,
    benchmark_large_dataset,
)


def main():
    print("=" * 65)
    print("                 SQL QUERY COMPILER")
    print("=" * 65)

    print("\nEnter a SQL SELECT query.")
    print("Example: SELECT name FROM Student WHERE age > 20")

    sql = input("\nSQL> ").strip()

    if not sql:
        print("Error: SQL query cannot be empty.")
        return

    print("\nINPUT SQL:")
    print(sql)

    # 1. Lexical analysis
    print("\n1. LEXICAL ANALYSIS")
    print("-" * 65)

    try:
        tokens = tokenize(sql)
        for token in tokens:
            print(token)
    except (SyntaxError, ValueError, TypeError) as error:
        print("Lexical Error:", error)
        return

    # 2. Syntax analysis
    print("\n2. SYNTAX ANALYSIS")
    print("-" * 65)

    try:
        ast = Parser(tokens).parse()
        print("Parsing completed successfully.")
    except (SyntaxError, ValueError, IndexError) as error:
        print("Syntax Error:", error)
        print("Compilation stopped.")
        return

    # 3. Abstract syntax tree
    print("\n3. ABSTRACT SYNTAX TREE")
    print("-" * 65)
    print(ast)

    # 4. Semantic analysis
    print("\n4. SEMANTIC ANALYSIS")
    print("-" * 65)

    analyzer = SemanticAnalyzer(ast)

    try:
        is_valid = analyzer.analyze()
    except Exception as error:
        print("Semantic Analysis Error:", error)
        return

    if not is_valid:
        print("Semantic Analysis: FAILED")
        for error in analyzer.errors:
            print("ERROR:", error)
        print("Compilation stopped due to semantic errors.")
        return

    print("Semantic Analysis: PASSED")
    print("All tables and columns are valid.")

    # 5. Intermediate representation
    print("\n5. INTERMEDIATE REPRESENTATION")
    print("-" * 65)

    try:
        ir_plan = IRBuilder(ast).build()
        print("PROJECT:", ", ".join(ir_plan.columns))

        if ast.condition is not None:
            print("FILTER:", ast.condition)

        print("SCAN:", ast.table)
    except Exception as error:
        print("IR Generation Error:", error)
        return

    # 6. Logical query analysis
    print("\n6. QUERY OPTIMIZATION")
    print("-" * 65)

    try:
        optimizer = QueryOptimizer(ast)
        required_columns = optimizer.optimize()
        output_columns = optimizer.get_output_columns()

        for message in optimizer.get_optimization_report():
            print("Optimization:", message)

        print("Output columns:", ", ".join(output_columns))
        print("Columns required internally:", ", ".join(required_columns))
    except Exception as error:
        print("Optimization Error:", error)
        return

    print("\nFINAL LOGICAL QUERY PLAN")
    print("-" * 65)
    print("PROJECT:", ", ".join(output_columns))

    if ast.condition is not None:
        print("    |")
        print("FILTER:", ast.condition)

    print("    |")
    print("SCAN:", ast.table)

    # 7. Database execution
    print("\n7. DATABASE EXECUTION")
    print("-" * 65)

    if ast.table.lower() != "student":
        print("Database execution currently supports the Student table only.")
        print("Compilation pipeline completed; execution skipped.")
        return

    try:
        setup_database()
        print("SQLite database is ready.")

        print("\nEXECUTING SQL QUERY")
        print("-" * 65)
        execute_query(sql)

        show_sqlite_query_plan(
            sql,
            "SQLITE QUERY EXECUTION PLAN"
        )

    except sqlite3.Error as error:
        print("Database Error:", error)
        return
    except Exception as error:
        print("Execution Error:", error)
        return

    # 8. Optional benchmarks
    print("\nOPTIONAL PERFORMANCE TESTS")
    print("-" * 65)
    print("1. Compare index performance on Student")
    print("2. Benchmark a 10,000-row dataset")
    print("3. Skip benchmarks")

    choice = input("Choose 1, 2, or 3: ").strip()

    try:
        if choice == "1":
            compare_index_performance(sql, runs=10)
        elif choice == "2":
            benchmark_large_dataset(runs=10)
        elif choice == "3":
            print("Benchmarks skipped.")
        else:
            print("Invalid choice. Benchmarks skipped.")
    except sqlite3.Error as error:
        print("Benchmark database error:", error)
        return
    except Exception as error:
        print("Benchmark error:", error)
        return

    print("\n" + "=" * 65)
    print("             COMPILATION COMPLETED")
    print("=" * 65)


if __name__ == "__main__":
    main()
