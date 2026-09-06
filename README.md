# From Dust to Bio-Infrastructure: Sintered Regolith Ceramics for Lunar BLSS

[![License: CC BY 4.0](https://img.shields.io/badge/Manuscript-CC--BY--4.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![License: MIT](https://img.shields.io/badge/Code-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Build Manuscript](https://github.com/dr-richard-barker/lunar-regolith-blss-review/actions/workflows/build-manuscript.yml/badge.svg)](https://github.com/dr-richard-barker/lunar-regolith-blss-review/actions)
[![GitHub Pages](https://img.shields.io/badge/Interactive%20Explorer-Live%20Demo-sky.svg)](https://dr-richard-barker.github.io/lunar-regolith-blss-review)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.placeholder-orange.svg)](https://doi.org/10.5281/zenodo.placeholder)
[![Style](https://img.shields.io/badge/Format-npj%20Microgravity-red.svg)](https://www.nature.com/npjmgrav/)

An open, collaborative, and FAIR (Findable, Accessible, Interoperable, Reusable) research repository containing the complete LaTeX source, verified citation database, publication figures, interactive simulation tools, and systems engineering Equivalent System Mass (ESM) models for the review manuscript:

> **From Dust to Bio-Infrastructure: A Mechanistic Review of Sintered Regolith Ceramics for Lunar Biogenerative Life Support Systems**  
> *Targeted for submission to npj Microgravity (Nature Portfolio)*

---

## 🌟 Interactive Infographic & Web Explorer

Explore the companion interactive tool with real-time parametric trade studies, fluid hydrodynamics simulations, and mission lifecycle economics:

👉 **[Launch Interactive Explorer](https://dr-richard-barker.github.io/lunar-regolith-blss-review)**  
📄 **[Download Compiled Manuscript (PDF)](manuscript.pdf)**

### Key Interactive Features:
1. **Substrate Toxicity & Radical Production**: Compare nanophase metallic iron ($\mathrm{npFe}^0$) and ROS generation kinetics across raw regolith, basalt controls, and sintered ceramics.
2. **Manufacturing Modality Radar**: Multi-attribute trade-off comparison of Microwave Sintering ($2.45/5.8\,\mathrm{GHz}$), Concentrated Solar Sintering (ALM), and Selective Laser Melting (SLM).
3. **Pore Hydrodynamics Simulator in 1/6 g**: Dynamic pore throat slider modeling air-filled porosity, capillary suction, and root-zone hypoxia risk.
4. **Mission ESM Calculator**: Dynamic sliders for habitat crew size (1--12) and mission duration (12--120 months) calculating the operational breakeven point.
5. **Closed-Loop Ecosystem Stepper**: Visualizing photoautotrophic crop growth, saprotrophic mushroom bioconversion, microbial bioweathering (BioRock), and $500^\circ\mathrm{C}$ thermal substrate regeneration.
6. **Technology Readiness Level (TRL) Roadmap**: Strategic progression across Phases 1--3 (TRL 1--9).

---

## 🔬 Scientific Abstract

Establishing an enduring human presence on the Moon requires transitioning from open-loop, resupply-dependent configurations to closed-loop Biogenerative Life Support Systems (BLSS). Terrestrial resupply imposes unsustainable launch burdens, while direct agricultural cultivation in unrefined lunar regolith is severely constrained by submicroscopic nanophase metallic iron ($\mathrm{npFe}^0$), abiotic generation of reactive oxygen species (ROS) via modified Fenton cascades, broken silicate dangling bonds, and sharp mineral shards that induce physical shearing and plant root apical growth arrest. Furthermore, fractional lunar gravity ($1/6\,g$) alters the Bond number, resulting in capillary entrapment, erratic nutrient transport, and pervasive root hypoxia in polydisperse regolith beds.

Here, we review an alternative in-situ bio-infrastructure paradigm: transforming unrefined regolith into engineered porous ceramics via thermal sintering. High-temperature processing ($>1050^\circ\mathrm{C}$) passivates reactive geochemical interfaces by solid-solubilizing $\mathrm{npFe}^0$ into stable augite and olivine matrices, rounds grain boundaries, and enables precise control over pore throat diameters ($30\text{--}60\,\mu\mathrm{m}$). This pore architecture stabilizes matric potential ($-2.5$ to $-5.0\,\mathrm{kPa}$), ensuring continuous capillary nutrient wicking while maintaining air-filled porosity above $25\text{--}30\%$. Equivalent System Mass (ESM) lifecycle modeling reveals that the initial launch-mass investment of a sintering plant reaches parity with direct regolith cultivation within $18\text{--}22$ months, driven by $>98.5\%$ water recovery efficiency and the elimination of chemical buffers. When integrated with fungal mycoponics, microbial bioweathering, and cyclic $500^\circ\mathrm{C}$ pyrolytic substrate regeneration, sintered regolith ceramics provide a closed-loop substrate foundation for sustainable extraterrestrial habitation.

---

## 📂 Repository Architecture

```text
.
├── .github/
│   └── workflows/
│       ├── build-manuscript.yml    # CI/CD: Automated LaTeX to PDF compilation
│       └── deploy-pages.yml        # CI/CD: Automated GitHub Pages deployment
├── analysis/
│   ├── esm_model.py                # NASA BVAD Equivalent System Mass lifecycle model
│   └── output/
│       └── esm_trajectory_baseline.csv # Exported 60-month baseline simulation
├── docs/                           # GitHub Pages deployment root (Interactive Explorer)
│   ├── index.html                  # Standalone interactive dashboard (Tailwind + Chart.js)
│   └── manuscript.pdf              # Pre-compiled high-resolution PDF
├── interactive/
│   └── index.html                  # Local copy of interactive web explorer
├── manuscript/
│   ├── main.tex                    # Master LaTeX document (npj Microgravity style)
│   ├── references.bib              # Verified 59-entry BibTeX bibliography
│   ├── figures/                    # Publication-grade figures (PNG / vector)
│   │   ├── fig1_toxicity_passivation.png
│   │   ├── fig2_sintering_radar.png
│   │   ├── fig3_hydrodynamics_aeration.png
│   │   ├── fig4_esm_lifecycle.png
│   │   ├── fig5_mission_economics.png
│   │   └── fig6_trl_roadmap.png
│   └── sections/                   # Modular LaTeX sections
│       ├── 00_abstract.tex
│       ├── 01_introduction.tex
│       ├── 02_toxicology_and_passivation.tex
│       ├── 03_materials_and_manufacturing.tex
│       ├── 04_multiphase_fluid_dynamics.tex
│       ├── 05_systems_engineering_esm.tex
│       ├── 06_closed_loop_ecosystems.tex
│       ├── 07_roadmap_and_trl.tex
│       ├── 08_conclusion.tex
│       └── 09_declarations.tex
├── .gitignore                      # Comprehensive LaTeX and Python ignore patterns
├── .zenodo.json                    # Machine-readable metadata for Zenodo DOI integration
├── CITATION.cff                    # Citation File Format for GitHub indexing
├── LICENSE                         # Dual CC-BY-4.0 & MIT open-source license
├── Makefile                        # Build automation recipes
├── manuscript.pdf                  # Compiled root manuscript
└── README.md                       # Project overview and FAIR documentation
```

---

## 📊 FAIR Compliance Matrix

| Principle | Implementation in this Repository |
| :--- | :--- |
| **Findable** | Persistent Zenodo DOI integration (`.zenodo.json`), structured metadata in `CITATION.cff`, standard keywords, and public GitHub indexing. |
| **Accessible** | Full open-access text under Creative Commons Attribution 4.0 (CC-BY-4.0), and open-source computational scripts under MIT License. |
| **Interoperable** | Standard modular LaTeX source adhering to Springer Nature / Nature Portfolio conventions, standard BibTeX bibliographic references, and standard CSV data exports. |
| **Reusable** | Automated GitHub Actions CI/CD workflows for PDF compilation, standalone zero-dependency Python analysis script, and explicit documentation of all BVAD modeling equations. |

---

## 🛠️ Building the Manuscript Locally

### Prerequisites
- TeX Live (2022 or newer) or MacTeX with `pdflatex`, `bibtex`, and `latexmk`.
- Python 3.8+ (for running the ESM analysis model).

### Quick Build (Makefile)
```bash
# Compile the complete manuscript to PDF
make pdf

# Clean auxiliary LaTeX files (.aux, .bbl, .log, etc.)
make clean

# Run the NASA BVAD Equivalent System Mass analysis
make esm

# Launch local preview of the interactive explorer
make serve
```

### Manual Compilation
```bash
cd manuscript
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
cp main.pdf ../manuscript.pdf
```

---

## 📈 Running the Systems Engineering ESM Model

The parametric lifecycle model calculates cumulative Equivalent System Mass (ESM) based on NASA Johnson Space Center BVAD specifications (NASA/CR-2004-208941):

```bash
python3 analysis/esm_model.py
```

### Sample Output:
```text
================================================================================
LUNAR BLSS EDAPHIC ARCHITECTURE: EQUIVALENT SYSTEM MASS (ESM) TRADE STUDY
================================================================================
Crew Size  | Horizon    | Raw ESM (kg)   | Sintered ESM (kg)  | Net Savings    | Breakeven
--------------------------------------------------------------------------------
3          | 24 mo      | 2,587          | 1,901              | 686            | 15.4 mo
3          | 60 mo      | 5,955          | 2,399              | 3,556          | 15.4 mo
6          | 24 mo      | 5,175          | 2,852              | 2,322          | 9.4 mo
6          | 60 mo      | 11,910         | 3,848              | 8,062          | 9.4 mo
12         | 24 mo      | 10,349         | 4,754              | 5,595          | 6.5 mo
12         | 60 mo      | 23,821         | 6,746              | 17,074         | 6.5 mo
================================================================================
```

---

## 📜 Citation

If you use this manuscript, repository, or interactive explorer in your research, please cite it as:

```bibtex
@article{lunar_blss_sintered_regolith_2026,
  title     = {From Dust to Bio-Infrastructure: A Mechanistic Review of Sintered Regolith Ceramics for Lunar Biogenerative Life Support Systems},
  author    = {Authors, Collaboration},
  journal   = {npj Microgravity (In Preparation)},
  year      = {2026},
  doi       = {10.5281/zenodo.placeholder},
  url       = {https://dr-richard-barker.github.io/lunar-regolith-blss-review}
}
```

---

## 📄 License

- **Manuscript Text, Figures & Media**: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Software Code & Analysis Scripts**: [MIT License](LICENSE)
