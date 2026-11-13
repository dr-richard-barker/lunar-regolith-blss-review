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

import csv
import os
from typing import Dict, List


# NASA BVAD Lunar/Planetary Surface Equivalency Factors (Hanford, 2004; Ewert et al., 2022; Bilardo et al., 2024)
BVAD_FACTORS = {
    "C_V": 9.16,          # kg/m^3 (pressurized volume infrastructure mass)
    "C_P_nuclear": 54.0,  # kg/kWe (surface fission power system)
    "C_P_solar": 237.0,   # kg/kWe (PV + RFC energy storage for 14-day lunar night)
    "C_C": 85.0,          # kg/kWth (composite thermal radiator system)
    "C_T": 1.25,          # kg/crew-hour (crew time mass equivalent)
}

# BVAD (2022) Nominal Edible Crop Productivity (per crew member, 50% caloric/fresh BLSS target)
EDIBLE_DRY_BIOMASS_KG_PER_CREW_MONTH = 10.5   # ~0.35 kg dry edible/crew-day
EDIBLE_KCAL_PER_KG_DRY = 3800.0               # nominal mixed crop caloric density

# Gravity ratios relative to Earth (g / g_E)
GRAVITY_RATIOS = {
    "earth": 1.00,
    "mars": 0.38,
    "moon": 0.16,
}

# Hydraulic parameters from Jones et al. (2012) Table 1 & Sintered Ceramic Design Target
SUBSTRATE_HYDRAULIC_PRESETS = {
    "turface_1g": {"alpha_cm_inv": 0.19, "n": 5.6, "theta_r": 0.34, "theta_s": 0.73, "K_s_cm_d": 41000.0},
    "mars_dune_sand_038g": {"alpha_cm_inv": 0.0304, "n": 10.0, "theta_r": 0.05, "theta_s": 0.40, "K_s_cm_d": 500.0},
    "lunar_regolith_016g": {"alpha_cm_inv": 0.0066, "n": 1.6, "theta_r": 0.05, "theta_s": 0.45, "K_s_cm_d": 30.0},
    "profile_1g": {"alpha_cm_inv": 0.086, "n": 5.1, "theta_r": 0.36, "theta_s": 0.71, "K_s_cm_d": None},
    "profile_40d_roots_1g": {"alpha_cm_inv": 0.055, "n": 3.1, "theta_r": 0.36, "theta_s": 0.60, "K_s_cm_d": None},
    "sintered_ceramic_016g": {"alpha_cm_inv": 0.035, "n": 4.8, "theta_r": 0.04, "theta_s": 0.40, "K_s_cm_d": 450.0},
}


def scale_van_genuchten_alpha(alpha_1g: float, gravity_ratio: float) -> float:
    """Miller & Miller (1955) linear gravity scaling of van Genuchten alpha (Jones et al., 2012)."""
    return alpha_1g * gravity_ratio


def arya_paris_pore_radius(particle_radius_um: float, porosity: float) -> float:
    """Simplified Arya & Paris (1981) / Jones & Or (1998) pore-to-particle radius relation (Eq. 1)."""
    if not (0.0 < porosity < 1.0):
        raise ValueError("Porosity must be strictly between 0 and 1.")
    return particle_radius_um * ((2.0 / 3.0) * (porosity / (1.0 - porosity))) ** 0.5


def compute_wlr_diffusivity(theta: float, phi: float) -> float:
    """
    Moldrup et al. (2000) Water-induced Linear Reduction (WLR) relative gas diffusivity Dp / Do.
    Critical lower percolation threshold for root aeration is 0.02 (2%; Schjonning et al., 2003).
    """
    if phi <= 0.0:
        raise ValueError("Total porosity phi must be positive.")
    epsilon = max(0.0, phi - theta)
    return (epsilon ** 2.5) / phi


def _architecture_params(
    arch: str,
    crew_size: int,
    destination: str = "moon",
) -> Dict[str, float]:
    """
    Returns baseline hardware, volume, power, thermal, crew-time, and consumable parameters
    scaled for a given architecture, crew size, and destination gravity/transit regime.
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

    p = _architecture_params(arch, crew_size=crew_size, destination=destination)
    esm_initial = p["m_initial"] + (p["v"] * c_v) + (p["p"] * c_p) + (p["c"] * c_c)
    monthly_rate = p["consumables_monthly"] + (p["t_monthly"] * c_t)

    cum_esm = esm_initial + (monthly_rate * mission_months)
    cum_edible_kg = crew_size * EDIBLE_DRY_BIOMASS_KG_PER_CREW_MONTH * mission_months * p["yield_factor"]
    cum_million_kcal = (cum_edible_kg * EDIBLE_KCAL_PER_KG_DRY) / 1e6

    return {
        "architecture": arch,
        "crew_size": crew_size,
        "mission_months": mission_months,
        "destination": destination,
        "power_system": power_system,
        "initial_esm": round(esm_initial, 1),
        "monthly_rate": round(monthly_rate, 2),
        "final_esm": round(cum_esm, 1),
        "cum_edible_kg": round(cum_edible_kg, 1),
        "esm_per_kg_edible": round(cum_esm / cum_edible_kg, 2) if cum_edible_kg > 0 else float("inf"),
        "esm_per_1e6_kcal": round(cum_esm / cum_million_kcal, 1) if cum_million_kcal > 0 else float("inf"),
    }


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


if __name__ == "__main__":
    print_summary_table()
    os.makedirs("analysis/output", exist_ok=True)
    baseline = calculate_esm(crew_size=6, mission_months=60)

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
