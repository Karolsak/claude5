# Induction Motor Efficiency Calculator - Comprehensive Lab

## Overview
This is an advanced Python + Tkinter application for analyzing induction motor efficiency, economic comparison, and dynamic simulation with real-time ODE solvers.

## Features

### 1. **Economic Analysis**
- Compares two motors (A and B) based on efficiency and power factor
- Calculates capacitor requirements for power factor correction
- Performs complete economic analysis including:
  - Annual operating costs
  - Demand charges
  - Energy consumption costs
  - Investment analysis with payback period
  - Interest and depreciation calculations

### 2. **Dynamic Simulation**
- Real-time induction motor simulation
- Two ODE solvers: **RK45 (Runge-Kutta 4th order)** and **Euler**
- Simulates motor behavior including:
  - Speed (RPM) vs Time
  - Torque (Nm) vs Time
  - Current (A) vs Time
- Interactive controls: Start, Stop, Reset

### 3. **Comparative Analysis**
- Efficiency vs Load curves
- Power Factor vs Load curves
- Power Losses comparison
- Current comparison at different loads

### 4. **User Interface**
- Professional Tkinter GUI with multiple tabs
- Interactive sliders for all parameters
- Real-time visualization with matplotlib
- Auto-scaling when window is resized
- Intuitive controls and navigation

## Problem Solved

**Original Problem:**
A consumer requires an induction motor of 36.775 kW. Two motors are offered:
- **Motor A**: Efficiency 88%, Power Factor 0.9
- **Motor B**: Efficiency 90%, Power Factor 0.81 (corrected to 0.89 with capacitors)
- Motor B costs Rs. 150 less than Motor A
- Capacitor cost: Rs. 60 per kVAR
- Two-part tariff: Rs. 70 per kVA + Rs. 0.05 per kWh
- Interest + Depreciation: 10%
- Working hours: 2400 hours/year

**Solution:**
The application calculates that **Motor B with capacitor correction is more economical** by approximately **Rs. 111.88 per year**.

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install Dependencies
```bash
pip install -r requirements.txt
```

### For Tkinter (if not already installed)
- **Ubuntu/Debian**: `sudo apt-get install python3-tk`
- **Fedora**: `sudo dnf install python3-tkinter`
- **macOS**: Tkinter comes pre-installed with Python
- **Windows**: Tkinter comes pre-installed with Python

## Usage

### Run the Application
```bash
python3 induction_motor_efficiency_calculator.py
```

### Using the Application

#### Tab 1: Main Menu & Parameters
1. Adjust motor specifications using sliders or direct input:
   - Output power required
   - Motor A and B efficiencies
   - Power factors
   
2. Set economic parameters:
   - Tariff rates
   - Working hours
   - Cost differences
   
3. Configure dynamic simulation parameters:
   - Motor electrical parameters
   - Mechanical parameters
   - Load conditions

4. Click **"Calculate Economic Analysis"** to perform analysis

#### Tab 2: Economic Analysis
- View detailed calculation results
- Compare annual costs
- See investment breakdown
- Analyze cumulative savings over years
- Interactive charts and visualizations

#### Tab 3: Dynamic Simulation
1. Select ODE Solver (RK45 or Euler)
2. Click **"Start"** to begin simulation
3. Click **"Stop"** to pause
4. Click **"Reset"** to clear and restart
5. Watch real-time plots of:
   - Motor speed ramping up
   - Torque development
   - Current behavior

#### Tab 4: Comparative Analysis
- Click **"Generate Comparative Analysis"**
- View efficiency curves at different loads
- Compare power factors before and after correction
- Analyze losses and current variations

## Technical Details

### Differential Equations
The induction motor model uses simplified differential equations:
```
dω/dt = (T_em - T_load) / J
```

Where:
- ω: Angular velocity (rad/s)
- T_em: Electromagnetic torque (Nm)
- T_load: Load torque (Nm)
- J: Moment of inertia (kg·m²)

### ODE Solvers

#### Euler Method
Simple first-order method:
```
y_{n+1} = y_n + h·f(t_n, y_n)
```

#### RK45 (Runge-Kutta 4th Order)
More accurate fourth-order method:
```
y_{n+1} = y_n + (h/6)·(k1 + 2k2 + 2k3 + k4)
```

## Key Calculations

### Capacitor Requirement
```
Q_capacitor = P·(tan(θ1) - tan(θ2))
where θ = arccos(power_factor)
```

### Apparent Power
```
S = P / (efficiency × power_factor)
```

### Annual Costs
```
Cost = (kVA × tariff_kVA) + (kWh × tariff_energy)
```

## Practical Applications

1. **Motor Selection**: Compare different motors for industrial applications
2. **Power Factor Correction**: Determine optimal capacitor size
3. **Economic Analysis**: Calculate ROI and payback period
4. **Dynamic Analysis**: Study motor startup behavior
5. **Load Studies**: Analyze performance at different load conditions

## Advanced Features

- **Auto-scaling**: All plots automatically adjust to window size
- **Real-time Simulation**: See motor behavior in real-time
- **Multiple Solvers**: Compare accuracy of different numerical methods
- **Interactive Controls**: Adjust parameters on-the-fly
- **Professional Visualization**: Publication-quality graphs

## Example Results

For the given problem:
- **Motor A Annual Cost**: Rs. 8,265.08
- **Motor B Annual Cost**: Rs. 8,117.02
- **Capacitor Required**: 8.53 kVAR
- **Capacitor Cost**: Rs. 511.80
- **Net Annual Savings**: Rs. 111.88
- **Payback Period**: ~4.6 years

## Troubleshooting

### Issue: Module not found
**Solution**: Install missing dependencies:
```bash
pip install numpy matplotlib scipy
```

### Issue: Tkinter not found
**Solution**: Install tkinter for your OS (see Installation section)

### Issue: Plots not displaying
**Solution**: Ensure matplotlib backend supports Tkinter:
```bash
pip install --upgrade matplotlib
```

## Author
Created for electrical engineering education and practical motor analysis.

## License
Open source - free to use and modify for educational purposes.
