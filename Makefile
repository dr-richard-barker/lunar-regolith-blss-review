.PHONY: all pdf clean esm serve view figures

all: pdf esm figures

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
	@rm -f manuscript/sections/*.aux manuscript/figures_source/*.aux manuscript/figures_source/*.log
	@echo "[OK] Clean completed."

figures:
	@echo "==> Compiling standalone pgfgantt figures..."
	@cd manuscript/figures_source && pdflatex -interaction=nonstopmode gantt_fig7_trl_roadmap.tex > /dev/null
	@cd manuscript/figures_source && pdflatex -interaction=nonstopmode gantt_fig8_multitrophic_cycle.tex > /dev/null
	@cd manuscript/figures_source && pdflatex -interaction=nonstopmode gantt_fig9_isru_esm_timeline.tex > /dev/null
	@/opt/homebrew/bin/magick -density 300 manuscript/figures_source/gantt_fig7_trl_roadmap.pdf -quality 100 manuscript/figures/fig7_trl_gantt.png
	@/opt/homebrew/bin/magick -density 300 manuscript/figures_source/gantt_fig8_multitrophic_cycle.pdf -quality 100 manuscript/figures/fig8_multitrophic_gantt.png
	@/opt/homebrew/bin/magick -density 300 manuscript/figures_source/gantt_fig9_isru_esm_timeline.pdf -quality 100 manuscript/figures/fig9_isru_esm_gantt.png
	@cp manuscript/figures/fig7_trl_gantt.png docs/figures/fig7_trl_gantt.png
	@cp manuscript/figures/fig8_multitrophic_gantt.png docs/figures/fig8_multitrophic_gantt.png
	@cp manuscript/figures/fig9_isru_esm_gantt.png docs/figures/fig9_isru_esm_gantt.png
	@echo "[OK] Standalone Gantt figures compiled and synchronized."

esm:
	@echo "==> Running NASA BVAD Equivalent System Mass lifecycle model..."
	@python3 analysis/esm_model.py

serve:
	@echo "==> Launching interactive explorer preview at http://localhost:8000..."
	@python3 -m http.server 8000 --directory docs

view: pdf
	@open manuscript.pdf
