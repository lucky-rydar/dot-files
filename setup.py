#!/usr/bin/env python3
import os
from pathlib import Path
import shutil

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
    cwd / "config" / "autostart" / "picom.desktop": Path.home() / ".config" / "autostart" / "picom.desktop"
}

for src, dest in symlinks.items():
    try:
        backup = dest.with_suffix(dest.suffix + ".backup") if dest.suffix else Path(str(dest) + ".backup")

        if dest.exists() or dest.is_symlink():
            if not backup.exists():
                # Move existing file/dir to backup
                shutil.move(str(dest), str(backup))
                print(f"Backed up {dest} -> {backup}")
            else:
                # Remove existing since backup already exists
                if dest.is_dir() and not dest.is_symlink():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
                print(f"Removed existing {dest} (backup already exists)")

        # Ensure parent directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Create symlink
        dest.symlink_to(src)
        print(f"Linked {src} -> {dest}")

    except Exception as e:
        print(f"Failed to link {src} -> {dest}: {e}")
