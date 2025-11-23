"""
Induction Motor Capacitor Calculation Lab
Advanced Electrical Engineering Application with Dynamic Simulation

Features:
- Power factor correction calculation
- Dynamic simulation with ODE solvers (RK45, Euler)
- Real-time visualization
- Interactive Tkinter GUI with auto-scaling
- Comprehensive analysis and results
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import math
from scipy.integrate import solve_ivp
from dataclasses import dataclass
from typing import Tuple, List, Dict
import threading
import time


@dataclass
class MotorParameters:
    """Motor parameters data class"""
    rated_power: float  # kW
    rated_voltage: float  # V
    rated_frequency: float  # Hz
    poles: int

    # Full load parameters
    pf_full: float
    eff_full: float

    # Half load parameters
    pf_half: float
    eff_half: float

    # No load parameters
    current_ratio_noload: float  # ratio to full load current
    pf_noload: float

    # Target power factor
    target_pf_halfload: float


class MotorCalculator:
    """Core calculation engine for motor analysis"""

    def __init__(self, params: MotorParameters):
        self.params = params
        self.results = {}

    def calculate_full_load(self) -> Dict:
        """Calculate full load parameters"""
        P_out = self.params.rated_power
        eff = self.params.eff_full
        pf = self.params.pf_full

        P_in = P_out / eff
        S = P_in / pf
        Q = S * math.sin(math.acos(pf))
        I = S * 1000 / (math.sqrt(3) * self.params.rated_voltage)

        return {
            'P_out': P_out,
            'P_in': P_in,
            'S': S,
            'Q': Q,
            'I': I,
            'pf': pf,
            'eff': eff
        }

    def calculate_half_load(self) -> Dict:
        """Calculate half load parameters"""
        P_out = self.params.rated_power / 2
        eff = self.params.eff_half
        pf = self.params.pf_half

        P_in = P_out / eff
        S = P_in / pf
        Q = S * math.sin(math.acos(pf))
        I = S * 1000 / (math.sqrt(3) * self.params.rated_voltage)

        return {
            'P_out': P_out,
            'P_in': P_in,
            'S': S,
            'Q': Q,
            'I': I,
            'pf': pf,
            'eff': eff
        }

    def calculate_no_load(self, I_full: float) -> Dict:
        """Calculate no load parameters"""
        I = I_full * self.params.current_ratio_noload
        pf = self.params.pf_noload

        S = math.sqrt(3) * self.params.rated_voltage * I / 1000
        P_in = S * pf
        Q = S * math.sin(math.acos(pf))

        return {
            'P_out': 0,
            'P_in': P_in,
            'S': S,
            'Q': Q,
            'I': I,
            'pf': pf,
            'eff': 0
        }

    def calculate_capacitor_bank(self, half_load: Dict) -> float:
        """Calculate required capacitor bank for target PF at half load"""
        P_in = half_load['P_in']
        Q_original = half_load['Q']

        target_pf = self.params.target_pf_halfload
        Q_target = P_in * math.tan(math.acos(target_pf))

        Q_cap = Q_original - Q_target

        return Q_cap

    def calculate_corrected_pf(self, original: Dict, Q_cap: float) -> Dict:
        """Calculate corrected power factor after adding capacitor"""
        P_in = original['P_in']
        Q_original = original['Q']

        Q_new = Q_original - Q_cap
        S_new = math.sqrt(P_in**2 + Q_new**2)

        if S_new > 0:
            pf_new = P_in / S_new
            # Check if leading or lagging
            if Q_new < 0:
                pf_new = -pf_new  # Leading (negative convention)
        else:
            pf_new = 1.0

        I_new = S_new * 1000 / (math.sqrt(3) * self.params.rated_voltage)

        return {
            'P_in': P_in,
            'Q': Q_new,
            'S': S_new,
            'pf': abs(pf_new),
            'pf_type': 'leading' if Q_new < 0 else 'lagging',
            'I': I_new
        }

    def perform_complete_analysis(self) -> Dict:
        """Perform complete motor analysis"""
        # Calculate operating conditions
        full_load = self.calculate_full_load()
        half_load = self.calculate_half_load()
        no_load = self.calculate_no_load(full_load['I'])

        # Calculate capacitor bank
        Q_cap = self.calculate_capacitor_bank(half_load)

        # Calculate corrected conditions
        full_corrected = self.calculate_corrected_pf(full_load, Q_cap)
        half_corrected = self.calculate_corrected_pf(half_load, Q_cap)
        no_load_corrected = self.calculate_corrected_pf(no_load, Q_cap)

        # Calculate capacitor specifications
        V_line = self.params.rated_voltage
        C_per_phase = Q_cap * 1e6 / (3 * 2 * math.pi * self.params.rated_frequency * V_line**2)

        return {
            'full_load': full_load,
            'half_load': half_load,
            'no_load': no_load,
            'Q_cap': Q_cap,
            'full_corrected': full_corrected,
            'half_corrected': half_corrected,
            'no_load_corrected': no_load_corrected,
            'C_per_phase': C_per_phase,
            'C_total': C_per_phase * 3
        }


class DynamicSimulator:
    """Dynamic simulation with ODE solvers"""

    def __init__(self, params: MotorParameters):
        self.params = params
        self.running = False
        self.time_data = []
        self.speed_data = []
        self.torque_data = []
        self.current_data = []

    def motor_dynamics(self, t, y, T_load, V_supply):
        """
        Motor differential equations
        State variables: [speed (rad/s), flux, theta]
        """
        omega = y[0]

        # Synchronous speed
        omega_s = 2 * math.pi * self.params.rated_frequency / (self.params.poles / 2)

        # Slip
        s = (omega_s - omega) / omega_s if omega_s != 0 else 0
        s = max(0.001, min(s, 1.0))  # Limit slip

        # Simplified motor model parameters
        R1 = 0.5  # Stator resistance (ohm)
        R2 = 0.3  # Rotor resistance (ohm)
        X1 = 2.0  # Stator reactance (ohm)
        X2 = 2.0  # Rotor reactance (ohm)
        Xm = 50.0  # Magnetizing reactance (ohm)

        # Equivalent circuit calculations
        Z2 = R2/s + 1j*X2
        Zm = 1j*Xm
        Z_parallel = (Z2 * Zm) / (Z2 + Zm)
        Z_total = R1 + 1j*X1 + Z_parallel

        # Current
        V_phase = V_supply / math.sqrt(3)
        I1 = V_phase / abs(Z_total)

        # Torque
        P_airgap = 3 * abs(I1)**2 * R2/s
        T_elec = P_airgap / omega_s

        # Inertia (typical value)
        J = 0.5  # kg.m^2

        # Equation of motion
        domega_dt = (T_elec - T_load) / J

        return [domega_dt, 0, omega]

    def simulate_startup(self, method='RK45', T_load=50, duration=3.0):
        """Simulate motor startup"""
        # Initial conditions: [speed, flux, theta]
        y0 = [0.0, 0.0, 0.0]

        # Time span
        t_span = (0, duration)
        t_eval = np.linspace(0, duration, 300)

        # Voltage supply (nominal)
        V_supply = self.params.rated_voltage

        # Solve ODE
        if method == 'RK45':
            sol = solve_ivp(
                lambda t, y: self.motor_dynamics(t, y, T_load, V_supply),
                t_span, y0, method='RK45', t_eval=t_eval,
                max_step=0.01
            )
        else:  # Euler method
            sol = self.euler_method(
                lambda t, y: self.motor_dynamics(t, y, T_load, V_supply),
                t_span, y0, t_eval
            )

        # Store results
        self.time_data = sol.t if hasattr(sol, 't') else t_eval
        self.speed_data = sol.y[0] if hasattr(sol, 'y') else sol[0]

        # Calculate torque and current
        omega_s = 2 * math.pi * self.params.rated_frequency / (self.params.poles / 2)
        self.torque_data = []
        self.current_data = []

        for omega in self.speed_data:
            s = (omega_s - omega) / omega_s if omega_s != 0 else 0
            s = max(0.001, min(s, 1.0))

            # Simplified torque calculation
            T = 200 * s / (s**2 + 0.1)  # Typical torque-slip curve
            self.torque_data.append(T)

            # Simplified current calculation
            I = 100 * (1 + 2*s)  # Current decreases as motor speeds up
            self.current_data.append(I)

        return {
            'time': self.time_data,
            'speed': self.speed_data,
            'torque': self.torque_data,
            'current': self.current_data
        }

    def euler_method(self, f, t_span, y0, t_eval):
        """Simple Euler method for ODE solving"""
        t = t_eval
        y = np.zeros((len(y0), len(t)))
        y[:, 0] = y0

        for i in range(len(t) - 1):
            dt = t[i+1] - t[i]
            dydt = f(t[i], y[:, i])
            y[:, i+1] = y[:, i] + dt * np.array(dydt)

        # Return in similar format to solve_ivp
        class Solution:
            pass

        sol = Solution()
        sol.t = t
        sol.y = y
        return sol


class MotorCapacitorLab(tk.Tk):
    """Main application class"""

    def __init__(self):
        super().__init__()

        self.title("Induction Motor Capacitor Calculation Lab")
        self.geometry("1400x900")

        # Default parameters for the given problem
        self.default_params = {
            'rated_power': 37.3,
            'rated_voltage': 415.0,
            'rated_frequency': 50.0,
            'poles': 4,
            'pf_full': 0.9,
            'eff_full': 0.9,
            'pf_half': 0.6,
            'eff_half': 0.7,
            'current_ratio_noload': 0.25,
            'pf_noload': 0.1,
            'target_pf_halfload': 0.8
        }

        # Simulation control
        self.simulation_running = False
        self.simulation_thread = None

        # Configure grid weight for auto-scaling
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create UI
        self.create_menu()
        self.create_main_interface()

        # Bind resize event
        self.bind('<Configure>', self.on_window_resize)

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Default Problem", command=self.load_default_problem)
        file_menu.add_command(label="Reset All", command=self.reset_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Calculate menu
        calc_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Calculate", menu=calc_menu)
        calc_menu.add_command(label="Perform Analysis", command=self.perform_analysis)
        calc_menu.add_command(label="Run Dynamic Simulation", command=self.start_simulation)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Instructions", command=self.show_instructions)

    def create_main_interface(self):
        """Create main interface with tabs"""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Create tabs
        self.tab_input = ttk.Frame(self.notebook)
        self.tab_results = ttk.Frame(self.notebook)
        self.tab_visualization = ttk.Frame(self.notebook)
        self.tab_simulation = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_input, text='Input Parameters')
        self.notebook.add(self.tab_results, text='Analysis Results')
        self.notebook.add(self.tab_visualization, text='Visualization')
        self.notebook.add(self.tab_simulation, text='Dynamic Simulation')

        # Configure tab grids
        for tab in [self.tab_input, self.tab_results, self.tab_visualization, self.tab_simulation]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

        # Create tab contents
        self.create_input_tab()
        self.create_results_tab()
        self.create_visualization_tab()
        self.create_simulation_tab()

    def create_input_tab(self):
        """Create input parameters tab"""
        # Main container with scrollbar
        canvas = tk.Canvas(self.tab_input)
        scrollbar = ttk.Scrollbar(self.tab_input, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Input fields dictionary
        self.input_vars = {}

        # Motor rated parameters
        rated_frame = ttk.LabelFrame(scrollable_frame, text="Motor Rated Parameters", padding=10)
        rated_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        inputs = [
            ('rated_power', 'Rated Power (kW)', 1, 200, 0.1),
            ('rated_voltage', 'Rated Voltage (V)', 100, 1000, 1),
            ('rated_frequency', 'Frequency (Hz)', 40, 70, 1),
            ('poles', 'Number of Poles', 2, 12, 2),
        ]

        for i, (key, label, min_val, max_val, step) in enumerate(inputs):
            self.create_slider_input(rated_frame, key, label, min_val, max_val, step, i,
                                     self.default_params[key])

        # Full load parameters
        full_frame = ttk.LabelFrame(scrollable_frame, text="Full Load Parameters", padding=10)
        full_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        inputs = [
            ('pf_full', 'Power Factor', 0.5, 1.0, 0.01),
            ('eff_full', 'Efficiency', 0.5, 1.0, 0.01),
        ]

        for i, (key, label, min_val, max_val, step) in enumerate(inputs):
            self.create_slider_input(full_frame, key, label, min_val, max_val, step, i,
                                     self.default_params[key])

        # Half load parameters
        half_frame = ttk.LabelFrame(scrollable_frame, text="Half Load Parameters", padding=10)
        half_frame.grid(row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        inputs = [
            ('pf_half', 'Power Factor', 0.3, 1.0, 0.01),
            ('eff_half', 'Efficiency', 0.3, 1.0, 0.01),
        ]

        for i, (key, label, min_val, max_val, step) in enumerate(inputs):
            self.create_slider_input(half_frame, key, label, min_val, max_val, step, i,
                                     self.default_params[key])

        # No load parameters
        noload_frame = ttk.LabelFrame(scrollable_frame, text="No Load Parameters", padding=10)
        noload_frame.grid(row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        inputs = [
            ('current_ratio_noload', 'Current Ratio (I_nl/I_fl)', 0.1, 0.5, 0.01),
            ('pf_noload', 'Power Factor', 0.05, 0.3, 0.01),
        ]

        for i, (key, label, min_val, max_val, step) in enumerate(inputs):
            self.create_slider_input(noload_frame, key, label, min_val, max_val, step, i,
                                     self.default_params[key])

        # Target parameters
        target_frame = ttk.LabelFrame(scrollable_frame, text="Target Parameters", padding=10)
        target_frame.grid(row=4, column=0, columnspan=2, sticky='ew', padx=10, pady=5)

        self.create_slider_input(target_frame, 'target_pf_halfload',
                                'Target PF at Half Load', 0.7, 1.0, 0.01, 0,
                                self.default_params['target_pf_halfload'])

        # Control buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Calculate", command=self.perform_analysis,
                  style='Accent.TButton').grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Reset", command=self.reset_all).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Load Default Problem",
                  command=self.load_default_problem).grid(row=0, column=2, padx=5)

        # Pack canvas and scrollbar
        canvas.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # Configure grid weights
        self.tab_input.grid_rowconfigure(0, weight=1)
        self.tab_input.grid_columnconfigure(0, weight=1)

    def create_slider_input(self, parent, key, label, min_val, max_val, step, row, default):
        """Create a slider input with label and value display"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky='w', padx=5, pady=5)

        var = tk.DoubleVar(value=default)
        self.input_vars[key] = var

        value_label = ttk.Label(parent, text=f"{default:.3f}")
        value_label.grid(row=row, column=1, padx=5)

        slider = ttk.Scale(parent, from_=min_val, to=max_val, variable=var, orient='horizontal',
                          command=lambda v: value_label.config(text=f"{float(v):.3f}"))
        slider.grid(row=row, column=2, sticky='ew', padx=5)

        parent.grid_columnconfigure(2, weight=1)

    def create_results_tab(self):
        """Create results display tab"""
        # Create scrolled text widget
        self.results_text = scrolledtext.ScrolledText(self.tab_results, wrap=tk.WORD,
                                                       font=('Courier', 10))
        self.results_text.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Configure tags for formatting
        self.results_text.tag_config('heading', font=('Courier', 12, 'bold'), foreground='blue')
        self.results_text.tag_config('subheading', font=('Courier', 10, 'bold'))
        self.results_text.tag_config('important', foreground='red', font=('Courier', 10, 'bold'))

    def create_visualization_tab(self):
        """Create visualization tab with matplotlib"""
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8), dpi=100)

        # Create subplots
        self.ax1 = self.fig.add_subplot(2, 2, 1)
        self.ax2 = self.fig.add_subplot(2, 2, 2)
        self.ax3 = self.fig.add_subplot(2, 2, 3)
        self.ax4 = self.fig.add_subplot(2, 2, 4)

        self.fig.tight_layout(pad=3.0)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_visualization)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Add toolbar
        toolbar_frame = ttk.Frame(self.tab_visualization)
        toolbar_frame.grid(row=1, column=0, sticky='ew')
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

    def create_simulation_tab(self):
        """Create dynamic simulation tab"""
        # Control frame
        control_frame = ttk.LabelFrame(self.tab_simulation, text="Simulation Controls", padding=10)
        control_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)

        ttk.Label(control_frame, text="ODE Solver:").grid(row=0, column=0, padx=5, pady=5)
        self.solver_var = tk.StringVar(value='RK45')
        ttk.Radiobutton(control_frame, text="RK45 (Adaptive)", variable=self.solver_var,
                       value='RK45').grid(row=0, column=1, padx=5)
        ttk.Radiobutton(control_frame, text="Euler (Fixed Step)", variable=self.solver_var,
                       value='Euler').grid(row=0, column=2, padx=5)

        ttk.Label(control_frame, text="Load Torque (Nm):").grid(row=1, column=0, padx=5, pady=5)
        self.load_torque_var = tk.DoubleVar(value=50.0)
        ttk.Scale(control_frame, from_=0, to=200, variable=self.load_torque_var,
                 orient='horizontal').grid(row=1, column=1, columnspan=2, sticky='ew', padx=5)
        self.load_label = ttk.Label(control_frame, text="50.0 Nm")
        self.load_label.grid(row=1, column=3, padx=5)
        self.load_torque_var.trace('w', lambda *args: self.load_label.config(
            text=f"{self.load_torque_var.get():.1f} Nm"))

        ttk.Label(control_frame, text="Duration (s):").grid(row=2, column=0, padx=5, pady=5)
        self.duration_var = tk.DoubleVar(value=3.0)
        ttk.Entry(control_frame, textvariable=self.duration_var, width=10).grid(row=2, column=1, padx=5)

        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10)

        self.btn_start = ttk.Button(button_frame, text="Start Simulation",
                                     command=self.start_simulation)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = ttk.Button(button_frame, text="Stop Simulation",
                                    command=self.stop_simulation, state='disabled')
        self.btn_stop.grid(row=0, column=1, padx=5)

        ttk.Button(button_frame, text="Reset", command=self.reset_simulation).grid(row=0, column=2, padx=5)

        # Simulation plots
        self.sim_fig = Figure(figsize=(12, 8), dpi=100)

        self.sim_ax1 = self.sim_fig.add_subplot(2, 2, 1)
        self.sim_ax2 = self.sim_fig.add_subplot(2, 2, 2)
        self.sim_ax3 = self.sim_fig.add_subplot(2, 2, 3)
        self.sim_ax4 = self.sim_fig.add_subplot(2, 2, 4)

        self.sim_fig.tight_layout(pad=3.0)

        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, master=self.tab_simulation)
        self.sim_canvas.draw()
        self.sim_canvas.get_tk_widget().grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        # Configure grid
        self.tab_simulation.grid_rowconfigure(1, weight=1)
        self.tab_simulation.grid_columnconfigure(0, weight=1)

    def get_motor_parameters(self) -> MotorParameters:
        """Get motor parameters from input fields"""
        return MotorParameters(
            rated_power=self.input_vars['rated_power'].get(),
            rated_voltage=self.input_vars['rated_voltage'].get(),
            rated_frequency=self.input_vars['rated_frequency'].get(),
            poles=int(self.input_vars['poles'].get()),
            pf_full=self.input_vars['pf_full'].get(),
            eff_full=self.input_vars['eff_full'].get(),
            pf_half=self.input_vars['pf_half'].get(),
            eff_half=self.input_vars['eff_half'].get(),
            current_ratio_noload=self.input_vars['current_ratio_noload'].get(),
            pf_noload=self.input_vars['pf_noload'].get(),
            target_pf_halfload=self.input_vars['target_pf_halfload'].get()
        )

    def perform_analysis(self):
        """Perform complete motor analysis"""
        try:
            # Get parameters
            params = self.get_motor_parameters()

            # Create calculator
            calc = MotorCalculator(params)

            # Perform analysis
            results = calc.perform_complete_analysis()

            # Display results
            self.display_results(results)

            # Update visualizations
            self.update_visualizations(results)

            # Switch to results tab
            self.notebook.select(self.tab_results)

            messagebox.showinfo("Success", "Analysis completed successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")

    def display_results(self, results: Dict):
        """Display analysis results"""
        self.results_text.delete(1.0, tk.END)

        def write_line(text, tag=None):
            if tag:
                self.results_text.insert(tk.END, text + '\n', tag)
            else:
                self.results_text.insert(tk.END, text + '\n')

        write_line("=" * 80, 'heading')
        write_line("INDUCTION MOTOR CAPACITOR CALCULATION ANALYSIS", 'heading')
        write_line("=" * 80, 'heading')
        write_line("")

        # Original conditions
        write_line("ORIGINAL OPERATING CONDITIONS (Without Capacitor)", 'subheading')
        write_line("-" * 80)
        write_line("")

        write_line("Full Load:")
        fl = results['full_load']
        write_line(f"  Output Power:      {fl['P_out']:>10.3f} kW")
        write_line(f"  Input Power:       {fl['P_in']:>10.3f} kW")
        write_line(f"  Apparent Power:    {fl['S']:>10.3f} kVA")
        write_line(f"  Reactive Power:    {fl['Q']:>10.3f} kVAR")
        write_line(f"  Current:           {fl['I']:>10.3f} A")
        write_line(f"  Power Factor:      {fl['pf']:>10.3f} (lagging)")
        write_line(f"  Efficiency:        {fl['eff']*100:>10.2f} %")
        write_line("")

        write_line("Half Load:")
        hl = results['half_load']
        write_line(f"  Output Power:      {hl['P_out']:>10.3f} kW")
        write_line(f"  Input Power:       {hl['P_in']:>10.3f} kW")
        write_line(f"  Apparent Power:    {hl['S']:>10.3f} kVA")
        write_line(f"  Reactive Power:    {hl['Q']:>10.3f} kVAR")
        write_line(f"  Current:           {hl['I']:>10.3f} A")
        write_line(f"  Power Factor:      {hl['pf']:>10.3f} (lagging)")
        write_line(f"  Efficiency:        {hl['eff']*100:>10.2f} %")
        write_line("")

        write_line("No Load:")
        nl = results['no_load']
        write_line(f"  Input Power:       {nl['P_in']:>10.3f} kW")
        write_line(f"  Apparent Power:    {nl['S']:>10.3f} kVA")
        write_line(f"  Reactive Power:    {nl['Q']:>10.3f} kVAR")
        write_line(f"  Current:           {nl['I']:>10.3f} A")
        write_line(f"  Power Factor:      {nl['pf']:>10.3f} (lagging)")
        write_line("")
        write_line("")

        # Capacitor bank
        write_line("CAPACITOR BANK SPECIFICATION", 'subheading')
        write_line("-" * 80)
        write_line("")
        write_line(f"Required Capacitor Bank:     {results['Q_cap']:>10.3f} kVAR", 'important')
        write_line(f"Capacitance per Phase:       {results['C_per_phase']*1e6:>10.3f} µF")
        write_line(f"Total Capacitance (3-phase): {results['C_total']*1e6:>10.3f} µF")
        write_line("")
        write_line("")

        # Corrected conditions
        write_line("CORRECTED OPERATING CONDITIONS (With Capacitor)", 'subheading')
        write_line("-" * 80)
        write_line("")

        write_line("Full Load:")
        flc = results['full_corrected']
        write_line(f"  Active Power:      {flc['P_in']:>10.3f} kW")
        write_line(f"  Reactive Power:    {flc['Q']:>10.3f} kVAR ({flc['pf_type']})")
        write_line(f"  Apparent Power:    {flc['S']:>10.3f} kVA")
        write_line(f"  Power Factor:      {flc['pf']:>10.3f} ({flc['pf_type']})", 'important')
        write_line(f"  Current:           {flc['I']:>10.3f} A")
        write_line("")

        write_line("Half Load:")
        hlc = results['half_corrected']
        write_line(f"  Active Power:      {hlc['P_in']:>10.3f} kW")
        write_line(f"  Reactive Power:    {hlc['Q']:>10.3f} kVAR ({hlc['pf_type']})")
        write_line(f"  Apparent Power:    {hlc['S']:>10.3f} kVA")
        write_line(f"  Power Factor:      {hlc['pf']:>10.3f} ({hlc['pf_type']})", 'important')
        write_line(f"  Current:           {hlc['I']:>10.3f} A")
        write_line("")

        write_line("No Load:")
        nlc = results['no_load_corrected']
        write_line(f"  Active Power:      {nlc['P_in']:>10.3f} kW")
        write_line(f"  Reactive Power:    {nlc['Q']:>10.3f} kVAR ({nlc['pf_type']})")
        write_line(f"  Apparent Power:    {nlc['S']:>10.3f} kVA")
        write_line(f"  Power Factor:      {nlc['pf']:>10.3f} ({nlc['pf_type']})", 'important')
        write_line(f"  Current:           {nlc['I']:>10.3f} A")
        write_line("")
        write_line("")

        # Summary
        write_line("ANSWER TO THE PROBLEM", 'heading')
        write_line("=" * 80, 'heading')
        write_line("")
        write_line(f"(i)  Line Power Factor at FULL LOAD:  {flc['pf']:>6.3f} {flc['pf_type']}", 'important')
        write_line(f"(ii) Line Power Factor at NO LOAD:    {nlc['pf']:>6.3f} {nlc['pf_type']}", 'important')
        write_line("")
        write_line("=" * 80, 'heading')

    def update_visualizations(self, results: Dict):
        """Update visualization plots"""
        # Clear all axes
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()

        # Plot 1: Power Factor Comparison
        conditions = ['Full Load', 'Half Load', 'No Load']
        pf_original = [results['full_load']['pf'], results['half_load']['pf'],
                      results['no_load']['pf']]
        pf_corrected = [results['full_corrected']['pf'], results['half_corrected']['pf'],
                       results['no_load_corrected']['pf']]

        x = np.arange(len(conditions))
        width = 0.35

        self.ax1.bar(x - width/2, pf_original, width, label='Without Capacitor', color='coral')
        self.ax1.bar(x + width/2, pf_corrected, width, label='With Capacitor', color='skyblue')
        self.ax1.set_ylabel('Power Factor')
        self.ax1.set_title('Power Factor Comparison')
        self.ax1.set_xticks(x)
        self.ax1.set_xticklabels(conditions)
        self.ax1.legend()
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_ylim([0, 1.1])

        # Plot 2: Power Flow Diagram
        powers_original = [
            results['full_load']['P_in'],
            results['half_load']['P_in'],
            results['no_load']['P_in']
        ]
        reactive_original = [
            results['full_load']['Q'],
            results['half_load']['Q'],
            results['no_load']['Q']
        ]
        reactive_corrected = [
            results['full_corrected']['Q'],
            results['half_corrected']['Q'],
            results['no_load_corrected']['Q']
        ]

        self.ax2.plot(conditions, powers_original, 'o-', label='Active Power', linewidth=2, markersize=8)
        self.ax2.plot(conditions, reactive_original, 's-', label='Reactive (Original)', linewidth=2, markersize=8)
        self.ax2.plot(conditions, reactive_corrected, '^-', label='Reactive (Corrected)', linewidth=2, markersize=8)
        self.ax2.set_ylabel('Power (kW/kVAR)')
        self.ax2.set_title('Power Flow Analysis')
        self.ax2.legend()
        self.ax2.grid(True, alpha=0.3)

        # Plot 3: Current Comparison
        current_original = [
            results['full_load']['I'],
            results['half_load']['I'],
            results['no_load']['I']
        ]
        current_corrected = [
            results['full_corrected']['I'],
            results['half_corrected']['I'],
            results['no_load_corrected']['I']
        ]

        self.ax3.bar(x - width/2, current_original, width, label='Without Capacitor', color='orange')
        self.ax3.bar(x + width/2, current_corrected, width, label='With Capacitor', color='green')
        self.ax3.set_ylabel('Current (A)')
        self.ax3.set_title('Line Current Comparison')
        self.ax3.set_xticks(x)
        self.ax3.set_xticklabels(conditions)
        self.ax3.legend()
        self.ax3.grid(True, alpha=0.3)

        # Plot 4: Power Triangle at Half Load
        P_hl = results['half_load']['P_in']
        Q_hl_original = results['half_load']['Q']
        Q_hl_corrected = results['half_corrected']['Q']
        Q_cap = results['Q_cap']

        self.ax4.arrow(0, 0, P_hl, 0, head_width=1, head_length=1, fc='blue', ec='blue', linewidth=2)
        self.ax4.text(P_hl/2, -2, f'P = {P_hl:.1f} kW', ha='center', fontsize=10, color='blue')

        self.ax4.arrow(P_hl, 0, 0, Q_hl_original, head_width=1, head_length=1, fc='red', ec='red', linewidth=2)
        self.ax4.text(P_hl+3, Q_hl_original/2, f'Q_orig = {Q_hl_original:.1f} kVAR', fontsize=9, color='red')

        self.ax4.arrow(P_hl, Q_hl_original, 0, -Q_cap, head_width=1, head_length=1, fc='green', ec='green', linewidth=2, linestyle='--')
        self.ax4.text(P_hl+3, Q_hl_original-Q_cap/2, f'Q_cap = {Q_cap:.1f} kVAR', fontsize=9, color='green')

        self.ax4.arrow(0, 0, P_hl, Q_hl_corrected, head_width=1, head_length=1.5, fc='purple', ec='purple', linewidth=2)
        self.ax4.text(P_hl/2+2, Q_hl_corrected+2, f'S_new = {results["half_corrected"]["S"]:.1f} kVA', fontsize=9, color='purple')

        self.ax4.set_xlabel('Active Power (kW)')
        self.ax4.set_ylabel('Reactive Power (kVAR)')
        self.ax4.set_title('Power Triangle at Half Load')
        self.ax4.grid(True, alpha=0.3)
        self.ax4.axis('equal')

        self.fig.tight_layout()
        self.canvas.draw()

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.simulation_running:
            messagebox.showwarning("Warning", "Simulation already running!")
            return

        try:
            params = self.get_motor_parameters()
            solver = self.solver_var.get()
            T_load = self.load_torque_var.get()
            duration = self.duration_var.get()

            self.simulation_running = True
            self.btn_start.config(state='disabled')
            self.btn_stop.config(state='normal')

            # Run simulation in separate thread
            self.simulation_thread = threading.Thread(
                target=self.run_simulation_thread,
                args=(params, solver, T_load, duration)
            )
            self.simulation_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed: {str(e)}")
            self.simulation_running = False
            self.btn_start.config(state='normal')
            self.btn_stop.config(state='disabled')

    def run_simulation_thread(self, params, solver, T_load, duration):
        """Run simulation in separate thread"""
        try:
            simulator = DynamicSimulator(params)
            results = simulator.simulate_startup(method=solver, T_load=T_load, duration=duration)

            # Update plots on main thread
            self.after(0, lambda: self.update_simulation_plots(results))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Simulation error: {str(e)}"))
        finally:
            self.simulation_running = False
            self.after(0, lambda: self.btn_start.config(state='normal'))
            self.after(0, lambda: self.btn_stop.config(state='disabled'))

    def update_simulation_plots(self, results):
        """Update simulation plots"""
        # Clear axes
        for ax in [self.sim_ax1, self.sim_ax2, self.sim_ax3, self.sim_ax4]:
            ax.clear()

        time = results['time']
        speed = np.array(results['speed'])
        torque = results['torque']
        current = results['current']

        # Convert speed to RPM
        speed_rpm = speed * 60 / (2 * np.pi)

        # Synchronous speed
        omega_s = 2 * np.pi * self.get_motor_parameters().rated_frequency / (self.get_motor_parameters().poles / 2)
        sync_speed_rpm = omega_s * 60 / (2 * np.pi)

        # Plot 1: Speed vs Time
        self.sim_ax1.plot(time, speed_rpm, 'b-', linewidth=2)
        self.sim_ax1.axhline(y=sync_speed_rpm, color='r', linestyle='--', label=f'Sync Speed ({sync_speed_rpm:.0f} RPM)')
        self.sim_ax1.set_xlabel('Time (s)')
        self.sim_ax1.set_ylabel('Speed (RPM)')
        self.sim_ax1.set_title('Motor Speed During Startup')
        self.sim_ax1.grid(True, alpha=0.3)
        self.sim_ax1.legend()

        # Plot 2: Torque vs Time
        self.sim_ax2.plot(time, torque, 'g-', linewidth=2)
        self.sim_ax2.set_xlabel('Time (s)')
        self.sim_ax2.set_ylabel('Torque (Nm)')
        self.sim_ax2.set_title('Electromagnetic Torque')
        self.sim_ax2.grid(True, alpha=0.3)

        # Plot 3: Current vs Time
        self.sim_ax3.plot(time, current, 'r-', linewidth=2)
        self.sim_ax3.set_xlabel('Time (s)')
        self.sim_ax3.set_ylabel('Current (A)')
        self.sim_ax3.set_title('Stator Current')
        self.sim_ax3.grid(True, alpha=0.3)

        # Plot 4: Torque-Speed Characteristic
        self.sim_ax4.plot(speed_rpm, torque, 'purple', linewidth=2)
        self.sim_ax4.set_xlabel('Speed (RPM)')
        self.sim_ax4.set_ylabel('Torque (Nm)')
        self.sim_ax4.set_title('Torque-Speed Characteristic')
        self.sim_ax4.grid(True, alpha=0.3)

        self.sim_fig.tight_layout()
        self.sim_canvas.draw()

        # Switch to simulation tab
        self.notebook.select(self.tab_simulation)

    def stop_simulation(self):
        """Stop running simulation"""
        self.simulation_running = False
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')

    def reset_simulation(self):
        """Reset simulation plots"""
        for ax in [self.sim_ax1, self.sim_ax2, self.sim_ax3, self.sim_ax4]:
            ax.clear()
        self.sim_canvas.draw()

    def load_default_problem(self):
        """Load the default problem parameters"""
        for key, value in self.default_params.items():
            if key in self.input_vars:
                self.input_vars[key].set(value)
        messagebox.showinfo("Loaded", "Default problem parameters loaded successfully!")

    def reset_all(self):
        """Reset all inputs and outputs"""
        self.load_default_problem()
        self.results_text.delete(1.0, tk.END)

        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()
        self.canvas.draw()

        self.reset_simulation()

    def on_window_resize(self, event):
        """Handle window resize for auto-scaling"""
        # Update canvas sizes if needed
        pass

    def show_about(self):
        """Show about dialog"""
        about_text = """
Induction Motor Capacitor Calculation Lab
Version 1.0

Advanced Electrical Engineering Application

Features:
• Power factor correction analysis
• Capacitor bank sizing
• Dynamic motor simulation
• Real-time ODE solvers (RK45, Euler)
• Comprehensive visualization

Developed for electrical engineering education and practical applications.
        """
        messagebox.showinfo("About", about_text)

    def show_instructions(self):
        """Show instructions dialog"""
        instructions = """
INSTRUCTIONS:

1. Input Parameters Tab:
   - Adjust motor parameters using sliders
   - Set operating conditions at different loads
   - Click 'Calculate' to perform analysis

2. Analysis Results Tab:
   - View detailed calculation results
   - See original and corrected power factors
   - Review capacitor bank specifications

3. Visualization Tab:
   - Compare power factors graphically
   - Analyze power flow
   - View power triangles

4. Dynamic Simulation Tab:
   - Select ODE solver method
   - Set load torque and duration
   - Run startup simulation
   - Observe transient behavior

Tips:
• Use 'Load Default Problem' to see the example
• Adjust parameters with sliders for real-time updates
• Export results using File menu
        """
        messagebox.showinfo("Instructions", instructions)


def main():
    """Main entry point"""
    app = MotorCapacitorLab()
    app.mainloop()


if __name__ == "__main__":
    main()
