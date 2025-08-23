from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="bin_picking_mockup",
                executable="bin_picking_mockup_node",
                output="screen",
            )
        ]
    )
