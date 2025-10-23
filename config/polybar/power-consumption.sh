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
    if [ -f "/sys/class/power_supply/BAT1/power_now" ]; then
        power_uw=$(cat /sys/class/power_supply/BAT1/power_now)
        # Convert microwatts to watts
        power_w=$(echo "scale=1; $power_uw / 1000000" | bc)
        echo "${power_w}"
    fi
else
    # Show nothing when plugged in
    echo ""
fi
