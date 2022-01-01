install-dependencies:
	pip install pip-tools
	pip-sync requirements.txt
	pip install --upgrade pip
	pre-commit install

update-python-packages:
	pip install -UI pip-tools
	pip-compile -U requirements.in
