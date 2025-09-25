#!/usr/bin/env python3
import os
from pathlib import Path
import shutil
import subprocess

cwd = Path.cwd()

# Ensure ~/Pictures exists
pictures_dir = Path.home() / "Pictures"
pictures_dir.mkdir(parents=True, exist_ok=True)

# Define symlink mappings
symlinks = {
    cwd / "config" / "alacritty": Path.home() / ".config" / "alacritty",
    # cwd / "config" / "autorandr": Path.home() / ".config" / "autorandr",  # commented out
    cwd / "config" / "i3": Path.home() / ".config" / "i3",
    cwd / "config" / "polybar": Path.home() / ".config" / "polybar",
    cwd / "background.jpg": pictures_dir / "background.jpg",
    cwd / "config" / "zsh" / ".zshrc": Path.home() / ".zshrc",
    cwd / "config" / "autostart" / "picom.desktop": Path.home() / ".config" / "autostart" / "picom.desktop",
    cwd / "config" / "xorg" / "40-tauchpad-input.conf": Path("/etc/X11/xorg.conf.d/40-tauchpad-input.conf"),
}

for src, dest in symlinks.items():
    src = Path(src)
    dest = Path(dest)

    # Special case: /etc/X11 requires root
    if dest.is_absolute() and str(dest).startswith("/etc/"):
        try:
            backup = Path(str(dest) + ".backup")
            if dest.exists() or dest.is_symlink():
                if not backup.exists():
                    subprocess.run(["sudo", "mv", str(dest), str(backup)], check=True)
                    print(f"Backed up {dest} -> {backup} (sudo)")
                else:
                    subprocess.run(["sudo", "rm", "-rf", str(dest)], check=True)
                    print(f"Removed existing {dest} (backup exists) (sudo)")
            subprocess.run(["sudo", "ln", "-s", str(src), str(dest)], check=True)
            print(f"Linked {src} -> {dest} (sudo)")
        except subprocess.CalledProcessError as e:
            print(f"Failed to link {src} -> {dest} with sudo: {e}")
        continue

    # Normal user-level links
    try:
        backup = dest.with_suffix(dest.suffix + ".backup") if dest.suffix else Path(str(dest) + ".backup")

        if dest.exists() or dest.is_symlink():
            if not backup.exists():
                shutil.move(str(dest), str(backup))
                print(f"Backed up {dest} -> {backup}")
            else:
                if dest.is_dir() and not dest.is_symlink():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
                print(f"Removed existing {dest} (backup already exists)")

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.symlink_to(src)
        print(f"Linked {src} -> {dest}")

    except Exception as e:
        print(f"Failed to link {src} -> {dest}: {e}")

