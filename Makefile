links:
	rm -rf docs/link/*
	python scripts/generate_links.py --sources *.py --output docs/link

publish:
	python setup.py sdist
	twine upload dist/* --username alexflint

deps:
	python -m pip install twine  # for publishing to PyPI