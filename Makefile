.PHONY: install install-web install-py build run dev-api clean

install: install-py install-web

install-py:
	python3 -m pip install -r requirements.txt

install-web:
	cd web && pnpm install

build:
	cd web && pnpm build

run: build
	python3 -m app

dev-api:
	python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8787 --reload

clean:
	rm -rf app/static/assets app/static/index.html web/node_modules
