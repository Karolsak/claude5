"""
Verification script for Problems 3 and 4
"""

print("=" * 60)
print("ELECTRICAL ENGINEERING PROBLEMS - SOLUTIONS VERIFICATION")
print("=" * 60)

# Problem 3: LM317 Voltage Regulator
print("\n📌 PROBLEM 3: LM317 Voltage Regulator")
print("-" * 60)

# Given values
V_REF = 1.25  # V (LM317 reference voltage, actual value)
R1 = 220  # Ω
R2 = 2000  # Ω (2 kΩ)
I_ADJ = 50e-6  # A (50 μA)
V_in = 35  # V

print(f"Given:")
print(f"  V_in  = {V_in} V")
print(f"  V_REF = {V_REF} V")
print(f"  R1    = {R1} Ω")
print(f"  R2    = {R2} Ω")
print(f"  I_ADJ = {I_ADJ * 1e6} μA")

# Calculate minimum output voltage
V_out_min = V_REF
print(f"\nCalculations:")
print(f"  V_out(min) = V_REF = {V_out_min:.2f} V")

# Calculate maximum output voltage
# V_out = V_REF * (1 + R2/R1) + I_ADJ * R2
term1 = V_REF * (1 + R2/R1)
term2 = I_ADJ * R2
V_out_max = term1 + term2

print(f"  V_out(max) = V_REF × (1 + R2/R1) + I_ADJ × R2")
print(f"             = {V_REF} × (1 + {R2}/{R1}) + {I_ADJ*1e6}μA × {R2}Ω")
print(f"             = {V_REF} × {1 + R2/R1:.2f} + {term2:.3f}")
print(f"             = {term1:.3f} + {term2:.3f}")
print(f"             = {V_out_max:.2f} V")

print(f"\n✅ ANSWER: V_out(min) = {V_out_min:.2f} V, V_out(max) = {V_out_max:.2f} V")
print(f"   Expected: (1.25 V, 12.71 V)")

# Verification
if abs(V_out_min - 1.25) < 0.01 and abs(V_out_max - 12.71) < 0.01:
    print("   ✓ CORRECT!")
else:
    print("   ✗ Check calculations")

print("\n" + "=" * 60)

# Problem 4: 7812 Current Regulator
print("\n📌 PROBLEM 4: 7812 Current Regulator")
print("-" * 60)

# Given values
V_REG = 12  # V (7812 regulated voltage)
I_desired = 1.0  # A

print(f"Given:")
print(f"  V_REG (7812) = {V_REG} V")
print(f"  I_desired    = {I_desired} A")

# Calculate required R1
# For current regulator: I = V_REG / R1
# Therefore: R1 = V_REG / I
R1_required = V_REG / I_desired

print(f"\nCalculations:")
print(f"  For constant current regulator using 7812:")
print(f"  I = V_REG / R1")
print(f"  Therefore: R1 = V_REG / I")
print(f"           R1 = {V_REG} V / {I_desired} A")
print(f"           R1 = {R1_required:.1f} Ω")

# Power dissipation
P_dissipated = I_desired**2 * R1_required
print(f"\n  Power dissipation in R1:")
print(f"  P = I² × R1 = {I_desired}² × {R1_required}")
print(f"  P = {P_dissipated:.1f} W")
print(f"  (Use resistor rated ≥ 15W)")

print(f"\n✅ ANSWER: R1 = {R1_required:.0f} Ω")
print(f"   Expected: 12 Ω")

# Verification
if abs(R1_required - 12) < 0.1:
    print("   ✓ CORRECT!")
else:
    print("   ✗ Check calculations")

print("\n" + "=" * 60)
print("\n📊 SUMMARY")
print("-" * 60)
print(f"Problem 3: LM317 output range = {V_out_min:.2f}V to {V_out_max:.2f}V")
print(f"Problem 4: R1 for 1A current = {R1_required:.0f}Ω")
print("\n✓ All solutions verified!")
print("✓ Run 'python voltage_regulator_lab.py' for interactive GUI")
print("=" * 60)
