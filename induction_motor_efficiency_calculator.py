"""
Comprehensive Induction Motor Efficiency and Economic Analysis Lab
with Dynamic Simulation and Real-time ODE Solvers

Features:
- Motor economic comparison with capacitor correction
- Dynamic induction motor simulation
- Real-time ODE solvers (RK45 and Euler)
- Interactive GUI with Tkinter
- Auto-scaling visualization
- Practical electrical engineering applications
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import math
from scipy.integrate import solve_ivp


class InductionMotorLab:
    """Main application class for Induction Motor Analysis Lab"""

    def __init__(self, root):
        self.root = root
        self.root.title("Induction Motor Efficiency & Dynamic Analysis Lab")
        self.root.geometry("1400x900")

        # Simulation state
        self.is_running = False
        self.simulation_time = 0
        self.dt = 0.01  # Time step for simulation
        self.solver_type = "RK45"  # Default solver

        # Motor state variables for dynamic simulation
        self.omega = 0  # Angular velocity (rad/s)
        self.torque = 0  # Torque (Nm)
        self.current = 0  # Current (A)

        # History for plotting
        self.time_history = []
        self.omega_history = []
        self.torque_history = []
        self.current_history = []

        # Motor parameters (default values)
        self.params = {
            'output_power': 36.775,  # kW
            'motor_a_eff': 88.0,  # %
            'motor_a_pf': 0.9,
            'motor_b_eff': 90.0,  # %
            'motor_b_pf_initial': 0.81,
            'motor_b_pf_corrected': 0.89,
            'tariff_kva': 70.0,  # Rs per kVA
            'tariff_energy': 0.05,  # Rs per kWh
            'working_hours': 2400,  # hours per year
            'interest_depreciation': 10.0,  # %
            'motor_b_cost_diff': -150.0,  # Rs (negative means B is cheaper)
            'capacitor_cost': 60.0,  # Rs per kVAR
            # Dynamic simulation parameters
            'rated_voltage': 415.0,  # V (line-to-line)
            'rated_frequency': 50.0,  # Hz
            'poles': 4,
            'stator_resistance': 0.5,  # Ohm
            'rotor_resistance': 0.3,  # Ohm
            'stator_leakage': 0.002,  # H
            'rotor_leakage': 0.002,  # H
            'magnetizing_inductance': 0.1,  # H
            'moment_of_inertia': 0.5,  # kg.m^2
            'load_torque': 100.0,  # Nm (variable load)
        }

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create tabs
        self.create_main_menu_tab()
        self.create_economic_analysis_tab()
        self.create_dynamic_simulation_tab()
        self.create_comparative_analysis_tab()

        # Bind resize event for auto-scaling
        self.root.bind('<Configure>', self.on_window_resize)

    def create_main_menu_tab(self):
        """Create main menu tab with input parameters"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Main Menu & Parameters")

        # Create scrollable frame
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Title
        title_label = tk.Label(scrollable_frame,
                              text="Induction Motor Efficiency & Economic Analysis",
                              font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Input parameters sections
        self.create_parameter_section(scrollable_frame, "Motor Specifications", [
            ('output_power', 'Output Power Required (kW):', 1, 1000),
            ('motor_a_eff', 'Motor A Efficiency (%):', 50, 100),
            ('motor_a_pf', 'Motor A Power Factor:', 0.5, 1.0),
            ('motor_b_eff', 'Motor B Efficiency (%):', 50, 100),
            ('motor_b_pf_initial', 'Motor B Initial Power Factor:', 0.5, 1.0),
            ('motor_b_pf_corrected', 'Motor B Corrected Power Factor:', 0.5, 1.0),
        ], 1)

        self.create_parameter_section(scrollable_frame, "Economic Parameters", [
            ('tariff_kva', 'Tariff per kVA (Rs):', 0, 200),
            ('tariff_energy', 'Tariff per kWh (Rs):', 0, 1),
            ('working_hours', 'Working Hours per Year:', 0, 8760),
            ('interest_depreciation', 'Interest + Depreciation (%):', 0, 50),
            ('motor_b_cost_diff', 'Motor B Cost Difference (Rs):', -10000, 10000),
            ('capacitor_cost', 'Capacitor Cost per kVAR (Rs):', 0, 500),
        ], 10)

        self.create_parameter_section(scrollable_frame, "Dynamic Simulation Parameters", [
            ('rated_voltage', 'Rated Voltage (V):', 100, 1000),
            ('rated_frequency', 'Frequency (Hz):', 25, 100),
            ('poles', 'Number of Poles:', 2, 12),
            ('stator_resistance', 'Stator Resistance (Ω):', 0.1, 10),
            ('rotor_resistance', 'Rotor Resistance (Ω):', 0.1, 10),
            ('magnetizing_inductance', 'Magnetizing Inductance (H):', 0.01, 1),
            ('moment_of_inertia', 'Moment of Inertia (kg.m²):', 0.1, 10),
            ('load_torque', 'Load Torque (Nm):', 0, 500),
        ], 19)

        # Calculate button
        calc_button = tk.Button(scrollable_frame,
                               text="Calculate Economic Analysis",
                               command=self.calculate_economic_analysis,
                               bg='#4CAF50', fg='white',
                               font=('Arial', 12, 'bold'),
                               padx=20, pady=10)
        calc_button.grid(row=30, column=0, columnspan=3, pady=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_parameter_section(self, parent, title, parameters, start_row):
        """Create a section of parameter inputs with sliders"""
        # Section title
        section_label = tk.Label(parent, text=title,
                                font=('Arial', 12, 'bold'),
                                bg='#e0e0e0')
        section_label.grid(row=start_row, column=0, columnspan=3,
                          sticky='ew', pady=(10, 5), padx=5)

        # Parameter inputs
        if not hasattr(self, 'param_vars'):
            self.param_vars = {}
        if not hasattr(self, 'param_sliders'):
            self.param_sliders = {}

        for i, (key, label, min_val, max_val) in enumerate(parameters):
            row = start_row + i + 1

            # Label
            lbl = tk.Label(parent, text=label, anchor='w')
            lbl.grid(row=row, column=0, sticky='w', padx=5, pady=2)

            # Entry
            var = tk.DoubleVar(value=self.params[key])
            self.param_vars[key] = var
            entry = tk.Entry(parent, textvariable=var, width=15)
            entry.grid(row=row, column=1, padx=5, pady=2)

            # Slider
            slider = tk.Scale(parent, from_=min_val, to=max_val,
                            orient='horizontal', resolution=0.01,
                            variable=var, length=300)
            slider.grid(row=row, column=2, padx=5, pady=2)
            self.param_sliders[key] = slider

    def create_economic_analysis_tab(self):
        """Create tab for economic analysis results"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Economic Analysis")

        # Results frame
        results_frame = ttk.LabelFrame(tab, text="Analysis Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Text widget for results
        self.results_text = tk.Text(results_frame, wrap='word',
                                    font=('Courier', 10),
                                    bg='#f5f5f5')
        self.results_text.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.results_text.config(yscrollcommand=scrollbar.set)

        # Visualization frame
        viz_frame = ttk.LabelFrame(tab, text="Cost Comparison", padding=10)
        viz_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create matplotlib figure
        self.eco_fig = Figure(figsize=(10, 4), dpi=100)
        self.eco_canvas = FigureCanvasTkAgg(self.eco_fig, viz_frame)
        self.eco_canvas.get_tk_widget().pack(fill='both', expand=True)

    def create_dynamic_simulation_tab(self):
        """Create tab for dynamic motor simulation"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dynamic Simulation")

        # Control panel
        control_frame = ttk.LabelFrame(tab, text="Simulation Controls", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)

        # Solver selection
        solver_label = tk.Label(control_frame, text="ODE Solver:")
        solver_label.grid(row=0, column=0, padx=5)

        self.solver_var = tk.StringVar(value="RK45")
        solver_combo = ttk.Combobox(control_frame, textvariable=self.solver_var,
                                   values=["RK45", "Euler"], state='readonly', width=15)
        solver_combo.grid(row=0, column=1, padx=5)

        # Control buttons
        self.start_button = tk.Button(control_frame, text="Start",
                                      command=self.start_simulation,
                                      bg='#4CAF50', fg='white',
                                      font=('Arial', 10, 'bold'),
                                      width=10)
        self.start_button.grid(row=0, column=2, padx=5)

        self.stop_button = tk.Button(control_frame, text="Stop",
                                     command=self.stop_simulation,
                                     bg='#f44336', fg='white',
                                     font=('Arial', 10, 'bold'),
                                     width=10, state='disabled')
        self.stop_button.grid(row=0, column=3, padx=5)

        reset_button = tk.Button(control_frame, text="Reset",
                                command=self.reset_simulation,
                                bg='#2196F3', fg='white',
                                font=('Arial', 10, 'bold'),
                                width=10)
        reset_button.grid(row=0, column=4, padx=5)

        # Status label
        self.status_label = tk.Label(control_frame, text="Status: Ready",
                                     font=('Arial', 10))
        self.status_label.grid(row=0, column=5, padx=20)

        # Visualization frame
        viz_frame = ttk.LabelFrame(tab, text="Real-time Simulation", padding=10)
        viz_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Create matplotlib figure for simulation
        self.sim_fig = Figure(figsize=(12, 8), dpi=100)
        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, viz_frame)
        self.sim_canvas.get_tk_widget().pack(fill='both', expand=True)

        # Create subplots
        self.ax_speed = self.sim_fig.add_subplot(311)
        self.ax_torque = self.sim_fig.add_subplot(312)
        self.ax_current = self.sim_fig.add_subplot(313)

        self.setup_simulation_plots()

    def create_comparative_analysis_tab(self):
        """Create tab for comparative analysis"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Comparative Analysis")

        # Analysis frame
        analysis_frame = ttk.LabelFrame(tab, text="Efficiency & Power Factor Analysis",
                                       padding=10)
        analysis_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create matplotlib figure
        self.comp_fig = Figure(figsize=(12, 8), dpi=100)
        self.comp_canvas = FigureCanvasTkAgg(self.comp_fig, analysis_frame)
        self.comp_canvas.get_tk_widget().pack(fill='both', expand=True)

        # Calculate button
        calc_button = tk.Button(tab, text="Generate Comparative Analysis",
                               command=self.generate_comparative_analysis,
                               bg='#FF9800', fg='white',
                               font=('Arial', 11, 'bold'),
                               padx=20, pady=10)
        calc_button.pack(pady=10)

    def calculate_economic_analysis(self):
        """Calculate and display economic analysis"""
        # Update parameters from GUI
        for key, var in self.param_vars.items():
            self.params[key] = var.get()

        # Extract parameters
        P_out = self.params['output_power']

        # Motor A calculations
        eff_a = self.params['motor_a_eff'] / 100
        pf_a = self.params['motor_a_pf']
        P_in_a = P_out / eff_a
        S_a = P_in_a / pf_a

        # Motor B calculations (initial)
        eff_b = self.params['motor_b_eff'] / 100
        pf_b_initial = self.params['motor_b_pf_initial']
        pf_b_corrected = self.params['motor_b_pf_corrected']
        P_in_b = P_out / eff_b
        S_b_initial = P_in_b / pf_b_initial
        S_b_corrected = P_in_b / pf_b_corrected

        # Capacitor calculation
        theta_1 = math.acos(pf_b_initial)
        theta_2 = math.acos(pf_b_corrected)
        Q_initial = P_in_b * math.tan(theta_1)
        Q_corrected = P_in_b * math.tan(theta_2)
        Q_capacitor = Q_initial - Q_corrected

        # Economic calculations
        tariff_kva = self.params['tariff_kva']
        tariff_energy = self.params['tariff_energy']
        working_hours = self.params['working_hours']

        # Motor A costs
        demand_charge_a = S_a * tariff_kva
        energy_consumption_a = P_in_a * working_hours
        energy_charge_a = energy_consumption_a * tariff_energy
        total_annual_cost_a = demand_charge_a + energy_charge_a

        # Motor B costs (with capacitor)
        demand_charge_b = S_b_corrected * tariff_kva
        energy_consumption_b = P_in_b * working_hours
        energy_charge_b = energy_consumption_b * tariff_energy
        total_annual_cost_b = demand_charge_b + energy_charge_b

        # Annual savings
        annual_savings = total_annual_cost_a - total_annual_cost_b

        # Investment analysis
        capacitor_cost = Q_capacitor * self.params['capacitor_cost']
        motor_cost_diff = self.params['motor_b_cost_diff']
        net_investment = capacitor_cost + motor_cost_diff

        interest_dep_rate = self.params['interest_depreciation'] / 100
        annual_fixed_cost = net_investment * interest_dep_rate

        net_annual_savings = annual_savings - annual_fixed_cost

        if net_annual_savings > 0:
            payback_period = abs(net_investment) / annual_savings if annual_savings > 0 else float('inf')
        else:
            payback_period = float('inf')

        # Display results
        self.results_text.delete(1.0, tk.END)
        results = f"""
{'='*80}
INDUCTION MOTOR ECONOMIC ANALYSIS RESULTS
{'='*80}

MOTOR A ANALYSIS:
{'='*80}
  Output Power:              {P_out:.3f} kW
  Efficiency:                {eff_a*100:.2f}%
  Power Factor:              {pf_a:.3f}
  Input Power:               {P_in_a:.3f} kW
  Apparent Power:            {S_a:.3f} kVA

  Annual Costs:
    Demand Charge:           Rs. {demand_charge_a:.2f}
    Energy Consumption:      {energy_consumption_a:.2f} kWh
    Energy Charge:           Rs. {energy_charge_a:.2f}
    TOTAL ANNUAL COST:       Rs. {total_annual_cost_a:.2f}

{'='*80}
MOTOR B ANALYSIS:
{'='*80}
  Output Power:              {P_out:.3f} kW
  Efficiency:                {eff_b*100:.2f}%
  Initial Power Factor:      {pf_b_initial:.3f}
  Corrected Power Factor:    {pf_b_corrected:.3f}
  Input Power:               {P_in_b:.3f} kW

  Before Correction:
    Apparent Power:          {S_b_initial:.3f} kVA
    Reactive Power:          {Q_initial:.3f} kVAR

  After Correction:
    Apparent Power:          {S_b_corrected:.3f} kVA
    Reactive Power:          {Q_corrected:.3f} kVAR

  Capacitor Required:        {Q_capacitor:.3f} kVAR

  Annual Costs:
    Demand Charge:           Rs. {demand_charge_b:.2f}
    Energy Consumption:      {energy_consumption_b:.2f} kWh
    Energy Charge:           Rs. {energy_charge_b:.2f}
    TOTAL ANNUAL COST:       Rs. {total_annual_cost_b:.2f}

{'='*80}
ECONOMIC COMPARISON:
{'='*80}
  Annual Operating Cost Savings:  Rs. {annual_savings:.2f}

  Investment Analysis:
    Capacitor Cost:                Rs. {capacitor_cost:.2f}
    Motor B Cost Difference:       Rs. {motor_cost_diff:.2f}
    Net Additional Investment:     Rs. {net_investment:.2f}

  Annual Fixed Costs:
    Interest & Depreciation ({interest_dep_rate*100}%): Rs. {annual_fixed_cost:.2f}

  NET ANNUAL SAVINGS:              Rs. {net_annual_savings:.2f}

  Payback Period:                  {payback_period:.2f} years

{'='*80}
RECOMMENDATION:
{'='*80}
"""

        if net_annual_savings > 0:
            results += f"""  ✓ MOTOR B with capacitor correction is MORE ECONOMICAL
  ✓ Net savings: Rs. {net_annual_savings:.2f} per year
  ✓ Investment will be recovered in {payback_period:.2f} years
"""
        else:
            results += f"""  ✓ MOTOR A is MORE ECONOMICAL
  ✓ Motor A saves: Rs. {abs(net_annual_savings):.2f} per year
"""

        results += f"\n{'='*80}\n"

        self.results_text.insert(1.0, results)

        # Update visualization
        self.plot_economic_comparison(total_annual_cost_a, total_annual_cost_b,
                                     net_investment, annual_savings, net_annual_savings)

    def plot_economic_comparison(self, cost_a, cost_b, investment,
                                 operating_savings, net_savings):
        """Plot economic comparison charts"""
        self.eco_fig.clear()

        # Annual costs comparison
        ax1 = self.eco_fig.add_subplot(221)
        motors = ['Motor A', 'Motor B\n(with capacitor)']
        costs = [cost_a, cost_b]
        colors = ['#f44336', '#4CAF50']
        bars = ax1.bar(motors, costs, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        ax1.set_ylabel('Annual Cost (Rs)', fontweight='bold')
        ax1.set_title('Annual Operating Costs Comparison', fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'Rs. {height:.2f}',
                    ha='center', va='bottom', fontweight='bold')

        # Investment breakdown
        ax2 = self.eco_fig.add_subplot(222)
        categories = ['Motor B\nSavings', 'Capacitor\nCost', 'Net\nInvestment']
        values = [-self.params['motor_b_cost_diff'],
                 self.params['capacitor_cost'],
                 investment]
        colors_inv = ['#4CAF50', '#f44336', '#2196F3']
        bars2 = ax2.bar(categories, values, color=colors_inv, alpha=0.7,
                       edgecolor='black', linewidth=2)
        ax2.set_ylabel('Amount (Rs)', fontweight='bold')
        ax2.set_title('Investment Analysis', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)

        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'Rs. {height:.2f}',
                    ha='center', va='bottom' if height > 0 else 'top',
                    fontweight='bold')

        # Savings breakdown
        ax3 = self.eco_fig.add_subplot(223)
        savings_categories = ['Operating\nSavings', 'Fixed\nCosts', 'Net\nSavings']
        fixed_costs = investment * self.params['interest_depreciation'] / 100
        savings_values = [operating_savings, -fixed_costs, net_savings]
        colors_sav = ['#4CAF50', '#f44336', '#2196F3']
        bars3 = ax3.bar(savings_categories, savings_values, color=colors_sav,
                       alpha=0.7, edgecolor='black', linewidth=2)
        ax3.set_ylabel('Annual Amount (Rs)', fontweight='bold')
        ax3.set_title('Annual Savings Analysis', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)

        for bar in bars3:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'Rs. {height:.2f}',
                    ha='center', va='bottom' if height > 0 else 'top',
                    fontweight='bold')

        # Cumulative savings over years
        ax4 = self.eco_fig.add_subplot(224)
        years = np.arange(0, 11)
        cumulative_a = -investment + operating_savings * years - fixed_costs * years
        cumulative_b = net_savings * years - investment

        ax4.plot(years, cumulative_b, marker='o', linewidth=2,
                label='Net Cumulative Benefit', color='#2196F3')
        ax4.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax4.axhline(y=-investment, color='red', linestyle='--', linewidth=1,
                   alpha=0.5, label='Initial Investment')
        ax4.fill_between(years, 0, cumulative_b, where=(cumulative_b>=0),
                        alpha=0.3, color='green', label='Profit Region')
        ax4.fill_between(years, 0, cumulative_b, where=(cumulative_b<0),
                        alpha=0.3, color='red', label='Loss Region')
        ax4.set_xlabel('Years', fontweight='bold')
        ax4.set_ylabel('Cumulative Benefit (Rs)', fontweight='bold')
        ax4.set_title('Cumulative Financial Analysis', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend()

        self.eco_fig.tight_layout()
        self.eco_canvas.draw()

    def setup_simulation_plots(self):
        """Setup initial simulation plots"""
        # Speed plot
        self.ax_speed.set_ylabel('Speed (RPM)', fontweight='bold')
        self.ax_speed.set_title('Motor Speed vs Time', fontweight='bold')
        self.ax_speed.grid(True, alpha=0.3)

        # Torque plot
        self.ax_torque.set_ylabel('Torque (Nm)', fontweight='bold')
        self.ax_torque.set_title('Motor Torque vs Time', fontweight='bold')
        self.ax_torque.grid(True, alpha=0.3)

        # Current plot
        self.ax_current.set_ylabel('Current (A)', fontweight='bold')
        self.ax_current.set_xlabel('Time (s)', fontweight='bold')
        self.ax_current.set_title('Motor Current vs Time', fontweight='bold')
        self.ax_current.grid(True, alpha=0.3)

        self.sim_fig.tight_layout()
        self.sim_canvas.draw()

    def induction_motor_model(self, t, y):
        """
        Induction motor differential equations
        State variables: [omega, i_sq, i_sd, psi_rq, psi_rd]
        """
        omega = y[0]  # Rotor angular velocity

        # Motor parameters
        Rs = self.params['stator_resistance']
        Rr = self.params['rotor_resistance']
        Ls = self.params['stator_leakage'] + self.params['magnetizing_inductance']
        Lr = self.params['rotor_leakage'] + self.params['magnetizing_inductance']
        Lm = self.params['magnetizing_inductance']
        J = self.params['moment_of_inertia']
        p = self.params['poles'] / 2  # Pole pairs

        # Synchronous speed
        omega_s = 2 * np.pi * self.params['rated_frequency']

        # Slip
        slip = (omega_s - omega) / omega_s if omega_s != 0 else 1

        # Simplified torque calculation
        torque = 3 * p * Lm**2 * self.params['rated_voltage']**2 * Rr * slip / \
                (Rr**2 + (slip * omega_s * Lr)**2) / omega_s

        # Load torque (can be variable)
        T_load = self.params['load_torque']

        # Mechanical equation
        domega_dt = (torque - T_load) / J

        # Current estimation (simplified)
        current = np.sqrt(2) * self.params['rated_voltage'] / \
                 np.sqrt(Rs**2 + (omega_s * Ls)**2)

        # Store for display
        self.torque = torque
        self.current = current

        return [domega_dt]

    def euler_step(self, f, t, y, dt):
        """Euler method for ODE solving"""
        dydt = f(t, y)
        y_new = [y[i] + dt * dydt[i] for i in range(len(y))]
        return y_new

    def rk45_step(self, f, t, y, dt):
        """Runge-Kutta 4th order method"""
        k1 = f(t, y)
        k2 = f(t + dt/2, [y[i] + dt*k1[i]/2 for i in range(len(y))])
        k3 = f(t + dt/2, [y[i] + dt*k2[i]/2 for i in range(len(y))])
        k4 = f(t + dt, [y[i] + dt*k3[i] for i in range(len(y))])

        y_new = [y[i] + dt/6 * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i])
                for i in range(len(y))]
        return y_new

    def start_simulation(self):
        """Start the dynamic simulation"""
        self.is_running = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="Status: Running", fg='green')
        self.solver_type = self.solver_var.get()

        self.run_simulation()

    def stop_simulation(self):
        """Stop the simulation"""
        self.is_running = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="Status: Stopped", fg='red')

    def reset_simulation(self):
        """Reset the simulation"""
        self.stop_simulation()
        self.simulation_time = 0
        self.omega = 0
        self.torque = 0
        self.current = 0
        self.time_history = []
        self.omega_history = []
        self.torque_history = []
        self.current_history = []

        # Clear plots
        self.ax_speed.clear()
        self.ax_torque.clear()
        self.ax_current.clear()
        self.setup_simulation_plots()

        self.status_label.config(text="Status: Reset", fg='blue')

    def run_simulation(self):
        """Run one step of the simulation"""
        if not self.is_running:
            return

        # Initial condition
        y = [self.omega]

        # Solve ODE for one time step
        if self.solver_type == "Euler":
            y_new = self.euler_step(self.induction_motor_model,
                                   self.simulation_time, y, self.dt)
        else:  # RK45
            y_new = self.rk45_step(self.induction_motor_model,
                                  self.simulation_time, y, self.dt)

        # Update state
        self.omega = y_new[0]
        self.simulation_time += self.dt

        # Convert to RPM
        rpm = self.omega * 60 / (2 * np.pi)

        # Store history
        self.time_history.append(self.simulation_time)
        self.omega_history.append(rpm)
        self.torque_history.append(self.torque)
        self.current_history.append(self.current)

        # Limit history length
        max_points = 500
        if len(self.time_history) > max_points:
            self.time_history = self.time_history[-max_points:]
            self.omega_history = self.omega_history[-max_points:]
            self.torque_history = self.torque_history[-max_points:]
            self.current_history = self.current_history[-max_points:]

        # Update plots every 10 steps
        if len(self.time_history) % 10 == 0:
            self.update_simulation_plots()

        # Schedule next step
        if self.simulation_time < 10.0:  # Run for 10 seconds
            self.root.after(10, self.run_simulation)
        else:
            self.stop_simulation()
            self.status_label.config(text="Status: Completed", fg='blue')

    def update_simulation_plots(self):
        """Update simulation plots with current data"""
        # Clear axes
        self.ax_speed.clear()
        self.ax_torque.clear()
        self.ax_current.clear()

        # Plot data
        self.ax_speed.plot(self.time_history, self.omega_history,
                          'b-', linewidth=2, label='Speed')
        self.ax_speed.axhline(y=1500, color='r', linestyle='--',
                             label='Synchronous Speed', alpha=0.5)
        self.ax_speed.set_ylabel('Speed (RPM)', fontweight='bold')
        self.ax_speed.set_title(f'Motor Speed vs Time ({self.solver_type} Solver)',
                               fontweight='bold')
        self.ax_speed.grid(True, alpha=0.3)
        self.ax_speed.legend()

        self.ax_torque.plot(self.time_history, self.torque_history,
                           'g-', linewidth=2, label='Electromagnetic Torque')
        self.ax_torque.axhline(y=self.params['load_torque'], color='r',
                              linestyle='--', label='Load Torque', alpha=0.5)
        self.ax_torque.set_ylabel('Torque (Nm)', fontweight='bold')
        self.ax_torque.set_title('Motor Torque vs Time', fontweight='bold')
        self.ax_torque.grid(True, alpha=0.3)
        self.ax_torque.legend()

        self.ax_current.plot(self.time_history, self.current_history,
                            'r-', linewidth=2, label='Stator Current')
        self.ax_current.set_ylabel('Current (A)', fontweight='bold')
        self.ax_current.set_xlabel('Time (s)', fontweight='bold')
        self.ax_current.set_title('Motor Current vs Time', fontweight='bold')
        self.ax_current.grid(True, alpha=0.3)
        self.ax_current.legend()

        self.sim_fig.tight_layout()
        self.sim_canvas.draw()

    def generate_comparative_analysis(self):
        """Generate comparative analysis of efficiency and power factor"""
        self.comp_fig.clear()

        # Efficiency comparison at different loads
        ax1 = self.comp_fig.add_subplot(221)
        loads = np.linspace(0.25, 1.25, 50)  # 25% to 125% load

        # Typical efficiency curves (approximation)
        eff_a_curve = self.params['motor_a_eff'] * \
                     (1 - 0.15 * (loads - 1)**2)  # Peak at rated load
        eff_b_curve = self.params['motor_b_eff'] * \
                     (1 - 0.12 * (loads - 1)**2)  # Flatter curve

        ax1.plot(loads * 100, eff_a_curve, 'b-', linewidth=2,
                label='Motor A', marker='o', markersize=4)
        ax1.plot(loads * 100, eff_b_curve, 'g-', linewidth=2,
                label='Motor B', marker='s', markersize=4)
        ax1.set_xlabel('Load (%)', fontweight='bold')
        ax1.set_ylabel('Efficiency (%)', fontweight='bold')
        ax1.set_title('Efficiency vs Load', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Power factor comparison
        ax2 = self.comp_fig.add_subplot(222)
        pf_a_curve = self.params['motor_a_pf'] * \
                    (0.7 + 0.3 * loads)  # Improves with load
        pf_b_initial_curve = self.params['motor_b_pf_initial'] * \
                            (0.65 + 0.35 * loads)
        pf_b_corrected_curve = self.params['motor_b_pf_corrected'] * \
                              (0.75 + 0.25 * loads)

        ax2.plot(loads * 100, pf_a_curve, 'b-', linewidth=2,
                label='Motor A', marker='o', markersize=4)
        ax2.plot(loads * 100, pf_b_initial_curve, 'r--', linewidth=2,
                label='Motor B (uncorrected)', marker='s', markersize=4)
        ax2.plot(loads * 100, pf_b_corrected_curve, 'g-', linewidth=2,
                label='Motor B (corrected)', marker='^', markersize=4)
        ax2.set_xlabel('Load (%)', fontweight='bold')
        ax2.set_ylabel('Power Factor', fontweight='bold')
        ax2.set_title('Power Factor vs Load', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # Losses comparison
        ax3 = self.comp_fig.add_subplot(223)
        P_out_array = loads * self.params['output_power']
        losses_a = P_out_array * (1/self.params['motor_a_eff']*100 - 1)
        losses_b = P_out_array * (1/self.params['motor_b_eff']*100 - 1)

        ax3.plot(loads * 100, losses_a, 'b-', linewidth=2,
                label='Motor A Losses', marker='o', markersize=4)
        ax3.plot(loads * 100, losses_b, 'g-', linewidth=2,
                label='Motor B Losses', marker='s', markersize=4)
        ax3.fill_between(loads * 100, losses_b, losses_a,
                        alpha=0.3, color='green', label='Savings')
        ax3.set_xlabel('Load (%)', fontweight='bold')
        ax3.set_ylabel('Losses (kW)', fontweight='bold')
        ax3.set_title('Power Losses vs Load', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend()

        # Current comparison
        ax4 = self.comp_fig.add_subplot(224)

        # Estimated current (simplified)
        V_rated = self.params['rated_voltage']
        current_a = (P_out_array * 1000) / (np.sqrt(3) * V_rated *
                    pf_a_curve * eff_a_curve / 100)
        current_b_initial = (P_out_array * 1000) / (np.sqrt(3) * V_rated *
                           pf_b_initial_curve * eff_b_curve / 100)
        current_b_corrected = (P_out_array * 1000) / (np.sqrt(3) * V_rated *
                             pf_b_corrected_curve * eff_b_curve / 100)

        ax4.plot(loads * 100, current_a, 'b-', linewidth=2,
                label='Motor A', marker='o', markersize=4)
        ax4.plot(loads * 100, current_b_initial, 'r--', linewidth=2,
                label='Motor B (uncorrected)', marker='s', markersize=4)
        ax4.plot(loads * 100, current_b_corrected, 'g-', linewidth=2,
                label='Motor B (corrected)', marker='^', markersize=4)
        ax4.set_xlabel('Load (%)', fontweight='bold')
        ax4.set_ylabel('Current (A)', fontweight='bold')
        ax4.set_title('Line Current vs Load', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend()

        self.comp_fig.tight_layout()
        self.comp_canvas.draw()

    def on_window_resize(self, event):
        """Handle window resize for auto-scaling"""
        # This is called on any configure event
        # The canvases will automatically resize with their parent frames
        pass


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = InductionMotorLab(root)
    root.mainloop()


if __name__ == "__main__":
    main()
