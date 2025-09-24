#!/bin/bash
# Update system and install all necessary packages for i3 build

sudo pacman -Syu --needed --noconfirm \
  nano vim neovim \
  openssh \
  htop btop smartmontools \
  wget xdg-utils \
  i3-wm i3status i3lock-fancy dmenu \
  picom feh nerd-fonts \
  lightdm lightdm-gtk-greeter \
  thunar thunar-volman xfce4-settings xfce4-power-manager \
  alacritty chromium flameshot \
  pipewire pipewire-pulse wireplumber \
  networkmanager network-manager-applet \
  mesa mesa-utils xf86-video-intel \
  tlp \
  linux-lts \
  sudo git dialog zsh
