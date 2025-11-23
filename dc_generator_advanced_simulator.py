"""
Advanced DC Generator Simulator with Dynamic Analysis
Includes: ODE Solvers, Real-time Simulation, Comprehensive GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from scipy.interpolate import interp1d
from scipy.integrate import solve_ivp, odeint
import threading
import time

class DCGeneratorSimulator:
    """Advanced DC Generator Simulator with Mathematical Modeling"""

    def __init__(self):
        # Default OCC data (Open Circuit Characteristic)
        self.if_data = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.4, 2.0])
        self.emf_data = np.array([80, 135, 178, 198, 210, 228, 246])

        # Generator parameters
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

        # Simulation state
        self.simulation_running = False
        self.simulation_paused = False
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.speed_data = []

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
        for _ in range(max_iter):
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
        return if_guess

    def find_no_load_voltage(self):
        """Find no-load terminal voltage (self-excited condition)"""
        # At no-load: V = E and If = V/Rf
        # Need to find intersection point
        max_iter = 100
        V = 200  # Initial guess

        for _ in range(max_iter):
            If = V / self.shunt_resistance
            E = self.get_emf_from_field_current(If)
            error = abs(E - V)
            if error < 0.01:
                return V, If, E
            V = 0.5 * V + 0.5 * E  # Relaxation

        return V, If, E

    def calculate_series_turns(self):
        """Calculate required series winding turns per pole"""
        # Step 1: Find no-load voltage
        V_no_load, If_no_load, E_no_load = self.find_no_load_voltage()

        # Step 2: At 50A load, terminal voltage should equal no-load voltage
        # V_load = E_load - Ia * Ra
        # V_load = V_no_load (requirement)
        # E_load = V_no_load + Ia * Ra

        Ia = self.load_current
        V_load = V_no_load
        E_load_required = V_load + Ia * self.armature_resistance

        # Step 3: Find total field current needed for E_load
        If_total_required = self.get_field_current_from_emf(E_load_required)

        # Step 4: Shunt field current at load
        If_shunt = V_load / self.shunt_resistance

        # Step 5: Additional field current from series winding
        # Series winding carries load current (Ia)
        # MMF_series = Ns * Ia
        # MMF_shunt = Nf * If_shunt
        # Total MMF equivalent = Nf * If_total
        # Therefore: Nf * If_total = Nf * If_shunt + Ns * Ia
        # Ns = Nf * (If_total - If_shunt) / Ia

        Ns = self.shunt_turns * (If_total_required - If_shunt) / Ia

        results = {
            'V_no_load': V_no_load,
            'If_no_load': If_no_load,
            'E_no_load': E_no_load,
            'E_load_required': E_load_required,
            'If_total_required': If_total_required,
            'If_shunt_at_load': If_shunt,
            'series_turns': Ns,
            'V_load': V_load,
            'Ia': Ia
        }

        self.series_turns = Ns
        return results

    def generator_ode_system(self, t, y, V_load, omega_m):
        """
        ODE system for DC generator dynamics
        State vector y = [Ia, If]
        Ia: Armature current
        If: Field current
        """
        Ia, If = y

        # EMF generated
        E = self.get_emf_from_field_current(If)

        # Equations:
        # La * dIa/dt = E - Ia*Ra - V_load
        # Lf * dIf/dt = V_load - If*Rf

        dIa_dt = (E - Ia * self.armature_resistance - V_load) / self.La
        dIf_dt = (V_load - If * self.shunt_resistance) / self.Lf

        return [dIa_dt, dIf_dt]

    def simulate_load_step_response(self, t_span=(0, 2), V_load=200, method='RK45'):
        """
        Simulate generator response to load change
        """
        # Initial conditions
        V_init, If_init, _ = self.find_no_load_voltage()
        y0 = [0.1, If_init]  # [Ia, If]

        # Fixed speed assumption
        omega_m = self.omega_rated

        # Solve ODE
        if method == 'RK45':
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
        else:  # Euler
            dt = 0.001
            t_eval = np.arange(t_span[0], t_span[1], dt)
            Ia_result = [y0[0]]
            If_result = [y0[1]]

            for i in range(1, len(t_eval)):
                y_current = [Ia_result[-1], If_result[-1]]
                dydt = self.generator_ode_system(t_eval[i], y_current, V_load, omega_m)
                Ia_result.append(y_current[0] + dydt[0] * dt)
                If_result.append(y_current[1] + dydt[1] * dt)

            Ia_result = np.array(Ia_result)
            If_result = np.array(If_result)

        # Calculate EMF and terminal voltage
        E_result = np.array([self.get_emf_from_field_current(If) for If in If_result])
        V_terminal = E_result - Ia_result * self.armature_resistance

        return {
            't': t_eval,
            'Ia': Ia_result,
            'If': If_result,
            'E': E_result,
            'V_terminal': V_terminal
        }

    def calculate_performance_curves(self, load_range=None):
        """Calculate generator performance characteristics"""
        if load_range is None:
            load_range = np.linspace(0, 100, 50)

        V_no_load, _, _ = self.find_no_load_voltage()

        V_terminal = []
        E_generated = []
        If_total = []
        efficiency = []

        for Ia in load_range:
            # For compound generator with series winding
            # Estimate terminal voltage iteratively
            V_t = V_no_load  # Initial guess

            for _ in range(50):
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

            # Efficiency calculation
            P_out = V_t * Ia
            P_losses = Ia**2 * self.armature_resistance + V_t**2 / self.shunt_resistance
            P_in = P_out + P_losses
            eff = (P_out / P_in * 100) if P_in > 0 else 0
            efficiency.append(eff)

        return {
            'Ia': load_range,
            'V_terminal': np.array(V_terminal),
            'E': np.array(E_generated),
            'If': np.array(If_total),
            'efficiency': np.array(efficiency)
        }


class DCGeneratorGUI:
    """Advanced Tkinter GUI for DC Generator Simulator"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced DC Generator Simulator - Electrical Engineering Tool")
        self.root.geometry("1400x900")

        # Initialize simulator
        self.simulator = DCGeneratorSimulator()

        # Simulation control
        self.sim_running = False
        self.sim_thread = None

        # Configure grid weights for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=3)

        # Create menu bar
        self.create_menu_bar()

        # Create left panel (controls)
        self.create_left_panel()

        # Create right panel (visualization)
        self.create_right_panel()

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

        # Initialize plots
        self.update_all_plots()

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Results", command=self.save_results)
        file_menu.add_command(label="Load Configuration", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Calculate Series Turns", command=self.solve_series_turns)
        analysis_menu.add_command(label="Performance Curves", command=self.plot_performance_curves)
        analysis_menu.add_command(label="Dynamic Simulation", command=self.run_dynamic_simulation)
        analysis_menu.add_command(label="OCC Analysis", command=self.analyze_occ)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)

    def create_left_panel(self):
        """Create left control panel"""
        left_panel = ttk.Frame(self.main_container, padding="10")
        left_panel.grid(row=0, column=0, sticky="nsew")

        # Create notebook for organized tabs
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill='both', expand=True)

        # Tab 1: Parameters
        self.create_parameters_tab()

        # Tab 2: OCC Data
        self.create_occ_tab()

        # Tab 3: Simulation Control
        self.create_simulation_tab()

        # Tab 4: Results
        self.create_results_tab()

    def create_parameters_tab(self):
        """Create parameters input tab"""
        param_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(param_frame, text="Parameters")

        # Scrollable frame
        canvas = tk.Canvas(param_frame)
        scrollbar = ttk.Scrollbar(param_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        row = 0

        # Generator Parameters Section
        ttk.Label(scrollable_frame, text="Generator Parameters",
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # Shunt turns
        ttk.Label(scrollable_frame, text="Shunt Turns/Pole:").grid(row=row, column=0, sticky='w', pady=2)
        self.shunt_turns_var = tk.StringVar(value=str(self.simulator.shunt_turns))
        ttk.Entry(scrollable_frame, textvariable=self.shunt_turns_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        # Shunt resistance
        ttk.Label(scrollable_frame, text="Shunt Resistance (Ω):").grid(row=row, column=0, sticky='w', pady=2)
        self.shunt_resistance_var = tk.StringVar(value=str(self.simulator.shunt_resistance))
        ttk.Entry(scrollable_frame, textvariable=self.shunt_resistance_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        # Armature resistance
        ttk.Label(scrollable_frame, text="Armature Resistance (Ω):").grid(row=row, column=0, sticky='w', pady=2)
        self.armature_resistance_var = tk.StringVar(value=str(self.simulator.armature_resistance))
        ttk.Entry(scrollable_frame, textvariable=self.armature_resistance_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        # Load current
        ttk.Label(scrollable_frame, text="Load Current (A):").grid(row=row, column=0, sticky='w', pady=2)
        self.load_current_var = tk.StringVar(value=str(self.simulator.load_current))
        ttk.Entry(scrollable_frame, textvariable=self.load_current_var, width=15).grid(row=row, column=1, pady=2)
        row += 1

        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1

        # Dynamic Parameters Section
        ttk.Label(scrollable_frame, text="Dynamic Parameters",
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1

        # Armature inductance
        ttk.Label(scrollable_frame, text="Armature Inductance (H):").grid(row=row, column=0, sticky='w', pady=2)
        self.La_var = tk.DoubleVar(value=self.simulator.La)
        ttk.Scale(scrollable_frame, from_=0.01, to=1.0, variable=self.La_var,
                 orient='horizontal', length=150, command=self.update_param_labels).grid(row=row, column=1, pady=2)
        self.La_label = ttk.Label(scrollable_frame, text=f"{self.simulator.La:.3f}")
        self.La_label.grid(row=row, column=2, padx=5)
        row += 1

        # Field inductance
        ttk.Label(scrollable_frame, text="Field Inductance (H):").grid(row=row, column=0, sticky='w', pady=2)
        self.Lf_var = tk.DoubleVar(value=self.simulator.Lf)
        ttk.Scale(scrollable_frame, from_=1.0, to=50.0, variable=self.Lf_var,
                 orient='horizontal', length=150, command=self.update_param_labels).grid(row=row, column=1, pady=2)
        self.Lf_label = ttk.Label(scrollable_frame, text=f"{self.simulator.Lf:.1f}")
        self.Lf_label.grid(row=row, column=2, padx=5)
        row += 1

        # Moment of inertia
        ttk.Label(scrollable_frame, text="Inertia J (kg·m²):").grid(row=row, column=0, sticky='w', pady=2)
        self.J_var = tk.DoubleVar(value=self.simulator.J)
        ttk.Scale(scrollable_frame, from_=0.1, to=5.0, variable=self.J_var,
                 orient='horizontal', length=150, command=self.update_param_labels).grid(row=row, column=1, pady=2)
        self.J_label = ttk.Label(scrollable_frame, text=f"{self.simulator.J:.2f}")
        self.J_label.grid(row=row, column=2, padx=5)
        row += 1

        # Speed
        ttk.Label(scrollable_frame, text="Speed (RPM):").grid(row=row, column=0, sticky='w', pady=2)
        self.speed_var = tk.DoubleVar(value=1500)
        ttk.Scale(scrollable_frame, from_=500, to=3000, variable=self.speed_var,
                 orient='horizontal', length=150, command=self.update_param_labels).grid(row=row, column=1, pady=2)
        self.speed_label = ttk.Label(scrollable_frame, text="1500")
        self.speed_label.grid(row=row, column=2, padx=5)
        row += 1

        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1

        # Update button
        ttk.Button(scrollable_frame, text="Update Parameters",
                  command=self.update_parameters).grid(row=row, column=0, columnspan=3, pady=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_occ_tab(self):
        """Create OCC data input tab"""
        occ_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(occ_frame, text="OCC Data")

        ttk.Label(occ_frame, text="Open Circuit Characteristic",
                 font=('Arial', 10, 'bold')).pack(pady=5)

        # Text widget for OCC data
        occ_text_frame = ttk.Frame(occ_frame)
        occ_text_frame.pack(fill='both', expand=True, pady=5)

        ttk.Label(occ_text_frame, text="Field Current (A):").grid(row=0, column=0, sticky='w')
        self.if_text = scrolledtext.ScrolledText(occ_text_frame, width=20, height=5)
        self.if_text.grid(row=1, column=0, padx=5, pady=5)
        self.if_text.insert('1.0', ', '.join(map(str, self.simulator.if_data)))

        ttk.Label(occ_text_frame, text="EMF (V):").grid(row=0, column=1, sticky='w')
        self.emf_text = scrolledtext.ScrolledText(occ_text_frame, width=20, height=5)
        self.emf_text.grid(row=1, column=1, padx=5, pady=5)
        self.emf_text.insert('1.0', ', '.join(map(str, self.simulator.emf_data)))

        ttk.Button(occ_frame, text="Update OCC Data",
                  command=self.update_occ_data).pack(pady=10)

    def create_simulation_tab(self):
        """Create simulation control tab"""
        sim_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(sim_frame, text="Simulation")

        ttk.Label(sim_frame, text="Dynamic Simulation Control",
                 font=('Arial', 10, 'bold')).pack(pady=5)

        # Simulation time
        time_frame = ttk.Frame(sim_frame)
        time_frame.pack(fill='x', pady=5)
        ttk.Label(time_frame, text="Simulation Time (s):").pack(side='left')
        self.sim_time_var = tk.StringVar(value="2.0")
        ttk.Entry(time_frame, textvariable=self.sim_time_var, width=10).pack(side='left', padx=5)

        # ODE Solver selection
        solver_frame = ttk.Frame(sim_frame)
        solver_frame.pack(fill='x', pady=5)
        ttk.Label(solver_frame, text="ODE Solver:").pack(side='left')
        self.solver_var = tk.StringVar(value="RK45")
        ttk.Radiobutton(solver_frame, text="RK45", variable=self.solver_var,
                       value="RK45").pack(side='left', padx=5)
        ttk.Radiobutton(solver_frame, text="Euler", variable=self.solver_var,
                       value="Euler").pack(side='left', padx=5)

        # Load voltage
        load_frame = ttk.Frame(sim_frame)
        load_frame.pack(fill='x', pady=5)
        ttk.Label(load_frame, text="Load Voltage (V):").pack(side='left')
        self.load_voltage_var = tk.StringVar(value="200")
        ttk.Entry(load_frame, textvariable=self.load_voltage_var, width=10).pack(side='left', padx=5)

        # Control buttons
        button_frame = ttk.Frame(sim_frame)
        button_frame.pack(pady=20)

        self.start_btn = ttk.Button(button_frame, text="▶ Start",
                                    command=self.start_simulation, width=12)
        self.start_btn.grid(row=0, column=0, padx=5, pady=5)

        self.stop_btn = ttk.Button(button_frame, text="⏸ Stop",
                                   command=self.stop_simulation, width=12, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5)

        self.reset_btn = ttk.Button(button_frame, text="↻ Reset",
                                    command=self.reset_simulation, width=12)
        self.reset_btn.grid(row=1, column=0, padx=5, pady=5)

        ttk.Button(button_frame, text="Calculate",
                  command=self.run_dynamic_simulation, width=12).grid(row=1, column=1, padx=5, pady=5)

        # Status
        ttk.Label(sim_frame, text="Status:").pack(pady=(20, 0))
        self.status_text = scrolledtext.ScrolledText(sim_frame, width=40, height=8)
        self.status_text.pack(fill='both', expand=True, pady=5)
        self.log_message("System ready.")

    def create_results_tab(self):
        """Create results display tab"""
        results_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(results_frame, text="Results")

        ttk.Label(results_frame, text="Calculation Results",
                 font=('Arial', 10, 'bold')).pack(pady=5)

        self.results_text = scrolledtext.ScrolledText(results_frame, width=40, height=25)
        self.results_text.pack(fill='both', expand=True, pady=5)

        ttk.Button(results_frame, text="Clear Results",
                  command=lambda: self.results_text.delete('1.0', 'end')).pack(pady=5)

    def create_right_panel(self):
        """Create right visualization panel"""
        right_panel = ttk.Frame(self.main_container, padding="5")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Create notebook for multiple plots
        self.plot_notebook = ttk.Notebook(right_panel)
        self.plot_notebook.grid(row=0, column=0, sticky="nsew")

        # Create multiple plot tabs
        self.create_occ_plot_tab()
        self.create_performance_plot_tab()
        self.create_dynamic_plot_tab()
        self.create_characteristics_plot_tab()

    def create_occ_plot_tab(self):
        """Create OCC plot tab"""
        occ_plot_frame = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(occ_plot_frame, text="OCC Curve")

        self.occ_fig = Figure(figsize=(8, 6), dpi=100)
        self.occ_ax = self.occ_fig.add_subplot(111)

        self.occ_canvas = FigureCanvasTkAgg(self.occ_fig, occ_plot_frame)
        self.occ_canvas.draw()
        self.occ_canvas.get_tk_widget().pack(fill='both', expand=True)

        toolbar = NavigationToolbar2Tk(self.occ_canvas, occ_plot_frame)
        toolbar.update()

    def create_performance_plot_tab(self):
        """Create performance curves plot tab"""
        perf_plot_frame = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(perf_plot_frame, text="Performance")

        self.perf_fig = Figure(figsize=(8, 6), dpi=100)
        self.perf_ax1 = self.perf_fig.add_subplot(211)
        self.perf_ax2 = self.perf_fig.add_subplot(212)

        self.perf_canvas = FigureCanvasTkAgg(self.perf_fig, perf_plot_frame)
        self.perf_canvas.draw()
        self.perf_canvas.get_tk_widget().pack(fill='both', expand=True)

        toolbar = NavigationToolbar2Tk(self.perf_canvas, perf_plot_frame)
        toolbar.update()

    def create_dynamic_plot_tab(self):
        """Create dynamic simulation plot tab"""
        dyn_plot_frame = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(dyn_plot_frame, text="Dynamic Response")

        self.dyn_fig = Figure(figsize=(8, 6), dpi=100)
        self.dyn_ax1 = self.dyn_fig.add_subplot(311)
        self.dyn_ax2 = self.dyn_fig.add_subplot(312)
        self.dyn_ax3 = self.dyn_fig.add_subplot(313)

        self.dyn_canvas = FigureCanvasTkAgg(self.dyn_fig, dyn_plot_frame)
        self.dyn_canvas.draw()
        self.dyn_canvas.get_tk_widget().pack(fill='both', expand=True)

        toolbar = NavigationToolbar2Tk(self.dyn_canvas, dyn_plot_frame)
        toolbar.update()

    def create_characteristics_plot_tab(self):
        """Create generator characteristics plot tab"""
        char_plot_frame = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(char_plot_frame, text="Characteristics")

        self.char_fig = Figure(figsize=(8, 6), dpi=100)
        self.char_ax = self.char_fig.add_subplot(111)

        self.char_canvas = FigureCanvasTkAgg(self.char_fig, char_plot_frame)
        self.char_canvas.draw()
        self.char_canvas.get_tk_widget().pack(fill='both', expand=True)

        toolbar = NavigationToolbar2Tk(self.char_canvas, char_plot_frame)
        toolbar.update()

    def update_param_labels(self, event=None):
        """Update parameter display labels"""
        self.La_label.config(text=f"{self.La_var.get():.3f}")
        self.Lf_label.config(text=f"{self.Lf_var.get():.1f}")
        self.J_label.config(text=f"{self.J_var.get():.2f}")
        self.speed_label.config(text=f"{int(self.speed_var.get())}")

    def update_parameters(self):
        """Update simulator parameters from GUI"""
        try:
            self.simulator.shunt_turns = float(self.shunt_turns_var.get())
            self.simulator.shunt_resistance = float(self.shunt_resistance_var.get())
            self.simulator.armature_resistance = float(self.armature_resistance_var.get())
            self.simulator.load_current = float(self.load_current_var.get())
            self.simulator.La = self.La_var.get()
            self.simulator.Lf = self.Lf_var.get()
            self.simulator.J = self.J_var.get()
            self.simulator.omega_rated = self.speed_var.get() * 2 * np.pi / 60  # Convert RPM to rad/s

            self.log_message("Parameters updated successfully.")
            self.update_all_plots()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid parameter values: {str(e)}")

    def update_occ_data(self):
        """Update OCC data from text input"""
        try:
            if_str = self.if_text.get('1.0', 'end').strip()
            emf_str = self.emf_text.get('1.0', 'end').strip()

            if_data = [float(x.strip()) for x in if_str.replace('\n', ',').split(',') if x.strip()]
            emf_data = [float(x.strip()) for x in emf_str.replace('\n', ',').split(',') if x.strip()]

            if len(if_data) != len(emf_data):
                raise ValueError("Field current and EMF arrays must have same length")

            self.simulator.if_data = np.array(if_data)
            self.simulator.emf_data = np.array(emf_data)
            self.simulator.update_occ_interpolation()

            self.log_message("OCC data updated successfully.")
            self.update_all_plots()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid OCC data: {str(e)}")

    def solve_series_turns(self):
        """Calculate and display series winding turns"""
        try:
            results = self.simulator.calculate_series_turns()

            output = "=== SERIES WINDING CALCULATION ===\n\n"
            output += "Problem: Calculate series winding turns to maintain\n"
            output += "constant terminal voltage from no-load to 50A load.\n\n"
            output += "--- No-Load Conditions ---\n"
            output += f"Terminal Voltage: {results['V_no_load']:.2f} V\n"
            output += f"Field Current: {results['If_no_load']:.4f} A\n"
            output += f"Generated EMF: {results['E_no_load']:.2f} V\n\n"
            output += "--- Load Conditions (50A) ---\n"
            output += f"Required EMF: {results['E_load_required']:.2f} V\n"
            output += f"Total Field Current Needed: {results['If_total_required']:.4f} A\n"
            output += f"Shunt Field Current: {results['If_shunt_at_load']:.4f} A\n"
            output += f"Armature Current: {results['Ia']:.2f} A\n\n"
            output += "--- RESULT ---\n"
            output += f"Series Winding Turns/Pole: {results['series_turns']:.2f}\n"
            output += f"Terminal Voltage at Load: {results['V_load']:.2f} V\n"
            output += f"Voltage Drop Compensated: {results['Ia'] * self.simulator.armature_resistance:.2f} V\n"

            self.results_text.delete('1.0', 'end')
            self.results_text.insert('1.0', output)

            self.log_message(f"Series turns calculated: {results['series_turns']:.2f} turns/pole")

        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed: {str(e)}")

    def run_dynamic_simulation(self):
        """Run dynamic simulation"""
        try:
            sim_time = float(self.sim_time_var.get())
            load_voltage = float(self.load_voltage_var.get())
            method = self.solver_var.get()

            self.log_message(f"Running dynamic simulation ({method} method)...")

            results = self.simulator.simulate_load_step_response(
                t_span=(0, sim_time),
                V_load=load_voltage,
                method=method
            )

            # Plot results
            self.dyn_ax1.clear()
            self.dyn_ax2.clear()
            self.dyn_ax3.clear()

            self.dyn_ax1.plot(results['t'], results['V_terminal'], 'b-', linewidth=2)
            self.dyn_ax1.set_ylabel('Terminal Voltage (V)', fontsize=9)
            self.dyn_ax1.grid(True, alpha=0.3)
            self.dyn_ax1.set_title(f'Dynamic Response - {method} Method', fontsize=10)

            self.dyn_ax2.plot(results['t'], results['Ia'], 'r-', linewidth=2)
            self.dyn_ax2.set_ylabel('Armature Current (A)', fontsize=9)
            self.dyn_ax2.grid(True, alpha=0.3)

            self.dyn_ax3.plot(results['t'], results['If'], 'g-', linewidth=2)
            self.dyn_ax3.set_ylabel('Field Current (A)', fontsize=9)
            self.dyn_ax3.set_xlabel('Time (s)', fontsize=9)
            self.dyn_ax3.grid(True, alpha=0.3)

            self.dyn_fig.tight_layout()
            self.dyn_canvas.draw()

            # Display results
            output = f"\n=== DYNAMIC SIMULATION RESULTS ===\n"
            output += f"Method: {method}\n"
            output += f"Simulation Time: {sim_time} s\n"
            output += f"Final Terminal Voltage: {results['V_terminal'][-1]:.2f} V\n"
            output += f"Final Armature Current: {results['Ia'][-1]:.2f} A\n"
            output += f"Final Field Current: {results['If'][-1]:.4f} A\n"
            output += f"Settling Time: ~{results['t'][-1]:.3f} s\n"

            self.results_text.insert('end', output)
            self.log_message("Dynamic simulation completed.")

        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed: {str(e)}")

    def plot_performance_curves(self):
        """Plot generator performance characteristics"""
        try:
            self.log_message("Calculating performance curves...")

            perf = self.simulator.calculate_performance_curves()

            self.perf_ax1.clear()
            self.perf_ax2.clear()

            # Voltage and EMF vs Load Current
            self.perf_ax1.plot(perf['Ia'], perf['V_terminal'], 'b-', linewidth=2, label='Terminal Voltage')
            self.perf_ax1.plot(perf['Ia'], perf['E'], 'r--', linewidth=2, label='Generated EMF')
            self.perf_ax1.set_ylabel('Voltage (V)', fontsize=9)
            self.perf_ax1.set_xlabel('Load Current (A)', fontsize=9)
            self.perf_ax1.legend(fontsize=8)
            self.perf_ax1.grid(True, alpha=0.3)
            self.perf_ax1.set_title('External Characteristic', fontsize=10)

            # Efficiency vs Load Current
            self.perf_ax2.plot(perf['Ia'], perf['efficiency'], 'g-', linewidth=2)
            self.perf_ax2.set_ylabel('Efficiency (%)', fontsize=9)
            self.perf_ax2.set_xlabel('Load Current (A)', fontsize=9)
            self.perf_ax2.grid(True, alpha=0.3)
            self.perf_ax2.set_title('Efficiency Curve', fontsize=10)

            self.perf_fig.tight_layout()
            self.perf_canvas.draw()

            self.log_message("Performance curves plotted.")

        except Exception as e:
            messagebox.showerror("Error", f"Plotting failed: {str(e)}")

    def analyze_occ(self):
        """Analyze and plot OCC curve"""
        self.update_occ_plot()
        self.log_message("OCC analysis updated.")

    def update_occ_plot(self):
        """Update OCC plot"""
        self.occ_ax.clear()

        # Plot original data points
        self.occ_ax.plot(self.simulator.if_data, self.simulator.emf_data,
                        'ro', markersize=8, label='Measured Data')

        # Plot interpolated curve
        if_fine = np.linspace(self.simulator.if_data.min(),
                             self.simulator.if_data.max(), 200)
        emf_fine = [self.simulator.get_emf_from_field_current(i) for i in if_fine]
        self.occ_ax.plot(if_fine, emf_fine, 'b-', linewidth=2, label='Interpolated Curve')

        # Mark operating point
        try:
            V_nl, If_nl, _ = self.simulator.find_no_load_voltage()
            E_nl = self.simulator.get_emf_from_field_current(If_nl)
            self.occ_ax.plot(If_nl, E_nl, 'g*', markersize=15, label=f'No-Load Point ({If_nl:.3f}A, {E_nl:.1f}V)')
        except:
            pass

        self.occ_ax.set_xlabel('Field Current (A)', fontsize=10)
        self.occ_ax.set_ylabel('Generated EMF (V)', fontsize=10)
        self.occ_ax.set_title('Open Circuit Characteristic (OCC)', fontsize=12, fontweight='bold')
        self.occ_ax.legend(fontsize=9)
        self.occ_ax.grid(True, alpha=0.3)

        self.occ_fig.tight_layout()
        self.occ_canvas.draw()

    def update_all_plots(self):
        """Update all visualization plots"""
        self.update_occ_plot()
        self.plot_performance_curves()

    def start_simulation(self):
        """Start real-time simulation"""
        if not self.sim_running:
            self.sim_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.log_message("Real-time simulation started...")

            # This could be expanded for real-time animated simulation
            self.run_dynamic_simulation()

    def stop_simulation(self):
        """Stop real-time simulation"""
        self.sim_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.log_message("Simulation stopped.")

    def reset_simulation(self):
        """Reset simulation"""
        self.stop_simulation()
        self.results_text.delete('1.0', 'end')
        self.status_text.delete('1.0', 'end')
        self.log_message("System reset.")
        self.update_all_plots()

    def log_message(self, message):
        """Log message to status window"""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.insert('end', f"[{timestamp}] {message}\n")
        self.status_text.see('end')

    def on_window_resize(self, event):
        """Handle window resize for responsive design"""
        # This ensures plots resize properly
        try:
            self.occ_fig.tight_layout()
            self.perf_fig.tight_layout()
            self.dyn_fig.tight_layout()
            self.char_fig.tight_layout()
        except:
            pass

    def save_results(self):
        """Save simulation results"""
        try:
            results_content = self.results_text.get('1.0', 'end')
            with open('dc_generator_results.txt', 'w') as f:
                f.write(results_content)
            messagebox.showinfo("Success", "Results saved to dc_generator_results.txt")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save results: {str(e)}")

    def load_config(self):
        """Load configuration (placeholder)"""
        messagebox.showinfo("Info", "Configuration loading feature - to be implemented")

    def show_about(self):
        """Show about dialog"""
        about_text = """
Advanced DC Generator Simulator
Version 1.0

Features:
• DC Shunt/Compound Generator Analysis
• Series Winding Calculation
• Dynamic ODE Simulation (RK45, Euler)
• Performance Characteristic Curves
• Real-time Visualization
• Professional Engineering Tool

Developed for Electrical Engineering Applications
        """
        messagebox.showinfo("About", about_text)

    def show_user_guide(self):
        """Show user guide"""
        guide_text = """
USER GUIDE

1. PARAMETERS TAB:
   - Enter generator specifications
   - Adjust dynamic parameters with sliders
   - Click 'Update Parameters' to apply

2. OCC DATA TAB:
   - Input field current and EMF data
   - Use comma-separated values
   - Click 'Update OCC Data' to apply

3. SIMULATION TAB:
   - Choose ODE solver (RK45 recommended)
   - Set simulation time and load voltage
   - Use Start/Stop/Reset buttons

4. ANALYSIS MENU:
   - Calculate Series Turns: Solve the compound winding problem
   - Performance Curves: Plot V-I, Efficiency curves
   - Dynamic Simulation: Run transient analysis

5. VISUALIZATION:
   - Multiple tabs show different characteristics
   - Use toolbar to zoom, pan, save plots
   - Window resizing auto-scales all elements
        """
        messagebox.showinfo("User Guide", guide_text)


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = DCGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
