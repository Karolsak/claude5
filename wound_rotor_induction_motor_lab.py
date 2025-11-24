#!/usr/bin/env python3
"""
Wound-Rotor Induction Motor Analysis Lab with Unbalanced Three-Phase Supply
Example 6.2: 460V/100hp motor with unbalanced voltages
Features:
- Dynamic simulation with ODE solvers (RK45, Euler)
- Real-time visualization of currents, torque, speed
- Unbalanced three-phase voltage analysis
- Interactive Tkinter GUI with auto-scaling
- Advanced electrical engineering analysis
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from scipy.integrate import solve_ivp
import cmath


class InductionMotorModel:
    """Mathematical model of wound-rotor induction motor with differential equations"""

    def __init__(self):
        # Motor parameters (Example 4.3 - 460V/100hp wound-rotor motor)
        self.P = 6  # Number of poles
        self.f = 60  # Frequency (Hz)
        self.rated_voltage = 460  # Rated voltage (V)
        self.rated_power = 100 * 746  # Rated power (W) - 100 hp
        self.rated_speed = 1170  # Rated speed (rpm)

        # Synchronous speed
        self.n_sync = 120 * self.f / self.P  # rpm
        self.omega_sync = 2 * np.pi * self.f / (self.P / 2)  # electrical rad/s

        # Equivalent circuit parameters (typical values for 100hp motor)
        self.R1 = 0.0625  # Stator resistance (ohms)
        self.X1 = 0.454   # Stator leakage reactance (ohms)
        self.Xm = 20.1    # Magnetizing reactance (ohms)
        self.R2 = 0.0862  # Rotor resistance (ohms)
        self.X2 = 0.454   # Rotor leakage reactance (ohms)

        # Mechanical parameters
        self.J = 5.0      # Moment of inertia (kg·m²)
        self.B = 0.1      # Friction coefficient (N·m·s)

        # Load torque parameters
        self.T_load = 0   # Load torque (N·m)

        # Unbalanced voltages (Example 6.2)
        self.V_ab = 450   # Line voltage ab (V)
        self.V_bc = 470   # Line voltage bc (V)
        self.V_ca = 440   # Line voltage ca (V)

        # Operating conditions
        self.current_speed = 1770  # Current speed (rpm)

    def phase_voltages_from_line(self):
        """Convert unbalanced line voltages to phase voltages using phasor analysis"""
        # Line voltages as phasors
        V_ab = self.V_ab * cmath.exp(1j * 0)  # Reference
        V_bc = self.V_bc * cmath.exp(1j * (-2 * np.pi / 3))
        V_ca = self.V_ca * cmath.exp(1j * (2 * np.pi / 3))

        # Phase voltages (assuming Y connection)
        # V_an = (V_ab - V_ca) / 3
        # V_bn = (V_bc - V_ab) / 3
        # V_cn = (V_ca - V_bc) / 3

        # Simplified: Use line-to-neutral conversion
        V_an = V_ab / np.sqrt(3) * cmath.exp(1j * np.pi / 6)
        V_bn = V_bc / np.sqrt(3) * cmath.exp(1j * (-np.pi / 2))
        V_cn = V_ca / np.sqrt(3) * cmath.exp(1j * (5 * np.pi / 6))

        return V_an, V_bn, V_cn

    def symmetrical_components(self):
        """Calculate positive, negative, and zero sequence components"""
        V_an, V_bn, V_cn = self.phase_voltages_from_line()

        # Symmetrical components transformation
        a = cmath.exp(1j * 2 * np.pi / 3)  # Operator

        # Positive sequence
        V_pos = (V_an + a * V_bn + a**2 * V_cn) / 3

        # Negative sequence
        V_neg = (V_an + a**2 * V_bn + a * V_cn) / 3

        # Zero sequence
        V_zero = (V_an + V_bn + V_cn) / 3

        return V_pos, V_neg, V_zero

    def calculate_slip(self, speed_rpm):
        """Calculate slip at given speed"""
        return (self.n_sync - speed_rpm) / self.n_sync

    def calculate_torque_steady_state(self, slip):
        """Calculate electromagnetic torque using equivalent circuit (steady-state)"""
        if abs(slip) < 1e-6:
            slip = 1e-6

        # Calculate for positive and negative sequence separately
        V_pos, V_neg, V_zero = self.symmetrical_components()
        V_pos_mag = abs(V_pos)
        V_neg_mag = abs(V_neg)

        # Positive sequence torque
        Z_in_pos = self.R2 / slip + 1j * self.X2
        Z_total_pos = self.R1 + 1j * self.X1 + (1j * self.Xm * Z_in_pos) / (1j * self.Xm + Z_in_pos)
        I1_pos = V_pos_mag / abs(Z_total_pos)

        # Power transferred to rotor (positive sequence)
        P_ag_pos = 3 * I1_pos**2 * self.R2 / slip
        T_pos = P_ag_pos / self.omega_sync

        # Negative sequence torque (slip for negative sequence = 2-s)
        slip_neg = 2 - slip
        if abs(slip_neg) < 1e-6:
            slip_neg = 1e-6

        Z_in_neg = self.R2 / slip_neg + 1j * self.X2
        Z_total_neg = self.R1 + 1j * self.X1 + (1j * self.Xm * Z_in_neg) / (1j * self.Xm + Z_in_neg)
        I1_neg = V_neg_mag / abs(Z_total_neg)

        # Negative sequence torque (opposes rotation)
        P_ag_neg = 3 * I1_neg**2 * self.R2 / slip_neg
        T_neg = -P_ag_neg / self.omega_sync

        # Total torque
        T_total = T_pos + T_neg

        return T_total, T_pos, T_neg

    def calculate_currents(self, slip):
        """Calculate stator and rotor currents"""
        V_pos, V_neg, V_zero = self.symmetrical_components()

        # Positive sequence current
        Z_in_pos = self.R2 / slip + 1j * self.X2
        Z_total_pos = self.R1 + 1j * self.X1 + (1j * self.Xm * Z_in_pos) / (1j * self.Xm + Z_in_pos)
        I1_pos = V_pos / Z_total_pos

        # Negative sequence current
        slip_neg = 2 - slip
        Z_in_neg = self.R2 / slip_neg + 1j * self.X2
        Z_total_neg = self.R1 + 1j * self.X1 + (1j * self.Xm * Z_in_neg) / (1j * self.Xm + Z_in_neg)
        I1_neg = V_neg / Z_total_neg

        # Phase currents
        a = cmath.exp(1j * 2 * np.pi / 3)
        I_a = I1_pos + I1_neg
        I_b = a**2 * I1_pos + a * I1_neg
        I_c = a * I1_pos + a**2 * I1_neg

        return I_a, I_b, I_c, I1_pos, I1_neg

    def calculate_power_and_efficiency(self, slip, speed_rpm):
        """Calculate input power, output power, losses, and efficiency"""
        I_a, I_b, I_c, I1_pos, I1_neg = self.calculate_currents(slip)
        V_an, V_bn, V_cn = self.phase_voltages_from_line()

        # Input power (three-phase)
        P_in = (V_an * np.conj(I_a) + V_bn * np.conj(I_b) + V_cn * np.conj(I_c)).real

        # Stator copper losses
        I_rms = (abs(I_a)**2 + abs(I_b)**2 + abs(I_c)**2) / 3
        P_cu_stator = 3 * I_rms * self.R1

        # Air gap power
        T_em, _, _ = self.calculate_torque_steady_state(slip)
        omega_m = speed_rpm * 2 * np.pi / 60
        P_ag = T_em * self.omega_sync

        # Rotor copper losses
        P_cu_rotor = slip * P_ag

        # Mechanical output power
        P_mech = T_em * omega_m

        # Friction and windage losses
        P_fw = self.B * omega_m**2

        # Output power
        P_out = P_mech - P_fw

        # Efficiency
        if P_in > 0:
            efficiency = (P_out / P_in) * 100
        else:
            efficiency = 0

        return P_in, P_out, P_cu_stator, P_cu_rotor, P_fw, efficiency

    def motor_dynamics(self, t, y, T_load):
        """Differential equations for motor dynamics
        State variables: y = [omega_m, theta_m]
        omega_m: mechanical angular velocity (rad/s)
        theta_m: rotor angle (rad)
        """
        omega_m = y[0]

        # Calculate slip
        speed_rpm = omega_m * 60 / (2 * np.pi)
        slip = self.calculate_slip(speed_rpm)

        # Calculate electromagnetic torque
        T_em, _, _ = self.calculate_torque_steady_state(slip)

        # Equation of motion: J * domega/dt = T_em - T_load - B*omega
        domega_dt = (T_em - T_load - self.B * omega_m) / self.J
        dtheta_dt = omega_m

        return [domega_dt, dtheta_dt]


class MotorSimulator:
    """Dynamic motor simulator with multiple ODE solver options"""

    def __init__(self, motor_model):
        self.motor = motor_model
        self.time = []
        self.speed = []
        self.torque = []
        self.current_a = []
        self.current_b = []
        self.current_c = []
        self.slip_history = []
        self.is_running = False
        self.solver_type = "RK45"

    def reset(self):
        """Reset simulation data"""
        self.time = []
        self.speed = []
        self.torque = []
        self.current_a = []
        self.current_b = []
        self.current_c = []
        self.slip_history = []

    def euler_step(self, t, y, dt, T_load):
        """Single Euler integration step"""
        dydt = self.motor.motor_dynamics(t, y, T_load)
        y_new = [y[i] + dydt[i] * dt for i in range(len(y))]
        return y_new

    def rk45_step(self, t, y, dt, T_load):
        """Single RK45 (4th order Runge-Kutta) step"""
        k1 = self.motor.motor_dynamics(t, y, T_load)

        y2 = [y[i] + 0.5 * dt * k1[i] for i in range(len(y))]
        k2 = self.motor.motor_dynamics(t + 0.5 * dt, y2, T_load)

        y3 = [y[i] + 0.5 * dt * k2[i] for i in range(len(y))]
        k3 = self.motor.motor_dynamics(t + 0.5 * dt, y3, T_load)

        y4 = [y[i] + dt * k3[i] for i in range(len(y))]
        k4 = self.motor.motor_dynamics(t + dt, y4, T_load)

        y_new = [y[i] + (dt / 6) * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i]) for i in range(len(y))]
        return y_new

    def simulate_transient(self, initial_speed_rpm, T_load, t_span, dt=0.001):
        """Simulate motor transient response"""
        self.reset()

        # Initial conditions
        omega_0 = initial_speed_rpm * 2 * np.pi / 60  # Convert to rad/s
        y0 = [omega_0, 0]  # [omega_m, theta_m]

        t_start, t_end = t_span
        t_current = t_start
        y_current = y0

        while t_current < t_end:
            # Store current values
            speed_rpm = y_current[0] * 60 / (2 * np.pi)
            slip = self.motor.calculate_slip(speed_rpm)
            T_em, _, _ = self.motor.calculate_torque_steady_state(slip)
            I_a, I_b, I_c, _, _ = self.motor.calculate_currents(slip)

            self.time.append(t_current)
            self.speed.append(speed_rpm)
            self.torque.append(T_em)
            self.current_a.append(abs(I_a))
            self.current_b.append(abs(I_b))
            self.current_c.append(abs(I_c))
            self.slip_history.append(slip)

            # Integration step
            if self.solver_type == "RK45":
                y_current = self.rk45_step(t_current, y_current, dt, T_load)
            else:  # Euler
                y_current = self.euler_step(t_current, y_current, dt, T_load)

            t_current += dt

        return self.time, self.speed, self.torque


class MotorAnalysisGUI:
    """Advanced Tkinter GUI for motor analysis"""

    def __init__(self, root):
        self.root = root
        self.root.title("Wound-Rotor Induction Motor Analysis Lab - Example 6.2")
        self.root.geometry("1400x900")

        # Motor model and simulator
        self.motor = InductionMotorModel()
        self.simulator = MotorSimulator(self.motor)

        # Animation control
        self.is_simulating = False
        self.anim = None

        # Setup GUI
        self.setup_styles()
        self.create_menu()
        self.create_main_layout()

        # Bind resize event for auto-scaling
        self.root.bind('<Configure>', self.on_window_resize)

        # Initial calculation
        self.calculate_steady_state()

    def setup_styles(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'), foreground='#34495e')
        style.configure('Info.TLabel', font=('Arial', 10), foreground='#2c3e50')
        style.configure('Value.TLabel', font=('Arial', 10, 'bold'), foreground='#27ae60')

        style.configure('Start.TButton', font=('Arial', 10, 'bold'), foreground='green')
        style.configure('Stop.TButton', font=('Arial', 10, 'bold'), foreground='red')
        style.configure('Reset.TButton', font=('Arial', 10, 'bold'), foreground='blue')

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Reset All", command=self.reset_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Steady State Analysis", command=self.calculate_steady_state)
        analysis_menu.add_command(label="Start Dynamic Simulation", command=self.start_simulation)
        analysis_menu.add_command(label="Stop Simulation", command=self.stop_simulation)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_layout(self):
        """Create main GUI layout with tabs"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Steady State Analysis
        self.tab_steady = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_steady, text="Steady State Analysis")
        self.create_steady_state_tab()

        # Tab 2: Dynamic Simulation
        self.tab_dynamic = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dynamic, text="Dynamic Simulation")
        self.create_dynamic_simulation_tab()

        # Tab 3: Voltage Analysis
        self.tab_voltage = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_voltage, text="Voltage Analysis")
        self.create_voltage_analysis_tab()

    def create_steady_state_tab(self):
        """Create steady state analysis tab"""
        # Left panel - Input parameters
        left_frame = ttk.LabelFrame(self.tab_steady, text="Input Parameters", padding=10)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Voltage inputs
        ttk.Label(left_frame, text="Unbalanced Line Voltages:", style='Header.TLabel').grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(left_frame, text="V_ab (V):", style='Info.TLabel').grid(row=1, column=0, sticky='w', pady=2)
        self.v_ab_var = tk.DoubleVar(value=450)
        self.v_ab_slider = ttk.Scale(left_frame, from_=400, to=500, variable=self.v_ab_var, orient=tk.HORIZONTAL, length=200, command=self.on_parameter_change)
        self.v_ab_slider.grid(row=1, column=1, pady=2)
        self.v_ab_label = ttk.Label(left_frame, text="450.0 V", style='Value.TLabel')
        self.v_ab_label.grid(row=1, column=2, padx=5)

        ttk.Label(left_frame, text="V_bc (V):", style='Info.TLabel').grid(row=2, column=0, sticky='w', pady=2)
        self.v_bc_var = tk.DoubleVar(value=470)
        self.v_bc_slider = ttk.Scale(left_frame, from_=400, to=500, variable=self.v_bc_var, orient=tk.HORIZONTAL, length=200, command=self.on_parameter_change)
        self.v_bc_slider.grid(row=2, column=1, pady=2)
        self.v_bc_label = ttk.Label(left_frame, text="470.0 V", style='Value.TLabel')
        self.v_bc_label.grid(row=2, column=2, padx=5)

        ttk.Label(left_frame, text="V_ca (V):", style='Info.TLabel').grid(row=3, column=0, sticky='w', pady=2)
        self.v_ca_var = tk.DoubleVar(value=440)
        self.v_ca_slider = ttk.Scale(left_frame, from_=400, to=500, variable=self.v_ca_var, orient=tk.HORIZONTAL, length=200, command=self.on_parameter_change)
        self.v_ca_slider.grid(row=3, column=1, pady=2)
        self.v_ca_label = ttk.Label(left_frame, text="440.0 V", style='Value.TLabel')
        self.v_ca_label.grid(row=3, column=2, padx=5)

        # Operating speed
        ttk.Label(left_frame, text="\nOperating Conditions:", style='Header.TLabel').grid(row=4, column=0, columnspan=2, pady=5)

        ttk.Label(left_frame, text="Speed (rpm):", style='Info.TLabel').grid(row=5, column=0, sticky='w', pady=2)
        self.speed_var = tk.DoubleVar(value=1770)
        self.speed_slider = ttk.Scale(left_frame, from_=0, to=1800, variable=self.speed_var, orient=tk.HORIZONTAL, length=200, command=self.on_parameter_change)
        self.speed_slider.grid(row=5, column=1, pady=2)
        self.speed_label = ttk.Label(left_frame, text="1770.0 rpm", style='Value.TLabel')
        self.speed_label.grid(row=5, column=2, padx=5)

        # Load torque
        ttk.Label(left_frame, text="Load Torque (N·m):", style='Info.TLabel').grid(row=6, column=0, sticky='w', pady=2)
        self.load_var = tk.DoubleVar(value=0)
        self.load_slider = ttk.Scale(left_frame, from_=0, to=1000, variable=self.load_var, orient=tk.HORIZONTAL, length=200, command=self.on_parameter_change)
        self.load_slider.grid(row=6, column=1, pady=2)
        self.load_label = ttk.Label(left_frame, text="0.0 N·m", style='Value.TLabel')
        self.load_label.grid(row=6, column=2, padx=5)

        # Calculate button
        ttk.Button(left_frame, text="Calculate", command=self.calculate_steady_state).grid(row=7, column=0, columnspan=3, pady=10)

        # Right panel - Results
        right_frame = ttk.LabelFrame(self.tab_steady, text="Results", padding=10)
        right_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        # Results text widget
        self.results_text = tk.Text(right_frame, width=60, height=30, font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(right_frame, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)

        # Configure grid weights for resizing
        self.tab_steady.grid_rowconfigure(0, weight=1)
        self.tab_steady.grid_columnconfigure(0, weight=1)
        self.tab_steady.grid_columnconfigure(1, weight=2)

    def create_dynamic_simulation_tab(self):
        """Create dynamic simulation tab"""
        # Control panel
        control_frame = ttk.LabelFrame(self.tab_dynamic, text="Simulation Controls", padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Solver selection
        ttk.Label(control_frame, text="ODE Solver:", style='Info.TLabel').grid(row=0, column=0, sticky='w', padx=5)
        self.solver_var = tk.StringVar(value="RK45")
        solver_combo = ttk.Combobox(control_frame, textvariable=self.solver_var, values=["RK45", "Euler"], state='readonly', width=10)
        solver_combo.grid(row=0, column=1, padx=5)
        solver_combo.bind('<<ComboboxSelected>>', self.on_solver_change)

        # Simulation time
        ttk.Label(control_frame, text="Sim Time (s):", style='Info.TLabel').grid(row=0, column=2, sticky='w', padx=5)
        self.sim_time_var = tk.DoubleVar(value=2.0)
        sim_time_entry = ttk.Entry(control_frame, textvariable=self.sim_time_var, width=10)
        sim_time_entry.grid(row=0, column=3, padx=5)

        # Initial speed
        ttk.Label(control_frame, text="Initial Speed (rpm):", style='Info.TLabel').grid(row=0, column=4, sticky='w', padx=5)
        self.init_speed_var = tk.DoubleVar(value=0)
        init_speed_entry = ttk.Entry(control_frame, textvariable=self.init_speed_var, width=10)
        init_speed_entry.grid(row=0, column=5, padx=5)

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=1, column=0, columnspan=6, pady=10)

        self.start_btn = ttk.Button(button_frame, text="▶ Start", style='Start.TButton', command=self.start_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="⬛ Stop", style='Stop.TButton', command=self.stop_simulation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = ttk.Button(button_frame, text="⟲ Reset", style='Reset.TButton', command=self.reset_simulation)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # Plots frame
        plots_frame = ttk.Frame(self.tab_dynamic)
        plots_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.fig_dynamic = Figure(figsize=(12, 8), dpi=100)

        # Subplots
        self.ax_speed = self.fig_dynamic.add_subplot(3, 1, 1)
        self.ax_torque = self.fig_dynamic.add_subplot(3, 1, 2)
        self.ax_current = self.fig_dynamic.add_subplot(3, 1, 3)

        self.fig_dynamic.tight_layout(pad=3.0)

        # Canvas
        self.canvas_dynamic = FigureCanvasTkAgg(self.fig_dynamic, master=plots_frame)
        self.canvas_dynamic.draw()
        self.canvas_dynamic.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_voltage_analysis_tab(self):
        """Create voltage analysis tab"""
        # Analysis frame
        analysis_frame = ttk.LabelFrame(self.tab_voltage, text="Symmetrical Components Analysis", padding=10)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create matplotlib figure for phasor diagram
        self.fig_voltage = Figure(figsize=(10, 8), dpi=100)

        # Subplots
        self.ax_phasor = self.fig_voltage.add_subplot(2, 2, 1, projection='polar')
        self.ax_seq = self.fig_voltage.add_subplot(2, 2, 2)
        self.ax_line_volt = self.fig_voltage.add_subplot(2, 2, 3)
        self.ax_phase_volt = self.fig_voltage.add_subplot(2, 2, 4)

        self.fig_voltage.tight_layout(pad=3.0)

        # Canvas
        canvas_voltage = FigureCanvasTkAgg(self.fig_voltage, master=analysis_frame)
        canvas_voltage.draw()
        canvas_voltage.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Update voltage analysis
        self.update_voltage_analysis()

    def on_parameter_change(self, event=None):
        """Handle parameter slider changes"""
        self.v_ab_label.config(text=f"{self.v_ab_var.get():.1f} V")
        self.v_bc_label.config(text=f"{self.v_bc_var.get():.1f} V")
        self.v_ca_label.config(text=f"{self.v_ca_var.get():.1f} V")
        self.speed_label.config(text=f"{self.speed_var.get():.1f} rpm")
        self.load_label.config(text=f"{self.load_var.get():.1f} N·m")

        # Update motor parameters
        self.motor.V_ab = self.v_ab_var.get()
        self.motor.V_bc = self.v_bc_var.get()
        self.motor.V_ca = self.v_ca_var.get()
        self.motor.current_speed = self.speed_var.get()
        self.motor.T_load = self.load_var.get()

        # Auto-update voltage analysis if on that tab
        if self.notebook.index(self.notebook.select()) == 2:
            self.update_voltage_analysis()

    def on_solver_change(self, event=None):
        """Handle solver selection change"""
        self.simulator.solver_type = self.solver_var.get()

    def calculate_steady_state(self):
        """Calculate and display steady state results"""
        # Update parameters
        self.motor.V_ab = self.v_ab_var.get()
        self.motor.V_bc = self.v_bc_var.get()
        self.motor.V_ca = self.v_ca_var.get()
        speed_rpm = self.speed_var.get()

        # Calculate slip
        slip = self.motor.calculate_slip(speed_rpm)

        # Calculate torques
        T_total, T_pos, T_neg = self.motor.calculate_torque_steady_state(slip)

        # Calculate currents
        I_a, I_b, I_c, I1_pos, I1_neg = self.motor.calculate_currents(slip)

        # Calculate power and efficiency
        P_in, P_out, P_cu_s, P_cu_r, P_fw, eff = self.motor.calculate_power_and_efficiency(slip, speed_rpm)

        # Symmetrical components
        V_pos, V_neg, V_zero = self.motor.symmetrical_components()

        # Display results
        results = f"""
{'='*70}
    WOUND-ROTOR INDUCTION MOTOR ANALYSIS - EXAMPLE 6.2
    Unbalanced Three-Phase Operation
{'='*70}

MOTOR SPECIFICATIONS:
  Rated Power:        {self.motor.rated_power/746:.1f} hp ({self.motor.rated_power:.0f} W)
  Rated Voltage:      {self.motor.rated_voltage} V
  Number of Poles:    {self.motor.P}
  Frequency:          {self.motor.f} Hz
  Synchronous Speed:  {self.motor.n_sync:.0f} rpm

UNBALANCED LINE VOLTAGES:
  V_ab = {self.motor.V_ab:.1f} V
  V_bc = {self.motor.V_bc:.1f} V
  V_ca = {self.motor.V_ca:.1f} V

  Average Line Voltage: {(self.motor.V_ab + self.motor.V_bc + self.motor.V_ca)/3:.2f} V
  Voltage Unbalance Factor: {self.calculate_voltage_unbalance():.2f}%

SYMMETRICAL COMPONENTS:
  Positive Sequence:  {abs(V_pos):.2f} ∠ {np.angle(V_pos, deg=True):.2f}° V
  Negative Sequence:  {abs(V_neg):.2f} ∠ {np.angle(V_neg, deg=True):.2f}° V
  Zero Sequence:      {abs(V_zero):.2f} ∠ {np.angle(V_zero, deg=True):.2f}° V

  % Negative Sequence: {(abs(V_neg)/abs(V_pos))*100:.2f}%

OPERATING CONDITIONS:
  Speed:              {speed_rpm:.1f} rpm
  Slip:               {slip:.6f} ({slip*100:.3f}%)
  Frequency (rotor):  {slip * self.motor.f:.3f} Hz

PHASE CURRENTS:
  I_a = {abs(I_a):.2f} ∠ {np.angle(I_a, deg=True):.2f}° A (RMS)
  I_b = {abs(I_b):.2f} ∠ {np.angle(I_b, deg=True):.2f}° A (RMS)
  I_c = {abs(I_c):.2f} ∠ {np.angle(I_c, deg=True):.2f}° A (RMS)

  Average Current:    {(abs(I_a) + abs(I_b) + abs(I_c))/3:.2f} A
  Max Current:        {max(abs(I_a), abs(I_b), abs(I_c)):.2f} A
  Current Unbalance:  {self.calculate_current_unbalance(I_a, I_b, I_c):.2f}%

SEQUENCE CURRENTS:
  Positive Sequence:  {abs(I1_pos):.2f} ∠ {np.angle(I1_pos, deg=True):.2f}° A
  Negative Sequence:  {abs(I1_neg):.2f} ∠ {np.angle(I1_neg, deg=True):.2f}° A

ELECTROMAGNETIC TORQUE:
  Positive Sequence Torque:  {T_pos:.2f} N·m
  Negative Sequence Torque:  {T_neg:.2f} N·m
  Total Torque:              {T_total:.2f} N·m

  Torque (lb-ft):            {T_total * 0.73756:.2f} lb-ft

POWER ANALYSIS:
  Input Power:               {P_in:.2f} W ({P_in/746:.2f} hp)
  Output Power:              {P_out:.2f} W ({P_out/746:.2f} hp)

  Stator Copper Loss:        {P_cu_s:.2f} W
  Rotor Copper Loss:         {P_cu_r:.2f} W
  Friction & Windage:        {P_fw:.2f} W
  Total Losses:              {P_cu_s + P_cu_r + P_fw:.2f} W

  Efficiency:                {eff:.2f}%

EQUIVALENT CIRCUIT PARAMETERS:
  R1 (stator resistance):    {self.motor.R1:.4f} Ω
  X1 (stator reactance):     {self.motor.X1:.4f} Ω
  R2 (rotor resistance):     {self.motor.R2:.4f} Ω
  X2 (rotor reactance):      {self.motor.X2:.4f} Ω
  Xm (magnetizing):          {self.motor.Xm:.4f} Ω

PERFORMANCE METRICS:
  Power Factor:              {np.cos(np.angle(I_a)):.3f}
  Torque/Ampere:            {T_total/abs(I_a):.3f} N·m/A
  Specific Loading:          {abs(I_a)/self.motor.rated_power*1000:.3f} A/kW

{'='*70}
"""

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, results)

    def calculate_voltage_unbalance(self):
        """Calculate voltage unbalance factor"""
        avg = (self.motor.V_ab + self.motor.V_bc + self.motor.V_ca) / 3
        max_dev = max(abs(self.motor.V_ab - avg), abs(self.motor.V_bc - avg), abs(self.motor.V_ca - avg))
        return (max_dev / avg) * 100

    def calculate_current_unbalance(self, I_a, I_b, I_c):
        """Calculate current unbalance factor"""
        avg = (abs(I_a) + abs(I_b) + abs(I_c)) / 3
        max_dev = max(abs(abs(I_a) - avg), abs(abs(I_b) - avg), abs(abs(I_c) - avg))
        return (max_dev / avg) * 100

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.is_simulating:
            return

        self.is_simulating = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # Get simulation parameters
        initial_speed = self.init_speed_var.get()
        t_end = self.sim_time_var.get()
        T_load = self.load_var.get()

        # Run simulation
        self.simulator.simulate_transient(initial_speed, T_load, (0, t_end), dt=0.001)

        # Plot results
        self.plot_dynamic_results()

        self.is_simulating = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def stop_simulation(self):
        """Stop dynamic simulation"""
        self.is_simulating = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def reset_simulation(self):
        """Reset simulation"""
        self.simulator.reset()
        self.init_speed_var.set(0)
        self.sim_time_var.set(2.0)

        # Clear plots
        self.ax_speed.clear()
        self.ax_torque.clear()
        self.ax_current.clear()
        self.canvas_dynamic.draw()

    def plot_dynamic_results(self):
        """Plot dynamic simulation results"""
        # Clear previous plots
        self.ax_speed.clear()
        self.ax_torque.clear()
        self.ax_current.clear()

        # Speed plot
        self.ax_speed.plot(self.simulator.time, self.simulator.speed, 'b-', linewidth=2, label='Speed')
        self.ax_speed.axhline(y=self.motor.n_sync, color='r', linestyle='--', label=f'Sync Speed ({self.motor.n_sync:.0f} rpm)')
        self.ax_speed.set_xlabel('Time (s)')
        self.ax_speed.set_ylabel('Speed (rpm)')
        self.ax_speed.set_title('Motor Speed vs Time')
        self.ax_speed.grid(True, alpha=0.3)
        self.ax_speed.legend()

        # Torque plot
        self.ax_torque.plot(self.simulator.time, self.simulator.torque, 'g-', linewidth=2, label='Electromagnetic Torque')
        if self.load_var.get() > 0:
            self.ax_torque.axhline(y=self.load_var.get(), color='r', linestyle='--', label=f'Load Torque ({self.load_var.get():.1f} N·m)')
        self.ax_torque.set_xlabel('Time (s)')
        self.ax_torque.set_ylabel('Torque (N·m)')
        self.ax_torque.set_title('Electromagnetic Torque vs Time')
        self.ax_torque.grid(True, alpha=0.3)
        self.ax_torque.legend()

        # Current plot
        self.ax_current.plot(self.simulator.time, self.simulator.current_a, 'r-', linewidth=1.5, label='I_a', alpha=0.7)
        self.ax_current.plot(self.simulator.time, self.simulator.current_b, 'g-', linewidth=1.5, label='I_b', alpha=0.7)
        self.ax_current.plot(self.simulator.time, self.simulator.current_c, 'b-', linewidth=1.5, label='I_c', alpha=0.7)
        self.ax_current.set_xlabel('Time (s)')
        self.ax_current.set_ylabel('Current (A)')
        self.ax_current.set_title('Phase Currents vs Time (Unbalanced)')
        self.ax_current.grid(True, alpha=0.3)
        self.ax_current.legend()

        self.fig_dynamic.tight_layout(pad=3.0)
        self.canvas_dynamic.draw()

    def update_voltage_analysis(self):
        """Update voltage analysis plots"""
        # Get symmetrical components
        V_pos, V_neg, V_zero = self.motor.symmetrical_components()
        V_an, V_bn, V_cn = self.motor.phase_voltages_from_line()

        # Clear plots
        self.ax_phasor.clear()
        self.ax_seq.clear()
        self.ax_line_volt.clear()
        self.ax_phase_volt.clear()

        # Phasor diagram
        self.ax_phasor.set_title('Phase Voltage Phasor Diagram')

        # Plot phase voltages
        angles_phase = [np.angle(V_an), np.angle(V_bn), np.angle(V_cn)]
        magnitudes_phase = [abs(V_an), abs(V_bn), abs(V_cn)]
        colors_phase = ['r', 'g', 'b']
        labels_phase = ['V_an', 'V_bn', 'V_cn']

        for angle, mag, color, label in zip(angles_phase, magnitudes_phase, colors_phase, labels_phase):
            self.ax_phasor.arrow(0, 0, angle, mag, head_width=0.1, head_length=5, fc=color, ec=color, linewidth=2, label=label, alpha=0.7)

        self.ax_phasor.set_ylim(0, max(magnitudes_phase) * 1.2)
        self.ax_phasor.legend(loc='upper right')
        self.ax_phasor.grid(True, alpha=0.3)

        # Sequence components bar chart
        seq_labels = ['Positive', 'Negative', 'Zero']
        seq_magnitudes = [abs(V_pos), abs(V_neg), abs(V_zero)]
        seq_colors = ['green', 'red', 'gray']

        bars = self.ax_seq.bar(seq_labels, seq_magnitudes, color=seq_colors, alpha=0.7, edgecolor='black')
        self.ax_seq.set_ylabel('Voltage (V)')
        self.ax_seq.set_title('Symmetrical Components')
        self.ax_seq.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            self.ax_seq.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.2f}V',
                           ha='center', va='bottom', fontweight='bold')

        # Line voltages bar chart
        line_labels = ['V_ab', 'V_bc', 'V_ca']
        line_voltages = [self.motor.V_ab, self.motor.V_bc, self.motor.V_ca]
        line_colors = ['#e74c3c', '#3498db', '#f39c12']

        bars2 = self.ax_line_volt.bar(line_labels, line_voltages, color=line_colors, alpha=0.7, edgecolor='black')
        self.ax_line_volt.set_ylabel('Voltage (V)')
        self.ax_line_volt.set_title('Line Voltages (Unbalanced)')
        self.ax_line_volt.axhline(y=np.mean(line_voltages), color='black', linestyle='--', label='Average', linewidth=2)
        self.ax_line_volt.grid(True, alpha=0.3, axis='y')
        self.ax_line_volt.legend()

        # Add value labels
        for bar in bars2:
            height = bar.get_height()
            self.ax_line_volt.text(bar.get_x() + bar.get_width()/2., height,
                                  f'{height:.1f}V',
                                  ha='center', va='bottom', fontweight='bold')

        # Phase voltages bar chart
        phase_labels = ['V_an', 'V_bn', 'V_cn']
        phase_magnitudes = [abs(V_an), abs(V_bn), abs(V_cn)]
        phase_colors = ['#c0392b', '#27ae60', '#2980b9']

        bars3 = self.ax_phase_volt.bar(phase_labels, phase_magnitudes, color=phase_colors, alpha=0.7, edgecolor='black')
        self.ax_phase_volt.set_ylabel('Voltage (V)')
        self.ax_phase_volt.set_title('Phase Voltages (Calculated)')
        self.ax_phase_volt.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for bar in bars3:
            height = bar.get_height()
            self.ax_phase_volt.text(bar.get_x() + bar.get_width()/2., height,
                                   f'{height:.2f}V',
                                   ha='center', va='bottom', fontweight='bold')

        self.fig_voltage.tight_layout(pad=3.0)

    def on_window_resize(self, event=None):
        """Handle window resize for auto-scaling"""
        # This is called on window resize - matplotlib handles auto-scaling
        pass

    def reset_all(self):
        """Reset all parameters to default"""
        self.v_ab_var.set(450)
        self.v_bc_var.set(470)
        self.v_ca_var.set(440)
        self.speed_var.set(1770)
        self.load_var.set(0)
        self.init_speed_var.set(0)
        self.sim_time_var.set(2.0)
        self.solver_var.set("RK45")

        self.on_parameter_change()
        self.reset_simulation()
        self.calculate_steady_state()
        self.update_voltage_analysis()

    def show_about(self):
        """Show about dialog"""
        about_text = """
Wound-Rotor Induction Motor Analysis Lab
Example 6.2: Unbalanced Three-Phase Operation

Features:
• Steady-state analysis with unbalanced voltages
• Symmetrical components method
• Dynamic simulation with ODE solvers (RK45, Euler)
• Real-time visualization
• Interactive parameter adjustment
• Auto-scaling responsive GUI

Motor Specifications:
• 460V / 100hp Wound-Rotor Induction Motor
• 6-pole, 60 Hz
• Running at 1770 rpm with rotor shorted

Developed for Electrical Engineering Education
        """
        messagebox.showinfo("About", about_text)


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = MotorAnalysisGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
