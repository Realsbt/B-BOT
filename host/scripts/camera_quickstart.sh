#!/usr/bin/env bash
set -euo pipefail

PORT="${MICRO_ROS_PORT:-9999}"
ROS_DISTRO="${ROS_DISTRO:-humble}"

if [ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
  set +u
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
  set -u
fi

if [ -f "${HOME}/uros_ws/install/setup.bash" ]; then
  set +u
  # shellcheck disable=SC1091
  source "${HOME}/uros_ws/install/setup.bash"
  set -u
fi

export ROS_LOG_DIR="${ROS_LOG_DIR:-/tmp/ros_logs}"
mkdir -p "${ROS_LOG_DIR}"

if command -v ros2 >/dev/null 2>&1 && ros2 pkg executables micro_ros_agent >/dev/null 2>&1; then
  exec ros2 run micro_ros_agent micro_ros_agent udp4 --port "${PORT}" -v4
fi

docker_tty_args=()
if [ -t 0 ] && [ -t 1 ]; then
  docker_tty_args=(-it)
fi

exec docker run "${docker_tty_args[@]}" --rm \
  -v /dev:/dev \
  -v /dev/shm:/dev/shm \
  --privileged \
  --net=host \
  microros/micro-ros-agent:humble udp4 --port "${PORT}" -v4
