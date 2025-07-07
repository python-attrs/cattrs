test python='':
    uv run {{ if python != '' { '-p ' + python } else { '' } }} --all-extras --group test pytest -x --ff -n auto tests/

cov python='':
    uv run {{ if python != '' { '-p ' + python } else { '' } }} python -c 'import pathlib, site; pathlib.Path(f"{site.getsitepackages()[0]}/cov.pth").write_text("import coverage; coverage.process_startup()")'
    uv run {{ if python != '' { '-p ' + python } else { '' } }} --all-extras --group test coverage run -m pytest -x --ff -n auto tests/