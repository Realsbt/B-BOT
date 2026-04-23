from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    config_path = os.path.join(
        get_package_share_directory("wheeleg_vision_bridge"),
        "config",
        "config.yaml",
    )

    return LaunchDescription([
        Node(
            package="wheeleg_vision_bridge",
            executable="bridge_node",
            name="wheeleg_vision_bridge",
            output="screen",
            parameters=[config_path],
        )
    ])
