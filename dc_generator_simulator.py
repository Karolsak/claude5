#!/usr/bin/env python3
"""
DC Generator Simulator with Dynamic Analysis
Advanced Electrical Engineering Tool
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from scipy import interpolate
from scipy.integrate import odeint, solve_ivp
import threading
import time


class DCGeneratorSimulator:
    """Main application class for DC Generator Simulation"""

    def __init__(self, root):
        self.root = root
        self.root.title("DC Generator Simulator - Advanced Electrical Engineering Tool")
        self.root.geometry("1400x900")

        # Simulation control variables
        self.simulation_running = False
        self.simulation_thread = None
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.field_data = []

        # Problem data - OCC (Open Circuit Characteristic)
        self.if_data = np.array([0.2, 0.4, 0.6, 0.8, 1.0, 1.4, 2.0])
        self.emf_data = np.array([80, 135, 178, 198, 210, 228, 246])

        # Generator parameters
        self.params = {
            'shunt_turns': 1000,  # turns per pole
            'shunt_resistance': 240,  # Ω
            'armature_resistance': 0.36,  # Ω
            'load_current': 50,  # A
            'series_turns': 0,  # to be calculated
            'rated_voltage': 230,  # V
            'rated_speed': 1500,  # RPM
            'moment_inertia': 0.5,  # kg.m²
            'friction_coeff': 0.01,  # N.m.s
            'load_resistance': 10,  # Ω
        }

        # Create interpolation function for OCC
        self.occ_interp = interpolate.interp1d(
            self.if_data, self.emf_data,
            kind='cubic',
            fill_value='extrapolate'
        )

        # Setup UI
        self.setup_ui()

        # Bind resize event
        self.root.bind('<Configure>', self.on_window_resize)

    def setup_ui(self):
        """Setup the user interface"""
        # Create main notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create tabs
        self.tab_characteristic = ttk.Frame(self.notebook)
        self.tab_dynamic = ttk.Frame(self.notebook)
        self.tab_analysis = ttk.Frame(self.notebook)
        self.tab_results = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_characteristic, text='📊 Characteristic Analysis')
        self.notebook.add(self.tab_dynamic, text='⚡ Dynamic Simulation')
        self.notebook.add(self.tab_analysis, text='📈 Advanced Analysis')
        self.notebook.add(self.tab_results, text='📋 Results & Reports')

        # Setup each tab
        self.setup_characteristic_tab()
        self.setup_dynamic_tab()
        self.setup_analysis_tab()
        self.setup_results_tab()

    def setup_characteristic_tab(self):
        """Setup the characteristic analysis tab"""
        # Left panel - Controls
        left_frame = ttk.LabelFrame(self.tab_characteristic, text="Input Parameters", padding=10)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        left_frame.config(width=350)

        # Shunt winding parameters
        ttk.Label(left_frame, text="Shunt Winding Turns/Pole:").grid(row=0, column=0, sticky='w', pady=5)
        self.shunt_turns_var = tk.DoubleVar(value=self.params['shunt_turns'])
        ttk.Entry(left_frame, textvariable=self.shunt_turns_var, width=15).grid(row=0, column=1, pady=5)

        ttk.Label(left_frame, text="Shunt Resistance (Ω):").grid(row=1, column=0, sticky='w', pady=5)
        self.shunt_res_var = tk.DoubleVar(value=self.params['shunt_resistance'])
        ttk.Entry(left_frame, textvariable=self.shunt_res_var, width=15).grid(row=1, column=1, pady=5)

        ttk.Label(left_frame, text="Armature Resistance (Ω):").grid(row=2, column=0, sticky='w', pady=5)
        self.arm_res_var = tk.DoubleVar(value=self.params['armature_resistance'])
        ttk.Entry(left_frame, textvariable=self.arm_res_var, width=15).grid(row=2, column=1, pady=5)

        ttk.Label(left_frame, text="Load Current (A):").grid(row=3, column=0, sticky='w', pady=5)
        self.load_current_var = tk.DoubleVar(value=self.params['load_current'])
        self.load_current_scale = ttk.Scale(
            left_frame, from_=0, to=100,
            variable=self.load_current_var,
            orient='horizontal'
        )
        self.load_current_scale.grid(row=3, column=1, pady=5, sticky='ew')
        ttk.Label(left_frame, textvariable=self.load_current_var).grid(row=3, column=2, pady=5)

        # OCC Data display
        ttk.Separator(left_frame, orient='horizontal').grid(row=4, column=0, columnspan=3, sticky='ew', pady=10)
        ttk.Label(left_frame, text="Open Circuit Characteristic:", font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=3, sticky='w', pady=5)

        occ_text = scrolledtext.ScrolledText(left_frame, height=8, width=40)
        occ_text.grid(row=6, column=0, columnspan=3, pady=5)
        occ_text.insert('1.0', "If (A)\tEMF (V)\n")
        occ_text.insert('end', "-" * 30 + "\n")
        for i, e in zip(self.if_data, self.emf_data):
            occ_text.insert('end', f"{i:.1f}\t{e:.0f}\n")
        occ_text.config(state='disabled')

        # Calculate button
        ttk.Button(
            left_frame,
            text="Calculate Series Turns",
            command=self.calculate_series_turns
        ).grid(row=7, column=0, columnspan=3, pady=20, sticky='ew')

        # Results display
        self.result_text = scrolledtext.ScrolledText(left_frame, height=10, width=40)
        self.result_text.grid(row=8, column=0, columnspan=3, pady=5)

        # Right panel - Visualization
        right_frame = ttk.LabelFrame(self.tab_characteristic, text="Visualization", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.fig_char = Figure(figsize=(8, 6), dpi=100)
        self.ax_char = self.fig_char.add_subplot(111)

        self.canvas_char = FigureCanvasTkAgg(self.fig_char, master=right_frame)
        self.canvas_char.draw()
        self.canvas_char.get_tk_widget().pack(fill='both', expand=True)

        # Add toolbar
        toolbar = NavigationToolbar2Tk(self.canvas_char, right_frame)
        toolbar.update()

        # Initial plot
        self.plot_occ()

    def setup_dynamic_tab(self):
        """Setup the dynamic simulation tab"""
        # Left panel - Controls
        left_frame = ttk.LabelFrame(self.tab_dynamic, text="Simulation Parameters", padding=10)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        left_frame.config(width=350)

        # Simulation parameters
        ttk.Label(left_frame, text="Simulation Time (s):").grid(row=0, column=0, sticky='w', pady=5)
        self.sim_time_var = tk.DoubleVar(value=10.0)
        ttk.Entry(left_frame, textvariable=self.sim_time_var, width=15).grid(row=0, column=1, pady=5)

        ttk.Label(left_frame, text="Time Step (s):").grid(row=1, column=0, sticky='w', pady=5)
        self.time_step_var = tk.DoubleVar(value=0.01)
        ttk.Entry(left_frame, textvariable=self.time_step_var, width=15).grid(row=1, column=1, pady=5)

        ttk.Label(left_frame, text="Solver Method:").grid(row=2, column=0, sticky='w', pady=5)
        self.solver_var = tk.StringVar(value='RK45')
        solver_combo = ttk.Combobox(
            left_frame,
            textvariable=self.solver_var,
            values=['RK45', 'Euler', 'RK23', 'DOP853'],
            state='readonly',
            width=13
        )
        solver_combo.grid(row=2, column=1, pady=5)

        ttk.Separator(left_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)

        # Machine parameters with sliders
        ttk.Label(left_frame, text="Rated Voltage (V):").grid(row=4, column=0, sticky='w', pady=5)
        self.rated_voltage_var = tk.DoubleVar(value=self.params['rated_voltage'])
        ttk.Scale(
            left_frame, from_=100, to=400,
            variable=self.rated_voltage_var,
            orient='horizontal'
        ).grid(row=4, column=1, pady=5, sticky='ew')
        ttk.Label(left_frame, textvariable=self.rated_voltage_var).grid(row=4, column=2, pady=5)

        ttk.Label(left_frame, text="Field Current (A):").grid(row=5, column=0, sticky='w', pady=5)
        self.field_current_var = tk.DoubleVar(value=1.0)
        ttk.Scale(
            left_frame, from_=0.1, to=2.5,
            variable=self.field_current_var,
            orient='horizontal'
        ).grid(row=5, column=1, pady=5, sticky='ew')
        ttk.Label(left_frame, textvariable=self.field_current_var).grid(row=5, column=2, pady=5)

        ttk.Label(left_frame, text="Load Resistance (Ω):").grid(row=6, column=0, sticky='w', pady=5)
        self.load_res_var = tk.DoubleVar(value=self.params['load_resistance'])
        ttk.Scale(
            left_frame, from_=1, to=50,
            variable=self.load_res_var,
            orient='horizontal'
        ).grid(row=6, column=1, pady=5, sticky='ew')
        ttk.Label(left_frame, textvariable=self.load_res_var).grid(row=6, column=2, pady=5)

        ttk.Label(left_frame, text="Speed (RPM):").grid(row=7, column=0, sticky='w', pady=5)
        self.speed_var = tk.DoubleVar(value=self.params['rated_speed'])
        ttk.Scale(
            left_frame, from_=500, to=3000,
            variable=self.speed_var,
            orient='horizontal'
        ).grid(row=7, column=1, pady=5, sticky='ew')
        ttk.Label(left_frame, textvariable=self.speed_var).grid(row=7, column=2, pady=5)

        ttk.Separator(left_frame, orient='horizontal').grid(row=8, column=0, columnspan=3, sticky='ew', pady=10)

        # Control buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=9, column=0, columnspan=3, pady=10)

        self.start_btn = ttk.Button(
            button_frame,
            text="▶ Start",
            command=self.start_simulation,
            width=10
        )
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = ttk.Button(
            button_frame,
            text="⏸ Stop",
            command=self.stop_simulation,
            width=10,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=5)

        self.reset_btn = ttk.Button(
            button_frame,
            text="↻ Reset",
            command=self.reset_simulation,
            width=10
        )
        self.reset_btn.pack(side='left', padx=5)

        # Progress bar
        ttk.Label(left_frame, text="Simulation Progress:").grid(row=10, column=0, columnspan=3, sticky='w', pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            left_frame,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress_bar.grid(row=11, column=0, columnspan=3, pady=5, sticky='ew')

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            left_frame,
            textvariable=self.status_var,
            font=('Arial', 9, 'italic')
        ).grid(row=12, column=0, columnspan=3, pady=5)

        # Right panel - Real-time plots
        right_frame = ttk.LabelFrame(self.tab_dynamic, text="Real-Time Simulation", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Create matplotlib figure with subplots
        self.fig_dyn = Figure(figsize=(10, 8), dpi=100)
        self.ax_voltage = self.fig_dyn.add_subplot(311)
        self.ax_current = self.fig_dyn.add_subplot(312)
        self.ax_field = self.fig_dyn.add_subplot(313)

        self.fig_dyn.tight_layout(pad=3.0)

        self.canvas_dyn = FigureCanvasTkAgg(self.fig_dyn, master=right_frame)
        self.canvas_dyn.draw()
        self.canvas_dyn.get_tk_widget().pack(fill='both', expand=True)

        # Add toolbar
        toolbar = NavigationToolbar2Tk(self.canvas_dyn, right_frame)
        toolbar.update()

        # Initialize plots
        self.init_dynamic_plots()

    def setup_analysis_tab(self):
        """Setup the advanced analysis tab"""
        # Left panel - Analysis options
        left_frame = ttk.LabelFrame(self.tab_analysis, text="Analysis Options", padding=10)
        left_frame.pack(side='left', fill='both', expand=False, padx=5, pady=5)
        left_frame.config(width=350)

        # Analysis types
        ttk.Label(left_frame, text="Analysis Type:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=5)

        self.analysis_type = tk.StringVar(value='efficiency')

        ttk.Radiobutton(
            left_frame,
            text="Efficiency vs Load",
            variable=self.analysis_type,
            value='efficiency'
        ).grid(row=1, column=0, sticky='w', padx=20)

        ttk.Radiobutton(
            left_frame,
            text="Load Characteristics",
            variable=self.analysis_type,
            value='load_char'
        ).grid(row=2, column=0, sticky='w', padx=20)

        ttk.Radiobutton(
            left_frame,
            text="Voltage Regulation",
            variable=self.analysis_type,
            value='regulation'
        ).grid(row=3, column=0, sticky='w', padx=20)

        ttk.Radiobutton(
            left_frame,
            text="Magnetization Curve",
            variable=self.analysis_type,
            value='magnetization'
        ).grid(row=4, column=0, sticky='w', padx=20)

        ttk.Radiobutton(
            left_frame,
            text="Power Flow Analysis",
            variable=self.analysis_type,
            value='power_flow'
        ).grid(row=5, column=0, sticky='w', padx=20)

        ttk.Button(
            left_frame,
            text="Run Analysis",
            command=self.run_analysis
        ).grid(row=6, column=0, pady=20, sticky='ew', padx=20)

        # Analysis parameters
        ttk.Separator(left_frame, orient='horizontal').grid(row=7, column=0, sticky='ew', pady=10)
        ttk.Label(left_frame, text="Analysis Parameters:", font=('Arial', 10, 'bold')).grid(row=8, column=0, sticky='w', pady=5)

        ttk.Label(left_frame, text="Load Range (A):").grid(row=9, column=0, sticky='w', pady=5)
        load_range_frame = ttk.Frame(left_frame)
        load_range_frame.grid(row=10, column=0, sticky='ew', padx=20)

        ttk.Label(load_range_frame, text="Min:").pack(side='left')
        self.load_min_var = tk.DoubleVar(value=0)
        ttk.Entry(load_range_frame, textvariable=self.load_min_var, width=8).pack(side='left', padx=5)
        ttk.Label(load_range_frame, text="Max:").pack(side='left')
        self.load_max_var = tk.DoubleVar(value=100)
        ttk.Entry(load_range_frame, textvariable=self.load_max_var, width=8).pack(side='left', padx=5)

        ttk.Label(left_frame, text="Number of Points:").grid(row=11, column=0, sticky='w', pady=5)
        self.num_points_var = tk.IntVar(value=50)
        ttk.Entry(left_frame, textvariable=self.num_points_var, width=15).grid(row=12, column=0, padx=20, sticky='w')

        # Right panel - Analysis plots
        right_frame = ttk.LabelFrame(self.tab_analysis, text="Analysis Results", padding=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Create matplotlib figure
        self.fig_analysis = Figure(figsize=(10, 8), dpi=100)
        self.ax_analysis = self.fig_analysis.add_subplot(111)

        self.canvas_analysis = FigureCanvasTkAgg(self.fig_analysis, master=right_frame)
        self.canvas_analysis.draw()
        self.canvas_analysis.get_tk_widget().pack(fill='both', expand=True)

        # Add toolbar
        toolbar = NavigationToolbar2Tk(self.canvas_analysis, right_frame)
        toolbar.update()

    def setup_results_tab(self):
        """Setup the results and reports tab"""
        # Create notebook for different result views
        results_notebook = ttk.Notebook(self.tab_results)
        results_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Numerical results tab
        numerical_frame = ttk.Frame(results_notebook)
        results_notebook.add(numerical_frame, text='Numerical Results')

        self.numerical_text = scrolledtext.ScrolledText(
            numerical_frame,
            font=('Courier', 10),
            wrap='word'
        )
        self.numerical_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Summary tab
        summary_frame = ttk.Frame(results_notebook)
        results_notebook.add(summary_frame, text='Summary Report')

        self.summary_text = scrolledtext.ScrolledText(
            summary_frame,
            font=('Courier', 10),
            wrap='word'
        )
        self.summary_text.pack(fill='both', expand=True, padx=5, pady=5)

        # Export buttons
        button_frame = ttk.Frame(self.tab_results)
        button_frame.pack(side='bottom', fill='x', padx=5, pady=5)

        ttk.Button(
            button_frame,
            text="Export to Text",
            command=self.export_results
        ).pack(side='left', padx=5)

        ttk.Button(
            button_frame,
            text="Clear Results",
            command=self.clear_results
        ).pack(side='left', padx=5)

        # Initialize with welcome message
        self.numerical_text.insert('1.0', self.get_welcome_message())

    def get_welcome_message(self):
        """Get welcome message for results tab"""
        return """
╔══════════════════════════════════════════════════════════════════════╗
║     DC GENERATOR SIMULATOR - ADVANCED ELECTRICAL ENGINEERING TOOL    ║
╚══════════════════════════════════════════════════════════════════════╝

Welcome to the DC Generator Simulator!

This tool provides comprehensive analysis and simulation capabilities for
DC generators, including:

• Open Circuit Characteristic Analysis
• Series Winding Calculation for Compound Generators
• Dynamic Simulation with Multiple ODE Solvers (RK45, Euler, RK23, DOP853)
• Efficiency and Load Characteristic Analysis
• Voltage Regulation Studies
• Power Flow Analysis
• Real-time Visualization

GETTING STARTED:
1. Navigate to 'Characteristic Analysis' tab to solve the series turns problem
2. Use 'Dynamic Simulation' tab for real-time ODE-based simulation
3. Explore 'Advanced Analysis' for comprehensive performance studies
4. Results will be displayed here

═══════════════════════════════════════════════════════════════════════

"""

    def plot_occ(self):
        """Plot open circuit characteristic"""
        self.ax_char.clear()
        self.ax_char.plot(self.if_data, self.emf_data, 'bo-', label='Given Data', linewidth=2, markersize=8)

        # Plot interpolated curve
        if_fine = np.linspace(self.if_data[0], self.if_data[-1], 100)
        emf_fine = self.occ_interp(if_fine)
        self.ax_char.plot(if_fine, emf_fine, 'r--', label='Interpolated Curve', linewidth=1.5)

        self.ax_char.set_xlabel('Field Current (A)', fontsize=12, fontweight='bold')
        self.ax_char.set_ylabel('EMF (V)', fontsize=12, fontweight='bold')
        self.ax_char.set_title('Open Circuit Characteristic (OCC)', fontsize=14, fontweight='bold')
        self.ax_char.grid(True, alpha=0.3)
        self.ax_char.legend()

        self.canvas_char.draw()

    def calculate_series_turns(self):
        """Calculate series winding turns per pole"""
        try:
            # Get parameters
            N_sh = self.shunt_turns_var.get()
            R_sh = self.shunt_res_var.get()
            R_a = self.arm_res_var.get()
            I_L = self.load_current_var.get()

            # Step 1: Find no-load terminal voltage
            # At no-load, terminal voltage = generated EMF (approximately)
            # Field current at no-load: I_f_nl = V_t / R_sh
            # This requires iteration

            # Assume initial terminal voltage
            V_t_nl_guess = 220  # Initial guess

            # Iterate to find no-load voltage
            for iteration in range(50):
                I_f_nl = V_t_nl_guess / R_sh
                E_nl = float(self.occ_interp(I_f_nl))
                V_t_nl = E_nl  # At no-load, armature current is minimal

                if abs(V_t_nl - V_t_nl_guess) < 0.1:
                    break
                V_t_nl_guess = V_t_nl

            # Step 2: Calculate field current at load
            # Terminal voltage at load should equal no-load voltage
            V_t_load = V_t_nl

            # Shunt field current at load
            I_sh_load = V_t_load / R_sh

            # Armature current
            I_a = I_L + I_sh_load

            # Generated EMF at load
            E_load = V_t_load + I_a * R_a

            # Required total field current (from OCC to get E_load)
            # Inverse interpolation
            I_f_total_required = float(np.interp(E_load, self.emf_data, self.if_data))

            # Series field contribution
            I_f_series = I_f_total_required - I_sh_load

            # MMF balance: N_sh * I_sh_load + N_se * I_a = N_sh * I_f_total_required
            # But series winding carries armature current
            # MMF from series: N_se * I_a
            # Required additional MMF: N_sh * I_f_series

            # Therefore: N_se * I_a = N_sh * I_f_series
            N_se = (N_sh * I_f_series) / I_a

            # Display results
            self.result_text.config(state='normal')
            self.result_text.delete('1.0', 'end')

            result_str = f"""
╔══════════════════════════════════════════════════╗
║        SERIES WINDING CALCULATION RESULTS        ║
╚══════════════════════════════════════════════════╝

INPUT PARAMETERS:
─────────────────────────────────────────────────
  Shunt Turns/Pole:        {N_sh:.0f} turns
  Shunt Resistance:        {R_sh:.2f} Ω
  Armature Resistance:     {R_a:.3f} Ω
  Load Current:            {I_L:.2f} A

NO-LOAD CONDITION:
─────────────────────────────────────────────────
  Terminal Voltage:        {V_t_nl:.2f} V
  Field Current:           {I_f_nl:.4f} A
  Generated EMF:           {E_nl:.2f} V

LOAD CONDITION (at {I_L:.0f} A):
─────────────────────────────────────────────────
  Terminal Voltage:        {V_t_load:.2f} V (same as no-load)
  Shunt Field Current:     {I_sh_load:.4f} A
  Armature Current:        {I_a:.4f} A
  Generated EMF:           {E_load:.2f} V

FIELD CURRENT ANALYSIS:
─────────────────────────────────────────────────
  Total Field Current Req: {I_f_total_required:.4f} A
  Series Field Contrib:    {I_f_series:.4f} A

═══════════════════════════════════════════════════
  SERIES TURNS REQUIRED:   {N_se:.2f} turns/pole
═══════════════════════════════════════════════════

VERIFICATION:
  MMF from shunt:          {N_sh * I_sh_load:.2f} AT
  MMF from series:         {N_se * I_a:.2f} AT
  Total MMF:               {N_sh * I_sh_load + N_se * I_a:.2f} AT
  Required MMF:            {N_sh * I_f_total_required:.2f} AT

The series winding provides the additional magnetization
needed to compensate for armature resistance drop and
maintain constant terminal voltage under load.
"""

            self.result_text.insert('1.0', result_str)
            self.result_text.config(state='disabled')

            # Update results tab
            self.numerical_text.insert('end', '\n' + '='*70 + '\n')
            self.numerical_text.insert('end', 'CHARACTERISTIC ANALYSIS RESULTS\n')
            self.numerical_text.insert('end', '='*70 + '\n')
            self.numerical_text.insert('end', result_str)
            self.numerical_text.see('end')

            # Update plot with operating points
            self.ax_char.clear()
            self.plot_occ()

            # Add operating points
            self.ax_char.plot(I_f_nl, E_nl, 'go', markersize=12, label=f'No-Load: If={I_f_nl:.3f}A, E={E_nl:.1f}V')
            self.ax_char.plot(I_f_total_required, E_load, 'ro', markersize=12, label=f'Load: If={I_f_total_required:.3f}A, E={E_load:.1f}V')
            self.ax_char.legend()
            self.canvas_char.draw()

            # Store calculated series turns
            self.params['series_turns'] = N_se

            messagebox.showinfo(
                "Calculation Complete",
                f"Series winding turns required: {N_se:.2f} turns per pole\n\n"
                f"This ensures terminal voltage remains {V_t_nl:.1f}V at both no-load and {I_L}A load."
            )

        except Exception as e:
            messagebox.showerror("Calculation Error", f"An error occurred:\n{str(e)}")

    def init_dynamic_plots(self):
        """Initialize dynamic simulation plots"""
        self.ax_voltage.clear()
        self.ax_voltage.set_xlabel('Time (s)')
        self.ax_voltage.set_ylabel('Voltage (V)')
        self.ax_voltage.set_title('Terminal Voltage vs Time')
        self.ax_voltage.grid(True, alpha=0.3)

        self.ax_current.clear()
        self.ax_current.set_xlabel('Time (s)')
        self.ax_current.set_ylabel('Current (A)')
        self.ax_current.set_title('Load Current vs Time')
        self.ax_current.grid(True, alpha=0.3)

        self.ax_field.clear()
        self.ax_field.set_xlabel('Time (s)')
        self.ax_field.set_ylabel('Field Current (A)')
        self.ax_field.set_title('Field Current vs Time')
        self.ax_field.grid(True, alpha=0.3)

        self.fig_dyn.tight_layout()
        self.canvas_dyn.draw()

    def dc_generator_ode(self, t, y, params):
        """
        ODE system for DC generator dynamics
        State variables: [I_f, I_a, omega]
        I_f: Field current
        I_a: Armature current
        omega: Angular velocity
        """
        I_f, I_a, omega = y

        # Get EMF from field current (speed normalized)
        E_base = float(self.occ_interp(np.clip(I_f, self.if_data[0], self.if_data[-1])))

        # Speed effect on EMF
        omega_rated = params['rated_speed'] * 2 * np.pi / 60  # rad/s
        E = E_base * (omega / omega_rated)

        # Circuit equations
        R_f = params['shunt_resistance']
        R_a = params['armature_resistance']
        R_L = params['load_resistance']
        L_f = 0.5  # Field inductance (H)
        L_a = 0.01  # Armature inductance (H)

        # Terminal voltage
        V_t = E - I_a * R_a

        # Field equation: L_f * dI_f/dt = V_t - I_f * R_f
        dI_f_dt = (V_t - I_f * R_f) / L_f

        # Armature equation: L_a * dI_a/dt = E - I_a * (R_a + R_L)
        dI_a_dt = (E - I_a * (R_a + R_L)) / L_a

        # Mechanical equation: J * d(omega)/dt = T_e - T_L - B * omega
        J = params['moment_inertia']
        B = params['friction_coeff']

        # Electromagnetic torque (simplified)
        k_t = 0.5  # Torque constant
        T_e = k_t * I_f * I_a

        # Load torque (constant)
        T_L = 0.1

        domega_dt = (T_e - T_L - B * omega) / J

        return [dI_f_dt, dI_a_dt, domega_dt]

    def euler_solve(self, func, t_span, y0, dt, params):
        """Euler method ODE solver"""
        t_start, t_end = t_span
        t = np.arange(t_start, t_end, dt)
        n = len(t)
        y = np.zeros((n, len(y0)))
        y[0] = y0

        for i in range(1, n):
            if not self.simulation_running:
                break
            dy = func(t[i-1], y[i-1], params)
            y[i] = y[i-1] + np.array(dy) * dt

            # Update progress
            progress = (i / n) * 100
            self.progress_var.set(progress)

        return t[:i], y[:i]

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.simulation_running:
            return

        self.simulation_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_var.set("Simulation running...")

        # Clear previous data
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.field_data = []

        # Run simulation in separate thread
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

    def stop_simulation(self):
        """Stop dynamic simulation"""
        self.simulation_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Simulation stopped")

    def reset_simulation(self):
        """Reset simulation"""
        self.stop_simulation()
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.field_data = []
        self.progress_var.set(0)
        self.init_dynamic_plots()
        self.status_var.set("Ready")

    def run_simulation(self):
        """Run the dynamic simulation"""
        try:
            # Get parameters
            sim_time = self.sim_time_var.get()
            dt = self.time_step_var.get()
            solver = self.solver_var.get()

            # Update params
            params = {
                'rated_voltage': self.rated_voltage_var.get(),
                'rated_speed': self.speed_var.get(),
                'shunt_resistance': self.shunt_res_var.get(),
                'armature_resistance': self.arm_res_var.get(),
                'load_resistance': self.load_res_var.get(),
                'moment_inertia': 0.5,
                'friction_coeff': 0.01
            }

            # Initial conditions [I_f, I_a, omega]
            omega_0 = params['rated_speed'] * 2 * np.pi / 60
            y0 = [self.field_current_var.get(), 1.0, omega_0]

            # Solve ODE
            t_span = (0, sim_time)

            if solver == 'Euler':
                t, y = self.euler_solve(
                    self.dc_generator_ode,
                    t_span,
                    y0,
                    dt,
                    params
                )
            else:
                # Use scipy's solve_ivp with selected method
                sol = solve_ivp(
                    lambda t, y: self.dc_generator_ode(t, y, params),
                    t_span,
                    y0,
                    method=solver,
                    dense_output=True,
                    max_step=dt
                )

                t = np.linspace(0, sim_time, int(sim_time/dt))
                y = sol.sol(t).T

            if not self.simulation_running:
                return

            # Extract results
            I_f = y[:, 0]
            I_a = y[:, 1]
            omega = y[:, 2]

            # Calculate voltage
            V_t = []
            for i in range(len(t)):
                E_base = float(self.occ_interp(np.clip(I_f[i], self.if_data[0], self.if_data[-1])))
                omega_rated = params['rated_speed'] * 2 * np.pi / 60
                E = E_base * (omega[i] / omega_rated)
                V = E - I_a[i] * params['armature_resistance']
                V_t.append(V)

            V_t = np.array(V_t)

            # Store data
            self.time_data = t
            self.voltage_data = V_t
            self.current_data = I_a
            self.field_data = I_f

            # Update plots
            self.update_dynamic_plots()

            # Update results
            self.update_simulation_results(t, V_t, I_a, I_f, omega, params, solver)

            self.progress_var.set(100)
            self.status_var.set("Simulation complete")
            self.stop_simulation()

        except Exception as e:
            messagebox.showerror("Simulation Error", f"An error occurred:\n{str(e)}")
            self.stop_simulation()

    def update_dynamic_plots(self):
        """Update dynamic simulation plots"""
        self.ax_voltage.clear()
        self.ax_voltage.plot(self.time_data, self.voltage_data, 'b-', linewidth=2)
        self.ax_voltage.set_xlabel('Time (s)', fontweight='bold')
        self.ax_voltage.set_ylabel('Voltage (V)', fontweight='bold')
        self.ax_voltage.set_title('Terminal Voltage vs Time', fontweight='bold')
        self.ax_voltage.grid(True, alpha=0.3)

        self.ax_current.clear()
        self.ax_current.plot(self.time_data, self.current_data, 'r-', linewidth=2)
        self.ax_current.set_xlabel('Time (s)', fontweight='bold')
        self.ax_current.set_ylabel('Current (A)', fontweight='bold')
        self.ax_current.set_title('Armature Current vs Time', fontweight='bold')
        self.ax_current.grid(True, alpha=0.3)

        self.ax_field.clear()
        self.ax_field.plot(self.time_data, self.field_data, 'g-', linewidth=2)
        self.ax_field.set_xlabel('Time (s)', fontweight='bold')
        self.ax_field.set_ylabel('Field Current (A)', fontweight='bold')
        self.ax_field.set_title('Field Current vs Time', fontweight='bold')
        self.ax_field.grid(True, alpha=0.3)

        self.fig_dyn.tight_layout()
        self.canvas_dyn.draw()

    def update_simulation_results(self, t, V_t, I_a, I_f, omega, params, solver):
        """Update simulation results in results tab"""
        # Calculate statistics
        V_avg = np.mean(V_t)
        V_std = np.std(V_t)
        I_avg = np.mean(I_a)
        I_std = np.std(I_a)

        # Speed in RPM
        speed_rpm = omega * 60 / (2 * np.pi)
        speed_avg = np.mean(speed_rpm)

        # Power
        P_out = V_t * I_a
        P_avg = np.mean(P_out)

        result_str = f"""
╔══════════════════════════════════════════════════════════════════════╗
║               DYNAMIC SIMULATION RESULTS                             ║
╚══════════════════════════════════════════════════════════════════════╝

SIMULATION PARAMETERS:
─────────────────────────────────────────────────────────────────────
  Solver Method:           {solver}
  Simulation Time:         {t[-1]:.2f} s
  Time Steps:              {len(t)}

MACHINE PARAMETERS:
─────────────────────────────────────────────────────────────────────
  Rated Voltage:           {params['rated_voltage']:.2f} V
  Rated Speed:             {params['rated_speed']:.0f} RPM
  Armature Resistance:     {params['armature_resistance']:.3f} Ω
  Field Resistance:        {params['shunt_resistance']:.2f} Ω
  Load Resistance:         {params['load_resistance']:.2f} Ω

STEADY-STATE RESULTS:
─────────────────────────────────────────────────────────────────────
  Average Voltage:         {V_avg:.2f} ± {V_std:.2f} V
  Average Current:         {I_avg:.2f} ± {I_std:.2f} A
  Average Speed:           {speed_avg:.1f} RPM
  Average Power:           {P_avg:.2f} W

FINAL VALUES (at t = {t[-1]:.2f}s):
─────────────────────────────────────────────────────────────────────
  Terminal Voltage:        {V_t[-1]:.2f} V
  Armature Current:        {I_a[-1]:.2f} A
  Field Current:           {I_f[-1]:.4f} A
  Speed:                   {speed_rpm[-1]:.1f} RPM
  Output Power:            {V_t[-1] * I_a[-1]:.2f} W

═══════════════════════════════════════════════════════════════════════
"""

        self.numerical_text.insert('end', '\n' + '='*70 + '\n')
        self.numerical_text.insert('end', 'DYNAMIC SIMULATION RESULTS\n')
        self.numerical_text.insert('end', '='*70 + '\n')
        self.numerical_text.insert('end', result_str)
        self.numerical_text.see('end')

    def run_analysis(self):
        """Run selected analysis"""
        analysis = self.analysis_type.get()

        try:
            if analysis == 'efficiency':
                self.analyze_efficiency()
            elif analysis == 'load_char':
                self.analyze_load_characteristics()
            elif analysis == 'regulation':
                self.analyze_voltage_regulation()
            elif analysis == 'magnetization':
                self.analyze_magnetization()
            elif analysis == 'power_flow':
                self.analyze_power_flow()

        except Exception as e:
            messagebox.showerror("Analysis Error", f"An error occurred:\n{str(e)}")

    def analyze_efficiency(self):
        """Analyze efficiency vs load"""
        self.status_var.set("Running efficiency analysis...")

        # Load range
        I_L = np.linspace(self.load_min_var.get(), self.load_max_var.get(), self.num_points_var.get())

        # Parameters
        R_sh = self.shunt_res_var.get()
        R_a = self.arm_res_var.get()
        V_t = 230  # Assume constant terminal voltage

        # Calculate efficiency
        efficiency = []
        losses_cu = []
        losses_field = []
        power_out = []

        for i_l in I_L:
            I_sh = V_t / R_sh
            I_a = i_l + I_sh

            # Losses
            P_cu = I_a**2 * R_a  # Copper losses
            P_field = V_t * I_sh  # Field losses
            P_loss_total = P_cu + P_field

            # Output power
            P_out = V_t * i_l

            # Input power
            P_in = P_out + P_loss_total

            # Efficiency
            if P_in > 0:
                eff = (P_out / P_in) * 100
            else:
                eff = 0

            efficiency.append(eff)
            losses_cu.append(P_cu)
            losses_field.append(P_field)
            power_out.append(P_out)

        # Plot
        self.ax_analysis.clear()

        ax1 = self.ax_analysis
        ax1.plot(I_L, efficiency, 'b-', linewidth=2.5, label='Efficiency')
        ax1.set_xlabel('Load Current (A)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Efficiency (%)', fontsize=12, fontweight='bold', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.grid(True, alpha=0.3)

        ax2 = ax1.twinx()
        ax2.plot(I_L, losses_cu, 'r--', linewidth=2, label='Copper Losses')
        ax2.plot(I_L, losses_field, 'g--', linewidth=2, label='Field Losses')
        ax2.set_ylabel('Losses (W)', fontsize=12, fontweight='bold', color='r')
        ax2.tick_params(axis='y', labelcolor='r')

        ax1.set_title('Efficiency and Losses vs Load Current', fontsize=14, fontweight='bold')

        # Legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')

        self.fig_analysis.tight_layout()
        self.canvas_analysis.draw()

        # Find maximum efficiency
        max_eff = np.max(efficiency)
        max_eff_idx = np.argmax(efficiency)
        max_eff_current = I_L[max_eff_idx]

        result = f"""
EFFICIENCY ANALYSIS RESULTS:
Maximum Efficiency: {max_eff:.2f}% at {max_eff_current:.2f} A
Full Load Efficiency: {efficiency[-1]:.2f}%
"""

        self.numerical_text.insert('end', '\n' + result)
        self.numerical_text.see('end')

        self.status_var.set("Efficiency analysis complete")

    def analyze_load_characteristics(self):
        """Analyze load characteristics"""
        self.status_var.set("Running load characteristic analysis...")

        # Load range
        I_L = np.linspace(0, self.load_max_var.get(), self.num_points_var.get())

        # Parameters
        R_sh = self.shunt_res_var.get()
        R_a = self.arm_res_var.get()

        # Calculate terminal voltage for each load
        V_t = []
        E_g = []

        for i_l in I_L:
            # Assume initial terminal voltage
            v_t = 230

            # Iterate
            for _ in range(20):
                I_sh = v_t / R_sh
                I_a = i_l + I_sh
                I_f = I_sh

                E = float(self.occ_interp(np.clip(I_f, self.if_data[0], self.if_data[-1])))
                v_t_new = E - I_a * R_a

                if abs(v_t_new - v_t) < 0.1:
                    break
                v_t = v_t_new

            V_t.append(v_t)
            E_g.append(E)

        # Plot
        self.ax_analysis.clear()
        self.ax_analysis.plot(I_L, V_t, 'b-', linewidth=2.5, label='Terminal Voltage')
        self.ax_analysis.plot(I_L, E_g, 'r--', linewidth=2, label='Generated EMF')
        self.ax_analysis.set_xlabel('Load Current (A)', fontsize=12, fontweight='bold')
        self.ax_analysis.set_ylabel('Voltage (V)', fontsize=12, fontweight='bold')
        self.ax_analysis.set_title('Load Characteristics', fontsize=14, fontweight='bold')
        self.ax_analysis.grid(True, alpha=0.3)
        self.ax_analysis.legend()

        self.fig_analysis.tight_layout()
        self.canvas_analysis.draw()

        self.status_var.set("Load characteristic analysis complete")

    def analyze_voltage_regulation(self):
        """Analyze voltage regulation"""
        self.status_var.set("Running voltage regulation analysis...")

        R_sh = self.shunt_res_var.get()
        R_a = self.arm_res_var.get()

        # No-load voltage
        V_nl = 230
        I_f_nl = V_nl / R_sh
        E_nl = float(self.occ_interp(I_f_nl))

        # Full load
        I_L_fl = self.load_max_var.get()
        v_t = V_nl

        for _ in range(20):
            I_sh = v_t / R_sh
            I_a = I_L_fl + I_sh
            I_f = I_sh
            E = float(self.occ_interp(np.clip(I_f, self.if_data[0], self.if_data[-1])))
            v_t_new = E - I_a * R_a
            if abs(v_t_new - v_t) < 0.1:
                break
            v_t = v_t_new

        V_fl = v_t

        # Voltage regulation
        VR = ((V_nl - V_fl) / V_fl) * 100

        # Plot
        self.ax_analysis.clear()

        loads = ['No Load', 'Full Load']
        voltages = [V_nl, V_fl]
        colors = ['green', 'red']

        bars = self.ax_analysis.bar(loads, voltages, color=colors, alpha=0.7, edgecolor='black', linewidth=2)

        # Add value labels on bars
        for bar, voltage in zip(bars, voltages):
            height = bar.get_height()
            self.ax_analysis.text(bar.get_x() + bar.get_width()/2., height,
                                  f'{voltage:.1f} V',
                                  ha='center', va='bottom', fontsize=12, fontweight='bold')

        self.ax_analysis.set_ylabel('Terminal Voltage (V)', fontsize=12, fontweight='bold')
        self.ax_analysis.set_title(f'Voltage Regulation: {VR:.2f}%', fontsize=14, fontweight='bold')
        self.ax_analysis.grid(True, alpha=0.3, axis='y')

        self.fig_analysis.tight_layout()
        self.canvas_analysis.draw()

        result = f"""
VOLTAGE REGULATION ANALYSIS:
No-Load Voltage: {V_nl:.2f} V
Full-Load Voltage: {V_fl:.2f} V
Voltage Regulation: {VR:.2f}%
"""

        self.numerical_text.insert('end', '\n' + result)
        self.numerical_text.see('end')

        self.status_var.set("Voltage regulation analysis complete")

    def analyze_magnetization(self):
        """Analyze magnetization curve"""
        self.status_var.set("Running magnetization analysis...")

        self.ax_analysis.clear()

        # Plot OCC
        self.ax_analysis.plot(self.if_data, self.emf_data, 'bo-',
                             label='Measured Data', linewidth=2, markersize=10)

        # Interpolated
        if_fine = np.linspace(0, self.if_data[-1], 200)
        emf_fine = self.occ_interp(if_fine)
        self.ax_analysis.plot(if_fine, emf_fine, 'r-',
                             label='Magnetization Curve', linewidth=2)

        # Air gap line (linear part)
        slope = (self.emf_data[1] - self.emf_data[0]) / (self.if_data[1] - self.if_data[0])
        air_gap_line = slope * if_fine
        self.ax_analysis.plot(if_fine, air_gap_line, 'g--',
                             label='Air Gap Line', linewidth=1.5)

        self.ax_analysis.set_xlabel('Field Current (A)', fontsize=12, fontweight='bold')
        self.ax_analysis.set_ylabel('Generated EMF (V)', fontsize=12, fontweight='bold')
        self.ax_analysis.set_title('Magnetization Curve Analysis', fontsize=14, fontweight='bold')
        self.ax_analysis.grid(True, alpha=0.3)
        self.ax_analysis.legend()

        # Mark saturation point
        # Find where curve deviates significantly from air gap line
        deviation = emf_fine - air_gap_line
        sat_idx = np.where(deviation > 20)[0]
        if len(sat_idx) > 0:
            sat_idx = sat_idx[0]
            self.ax_analysis.plot(if_fine[sat_idx], emf_fine[sat_idx], 'r*',
                                 markersize=20, label='Saturation Onset')
            self.ax_analysis.legend()

        self.fig_analysis.tight_layout()
        self.canvas_analysis.draw()

        self.status_var.set("Magnetization analysis complete")

    def analyze_power_flow(self):
        """Analyze power flow"""
        self.status_var.set("Running power flow analysis...")

        # Parameters
        R_sh = self.shunt_res_var.get()
        R_a = self.arm_res_var.get()
        V_t = 230
        I_L = 50

        I_sh = V_t / R_sh
        I_a = I_L + I_sh
        I_f = I_sh

        E = float(self.occ_interp(I_f))

        # Power calculations
        P_developed = E * I_a
        P_cu_armature = I_a**2 * R_a
        P_output = V_t * I_L
        P_field = V_t * I_sh
        P_input = P_output + P_cu_armature + P_field

        # Create Sankey-like diagram using bar chart
        self.ax_analysis.clear()

        powers = [P_input, P_developed, P_output]
        losses = [0, P_cu_armature + P_field, P_cu_armature]

        labels = ['Input\nPower', 'Developed\nPower', 'Output\nPower']
        x_pos = np.arange(len(labels))

        bars1 = self.ax_analysis.bar(x_pos, powers, color='green', alpha=0.7,
                                     label='Useful Power', edgecolor='black', linewidth=2)
        bars2 = self.ax_analysis.bar(x_pos[1:], losses[1:], bottom=[powers[1], powers[2]],
                                     color='red', alpha=0.7, label='Losses',
                                     edgecolor='black', linewidth=2)

        # Add value labels
        for i, (bar, power) in enumerate(zip(bars1, powers)):
            height = bar.get_height()
            self.ax_analysis.text(bar.get_x() + bar.get_width()/2., height/2,
                                  f'{power:.0f} W',
                                  ha='center', va='center', fontsize=11, fontweight='bold')

        self.ax_analysis.set_ylabel('Power (W)', fontsize=12, fontweight='bold')
        self.ax_analysis.set_title('Power Flow Analysis', fontsize=14, fontweight='bold')
        self.ax_analysis.set_xticks(x_pos)
        self.ax_analysis.set_xticklabels(labels, fontweight='bold')
        self.ax_analysis.legend()
        self.ax_analysis.grid(True, alpha=0.3, axis='y')

        self.fig_analysis.tight_layout()
        self.canvas_analysis.draw()

        efficiency = (P_output / P_input) * 100

        result = f"""
POWER FLOW ANALYSIS:
Input Power: {P_input:.2f} W
Developed Power: {P_developed:.2f} W
Output Power: {P_output:.2f} W
Copper Losses: {P_cu_armature:.2f} W
Field Losses: {P_field:.2f} W
Total Losses: {P_cu_armature + P_field:.2f} W
Efficiency: {efficiency:.2f}%
"""

        self.numerical_text.insert('end', '\n' + result)
        self.numerical_text.see('end')

        self.status_var.set("Power flow analysis complete")

    def export_results(self):
        """Export results to text file"""
        try:
            with open('/home/user/claude5/dc_generator_results.txt', 'w') as f:
                f.write("DC GENERATOR SIMULATOR - RESULTS EXPORT\n")
                f.write("=" * 70 + "\n\n")
                f.write(self.numerical_text.get('1.0', 'end'))

            messagebox.showinfo("Export Complete", "Results exported to dc_generator_results.txt")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")

    def clear_results(self):
        """Clear results"""
        self.numerical_text.delete('1.0', 'end')
        self.numerical_text.insert('1.0', self.get_welcome_message())
        self.summary_text.delete('1.0', 'end')

    def on_window_resize(self, event):
        """Handle window resize event"""
        # This will be called on window resize
        # Matplotlib canvases will auto-adjust due to pack with expand=True
        pass


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = DCGeneratorSimulator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
