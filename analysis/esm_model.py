#!/usr/bin/env python3
"""
ESM & Root-Zone Physics Model: Lifecycle Evaluation for Lunar & Martian BLSS Edaphic Architectures

This module implements the NASA Advanced Life Support (ALS) Equivalent System Mass (ESM)
framework formalized in the Baseline Values and Assumptions Document (BVAD; Hanford, 2004;
Ewert et al., 2022, NASA/TP-20220002905) to quantitatively compare four extraterrestrial
crop-production edaphic paradigms:
  1. Conventional Hydroponics (Earth-imported rockwool/expanded clay & polymeric channels)
  2. Direct Regolith Cultivation (Unprocessed/treated lunar soil with nutrient solution)
  3. Hydroponic-Regolith Hybrid (Reusable channels + external regolith bioweathering recovery)
  4. Sintered Regolith Ceramic Bio-Infrastructure (ISRU engineered porous ceramics)

It also implements reduced-gravity root-zone hydraulic and gas-diffusion scaling from
Jones et al. (2012, Vadose Zone J., doi:10.2136/vzj2011.0081):
  - Miller & Miller (1955) gravity scaling of van Genuchten alpha
  - Arya & Paris (1981) / Jones & Or (1998) particle-to-pore radius scaling
  - Moldrup et al. (2000) Water-induced Linear Reduction (WLR) gas diffusivity (Dp/Do >= 0.02)

Mathematical Formulation:
  ESM = M + (V * C_V) + (P * C_P) + (C * C_C) + (T * C_T)
Normalized to edible output:
  ESM_edible = ESM / cumulative_edible_biomass_kg
"""

import os
import math
import sys
import json
import csv
import os
from typing import Dict, List


# NASA BVAD Lunar & Martian Surface Equivalency Factors (Hanford, 2004; Ewert et al., 2022; Ho et al., 2022)
BVAD_FACTORS = {
    "C_V": 9.16,            # kg/m^3 (pressurized volume infrastructure mass)
    "C_P_nuclear": 54.0,    # kg/kWe (surface fission power system)
    "C_P_solar": 237.0,     # kg/kWe (PV + RFC energy storage for 14-day lunar night)
    "C_C": 85.0,            # kg/kWth (composite thermal radiator system)
    "C_T": 1.25             # kg/crew-hour (crew time mass equivalent)
}

# Eight mission horizons requested by NASA GeneLab/OSDR Plant AWG (months)
MISSION_HORIZONS: List[Tuple[str, float]] = [
    ("2 weeks", 0.5),
    ("1 month", 1.0),
    ("3 months", 3.0),
    ("6 months", 6.0),
    ("1 year", 12.0),
    ("2 years", 24.0),
    ("5 years", 60.0),
    ("Permanent (10 yr)", 120.0),
]


def calculate_esm(
    crew_size: int = 6,
    mission_months: int = 60,
    power_system: str = "nuclear",
    gravity_regime: str = "lunar"
) -> Dict[str, any]:
    """
    Calculates cumulative ESM and monthly trajectories for both paradigms.
    Supports lunar (0.165 g) and Martian (0.38 g) gravity sensitivity.
    """
    scale = crew_size / 6.0
    # Mars (0.38g) vs Moon (0.16g): Mars imposes higher transit gear factor (~1.15x imported mass)
    # but slightly better passive drainage (~0.92x water entrapment in raw regolith).
    transit_mult = 1.15 if destination == "mars" else 1.0
    entrapment_mult = 0.92 if destination == "mars" else 1.0

    if arch == "conventional_hydroponics":
        return {
            "m_initial": 780.0 * scale * transit_mult,
            "v": 5.0 * scale,
            "p": 2.8 * scale,   # continuous pumping, pH/DO sensors, aeration
            "c": 2.3 * scale,
            "t_monthly": 14.0 * scale,
            "consumables_monthly": (28.0 + 13.8 + 18.0) * scale * transit_mult,  # 97.5% H2O, imported salts, rockwool media
            "yield_factor": 1.00,
        }
    elif arch == "direct_regolith":
        return {
            "m_initial": 420.0 * scale * transit_mult,
            "v": 12.5 * scale,
            "p": 1.2 * scale,
            "c": 1.0 * scale,
            "t_monthly": 40.0 * scale,
            "consumables_monthly": ((120.0 * entrapment_mult) + 12.1 + 5.0) * scale,  # 80% H2O, acid/EDTA, dust filters
            "yield_factor": 0.72,  # ROS/hypoxia yield penalty
        }
    elif arch == "hybrid_regolith":
        return {
            "m_initial": 1150.0 * scale * transit_mult,  # reusable troughs + external bioleaching reactor
            "v": 5.8 * scale,
            "p": 2.6 * scale,
            "c": 2.2 * scale,
            "t_monthly": 12.0 * scale,
            "consumables_monthly": (24.0 + 4.5 + 8.0) * scale * transit_mult,  # 97.8% H2O, partial bioleached nutrients
            "yield_factor": 0.96,
        }
    elif arch == "sintered_ceramic":
        return {
            "m_initial": (1850.0 + (150.0 * (crew_size - 6))) * transit_mult,
            "v": 4.2 * scale,
            "p": 2.4 * scale,
            "c": 2.0 * scale,
            "t_monthly": 6.0 * scale,
            "consumables_monthly": (18.0 + 0.67 + 1.5) * scale,  # >98.5% H2O, <8 kg/yr buffer, minimal spares
            "yield_factor": 1.02,  # optimal aeration + no media replacement downtime
        }
    else:
        raise ValueError(f"Unknown architecture: {arch}")


def calculate_esm_architecture(
    arch: str,
    crew_size: int = 6,
    mission_months: int = 60,
    power_system: str = "nuclear",
    destination: str = "moon",
) -> Dict[str, any]:
    """Calculates cumulative ESM and edible-yield-normalized ESM for one architecture."""
    c_p = BVAD_FACTORS["C_P_nuclear"] if power_system == "nuclear" else BVAD_FACTORS["C_P_solar"]
    c_v = BVAD_FACTORS["C_V"]
    c_c = BVAD_FACTORS["C_C"]
    c_t = BVAD_FACTORS["C_T"]
    # Mars (0.38 g) reduces capillary waterlogging slightly vs 0.165 g (~12% lower raw water trapping)
    # but increases solar dust attenuation and perchlorate/chemical buffer complexity; net raw water factor:
    raw_water_g_factor = 0.88 if gravity_regime == "mars" else 1.0

    p = _architecture_params(arch, crew_size=crew_size, destination=destination)
    esm_initial = p["m_initial"] + (p["v"] * c_v) + (p["p"] * c_p) + (p["c"] * c_c)
    monthly_rate = p["consumables_monthly"] + (p["t_monthly"] * c_t)

    cum_esm = esm_initial + (monthly_rate * mission_months)
    cum_edible_kg = crew_size * EDIBLE_DRY_BIOMASS_KG_PER_CREW_MONTH * mission_months * p["yield_factor"]
    cum_million_kcal = (cum_edible_kg * EDIBLE_KCAL_PER_KG_DRY) / 1e6

    # Monthly recurring consumables:
    # 1. Unrecovered water makeup: 120 kg/month (due to 80% recycling efficiency vs 98.5%)
    # 2. pH buffer acid resupply (HNO3/H2SO4) + chelates: ~12.1 kg/month (145 kg/yr)
    # 3. Dust filters & seals replacement: ~5.0 kg/month
    # 4. Crew labor converted to ESM: 40 hrs * 1.25 kg/hr = 50 kg ESM equivalent/mo
    raw_monthly_consumables_mass = ((120.0 * raw_water_g_factor) + 12.1 + 5.0) * scale
    raw_monthly_crew_esm = raw_t_monthly * c_t
    raw_monthly_esm_rate = raw_monthly_consumables_mass + raw_monthly_crew_esm


def calculate_esm(
    crew_size: int = 6,
    mission_months: int = 60,
    power_system: str = "nuclear",
    destination: str = "moon",
) -> Dict[str, any]:
    """
    Calculates cumulative ESM and monthly trajectories comparing Direct Regolith vs.
    Sintered Ceramic (preserving legacy API) plus all four AWG architectures.
    """
    raw = calculate_esm_architecture("direct_regolith", crew_size, mission_months, power_system, destination)
    hydro = calculate_esm_architecture("conventional_hydroponics", crew_size, mission_months, power_system, destination)
    hybrid = calculate_esm_architecture("hybrid_regolith", crew_size, mission_months, power_system, destination)
    sintered = calculate_esm_architecture("sintered_ceramic", crew_size, mission_months, power_system, destination)

    def _breakeven(a_init: float, a_rate: float, b_init: float, b_rate: float) -> float:
        delta_init = b_init - a_init
        delta_rate = a_rate - b_rate
        return round(delta_init / delta_rate, 1) if delta_rate > 0 else float("inf")

    breakeven_vs_raw = _breakeven(raw["initial_esm"], raw["monthly_rate"], sintered["initial_esm"], sintered["monthly_rate"])
    breakeven_vs_hydro = _breakeven(hydro["initial_esm"], hydro["monthly_rate"], sintered["initial_esm"], sintered["monthly_rate"])

    trajectory = []
    for m in range(mission_months + 1):
        cum_raw = raw["initial_esm"] + (raw["monthly_rate"] * m)
        cum_hydro = hydro["initial_esm"] + (hydro["monthly_rate"] * m)
        cum_hybrid = hybrid["initial_esm"] + (hybrid["monthly_rate"] * m)
        cum_sintered = sintered["initial_esm"] + (sintered["monthly_rate"] * m)
        trajectory.append({
            "month": m,
            "raw_esm": round(cum_raw, 1),
            "hydro_esm": round(cum_hydro, 1),
            "hybrid_esm": round(cum_hybrid, 1),
            "sintered_esm": round(cum_sintered, 1),
            "net_savings": round(cum_raw - cum_sintered, 1),
        })

    return {
        "crew_size": crew_size,
        "mission_months": mission_months,
        "power_system": power_system,
        "destination": destination,
        "raw_initial_esm": raw["initial_esm"],
        "raw_monthly_rate": raw["monthly_rate"],
        "sintered_initial_esm": sintered["initial_esm"],
        "sintered_monthly_rate": sintered["monthly_rate"],
        "breakeven_months": breakeven_vs_raw,
        "breakeven_vs_hydro_months": breakeven_vs_hydro,
        "net_savings_at_duration": round(trajectory[-1]["net_savings"], 1),
        "architectures": {
            "conventional_hydroponics": hydro,
            "direct_regolith": raw,
            "hybrid_regolith": hybrid,
            "sintered_ceramic": sintered,
        },
        "trajectory": trajectory,
    }


def print_summary_table():
    print("=" * 102)
    print("LUNAR BLSS EDAPHIC ARCHITECTURES: 4-SYSTEM ESM & EDIBLE YIELD TRADE STUDY (60 MONTHS, NUCLEAR)")
    print("=" * 102)
    print(f"{'Crew':<6} | {'Architecture':<25} | {'ESM (kg)':<10} | {'Edible (kg)':<12} | {'ESM/kg Edible':<14} | {'ESM/1e6 kcal'}")
    print("-" * 102)

    for crew in [3, 6, 12]:
        res = calculate_esm(crew_size=crew, mission_months=60)
        for key, label in [
            ("conventional_hydroponics", "Conventional Hydroponics"),
            ("direct_regolith", "Direct Regolith"),
            ("hybrid_regolith", "Hydroponic-Regolith Hybrid"),
            ("sintered_ceramic", "Sintered Ceramic ISRU"),
        ]:
            a = res["architectures"][key]
            print(f"{crew:<6} | {label:<25} | {a['final_esm']:<10,.0f} | {a['cum_edible_kg']:<12,.0f} | {a['esm_per_kg_edible']:<14.2f} | {a['esm_per_1e6_kcal']:,.1f}")
        print(f"       -> Sintered Breakeven: {res['breakeven_months']} mo (vs Direct Regolith) | {res['breakeven_vs_hydro_months']} mo (vs Conv. Hydroponics)")
        print("-" * 102)

    print("\nJONES ET AL. (2012) WLR GAS DIFFUSIVITY CHECK (Dp/Do >= 0.02 threshold):")
    for name, theta, phi in [
        ("Raw Lunar Regolith (saturated fines, theta=0.41, phi=0.45)", 0.41, 0.45),
        ("Profile + 40d Roots (theta=0.48, phi=0.60)", 0.48, 0.60),
        ("Sintered Ceramic 30-60 um (theta=0.14, phi=0.40)", 0.14, 0.40),
    ]:
        dp_do = compute_wlr_diffusivity(theta, phi)
        status = "AEROBIC OK" if dp_do >= 0.02 else "HYPOXIA RISK (<0.02)"
        print(f"  {name}: Dp/Do = {dp_do:.4f} [{status}]")
    print("=" * 102)

    print("\nEIGHT MISSION HORIZONS (6 CREW, NUCLEAR POWER — LUNAR 0.165g vs MARS 0.38g):")
    print("-" * 80)
    print(f"{'Horizon':<20} | {'Lunar Breakeven':<16} | {'Lunar Net Sav (kg)':<18} | {'Mars 0.38g Net Sav (kg)'}")
    print("-" * 80)
    for label, mo in MISSION_HORIZONS:
        lun = calculate_esm(crew_size=6, mission_months=max(1, int(round(mo))), gravity_regime="lunar")
        mar = calculate_esm(crew_size=6, mission_months=max(1, int(round(mo))), gravity_regime="mars")
        lun_net = (lun["raw_initial_esm"] + lun["raw_monthly_rate"] * mo) - (lun["sintered_initial_esm"] + lun["sintered_monthly_rate"] * mo)
        mar_net = (mar["raw_initial_esm"] + mar["raw_monthly_rate"] * mo) - (mar["sintered_initial_esm"] + mar["sintered_monthly_rate"] * mo)
        print(f"{label:<20} | {lun['breakeven_months']:<13.1f} mo | {lun_net:<18,.1f} | {mar_net:,.1f}")
    print("=" * 80)


if __name__ == "__main__":
    print_summary_table()
    os.makedirs("analysis/output", exist_ok=True)
    baseline = calculate_esm(crew_size=6, mission_months=60)
    os.makedirs("analysis/output", exist_ok=True)
    out_csv = "analysis/output/esm_trajectory_baseline.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["month", "raw_esm", "sintered_esm", "net_savings"])
        writer.writeheader()
        for row in baseline["trajectory"]:
            writer.writerow({k: row[k] for k in ["month", "raw_esm", "sintered_esm", "net_savings"]})

    out_4arch_csv = "analysis/output/esm_4arch_comparison.csv"
    with open(out_4arch_csv, "w", newline="") as f:
        fieldnames = ["month", "raw_esm", "hydro_esm", "hybrid_esm", "sintered_esm", "net_savings"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in baseline["trajectory"]:
            writer.writerow(row)

    print(f"\n[OK] Baseline trajectory exported to: {out_csv}")
    print(f"[OK] 4-architecture trajectory exported to: {out_4arch_csv}")
