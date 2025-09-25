To save list of installed packages use:

```
sudo pacman -Qqe > pacman-pkgs-list
```

To install them use:

```
sudo pacman -S --needed - < pacman-pkgs-list
```
