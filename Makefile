.PHONY: help install update run clean exit

install:
	pip3 install -r requirements.txt

activate:
	. venv/bin/activate

update:
	pip3 freeze > requirements.txt

run:
	python3 app.py

clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/