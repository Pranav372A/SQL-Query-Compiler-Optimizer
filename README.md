# SQL Query Compiler & Optimizer

A Python-based educational prototype that processes a supported subset of SQL `SELECT` queries through compiler stages and executes valid queries against an SQLite `Student` database.

## Features

- Lexical analysis: converts SQL input into tokens.
- Syntax analysis: parses supported `SELECT` statements.
- Abstract Syntax Tree (AST): represents the parsed query structure.
- Semantic analysis: validates supported table and column references.
- Intermediate representation (IR): builds logical `PROJECT`, `FILTER`, and `SCAN` operations.
- Logical query analysis: identifies output columns and columns needed by `WHERE` predicates.
- SQLite execution: runs supported queries and displays SQLite's query plan.
- Automated tests for valid queries, syntax/semantic errors, and logical conditions.

## Requirements

- Python 3.9 or later
- SQLite (included with standard Python installations)

No third-party Python packages are required by the core project.

## Run

Open a terminal in this folder and execute:

```bash
python main.py
```

Example query:

```sql
SELECT name, age FROM Student WHERE age > 20
```

The current database execution path supports the `Student` table. The parser supports a limited `SELECT` subset; it is not a full SQL implementation.

## Run tests

```bash
python -m unittest -v test_compiler.py
```

Or run the project status check:

```bash
python project_status.py
```

## Current scope and limitations

This is a prototype for learning and demonstrating compiler design concepts. The optimizer performs logical-plan analysis; SQLite chooses the physical execution plan. Features such as general multi-table `JOIN`, `GROUP BY`, `ORDER BY`, aggregate functions, and a graphical interface are outside the current implementation scope.

## Main modules

| File | Purpose |
|---|---|
| `main.py` | Connects the compiler stages and database execution |
| `lexer.py` | Tokenizes SQL input |
| `parser.py` | Parses the supported SQL grammar |
| `sql_ast.py` | AST node definitions |
| `semantic.py` | Schema-based semantic validation |
| `ir.py` | Builds the logical intermediate representation |
| `optimizer.py` | Logical query analysis |
| `database.py` | SQLite setup, execution, and query-plan display |
| `schema.py` | Supported schema definitions |
| `test_compiler.py` | Automated unit tests |
| `project_status.py` | Syntax and test status checks |

## Team

Pranav · Narayan · Surya Dev More

Academic project — VIT Vellore
