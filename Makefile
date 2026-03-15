.PHONY: lint lint-fix install

install:
	npm install

lint:
	npx markdownlint '**/*.md' --ignore node_modules

lint-fix:
	npx markdownlint '**/*.md' --ignore node_modules --fix
