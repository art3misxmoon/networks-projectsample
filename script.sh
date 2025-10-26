#!/bin/bash

# Default values
TRACKER_IP="localhost"
TRACKER_PORT=40001
SELF_IP="localhost"
SELF_PORT=5003
WEB_PORT=8083

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tracker-ip)
      TRACKER_IP="$2"
      shift 2
      ;;
    --tracker-port)
      TRACKER_PORT="$2"
      shift 2
      ;;
    --self-ip)
      SELF_IP="$2"
      shift 2
      ;;
    --self-port)
      SELF_PORT="$2"
      shift 2
      ;;
    --web-port)
      WEB_PORT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "Starting PokéBank peer with the following configuration:"
echo "Tracker: $TRACKER_IP:$TRACKER_PORT"
echo "Self: $SELF_IP:$SELF_PORT"
echo "Web Interface: http://$SELF_IP:$WEB_PORT"

# Start the Flask application with the specified parameters
python3 server.py \
  --tracker-ip "$TRACKER_IP" \
  --tracker-port "$TRACKER_PORT" \
  --self-ip "$SELF_IP" \
  --self-port "$SELF_PORT" \
  --web-port "$WEB_PORT"