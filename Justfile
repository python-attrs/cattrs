python := ""

lint:
	uv run -p python3.13 --group lint ruff check src/ tests bench
	uv run -p python3.13 --group lint black --check src tests docs/conf.py

test *args="-x --ff -n auto tests":
    uv run {{ if python != '' { '-p ' + python } else { '' } }} --all-extras --group test pytest {{args}}

cov *args="-x --ff -n auto tests":
    @uv run {{ if python != '' { '-p ' + python } else { '' } }} python -c 'import pathlib, site; pathlib.Path(f"{site.getsitepackages()[0]}/cov.pth").write_text("import coverage; coverage.process_startup()")'
    COVERAGE_PROCESS_START={{justfile_directory()}}/pyproject.toml uv run {{ if python != '' { '-p ' + python } else { '' } }} --all-extras --group test coverage run -m pytest {{args}}

bench-cmp:
	uv run pytest bench --benchmark-compare

bench:
	uv run pytest bench --benchmark-save base

docs: ## generate Sphinx HTML documentation, including API docs
	make -C docs clean
	make -C docs doctest
	make -C docs html

htmllive: docs ## compile the docs watching for changes
	make -C docs htmllive
