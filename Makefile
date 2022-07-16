links:
	rm -rf docs/link/*
	python scripts/generate_links.py --sources *.py --output docs/link

build:
	rm -rf dist/*
	python -m build

publish:
	python -m twine upload dist/* \
		--username alexflint \
		--repository testpypi

installtest:
	python -m pip install \
		--index-url https://test.pypi.org/simple/ \
		--no-deps \
		logicalinduction

deps:
	python -m pip install build twine  # for publishing to PyPI