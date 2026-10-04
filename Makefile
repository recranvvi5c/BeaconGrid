.PHONY: compile python native demo clean

compile: python native

python:
	python -m compileall -q beacongrid

native:
	cd grid && go build ./...

demo:
	python -m beacongrid --help

clean:
	@echo Cleaning generated report artifacts

