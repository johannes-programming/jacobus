.ONESHELL:
.PHONY: all add amend beautiful beautiful-other beautiful-py beautiful-toml black build canonicalize clean commit commit-version dist echo isort jacobus jacobus-other jacobus-py jacobus-toml make_jacobus out py311 py312 py313 py314 py315 pypi pyproject-fmt rebase reset ruff test toml-sorted upload version
SHELL := /bin/zsh

all: beautiful commit-version

add:
	git add -A;

amend: add
	git commit --amend --no-edit;

beautiful: beautiful-other beautiful-py beautiful-toml

beautiful-other: jacobus-other

beautiful-py: jacobus-py ruff

beautiful-toml: canonicalize toml-sorted pyproject-fmt

black: py311
	conda run -n py311 pip install 'black>=24.5,<26' >/dev/null;
	conda run -n py311 black --line-length=79 . ;

build: beautiful py311
	conda run -n py311 pip install 'build>=1.3,<2' >/dev/null;
	conda run -n py311 python -m build;

canonicalize: py311
	conda run -n py311 pip install 'packaging<27,>=26.3';
	conda run -n py311 pip install 'tomli-w<2,>=1.2';
	conda run -n py311 python make/canonicalize.py -- .;

clean:
	rm -fr 'dist/';
	rm -fr 'out/';

commit: add
	git commit --allow-empty $(PARAMS);

commit-version: add py311
	conda run -n py311 pip install 'toml-get>=1.1,<2' >/dev/null;
	git commit --allow-empty "$$(conda run -n py311 python -m toml_get @make/toml_get.txt)";

dist: clean build

echo:
	echo $(PARAMS);

isort: py311
	conda run -n py311 pip install 'isort>=6.0,<7' >/dev/null;
	conda run -n py311 isort . ;

jacobus: jacobus-other jacobus-py jacobus-toml py311

jacobus-other: py311
	conda run -n py311 pip install 'jacobus>=2.4,<3' >/dev/null;
	conda run -n py311 python -m jacobus @make/jacobus_empty.txt;
	cat make/manifest.txt >> MANIFEST.in;
	conda run -n py311 python -m jacobus @make/jacobus_sort.txt;
	conda run -n py311 python -m jacobus @make/jacobus_other_indent.txt;

jacobus-py: py311
	conda run -n py311 pip install 'jacobus>=2.4,<3' >/dev/null;
	conda run -n py311 python -m jacobus @make/jacobus_py.txt;

jacobus-toml: py311
	conda run -n py311 pip install 'jacobus>=2.4,<3' >/dev/null;
	conda run -n py311 python -m jacobus @make/jacobus_toml.txt;

make_jacobus:
	conda run -n base python make/env.py make_jacobus --python=3.11;

out:
	mkdir -p dist/out/;

py311:
	conda run -n base python make/env.py py311 --python=3.11;

py312:
	conda run -n base python make/env.py py312 --python=3.12;

py313:
	conda run -n base python make/env.py py313 --python=3.13;

py314:
	conda run -n base python make/env.py py314 --python=3.14;

py315:
	conda run -n base python make/env.py py315 --python=3.15;

pypi: dist upload

pyproject-fmt: py311
	conda run -n py311 pip install "pyproject-fmt<3,>=2.30";
	conda run -n py311 pyproject-fmt pyproject.toml >/dev/null 2>/dev/null || conda run -n py311 pyproject-fmt --check pyproject.toml;

rebase:
	git rebase --empty=drop --interactive $(PARAMS);

reset:
	git reset HEAD~1;

ruff: py311 out
	conda run -n py311 python -m pip install "ruff>=0.14,<1";
	conda run -n py311 ruff check --fix . ;
	conda run -n py311 ruff format . ;

test: dist make_jacobus out
	conda run -n make_jacobus pip install "style-checker<0.2,>=0.1.8";
	conda run -n make_jacobus python -m style_checker -- "**/*.py" > dist/out/style_checker_out.txt 2> dist/out/style_checker_err.txt || true;
	conda run -n make_jacobus python make/env.py test_jacobus_mypy --python=3.11 --recreate >/dev/null;
	conda run -n test_jacobus_mypy pip install dist/*.tar.gz >/dev/null;
	conda run -n test_jacobus_mypy python run_introspection.py > dist/out/introspection_out.txt 2> dist/out/introspection_err.txt || true;
	conda run -n test_jacobus_mypy pip install "mypy<3,>=2.4" >/dev/null;
	conda run -n test_jacobus_mypy python -m mypy --exclude build --exclude dist --exclude make --strict . > dist/out/mypy_dir_out.txt 2> dist/out/mypy_dir_err.txt || true;
	conda run -n test_jacobus_mypy python -m mypy --strict -p jacobus > dist/out/mypy_pkg_out.txt 2> dist/out/mypy_pkg_err.txt || true;
	conda run -n make_jacobus pip install "mypy<3,>=2.4";
	conda run -n make_jacobus python -m mypy --strict make > dist/out/mypy_make_out.txt 2> dist/out/mypy_make_err.txt || true;
	conda run -n make_jacobus python make/env.py test_jacobus_tests --python=3.11 --recreate >/dev/null;
	conda run -n test_jacobus_tests pip install dist/*.tar.gz >/dev/null;
	conda run -n test_jacobus_tests python run_tests.py > dist/out/tests_out.txt 2> dist/out/tests_err.txt || true;
	zip -r dist/out.zip dist/out;

toml-sorted: py311
	conda run -n py311 pip install 'toml-sorted>=2.2,<3' >/dev/null;
	conda run -n py311 python -m toml_sorted '**/*.toml';
	conda run -n py311 python -m toml_sorted @make/toml_sorted_pyproject.txt;

upload: py311
	conda run -n py311 pip install 'twine>=5.2,<7' >/dev/null;
	conda run -n py311 twine upload 'dist/*';

version: all pypi
