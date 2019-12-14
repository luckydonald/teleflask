upload:
	python setup.py sdist
	twine upload dist/*
	git push --follow-tags
