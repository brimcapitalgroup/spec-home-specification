.PHONY: lint lint-fix install setup render fetch-prices report-needs report-totals report-status serve

install: ## Install Node dependencies
	npm install

setup: ## Install all dependencies (node + python)
	npm install && cd tools && uv sync

lint: ## Run markdownlint
	npx markdownlint '**/*.md' --ignore node_modules --ignore site

lint-fix: ## Fix markdownlint issues
	npx markdownlint '**/*.md' --ignore node_modules --ignore site --fix

render: ## Render all Markdown from JSON
	cd tools && uv run price-tracker render

fetch-prices: ## Validate URLs and update price status
	cd tools && uv run price-tracker fetch

report-needs: ## Show materials still needing selection
	cd tools && uv run price-tracker report needs

report-totals: ## Show cost totals by category
	cd tools && uv run price-tracker report totals

report-status: ## Show status of all material selections
	cd tools && uv run price-tracker report status

serve: ## Render and serve locally
	cd tools && uv run price-tracker render && python -m http.server -d ../site 8080
