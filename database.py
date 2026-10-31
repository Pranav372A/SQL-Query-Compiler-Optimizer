
"""SQLite database utilities for the SQL Query Compiler project.

Features:
- Student database setup
- Read-only SELECT execution
- SQLite query-plan inspection
- Repeated query timing
- Index performance comparison
- Reproducible 10,000-row benchmark
- Restoration of index state after benchmarks
"""

import random
import sqlite3
import statistics
import time


DATABASE_NAME = "student.db"
BENCHMARK_RUNS = 10
BENCHMARK_ROWS = 10000


# --------------------------------------------------
# 1. DATABASE CONNECTION AND VALIDATION
# --------------------------------------------------

def validate_read_only_query(sql):
    """Reject empty input and statements outside the SELECT-only scope."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    query = sql.strip()

    if query[:6].upper() != "SELECT":
        raise ValueError("Only SELECT queries are supported.")

    if len(query) > 6 and not (
        query[6].isspace() or query[6] == "("
    ):
        raise ValueError("Invalid SELECT statement.")

    # sqlite3.Cursor.execute() also rejects multiple SQL statements.
    # Remove one optional final semicolon before this basic check.
    without_final_semicolon = query.rstrip()

    if without_final_semicolon.endswith(";"):
        without_final_semicolon = without_final_semicolon[:-1]

    if ";" in without_final_semicolon:
        raise ValueError("Only one SQL statement is supported.")


def _select_authorizer(action, arg1, arg2, database, trigger):
    """Allow reading and SELECT operations, denying database modifications."""
    allowed_actions = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
    }

    # Some Python/SQLite builds expose this action.
    if hasattr(sqlite3, "SQLITE_RECURSIVE"):
        allowed_actions.add(sqlite3.SQLITE_RECURSIVE)

    if action in allowed_actions:
        return sqlite3.SQLITE_OK

    return sqlite3.SQLITE_DENY


def _connect_read_only():
    """Open a connection configured to prohibit database writes."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        connection.execute("PRAGMA query_only = ON")
        connection.set_authorizer(_select_authorizer)
        return connection
    except Exception:
        connection.close()
        raise


def _validate_runs(runs):
    """Ensure the benchmark run count is a positive integer."""
    if (
        not isinstance(runs, int)
        or isinstance(runs, bool)
        or runs < 1
    ):
        raise ValueError("runs must be a positive integer.")


def _index_exists(index_name):
    """Check whether a named index exists."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        row = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'index' AND name = ?
            """,
            (index_name,),
        ).fetchone()

        return row is not None
    finally:
        connection.close()


# --------------------------------------------------
# 2. STUDENT DATABASE SETUP
# --------------------------------------------------

def setup_database():
    """Create the Student table and insert sample rows if it is empty."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Student (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                department TEXT
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM Student")
        row_count = cursor.fetchone()[0]

        if row_count == 0:
            students = [
                (1, "Aarav", 19, "CSE"),
                (2, "Priya", 22, "ECE"),
                (3, "Rahul", 21, "CSE"),
                (4, "Sneha", 18, "IT"),
                (5, "Karan", 24, "CSE"),
            ]

            cursor.executemany("""
                INSERT INTO Student
                    (id, name, age, department)
                VALUES (?, ?, ?, ?)
            """, students)

        connection.commit()
        print("Student database setup completed.")

    finally:
        connection.close()


# --------------------------------------------------
# 3. SQLITE QUERY PLAN
# --------------------------------------------------

def show_sqlite_query_plan(
    sql,
    label="SQLITE QUERY EXECUTION PLAN",
):
    """Display and return SQLite's physical execution plan."""
    validate_read_only_query(sql)
    connection = _connect_read_only()

    try:
        cursor = connection.cursor()
        cursor.execute("EXPLAIN QUERY PLAN " + sql)
        plan = cursor.fetchall()

        print(f"\n{label}")
        print("-" * 60)

        for row in plan:
            print(row)

        return plan

    finally:
        connection.close()


# --------------------------------------------------
# 4. READ-ONLY QUERY EXECUTION
# --------------------------------------------------

def execute_query(sql):
    """Execute a SELECT query, display its results, and return the rows."""
    validate_read_only_query(sql)
    connection = _connect_read_only()

    try:
        cursor = connection.cursor()
        start = time.perf_counter()

        cursor.execute(sql)

        if cursor.description is None:
            raise ValueError(
                "Only queries returning results are supported."
            )

        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()
        elapsed = (time.perf_counter() - start) * 1000

        print("\nDATABASE QUERY RESULTS")
        print("-" * 50)
        print("Columns:", columns)

        for row in rows:
            print(row)

        print("Total rows returned:", len(rows))
        print(f"Execution and fetch time: {elapsed:.4f} ms")

        return rows

    finally:
        connection.close()


# --------------------------------------------------
# 5. REPEATED QUERY MEASUREMENTS
# --------------------------------------------------

def measure_query(sql, runs=BENCHMARK_RUNS):
    """Measure repeated SELECT execution and return timing statistics."""
    validate_read_only_query(sql)
    _validate_runs(runs)

    timings = []
    connection = _connect_read_only()

    try:
        cursor = connection.cursor()

        # Warm-up run; not included in measurements.
        cursor.execute(sql)
        cursor.fetchall()

        for _ in range(runs):
            start = time.perf_counter()

            cursor.execute(sql)
            cursor.fetchall()

            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)

        return {
            "runs": runs,
            "average_ms": statistics.mean(timings),
            "minimum_ms": min(timings),
            "maximum_ms": max(timings),
        }

    finally:
        connection.close()


def display_benchmark(label, result):
    """Print a benchmark result dictionary."""
    print(f"\n{label}")
    print("-" * 50)
    print("Measured runs:", result["runs"])
    print(f"Average time: {result['average_ms']:.4f} ms")
    print(f"Minimum time: {result['minimum_ms']:.4f} ms")
    print(f"Maximum time: {result['maximum_ms']:.4f} ms")


# --------------------------------------------------
# 6. INDEX UTILITIES
# --------------------------------------------------

def _set_student_age_index(enabled):
    """Create or remove the Student age index."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        if enabled:
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_student_age
                ON Student(age)
            """)
        else:
            connection.execute(
                "DROP INDEX IF EXISTS idx_student_age"
            )

        connection.commit()

    finally:
        connection.close()


def _set_benchmark_age_index(enabled):
    """Create or remove the StudentBenchmark age index."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        if enabled:
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmark_age
                ON StudentBenchmark(age)
            """)
        else:
            connection.execute(
                "DROP INDEX IF EXISTS idx_benchmark_age"
            )

        connection.commit()

    finally:
        connection.close()


def _restore_index(index_name, existed_before, index_setter):
    """Restore an index to the state it had before a benchmark."""
    index_setter(existed_before)


def _index_was_used(plan, index_name):
    """Return True when SQLite's displayed plan references the index."""
    return any(index_name in str(row) for row in plan)


def _print_comparison(title, before, after, index_used, row_count=None):
    """Display the timing comparison without claiming guaranteed speedup."""
    difference = before["average_ms"] - after["average_ms"]

    print(f"\n{title}")
    print("=" * 55)

    if row_count is not None:
        print("Dataset rows:", row_count)

    print(f"Average without index: {before['average_ms']:.4f} ms")
    print(f"Average with index:    {after['average_ms']:.4f} ms")
    print("Index selected by SQLite:", "Yes" if index_used else "No")
    print(f"Time difference: {difference:.4f} ms")

    if before["average_ms"] > 0:
        percentage = difference / before["average_ms"] * 100
        print(f"Measured change: {percentage:.2f}%")

    if difference > 0:
        print("Observation: Indexed measurements were faster.")
    elif difference < 0:
        print("Observation: Indexed measurements were slower.")
    else:
        print("Observation: Average measurements were equal.")

    print(
        "Note: Results depend on SQLite's query plan, caching, "
        "system load, and dataset characteristics."
    )


# --------------------------------------------------
# 7. COMPARE INDEX PERFORMANCE ON STUDENT
# --------------------------------------------------

def compare_index_performance(sql, runs=BENCHMARK_RUNS):
    """Compare query plans and timings with and without the Student index."""
    validate_read_only_query(sql)
    _validate_runs(runs)

    existed_before = _index_exists("idx_student_age")

    try:
        _set_student_age_index(False)

        before_plan = show_sqlite_query_plan(
            sql, "QUERY PLAN WITHOUT INDEX"
        )
        before = measure_query(sql, runs)
        display_benchmark("BENCHMARK WITHOUT INDEX", before)

        _set_student_age_index(True)

        after_plan = show_sqlite_query_plan(
            sql, "QUERY PLAN WITH INDEX"
        )
        after = measure_query(sql, runs)
        display_benchmark("BENCHMARK WITH INDEX", after)

        index_used = _index_was_used(
            after_plan, "idx_student_age"
        )

        _print_comparison(
            "INDEX PERFORMANCE COMPARISON",
            before,
            after,
            index_used,
        )

        return before, after

    finally:
        _restore_index(
            "idx_student_age",
            existed_before,
            _set_student_age_index,
        )


# --------------------------------------------------
# 8. CREATE A LARGE BENCHMARK TABLE
# --------------------------------------------------

def setup_benchmark_database():
    """Create a reproducible benchmark table with 10,000 records."""
    connection = sqlite3.connect(DATABASE_NAME)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS StudentBenchmark (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                department TEXT NOT NULL
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM StudentBenchmark")
        existing_count = cursor.fetchone()[0]

        if existing_count != BENCHMARK_ROWS:
            cursor.execute(
                "DROP INDEX IF EXISTS idx_benchmark_age"
            )
            cursor.execute("DELETE FROM StudentBenchmark")

            rng = random.Random(42)
            departments = ["CSE", "ECE", "IT", "MECH", "CIVIL"]

            records = [
                (
                    student_id,
                    f"Student_{student_id}",
                    rng.randint(18, 30),
                    rng.choice(departments),
                )
                for student_id in range(1, BENCHMARK_ROWS + 1)
            ]

            cursor.executemany("""
                INSERT INTO StudentBenchmark
                    (id, name, age, department)
                VALUES (?, ?, ?, ?)
            """, records)

            connection.commit()

        print(
            f"\nBenchmark dataset ready: {BENCHMARK_ROWS} records."
        )

    finally:
        connection.close()


# --------------------------------------------------
# 9. LARGE-DATASET INDEX EXPERIMENT
# --------------------------------------------------

def benchmark_large_dataset(runs=BENCHMARK_RUNS):
    """Benchmark an age filter on the generated large dataset."""
    _validate_runs(runs)
    setup_benchmark_database()

    query = """
        SELECT name
        FROM StudentBenchmark
        WHERE age > 20
    """

    existed_before = _index_exists("idx_benchmark_age")

    try:
        _set_benchmark_age_index(False)

        before_plan = show_sqlite_query_plan(
            query, "LARGE DATASET: PLAN WITHOUT INDEX"
        )
        before = measure_query(query, runs)
        display_benchmark("LARGE DATASET: WITHOUT INDEX", before)

        _set_benchmark_age_index(True)

        connection = sqlite3.connect(DATABASE_NAME)
        try:
            connection.execute("ANALYZE")
            connection.commit()
        finally:
            connection.close()

        after_plan = show_sqlite_query_plan(
            query, "LARGE DATASET: PLAN WITH INDEX"
        )
        after = measure_query(query, runs)
        display_benchmark("LARGE DATASET: WITH INDEX", after)

        index_used = _index_was_used(
            after_plan, "idx_benchmark_age"
        )

        _print_comparison(
            "LARGE DATASET COMPARISON",
            before,
            after,
            index_used,
            BENCHMARK_ROWS,
        )

        return before, after

    finally:
        _restore_index(
            "idx_benchmark_age",
            existed_before,
            _set_benchmark_age_index,
        )


# --------------------------------------------------
# 10. BACKWARD-COMPATIBLE HELPERS
# --------------------------------------------------

def compare_index_plans(sql):
    """Display query plans before and after creating the Student index."""
    validate_read_only_query(sql)
    existed_before = _index_exists("idx_student_age")

    try:
        _set_student_age_index(False)
        before = show_sqlite_query_plan(
            sql, "QUERY PLAN BEFORE INDEXING"
        )

        _set_student_age_index(True)
        after = show_sqlite_query_plan(
            sql, "QUERY PLAN AFTER INDEXING"
        )

        return before, after

    finally:
        _restore_index(
            "idx_student_age",
            existed_before,
            _set_student_age_index,
        )


def benchmark_query(sql, runs=BENCHMARK_RUNS):
    """Backward-compatible wrapper for query benchmarking."""
    result = measure_query(sql, runs)
    display_benchmark("QUERY PERFORMANCE BENCHMARK", result)
    return result


# --------------------------------------------------
# 11. RUN THIS FILE DIRECTLY
# --------------------------------------------------

if __name__ == "__main__":
    setup_database()

    query = """
        SELECT name, age
        FROM Student
        WHERE age > 20
    """

    print("\nORIGINAL STUDENT TABLE")
    execute_query(query)

    print("\nOPTIONAL PERFORMANCE TESTS")
    print("1. Compare index performance on Student")
    print("2. Benchmark a 10,000-row dataset")
    print("3. Skip benchmarks")

    choice = input("Choose 1, 2, or 3: ").strip()

    if choice == "1":
        compare_index_performance(query, runs=BENCHMARK_RUNS)
    elif choice == "2":
        benchmark_large_dataset(runs=BENCHMARK_RUNS)
    elif choice == "3":
        print("Benchmarks skipped.")
    else:
        print("Invalid choice. Benchmarks skipped.")

    print("\nDATABASE OPERATIONS COMPLETED")
