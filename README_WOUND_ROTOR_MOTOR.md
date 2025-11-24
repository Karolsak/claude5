# Wound-Rotor Induction Motor Analysis Lab

## Example 6.2: Unbalanced Three-Phase Operation

A comprehensive Python + Tkinter GUI application for analyzing wound-rotor induction motors operating under unbalanced three-phase voltage conditions.

### Problem Statement

The 460V/100hp wound-rotor induction motor from Example 4.3 is operating from an unbalanced three-phase three-wire 60 Hz source:
- **V_ab** = 450 V
- **V_bc** = 470 V
- **V_ca** = 440 V

Running at **1770 rpm** with the rotor shorted, the application calculates:
- All currents (phase and sequence)
- Powers (input, output, losses)
- Electromagnetic torques (positive, negative, total)
- Slip and efficiency
- Symmetrical components analysis

---

## Features

### 1. **Comprehensive GUI with Tkinter**
- **Main Menu**: File, Analysis, and Help menus
- **Three Tabs**:
  1. **Steady State Analysis**: Input parameters, sliders, and detailed results
  2. **Dynamic Simulation**: Real-time ODE solver with visualization
  3. **Voltage Analysis**: Symmetrical components and phasor diagrams

### 2. **Mathematical Modeling**
- **Equivalent Circuit Model**: Complete per-phase equivalent circuit
- **Symmetrical Components**: Positive, negative, and zero sequence analysis
- **Differential Equations**: Motor dynamics with torque equation:
  ```
  J * dω/dt = T_em - T_load - B*ω
  ```

### 3. **ODE Solvers for Dynamic Simulation**
- **RK45 (Runge-Kutta 4th order)**: High-accuracy adaptive solver
- **Euler Method**: Simple first-order solver for comparison
- Real-time selection between solvers

### 4. **Advanced Visualization**
- **Speed vs Time**: Motor acceleration/deceleration curves
- **Torque vs Time**: Electromagnetic torque dynamics
- **Current vs Time**: Three-phase unbalanced currents
- **Phasor Diagrams**: Voltage phasor visualization
- **Bar Charts**: Sequence components and voltage comparison

### 5. **Interactive Controls**
- **Adjustment Sliders**:
  - V_ab, V_bc, V_ca (400-500 V)
  - Operating Speed (0-1800 rpm)
  - Load Torque (0-1000 N·m)
  - Initial Speed for simulation
  - Simulation Time
- **Buttons**: Start, Stop, Reset
- **Auto-update**: Real-time calculations as parameters change

### 6. **Auto-Scaling & Responsive Layout**
- Automatic window resizing
- Grid weight configuration for proportional scaling
- Matplotlib tight_layout for optimal plot arrangement

---

## Installation

### Prerequisites
```bash
# Python 3.7 or higher
python3 --version

# Required packages
pip install numpy matplotlib scipy
```

### Tkinter Installation
**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
```bash
# Usually pre-installed with Python
# If not, install Python from python.org
```

**Windows:**
```bash
# Included with standard Python installation
```

---

## Usage

### Running the Application
```bash
python3 wound_rotor_induction_motor_lab.py
```

### Quick Start Guide

#### **Tab 1: Steady State Analysis**
1. Adjust voltage sliders to set unbalanced line voltages
2. Set operating speed (default: 1770 rpm)
3. Set load torque if needed
4. Click **Calculate** to see detailed results

**Results Include:**
- Motor specifications
- Unbalanced voltages and unbalance factor
- Symmetrical components (positive, negative, zero sequence)
- Phase currents with angles
- Sequence currents
- Electromagnetic torque breakdown
- Complete power analysis
- Efficiency calculation
- Equivalent circuit parameters

#### **Tab 2: Dynamic Simulation**
1. Select ODE solver (RK45 recommended for accuracy)
2. Set simulation time (default: 2.0 seconds)
3. Set initial speed (0 for startup from standstill)
4. Click **▶ Start** to run simulation

**Visualizations:**
- **Speed curve**: Shows motor acceleration to steady-state
- **Torque curve**: Electromagnetic torque development
- **Current curves**: Three-phase currents during transient

5. Use **⬛ Stop** to interrupt simulation
6. Use **⟲ Reset** to clear and restart

#### **Tab 3: Voltage Analysis**
- **Phasor Diagram**: Phase voltage phasors (V_an, V_bn, V_cn)
- **Symmetrical Components**: Bar chart of sequence components
- **Line Voltages**: Unbalanced line voltages with average
- **Phase Voltages**: Calculated phase voltages

Updates automatically when voltage sliders are adjusted.

---

## Technical Details

### Motor Parameters (100 hp Wound-Rotor Motor)
```python
Poles:                  6
Rated Voltage:          460 V
Rated Power:            100 hp (74.6 kW)
Frequency:              60 Hz
Synchronous Speed:      1200 rpm

Equivalent Circuit:
  R1 (stator):          0.0625 Ω
  X1 (stator):          0.454 Ω
  R2 (rotor):           0.0862 Ω
  X2 (rotor):           0.454 Ω
  Xm (magnetizing):     20.1 Ω

Mechanical:
  Inertia (J):          5.0 kg·m²
  Friction (B):         0.1 N·m·s
```

### Symmetrical Components Method
The unbalanced voltages are decomposed into:

**Positive Sequence (V₁):**
```
V₁ = (V_a + a·V_b + a²·V_c) / 3
```

**Negative Sequence (V₂):**
```
V₂ = (V_a + a²·V_b + a·V_c) / 3
```

**Zero Sequence (V₀):**
```
V₀ = (V_a + V_b + V_c) / 3
```

Where `a = e^(j2π/3)` is the complex operator.

### Torque Calculation
**Positive Sequence Torque:**
```
T_pos = 3·I₁²·R₂/(s·ω_sync)
```

**Negative Sequence Torque (opposes rotation):**
```
T_neg = -3·I₂²·R₂/((2-s)·ω_sync)
```

**Total Torque:**
```
T_total = T_pos + T_neg
```

### Dynamic Equation
```
J·dω/dt = T_em - T_load - B·ω
```

Where:
- **J**: Moment of inertia
- **ω**: Mechanical angular velocity
- **T_em**: Electromagnetic torque
- **T_load**: Load torque
- **B**: Friction coefficient

---

## Electrical Engineering Applications

### 1. **Unbalanced Voltage Detection**
- Identifies voltage unbalance in power systems
- Calculates unbalance factor percentage
- Shows impact on motor performance

### 2. **Motor Derating**
- Negative sequence creates reverse rotating field
- Additional heating in rotor (I² losses)
- Reduced efficiency and torque capability

### 3. **Power Quality Analysis**
- Symmetrical components for fault analysis
- Sequence impedance determination
- Harmonic analysis framework

### 4. **Motor Starting Studies**
- Transient current and torque profiles
- Acceleration time calculation
- Thermal limits verification

### 5. **Load Matching**
- Torque-speed characteristics
- Optimal operating point determination
- Efficiency optimization

### 6. **Educational Tool**
- Visualize phasor relationships
- Compare ODE solver methods
- Understand motor dynamics

---

## ODE Solver Comparison

### RK45 (Runge-Kutta 4th Order)
- **Accuracy**: High (4th order)
- **Speed**: Moderate
- **Use case**: Accurate transient analysis
- **Error**: O(h⁵)

### Euler Method
- **Accuracy**: Low (1st order)
- **Speed**: Fast
- **Use case**: Quick approximations
- **Error**: O(h²)

**Recommendation**: Use RK45 for final analysis, Euler for quick checks.

---

## Sample Results (Example 6.2)

### Operating Conditions
- V_ab = 450 V, V_bc = 470 V, V_ca = 440 V
- Speed = 1770 rpm
- Slip = 0.025 (2.5%)

### Expected Results
```
Symmetrical Components:
  Positive Sequence:  ~260 V
  Negative Sequence:  ~8-12 V (3-4%)

Phase Currents:
  I_a, I_b, I_c:      Unbalanced (±5-10% variation)

Torque:
  Positive Sequence:  High (forward)
  Negative Sequence:  Low (braking)
  Total:              Net forward torque

Efficiency:           Reduced due to unbalance (~2-3% loss)
```

---

## Troubleshooting

### GUI doesn't start
```bash
# Check Tkinter installation
python3 -c "import tkinter"

# If error, install python3-tk
sudo apt-get install python3-tk  # Ubuntu/Debian
```

### Import errors
```bash
# Install missing packages
pip install numpy matplotlib scipy
```

### Plots not displaying
```bash
# Ensure matplotlib backend is correct
import matplotlib
matplotlib.use('TkAgg')
```

---

## Code Structure

```
wound_rotor_induction_motor_lab.py
│
├── InductionMotorModel          # Motor mathematical model
│   ├── phase_voltages_from_line()
│   ├── symmetrical_components()
│   ├── calculate_slip()
│   ├── calculate_torque_steady_state()
│   ├── calculate_currents()
│   ├── calculate_power_and_efficiency()
│   └── motor_dynamics()         # Differential equations
│
├── MotorSimulator               # Dynamic simulation engine
│   ├── euler_step()             # Euler method
│   ├── rk45_step()              # RK45 method
│   └── simulate_transient()     # Main simulation loop
│
└── MotorAnalysisGUI             # Tkinter GUI application
    ├── create_steady_state_tab()
    ├── create_dynamic_simulation_tab()
    ├── create_voltage_analysis_tab()
    ├── calculate_steady_state()
    ├── start_simulation()
    └── update_voltage_analysis()
```

---

## Advanced Features

### 1. **Real-time Parameter Updates**
- Sliders trigger immediate recalculation
- No need to click "Calculate" repeatedly
- Smooth interactive experience

### 2. **Comprehensive Error Handling**
- Division by zero protection (slip → 0)
- Numerical stability checks
- Graceful degradation

### 3. **Professional Visualization**
- Color-coded phases (R-G-B)
- Grid overlays for readability
- Legend placement optimization
- Value annotations on bar charts

### 4. **Multi-solver Support**
- Easy switching between methods
- Consistent interface
- Performance comparison

---

## Future Enhancements

Potential additions for advanced users:
- Export results to CSV/Excel
- Custom motor parameter input
- Harmonic analysis
- Temperature rise calculation
- Multi-motor comparison
- 3D torque-speed surface plots
- Animation of phasor rotation
- Power factor correction simulation

---

## References

1. **Electric Machinery Fundamentals** - Stephen J. Chapman
2. **Analysis of Electric Machinery and Drive Systems** - Paul Krause
3. **Power System Analysis** - Hadi Saadat (Symmetrical Components)
4. **IEEE Std 112-2017** - IEEE Standard Test Procedure for Polyphase Induction Motors

---

## License

Educational use - Free for academic and learning purposes.

---

## Author

Created for electrical engineering education and motor analysis applications.

**Version:** 1.0
**Date:** 2025
**Python:** 3.7+

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all dependencies are installed
3. Ensure Python version is 3.7 or higher
4. Check that Tkinter is properly installed

---

## Conclusion

This comprehensive lab combines:
- ✅ Theoretical motor analysis
- ✅ Practical engineering calculations
- ✅ Interactive visualization
- ✅ Dynamic simulation
- ✅ Educational value

Perfect for:
- Electrical engineering students
- Motor design engineers
- Power systems analysts
- Educational institutions
- Research and development

**Enjoy exploring wound-rotor induction motor behavior! 🔌⚡**
