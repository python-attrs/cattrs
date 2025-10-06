python := ""
covcleanup := "true"

# Sync the environment, to a particular version if provided. The `python` variable takes precedence over the argument.
sync version="":
    uv sync {{ if python != '' { '-p ' + python } else if version != '' { '-p ' + version } else  { '' } }} --all-groups --all-extras

lint:
	uv run -p python3.13 --group lint ruff check src/ tests bench
	uv run -p python3.13 --group lint black --check src tests docs/conf.py

test *args="-x --ff -n auto tests":
    uv run {{ if python != '' { '-p ' + python } else { '' } }} --all-extras --group test --group lint pytest {{args}}

testall:
    just python=python3.9 test
    just python=python3.10 test
    just python=pypy3.10 test
    just python=python3.11 test
    just python=python3.12 test
    just python=python3.13 test

cov *args="-x --ff -n auto tests":
    uv run {{ if python != '' { '-p ' + python } else { '' } }} --all-extras --group test --group lint coverage run -m pytest {{args}}
    {{ if covcleanup == "true" { "uv run coverage combine" } else { "" } }}
    {{ if covcleanup == "true" { "uv run coverage report" } else { "" } }}
    {{ if covcleanup == "true" { "@rm .coverage*" } else { "" } }}

covall:
    just python=python3.9 covcleanup=false cov
    just python=python3.10 covcleanup=false cov
    just python=pypy3.10 covcleanup=false cov
    just python=python3.11 covcleanup=false cov
    just python=python3.12 covcleanup=false cov
    just python=python3.13 covcleanup=false cov
    uv run coverage combine
    uv run coverage report
    @rm .coverage*

bench-cmp:
	uv run pytest bench --benchmark-compare

bench:
	uv run pytest bench --benchmark-save base

docs output_dir="_build": ## generate Sphinx HTML documentation, including API docs
	make -C docs -e BUILDDIR={{output_dir}} clean
	make -C docs -e BUILDDIR={{output_dir}} doctest
	make -C docs -e BUILDDIR={{output_dir}} html

htmllive: docs ## compile the docs watching for changes
	make -C docs htmllive
