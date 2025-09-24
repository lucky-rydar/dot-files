#!/bin/bash
# Enable necessary systemd services after installation

# Network manager
sudo systemctl enable NetworkManager

# Display Manager
sudo systemctl enable lightdm

# Power management
sudo systemctl enable tlp
