# Advanced Three-Phase Synchronous Generator Analysis Lab

## Overview

This comprehensive Python + Tkinter laboratory application provides advanced analysis and simulation capabilities for three-phase synchronous generators. It combines static power calculations with dynamic simulation using multiple ODE solvers.

## Problem Statement

**Given Problem:**
A three-phase, non-salient pole, Y-connected synchronous generator with:
- Synchronous reactance: Xs = 14.0 Ω
- Active power output: Pout = 1.68 MW
- Line-to-line voltage: V1L = 11 kV
- Armature current: Ia = 100.0 A
- Negligible armature resistance: R1 ≈ 0
- Inductive power factor (lagging)

**Find:**
1. Power factor (cos φ)
2. Load angle (δ)
3. Induced EMF (Ef)

## Features

### Static Analysis
- **Power Factor Calculation**: Computes cos φ from active and apparent power
- **Load Angle Calculation**: Determines the electrical angle δ between terminal voltage and induced EMF
- **EMF Calculation**: Calculates the induced electromotive force in the armature winding
- **Additional Metrics**:
  - Voltage regulation
  - Maximum power capability
  - Power margin
  - Stability margin

### Dynamic Simulation
- **Multiple ODE Solvers**:
  - **RK45**: Runge-Kutta 4th/5th order (adaptive)
  - **RK4**: Classical Runge-Kutta 4th order
  - **Euler**: Simple Euler method
- **Swing Equation Simulation**: Models generator rotor dynamics
- **Real-time Visualization**: Live plots of load angle, speed, and power
- **Adjustable Parameters**: Inertia constant (H), damping coefficient (D), mechanical torque (Tm)

### User Interface
- **Multi-tab Design**:
  - Static Analysis: Input parameters and view calculated results
  - Dynamic Simulation: Run time-domain simulations with ODE solvers
  - Parameter Control: Fine-tune all generator parameters with sliders
  - Results & Analysis: View phasor diagrams and power-angle curves

- **Interactive Controls**:
  - Slider bars for easy parameter adjustment
  - Numerical entry fields for precise values
  - Start/Stop/Reset buttons for simulation control
  - Auto-scaling responsive window design

### Visualization
- **Phasor Diagram**: Shows voltage, current, and EMF relationships
- **Power-Angle Curve**: Displays P-δ characteristic with operating point
- **Dynamic Plots**: Real-time display of:
  - Load angle vs. time
  - Rotor speed vs. time
  - Electrical power vs. time

## Installation

### Requirements
```bash
pip install numpy matplotlib scipy
```

### Python Version
- Python 3.6 or higher
- tkinter (usually included with Python)

## Usage

### Running the Application
```bash
python3 synchronous_generator_analysis_lab.py
```

### Quick Start Guide

1. **Static Analysis**:
   - Navigate to "Static Analysis" tab
   - Adjust input parameters using sliders or entry fields
   - Click "Calculate Parameters" button
   - View detailed results in the text area
   - Results include power factor, load angle, and induced EMF

2. **Dynamic Simulation**:
   - Navigate to "Dynamic Simulation" tab
   - Select ODE solver (RK45, RK4, or Euler)
   - Set time step and dynamic parameters (H, D, Tm)
   - Click "Start" to begin simulation
   - Watch real-time plots update
   - Click "Stop" to pause or "Reset" to restart

3. **Parameter Control**:
   - Navigate to "Parameter Control" tab
   - Fine-tune all parameters with detailed sliders
   - Organized by category: Generator Parameters, Operating Conditions, Dynamic Parameters

4. **Results & Analysis**:
   - Navigate to "Results & Analysis" tab
   - View phasor diagram showing voltage/current relationships
   - Examine power-angle characteristic curve
   - Identify operating point and stability margins
   - Export results to text file

## Mathematical Background

### Static Calculations

**Phase Voltage (Y-connected):**
```
Vφ = V_LL / √3
```

**Apparent Power:**
```
S = √3 × V_LL × Ia
```

**Power Factor:**
```
cos(φ) = P / S
```

**Induced EMF (lagging power factor):**
```
Ef = √[(Vφ·cos(φ) + Ia·R1)² + (Vφ·sin(φ) + Ia·Xs)²]
```

**Load Angle:**
```
tan(δ) = (Ia·Xs·cos(φ)) / (Vφ + Ia·Xs·sin(φ))
```

### Dynamic Simulation

**Swing Equation:**
```
2H·(dω/dt) = Tm - Te - D·(ω - ωs)
dδ/dt = (ω - ωs)·ωb
```

Where:
- H = Inertia constant (seconds)
- ω = Rotor speed (pu)
- Tm = Mechanical torque (pu)
- Te = Electrical torque (pu)
- D = Damping coefficient
- δ = Load angle (radians)
- ωb = Base angular frequency (rad/s)

**Power-Angle Relationship:**
```
P = (3·Vφ·Ef·sin(δ)) / Xs
```

## Solution for Given Problem

For the given parameters:
- Xs = 14.0 Ω
- Pout = 1.68 MW
- V1L = 11 kV
- Ia = 100.0 A

**Expected Results:**
- **Phase Voltage**: Vφ = 11000/√3 = 6350.85 V
- **Apparent Power**: S = √3 × 11000 × 100 = 1.905 MVA
- **Power Factor**: cos(φ) = 1.68/1.905 ≈ 0.882 (lagging)
- **Power Factor Angle**: φ ≈ 28.19°
- **Load Angle**: δ ≈ calculated from equations
- **Induced EMF**: Ef ≈ calculated from equations

Use the application to verify these calculations and explore the dynamic behavior!

## Advanced Features

### Auto-Scaling Window
- Responsive design with automatic layout adjustment
- Grid-based layout with proper weight distribution
- All components scale proportionally with window size

### Real-Time ODE Solvers
- **RK45**: Most accurate, adaptive step size
- **RK4**: Good balance of accuracy and speed
- **Euler**: Fastest but less accurate, good for quick visualization

### Export Functionality
- Export complete analysis results to text file
- Includes both static calculations and dynamic simulation data
- Time-series data in tabular format

## Practical Applications in Electrical Engineering

1. **Generator Design**: Verify generator specifications and operating limits
2. **Power System Stability**: Analyze transient stability and swing dynamics
3. **Protection System Design**: Determine safe operating ranges
4. **Load Studies**: Evaluate generator response to load changes
5. **Education**: Teaching tool for power systems courses
6. **Research**: Platform for testing control algorithms

## Tips for Best Results

1. **Parameter Selection**:
   - Start with default values
   - Adjust one parameter at a time
   - Observe effect on results

2. **Dynamic Simulation**:
   - Use RK45 for accurate results
   - Use Euler for quick visualization
   - Adjust time step based on desired accuracy vs. speed

3. **Stability Analysis**:
   - Monitor load angle: should stay below 90° for stable operation
   - Check power margin: higher is safer
   - Observe damping in dynamic response

## Troubleshooting

**Issue**: Application doesn't start
- **Solution**: Ensure all dependencies are installed (numpy, matplotlib, scipy)

**Issue**: Simulation runs too slowly
- **Solution**: Increase time step or use Euler solver

**Issue**: Invalid power factor error
- **Solution**: Check that active power is consistent with voltage and current ratings

**Issue**: Plots not updating
- **Solution**: Reset simulation and restart

## Technical Specifications

- **GUI Framework**: Tkinter with ttk widgets
- **Plotting**: Matplotlib with FigureCanvasTkAgg backend
- **Numerical Methods**: NumPy and SciPy
- **Window Size**: 1400×900 (default), minimum 1200×800
- **Simulation Time**: Default 10 seconds
- **Default Time Step**: 0.01 seconds

## File Structure

```
synchronous_generator_analysis_lab.py  # Main application file
README_GENERATOR_LAB.md               # This documentation
```

## Author

Created as part of advanced electrical engineering laboratory exercises.

## License

Open source - free for educational and research purposes.

## Version History

- **v1.0**: Initial release with static analysis and dynamic simulation
  - Multi-tab interface
  - Three ODE solvers (RK45, RK4, Euler)
  - Real-time visualization
  - Phasor diagrams and power-angle curves
  - Auto-scaling responsive design
  - Export functionality

## Future Enhancements

Potential additions:
- More sophisticated excitation system models
- Governor control simulation
- Multi-machine system simulation
- Fault analysis capabilities
- Parameter optimization tools
- 3D visualization of generator behavior

---

**Happy Analyzing!** 🔌⚡

For questions or issues, refer to electrical machinery textbooks or power systems analysis references.
