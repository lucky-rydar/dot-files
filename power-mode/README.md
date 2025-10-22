# Power Mode - CPU/GPU Performance Manager

Lightweight Python CLI utility to control CPU/GPU performance profiles and monitor system power draw on Debian with Intel CPU + NVIDIA GPU.

## Quick Start

### 1. Check current status
```bash
./power-mode.py status
```

### 2. List available modes
```bash
./power-mode.py list-modes
```

### 3. Apply a mode
```bash
sudo ./power-mode.py apply max
```

### 4. Restore previous settings
```bash
sudo ./power-mode.py restore-backup
```

## Features

- ✅ CPU frequency and governor control
- ✅ CPU core online/offline management
- ✅ NVIDIA GPU power limit control
- ✅ Real-time power monitoring
- ✅ Automatic backup before changes
- ✅ Auto-recovery on errors
- ✅ No external dependencies (Python stdlib only)

## Installation

The script is already in place. To use it system-wide:

```bash
# Option 1: Create symlink in PATH
sudo ln -s ~/.config/dot-files/power-mode/power-mode.py /usr/local/bin/power-mode

# Option 2: Add alias to ~/.zshrc
echo 'alias power-mode="~/.config/dot-files/power-mode/power-mode.py"' >> ~/.zshrc
```

## Configuration

Edit `modes.json` to customize power modes. See example modes for reference.

**Important**: Adjust `online_cores` based on your CPU topology. 

### Identifying P-cores vs E-cores

Check with:
```bash
lscpu -e
```

Typical Intel hybrid layout:
- **P-cores** (Performance): CPU 0-11
- **E-cores** (Efficiency): CPU 12-23

See `CPU_TOPOLOGY.md` for more details.

### Frequency Units

Specify CPU frequency in **MHz** in the config:
```json
"max_freq_mhz": 800  // = 800 MHz
```

## Polybar Integration

Add to your Polybar config:

```ini
[module/power]
type = custom/script
exec = ~/.config/dot-files/power-mode/power-mode.py get-power
interval = 2
format = "⚡ <output> W"
```

## Safety

- Built-in sanity checks for frequency/power limits
- Automatic backup before applying modes
- Auto-recovery on errors
- Requires sudo only for write operations

## Troubleshooting

### Power reading shows "Unable to read power"
- Check if battery interface exists: `ls /sys/class/power_supply/BAT*/power_now`
- Try: `cat /sys/class/power_supply/BAT1/power_now`

### NVIDIA GPU commands fail
- Verify nvidia-smi works: `nvidia-smi`
- Check if you're root: `sudo ./power-mode.py apply <mode>`

### CPU frequency not changing
- Check available governors: `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors`
- Verify min/max frequency range: `cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_{min,max}_freq`

## Technical Details

See `.tmp/tech-task.md` for full design documentation.
