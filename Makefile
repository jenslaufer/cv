.PHONY: build pdf check tailor test

build:        ## regenerate index.html + cv.pdf + cv.docx from data.md
	python -m gen build --pdf --docx

check:        ## fail if index.html drifted from data.md
	python -m gen check

test:         ## run the test suite
	python -m pytest -q

# usage: make tailor JOB=examples/job-java-backend.txt SLUG=acme TITLE="..."
tailor:
	python -m gen tailor --job $(JOB) --slug $(SLUG) --title "$(TITLE)" --pdf
