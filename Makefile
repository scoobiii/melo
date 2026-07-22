setup:
\tpython -m venv .venv

lint:
\truff check .

format:
\tblack .

test:
\tpytest

coverage:
\tcoverage run -m pytest
\tcoverage report
