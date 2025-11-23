"""
Advanced Voltage and Current Regulator Analysis Lab
Electrical Engineering Simulation Tool
Includes LM317 Voltage Regulator and 7812 Current Regulator Analysis
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.integrate import ode
import math


class VoltageRegulatorLab:
    """Comprehensive Voltage and Current Regulator Analysis and Simulation"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Voltage & Current Regulator Analysis Lab")
        self.root.geometry("1400x900")

        # Simulation state
        self.simulation_running = False
        self.simulation_paused = False
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.power_data = []
        self.efficiency_data = []

        # Default parameters for LM317
        self.v_ref = tk.DoubleVar(value=1.25)  # LM317 reference voltage
        self.r1 = tk.DoubleVar(value=220)  # R1 in ohms
        self.r2 = tk.DoubleVar(value=2000)  # R2 in ohms
        self.i_adj = tk.DoubleVar(value=50e-6)  # Adjustment current in A
        self.v_in = tk.DoubleVar(value=35)  # Input voltage

        # Parameters for 7812 Current Regulator
        self.v_reg = tk.DoubleVar(value=12)  # 7812 regulated voltage
        self.i_desired = tk.DoubleVar(value=1.0)  # Desired current in A
        self.r_sense = tk.DoubleVar(value=12)  # Sense resistor

        # Load parameters
        self.r_load = tk.DoubleVar(value=100)  # Load resistance
        self.c_load = tk.DoubleVar(value=100e-6)  # Load capacitance
        self.l_series = tk.DoubleVar(value=1e-3)  # Series inductance

        # Simulation parameters
        self.sim_method = tk.StringVar(value="RK45")
        self.sim_time = tk.DoubleVar(value=0.1)  # Total simulation time
        self.dt = 0.0001  # Time step

        # Current mode selection
        self.mode = tk.StringVar(value="LM317")

        # Setup UI
        self.setup_ui()

        # Bind resize event
        self.root.bind('<Configure>', self.on_resize)

    def setup_ui(self):
        """Setup the user interface"""
        # Create main container with grid
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure grid weights for responsive layout
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)

        # Title
        title_frame = ttk.Frame(self.main_container)
        title_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=5)

        title_label = ttk.Label(title_frame,
                               text="Advanced Voltage & Current Regulator Analysis Lab",
                               font=('Arial', 16, 'bold'))
        title_label.pack()

        # Left panel container with scrollbar
        left_container = ttk.Frame(self.main_container)
        left_container.grid(row=1, column=0, sticky='nsew', padx=5)

        # Create canvas and scrollbar for left panel
        self.left_canvas = tk.Canvas(left_container, width=400)
        left_scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=self.left_canvas.yview)

        # Scrollable frame inside canvas
        self.left_panel = ttk.Frame(self.left_canvas)

        # Configure canvas
        self.left_canvas.configure(yscrollcommand=left_scrollbar.set)

        # Pack scrollbar and canvas
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create window in canvas
        self.canvas_frame = self.left_canvas.create_window((0, 0), window=self.left_panel, anchor='nw')

        # Update scrollregion when frame changes size
        self.left_panel.bind('<Configure>', lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all")))

        # Bind mousewheel to scrolling (both Windows and Linux)
        self.left_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.left_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.left_canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Right panel - Visualization
        self.right_panel = ttk.Frame(self.main_container)
        self.right_panel.grid(row=1, column=1, sticky='nsew', padx=5)
        self.main_container.grid_columnconfigure(1, weight=1)

        self.setup_control_panel()
        self.setup_visualization_panel()

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling for both Windows and Linux"""
        if event.num == 5 or event.delta == -120:
            self.left_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:
            self.left_canvas.yview_scroll(-1, "units")
        else:
            self.left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def setup_control_panel(self):
        """Setup control panel with inputs and sliders"""
        # Mode Selection
        mode_frame = ttk.LabelFrame(self.left_panel, text="Analysis Mode", padding=10)
        mode_frame.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(mode_frame, text="LM317 Voltage Regulator",
                       variable=self.mode, value="LM317",
                       command=self.update_calculations).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="7812 Current Regulator",
                       variable=self.mode, value="7812",
                       command=self.update_calculations).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Dynamic Response Analysis",
                       variable=self.mode, value="Dynamic",
                       command=self.update_calculations).pack(anchor=tk.W)

        # LM317 Parameters
        self.lm317_frame = ttk.LabelFrame(self.left_panel, text="LM317 Parameters", padding=10)
        self.lm317_frame.pack(fill=tk.X, pady=5)

        self.create_slider(self.lm317_frame, "Input Voltage (V):", self.v_in, 5, 40, 0)
        self.create_slider(self.lm317_frame, "R1 (Ω):", self.r1, 100, 500, 1)
        self.create_slider(self.lm317_frame, "R2 (Ω):", self.r2, 100, 10000, 2)
        self.create_slider(self.lm317_frame, "I_ADJ (μA):", self.i_adj, 10e-6, 100e-6, 3, scale=1e6)
        self.create_slider(self.lm317_frame, "V_REF (V):", self.v_ref, 1.2, 1.3, 4)

        # 7812 Parameters
        self.reg7812_frame = ttk.LabelFrame(self.left_panel, text="7812 Current Regulator", padding=10)
        self.reg7812_frame.pack(fill=tk.X, pady=5)

        self.create_slider(self.reg7812_frame, "Desired Current (A):", self.i_desired, 0.1, 2.0, 0)
        self.create_slider(self.reg7812_frame, "V_REG (V):", self.v_reg, 10, 15, 1)

        # Load Parameters
        load_frame = ttk.LabelFrame(self.left_panel, text="Load Parameters", padding=10)
        load_frame.pack(fill=tk.X, pady=5)

        self.create_slider(load_frame, "Load Resistance (Ω):", self.r_load, 1, 1000, 0)
        self.create_slider(load_frame, "Load Capacitance (μF):", self.c_load, 1e-6, 1000e-6, 1, scale=1e6)
        self.create_slider(load_frame, "Series Inductance (mH):", self.l_series, 0.1e-3, 10e-3, 2, scale=1e3)

        # Simulation Parameters
        sim_frame = ttk.LabelFrame(self.left_panel, text="Simulation Settings", padding=10)
        sim_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sim_frame, text="ODE Solver:").grid(row=0, column=0, sticky=tk.W, pady=2)
        solver_combo = ttk.Combobox(sim_frame, textvariable=self.sim_method,
                                    values=["RK45", "Euler", "RK23"], state="readonly", width=15)
        solver_combo.grid(row=0, column=1, pady=2)

        self.create_slider(sim_frame, "Simulation Time (s):", self.sim_time, 0.001, 0.5, 1)

        # Results Display
        self.results_frame = ttk.LabelFrame(self.left_panel, text="Calculation Results", padding=10)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.results_text = tk.Text(self.results_frame, height=15, width=35,
                                    font=('Courier', 9), state='normal')
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for results
        results_scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL,
                                 command=self.results_text.yview)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=results_scrollbar.set)

        # Control Buttons - Prominent section
        button_outer_frame = ttk.LabelFrame(self.left_panel, text="Simulation Controls", padding=10)
        button_outer_frame.pack(fill=tk.X, pady=10, padx=5)

        # Start button (larger and green-styled)
        self.start_btn = tk.Button(button_outer_frame, text="▶ START SIMULATION",
                                   command=self.start_simulation,
                                   bg='#28a745', fg='white', font=('Arial', 11, 'bold'),
                                   relief=tk.RAISED, bd=3, cursor='hand2',
                                   activebackground='#218838', activeforeground='white')
        self.start_btn.pack(fill=tk.X, pady=3)

        # Stop and Reset buttons in same row
        control_row = ttk.Frame(button_outer_frame)
        control_row.pack(fill=tk.X, pady=3)

        self.stop_btn = tk.Button(control_row, text="⏸ STOP",
                                  command=self.stop_simulation,
                                  bg='#ffc107', fg='black', font=('Arial', 10, 'bold'),
                                  relief=tk.RAISED, bd=2, cursor='hand2',
                                  activebackground='#e0a800', activeforeground='black')
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.reset_btn = tk.Button(control_row, text="⟲ RESET",
                                   command=self.reset_simulation,
                                   bg='#dc3545', fg='white', font=('Arial', 10, 'bold'),
                                   relief=tk.RAISED, bd=2, cursor='hand2',
                                   activebackground='#c82333', activeforeground='white')
        self.reset_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_slider(self, parent, label, variable, min_val, max_val, row, scale=1):
        """Create a labeled slider with value display"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)

        slider = ttk.Scale(parent, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                          variable=variable, command=lambda v: self.update_calculations())
        slider.grid(row=row, column=1, sticky='ew', pady=2, padx=5)

        value_label = ttk.Label(parent, text=f"{variable.get()*scale:.2f}")
        value_label.grid(row=row, column=2, sticky=tk.W, pady=2)

        # Update value label when slider changes
        def update_label(val):
            value_label.config(text=f"{float(val)*scale:.2f}")
        slider.config(command=lambda v: (update_label(v), self.update_calculations()))

        parent.grid_columnconfigure(1, weight=1)

    def setup_visualization_panel(self):
        """Setup visualization panel with plots"""
        # Create notebook for multiple tabs
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Voltage Response
        self.voltage_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.voltage_tab, text="Voltage Response")

        self.fig_voltage = Figure(figsize=(8, 6), dpi=100)
        self.ax_voltage = self.fig_voltage.add_subplot(111)
        self.ax_voltage.set_xlabel('Time (s)', fontsize=10)
        self.ax_voltage.set_ylabel('Voltage (V)', fontsize=10)
        self.ax_voltage.set_title('Output Voltage vs Time', fontsize=12, fontweight='bold')
        self.ax_voltage.grid(True, alpha=0.3)

        self.canvas_voltage = FigureCanvasTkAgg(self.fig_voltage, self.voltage_tab)
        self.canvas_voltage.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 2: Current Response
        self.current_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.current_tab, text="Current Response")

        self.fig_current = Figure(figsize=(8, 6), dpi=100)
        self.ax_current = self.fig_current.add_subplot(111)
        self.ax_current.set_xlabel('Time (s)', fontsize=10)
        self.ax_current.set_ylabel('Current (A)', fontsize=10)
        self.ax_current.set_title('Output Current vs Time', fontsize=12, fontweight='bold')
        self.ax_current.grid(True, alpha=0.3)

        self.canvas_current = FigureCanvasTkAgg(self.fig_current, self.current_tab)
        self.canvas_current.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 3: Power and Efficiency
        self.power_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.power_tab, text="Power & Efficiency")

        self.fig_power = Figure(figsize=(8, 6), dpi=100)
        self.ax_power1 = self.fig_power.add_subplot(211)
        self.ax_power2 = self.fig_power.add_subplot(212)

        self.ax_power1.set_xlabel('Time (s)', fontsize=10)
        self.ax_power1.set_ylabel('Power (W)', fontsize=10)
        self.ax_power1.set_title('Power Dissipation', fontsize=11, fontweight='bold')
        self.ax_power1.grid(True, alpha=0.3)

        self.ax_power2.set_xlabel('Time (s)', fontsize=10)
        self.ax_power2.set_ylabel('Efficiency (%)', fontsize=10)
        self.ax_power2.set_title('Regulator Efficiency', fontsize=11, fontweight='bold')
        self.ax_power2.grid(True, alpha=0.3)

        self.fig_power.tight_layout()

        self.canvas_power = FigureCanvasTkAgg(self.fig_power, self.power_tab)
        self.canvas_power.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 4: Characteristics
        self.char_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.char_tab, text="V-I Characteristics")

        self.fig_char = Figure(figsize=(8, 6), dpi=100)
        self.ax_char = self.fig_char.add_subplot(111)
        self.ax_char.set_xlabel('Output Current (A)', fontsize=10)
        self.ax_char.set_ylabel('Output Voltage (V)', fontsize=10)
        self.ax_char.set_title('Voltage Regulator Characteristics', fontsize=12, fontweight='bold')
        self.ax_char.grid(True, alpha=0.3)

        self.canvas_char = FigureCanvasTkAgg(self.fig_char, self.char_tab)
        self.canvas_char.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_calculations(self):
        """Update all calculations based on current parameters"""
        mode = self.mode.get()

        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "=" * 40 + "\n")
        self.results_text.insert(tk.END, f"  {mode} Analysis\n")
        self.results_text.insert(tk.END, "=" * 40 + "\n\n")

        if mode == "LM317":
            self.calculate_lm317()
        elif mode == "7812":
            self.calculate_7812()
        elif mode == "Dynamic":
            self.results_text.insert(tk.END, "Click 'Start Simulation' to run\n")
            self.results_text.insert(tk.END, "dynamic response analysis.\n")

    def calculate_lm317(self):
        """Calculate LM317 voltage regulator parameters (Problem 3)"""
        v_ref = self.v_ref.get()
        r1 = self.r1.get()
        r2 = self.r2.get()
        i_adj = self.i_adj.get()
        v_in = self.v_in.get()

        # LM317 output voltage formula
        # V_out = V_REF * (1 + R2/R1) + I_ADJ * R2

        # Minimum output (R2 = 0)
        v_out_min = v_ref

        # Maximum output (with current R2)
        v_out_max = v_ref * (1 + r2/r1) + i_adj * r2

        # Current output voltage
        v_out = v_out_max

        # Output current calculation
        i_out = (v_in - v_out) / self.r_load.get() if self.r_load.get() > 0 else 0

        # Power calculations
        p_in = v_in * i_out
        p_out = v_out * i_out
        p_dissipated = p_in - p_out
        efficiency = (p_out / p_in * 100) if p_in > 0 else 0

        # Dropout voltage
        v_dropout = v_in - v_out

        # Display results
        self.results_text.insert(tk.END, "Input Parameters:\n")
        self.results_text.insert(tk.END, f"  V_in  = {v_in:.2f} V\n")
        self.results_text.insert(tk.END, f"  V_REF = {v_ref:.3f} V\n")
        self.results_text.insert(tk.END, f"  R1    = {r1:.0f} Ω\n")
        self.results_text.insert(tk.END, f"  R2    = {r2:.0f} Ω\n")
        self.results_text.insert(tk.END, f"  I_ADJ = {i_adj*1e6:.1f} μA\n")
        self.results_text.insert(tk.END, f"  R_L   = {self.r_load.get():.1f} Ω\n\n")

        self.results_text.insert(tk.END, "Output Results:\n")
        self.results_text.insert(tk.END, f"  V_out (min) = {v_out_min:.3f} V\n")
        self.results_text.insert(tk.END, f"  V_out (max) = {v_out_max:.3f} V\n")
        self.results_text.insert(tk.END, f"  V_out (current) = {v_out:.3f} V\n")
        self.results_text.insert(tk.END, f"  I_out = {i_out*1000:.2f} mA\n\n")

        self.results_text.insert(tk.END, "Power Analysis:\n")
        self.results_text.insert(tk.END, f"  P_in   = {p_in:.3f} W\n")
        self.results_text.insert(tk.END, f"  P_out  = {p_out:.3f} W\n")
        self.results_text.insert(tk.END, f"  P_loss = {p_dissipated:.3f} W\n")
        self.results_text.insert(tk.END, f"  η      = {efficiency:.2f} %\n\n")

        self.results_text.insert(tk.END, "Additional Info:\n")
        self.results_text.insert(tk.END, f"  Dropout V = {v_dropout:.2f} V\n")

        # Problem 3 specific answer
        if abs(r1 - 220) < 1 and abs(r2 - 2000) < 1:
            self.results_text.insert(tk.END, f"\n{'='*40}\n")
            self.results_text.insert(tk.END, "Problem 3 Solution:\n")
            self.results_text.insert(tk.END, f"  Min V_out = {v_out_min:.2f} V\n")
            self.results_text.insert(tk.END, f"  Max V_out = {v_out_max:.2f} V\n")
            self.results_text.insert(tk.END, f"{'='*40}\n")

        # Plot V-I characteristics
        self.plot_vi_characteristics()

    def calculate_7812(self):
        """Calculate 7812 current regulator parameters (Problem 4)"""
        v_reg = self.v_reg.get()
        i_desired = self.i_desired.get()

        # For 7812 current regulator: I = V_REG / R1
        # Therefore: R1 = V_REG / I
        r1_required = v_reg / i_desired if i_desired > 0 else 0

        # Actual current with current R_sense
        r_sense = self.r_sense.get()
        i_actual = v_reg / r_sense if r_sense > 0 else 0

        # Power dissipation in sense resistor
        p_sense = i_actual ** 2 * r_sense

        # Load voltage (assuming simple model)
        v_load = i_actual * self.r_load.get()

        # Total power
        p_out = v_load * i_actual

        self.results_text.insert(tk.END, "Input Parameters:\n")
        self.results_text.insert(tk.END, f"  V_REG (7812) = {v_reg:.1f} V\n")
        self.results_text.insert(tk.END, f"  I_desired    = {i_desired:.3f} A\n")
        self.results_text.insert(tk.END, f"  R_sense      = {r_sense:.2f} Ω\n")
        self.results_text.insert(tk.END, f"  R_load       = {self.r_load.get():.1f} Ω\n\n")

        self.results_text.insert(tk.END, "Design Results:\n")
        self.results_text.insert(tk.END, f"  R1 required  = {r1_required:.2f} Ω\n")
        self.results_text.insert(tk.END, f"  I_actual     = {i_actual:.3f} A\n")
        self.results_text.insert(tk.END, f"  I_error      = {abs(i_actual-i_desired)*1000:.1f} mA\n\n")

        self.results_text.insert(tk.END, "Power Analysis:\n")
        self.results_text.insert(tk.END, f"  P_sense = {p_sense:.3f} W\n")
        self.results_text.insert(tk.END, f"  P_load  = {p_out:.3f} W\n")
        self.results_text.insert(tk.END, f"  V_load  = {v_load:.2f} V\n\n")

        # Problem 4 specific answer
        if abs(i_desired - 1.0) < 0.01:
            self.results_text.insert(tk.END, f"{'='*40}\n")
            self.results_text.insert(tk.END, "Problem 4 Solution:\n")
            self.results_text.insert(tk.END, f"  R1 = {r1_required:.0f} Ω\n")
            self.results_text.insert(tk.END, f"  (for I = {i_desired:.1f} A)\n")
            self.results_text.insert(tk.END, f"{'='*40}\n")

        # Update R_sense to match required value
        self.r_sense.set(r1_required)

    def plot_vi_characteristics(self):
        """Plot voltage-current characteristics"""
        v_ref = self.v_ref.get()
        r1 = self.r1.get()
        r2 = self.r2.get()
        i_adj = self.i_adj.get()
        v_in = self.v_in.get()

        # Calculate V_out for this configuration
        v_out_ideal = v_ref * (1 + r2/r1) + i_adj * r2

        # Simulate load regulation (output voltage vs current)
        i_load = np.linspace(0, 2, 100)  # 0 to 2A

        # Simple model: V_out drops slightly with increasing current
        # due to internal resistance and dropout
        r_internal = 0.5  # Internal resistance in ohms
        v_dropout_min = 2  # Minimum dropout voltage

        v_out = []
        for i in i_load:
            v_drop = i * r_internal
            v_o = v_out_ideal - v_drop
            # Check dropout condition
            if (v_in - v_o) < v_dropout_min:
                v_o = v_in - v_dropout_min
            v_out.append(max(0, v_o))

        self.ax_char.clear()
        self.ax_char.plot(i_load, v_out, 'b-', linewidth=2, label='Load Regulation')
        self.ax_char.axhline(y=v_out_ideal, color='r', linestyle='--',
                            label=f'Ideal V_out = {v_out_ideal:.2f}V')
        self.ax_char.set_xlabel('Output Current (A)', fontsize=10)
        self.ax_char.set_ylabel('Output Voltage (V)', fontsize=10)
        self.ax_char.set_title('LM317 Load Regulation Curve', fontsize=12, fontweight='bold')
        self.ax_char.grid(True, alpha=0.3)
        self.ax_char.legend()
        self.canvas_char.draw()

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.simulation_running:
            messagebox.showwarning("Warning", "Simulation already running!")
            return

        self.simulation_running = True
        self.simulation_paused = False

        # Reset data
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.power_data = []
        self.efficiency_data = []

        # Run simulation based on selected method
        method = self.sim_method.get()

        if method == "RK45":
            self.simulate_rk45()
        elif method == "Euler":
            self.simulate_euler()
        elif method == "RK23":
            self.simulate_rk23()

        self.simulation_running = False

    def simulate_euler(self):
        """Simulate using Euler method"""
        # Initial conditions
        t = 0
        v_c = 0  # Capacitor voltage
        i_l = 0  # Inductor current

        # Parameters
        v_in = self.v_in.get()
        v_ref = self.v_ref.get()
        r1 = self.r1.get()
        r2 = self.r2.get()
        i_adj = self.i_adj.get()
        r_load = self.r_load.get()
        c_load = self.c_load.get()
        l_series = self.l_series.get()
        t_max = self.sim_time.get()

        # Target output voltage
        v_out_target = v_ref * (1 + r2/r1) + i_adj * r2

        # Time step
        dt = self.dt

        # Simulation loop
        while t < t_max and self.simulation_running:
            # Differential equations for LC circuit with voltage source
            # dv_c/dt = i_l / C
            # di_l/dt = (v_in - v_c - i_l*R) / L

            # Regulator tries to maintain v_out_target
            v_source = v_out_target if (v_in - v_out_target) > 2 else v_in - 2

            # State derivatives
            dv_c_dt = i_l / c_load
            di_l_dt = (v_source - v_c - i_l * r_load) / l_series

            # Euler update
            v_c = v_c + dv_c_dt * dt
            i_l = i_l + di_l_dt * dt

            # Ensure physical constraints
            v_c = max(0, min(v_c, v_in))
            i_l = max(0, i_l)

            # Calculate power and efficiency
            p_out = v_c * i_l
            p_in = v_in * i_l
            efficiency = (p_out / p_in * 100) if p_in > 1e-6 else 0

            # Store data
            self.time_data.append(t)
            self.voltage_data.append(v_c)
            self.current_data.append(i_l)
            self.power_data.append(p_out)
            self.efficiency_data.append(efficiency)

            t += dt

        self.update_plots()

    def simulate_rk45(self):
        """Simulate using RK45 method (Runge-Kutta 4th/5th order)"""
        # Parameters
        v_in = self.v_in.get()
        v_ref = self.v_ref.get()
        r1 = self.r1.get()
        r2 = self.r2.get()
        i_adj = self.i_adj.get()
        r_load = self.r_load.get()
        c_load = self.c_load.get()
        l_series = self.l_series.get()
        t_max = self.sim_time.get()

        # Target output voltage
        v_out_target = v_ref * (1 + r2/r1) + i_adj * r2

        # Define system of ODEs
        def system_odes(t, y):
            v_c, i_l = y

            # Source voltage from regulator
            v_source = v_out_target if (v_in - v_out_target) > 2 else v_in - 2

            # State equations
            dv_c_dt = i_l / c_load
            di_l_dt = (v_source - v_c - i_l * r_load) / l_series

            return [dv_c_dt, di_l_dt]

        # Initial conditions [v_c, i_l]
        y0 = [0.0, 0.0]

        # Create ODE solver
        solver = ode(system_odes)
        solver.set_integrator('dopri5')  # RK45
        solver.set_initial_value(y0, 0)

        dt = self.dt

        # Solve ODE
        while solver.successful() and solver.t < t_max and self.simulation_running:
            solver.integrate(solver.t + dt)

            v_c, i_l = solver.y
            t = solver.t

            # Ensure physical constraints
            v_c = max(0, min(v_c, v_in))
            i_l = max(0, i_l)

            # Calculate power and efficiency
            p_out = v_c * i_l
            p_in = v_in * i_l
            efficiency = (p_out / p_in * 100) if p_in > 1e-6 else 0

            # Store data
            self.time_data.append(t)
            self.voltage_data.append(v_c)
            self.current_data.append(i_l)
            self.power_data.append(p_out)
            self.efficiency_data.append(efficiency)

        self.update_plots()

    def simulate_rk23(self):
        """Simulate using RK23 method (Runge-Kutta 2nd/3rd order)"""
        # Parameters
        v_in = self.v_in.get()
        v_ref = self.v_ref.get()
        r1 = self.r1.get()
        r2 = self.r2.get()
        i_adj = self.i_adj.get()
        r_load = self.r_load.get()
        c_load = self.c_load.get()
        l_series = self.l_series.get()
        t_max = self.sim_time.get()

        # Target output voltage
        v_out_target = v_ref * (1 + r2/r1) + i_adj * r2

        # RK23 implementation
        def rk23_step(t, y, dt, func):
            k1 = np.array(func(t, y))
            k2 = np.array(func(t + dt/2, y + dt/2 * k1))
            k3 = np.array(func(t + dt, y - dt*k1 + 2*dt*k2))

            # 2nd order estimate
            y_new = y + dt * (k1 + 4*k2 + k3) / 6
            return y_new

        def system_odes(t, y):
            v_c, i_l = y

            v_source = v_out_target if (v_in - v_out_target) > 2 else v_in - 2

            dv_c_dt = i_l / c_load
            di_l_dt = (v_source - v_c - i_l * r_load) / l_series

            return [dv_c_dt, di_l_dt]

        # Initial conditions
        t = 0
        y = np.array([0.0, 0.0])
        dt = self.dt

        # Simulation loop
        while t < t_max and self.simulation_running:
            y = rk23_step(t, y, dt, system_odes)
            t += dt

            v_c, i_l = y

            # Ensure physical constraints
            v_c = max(0, min(v_c, v_in))
            i_l = max(0, i_l)
            y = np.array([v_c, i_l])

            # Calculate power and efficiency
            p_out = v_c * i_l
            p_in = v_in * i_l
            efficiency = (p_out / p_in * 100) if p_in > 1e-6 else 0

            # Store data
            self.time_data.append(t)
            self.voltage_data.append(v_c)
            self.current_data.append(i_l)
            self.power_data.append(p_out)
            self.efficiency_data.append(efficiency)

        self.update_plots()

    def update_plots(self):
        """Update all plot displays"""
        if not self.time_data:
            return

        t = np.array(self.time_data)
        v = np.array(self.voltage_data)
        i = np.array(self.current_data)
        p = np.array(self.power_data)
        eff = np.array(self.efficiency_data)

        # Voltage plot
        self.ax_voltage.clear()
        self.ax_voltage.plot(t * 1000, v, 'b-', linewidth=2, label='V_out')
        v_target = self.v_ref.get() * (1 + self.r2.get()/self.r1.get()) + self.i_adj.get() * self.r2.get()
        self.ax_voltage.axhline(y=v_target, color='r', linestyle='--',
                               label=f'Target = {v_target:.2f}V')
        self.ax_voltage.set_xlabel('Time (ms)', fontsize=10)
        self.ax_voltage.set_ylabel('Voltage (V)', fontsize=10)
        self.ax_voltage.set_title('Output Voltage Response', fontsize=12, fontweight='bold')
        self.ax_voltage.grid(True, alpha=0.3)
        self.ax_voltage.legend()
        self.canvas_voltage.draw()

        # Current plot
        self.ax_current.clear()
        self.ax_current.plot(t * 1000, i * 1000, 'g-', linewidth=2, label='I_out')
        self.ax_current.set_xlabel('Time (ms)', fontsize=10)
        self.ax_current.set_ylabel('Current (mA)', fontsize=10)
        self.ax_current.set_title('Output Current Response', fontsize=12, fontweight='bold')
        self.ax_current.grid(True, alpha=0.3)
        self.ax_current.legend()
        self.canvas_current.draw()

        # Power plot
        self.ax_power1.clear()
        self.ax_power1.plot(t * 1000, p * 1000, 'r-', linewidth=2, label='P_out')
        self.ax_power1.set_xlabel('Time (ms)', fontsize=10)
        self.ax_power1.set_ylabel('Power (mW)', fontsize=10)
        self.ax_power1.set_title('Output Power', fontsize=11, fontweight='bold')
        self.ax_power1.grid(True, alpha=0.3)
        self.ax_power1.legend()

        # Efficiency plot
        self.ax_power2.clear()
        self.ax_power2.plot(t * 1000, eff, 'm-', linewidth=2, label='Efficiency')
        self.ax_power2.set_xlabel('Time (ms)', fontsize=10)
        self.ax_power2.set_ylabel('Efficiency (%)', fontsize=10)
        self.ax_power2.set_title('Regulator Efficiency', fontsize=11, fontweight='bold')
        self.ax_power2.grid(True, alpha=0.3)
        self.ax_power2.legend()

        self.fig_power.tight_layout()
        self.canvas_power.draw()

        # Update results
        if len(v) > 0:
            self.results_text.insert(tk.END, f"\n{'='*40}\n")
            self.results_text.insert(tk.END, "Simulation Results:\n")
            self.results_text.insert(tk.END, f"  Final V_out = {v[-1]:.3f} V\n")
            self.results_text.insert(tk.END, f"  Final I_out = {i[-1]*1000:.2f} mA\n")
            self.results_text.insert(tk.END, f"  Final P_out = {p[-1]*1000:.2f} mW\n")
            self.results_text.insert(tk.END, f"  Avg Efficiency = {np.mean(eff):.2f} %\n")
            self.results_text.insert(tk.END, f"  Settling time ≈ {t[-1]*1000:.2f} ms\n")

    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.simulation_paused = True

    def reset_simulation(self):
        """Reset the simulation"""
        self.simulation_running = False
        self.simulation_paused = False

        # Clear data
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.power_data = []
        self.efficiency_data = []

        # Clear plots
        self.ax_voltage.clear()
        self.ax_voltage.set_xlabel('Time (s)', fontsize=10)
        self.ax_voltage.set_ylabel('Voltage (V)', fontsize=10)
        self.ax_voltage.set_title('Output Voltage vs Time', fontsize=12, fontweight='bold')
        self.ax_voltage.grid(True, alpha=0.3)
        self.canvas_voltage.draw()

        self.ax_current.clear()
        self.ax_current.set_xlabel('Time (s)', fontsize=10)
        self.ax_current.set_ylabel('Current (A)', fontsize=10)
        self.ax_current.set_title('Output Current vs Time', fontsize=12, fontweight='bold')
        self.ax_current.grid(True, alpha=0.3)
        self.canvas_current.draw()

        self.ax_power1.clear()
        self.ax_power2.clear()
        self.canvas_power.draw()

        # Reset results
        self.update_calculations()

    def on_resize(self, event):
        """Handle window resize event"""
        # Auto-scale plots when window is resized
        try:
            self.fig_voltage.tight_layout()
            self.canvas_voltage.draw()

            self.fig_current.tight_layout()
            self.canvas_current.draw()

            self.fig_power.tight_layout()
            self.canvas_power.draw()

            self.fig_char.tight_layout()
            self.canvas_char.draw()
        except:
            pass


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = VoltageRegulatorLab(root)

    # Initial calculation
    app.update_calculations()

    root.mainloop()


if __name__ == "__main__":
    main()
