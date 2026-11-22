.DEFAULT_GOAL := all
pysources = diplomatic tests tools

TAILWIND = cd css && deno run -A tailwindcss -i src/tailwind.css -c tailwind.config.js -o ../diplomatic/static/bundled/main.css
ENGINE = cd engine && deno run -A
ENGINE_ARGS = build.js ../diplomatic/static/bundled/game.js

.PHONY: css
css:
	$(TAILWIND) --minify

.PHONY: css-watch
css-watch:
	$(TAILWIND) --watch

.PHONY: engine
engine:
	$(ENGINE) $(ENGINE_ARGS)

.PHONY: engine-watch
engine-watch:
	$(ENGINE) --watch=../diplomatic/assets $(ENGINE_ARGS)

.PHONY: format
format:
	uv run ruff check --fix $(pysources)
	uv run ruff format $(pysources)

.PHONY: lint
lint:
	uv run ruff check $(pysources)
	uv run ruff format --check $(pysources)

.PHONY: test
test:
	uv run pytest -q tests diplomatico/tests

.PHONY: all
all: format lint test
