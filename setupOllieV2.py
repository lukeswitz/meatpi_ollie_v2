#!/bin/bash
# macOS USB Serial Device Setup
# meatpi.com macOS version

SYMLINK_DIR="$HOME/meatpi-devices"

echo "Creating MEATPI device symlinks in $SYMLINK_DIR..."

# Create directory if it doesn't exist
mkdir -p "$SYMLINK_DIR"

# Check if we need sudo for operations
NEED_SUDO=false
if [[ -e "$SYMLINK_DIR"/MEATPI-* ]] && [[ $(stat -f "%Su" "$SYMLINK_DIR"/MEATPI-* 2>/dev/null | head -1) == "root" ]]; then
    NEED_SUDO=true
fi

# Remove old symlinks
if [ "$NEED_SUDO" = true ]; then
    echo "Removing old root-owned symlinks..."
    sudo rm -f "$SYMLINK_DIR"/MEATPI-* 2>/dev/null
else
    rm -f "$SYMLINK_DIR"/MEATPI-* 2>/dev/null
fi

# Fix directory ownership if needed
if [[ $(stat -f "%Su" "$SYMLINK_DIR") == "root" ]]; then
    echo "Fixing directory ownership..."
    sudo chown "$(whoami):staff" "$SYMLINK_DIR"
fi

# Create symlinks for CH343 devices as regular user
for device in /dev/cu.wchusbserial*; do
    if [[ -e "$device" ]]; then
        device_num=$(echo "$device" | grep -o '[0-9]$')
        echo "Found device: $device (ending in $device_num)"
        
        case "$device_num" in
            1) ln -sf "$device" "$SYMLINK_DIR/MEATPI-CAN0" && echo "  -> MEATPI-CAN0" ;;
            3) ln -sf "$device" "$SYMLINK_DIR/MEATPI-UARTA" && echo "  -> MEATPI-UARTA" ;;
            5) ln -sf "$device" "$SYMLINK_DIR/MEATPI-UARTB" && echo "  -> MEATPI-UARTB" ;;
            7) ln -sf "$device" "$SYMLINK_DIR/MEATPI-RS232" && echo "  -> MEATPI-RS232" ;;
            9) ln -sf "$device" "$SYMLINK_DIR/MEATPI-RS485" && echo "  -> MEATPI-RS485" ;;
        esac
    fi
done

echo ""
echo "Device symlinks created in: $SYMLINK_DIR"
ls -la "$SYMLINK_DIR/"

echo ""
echo "✅ Setup complete! Your devices are ready:"
if [[ -L "$SYMLINK_DIR/MEATPI-CAN0" ]]; then
    echo "   CAN Interface:  $SYMLINK_DIR/MEATPI-CAN0 -> $(readlink "$SYMLINK_DIR/MEATPI-CAN0")"
fi
if [[ -L "$SYMLINK_DIR/MEATPI-UARTA" ]]; then
    echo "   UART A:         $SYMLINK_DIR/MEATPI-UARTA -> $(readlink "$SYMLINK_DIR/MEATPI-UARTA")"
fi
if [[ -L "$SYMLINK_DIR/MEATPI-UARTB" ]]; then
    echo "   UART B:         $SYMLINK_DIR/MEATPI-UARTB -> $(readlink "$SYMLINK_DIR/MEATPI-UARTB")"
fi
if [[ -L "$SYMLINK_DIR/MEATPI-RS232" ]]; then
    echo "   RS232:          $SYMLINK_DIR/MEATPI-RS232 -> $(readlink "$SYMLINK_DIR/MEATPI-RS232")"
fi

echo ""
echo "Usage: Replace device paths in your apps with these symlinks"
echo "Run again anytime with: ./olliev2_macOS.sh"