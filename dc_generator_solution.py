#!/usr/bin/env python3
"""
DC Shunt Generator Series Winding Calculation
Standalone solution without GUI dependencies
"""


def interpolate_linear(x_data, y_data, x):
    """Simple linear interpolation"""
    for i in range(len(x_data) - 1):
        if x_data[i] <= x <= x_data[i + 1]:
            # Linear interpolation
            slope = (y_data[i + 1] - y_data[i]) / (x_data[i + 1] - x_data[i])
            return y_data[i] + slope * (x - x_data[i])

    # Extrapolation for values outside range
    if x < x_data[0]:
        slope = (y_data[1] - y_data[0]) / (x_data[1] - x_data[0])
        return y_data[0] + slope * (x - x_data[0])
    else:
        slope = (y_data[-1] - y_data[-2]) / (x_data[-1] - x_data[-2])
        return y_data[-1] + slope * (x - x_data[-1])


def inverse_interpolate(x_data, y_data, y):
    """Inverse interpolation - find x given y"""
    for i in range(len(y_data) - 1):
        if y_data[i] <= y <= y_data[i + 1]:
            # Linear interpolation
            slope = (x_data[i + 1] - x_data[i]) / (y_data[i + 1] - y_data[i])
            return x_data[i] + slope * (y - y_data[i])

    # Extrapolation
    if y < y_data[0]:
        slope = (x_data[1] - x_data[0]) / (y_data[1] - y_data[0])
        return x_data[0] + slope * (y - y_data[0])
    else:
        slope = (x_data[-1] - x_data[-2]) / (y_data[-1] - y_data[-2])
        return x_data[-1] + slope * (y - y_data[-1])


def solve_dc_generator_series_turns():
    """
    Solve for series winding turns per pole

    Problem: DC shunt generator with given OCC.
    Find series turns to make terminal voltage same at 50A output as no-load.
    """

    print("=" * 80)
    print(" DC SHUNT GENERATOR - SERIES WINDING CALCULATION")
    print("=" * 80)
    print()

    # Given data
    if_data = [0.2, 0.4, 0.6, 0.8, 1.0, 1.4, 2.0]  # Field current (A)
    emf_data = [80, 135, 178, 198, 210, 228, 246]   # EMF (V)

    N_sh = 1000      # Shunt turns per pole
    R_sh = 240       # Shunt resistance (Ω)
    R_a = 0.36       # Armature resistance including series winding (Ω)
    I_L = 50         # Load current (A)

    print("GIVEN DATA:")
    print("-" * 80)
    print(f"  Shunt winding turns per pole:     {N_sh} turns")
    print(f"  Shunt winding resistance:         {R_sh} Ω")
    print(f"  Armature resistance:              {R_a} Ω")
    print(f"  Load current:                     {I_L} A")
    print()
    print("  Open Circuit Characteristic (OCC):")
    print(f"  {'Field Current (A)':<20} {'EMF (V)':<10}")
    print(f"  {'-'*20} {'-'*10}")
    for i_f, emf in zip(if_data, emf_data):
        print(f"  {i_f:<20.1f} {emf:<10.0f}")
    print()

    # Step 1: Find no-load terminal voltage
    print("STEP 1: NO-LOAD CONDITION")
    print("-" * 80)

    # At no-load, terminal voltage ≈ generated EMF
    # Field current: I_f = V_t / R_sh
    # This requires iteration since V_t depends on I_f

    V_t_nl_guess = 220  # Initial guess

    print("  Iterating to find no-load voltage...")
    for iteration in range(50):
        I_f_nl = V_t_nl_guess / R_sh
        E_nl = interpolate_linear(if_data, emf_data, I_f_nl)
        V_t_nl = E_nl  # At no-load, I_a ≈ 0, so V_t ≈ E

        if abs(V_t_nl - V_t_nl_guess) < 0.1:
            break
        V_t_nl_guess = V_t_nl

    print(f"  Converged in {iteration + 1} iterations")
    print(f"  No-load terminal voltage:         {V_t_nl:.2f} V")
    print(f"  No-load field current:            {I_f_nl:.4f} A")
    print(f"  No-load generated EMF:            {E_nl:.2f} V")
    print()

    # Step 2: Load condition
    print("STEP 2: LOAD CONDITION (50 A)")
    print("-" * 80)

    # Terminal voltage at load should equal no-load voltage
    V_t_load = V_t_nl

    print(f"  Required terminal voltage:        {V_t_load:.2f} V (same as no-load)")

    # Shunt field current at load
    I_sh_load = V_t_load / R_sh
    print(f"  Shunt field current:              {I_sh_load:.4f} A")

    # Armature current
    I_a = I_L + I_sh_load
    print(f"  Armature current:                 {I_a:.4f} A")

    # Generated EMF at load
    E_load = V_t_load + I_a * R_a
    print(f"  Required generated EMF:           {E_load:.2f} V")
    print()

    # Step 3: Required field current
    print("STEP 3: FIELD CURRENT ANALYSIS")
    print("-" * 80)

    # From OCC, find field current needed to produce E_load
    I_f_total_required = inverse_interpolate(if_data, emf_data, E_load)
    print(f"  Total field current required:     {I_f_total_required:.4f} A")
    print(f"    (from OCC to produce {E_load:.2f} V)")
    print()

    # Series field contribution
    I_f_series = I_f_total_required - I_sh_load
    print(f"  Field current from shunt:         {I_sh_load:.4f} A")
    print(f"  Additional field current needed:  {I_f_series:.4f} A")
    print(f"    (to be provided by series winding)")
    print()

    # Step 4: Calculate series turns
    print("STEP 4: SERIES WINDING CALCULATION")
    print("-" * 80)

    # MMF balance:
    # Total MMF = MMF from shunt + MMF from series
    # N_sh * I_f_total = N_sh * I_sh + N_se * I_a
    #
    # Rearranging:
    # N_sh * (I_f_total - I_sh) = N_se * I_a
    # N_sh * I_f_series = N_se * I_a
    # N_se = (N_sh * I_f_series) / I_a

    N_se = (N_sh * I_f_series) / I_a

    print("  MMF Balance Equation:")
    print(f"    Total MMF required    = {N_sh * I_f_total_required:.2f} AT")
    print(f"    MMF from shunt        = {N_sh * I_sh_load:.2f} AT")
    print(f"    MMF from series       = {N_se * I_a:.2f} AT")
    print()
    print(f"  Series winding calculation:")
    print(f"    N_se = (N_sh × I_f_series) / I_a")
    print(f"    N_se = ({N_sh} × {I_f_series:.4f}) / {I_a:.4f}")
    print(f"    N_se = {N_se:.2f} turns per pole")
    print()

    # Verification
    print("STEP 5: VERIFICATION")
    print("-" * 80)

    mmf_shunt = N_sh * I_sh_load
    mmf_series = N_se * I_a
    mmf_total_actual = mmf_shunt + mmf_series
    mmf_total_required = N_sh * I_f_total_required

    print(f"  MMF from shunt winding:           {mmf_shunt:.2f} AT")
    print(f"  MMF from series winding:          {mmf_series:.2f} AT")
    print(f"  Total MMF (actual):               {mmf_total_actual:.2f} AT")
    print(f"  Total MMF (required):             {mmf_total_required:.2f} AT")
    print(f"  Error:                            {abs(mmf_total_actual - mmf_total_required):.4f} AT")
    print()

    # Final result
    print("=" * 80)
    print(" FINAL RESULT")
    print("=" * 80)
    print()
    print(f"  ╔════════════════════════════════════════════════════════════════════╗")
    print(f"  ║  SERIES WINDING TURNS REQUIRED:  {N_se:>6.2f} turns per pole        ║")
    print(f"  ╚════════════════════════════════════════════════════════════════════╝")
    print()
    print("EXPLANATION:")
    print("-" * 80)
    print(f"""
  The series winding provides additional magnetomotive force (MMF) to
  compensate for the voltage drop across the armature resistance when
  the generator is loaded.

  At no-load:
    • Terminal voltage = {V_t_nl:.2f} V
    • Only shunt field provides excitation

  At 50 A load:
    • Without series winding, voltage would drop due to I×R loss
    • Series winding adds {mmf_series:.2f} AT of MMF
    • This increases generated EMF from {E_nl:.2f} V to {E_load:.2f} V
    • Terminal voltage maintained at {V_t_load:.2f} V

  The series winding makes this a COMPOUND generator with FLAT compounding
  (constant terminal voltage from no-load to full-load).
""")
    print("=" * 80)

    return N_se


if __name__ == "__main__":
    series_turns = solve_dc_generator_series_turns()
    print(f"\nCalculation complete. Series turns = {series_turns:.2f} turns/pole\n")
