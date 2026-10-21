test:
	python -m unittest discover -s tests -v
	cd grid && go test ./...

.PHONY: test

schema:
	python scripts/check_schema.py

.PHONY: schema
