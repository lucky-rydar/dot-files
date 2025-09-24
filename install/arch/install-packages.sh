#!/bin/bash
# Update system and install all necessary packages for i3 build

sudo pacman -Syu \

# Editors
nano vim neovim \

# SSH
openssh \

# Monitoring
htop btop smartmontools \

# Download and utilities
wget xdg-utils \

# i3 and utilities
i3-wm i3status i3lock-fancy dmenu \

# Additional to i3
picom feh nerd-fonts \

# Display Manager
lightdm lightdm-gtk-greeter \

# Minimal XFCE utilities
thunar thunar-volman xfce4-settings xfce4-power-manager \

# Terminal and browser
alacritty chromium flameshot \

# Audio stack
pipewire pipewire-pulse wireplumber \

# Network manager
networkmanager network-manager-applet \

# Graphics drivers
mesa mesa-utils xf86-video-intel \

# Power management
tlp \

# Kernel
linux-lts \

# Shell and CLI utilities
sudo git dialog zsh
