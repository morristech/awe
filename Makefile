clean:
	rm -rf build

build-client:
	cd awe/resources/client/awe && npm run build

dev-client:
	cd awe/resources/client/awe && npm start

build-package:
	python setup.py bdist_wheel

update-readme:
	python tools/generate_readme.py

flake8:
	flake8 awe

pytest:
	pytest --forked --junit-xml=test-reports/pytest/report.xml tests

build: clean build-client build-package update-readme

test: flake8 pytest

publish:
	tools/publish.sh

bump-patch-version:
	python tools/bump_version.py patch

bump-minor-version:
	python tools/bump_version.py minor

finish-feature:
	tools/finish-feature.sh

export-examples:
	python tools/export_examples.py

publish-examples:
	tools/publish-examples.sh

build-docs:
	cd docs && sphinx-build source build
