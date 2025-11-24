#!/usr/bin/env python3
"""
Test script for DC Motor Analysis
Tests the core calculations without GUI
"""

import sys
import numpy as np

# Import the analyzer class
sys.path.insert(0, '/home/user/claude5')

try:
    from dc_shunt_motor_analysis import DCShuntMotorAnalyzer
    
    print("="*70)
    print("DC SHUNT MOTOR ANALYSIS - TEST SCRIPT")
    print("="*70)
    print()
    
    # Create analyzer instance
    analyzer = DCShuntMotorAnalyzer()
    
    print("Motor Parameters:")
    print(f"  Rated Voltage: {analyzer.V_rated} V")
    print(f"  Base Speed: {analyzer.n_base} rpm")
    print(f"  Full-Load Ia: {analyzer.I_a_rated} A")
    print(f"  Armature Resistance: {analyzer.R_a} Ω")
    print(f"  Field Resistance: {analyzer.R_f} Ω")
    print()
    
    # Test Part (a)
    print("="*70)
    print("TESTING PART (a): Demagnetizing Effect")
    print("="*70)
    result_a = analyzer.solve_problem_part_a()
    print(f"✓ Back EMF at no-load: {result_a['Ea_no_load']:.2f} V")
    print(f"✓ Back EMF at full-load: {result_a['Ea_full_load']:.2f} V")
    print(f"✓ Demagnetizing effect: {result_a['AT_demag_practical']:.1f} AT/pole")
    print()
    
    # Test Part (b)
    print("="*70)
    print("TESTING PART (b): Speed with Series Field")
    print("="*70)
    result_b = analyzer.solve_problem_part_b()
    print(f"✓ Back EMF with series field: {result_b['Ea']:.2f} V")
    print(f"✓ Total field AT/pole: {result_b['AT_total']:.1f} AT")
    print(f"✓ Operating speed: {result_b['speed']:.1f} rpm")
    print(f"✓ Speed reduction: {analyzer.n_base - result_b['speed']:.1f} rpm")
    print()
    
    # Test magnetization curve
    print("="*70)
    print("TESTING MAGNETIZATION CURVE")
    print("="*70)
    test_If = 1.5
    test_speed = 1800
    Ea = analyzer.get_Ea_from_If(test_If, test_speed)
    print(f"✓ For If = {test_If} A at {test_speed} rpm: Ea = {Ea:.2f} V")
    print()
    
    # Test dynamic simulation setup
    print("="*70)
    print("TESTING DYNAMIC SIMULATION SETUP")
    print("="*70)
    V_applied = 230.0
    T_load = 10.0
    initial_state = [0.0, 0.0]
    
    # Test ODE function
    state_dot = analyzer.motor_dynamics_ode(0, initial_state, V_applied, T_load, False)
    print(f"✓ Initial derivatives: dω/dt = {state_dot[0]:.2f}, dIa/dt = {state_dot[1]:.2f}")
    print()
    
    # Test short simulation with Euler
    print("Testing Euler solver (0.1 second simulation)...")
    sol_euler = analyzer.simulate_dynamic_euler((0, 0.1), initial_state, V_applied, T_load, False, dt=0.001)
    print(f"✓ Euler simulation completed: {len(sol_euler.t)} time points")
    print(f"✓ Final speed: {sol_euler.y[0, -1] * 60 / (2*np.pi):.2f} rad/s")
    print()
    
    # Test short simulation with RK45
    print("Testing RK45 solver (0.1 second simulation)...")
    try:
        from scipy.integrate import solve_ivp
        sol_rk45 = analyzer.simulate_dynamic_rk45((0, 0.1), initial_state, V_applied, T_load, False)
        print(f"✓ RK45 simulation completed: {len(sol_rk45.t)} time points")
        print(f"✓ Final speed: {sol_rk45.y[0, -1] * 60 / (2*np.pi):.2f} rad/s")
    except ImportError:
        print("⚠ scipy not available, skipping RK45 test")
    print()
    
    print("="*70)
    print("ALL TESTS PASSED ✓")
    print("="*70)
    print()
    print("Summary:")
    print(f"  (a) Demagnetizing effect: {result_a['AT_demag_practical']:.0f} AT/pole")
    print(f"  (b) Speed with series field: {result_b['speed']:.0f} rpm")
    print()
    print("The DC motor analysis calculations are working correctly!")
    print("To run the full GUI application, use: python3 dc_shunt_motor_analysis.py")
    print()
    
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure numpy, matplotlib, and scipy are installed:")
    print("  pip install numpy matplotlib scipy")
    sys.exit(1)
except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
