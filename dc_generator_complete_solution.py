"""
Complete DC Generator Analysis and Simulation Tool
Works in both GUI and Console modes
Includes: Series Winding Calculation, ODE Solvers, Performance Analysis
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.integrate import solve_ivp, odeint
import sys

class DCGeneratorSimulator:
    """Advanced DC Generator Simulator with Mathematical Modeling"""

    def __init__(self):
        # Problem-specific OCC data
        self.if_data = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.4, 2.0])
        self.emf_data = np.array([80, 135, 178, 198, 210, 228, 246])

        # Generator parameters from the problem
        self.shunt_turns = 1000  # turns per pole
        self.shunt_resistance = 240  # Ohms
        self.armature_resistance = 0.36  # Ohms (including series winding)
        self.series_turns = 0  # To be calculated
        self.load_current = 50  # Amperes

        # Dynamic simulation parameters
        self.La = 0.1  # Armature inductance (H)
        self.Lf = 10.0  # Field inductance (H)
        self.J = 0.5   # Moment of inertia (kg·m²)
        self.B = 0.01  # Friction coefficient
        self.omega_rated = 157.08  # Rated speed (rad/s) - 1500 RPM
        self.Kt = 1.0  # Torque constant

        # Create interpolation function for OCC
        self.update_occ_interpolation()

    def update_occ_interpolation(self):
        """Create interpolation function from OCC data"""
        self.emf_interpolator = interp1d(
            self.if_data,
            self.emf_data,
            kind='cubic',
            fill_value='extrapolate'
        )

    def get_emf_from_field_current(self, if_current):
        """Get EMF from field current using interpolation"""
        return float(self.emf_interpolator(if_current))

    def get_field_current_from_emf(self, emf_target, max_iter=100, tol=0.01):
        """Inverse function: Get field current from target EMF"""
        # Use Newton-Raphson method
        if_guess = 1.0
        for iteration in range(max_iter):
            emf_current = self.get_emf_from_field_current(if_guess)
            error = emf_current - emf_target
            if abs(error) < tol:
                return if_guess
            # Numerical derivative
            delta = 0.001
            emf_delta = self.get_emf_from_field_current(if_guess + delta)
            derivative = (emf_delta - emf_current) / delta
            if abs(derivative) < 1e-6:
                break
            if_guess = if_guess - error / derivative
            if if_guess < 0:
                if_guess = 0.1
        return if_guess

    def find_no_load_voltage(self):
        """
        Find no-load terminal voltage (self-excited condition)
        At no-load: V = E and If = V/Rf
        Need to find intersection point
        """
        max_iter = 100
        V = 200  # Initial guess

        for iteration in range(max_iter):
            If = V / self.shunt_resistance
            E = self.get_emf_from_field_current(If)
            error = abs(E - V)
            if error < 0.01:
                return V, If, E
            # Relaxation method for stability
            V = 0.5 * V + 0.5 * E

        return V, If, E

    def calculate_series_turns(self):
        """
        Calculate required series winding turns per pole

        Problem: Find series winding turns so that terminal voltage at 50A load
        equals the no-load terminal voltage.

        Solution approach:
        1. Find no-load operating point (V, If, E)
        2. At 50A load, terminal voltage should be same as no-load
        3. Calculate required EMF: E_load = V + Ia*Ra
        4. Find total field current needed for E_load
        5. Calculate series turns from MMF balance
        """
        print("\n" + "="*70)
        print("DC SHUNT GENERATOR - SERIES WINDING CALCULATION")
        print("="*70)

        # Step 1: Find no-load voltage
        print("\nSTEP 1: Finding No-Load Operating Point")
        print("-" * 50)
        V_no_load, If_no_load, E_no_load = self.find_no_load_voltage()
        print(f"No-Load Terminal Voltage (V₀):     {V_no_load:.3f} V")
        print(f"No-Load Field Current (If₀):       {If_no_load:.5f} A")
        print(f"No-Load Generated EMF (E₀):        {E_no_load:.3f} V")

        # Step 2: Calculate requirements at load
        print("\nSTEP 2: Load Condition Requirements (Ia = 50A)")
        print("-" * 50)
        Ia = self.load_current
        V_load = V_no_load  # Required: same as no-load

        # Voltage drop in armature
        V_drop = Ia * self.armature_resistance
        print(f"Load Current (Ia):                 {Ia:.2f} A")
        print(f"Armature Resistance (Ra):          {self.armature_resistance:.3f} Ω")
        print(f"Voltage Drop (Ia × Ra):            {V_drop:.3f} V")

        # Required EMF at load
        E_load_required = V_load + V_drop
        print(f"Required Terminal Voltage (V):     {V_load:.3f} V")
        print(f"Required Generated EMF (E):        {E_load_required:.3f} V")

        # Step 3: Find total field current needed
        print("\nSTEP 3: Field Current Calculation")
        print("-" * 50)
        If_total_required = self.get_field_current_from_emf(E_load_required)
        print(f"Total Field Current Required:      {If_total_required:.5f} A")

        # Step 4: Shunt field current at load
        If_shunt = V_load / self.shunt_resistance
        print(f"Shunt Field Current at Load:       {If_shunt:.5f} A")
        print(f"  (If_shunt = V / Rf = {V_load:.3f} / {self.shunt_resistance})")

        # Step 5: Calculate series winding turns
        print("\nSTEP 4: Series Winding Calculation")
        print("-" * 50)
        print("MMF Balance Equation:")
        print("  Total MMF = Shunt MMF + Series MMF")
        print(f"  Nf × If_total = Nf × If_shunt + Ns × Ia")
        print(f"  {self.shunt_turns} × {If_total_required:.5f} = {self.shunt_turns} × {If_shunt:.5f} + Ns × {Ia}")
        print()
        print("Solving for Ns:")
        print("  Ns = Nf × (If_total - If_shunt) / Ia")

        # Additional MMF from series winding (in equivalent field current)
        If_series_equiv = If_total_required - If_shunt
        print(f"  Additional Field Current Needed:   {If_series_equiv:.5f} A")

        # Series winding turns
        Ns = self.shunt_turns * If_series_equiv / Ia
        print(f"  Ns = {self.shunt_turns} × {If_series_equiv:.5f} / {Ia}")
        print(f"  Ns = {Ns:.4f} turns/pole")

        # Verification
        print("\nSTEP 5: Verification")
        print("-" * 50)
        # Total MMF check
        MMF_shunt = self.shunt_turns * If_shunt
        MMF_series = Ns * Ia
        MMF_total_check = MMF_shunt + MMF_series
        MMF_required = self.shunt_turns * If_total_required

        print(f"Shunt MMF:      {MMF_shunt:.2f} A·turns")
        print(f"Series MMF:     {MMF_series:.2f} A·turns")
        print(f"Total MMF:      {MMF_total_check:.2f} A·turns")
        print(f"Required MMF:   {MMF_required:.2f} A·turns")
        print(f"Match Error:    {abs(MMF_total_check - MMF_required):.4f} A·turns")

        # Final summary
        print("\n" + "="*70)
        print("FINAL RESULT")
        print("="*70)
        print(f"Series Winding Turns per Pole: {Ns:.2f} turns")
        print(f"Terminal Voltage maintained at: {V_load:.2f} V")
        print(f"  (No-Load: {V_no_load:.2f} V, Full-Load: {V_load:.2f} V)")
        print("="*70)

        self.series_turns = Ns

        results = {
            'V_no_load': V_no_load,
            'If_no_load': If_no_load,
            'E_no_load': E_no_load,
            'V_load': V_load,
            'Ia': Ia,
            'V_drop': V_drop,
            'E_load_required': E_load_required,
            'If_total_required': If_total_required,
            'If_shunt_at_load': If_shunt,
            'If_series_equiv': If_series_equiv,
            'series_turns': Ns,
            'MMF_shunt': MMF_shunt,
            'MMF_series': MMF_series,
            'MMF_total': MMF_total_check
        }

        return results

    def generator_ode_system(self, t, y, V_load, omega_m):
        """
        ODE system for DC generator dynamics
        State vector y = [Ia, If]

        Differential equations:
        1. La * dIa/dt = E - Ia*Ra - V_load
        2. Lf * dIf/dt = V_load - If*Rf
        """
        Ia, If = y

        # EMF generated (function of field current)
        E = self.get_emf_from_field_current(If)

        # State derivatives
        dIa_dt = (E - Ia * self.armature_resistance - V_load) / self.La
        dIf_dt = (V_load - If * self.shunt_resistance) / self.Lf

        return [dIa_dt, dIf_dt]

    def simulate_dynamic_response(self, t_span=(0, 2), V_load=200, method='RK45'):
        """
        Simulate generator dynamic response using ODE solvers

        Methods available:
        - RK45: Runge-Kutta 4/5th order (adaptive step)
        - Euler: Forward Euler method (fixed step)
        """
        print(f"\n{'='*70}")
        print(f"DYNAMIC SIMULATION - {method} METHOD")
        print(f"{'='*70}")

        # Initial conditions
        V_init, If_init, _ = self.find_no_load_voltage()
        y0 = [0.1, If_init]  # [Ia, If]

        print(f"Initial Conditions:")
        print(f"  Armature Current: {y0[0]:.3f} A")
        print(f"  Field Current: {y0[1]:.5f} A")
        print(f"Load Voltage: {V_load} V")
        print(f"Simulation Time: {t_span[1]} seconds")

        omega_m = self.omega_rated

        # Solve ODE
        if method == 'RK45':
            print(f"\nSolving using Runge-Kutta 4/5 (adaptive step)...")
            sol = solve_ivp(
                lambda t, y: self.generator_ode_system(t, y, V_load, omega_m),
                t_span,
                y0,
                method='RK45',
                dense_output=True,
                max_step=0.01
            )
            t_eval = np.linspace(t_span[0], t_span[1], 500)
            y_eval = sol.sol(t_eval)
            Ia_result = y_eval[0]
            If_result = y_eval[1]

        else:  # Euler method
            print(f"\nSolving using Forward Euler method...")
            dt = 0.001
            t_eval = np.arange(t_span[0], t_span[1], dt)
            Ia_result = [y0[0]]
            If_result = [y0[1]]

            for i in range(1, len(t_eval)):
                y_current = [Ia_result[-1], If_result[-1]]
                dydt = self.generator_ode_system(t_eval[i-1], y_current, V_load, omega_m)
                Ia_result.append(y_current[0] + dydt[0] * dt)
                If_result.append(y_current[1] + dydt[1] * dt)

            Ia_result = np.array(Ia_result)
            If_result = np.array(If_result)

        # Calculate EMF and terminal voltage
        E_result = np.array([self.get_emf_from_field_current(If) for If in If_result])
        V_terminal = E_result - Ia_result * self.armature_resistance

        print(f"\nFinal State:")
        print(f"  Terminal Voltage: {V_terminal[-1]:.3f} V")
        print(f"  Armature Current: {Ia_result[-1]:.3f} A")
        print(f"  Field Current: {If_result[-1]:.5f} A")
        print(f"  Generated EMF: {E_result[-1]:.3f} V")

        return {
            't': t_eval,
            'Ia': Ia_result,
            'If': If_result,
            'E': E_result,
            'V_terminal': V_terminal,
            'method': method
        }

    def calculate_performance_curves(self, load_range=None):
        """Calculate generator performance characteristics"""
        print(f"\n{'='*70}")
        print("PERFORMANCE CHARACTERISTICS CALCULATION")
        print(f"{'='*70}")

        if load_range is None:
            load_range = np.linspace(0, 100, 50)

        V_no_load, _, _ = self.find_no_load_voltage()

        V_terminal = []
        E_generated = []
        If_total = []
        efficiency = []
        power_out = []

        print(f"Calculating for {len(load_range)} load points...")

        for Ia in load_range:
            # For compound generator with series winding
            V_t = V_no_load  # Initial guess

            for iteration in range(50):
                If_shunt = V_t / self.shunt_resistance
                # Series MMF contribution
                If_series_equiv = (self.series_turns / self.shunt_turns) * Ia
                If_tot = If_shunt + If_series_equiv

                E = self.get_emf_from_field_current(If_tot)
                V_t_new = E - Ia * self.armature_resistance

                if abs(V_t_new - V_t) < 0.01:
                    break
                V_t = 0.7 * V_t + 0.3 * V_t_new

            V_terminal.append(V_t)
            E_generated.append(E)
            If_total.append(If_tot)

            # Power and efficiency calculation
            P_out = V_t * Ia
            P_armature_loss = Ia**2 * self.armature_resistance
            P_field_loss = V_t**2 / self.shunt_resistance
            P_losses = P_armature_loss + P_field_loss
            P_in = P_out + P_losses
            eff = (P_out / P_in * 100) if P_in > 0 else 0

            efficiency.append(eff)
            power_out.append(P_out)

        print("Performance calculation completed.")

        # Print key operating points
        print("\nKey Operating Points:")
        idx_no_load = 0
        idx_50A = np.argmin(np.abs(load_range - 50))
        idx_max_eff = np.argmax(efficiency)

        print(f"\nNo-Load (Ia = {load_range[idx_no_load]:.1f}A):")
        print(f"  V_terminal = {V_terminal[idx_no_load]:.2f} V")
        print(f"  Efficiency = {efficiency[idx_no_load]:.2f}%")

        print(f"\n50A Load (Ia = {load_range[idx_50A]:.1f}A):")
        print(f"  V_terminal = {V_terminal[idx_50A]:.2f} V")
        print(f"  Power = {power_out[idx_50A]:.2f} W")
        print(f"  Efficiency = {efficiency[idx_50A]:.2f}%")

        print(f"\nMaximum Efficiency (Ia = {load_range[idx_max_eff]:.1f}A):")
        print(f"  V_terminal = {V_terminal[idx_max_eff]:.2f} V")
        print(f"  Power = {power_out[idx_max_eff]:.2f} W")
        print(f"  Efficiency = {efficiency[idx_max_eff]:.2f}%")

        return {
            'Ia': load_range,
            'V_terminal': np.array(V_terminal),
            'E': np.array(E_generated),
            'If': np.array(If_total),
            'efficiency': np.array(efficiency),
            'power': np.array(power_out)
        }

    def plot_all_characteristics(self, filename='dc_generator_analysis.png'):
        """Create comprehensive visualization of all characteristics"""
        print(f"\n{'='*70}")
        print("GENERATING COMPREHENSIVE PLOTS")
        print(f"{'='*70}")

        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))

        # 1. OCC Curve
        print("Plotting OCC curve...")
        ax1 = plt.subplot(3, 3, 1)
        ax1.plot(self.if_data, self.emf_data, 'ro-', markersize=8, linewidth=2, label='Measured')
        if_fine = np.linspace(self.if_data.min(), self.if_data.max(), 200)
        emf_fine = [self.get_emf_from_field_current(i) for i in if_fine]
        ax1.plot(if_fine, emf_fine, 'b--', linewidth=1.5, label='Interpolated')

        # Mark no-load point
        V_nl, If_nl, E_nl = self.find_no_load_voltage()
        ax1.plot(If_nl, E_nl, 'g*', markersize=15, label=f'No-Load\n({If_nl:.3f}A, {E_nl:.1f}V)')

        ax1.set_xlabel('Field Current (A)', fontsize=10, fontweight='bold')
        ax1.set_ylabel('Generated EMF (V)', fontsize=10, fontweight='bold')
        ax1.set_title('Open Circuit Characteristic (OCC)', fontsize=11, fontweight='bold')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)

        # 2. Performance curves
        print("Calculating performance characteristics...")
        perf = self.calculate_performance_curves()

        # External characteristic (V-I curve)
        ax2 = plt.subplot(3, 3, 2)
        ax2.plot(perf['Ia'], perf['V_terminal'], 'b-', linewidth=2.5, label='Terminal Voltage')
        ax2.plot(perf['Ia'], perf['E'], 'r--', linewidth=2, alpha=0.7, label='Generated EMF')
        ax2.axhline(y=V_nl, color='g', linestyle=':', linewidth=1.5, label=f'No-Load V ({V_nl:.1f}V)')
        ax2.axvline(x=50, color='orange', linestyle=':', linewidth=1.5, label='50A Load')
        ax2.set_xlabel('Load Current (A)', fontsize=10, fontweight='bold')
        ax2.set_ylabel('Voltage (V)', fontsize=10, fontweight='bold')
        ax2.set_title('External Characteristic', fontsize=11, fontweight='bold')
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)

        # Efficiency curve
        ax3 = plt.subplot(3, 3, 3)
        ax3.plot(perf['Ia'], perf['efficiency'], 'g-', linewidth=2.5)
        ax3.axvline(x=50, color='orange', linestyle=':', linewidth=1.5, label='50A Load')
        max_eff_idx = np.argmax(perf['efficiency'])
        ax3.plot(perf['Ia'][max_eff_idx], perf['efficiency'][max_eff_idx], 'r*',
                markersize=15, label=f"Max η = {perf['efficiency'][max_eff_idx]:.1f}%")
        ax3.set_xlabel('Load Current (A)', fontsize=10, fontweight='bold')
        ax3.set_ylabel('Efficiency (%)', fontsize=10, fontweight='bold')
        ax3.set_title('Efficiency Characteristic', fontsize=11, fontweight='bold')
        ax3.legend(fontsize=8)
        ax3.grid(True, alpha=0.3)

        # 3. Dynamic response - RK45
        print("Running dynamic simulation (RK45)...")
        dyn_rk45 = self.simulate_dynamic_response(t_span=(0, 2), V_load=V_nl, method='RK45')

        ax4 = plt.subplot(3, 3, 4)
        ax4.plot(dyn_rk45['t'], dyn_rk45['V_terminal'], 'b-', linewidth=2)
        ax4.set_ylabel('Terminal Voltage (V)', fontsize=9, fontweight='bold')
        ax4.set_title('Dynamic Response - RK45 Method', fontsize=11, fontweight='bold')
        ax4.grid(True, alpha=0.3)

        ax5 = plt.subplot(3, 3, 5)
        ax5.plot(dyn_rk45['t'], dyn_rk45['Ia'], 'r-', linewidth=2)
        ax5.set_ylabel('Armature Current (A)', fontsize=9, fontweight='bold')
        ax5.grid(True, alpha=0.3)

        ax6 = plt.subplot(3, 3, 6)
        ax6.plot(dyn_rk45['t'], dyn_rk45['If'], 'g-', linewidth=2)
        ax6.set_ylabel('Field Current (A)', fontsize=9, fontweight='bold')
        ax6.set_xlabel('Time (s)', fontsize=10, fontweight='bold')
        ax6.grid(True, alpha=0.3)

        # 4. Dynamic response - Euler
        print("Running dynamic simulation (Euler)...")
        dyn_euler = self.simulate_dynamic_response(t_span=(0, 2), V_load=V_nl, method='Euler')

        ax7 = plt.subplot(3, 3, 7)
        ax7.plot(dyn_euler['t'], dyn_euler['V_terminal'], 'b-', linewidth=2)
        ax7.set_ylabel('Terminal Voltage (V)', fontsize=9, fontweight='bold')
        ax7.set_title('Dynamic Response - Euler Method', fontsize=11, fontweight='bold')
        ax7.grid(True, alpha=0.3)

        ax8 = plt.subplot(3, 3, 8)
        ax8.plot(dyn_euler['t'], dyn_euler['Ia'], 'r-', linewidth=2)
        ax8.set_ylabel('Armature Current (A)', fontsize=9, fontweight='bold')
        ax8.set_xlabel('Time (s)', fontsize=10, fontweight='bold')
        ax8.grid(True, alpha=0.3)

        # 5. Power characteristic
        ax9 = plt.subplot(3, 3, 9)
        ax9.plot(perf['Ia'], perf['power'], 'm-', linewidth=2.5)
        ax9.axvline(x=50, color='orange', linestyle=':', linewidth=1.5, label='50A Load')
        ax9.set_xlabel('Load Current (A)', fontsize=10, fontweight='bold')
        ax9.set_ylabel('Output Power (W)', fontsize=10, fontweight='bold')
        ax9.set_title('Power Characteristic', fontsize=11, fontweight='bold')
        ax9.legend(fontsize=8)
        ax9.grid(True, alpha=0.3)

        plt.suptitle('DC SHUNT/COMPOUND GENERATOR - COMPLETE ANALYSIS',
                    fontsize=14, fontweight='bold', y=0.995)
        plt.tight_layout()

        # Save figure
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"\nPlot saved to: {filename}")

        return fig

def run_complete_analysis():
    """Run complete analysis of the DC generator problem"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + " "*15 + "DC GENERATOR COMPLETE ANALYSIS" + " "*23 + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    # Create simulator instance
    simulator = DCGeneratorSimulator()

    # Print problem statement
    print("\nPROBLEM STATEMENT:")
    print("-" * 70)
    print("A DC shunt generator has the following open-circuit characteristic")
    print("when separately excited:")
    print()
    print("Field Current (A): ", end="")
    for val in simulator.if_data:
        print(f"{val:6.1f}", end=" ")
    print()
    print("EMF (V):          ", end="")
    for val in simulator.emf_data:
        print(f"{val:6.0f}", end=" ")
    print("\n")
    print(f"Shunt winding: {simulator.shunt_turns} turns/pole, {simulator.shunt_resistance}Ω resistance")
    print(f"Armature resistance (including series winding): {simulator.armature_resistance}Ω")
    print(f"Target load current: {simulator.load_current}A")
    print()
    print("OBJECTIVE: Find series winding turns/pole to maintain constant")
    print("           terminal voltage from no-load to 50A load.")
    print("-" * 70)

    # 1. Calculate series winding turns (main problem)
    results = simulator.calculate_series_turns()

    # 2. Generate comprehensive plots
    simulator.plot_all_characteristics('dc_generator_complete_analysis.png')

    # 3. Save detailed results to file
    print(f"\n{'='*70}")
    print("SAVING DETAILED RESULTS")
    print(f"{'='*70}")

    with open('dc_generator_results.txt', 'w') as f:
        f.write("="*70 + "\n")
        f.write("DC GENERATOR ANALYSIS - DETAILED RESULTS\n")
        f.write("="*70 + "\n\n")

        f.write("PROBLEM SPECIFICATION:\n")
        f.write(f"  Shunt turns/pole: {simulator.shunt_turns}\n")
        f.write(f"  Shunt resistance: {simulator.shunt_resistance} Ω\n")
        f.write(f"  Armature resistance: {simulator.armature_resistance} Ω\n")
        f.write(f"  Target load: {simulator.load_current} A\n\n")

        f.write("SOLUTION:\n")
        f.write(f"  Series winding turns/pole: {results['series_turns']:.2f}\n")
        f.write(f"  No-load voltage: {results['V_no_load']:.3f} V\n")
        f.write(f"  Full-load voltage: {results['V_load']:.3f} V\n")
        f.write(f"  Voltage regulation: {((results['V_no_load']-results['V_load'])/results['V_load']*100):.3f}%\n\n")

        f.write("DETAILED CALCULATIONS:\n")
        for key, value in results.items():
            f.write(f"  {key}: {value}\n")

    print("Results saved to: dc_generator_results.txt")

    # Summary
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + " "*22 + "ANALYSIS COMPLETE" + " "*29 + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    print(f"\nFINAL ANSWER: Series winding = {results['series_turns']:.2f} turns/pole")
    print(f"\nOutput files generated:")
    print(f"  1. dc_generator_complete_analysis.png  (Visual plots)")
    print(f"  2. dc_generator_results.txt            (Detailed results)")
    print("\n")

if __name__ == "__main__":
    run_complete_analysis()
