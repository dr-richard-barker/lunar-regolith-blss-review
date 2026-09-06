.PHONY: all pdf clean esm serve view

all: pdf esm

pdf:
	@echo "==> Compiling LaTeX manuscript (Pass 1: pdflatex)..."
	@cd manuscript && pdflatex -interaction=nonstopmode main.tex > /dev/null
	@echo "==> Resolving citations (bibtex)..."
	@cd manuscript && bibtex main > /dev/null
	@echo "==> Compiling LaTeX manuscript (Pass 2: pdflatex)..."
	@cd manuscript && pdflatex -interaction=nonstopmode main.tex > /dev/null
	@echo "==> Compiling LaTeX manuscript (Pass 3: pdflatex)..."
	@cd manuscript && pdflatex -interaction=nonstopmode main.tex > /dev/null
	@cp manuscript/main.pdf manuscript.pdf
	@cp manuscript/main.pdf docs/manuscript.pdf
	@echo "[OK] Successfully compiled manuscript.pdf (and synchronized docs/manuscript.pdf)"

clean:
	@echo "==> Cleaning LaTeX auxiliary build files..."
	@rm -f manuscript/*.aux manuscript/*.bbl manuscript/*.blg manuscript/*.log manuscript/*.out manuscript/*.toc manuscript/*.synctex.gz manuscript/*.fls manuscript/*.fdb_latexmk
	@rm -f manuscript/sections/*.aux
	@echo "[OK] Clean completed."

esm:
	@echo "==> Running NASA BVAD Equivalent System Mass lifecycle model..."
	@python3 analysis/esm_model.py

serve:
	@echo "==> Launching interactive explorer preview at http://localhost:8000..."
	@python3 -m http.server 8000 --directory docs

view: pdf
	@open manuscript.pdf
