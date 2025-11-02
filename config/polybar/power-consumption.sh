#!/bin/bash

# Check if AC adapter is connected
if [ -f "/sys/class/power_supply/ACAD/online" ]; then
    ac_online=$(cat /sys/class/power_supply/ACAD/online)
else
    # Fallback for systems with different AC adapter naming
    ac_online=0
fi

# Only show power consumption when on battery (ACAD/online == 0)
if [ "$ac_online" -eq 0 ]; then
    if [ -f "/sys/class/power_supply/BAT1/power_now" ] && \
       [ -f "/sys/class/power_supply/BAT1/energy_now" ] && \
       [ -f "/sys/class/power_supply/BAT1/energy_full" ]; then
        
        power_uw=$(cat /sys/class/power_supply/BAT1/power_now)
        energy_now_uw=$(cat /sys/class/power_supply/BAT1/energy_now)
        
        # Convert microwatts to watts
        power_w=$(echo "scale=1; $power_uw / 1000000" | bc)
        
        # Calculate time remaining in minutes
        # energy_now (µWh) / power_now (µW) = time (hours)
        # Then multiply by 60 to get minutes
        if [ "$power_uw" -gt 0 ]; then
            time_minutes=$(echo "scale=3; ($energy_now_uw / $power_uw) * 60" | bc | cut -d. -f1)
            echo "${power_w} W - ${time_minutes} min"
        else
            echo "${power_w} W"
        fi
    fi
else
    # Show nothing when plugged in
    echo ""
fi
