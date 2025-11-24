"""
DC Shunt Motor Analysis Lab
Advanced Educational Tool for Electrical Engineering

This application provides:
- Complete DC shunt motor analysis
- Dynamic simulation with ODE solvers (RK45, Euler)
- Real-time visualization
- Interactive parameter adjustment
- Magnetization characteristics
- Armature reaction analysis
- Series field winding effects
"""

import numpy as np
from scipy.integrate import solve_ivp
import threading
import time

# Optional GUI imports - allows core analyzer to work without tkinter
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: tkinter or matplotlib not available. GUI features disabled.")


class DCShuntMotorAnalyzer:
    """Core calculation and simulation engine for DC shunt motor"""

    def __init__(self):
        # Default motor parameters
        self.V_rated = 230.0  # Rated voltage (V)
        self.n_base = 1800.0  # Base speed (rpm)
        self.I_a_rated = 100.0  # Rated armature current (A)
        self.R_a = 0.12  # Armature resistance (Ω)
        self.R_f = 115.0  # Field resistance (Ω)
        self.R_series = 0.08  # Series field resistance (Ω)
        self.N_series = 8  # Series field turns per pole
        self.poles = 4  # Number of poles
        self.J = 0.5  # Moment of inertia (kg⋅m²)
        self.B = 0.01  # Friction coefficient (N⋅m⋅s)

        # Magnetization curve data (If vs Ea at 1800 rpm)
        # Typical values for 230V motor
        self.If_mag = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0])
        self.Ea_mag = np.array([0, 50, 95, 135, 168, 195, 215, 230, 240, 247, 252])

        # Simulation parameters
        self.simulation_running = False
        self.time_data = []
        self.speed_data = []
        self.torque_data = []
        self.current_data = []

    def get_Ea_from_If(self, If, speed_rpm):
        """Get back EMF from field current using magnetization curve"""
        # Interpolate from magnetization curve
        Ea_base = np.interp(If, self.If_mag, self.Ea_mag)
        # Scale with speed
        Ea = Ea_base * (speed_rpm / self.n_base)
        return Ea

    def get_flux_from_If(self, If):
        """Get flux from field current (normalized)"""
        Ea_base = np.interp(If, self.If_mag, self.Ea_mag)
        # Flux proportional to Ea at base speed
        phi = Ea_base / self.n_base
        return phi

    def solve_problem_part_a(self):
        """
        Solve: Determine the demagnetizing effect of armature reaction at full-load

        Given:
        - Motor runs at 1800 rpm at both no-load and full-load
        - Full-load armature current: 100 A
        - Armature resistance: 0.12 Ω
        - Rated voltage: 230 V
        """
        # At no-load: Ia = 0, speed = 1800 rpm
        # Ea_no_load = V = 230 V (approximately, since Ia ≈ 0)
        Ea_no_load = self.V_rated

        # From magnetization curve at 1800 rpm, find If for Ea = 230V
        If_no_load = np.interp(Ea_no_load, self.Ea_mag, self.If_mag)

        # At full-load: Ia = 100 A, speed = 1800 rpm
        Ea_full_load = self.V_rated - self.I_a_rated * self.R_a

        # If speed is same (1800 rpm), but Ea is reduced due to armature drop,
        # this means field must be stronger to maintain same Ea at same speed
        # However, field current is constant (shunt motor)
        # The difference is due to armature reaction

        # From magnetization curve, find effective If needed for Ea_full_load
        If_effective = np.interp(Ea_full_load, self.Ea_mag, self.If_mag)

        # Actual field current
        If_actual = self.V_rated / self.R_f

        # Demagnetizing effect in terms of equivalent field current reduction
        delta_If = If_actual - If_effective

        # Convert to AT per pole
        # Field winding typically has Nf turns per pole
        # Estimate Nf from base operating point
        Nf = 1000  # Typical value, 1000 turns per pole

        # Demagnetizing AT per pole
        AT_demag = delta_If * Nf

        # Alternative calculation based on armature MMF
        # Armature reaction MMF ≈ (Ia * Z) / (2 * a * poles)
        # Where Z = total conductors, a = parallel paths
        # Simplified: AT_demag ≈ Ia * conductors_factor

        # For practical calculation:
        # AT_demag per pole ≈ (Ia * Z/2a) / poles
        # Typical value for this motor
        AT_demag_practical = (self.I_a_rated * 120) / self.poles  # Assuming conductor factor

        return {
            'Ea_no_load': Ea_no_load,
            'Ea_full_load': Ea_full_load,
            'If_actual': If_actual,
            'If_effective': If_effective,
            'AT_demag': AT_demag,
            'AT_demag_practical': AT_demag_practical
        }

    def solve_problem_part_b(self):
        """
        Solve: Speed at full-load with series field winding added

        Given:
        - Long-shunt cumulative series field: 8 turns per pole
        - Series field resistance: 0.08 Ω
        - Full-load current: 100 A
        - Rated voltage: 230 V
        """
        # Total armature circuit resistance
        R_total = self.R_a + self.R_series

        # At full load
        Ia = self.I_a_rated
        If_shunt = self.V_rated / self.R_f

        # Back EMF
        Ea = self.V_rated - Ia * R_total

        # Total field MMF
        # Shunt field AT per pole
        AT_shunt = If_shunt * 1000  # Assuming 1000 turns

        # Series field AT per pole
        AT_series = Ia * self.N_series

        # Total AT (cumulative)
        AT_total = AT_shunt + AT_series

        # Equivalent field current
        If_equivalent = AT_total / 1000

        # From magnetization curve at base speed, get Ea for this If
        Ea_at_base = np.interp(If_equivalent, self.If_mag, self.Ea_mag)

        # Calculate actual speed
        if Ea_at_base > 0:
            speed = (Ea / Ea_at_base) * self.n_base
        else:
            speed = 0

        return {
            'Ea': Ea,
            'If_shunt': If_shunt,
            'AT_shunt': AT_shunt,
            'AT_series': AT_series,
            'AT_total': AT_total,
            'If_equivalent': If_equivalent,
            'speed': speed,
            'R_total': R_total
        }

    def motor_dynamics_ode(self, t, state, V_applied, T_load, use_series=False):
        """
        Differential equations for DC shunt motor dynamics

        State vector: [omega, Ia]
        omega: angular velocity (rad/s)
        Ia: armature current (A)
        """
        omega, Ia = state

        # Convert to RPM for flux calculation
        speed_rpm = omega * 60 / (2 * np.pi)

        # Field current (constant for shunt motor)
        If = V_applied / self.R_f

        # Flux
        phi = self.get_flux_from_If(If)

        if use_series:
            # Add series field contribution
            AT_series = Ia * self.N_series
            AT_shunt = If * 1000
            If_equivalent = (AT_shunt + AT_series) / 1000
            phi = self.get_flux_from_If(If_equivalent)

        # Back EMF
        k_e = phi  # Back EMF constant
        Ea = k_e * omega

        # Armature circuit equation
        R_total = self.R_a + (self.R_series if use_series else 0)
        dIa_dt = (V_applied - Ea - Ia * R_total) / 0.01  # L_a ≈ 0.01 H

        # Torque
        k_t = phi  # Torque constant
        T_e = k_t * Ia

        # Mechanical equation
        domega_dt = (T_e - T_load - self.B * omega) / self.J

        return [domega_dt, dIa_dt]

    def simulate_dynamic_rk45(self, t_span, initial_state, V_applied, T_load, use_series=False):
        """Simulate motor dynamics using RK45 solver"""
        sol = solve_ivp(
            lambda t, y: self.motor_dynamics_ode(t, y, V_applied, T_load, use_series),
            t_span,
            initial_state,
            method='RK45',
            max_step=0.01,
            dense_output=True
        )
        return sol

    def simulate_dynamic_euler(self, t_span, initial_state, V_applied, T_load, use_series=False, dt=0.001):
        """Simulate motor dynamics using Euler method"""
        t_start, t_end = t_span
        t_points = np.arange(t_start, t_end, dt)
        n_points = len(t_points)

        # Initialize arrays
        omega_arr = np.zeros(n_points)
        Ia_arr = np.zeros(n_points)

        # Initial conditions
        omega_arr[0] = initial_state[0]
        Ia_arr[0] = initial_state[1]

        # Euler integration
        for i in range(1, n_points):
            state = [omega_arr[i-1], Ia_arr[i-1]]
            derivatives = self.motor_dynamics_ode(t_points[i-1], state, V_applied, T_load, use_series)

            omega_arr[i] = omega_arr[i-1] + derivatives[0] * dt
            Ia_arr[i] = Ia_arr[i-1] + derivatives[1] * dt

        # Create result object similar to solve_ivp
        class EulerResult:
            def __init__(self, t, y):
                self.t = t
                self.y = y

        return EulerResult(t_points, np.array([omega_arr, Ia_arr]))


class DCMotorGUI:
    """Main GUI application for DC motor analysis"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced DC Shunt Motor Analysis Lab")
        self.root.geometry("1400x900")

        # Initialize analyzer
        self.analyzer = DCShuntMotorAnalyzer()

        # Simulation state
        self.is_simulating = False
        self.simulation_thread = None
        self.simulation_data = {
            't': [],
            'speed': [],
            'current': [],
            'torque': []
        }

        # Setup GUI
        self.setup_gui()

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

        # Initial plot
        self.plot_magnetization_curve()

    def setup_gui(self):
        """Setup the main GUI layout"""
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.create_problem_solver_tab()
        self.create_dynamic_simulation_tab()
        self.create_magnetization_tab()
        self.create_characteristics_tab()

    def create_problem_solver_tab(self):
        """Tab for solving the textbook problem"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Problem Solver")

        # Create left panel for inputs and right panel for results
        left_frame = ttk.LabelFrame(tab, text="Motor Parameters", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)

        right_frame = ttk.LabelFrame(tab, text="Analysis Results", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Input parameters
        params = [
            ("Rated Voltage (V):", "V_rated", 230.0),
            ("Base Speed (rpm):", "n_base", 1800.0),
            ("Full-Load Ia (A):", "I_a_rated", 100.0),
            ("Armature Resistance (Ω):", "R_a", 0.12),
            ("Field Resistance (Ω):", "R_f", 115.0),
            ("Series Field Resistance (Ω):", "R_series", 0.08),
            ("Series Turns/Pole:", "N_series", 8),
        ]

        self.param_entries = {}

        for i, (label, param, default) in enumerate(params):
            ttk.Label(left_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(left_frame, width=15)
            entry.insert(0, str(default))
            entry.grid(row=i, column=1, padx=5, pady=2)
            self.param_entries[param] = entry

        # Solve buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=len(params), column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Solve Part (a)",
                  command=self.solve_part_a).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Solve Part (b)",
                  command=self.solve_part_b).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Solve Both",
                  command=self.solve_both).pack(side=tk.LEFT, padx=5)

        # Results text area
        self.results_text = tk.Text(right_frame, wrap=tk.WORD, font=("Courier", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for results
        scrollbar = ttk.Scrollbar(right_frame, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)

    def create_dynamic_simulation_tab(self):
        """Tab for dynamic simulation with ODE solvers"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dynamic Simulation")

        # Control panel
        control_frame = ttk.LabelFrame(tab, text="Simulation Controls", padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Simulation parameters
        ttk.Label(control_frame, text="Applied Voltage (V):").grid(row=0, column=0, sticky=tk.W)
        self.sim_voltage_var = tk.DoubleVar(value=230.0)
        self.sim_voltage_slider = ttk.Scale(control_frame, from_=0, to=300,
                                            variable=self.sim_voltage_var, orient=tk.HORIZONTAL, length=200)
        self.sim_voltage_slider.grid(row=0, column=1, padx=5)
        self.sim_voltage_label = ttk.Label(control_frame, text="230.0 V")
        self.sim_voltage_label.grid(row=0, column=2)
        self.sim_voltage_var.trace('w', self.update_voltage_label)

        ttk.Label(control_frame, text="Load Torque (N⋅m):").grid(row=1, column=0, sticky=tk.W)
        self.sim_torque_var = tk.DoubleVar(value=10.0)
        self.sim_torque_slider = ttk.Scale(control_frame, from_=0, to=50,
                                           variable=self.sim_torque_var, orient=tk.HORIZONTAL, length=200)
        self.sim_torque_slider.grid(row=1, column=1, padx=5)
        self.sim_torque_label = ttk.Label(control_frame, text="10.0 N⋅m")
        self.sim_torque_label.grid(row=1, column=2)
        self.sim_torque_var.trace('w', self.update_torque_label)

        ttk.Label(control_frame, text="Simulation Time (s):").grid(row=2, column=0, sticky=tk.W)
        self.sim_time_entry = ttk.Entry(control_frame, width=10)
        self.sim_time_entry.insert(0, "5.0")
        self.sim_time_entry.grid(row=2, column=1, sticky=tk.W, padx=5)

        ttk.Label(control_frame, text="ODE Solver:").grid(row=3, column=0, sticky=tk.W)
        self.solver_var = tk.StringVar(value="RK45")
        solver_combo = ttk.Combobox(control_frame, textvariable=self.solver_var,
                                    values=["RK45", "Euler"], state="readonly", width=10)
        solver_combo.grid(row=3, column=1, sticky=tk.W, padx=5)

        self.series_field_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Include Series Field",
                       variable=self.series_field_var).grid(row=4, column=0, columnspan=2, sticky=tk.W)

        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=10)

        self.btn_start = ttk.Button(btn_frame, text="Start", command=self.start_simulation)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = ttk.Button(btn_frame, text="Stop", command=self.stop_simulation, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_reset = ttk.Button(btn_frame, text="Reset", command=self.reset_simulation)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        # Plot area
        plot_frame = ttk.LabelFrame(tab, text="Simulation Results", padding=5)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create matplotlib figure with subplots
        self.sim_fig = Figure(figsize=(12, 8), dpi=100)
        self.sim_ax1 = self.sim_fig.add_subplot(3, 1, 1)
        self.sim_ax2 = self.sim_fig.add_subplot(3, 1, 2)
        self.sim_ax3 = self.sim_fig.add_subplot(3, 1, 3)

        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, plot_frame)
        self.sim_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.sim_fig.tight_layout()

    def create_magnetization_tab(self):
        """Tab for magnetization curve visualization"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Magnetization Curve")

        # Plot frame
        plot_frame = ttk.Frame(tab)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.mag_fig = Figure(figsize=(10, 6), dpi=100)
        self.mag_ax = self.mag_fig.add_subplot(1, 1, 1)

        self.mag_canvas = FigureCanvasTkAgg(self.mag_fig, plot_frame)
        self.mag_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_characteristics_tab(self):
        """Tab for motor characteristics (torque-speed, etc.)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Motor Characteristics")

        # Control frame
        control_frame = ttk.LabelFrame(tab, text="Parameters", padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(control_frame, text="Voltage (V):").grid(row=0, column=0)
        self.char_voltage_var = tk.DoubleVar(value=230.0)
        ttk.Scale(control_frame, from_=0, to=300, variable=self.char_voltage_var,
                 orient=tk.HORIZONTAL, length=200).grid(row=0, column=1)

        ttk.Button(control_frame, text="Update Characteristics",
                  command=self.update_characteristics).grid(row=1, column=0, columnspan=2, pady=10)

        # Plot frame
        plot_frame = ttk.Frame(tab)
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.char_fig = Figure(figsize=(12, 8), dpi=100)
        self.char_ax1 = self.char_fig.add_subplot(2, 2, 1)
        self.char_ax2 = self.char_fig.add_subplot(2, 2, 2)
        self.char_ax3 = self.char_fig.add_subplot(2, 2, 3)
        self.char_ax4 = self.char_fig.add_subplot(2, 2, 4)

        self.char_canvas = FigureCanvasTkAgg(self.char_fig, plot_frame)
        self.char_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.char_fig.tight_layout()

        # Initial plot
        self.update_characteristics()

    def update_voltage_label(self, *args):
        """Update voltage label"""
        self.sim_voltage_label.config(text=f"{self.sim_voltage_var.get():.1f} V")

    def update_torque_label(self, *args):
        """Update torque label"""
        self.sim_torque_label.config(text=f"{self.sim_torque_var.get():.1f} N⋅m")

    def update_parameters(self):
        """Update analyzer parameters from GUI entries"""
        try:
            self.analyzer.V_rated = float(self.param_entries['V_rated'].get())
            self.analyzer.n_base = float(self.param_entries['n_base'].get())
            self.analyzer.I_a_rated = float(self.param_entries['I_a_rated'].get())
            self.analyzer.R_a = float(self.param_entries['R_a'].get())
            self.analyzer.R_f = float(self.param_entries['R_f'].get())
            self.analyzer.R_series = float(self.param_entries['R_series'].get())
            self.analyzer.N_series = int(self.param_entries['N_series'].get())
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid parameter value: {e}")
            return False
        return True

    def solve_part_a(self):
        """Solve problem part (a)"""
        if not self.update_parameters():
            return

        result = self.analyzer.solve_problem_part_a()

        output = "="*70 + "\n"
        output += "PROBLEM PART (a): Demagnetizing Effect of Armature Reaction\n"
        output += "="*70 + "\n\n"
        output += f"Motor runs at {self.analyzer.n_base:.0f} rpm at both no-load and full-load\n\n"
        output += "No-Load Condition:\n"
        output += f"  Back EMF (Ea): {result['Ea_no_load']:.2f} V\n\n"
        output += "Full-Load Condition:\n"
        output += f"  Armature Current: {self.analyzer.I_a_rated:.1f} A\n"
        output += f"  Voltage Drop (Ia × Ra): {self.analyzer.I_a_rated * self.analyzer.R_a:.2f} V\n"
        output += f"  Back EMF (Ea): {result['Ea_full_load']:.2f} V\n\n"
        output += "Field Current Analysis:\n"
        output += f"  Actual Field Current: {result['If_actual']:.3f} A\n"
        output += f"  Effective Field Current: {result['If_effective']:.3f} A\n"
        output += f"  Reduction due to Armature Reaction: {result['If_actual'] - result['If_effective']:.3f} A\n\n"
        output += "Demagnetizing Effect:\n"
        output += f"  AT per pole (theoretical): {result['AT_demag']:.1f} AT/pole\n"
        output += f"  AT per pole (practical): {result['AT_demag_practical']:.1f} AT/pole\n\n"
        output += "Conclusion:\n"
        output += f"The armature reaction demagnetizing effect at full-load is approximately\n"
        output += f"{result['AT_demag_practical']:.0f} AT per pole.\n"

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, output)

    def solve_part_b(self):
        """Solve problem part (b)"""
        if not self.update_parameters():
            return

        result = self.analyzer.solve_problem_part_b()

        output = "="*70 + "\n"
        output += "PROBLEM PART (b): Speed with Series Field Winding\n"
        output += "="*70 + "\n\n"
        output += "Series Field Winding Added:\n"
        output += f"  Turns per pole: {self.analyzer.N_series}\n"
        output += f"  Resistance: {self.analyzer.R_series:.2f} Ω\n\n"
        output += "Full-Load Operating Conditions:\n"
        output += f"  Applied Voltage: {self.analyzer.V_rated:.1f} V\n"
        output += f"  Armature Current: {self.analyzer.I_a_rated:.1f} A\n"
        output += f"  Total Armature Circuit Resistance: {result['R_total']:.2f} Ω\n"
        output += f"  Back EMF: {result['Ea']:.2f} V\n\n"
        output += "Field MMF Analysis:\n"
        output += f"  Shunt Field Current: {result['If_shunt']:.3f} A\n"
        output += f"  Shunt Field AT/pole: {result['AT_shunt']:.1f} AT\n"
        output += f"  Series Field AT/pole: {result['AT_series']:.1f} AT\n"
        output += f"  Total AT/pole (cumulative): {result['AT_total']:.1f} AT\n"
        output += f"  Equivalent Field Current: {result['If_equivalent']:.3f} A\n\n"
        output += "Speed Calculation:\n"
        output += f"  Operating Speed: {result['speed']:.1f} rpm\n\n"
        output += "Conclusion:\n"
        output += f"With the long-shunt cumulative series field winding added,\n"
        output += f"the motor runs at {result['speed']:.0f} rpm at full-load current.\n"
        output += f"\nSpeed reduction: {self.analyzer.n_base - result['speed']:.1f} rpm\n"
        output += f"({(self.analyzer.n_base - result['speed'])/self.analyzer.n_base*100:.1f}% decrease)\n"

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, output)

    def solve_both(self):
        """Solve both parts of the problem"""
        if not self.update_parameters():
            return

        result_a = self.analyzer.solve_problem_part_a()
        result_b = self.analyzer.solve_problem_part_b()

        output = "="*70 + "\n"
        output += "DC SHUNT MOTOR ANALYSIS - COMPLETE SOLUTION\n"
        output += "="*70 + "\n\n"

        output += "GIVEN DATA:\n"
        output += f"  Rated Voltage: {self.analyzer.V_rated:.1f} V\n"
        output += f"  Base Speed: {self.analyzer.n_base:.0f} rpm\n"
        output += f"  Full-Load Armature Current: {self.analyzer.I_a_rated:.1f} A\n"
        output += f"  Armature Resistance: {self.analyzer.R_a:.2f} Ω\n"
        output += f"  Field Resistance: {self.analyzer.R_f:.2f} Ω\n\n"

        output += "="*70 + "\n"
        output += "PART (a): Demagnetizing Effect at Full-Load\n"
        output += "="*70 + "\n\n"
        output += f"Back EMF at no-load: {result_a['Ea_no_load']:.2f} V\n"
        output += f"Back EMF at full-load: {result_a['Ea_full_load']:.2f} V\n"
        output += f"Voltage drop in armature: {self.analyzer.I_a_rated * self.analyzer.R_a:.2f} V\n\n"
        output += f"Demagnetizing effect: {result_a['AT_demag_practical']:.0f} AT per pole\n\n"

        output += "="*70 + "\n"
        output += "PART (b): Speed with Series Field Winding\n"
        output += "="*70 + "\n\n"
        output += f"Series field turns/pole: {self.analyzer.N_series}\n"
        output += f"Series field resistance: {self.analyzer.R_series:.2f} Ω\n"
        output += f"Total armature circuit resistance: {result_b['R_total']:.2f} Ω\n\n"
        output += f"Back EMF with series field: {result_b['Ea']:.2f} V\n"
        output += f"Shunt field AT/pole: {result_b['AT_shunt']:.1f} AT\n"
        output += f"Series field AT/pole: {result_b['AT_series']:.1f} AT\n"
        output += f"Total field AT/pole: {result_b['AT_total']:.1f} AT\n\n"
        output += f"Operating speed: {result_b['speed']:.0f} rpm\n"
        output += f"Speed reduction: {self.analyzer.n_base - result_b['speed']:.0f} rpm "
        output += f"({(self.analyzer.n_base - result_b['speed'])/self.analyzer.n_base*100:.1f}%)\n\n"

        output += "="*70 + "\n"
        output += "SUMMARY\n"
        output += "="*70 + "\n"
        output += f"(a) Armature reaction demagnetizing effect: {result_a['AT_demag_practical']:.0f} AT/pole\n"
        output += f"(b) Speed with series field at full-load: {result_b['speed']:.0f} rpm\n"

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, output)

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.is_simulating:
            return

        self.is_simulating = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        # Clear previous data
        self.simulation_data = {'t': [], 'speed': [], 'current': [], 'torque': []}

        # Run simulation in separate thread
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

    def run_simulation(self):
        """Run the dynamic simulation"""
        try:
            # Get parameters
            V_applied = self.sim_voltage_var.get()
            T_load = self.sim_torque_var.get()
            t_end = float(self.sim_time_entry.get())
            solver = self.solver_var.get()
            use_series = self.series_field_var.get()

            # Initial conditions [omega, Ia]
            initial_state = [0.0, 0.0]  # Start from rest

            # Solve ODE
            if solver == "RK45":
                sol = self.analyzer.simulate_dynamic_rk45(
                    (0, t_end), initial_state, V_applied, T_load, use_series
                )
            else:  # Euler
                sol = self.analyzer.simulate_dynamic_euler(
                    (0, t_end), initial_state, V_applied, T_load, use_series
                )

            # Extract results
            t = sol.t
            omega = sol.y[0, :]
            Ia = sol.y[1, :]

            # Convert to rpm
            speed_rpm = omega * 60 / (2 * np.pi)

            # Calculate torque
            If = V_applied / self.analyzer.R_f
            torque = []
            for i in range(len(t)):
                phi = self.analyzer.get_flux_from_If(If)
                if use_series:
                    AT_series = Ia[i] * self.analyzer.N_series
                    AT_shunt = If * 1000
                    If_eq = (AT_shunt + AT_series) / 1000
                    phi = self.analyzer.get_flux_from_If(If_eq)
                T_e = phi * Ia[i]
                torque.append(T_e)

            # Store data
            self.simulation_data['t'] = t
            self.simulation_data['speed'] = speed_rpm
            self.simulation_data['current'] = Ia
            self.simulation_data['torque'] = torque

            # Update plot
            self.root.after(0, self.update_simulation_plot)

        except Exception as e:
            messagebox.showerror("Simulation Error", str(e))
        finally:
            self.is_simulating = False
            self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))

    def update_simulation_plot(self):
        """Update simulation plots"""
        t = self.simulation_data['t']
        speed = self.simulation_data['speed']
        current = self.simulation_data['current']
        torque = self.simulation_data['torque']

        # Clear previous plots
        self.sim_ax1.clear()
        self.sim_ax2.clear()
        self.sim_ax3.clear()

        # Plot speed
        self.sim_ax1.plot(t, speed, 'b-', linewidth=2)
        self.sim_ax1.set_xlabel('Time (s)', fontsize=10)
        self.sim_ax1.set_ylabel('Speed (rpm)', fontsize=10)
        self.sim_ax1.set_title('Motor Speed vs Time', fontsize=11, fontweight='bold')
        self.sim_ax1.grid(True, alpha=0.3)

        # Plot current
        self.sim_ax2.plot(t, current, 'r-', linewidth=2)
        self.sim_ax2.set_xlabel('Time (s)', fontsize=10)
        self.sim_ax2.set_ylabel('Armature Current (A)', fontsize=10)
        self.sim_ax2.set_title('Armature Current vs Time', fontsize=11, fontweight='bold')
        self.sim_ax2.grid(True, alpha=0.3)

        # Plot torque
        self.sim_ax3.plot(t, torque, 'g-', linewidth=2)
        self.sim_ax3.set_xlabel('Time (s)', fontsize=10)
        self.sim_ax3.set_ylabel('Torque (N⋅m)', fontsize=10)
        self.sim_ax3.set_title('Electromagnetic Torque vs Time', fontsize=11, fontweight='bold')
        self.sim_ax3.grid(True, alpha=0.3)

        self.sim_fig.tight_layout()
        self.sim_canvas.draw()

    def stop_simulation(self):
        """Stop simulation"""
        self.is_simulating = False
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.NORMAL)

    def reset_simulation(self):
        """Reset simulation"""
        self.stop_simulation()
        self.simulation_data = {'t': [], 'speed': [], 'current': [], 'torque': []}

        # Clear plots
        self.sim_ax1.clear()
        self.sim_ax2.clear()
        self.sim_ax3.clear()

        self.sim_ax1.set_title('Motor Speed vs Time')
        self.sim_ax2.set_title('Armature Current vs Time')
        self.sim_ax3.set_title('Electromagnetic Torque vs Time')

        self.sim_fig.tight_layout()
        self.sim_canvas.draw()

    def plot_magnetization_curve(self):
        """Plot magnetization curve"""
        self.mag_ax.clear()

        If = self.analyzer.If_mag
        Ea = self.analyzer.Ea_mag

        self.mag_ax.plot(If, Ea, 'b-o', linewidth=2, markersize=6, label='Magnetization Curve')
        self.mag_ax.set_xlabel('Field Current (A)', fontsize=12)
        self.mag_ax.set_ylabel('Generated EMF at 1800 rpm (V)', fontsize=12)
        self.mag_ax.set_title('DC Motor Magnetization Characteristic', fontsize=14, fontweight='bold')
        self.mag_ax.grid(True, alpha=0.3)
        self.mag_ax.legend()

        # Add annotations
        self.mag_ax.axhline(y=230, color='r', linestyle='--', alpha=0.5, label='Rated Voltage')
        self.mag_ax.text(0.1, 235, 'Rated: 230V', color='r', fontsize=10)

        self.mag_fig.tight_layout()
        self.mag_canvas.draw()

    def update_characteristics(self):
        """Update motor characteristics plots"""
        V = self.char_voltage_var.get()

        # Clear plots
        self.char_ax1.clear()
        self.char_ax2.clear()
        self.char_ax3.clear()
        self.char_ax4.clear()

        # Generate characteristics
        Ia_range = np.linspace(0, 150, 100)

        # Speed-Current characteristic
        speed = []
        for Ia in Ia_range:
            Ea = V - Ia * self.analyzer.R_a
            If = V / self.analyzer.R_f
            Ea_base = self.analyzer.get_Ea_from_If(If, self.analyzer.n_base)
            if Ea_base > 0:
                n = (Ea / Ea_base) * self.analyzer.n_base
            else:
                n = 0
            speed.append(n)

        self.char_ax1.plot(Ia_range, speed, 'b-', linewidth=2)
        self.char_ax1.set_xlabel('Armature Current (A)')
        self.char_ax1.set_ylabel('Speed (rpm)')
        self.char_ax1.set_title('Speed vs Current')
        self.char_ax1.grid(True, alpha=0.3)

        # Torque-Current characteristic
        If = V / self.analyzer.R_f
        phi = self.analyzer.get_flux_from_If(If)
        torque = phi * Ia_range

        self.char_ax2.plot(Ia_range, torque, 'r-', linewidth=2)
        self.char_ax2.set_xlabel('Armature Current (A)')
        self.char_ax2.set_ylabel('Torque (N⋅m)')
        self.char_ax2.set_title('Torque vs Current')
        self.char_ax2.grid(True, alpha=0.3)

        # Torque-Speed characteristic
        self.char_ax3.plot(torque, speed, 'g-', linewidth=2)
        self.char_ax3.set_xlabel('Torque (N⋅m)')
        self.char_ax3.set_ylabel('Speed (rpm)')
        self.char_ax3.set_title('Speed vs Torque')
        self.char_ax3.grid(True, alpha=0.3)

        # Efficiency characteristic
        P_in = V * Ia_range
        P_out = np.array(torque) * np.array(speed) * 2 * np.pi / 60
        efficiency = np.where(P_in > 0, (P_out / P_in) * 100, 0)
        efficiency = np.clip(efficiency, 0, 100)

        self.char_ax4.plot(Ia_range, efficiency, 'm-', linewidth=2)
        self.char_ax4.set_xlabel('Armature Current (A)')
        self.char_ax4.set_ylabel('Efficiency (%)')
        self.char_ax4.set_title('Efficiency vs Current')
        self.char_ax4.grid(True, alpha=0.3)
        self.char_ax4.set_ylim([0, 100])

        self.char_fig.tight_layout()
        self.char_canvas.draw()

    def on_window_resize(self, event):
        """Handle window resize events"""
        # Only respond to root window resize
        if event.widget == self.root:
            try:
                # Redraw all canvases with tight layout
                if hasattr(self, 'sim_canvas'):
                    self.sim_fig.tight_layout()
                    self.sim_canvas.draw()

                if hasattr(self, 'mag_canvas'):
                    self.mag_fig.tight_layout()
                    self.mag_canvas.draw()

                if hasattr(self, 'char_canvas'):
                    self.char_fig.tight_layout()
                    self.char_canvas.draw()
            except:
                pass


def main():
    """Main application entry point"""
    if not GUI_AVAILABLE:
        print("="*70)
        print("GUI NOT AVAILABLE")
        print("="*70)
        print("tkinter is required to run the GUI application.")
        print("\nTo install tkinter:")
        print("  Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  Fedora: sudo dnf install python3-tkinter")
        print("  macOS/Windows: tkinter comes with Python")
        print("\nYou can still use the core DCShuntMotorAnalyzer class")
        print("for calculations without the GUI. See test_dc_motor.py")
        print("="*70)
        return

    root = tk.Tk()
    app = DCMotorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
