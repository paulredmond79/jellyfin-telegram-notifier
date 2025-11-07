#!/bin/bash

# Set default values if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}
UMASK=${UMASK:-002}
TZ=${TZ:-Etc/UTC}

# Set timezone
if [ -n "$TZ" ]; then
    echo "Setting timezone to $TZ"
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
    echo $TZ > /etc/timezone
fi

# Get current UID and GID of pythonapp user
CURRENT_UID=$(id -u pythonapp)
CURRENT_GID=$(id -g pythonapp)

echo "Current pythonapp UID:GID is $CURRENT_UID:$CURRENT_GID"
echo "Setting pythonapp UID:GID to $PUID:$PGID"

# Modify the pythonapp user's UID and GID if different from current
if [ "$CURRENT_UID" != "$PUID" ] || [ "$CURRENT_GID" != "$PGID" ]; then
    # Change GID
    if [ "$CURRENT_GID" != "$PGID" ]; then
        groupmod -o -g "$PGID" pythonapp
    fi
    
    # Change UID
    if [ "$CURRENT_UID" != "$PUID" ]; then
        usermod -o -u "$PUID" pythonapp
    fi
    
    echo "Updated pythonapp UID:GID to $(id -u pythonapp):$(id -g pythonapp)"
fi

# Ensure directories exist and have correct ownership
echo "Ensuring /app/log and /app/data directories exist with correct ownership"
mkdir -p /app/log /app/data
chown -R pythonapp:pythonapp /app/log /app/data

# Set umask
echo "Setting umask to $UMASK"
umask $UMASK

# Execute the command as pythonapp user
echo "Starting application as pythonapp user"
exec gosu pythonapp "$@"
