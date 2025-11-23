# DC Generator Simulator - Installation & Quick Start Guide

## Quick Start (No Dependencies)

If you just want to solve the DC generator problem without the GUI:

```bash
python3 dc_generator_solution.py
```

This standalone script requires **no external dependencies** and will calculate the series winding turns.

**Answer: 6.91 turns per pole**

## Full Installation (With GUI)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install numpy scipy matplotlib
```

### Step 2: Run the Full GUI Application

```bash
python3 dc_generator_simulator.py
```

## System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Linux, macOS, or Windows
- **Display**: Required for GUI (Tkinter)
- **RAM**: Minimum 512 MB
- **Disk Space**: ~50 MB

## Package Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | ≥1.21.0 | Numerical computations |
| scipy | ≥1.7.0 | ODE solvers and interpolation |
| matplotlib | ≥3.4.0 | Plotting and visualization |
| tkinter | Built-in | GUI framework |

## Installation Methods

### Method 1: Using pip (Recommended)

```bash
# Update pip
python3 -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

### Method 2: Using conda

```bash
conda install numpy scipy matplotlib
```

### Method 3: System Package Manager (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install python3-numpy python3-scipy python3-matplotlib python3-tk
```

### Method 4: System Package Manager (macOS with Homebrew)

```bash
brew install python
pip3 install numpy scipy matplotlib
```

## Verifying Installation

Run this command to verify all packages are installed:

```bash
python3 -c "import numpy, scipy, matplotlib, tkinter; print('✓ All packages installed successfully!')"
```

## Files Overview

```
claude5/
├── dc_generator_simulator.py      # Full GUI application with dynamic simulation
├── dc_generator_solution.py       # Standalone calculation (no dependencies)
├── requirements.txt                # Python package requirements
├── README_DC_GENERATOR.md         # Comprehensive documentation
├── INSTALLATION_GUIDE.md          # This file
└── dc_generator_results.txt       # Generated results (created by app)
```

## Usage

### Option 1: Standalone Solution (Fast)

```bash
python3 dc_generator_solution.py
```

**Output:**
- Detailed step-by-step calculation
- Series turns: 6.91 turns/pole
- Complete verification
- No GUI required

### Option 2: Full GUI Application (Advanced)

```bash
python3 dc_generator_simulator.py
```

**Features:**
- Interactive parameter adjustment
- Real-time dynamic simulation
- Multiple analysis tools
- Professional visualizations
- Export results

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'numpy'"

**Solution:**
```bash
pip install numpy scipy matplotlib
```

### Issue: "ModuleNotFoundError: No module named 'tkinter'"

**Solution (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk
```

**Solution (macOS):**
```bash
brew reinstall python-tk
```

**Solution (Windows):**
Reinstall Python from python.org with "tcl/tk and IDLE" option checked.

### Issue: GUI window doesn't appear

**Check:**
1. Is DISPLAY environment variable set? (Linux/macOS)
2. Is X server running? (Linux)
3. Try running the standalone version instead

### Issue: Simulation runs slowly

**Solutions:**
1. Reduce simulation time
2. Increase time step
3. Use Euler solver instead of RK45
4. Close other applications

### Issue: Plots not updating

**Solution:**
- Click the "Reset" button
- Restart the application
- Check matplotlib backend

## Performance Optimization

### For Faster Simulations:

1. **Reduce time steps:**
   ```
   Simulation Time: 5s (instead of 10s)
   Time Step: 0.05s (instead of 0.01s)
   ```

2. **Use simpler solver:**
   - Select "Euler" instead of "RK45"

3. **Reduce number of points in analysis:**
   ```
   Number of Points: 20 (instead of 50)
   ```

## Advanced Configuration

### Custom OCC Data

Edit `dc_generator_simulator.py` lines 25-26:

```python
self.if_data = np.array([0.2, 0.4, 0.6, ...])  # Your field current data
self.emf_data = np.array([80, 135, 178, ...])   # Your EMF data
```

### Custom Parameters

Modify the `params` dictionary (lines 29-40) for different generator specifications.

## Running on Server (Headless)

If you don't have a display, use the standalone version:

```bash
python3 dc_generator_solution.py > results.txt
```

Or use virtual display (Linux):

```bash
sudo apt-get install xvfb
xvfb-run python3 dc_generator_simulator.py
```

## Exporting Results

### From GUI:
1. Navigate to "Results & Reports" tab
2. Click "Export to Text"
3. Find file: `dc_generator_results.txt`

### From Standalone:
```bash
python3 dc_generator_solution.py > my_results.txt
```

## Getting Help

### Within Application:
- Hover over controls for tooltips
- Check status bar for messages
- View results tab for detailed output

### Command Line:
```bash
python3 dc_generator_solution.py --help  # (if help implemented)
```

### Documentation:
- See `README_DC_GENERATOR.md` for detailed feature guide
- Check code comments for technical details

## Uninstallation

### Remove Python packages:
```bash
pip uninstall numpy scipy matplotlib
```

### Remove application files:
```bash
rm dc_generator_simulator.py dc_generator_solution.py
rm requirements.txt README_DC_GENERATOR.md INSTALLATION_GUIDE.md
```

## Next Steps

After installation:

1. **Learn the Interface:**
   - Run `dc_generator_simulator.py`
   - Explore each tab
   - Try different parameters

2. **Solve the Problem:**
   - Go to "Characteristic Analysis" tab
   - Click "Calculate Series Turns"
   - View detailed results

3. **Run Simulations:**
   - Navigate to "Dynamic Simulation"
   - Adjust parameters
   - Click "Start" and observe real-time plots

4. **Analyze Performance:**
   - Use "Advanced Analysis" tab
   - Try different analysis types
   - Export results

## Support

For technical issues:
- Check Python version: `python3 --version`
- Check installed packages: `pip list`
- Verify tkinter: `python3 -m tkinter`

## Updates

To update the application:
1. Pull latest changes from repository
2. Reinstall requirements: `pip install -r requirements.txt --upgrade`

---

**Enjoy exploring DC generator characteristics!**

*Last updated: 2025-11-23*
