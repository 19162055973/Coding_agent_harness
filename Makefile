.PHONY: test install run demo lint

install:
	pip install -e ".[dev]"

test:
	python -m pytest -q

demo:
	python -m forgeloop.demo.mechanisms

run:
	uvicorn forgeloop.api.app:app --host 0.0.0.0 --port 8000

creds-status:
	forgeloop creds status
