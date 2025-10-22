#!/usr/bin/env python3
"""
power-mode: Lightweight CPU/GPU performance profile manager
Manages power profiles for Debian systems with Intel CPU + NVIDIA GPU
"""

import argparse
import json
import os
import sys
import time
import subprocess
import glob
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List


# Configuration
def get_real_user_home():
    """Get the real user's home directory, even when run with sudo"""
    # Check if running under sudo
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        # Get the real user's home directory
        import pwd
        try:
            return pwd.getpwnam(sudo_user).pw_dir
        except KeyError:
            pass
    
    # Fall back to current user's home
    return os.path.expanduser("~")


REAL_USER_HOME = get_real_user_home()
DEFAULT_BASE_DIR = os.path.join(REAL_USER_HOME, ".config/dot-files/power-mode")
MODES_FILE = "modes.json"
BACKUP_FILE = "backup.json"
ACTIVE_FILE = "active.json"


class Logger:
    """Simple logger that prints to stdout/stderr"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def info(self, msg: str):
        print(f"[INFO] {msg}", file=sys.stdout)
    
    def debug(self, msg: str):
        if self.verbose:
            print(f"[DEBUG] {msg}", file=sys.stdout)
    
    def error(self, msg: str):
        print(f"[ERROR] {msg}", file=sys.stderr)
    
    def warning(self, msg: str):
        print(f"[WARNING] {msg}", file=sys.stderr)


class PowerReader:
    """Read system power consumption from battery interface"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.battery_path = None
        self._find_battery()
    
    def _find_battery(self):
        """Find battery power interface"""
        power_supply_dir = "/sys/class/power_supply"
        
        # Try common battery names
        for bat_name in ["BAT1", "BAT0", "BAT"]:
            path = f"{power_supply_dir}/{bat_name}/power_now"
            if os.path.exists(path):
                self.battery_path = path
                self.logger.debug(f"Found battery at {path}")
                return
        
        self.logger.warning("Battery power interface not found")
    
    def get_power(self) -> Optional[float]:
        """Get current power draw in watts"""
        if not self.battery_path:
            return None
        
        try:
            with open(self.battery_path) as f:
                power_uw = int(f.read().strip())
            power_w = power_uw / 1_000_000
            self.logger.debug(f"Power reading: {power_w:.2f} W")
            return round(power_w, 2)
        except (FileNotFoundError, ValueError, PermissionError) as e:
            self.logger.error(f"Failed to read power: {e}")
            return None
    
    def is_on_ac(self) -> bool:
        """Check if system is on AC power"""
        acad_path = "/sys/class/power_supply/ACAD/online"
        try:
            with open(acad_path) as f:
                return int(f.read().strip()) == 1
        except (FileNotFoundError, ValueError, PermissionError):
            return False


class CPUManager:
    """Manage CPU frequency, governor, and core online status"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.cpu_base = "/sys/devices/system/cpu"
    
    def get_online_cores(self) -> List[int]:
        """Get list of currently online CPU cores"""
        online = []
        cpu_dirs = glob.glob(f"{self.cpu_base}/cpu[0-9]*")
        
        for cpu_dir in sorted(cpu_dirs):
            cpu_num = int(os.path.basename(cpu_dir)[3:])
            online_path = f"{cpu_dir}/online"
            
            # CPU0 is always online and may not have 'online' file
            if cpu_num == 0:
                online.append(0)
                continue
            
            try:
                with open(online_path) as f:
                    if int(f.read().strip()) == 1:
                        online.append(cpu_num)
            except (FileNotFoundError, ValueError):
                # If no online file, assume it's online
                online.append(cpu_num)
        
        return online
    
    def set_online_cores(self, cores: List[int]):
        """Set which CPU cores should be online"""
        all_cores = self._get_all_cores()
        
        for cpu_num in all_cores:
            if cpu_num == 0:  # CPU0 cannot be offlined
                continue
            
            should_be_online = cpu_num in cores
            online_path = f"{self.cpu_base}/cpu{cpu_num}/online"
            
            try:
                with open(online_path, 'w') as f:
                    f.write('1' if should_be_online else '0')
                self.logger.debug(f"CPU{cpu_num}: {'online' if should_be_online else 'offline'}")
            except (FileNotFoundError, PermissionError) as e:
                self.logger.error(f"Failed to set CPU{cpu_num} state: {e}")
    
    def _get_all_cores(self) -> List[int]:
        """Get list of all CPU cores"""
        cpu_dirs = glob.glob(f"{self.cpu_base}/cpu[0-9]*")
        return sorted([int(os.path.basename(d)[3:]) for d in cpu_dirs])
    
    def get_governor(self) -> Optional[str]:
        """Get current CPU governor"""
        gov_path = f"{self.cpu_base}/cpu0/cpufreq/scaling_governor"
        try:
            with open(gov_path) as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            return None
    
    def set_governor(self, governor: str):
        """Set CPU governor for all online cores"""
        online_cores = self.get_online_cores()
        
        for cpu_num in online_cores:
            gov_path = f"{self.cpu_base}/cpu{cpu_num}/cpufreq/scaling_governor"
            try:
                with open(gov_path, 'w') as f:
                    f.write(governor)
                self.logger.debug(f"CPU{cpu_num}: governor={governor}")
            except (FileNotFoundError, PermissionError) as e:
                self.logger.error(f"Failed to set governor for CPU{cpu_num}: {e}")
    
    def get_max_freq(self) -> Optional[int]:
        """Get current max frequency limit in kHz"""
        freq_path = f"{self.cpu_base}/cpu0/cpufreq/scaling_max_freq"
        try:
            with open(freq_path) as f:
                return int(f.read().strip())
        except (FileNotFoundError, PermissionError, ValueError):
            return None
    
    def set_max_freq(self, freq_khz: int):
        """Set max CPU frequency for all online cores"""
        online_cores = self.get_online_cores()
        
        # Sanity check
        if freq_khz < 400000 or freq_khz > 6000000:
            self.logger.error(f"Invalid frequency {freq_khz} kHz ({freq_khz/1000:.0f} MHz) (range: 400-6000 MHz)")
            return
        
        for cpu_num in online_cores:
            freq_path = f"{self.cpu_base}/cpu{cpu_num}/cpufreq/scaling_max_freq"
            try:
                with open(freq_path, 'w') as f:
                    f.write(str(freq_khz))
                self.logger.debug(f"CPU{cpu_num}: max_freq={freq_khz} kHz ({freq_khz/1000:.0f} MHz)")
            except (FileNotFoundError, PermissionError) as e:
                self.logger.error(f"Failed to set max_freq for CPU{cpu_num}: {e}")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current CPU configuration"""
        return {
            "online_cores": self.get_online_cores(),
            "governor": self.get_governor(),
            "max_freq_khz": self.get_max_freq()
        }


class GPUManager:
    """Manage NVIDIA GPU power and clock limits"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.nvidia_smi = self._find_nvidia_smi()
    
    def _find_nvidia_smi(self) -> Optional[str]:
        """Check if nvidia-smi is available"""
        try:
            result = subprocess.run(
                ["which", "nvidia-smi"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                self.logger.debug(f"Found nvidia-smi at {path}")
                return path
        except Exception as e:
            self.logger.warning(f"nvidia-smi not found: {e}")
        return None
    
    def is_available(self) -> bool:
        """Check if NVIDIA GPU is available"""
        return self.nvidia_smi is not None
    
    def get_power_limit(self) -> Optional[float]:
        """Get current GPU power limit in watts"""
        if not self.is_available():
            return None
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=power.limit", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                value = result.stdout.strip()
                # Handle [N/A] or other non-numeric values
                if value and value != "[N/A]" and not value.startswith("["):
                    return float(value)
        except (ValueError, subprocess.SubprocessError) as e:
            self.logger.debug(f"Could not get GPU power limit: {e}")
        return None
    
    def set_power_limit(self, power_w: int):
        """Set GPU power limit in watts"""
        if not self.is_available():
            self.logger.error("NVIDIA GPU not available")
            return
        
        # Sanity check for RTX 4070 Mobile (typical range: 35-140W)
        if power_w < 10 or power_w > 150:
            self.logger.error(f"Invalid power limit {power_w}W (range: 10-150W)")
            return
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "-pl", str(power_w)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.logger.debug(f"GPU: power_limit={power_w}W")
            else:
                self.logger.error(f"Failed to set GPU power limit: {result.stderr}")
        except subprocess.SubprocessError as e:
            self.logger.error(f"Failed to set GPU power limit: {e}")
    
    def get_clock_limits(self) -> Optional[Dict[str, int]]:
        """Get current GPU clock limits"""
        if not self.is_available():
            return None
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=clocks.gr,clocks.mem", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                clocks = result.stdout.strip().split(", ")
                return {
                    "core": int(clocks[0]),
                    "mem": int(clocks[1])
                }
        except (ValueError, subprocess.SubprocessError, IndexError) as e:
            self.logger.error(f"Failed to get GPU clocks: {e}")
        return None
    
    def set_clock_limits(self, min_mhz: Optional[int], max_mhz: Optional[int]):
        """Set GPU clock limits (basic implementation)"""
        # Note: Clock limiting on NVIDIA requires more complex setup
        # This is a placeholder - full implementation would use nvidia-smi or NVML
        self.logger.warning("GPU clock limiting not fully implemented yet")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current GPU configuration"""
        if not self.is_available():
            return {"available": False}
        
        return {
            "available": True,
            "backend": "nvidia",
            "power_limit_w": self.get_power_limit(),
            "clocks": self.get_clock_limits()
        }


class Snapshot:
    """Handle system state snapshots (backup/restore)"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.cpu_manager = CPUManager(logger)
        self.gpu_manager = GPUManager(logger)
        self.power_reader = PowerReader(logger)
    
    def dump(self) -> Dict[str, Any]:
        """Capture current system state"""
        self.logger.debug("Dumping current system state")
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "machine_id": self._get_machine_id(),
            "cpu": self.cpu_manager.get_current_state(),
            "gpu": self.gpu_manager.get_current_state(),
            "on_ac_power": self.power_reader.is_on_ac()
        }
        
        return snapshot
    
    def save(self, path: str):
        """Save snapshot to file"""
        snapshot = self.dump()
        try:
            with open(path, 'w') as f:
                json.dump(snapshot, f, indent=2)
            self.logger.info(f"Snapshot saved to {path}")
        except IOError as e:
            self.logger.error(f"Failed to save snapshot: {e}")
    
    def load(self, path: str) -> Optional[Dict[str, Any]]:
        """Load snapshot from file"""
        try:
            with open(path) as f:
                snapshot = json.load(f)
            self.logger.debug(f"Loaded snapshot from {path}")
            return snapshot
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load snapshot: {e}")
            return None
    
    def restore(self, snapshot: Dict[str, Any]):
        """Restore system state from snapshot"""
        self.logger.info("Restoring system state from snapshot")
        
        try:
            # Restore CPU settings
            if "cpu" in snapshot:
                cpu = snapshot["cpu"]
                
                if "online_cores" in cpu and cpu["online_cores"]:
                    self.cpu_manager.set_online_cores(cpu["online_cores"])
                
                if "governor" in cpu and cpu["governor"]:
                    self.cpu_manager.set_governor(cpu["governor"])
                
                if "max_freq_khz" in cpu and cpu["max_freq_khz"]:
                    self.cpu_manager.set_max_freq(cpu["max_freq_khz"])
            
            # Restore GPU settings
            if "gpu" in snapshot and snapshot["gpu"].get("available"):
                gpu = snapshot["gpu"]
                
                if "power_limit_w" in gpu and gpu["power_limit_w"]:
                    self.gpu_manager.set_power_limit(int(gpu["power_limit_w"]))
            
            self.logger.info("System state restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore snapshot: {e}")
            return False
    
    def _get_machine_id(self) -> str:
        """Get machine ID for identification"""
        try:
            with open("/etc/machine-id") as f:
                return f.read().strip()
        except IOError:
            return "unknown"


class ModeManager:
    """Manage power mode definitions and application"""
    
    def __init__(self, base_dir: str, logger: Logger):
        self.base_dir = base_dir
        self.logger = logger
        self.modes_path = os.path.join(base_dir, MODES_FILE)
        self.backup_path = os.path.join(base_dir, BACKUP_FILE)
        self.active_path = os.path.join(base_dir, ACTIVE_FILE)
        
        self.cpu_manager = CPUManager(logger)
        self.gpu_manager = GPUManager(logger)
        self.snapshot = Snapshot(logger)
    
    def load_modes(self) -> Optional[Dict[str, Any]]:
        """Load modes from modes.json"""
        try:
            with open(self.modes_path) as f:
                modes = json.load(f)
            self.logger.debug(f"Loaded {len(modes)} modes")
            return modes
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to load modes: {e}")
            return None
    
    def list_modes(self):
        """List all available modes"""
        modes = self.load_modes()
        if not modes:
            print("No modes available")
            return
        
        print("Available modes:")
        for name, config in modes.items():
            desc = config.get("description", "No description")
            print(f"  {name:15s} - {desc}")
    
    def show_mode(self, mode_name: str):
        """Show details of a specific mode"""
        modes = self.load_modes()
        if not modes or mode_name not in modes:
            self.logger.error(f"Mode '{mode_name}' not found")
            return
        
        print(f"Mode: {mode_name}")
        print(json.dumps(modes[mode_name], indent=2))
    
    def apply_mode(self, mode_name: str):
        """Apply a power mode"""
        modes = self.load_modes()
        if not modes or mode_name not in modes:
            self.logger.error(f"Mode '{mode_name}' not found")
            return False
        
        mode = modes[mode_name]
        self.logger.info(f"Applying mode: {mode_name}")
        
        # Step 1: Backup current state
        self.logger.info("Creating backup of current state")
        self.snapshot.save(self.backup_path)
        
        # Step 2: Apply mode settings
        try:
            # Apply CPU settings
            if "cpu" in mode:
                cpu_config = mode["cpu"]
                
                if "online_cores" in cpu_config:
                    cores = self._parse_online_cores(cpu_config["online_cores"])
                    if cores:
                        self.cpu_manager.set_online_cores(cores)
                
                if "governor" in cpu_config:
                    self.cpu_manager.set_governor(cpu_config["governor"])
                
                if "max_freq_mhz" in cpu_config:
                    freq_khz = cpu_config["max_freq_mhz"] * 1000
                    self.cpu_manager.set_max_freq(freq_khz)
            
            # Apply GPU settings
            if "gpu" in mode and self.gpu_manager.is_available():
                gpu_config = mode["gpu"]
                
                if "power_limit_w" in gpu_config:
                    self.gpu_manager.set_power_limit(gpu_config["power_limit_w"])
                
                # Clock limits (if implemented)
                if "gpu_clock_min_mhz" in gpu_config or "gpu_clock_max_mhz" in gpu_config:
                    min_mhz = gpu_config.get("gpu_clock_min_mhz")
                    max_mhz = gpu_config.get("gpu_clock_max_mhz")
                    self.gpu_manager.set_clock_limits(min_mhz, max_mhz)
            
            # Step 3: Record active mode
            self._record_active_mode(mode_name)
            
            self.logger.info(f"Mode '{mode_name}' applied successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply mode: {e}")
            self.logger.info("Attempting to restore from backup")
            
            # Try to restore backup on error
            backup = self.snapshot.load(self.backup_path)
            if backup:
                self.snapshot.restore(backup)
            
            return False
    
    def _parse_online_cores(self, cores_spec) -> List[int]:
        """Parse online_cores specification into list of CPU numbers"""
        # Simple implementation: just accept explicit list
        # Format: [0, 1, 2, 3, 12, 13, 14, 15]
        if isinstance(cores_spec, list) and all(isinstance(c, int) for c in cores_spec):
            return cores_spec
        
        self.logger.warning("Complex online_cores format not yet implemented, skipping")
        return []
    
    def restore_backup(self):
        """Restore system to backed-up state"""
        backup = self.snapshot.load(self.backup_path)
        if not backup:
            self.logger.error("No backup found")
            return False
        
        success = self.snapshot.restore(backup)
        if success:
            # Clear active mode
            self._clear_active_mode()
        return success
    
    def _record_active_mode(self, mode_name: str):
        """Record the currently active mode"""
        active_info = {
            "mode": mode_name,
            "timestamp": datetime.now().isoformat(),
            "config_path": self.modes_path
        }
        
        try:
            with open(self.active_path, 'w') as f:
                json.dump(active_info, f, indent=2)
        except IOError as e:
            self.logger.error(f"Failed to record active mode: {e}")
    
    def _clear_active_mode(self):
        """Clear active mode record"""
        try:
            if os.path.exists(self.active_path):
                os.remove(self.active_path)
        except IOError as e:
            self.logger.error(f"Failed to clear active mode: {e}")
    
    def get_active_mode(self) -> Optional[str]:
        """Get name of currently active mode"""
        try:
            with open(self.active_path) as f:
                active_info = json.load(f)
            return active_info.get("mode")
        except (IOError, json.JSONDecodeError):
            return None


class PowerMode:
    """Main application class"""
    
    def __init__(self, base_dir: str, verbose: bool):
        self.base_dir = base_dir
        self.logger = Logger(verbose)
        self.power_reader = PowerReader(self.logger)
        self.snapshot = Snapshot(self.logger)
        self.mode_manager = ModeManager(base_dir, self.logger)
        
        # Ensure base directory exists
        self._ensure_base_dir()
    
    def _ensure_base_dir(self):
        """Create base directory if it doesn't exist"""
        Path(self.base_dir).mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Using base directory: {self.base_dir}")
    
    def _check_root(self) -> bool:
        """Check if running as root"""
        return os.geteuid() == 0
    
    def get_power(self):
        """Get and print current power draw"""
        power = self.power_reader.get_power()
        if power is not None:
            print(f"{power:.2f}")
        else:
            self.logger.error("Unable to read power")
            sys.exit(1)
    
    def watch_power(self, interval: float = 1.0):
        """Continuously print power draw"""
        try:
            while True:
                power = self.power_reader.get_power()
                if power is not None:
                    print(f"{power:.2f}")
                    sys.stdout.flush()
                time.sleep(interval)
        except KeyboardInterrupt:
            pass
    
    def show_current_params(self):
        """Display current system parameters"""
        snapshot = self.snapshot.dump()
        print("Current system parameters:")
        print(json.dumps(snapshot, indent=2))
    
    def dump_current_params(self):
        """Dump current parameters to backup.json"""
        backup_path = os.path.join(self.base_dir, BACKUP_FILE)
        self.snapshot.save(backup_path)
    
    def status(self):
        """Show system status"""
        print("=== Power Mode Status ===")
        
        # Active mode
        active_mode = self.mode_manager.get_active_mode()
        if active_mode:
            print(f"Active mode: {active_mode}")
        else:
            print("Active mode: None")
        
        # Current power
        power = self.power_reader.get_power()
        if power is not None:
            print(f"Current power: {power:.2f} W")
        
        # AC status
        on_ac = self.power_reader.is_on_ac()
        print(f"Power source: {'AC' if on_ac else 'Battery'}")
        
        # CPU info
        cpu_manager = CPUManager(self.logger)
        online_cores = cpu_manager.get_online_cores()
        governor = cpu_manager.get_governor()
        max_freq = cpu_manager.get_max_freq()
        
        print(f"\nCPU:")
        print(f"  Online cores: {len(online_cores)} ({online_cores})")
        print(f"  Governor: {governor}")
        if max_freq:
            print(f"  Max frequency: {max_freq/1000:.0f} MHz")
        
        # GPU info
        gpu_manager = GPUManager(self.logger)
        if gpu_manager.is_available():
            power_limit = gpu_manager.get_power_limit()
            print(f"\nGPU:")
            print(f"  Available: Yes (NVIDIA)")
            if power_limit:
                print(f"  Power limit: {power_limit:.1f} W")
        else:
            print(f"\nGPU: Not available")


def main():
    parser = argparse.ArgumentParser(
        description="Power mode management utility",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "-d", "--dir",
        default=DEFAULT_BASE_DIR,
        help=f"Base directory (default: {DEFAULT_BASE_DIR})"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Commands
    subparsers.add_parser("get-power", help="Print current power draw (W)")
    
    watch_parser = subparsers.add_parser("watch-power", help="Continuously print power")
    watch_parser.add_argument("interval", nargs="?", type=float, default=1.0,
                             help="Update interval in seconds (default: 1.0)")
    
    subparsers.add_parser("list-modes", help="List available modes")
    
    show_mode_parser = subparsers.add_parser("show-mode", help="Show mode details")
    show_mode_parser.add_argument("name", help="Mode name")
    
    apply_parser = subparsers.add_parser("apply", help="Apply a mode")
    apply_parser.add_argument("name", help="Mode name")
    
    subparsers.add_parser("restore-backup", help="Restore from backup")
    subparsers.add_parser("dump-current-params", help="Dump current parameters to backup")
    subparsers.add_parser("show-current-params", help="Display current parameters")
    subparsers.add_parser("get-active-mode", help="Get currently active mode")
    subparsers.add_parser("status", help="Show system status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize application
    app = PowerMode(args.dir, args.verbose)
    
    # Commands that need root
    write_commands = ["apply", "restore-backup"]
    if args.command in write_commands and not app._check_root():
        print("ERROR: This command requires root privileges", file=sys.stderr)
        print("Please run with sudo", file=sys.stderr)
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == "get-power":
            app.get_power()
        
        elif args.command == "watch-power":
            app.watch_power(args.interval)
        
        elif args.command == "list-modes":
            app.mode_manager.list_modes()
        
        elif args.command == "show-mode":
            app.mode_manager.show_mode(args.name)
        
        elif args.command == "apply":
            success = app.mode_manager.apply_mode(args.name)
            sys.exit(0 if success else 1)
        
        elif args.command == "restore-backup":
            success = app.mode_manager.restore_backup()
            sys.exit(0 if success else 1)
        
        elif args.command == "dump-current-params":
            app.dump_current_params()
        
        elif args.command == "show-current-params":
            app.show_current_params()
        
        elif args.command == "get-active-mode":
            mode = app.mode_manager.get_active_mode()
            if mode:
                print(mode)
            else:
                print("none")
        
        elif args.command == "status":
            app.status()
        
        else:
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
