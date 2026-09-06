#!/usr/bin/env python3
"""
ESM Model: Equivalent System Mass Lifecycle Evaluation for Lunar BLSS Edaphic Architectures

This module implements the NASA Advanced Life Support (ALS) Equivalent System Mass (ESM)
framework formalized in the Baseline Values and Assumptions Document (BVAD; Hanford, 2004)
to quantitatively compare two lunar crop-production edaphic paradigms:
  1. Direct Regolith Cultivation (Unprocessed Lunar Soil Augmented with Nutrient Solution)
  2. Sintered Regolith Ceramic Hydroponics (ISRU Engineered Porous Ceramic Bio-Infrastructure)

Mathematical Formulation:
  ESM = M + (V * C_V) + (P * C_P) + (C * C_C) + (T * C_T)
Where:
  M   = Hardware and consumable initial mass (kg)
  V   = Pressurized habitat volume occupied (m^3)
  C_V = Habitat volume equivalency factor (kg/m^3) [Nominal: 9.16 - 12.5 kg/m^3]
  P   = Operational electrical power demand (kWe)
  C_P = Power infrastructure equivalency factor (kg/kWe) [Nuclear: ~54 kg/kWe; Solar: ~237 kg/kWe]
  C   = Thermal cooling / heat rejection load (kWth)
  C_C = Thermal infrastructure equivalency factor (kg/kWth) [Nominal: 60 - 145 kg/kWth]
  T   = Routine crew maintenance labor (crew-hours/year)
  C_T = Crew time equivalency factor (kg/crew-hour) [Nominal: 1.25 kg/crew-hour]

Parametric Consumables & Degradation Functions:
  - Direct Regolith Cultivation experiences:
      * Capillary entrapment in sub-micron fines: water recovery efficiency eta_H2O ~ 78-82%
      * Mineral alkaline dissolution spikes: buffer resupply ~ 145 kg/year per 6-crew module
      * Mechanical wear & dust filter replacements: ongoing crew maintenance penalty
  - Sintered Ceramic Hydroponics experiences:
      * Controlled monodisperse pore throat (30-60 um): eta_H2O > 98.5%
      * Passivated vitrified silicate matrix: stable pH 5.8-6.2, buffer resupply < 8 kg/year
      * High initial upfront capital mass (sintering plant: ~1850 kg for 6 crew)
"""

import math
import sys
import json
import csv
from typing import Dict, List, Tuple


# NASA BVAD Lunar Surface Equivalency Factors (Hanford, 2004; Bilardo et al., 2024)
BVAD_FACTORS = {
    "C_V": 9.16,      # kg/m^3 (pressurized volume infrastructure mass)
    "C_P_nuclear": 54.0,   # kg/kWe (surface fission power system)
    "C_P_solar": 237.0,    # kg/kWe (PV + RFC energy storage for 14-day lunar night)
    "C_C": 85.0,      # kg/kWth (composite thermal radiator system)
    "C_T": 1.25       # kg/crew-hour (crew time mass equivalent)
}


def calculate_esm(
    crew_size: int = 6,
    mission_months: int = 60,
    power_system: str = "nuclear"
) -> Dict[str, any]:
    """
    Calculates cumulative ESM and monthly trajectories for both paradigms.
    """
    scale = crew_size / 6.0
    c_p = BVAD_FACTORS["C_P_nuclear"] if power_system == "nuclear" else BVAD_FACTORS["C_P_solar"]
    c_v = BVAD_FACTORS["C_V"]
    c_c = BVAD_FACTORS["C_C"]
    c_t = BVAD_FACTORS["C_T"]

    # --- DIRECT REGOLITH SYSTEM ---
    # Upfront hardware: shallow bed containers, soil handling tools, local seals
    raw_m_initial = 420.0 * scale
    raw_v = 12.5 * scale  # m^3
    raw_p = 1.2 * scale   # kWe
    raw_c = 1.0 * scale   # kWth
    raw_t_monthly = (40.0 * scale)  # crew-hours per month (dust cleanup, filter change, mixing)

    # Initial ESM component
    raw_esm_initial = (
        raw_m_initial +
        (raw_v * c_v) +
        (raw_p * c_p) +
        (raw_c * c_c)
    )

    # Monthly recurring consumables:
    # 1. Unrecovered water makeup: 120 kg/month (due to 80% recycling efficiency vs 98.5%)
    # 2. pH buffer acid resupply (HNO3/H2SO4) + chelates: ~12.1 kg/month (145 kg/yr)
    # 3. Dust filters & seals replacement: ~5.0 kg/month
    # 4. Crew labor converted to ESM: 40 hrs * 1.25 kg/hr = 50 kg ESM equivalent/mo
    raw_monthly_consumables_mass = (120.0 + 12.1 + 5.0) * scale
    raw_monthly_crew_esm = raw_t_monthly * c_t
    raw_monthly_esm_rate = raw_monthly_consumables_mass + raw_monthly_crew_esm

    # --- SINTERED CERAMIC SYSTEM ---
    # Upfront hardware: microwave/solar sintering tooling, classification sieves, molds
    sintered_m_initial = 1850.0 + (150.0 * (crew_size - 6))
    sintered_v = 4.2 * scale   # m^3 (compact multi-tier vertical troughs)
    sintered_p = 2.4 * scale   # kWe (fluid pumps + sensor networks; sintering occurs pre-ops)
    sintered_c = 2.0 * scale   # kWth
    sintered_t_monthly = 6.0 * scale # crew-hours per month (routine inspection)

    sintered_esm_initial = (
        sintered_m_initial +
        (sintered_v * c_v) +
        (sintered_p * c_p) +
        (sintered_c * c_c)
    )

    # Monthly recurring consumables:
    # 1. Water makeup (>98.5% recovery): ~18 kg/month
    # 2. pH buffer resupply (<8 kg/yr): ~0.67 kg/month
    # 3. Replacement wick / filter elements: ~1.5 kg/month
    # 4. Crew labor converted to ESM: 6 hrs * 1.25 kg/hr = 7.5 kg ESM equivalent/mo
    sintered_monthly_consumables_mass = (18.0 + 0.67 + 1.5) * scale
    sintered_monthly_crew_esm = sintered_t_monthly * c_t
    sintered_monthly_esm_rate = sintered_monthly_consumables_mass + sintered_monthly_crew_esm

    # Breakeven point in months:
    delta_initial = sintered_esm_initial - raw_esm_initial
    delta_monthly = raw_monthly_esm_rate - sintered_monthly_esm_rate
    breakeven_months = delta_initial / delta_monthly if delta_monthly > 0 else float("inf")

    # Generate monthly trajectory
    trajectory = []
    for m in range(mission_months + 1):
        cum_raw = raw_esm_initial + (raw_monthly_esm_rate * m)
        cum_sintered = sintered_esm_initial + (sintered_monthly_esm_rate * m)
        net_savings = cum_raw - cum_sintered
        trajectory.append({
            "month": m,
            "raw_esm": round(cum_raw, 1),
            "sintered_esm": round(cum_sintered, 1),
            "net_savings": round(net_savings, 1)
        })

    return {
        "crew_size": crew_size,
        "mission_months": mission_months,
        "power_system": power_system,
        "raw_initial_esm": round(raw_esm_initial, 1),
        "raw_monthly_rate": round(raw_monthly_esm_rate, 2),
        "sintered_initial_esm": round(sintered_esm_initial, 1),
        "sintered_monthly_rate": round(sintered_monthly_esm_rate, 2),
        "breakeven_months": round(breakeven_months, 1),
        "net_savings_at_duration": round(trajectory[-1]["net_savings"], 1),
        "trajectory": trajectory
    }


def print_summary_table():
    print("=" * 80)
    print("LUNAR BLSS EDAPHIC ARCHITECTURE: EQUIVALENT SYSTEM MASS (ESM) TRADE STUDY")
    print("=" * 80)
    print(f"{'Crew Size':<10} | {'Horizon':<10} | {'Raw ESM (kg)':<14} | {'Sintered ESM (kg)':<18} | {'Net Savings':<14} | {'Breakeven'}")
    print("-" * 80)

    for crew in [3, 6, 12]:
        for months in [24, 60]:
            res = calculate_esm(crew_size=crew, mission_months=months)
            final = res["trajectory"][-1]
            print(f"{crew:<10} | {months} mo{'':<5} | {final['raw_esm']:<14,.0f} | {final['sintered_esm']:<18,.0f} | {final['net_savings']:<14,.0f} | {res['breakeven_months']:.1f} mo")
    print("=" * 80)


if __name__ == "__main__":
    print_summary_table()
    # Save baseline 6-crew 60-month run to CSV
    baseline = calculate_esm(crew_size=6, mission_months=60)
    out_csv = "analysis/output/esm_trajectory_baseline.csv"
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["month", "raw_esm", "sintered_esm", "net_savings"])
        writer.writeheader()
        for row in baseline["trajectory"]:
            writer.writerow(row)
    print(f"\n[OK] Baseline trajectory successfully exported to: {out_csv}")
