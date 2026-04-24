from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    config_path = os.path.join(
        get_package_share_directory("wheeleg_vision_bridge"),
        "config",
        "config.yaml",
    )

    return LaunchDescription([
        DeclareLaunchArgument("mode", default_value="idle"),
        DeclareLaunchArgument("dry_run", default_value="true"),
        DeclareLaunchArgument("transport", default_value="tcp"),
        DeclareLaunchArgument("tcp_host", default_value="wheeleg.local"),
        DeclareLaunchArgument("debug_window", default_value="false"),
        DeclareLaunchArgument("presentation_window", default_value="false"),
        DeclareLaunchArgument("presentation_fullscreen", default_value="false"),
        DeclareLaunchArgument("presentation_mirror", default_value="false"),
        DeclareLaunchArgument("presentation_title", default_value="B-BOT Vision Teleoperation"),
        DeclareLaunchArgument("debug_events", default_value="false"),
        DeclareLaunchArgument("stunt_armed", default_value="false"),
        Node(
            package="wheeleg_vision_bridge",
            executable="bridge_node",
            name="wheeleg_vision_bridge",
            output="screen",
            parameters=[
                config_path,
                {
                    "mode": LaunchConfiguration("mode"),
                    "dry_run": ParameterValue(LaunchConfiguration("dry_run"), value_type=bool),
                    "transport": LaunchConfiguration("transport"),
                    "tcp_host": LaunchConfiguration("tcp_host"),
                    "debug_window": ParameterValue(LaunchConfiguration("debug_window"), value_type=bool),
                    "presentation_window": ParameterValue(LaunchConfiguration("presentation_window"), value_type=bool),
                    "presentation_fullscreen": ParameterValue(LaunchConfiguration("presentation_fullscreen"), value_type=bool),
                    "presentation_mirror": ParameterValue(LaunchConfiguration("presentation_mirror"), value_type=bool),
                    "presentation_title": LaunchConfiguration("presentation_title"),
                    "debug_events": ParameterValue(LaunchConfiguration("debug_events"), value_type=bool),
                    "stunt_armed": ParameterValue(LaunchConfiguration("stunt_armed"), value_type=bool),
                },
            ],
        )
    ])
