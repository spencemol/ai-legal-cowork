.PHONY: build dev lint lint-fix format test test-watch

build:
	npx tsc

dev:
	npx tsx watch src/server.ts

lint:
	npx eslint src tests --ext .ts

lint-fix:
	npx eslint src tests --ext .ts --fix

format:
	npx prettier --write "src/**/*.ts" "tests/**/*.ts"

test:
	npx vitest run

test-watch:
	npx vitest
