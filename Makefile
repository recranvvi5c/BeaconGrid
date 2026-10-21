test:
	python -m unittest discover -s tests -v
	cd grid && go test ./...

.PHONY: test
