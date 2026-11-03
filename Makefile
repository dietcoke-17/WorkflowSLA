.PHONY: help install run seed report test docker-up docker-down clean

help:
	@echo "WorkflowSLA - Command Menu"
	@echo "  make install     Install dependencies"
	@echo "  make run         Start FastAPI server (http://localhost:8000)"
	@echo "  make seed        Generate 10,000+ synthetic tickets & transitions"
	@echo "  make report      Generate executive terminal analytics report"
	@echo "  make test        Execute test suite"
	@echo "  make docker-up   Launch PostgreSQL & API in Docker"
	@echo "  make docker-down Stop Docker containers"
	@echo "  make clean       Remove temporary files and databases"

install:
	pip install -r requirements.txt

run:
	python3 main.py

seed:
	python3 main.py --seed 10000

report:
	python3 main.py --report

test:
	python3 run_tests.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	rm -f workflowsla.db *.sqlite3
	find . -type d -name "__pycache__" -exec rm -rf {} +

