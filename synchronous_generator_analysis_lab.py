"""
Advanced Three-Phase Synchronous Generator Analysis Lab
with Dynamic Simulation and Real-Time Visualization

Features:
- Static power factor, load angle, and EMF calculations
- Dynamic simulation with RK45 and Euler ODE solvers
- Real-time visualization with matplotlib
- Comprehensive Tkinter GUI with auto-scaling
- Professional electrical engineering analysis tools
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import math
from scipy.integrate import ode

class SynchronousGeneratorLab:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Synchronous Generator Analysis Lab")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Simulation control
        self.simulation_running = False
        self.simulation_time = 0.0
        self.dt = 0.01  # Time step
        self.solver_type = "RK45"  # Default solver

        # Generator parameters (default values from problem)
        self.params = {
            'Xs': tk.DoubleVar(value=14.0),      # Synchronous reactance (Ω)
            'Pout': tk.DoubleVar(value=1.68),    # Active power (MW)
            'V1L': tk.DoubleVar(value=11.0),     # Line-to-line voltage (kV)
            'Ia': tk.DoubleVar(value=100.0),     # Armature current (A)
            'R1': tk.DoubleVar(value=0.0),       # Armature resistance (Ω)
            'f': tk.DoubleVar(value=60.0),       # Frequency (Hz)
            'H': tk.DoubleVar(value=3.0),        # Inertia constant (s)
            'D': tk.DoubleVar(value=2.0),        # Damping coefficient
            'Tm': tk.DoubleVar(value=1.0),       # Mechanical torque (pu)
            'Ef': tk.DoubleVar(value=1.0),       # Excitation voltage (pu)
        }

        # Results storage
        self.results = {}
        self.time_data = []
        self.delta_data = []
        self.omega_data = []
        self.power_data = []
        self.current_data = []

        # Dynamic simulation state
        self.state = [0.0, 1.0]  # [delta, omega] in rad and pu

        # Configure root grid for responsive design
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create main container with notebook (tabs)
        self.create_main_interface()

        # Bind resize event for auto-scaling
        self.root.bind('<Configure>', self.on_window_resize)

    def create_main_interface(self):
        """Create the main tabbed interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create tabs
        self.create_static_analysis_tab()
        self.create_dynamic_simulation_tab()
        self.create_parameter_control_tab()
        self.create_results_tab()

    def create_static_analysis_tab(self):
        """Static power calculations tab"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Static Analysis")

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(tab, text="Three-Phase Synchronous Generator - Static Analysis",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Input frame
        input_frame = ttk.LabelFrame(tab, text="Input Parameters", padding="15")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # Parameter inputs with sliders
        params_config = [
            ('Synchronous Reactance Xs (Ω):', 'Xs', 1.0, 50.0, 14.0),
            ('Active Power Pout (MW):', 'Pout', 0.1, 10.0, 1.68),
            ('Line-to-Line Voltage V1L (kV):', 'V1L', 1.0, 25.0, 11.0),
            ('Armature Current Ia (A):', 'Ia', 10.0, 500.0, 100.0),
            ('Armature Resistance R1 (Ω):', 'R1', 0.0, 5.0, 0.0),
        ]

        for idx, (label_text, param_key, min_val, max_val, default) in enumerate(params_config):
            # Label
            label = ttk.Label(input_frame, text=label_text)
            label.grid(row=idx, column=0, sticky=tk.W, pady=5, padx=5)

            # Slider
            slider = ttk.Scale(input_frame, from_=min_val, to=max_val,
                             variable=self.params[param_key],
                             orient=tk.HORIZONTAL, length=300)
            slider.grid(row=idx, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

            # Entry
            entry = ttk.Entry(input_frame, textvariable=self.params[param_key], width=15)
            entry.grid(row=idx, column=2, pady=5, padx=5)

        input_frame.grid_columnconfigure(1, weight=1)

        # Calculate button
        calc_button = ttk.Button(input_frame, text="Calculate Parameters",
                                command=self.calculate_static_parameters,
                                style='Accent.TButton')
        calc_button.grid(row=len(params_config), column=0, columnspan=3, pady=15)

        # Results frame
        self.results_frame = ttk.LabelFrame(tab, text="Calculation Results", padding="15")
        self.results_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # Results display (will be populated after calculation)
        self.results_text = tk.Text(self.results_frame, height=25, width=60,
                                    font=('Courier', 10), wrap=tk.WORD)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL,
                                 command=self.results_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)

    def create_dynamic_simulation_tab(self):
        """Dynamic simulation tab with ODE solvers"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Dynamic Simulation")

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(tab, text="Dynamic Simulation with ODE Solvers",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Control frame
        control_frame = ttk.LabelFrame(tab, text="Simulation Controls", padding="15")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), padx=5, pady=5)

        # Solver selection
        ttk.Label(control_frame, text="ODE Solver:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.solver_var = tk.StringVar(value="RK45")
        solver_combo = ttk.Combobox(control_frame, textvariable=self.solver_var,
                                    values=["RK45", "Euler", "RK4"],
                                    state='readonly', width=15)
        solver_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)

        # Time step
        ttk.Label(control_frame, text="Time Step (s):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dt_var = tk.DoubleVar(value=0.01)
        dt_entry = ttk.Entry(control_frame, textvariable=self.dt_var, width=15)
        dt_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        # Simulation parameters
        ttk.Label(control_frame, text="Inertia Constant H (s):").grid(row=2, column=0, sticky=tk.W, pady=5)
        h_scale = ttk.Scale(control_frame, from_=1.0, to=10.0,
                           variable=self.params['H'], orient=tk.HORIZONTAL, length=200)
        h_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        h_entry = ttk.Entry(control_frame, textvariable=self.params['H'], width=10)
        h_entry.grid(row=2, column=2, pady=5, padx=5)

        ttk.Label(control_frame, text="Damping Coeff D:").grid(row=3, column=0, sticky=tk.W, pady=5)
        d_scale = ttk.Scale(control_frame, from_=0.0, to=10.0,
                           variable=self.params['D'], orient=tk.HORIZONTAL, length=200)
        d_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        d_entry = ttk.Entry(control_frame, textvariable=self.params['D'], width=10)
        d_entry.grid(row=3, column=2, pady=5, padx=5)

        ttk.Label(control_frame, text="Mechanical Torque Tm (pu):").grid(row=4, column=0, sticky=tk.W, pady=5)
        tm_scale = ttk.Scale(control_frame, from_=0.0, to=2.0,
                            variable=self.params['Tm'], orient=tk.HORIZONTAL, length=200)
        tm_scale.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        tm_entry = ttk.Entry(control_frame, textvariable=self.params['Tm'], width=10)
        tm_entry.grid(row=4, column=2, pady=5, padx=5)

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=15)

        self.start_button = ttk.Button(button_frame, text="▶ Start",
                                       command=self.start_simulation,
                                       style='Accent.TButton', width=12)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(button_frame, text="⏸ Stop",
                                      command=self.stop_simulation,
                                      state='disabled', width=12)
        self.stop_button.grid(row=0, column=1, padx=5)

        self.reset_button = ttk.Button(button_frame, text="↻ Reset",
                                       command=self.reset_simulation, width=12)
        self.reset_button.grid(row=0, column=2, padx=5)

        # Status label
        self.status_label = ttk.Label(control_frame, text="Status: Ready",
                                      font=('Arial', 10, 'bold'))
        self.status_label.grid(row=6, column=0, columnspan=3, pady=5)

        # Visualization frame
        viz_frame = ttk.LabelFrame(tab, text="Real-Time Visualization", padding="10")
        viz_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        viz_frame.grid_rowconfigure(0, weight=1)
        viz_frame.grid_columnconfigure(0, weight=1)

        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 8), dpi=100)

        # Subplots for different parameters
        self.ax1 = self.fig.add_subplot(311)
        self.ax1.set_ylabel('Load Angle δ (deg)', fontsize=10)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_title('Dynamic Response', fontsize=12, fontweight='bold')

        self.ax2 = self.fig.add_subplot(312)
        self.ax2.set_ylabel('Speed ω (pu)', fontsize=10)
        self.ax2.grid(True, alpha=0.3)

        self.ax3 = self.fig.add_subplot(313)
        self.ax3.set_ylabel('Power (MW)', fontsize=10)
        self.ax3.set_xlabel('Time (s)', fontsize=10)
        self.ax3.grid(True, alpha=0.3)

        self.fig.tight_layout()

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def create_parameter_control_tab(self):
        """Advanced parameter control tab"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Parameter Control")

        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(tab, text="Advanced Parameter Control Center",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=10)

        # Scrollable frame for all parameters
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # All parameters with detailed controls
        all_params = [
            ('Generator Parameters', [
                ('Synchronous Reactance Xs (Ω)', 'Xs', 1.0, 50.0),
                ('Armature Resistance R1 (Ω)', 'R1', 0.0, 5.0),
                ('Frequency f (Hz)', 'f', 50.0, 60.0),
            ]),
            ('Operating Conditions', [
                ('Active Power Pout (MW)', 'Pout', 0.1, 10.0),
                ('Line Voltage V1L (kV)', 'V1L', 1.0, 25.0),
                ('Armature Current Ia (A)', 'Ia', 10.0, 500.0),
            ]),
            ('Dynamic Parameters', [
                ('Inertia Constant H (s)', 'H', 1.0, 10.0),
                ('Damping Coefficient D', 'D', 0.0, 10.0),
                ('Mechanical Torque Tm (pu)', 'Tm', 0.0, 2.0),
                ('Excitation Voltage Ef (pu)', 'Ef', 0.5, 2.0),
            ]),
        ]

        row_idx = 0
        for section_title, param_list in all_params:
            # Section frame
            section_frame = ttk.LabelFrame(scrollable_frame, text=section_title,
                                          padding="15")
            section_frame.grid(row=row_idx, column=0, sticky=(tk.W, tk.E),
                             padx=10, pady=10)

            for idx, param_info in enumerate(param_list):
                label_text, param_key, min_val, max_val = param_info

                # Label
                ttk.Label(section_frame, text=label_text).grid(
                    row=idx, column=0, sticky=tk.W, pady=8, padx=5)

                # Slider
                slider = ttk.Scale(section_frame, from_=min_val, to=max_val,
                                 variable=self.params[param_key],
                                 orient=tk.HORIZONTAL, length=400)
                slider.grid(row=idx, column=1, sticky=(tk.W, tk.E), pady=8, padx=10)

                # Value display
                value_label = ttk.Label(section_frame,
                                       textvariable=self.params[param_key],
                                       width=10)
                value_label.grid(row=idx, column=2, pady=8, padx=5)

                # Entry for precise input
                entry = ttk.Entry(section_frame, textvariable=self.params[param_key],
                                width=12)
                entry.grid(row=idx, column=3, pady=8, padx=5)

            section_frame.grid_columnconfigure(1, weight=1)
            row_idx += 1

        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

    def create_results_tab(self):
        """Comprehensive results and analysis tab"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="Results & Analysis")

        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(tab, text="Comprehensive Analysis Results",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=10)

        # Results notebook (sub-tabs)
        results_notebook = ttk.Notebook(tab)
        results_notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Phasor diagram tab
        phasor_tab = ttk.Frame(results_notebook, padding="10")
        results_notebook.add(phasor_tab, text="Phasor Diagram")

        self.phasor_fig = Figure(figsize=(8, 8), dpi=100)
        self.phasor_ax = self.phasor_fig.add_subplot(111, projection='polar')
        self.phasor_canvas = FigureCanvasTkAgg(self.phasor_fig, master=phasor_tab)
        self.phasor_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Power-angle curve tab
        power_angle_tab = ttk.Frame(results_notebook, padding="10")
        results_notebook.add(power_angle_tab, text="Power-Angle Curve")

        self.power_angle_fig = Figure(figsize=(10, 6), dpi=100)
        self.power_angle_ax = self.power_angle_fig.add_subplot(111)
        self.power_angle_canvas = FigureCanvasTkAgg(self.power_angle_fig,
                                                    master=power_angle_tab)
        self.power_angle_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Export button
        export_button = ttk.Button(tab, text="Export Results to File",
                                  command=self.export_results)
        export_button.grid(row=2, column=0, pady=10)

    def calculate_static_parameters(self):
        """Calculate power factor, load angle, and EMF"""
        try:
            # Get parameters
            Xs = self.params['Xs'].get()
            Pout = self.params['Pout'].get() * 1e6  # Convert MW to W
            V1L = self.params['V1L'].get() * 1e3    # Convert kV to V
            Ia = self.params['Ia'].get()
            R1 = self.params['R1'].get()

            # Calculate phase voltage (Y-connected)
            Vph = V1L / math.sqrt(3)

            # Calculate apparent power
            S = math.sqrt(3) * V1L * Ia

            # Calculate power factor
            cos_phi = Pout / S

            # Ensure power factor is valid
            if cos_phi > 1.0:
                messagebox.showerror("Error",
                    f"Invalid condition: Power factor > 1.0 ({cos_phi:.3f})\n" +
                    "Check if active power is consistent with voltage and current.")
                return

            # Calculate power factor angle
            phi = math.acos(cos_phi)
            sin_phi = math.sin(phi)

            # Calculate reactive power
            Q = S * sin_phi

            # Calculate EMF (induced voltage in armature)
            # For lagging power factor (inductive load):
            # Ef = √[(Vph*cos(φ) + Ia*R1)² + (Vph*sin(φ) + Ia*Xs)²]
            Ef_real = Vph * cos_phi + Ia * R1
            Ef_imag = Vph * sin_phi + Ia * Xs
            Ef = math.sqrt(Ef_real**2 + Ef_imag**2)

            # Calculate load angle δ (angle between Ef and Vph)
            delta_rad = math.atan2(Ia * Xs * cos_phi, Vph + Ia * Xs * sin_phi)
            delta_deg = math.degrees(delta_rad)

            # Alternative calculation for load angle
            # tan(δ) = (Ia*Xs*cos(φ)) / (Vph + Ia*Xs*sin(φ))

            # Calculate line-to-line EMF
            Ef_LL = Ef * math.sqrt(3)

            # Store results
            self.results = {
                'Vph': Vph,
                'S': S,
                'cos_phi': cos_phi,
                'phi_deg': math.degrees(phi),
                'sin_phi': sin_phi,
                'Q': Q,
                'Ef': Ef,
                'Ef_LL': Ef_LL,
                'delta_deg': delta_deg,
                'delta_rad': delta_rad,
                'efficiency': (Pout / S) * 100 if S > 0 else 0
            }

            # Display results
            self.display_static_results()

            # Update phasor diagram
            self.plot_phasor_diagram()

            # Update power-angle curve
            self.plot_power_angle_curve()

        except Exception as e:
            messagebox.showerror("Calculation Error", f"Error in calculation:\n{str(e)}")

    def display_static_results(self):
        """Display calculation results in text widget"""
        self.results_text.delete(1.0, tk.END)

        # Header
        self.results_text.insert(tk.END, "="*60 + "\n")
        self.results_text.insert(tk.END, "  THREE-PHASE SYNCHRONOUS GENERATOR ANALYSIS\n")
        self.results_text.insert(tk.END, "="*60 + "\n\n")

        # Input parameters
        self.results_text.insert(tk.END, "INPUT PARAMETERS:\n")
        self.results_text.insert(tk.END, "-"*60 + "\n")
        self.results_text.insert(tk.END, f"Synchronous Reactance (Xs):     {self.params['Xs'].get():.2f} Ω\n")
        self.results_text.insert(tk.END, f"Active Power (Pout):            {self.params['Pout'].get():.3f} MW\n")
        self.results_text.insert(tk.END, f"Line-to-Line Voltage (V1L):     {self.params['V1L'].get():.2f} kV\n")
        self.results_text.insert(tk.END, f"Armature Current (Ia):          {self.params['Ia'].get():.2f} A\n")
        self.results_text.insert(tk.END, f"Armature Resistance (R1):       {self.params['R1'].get():.3f} Ω\n")
        self.results_text.insert(tk.END, "\n")

        # Calculated results
        self.results_text.insert(tk.END, "CALCULATED RESULTS:\n")
        self.results_text.insert(tk.END, "-"*60 + "\n")
        self.results_text.insert(tk.END, f"Phase Voltage (Vph):            {self.results['Vph']:.2f} V\n")
        self.results_text.insert(tk.END, f"                                {self.results['Vph']/1000:.3f} kV\n\n")

        self.results_text.insert(tk.END, f"Apparent Power (S):             {self.results['S']/1e6:.3f} MVA\n")
        self.results_text.insert(tk.END, f"Reactive Power (Q):             {self.results['Q']/1e6:.3f} MVAR\n\n")

        # Main results (highlighted)
        self.results_text.insert(tk.END, "*** PRIMARY RESULTS ***\n")
        self.results_text.insert(tk.END, "="*60 + "\n")
        self.results_text.insert(tk.END, f"Power Factor (cos φ):           {self.results['cos_phi']:.4f}\n")
        self.results_text.insert(tk.END, f"Power Factor Angle (φ):         {self.results['phi_deg']:.2f}°\n")
        self.results_text.insert(tk.END, f"                                {math.radians(self.results['phi_deg']):.4f} rad\n\n")

        self.results_text.insert(tk.END, f"Load Angle (δ):                 {self.results['delta_deg']:.2f}°\n")
        self.results_text.insert(tk.END, f"                                {self.results['delta_rad']:.4f} rad\n\n")

        self.results_text.insert(tk.END, f"Induced EMF - Phase (Ef):       {self.results['Ef']:.2f} V\n")
        self.results_text.insert(tk.END, f"                                {self.results['Ef']/1000:.3f} kV\n")
        self.results_text.insert(tk.END, f"Induced EMF - Line (Ef,LL):     {self.results['Ef_LL']:.2f} V\n")
        self.results_text.insert(tk.END, f"                                {self.results['Ef_LL']/1000:.3f} kV\n")
        self.results_text.insert(tk.END, "="*60 + "\n\n")

        # Additional analysis
        self.results_text.insert(tk.END, "ADDITIONAL ANALYSIS:\n")
        self.results_text.insert(tk.END, "-"*60 + "\n")

        # Power factor type
        pf_type = "Lagging (Inductive)" if self.results['sin_phi'] > 0 else "Leading (Capacitive)"
        self.results_text.insert(tk.END, f"Power Factor Type:              {pf_type}\n")

        # Voltage regulation
        vr = ((self.results['Ef'] - self.results['Vph']) / self.results['Vph']) * 100
        self.results_text.insert(tk.END, f"Voltage Regulation:             {vr:.2f}%\n")

        # Maximum power (at δ = 90°)
        Xs = self.params['Xs'].get()
        Vph = self.results['Vph']
        Ef = self.results['Ef']
        Pmax = (3 * Vph * Ef / Xs) / 1e6  # in MW
        self.results_text.insert(tk.END, f"Maximum Power (δ=90°):          {Pmax:.3f} MW\n")

        # Power margin
        power_margin = ((Pmax - self.params['Pout'].get()) / Pmax) * 100
        self.results_text.insert(tk.END, f"Power Margin:                   {power_margin:.2f}%\n")

        # Stability margin
        delta_critical = 90.0
        stability_margin = delta_critical - abs(self.results['delta_deg'])
        self.results_text.insert(tk.END, f"Stability Margin:               {stability_margin:.2f}°\n")

        self.results_text.insert(tk.END, "\n")
        self.results_text.insert(tk.END, "="*60 + "\n")
        self.results_text.insert(tk.END, "  ANALYSIS COMPLETE\n")
        self.results_text.insert(tk.END, "="*60 + "\n")

    def plot_phasor_diagram(self):
        """Plot phasor diagram showing voltage and current relationships"""
        if not self.results:
            return

        self.phasor_ax.clear()

        # Get values
        Vph = self.results['Vph'] / 1000  # Convert to kV for display
        Ef = self.results['Ef'] / 1000
        Ia = self.params['Ia'].get()
        Xs = self.params['Xs'].get()
        phi = math.radians(self.results['phi_deg'])
        delta = self.results['delta_rad']

        # Scale current for display (use voltage base)
        Ia_scaled = (Ia * Xs) / 1000

        # Phasor angles (Vph as reference at 0°)
        angle_Vph = 0
        angle_Ia = -phi  # Lagging current
        angle_Ef = delta
        angle_IXs = angle_Ia + math.pi/2  # jXs*Ia is 90° ahead of Ia

        # Plot phasors
        arrow_props = dict(arrowstyle='->', lw=2)

        # Terminal voltage (reference)
        self.phasor_ax.annotate('', xy=(angle_Vph, Vph), xytext=(0, 0),
                               arrowprops=dict(arrowstyle='->', lw=3, color='blue'))
        self.phasor_ax.text(angle_Vph, Vph*1.1, 'Vφ', fontsize=12,
                           ha='center', color='blue', fontweight='bold')

        # Armature current
        self.phasor_ax.annotate('', xy=(angle_Ia, Ia_scaled), xytext=(0, 0),
                               arrowprops=dict(arrowstyle='->', lw=2, color='red'))
        self.phasor_ax.text(angle_Ia, Ia_scaled*1.15, 'Ia', fontsize=12,
                           ha='center', color='red', fontweight='bold')

        # Reactance voltage drop
        self.phasor_ax.annotate('', xy=(angle_IXs, Ia_scaled), xytext=(0, 0),
                               arrowprops=dict(arrowstyle='->', lw=2,
                                             color='orange', linestyle='--'))
        self.phasor_ax.text(angle_IXs, Ia_scaled*1.15, 'jXsIa', fontsize=11,
                           ha='center', color='orange')

        # Induced EMF
        self.phasor_ax.annotate('', xy=(angle_Ef, Ef), xytext=(0, 0),
                               arrowprops=dict(arrowstyle='->', lw=3, color='green'))
        self.phasor_ax.text(angle_Ef, Ef*1.1, 'Ef', fontsize=12,
                           ha='center', color='green', fontweight='bold')

        # Mark angles
        # Power factor angle
        arc1 = np.linspace(angle_Ia, angle_Vph, 20)
        r1 = Vph * 0.2
        self.phasor_ax.plot(arc1, [r1]*len(arc1), 'k--', lw=1)
        self.phasor_ax.text((angle_Ia + angle_Vph)/2, r1*1.2, f'φ={self.results["phi_deg"]:.1f}°',
                           fontsize=9, ha='center')

        # Load angle
        arc2 = np.linspace(angle_Vph, angle_Ef, 20)
        r2 = Vph * 0.3
        self.phasor_ax.plot(arc2, [r2]*len(arc2), 'g--', lw=1)
        self.phasor_ax.text((angle_Vph + angle_Ef)/2, r2*1.2, f'δ={self.results["delta_deg"]:.1f}°',
                           fontsize=9, ha='center', color='green')

        self.phasor_ax.set_title('Phasor Diagram - Synchronous Generator\n(Lagging Power Factor)',
                                fontsize=14, fontweight='bold', pad=20)
        self.phasor_ax.set_ylim(0, max(Vph, Ef) * 1.3)
        self.phasor_ax.grid(True, alpha=0.3)

        self.phasor_canvas.draw()

    def plot_power_angle_curve(self):
        """Plot power-angle characteristic curve"""
        if not self.results:
            return

        self.power_angle_ax.clear()

        # Calculate power-angle curve
        Xs = self.params['Xs'].get()
        Vph = self.results['Vph']
        Ef = self.results['Ef']

        # Angle range
        delta_range = np.linspace(0, 180, 200)
        delta_rad = np.radians(delta_range)

        # Power equation: P = (3 * Vph * Ef * sin(δ)) / Xs
        P_3phase = (3 * Vph * Ef * np.sin(delta_rad) / Xs) / 1e6  # Convert to MW

        # Plot curve
        self.power_angle_ax.plot(delta_range, P_3phase, 'b-', lw=2,
                                label='Power-Angle Curve')

        # Mark operating point
        operating_delta = self.results['delta_deg']
        operating_power = self.params['Pout'].get()
        self.power_angle_ax.plot(operating_delta, operating_power, 'ro',
                                markersize=10, label='Operating Point')

        # Mark maximum power point
        max_power = max(P_3phase)
        max_power_angle = 90.0
        self.power_angle_ax.plot(max_power_angle, max_power, 'gs',
                                markersize=10, label=f'Pmax = {max_power:.2f} MW')

        # Add vertical line at operating point
        self.power_angle_ax.axvline(x=operating_delta, color='r',
                                   linestyle='--', alpha=0.5)
        self.power_angle_ax.axhline(y=operating_power, color='r',
                                   linestyle='--', alpha=0.5)

        # Stability regions
        self.power_angle_ax.axvspan(0, 90, alpha=0.1, color='green',
                                   label='Stable Region')
        self.power_angle_ax.axvspan(90, 180, alpha=0.1, color='red',
                                   label='Unstable Region')

        # Labels and formatting
        self.power_angle_ax.set_xlabel('Load Angle δ (degrees)', fontsize=12, fontweight='bold')
        self.power_angle_ax.set_ylabel('Output Power P (MW)', fontsize=12, fontweight='bold')
        self.power_angle_ax.set_title('Power-Angle Characteristic Curve',
                                     fontsize=14, fontweight='bold')
        self.power_angle_ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.5)
        self.power_angle_ax.legend(loc='upper right', fontsize=10)
        self.power_angle_ax.set_xlim(0, 180)
        self.power_angle_ax.set_ylim(0, max_power * 1.2)

        # Add annotation for operating point
        self.power_angle_ax.annotate(
            f'Operating Point\nδ = {operating_delta:.1f}°\nP = {operating_power:.2f} MW',
            xy=(operating_delta, operating_power),
            xytext=(operating_delta + 20, operating_power + max_power*0.15),
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3',
                          color='red', lw=2),
            fontsize=10
        )

        self.power_angle_fig.tight_layout()
        self.power_angle_canvas.draw()

    def swing_equation(self, t, y):
        """
        Swing equation for synchronous generator dynamics
        dy/dt = [dδ/dt, dω/dt]
        where:
        - δ: load angle (rad)
        - ω: rotor speed (pu)
        """
        delta, omega = y

        # Parameters
        H = self.params['H'].get()
        D = self.params['D'].get()
        Tm = self.params['Tm'].get()

        # Electrical power (simplified)
        # Pe = Pmax * sin(delta)
        if self.results:
            Xs = self.params['Xs'].get()
            Vph = self.results['Vph']
            Ef = self.results['Ef']
            Pmax = (3 * Vph * Ef / Xs) / 1e6  # MW
        else:
            Pmax = 2.0  # Default

        Pe = Pmax * np.sin(delta)

        # Swing equation
        # 2H * dω/dt = Tm - Te - D*(ω - 1)
        omega_s = 1.0  # Synchronous speed (pu)
        f = self.params['f'].get()
        omega_base = 2 * np.pi * f

        # State derivatives
        ddelta_dt = (omega - omega_s) * omega_base
        domega_dt = (Tm - Pe - D * (omega - omega_s)) / (2 * H)

        return [ddelta_dt, domega_dt]

    def euler_step(self, t, y, dt):
        """Euler method step"""
        dydt = self.swing_equation(t, y)
        y_new = [y[i] + dydt[i] * dt for i in range(len(y))]
        return y_new

    def rk4_step(self, t, y, dt):
        """Runge-Kutta 4th order step"""
        k1 = self.swing_equation(t, y)

        y2 = [y[i] + 0.5 * dt * k1[i] for i in range(len(y))]
        k2 = self.swing_equation(t + 0.5*dt, y2)

        y3 = [y[i] + 0.5 * dt * k2[i] for i in range(len(y))]
        k3 = self.swing_equation(t + 0.5*dt, y3)

        y4 = [y[i] + dt * k3[i] for i in range(len(y))]
        k4 = self.swing_equation(t + dt, y4)

        y_new = [y[i] + (dt/6.0) * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i])
                 for i in range(len(y))]

        return y_new

    def start_simulation(self):
        """Start dynamic simulation"""
        self.simulation_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Status: Running Simulation...")

        # Get solver type
        self.solver_type = self.solver_var.get()
        self.dt = self.dt_var.get()

        # Run simulation loop
        self.run_simulation_step()

    def stop_simulation(self):
        """Stop dynamic simulation"""
        self.simulation_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Status: Simulation Stopped")

    def reset_simulation(self):
        """Reset simulation to initial conditions"""
        self.stop_simulation()

        # Reset state
        self.simulation_time = 0.0
        self.state = [0.0, 1.0]  # [delta, omega]

        # Clear data
        self.time_data = []
        self.delta_data = []
        self.omega_data = []
        self.power_data = []

        # Clear plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        self.ax1.set_ylabel('Load Angle δ (deg)', fontsize=10)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_title('Dynamic Response', fontsize=12, fontweight='bold')

        self.ax2.set_ylabel('Speed ω (pu)', fontsize=10)
        self.ax2.grid(True, alpha=0.3)

        self.ax3.set_ylabel('Power (MW)', fontsize=10)
        self.ax3.set_xlabel('Time (s)', fontsize=10)
        self.ax3.grid(True, alpha=0.3)

        self.canvas.draw()

        self.status_label.config(text="Status: Reset Complete")

    def run_simulation_step(self):
        """Run one step of the simulation"""
        if not self.simulation_running:
            return

        # Perform integration step
        if self.solver_type == "Euler":
            self.state = self.euler_step(self.simulation_time, self.state, self.dt)
        elif self.solver_type == "RK4":
            self.state = self.rk4_step(self.simulation_time, self.state, self.dt)
        else:  # RK45 (simplified implementation)
            self.state = self.rk4_step(self.simulation_time, self.state, self.dt)

        # Update time
        self.simulation_time += self.dt

        # Store data
        self.time_data.append(self.simulation_time)
        self.delta_data.append(math.degrees(self.state[0]))
        self.omega_data.append(self.state[1])

        # Calculate power
        if self.results:
            Xs = self.params['Xs'].get()
            Vph = self.results['Vph']
            Ef = self.results['Ef']
            Pmax = (3 * Vph * Ef / Xs) / 1e6
            Pe = Pmax * np.sin(self.state[0])
        else:
            Pe = 0.0
        self.power_data.append(Pe)

        # Update plots every 10 steps
        if len(self.time_data) % 10 == 0:
            self.update_simulation_plots()

        # Continue simulation if time < 10 seconds
        if self.simulation_time < 10.0 and self.simulation_running:
            self.root.after(1, self.run_simulation_step)
        else:
            self.stop_simulation()
            self.status_label.config(text="Status: Simulation Complete")

    def update_simulation_plots(self):
        """Update real-time simulation plots"""
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Plot load angle
        self.ax1.plot(self.time_data, self.delta_data, 'b-', lw=2)
        self.ax1.set_ylabel('Load Angle δ (deg)', fontsize=10)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_title(f'Dynamic Response - {self.solver_type} Solver',
                          fontsize=12, fontweight='bold')

        # Plot speed
        self.ax2.plot(self.time_data, self.omega_data, 'r-', lw=2)
        self.ax2.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
        self.ax2.set_ylabel('Speed ω (pu)', fontsize=10)
        self.ax2.grid(True, alpha=0.3)

        # Plot power
        self.ax3.plot(self.time_data, self.power_data, 'g-', lw=2)
        self.ax3.set_ylabel('Power (MW)', fontsize=10)
        self.ax3.set_xlabel('Time (s)', fontsize=10)
        self.ax3.grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()

    def export_results(self):
        """Export results to text file"""
        try:
            filename = f"generator_analysis_results_{self.simulation_time:.0f}.txt"
            with open(filename, 'w') as f:
                f.write("="*70 + "\n")
                f.write("SYNCHRONOUS GENERATOR ANALYSIS RESULTS\n")
                f.write("="*70 + "\n\n")

                f.write("STATIC ANALYSIS:\n")
                f.write("-"*70 + "\n")
                if self.results:
                    for key, value in self.results.items():
                        f.write(f"{key}: {value}\n")
                f.write("\n")

                f.write("DYNAMIC SIMULATION DATA:\n")
                f.write("-"*70 + "\n")
                f.write("Time(s)\tDelta(deg)\tOmega(pu)\tPower(MW)\n")
                for i in range(len(self.time_data)):
                    f.write(f"{self.time_data[i]:.3f}\t{self.delta_data[i]:.3f}\t")
                    f.write(f"{self.omega_data[i]:.4f}\t{self.power_data[i]:.4f}\n")

            messagebox.showinfo("Export Successful",
                              f"Results exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")

    def on_window_resize(self, event):
        """Handle window resize events for auto-scaling"""
        # This method is called when window is resized
        # The grid layout with weights handles most of the scaling automatically
        pass

def main():
    """Main application entry point"""
    root = tk.Tk()

    # Configure style
    style = ttk.Style()
    style.theme_use('clam')

    # Custom style for accent buttons
    style.configure('Accent.TButton',
                   font=('Arial', 10, 'bold'),
                   foreground='white',
                   background='#0066cc')

    # Create application
    app = SynchronousGeneratorLab(root)

    # Start GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()
