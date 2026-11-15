# NASA GeneLab / OSDR Plant AWG Feedback Response & PWM (PSI-187) Assessment

**Repository:** [`dr-richard-barker/lunar-regolith-blss-review`](https://github.com/dr-richard-barker/lunar-regolith-blss-review)  
**Working Group:** NASA GeneLab / Open Science Data Repository (OSDR) Plant Analysis Working Group (AWG) ([Gebre et al., 2025](https://doi.org/10.1093/nar/gkae1116))  
**Date:** 2026-11-13

---

## 1. Point-by-Point Response to AWG Manuscript Comments (`Hydroponics and regolith AWG paper.docx`)

| AWG Comment / Theme | Contributor(s) | Manuscript & Model Integration |
|---|---|---|
| **1. Phased / Modular Framing** — Avoid pitting hydroponics against regolith as mutually exclusive; frame them as complementary along mission duration. | Laura E. Fackrell, Nicholas J. B. Brereton, Richard J. Barker | Updated `01_introduction.tex`, `05_systems_engineering_esm.tex`, `analysis/esm_model.py`, and `docs/index.html` to present a phased hybrid trajectory: closed-loop passive-capillary hydroponics for early sorties (`2 wk`–`6 mo`), transitioning to sintered regolith ceramics beyond the `18–22 mo` ESM breakeven. |
| **2. Terrestrial Closed-Loop Benchmarks** — Benchmark space CEA against proven terrestrial closed-loop greenhouses (e.g., Lufa Farms). | Patrick Grove, Harmeet Multani | Added terrestrial CEA benchmarking in `01_introduction.tex` and `docs/index.html` as the baseline for water recirculation (`>98.5%`) and vertical modular rack density. |
| **3. Eight Mission Horizons** — Evaluate trade-offs across `2 weeks`, `1 month`, `3 months`, `6 months`, `1 year`, `2 years`, `5 years`, and `permanent`. | Laura E. Fackrell, Harrison Coker | Expanded `05_systems_engineering_esm.tex` and `analysis/esm_model.py` (`MISSION_HORIZONS`) to compute ESM across all 8 horizons for both Lunar (`0.165g`) and Martian (`0.38g`) gravities. |
| **4. Dust Containment, Sieving & Tailings Valorization** — Address fugitive regolith dust in habitats, size-fractionation (`45–75 µm`), and uses for coarse tailings & icy-regolith water sourcing. | Harrison Coker, Laura E. Fackrell | Integrated closed-loop dust containment, electrostatic/mechanical sieving, sintered brick/roadway tailings valorization, and polar icy-regolith water coupling in `05_systems_engineering_esm.tex`. |
| **5. LECA & Winogradsky Coupling** — Connect porous sintered ceramics to Lightweight Expanded Clay Aggregate (LECA) hydroponic beds and Winogradsky-style microbial columns. | Nicholas J. B. Brereton, Borja Barbero Barcenilla | Integrated LECA-analog drainage/root-support beds and Winogradsky microbial nutrient-cycling upcycling pathways into `06_closed_loop_ecosystems.tex`. |
| **6. Vadose Zone Physics (Jones et al., 2012)** — Ground microgravity/fractional-gravity pore-scale retention and gas diffusion in van Genuchten & Moldrup WLR theory. | Richard J. Barker | Integrated Jones et al. (2012; `10.2136/vzj2011.0081`), van Genuchten (1980; `10.2136/sssaj1980.03615995004400050002x`), and Moldrup et al. (2000; `10.2136/sssaj2000.6451588x`) into `04_multiphase_fluid_dynamics.tex` and `docs/index.html`. |
| **7. NASA OSDR / GeneLab Attribution & Datasets** — Include standard AWG attribution and cite open omics datasets. | Richard J. Barker, Borja Barbero Barcenilla | Added NASA GeneLab/OSDR AWG boilerplate, `Gebre et al. (2025)` (`10.1093/nar/gkae1116`), and datasets `OSD-267`, `OSD-269`, and `OSD-655` across `01_introduction.tex`, `09_declarations.tex`, `CITATION.cff`, `.zenodo.json`, and `docs/index.html`. |

---

## 2. Technical Assessment of NASA Plant Water Management (`PWM-5` & `PWM-6`, `PSI-187`)

- **Investigation ID:** `PSI-187` (NASA Physical Sciences Informatics Data Repository)
- **DOI:** [`10.60555/bvbr-k768`](https://doi.org/10.60555/bvbr-k768) (Weislogel, McQuillen, & Jenson, 2026; CC0-1.0, ~892 GB, Version 2 released Feb 18, 2026)
- **NTRS Reports:**
  - *Plant Water Management (PWM)* — [`NTRS 20200000783`](https://ntrs.nasa.gov/citations/20200000783)
  - *Plant Water Management in Microgravity* — Hatch et al. (2022), `ICES-2022-28`, [`NTRS 20220003535`](https://ntrs.nasa.gov/citations/20220003535)

### Key Engineering Relevance to Sintered Regolith Bio-Infrastructure
1. **Passive Capillary Fluidics Replace Mechanical Pumps:** `PWM-5` and `PWM-6` demonstrate that tapered wedge channels, controlled surface wetting, and capillary manifolds deliver aerated nutrient solution in microgravity using surface tension alone—directly informing the design of SLM-printed ceramic irrigation emitters and wicking pins (`Section 3` & `Section 4`).
2. **Bubble Management & Root-Zone Aeration:** `PSI-187` characterizes liquid-gas phase separation and bubble entrainment in root-zone analogs, complementing the `30–60 µm` sintered pore-throat envelope (`>25–30%` air-filled porosity) and Moldrup WLR gas diffusivity criteria (`Section 4`).
3. **Phased Mission Bridge:** In short-duration lunar sorties (`<6 months`), Earth-launched PWM-derived passive capillary hydroponic cassettes minimize launch mass; for long-duration (`>18–22 months`) habitats, those exact capillary geometries can be manufactured in situ via solar/laser sintering of lunar regolith.
