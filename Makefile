install-dependencies:
	pip install pip-tools
	pip-sync requirements.txt
	pip install --upgrade pip
	pip install pre-commit
	pre-commit install

update-python-packages:
	pip install -UI pip-tools
	pip-compile -U requirements.in
