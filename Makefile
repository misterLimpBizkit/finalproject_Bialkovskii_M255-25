install:
	poetry install

project:
	poetry run valutetrade

update-rates:
	poetry run valutetrade update-rates

show-rates:
	poetry run valutetrade show-rates

build:
	poetry build

publish:
	poetry publish --dry-run

package-install:
	python3 -m pip install dist/*.whl

lint:
	poetry run ruff check .