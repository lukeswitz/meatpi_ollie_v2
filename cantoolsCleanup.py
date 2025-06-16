#!/bin/bash
# Complete cleanup of MEATPI macOS setup

echo "🧹 Cleaning up MEATPI macOS setup..."

# 1. Remove the symlinks directory
if [ -d "$HOME/meatpi-devices" ]; then
    echo "Removing ~/meatpi-devices directory..."
    sudo rm -rf "$HOME/meatpi-devices"
    echo "✓ Removed ~/meatpi-devices"
fi

# 2. Remove the launch daemon plist (if it exists)
PLIST_PATH="/Library/LaunchDaemons/com.meatpi.usbserial.plist"
if [ -f "$PLIST_PATH" ]; then
    echo "Removing launch daemon..."
    sudo launchctl unload "$PLIST_PATH" 2>/dev/null
    sudo rm -f "$PLIST_PATH"
    echo "✓ Removed launch daemon"
fi

# 3. Remove the monitoring script
if [ -f "/usr/local/bin/meatpi-usb-monitor.sh" ]; then
    echo "Removing monitoring script..."
    sudo rm -f "/usr/local/bin/meatpi-usb-monitor.sh"
    echo "✓ Removed monitoring script"
fi

# 4. Remove the setup script
if [ -f "/usr/local/bin/meatpi-usb-setup.sh" ]; then
    echo "Removing setup script..."
    sudo rm -f "/usr/local/bin/meatpi-usb-setup.sh"
    echo "✓ Removed setup script"
fi

# 5. Remove symlink directory in /usr/local (if it exists)
if [ -d "/usr/local/dev/meatpi" ]; then
    echo "Removing /usr/local/dev/meatpi..."
    sudo rm -rf "/usr/local/dev/meatpi"
    echo "✓ Removed /usr/local/dev/meatpi"
fi

# 6. Remove any aliases from shell profiles
for profile in ~/.zshrc ~/.bash_profile ~/.bashrc; do
    if [ -f "$profile" ] && grep -q "meatpi" "$profile"; then
        echo "Removing meatpi aliases from $profile..."
        sed -i.bak '/meatpi/d' "$profile"
        echo "✓ Cleaned $profile (backup saved as ${profile}.bak)"
    fi
done

# 7. Clean up any remaining processes
if pgrep -f "meatpi-usb-monitor" > /dev/null; then
    echo "Stopping any running MEATPI processes..."
    sudo pkill -f "meatpi-usb-monitor"
    echo "✓ Stopped processes"
fi

echo ""
echo "🎉 Cleanup complete! All MEATPI setup has been removed."
echo ""
echo "Your original USB devices are still available at:"
ls /dev/cu.wchusbserial* 2>/dev/null || echo "No wchusbserial devices found"
echo ""
echo "You can now use the original device paths directly:"
echo "  /dev/cu.wchusbserial01234567891"
echo "  /dev/cu.wchusbserial01234567893" 
echo "  /dev/cu.wchusbserial01234567895"
echo "  /dev/cu.wchusbserial01234567897"