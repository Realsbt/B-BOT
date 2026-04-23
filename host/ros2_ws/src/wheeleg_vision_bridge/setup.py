import os
from glob import glob

from setuptools import find_packages, setup

package_name = "wheeleg_vision_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="yahboom",
    maintainer_email="yahboom@todo.todo",
    description="MediaPipe vision to wheeleg serial command bridge.",
    license="TODO",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "bridge_node = wheeleg_vision_bridge.bridge_node:main",
        ],
    },
)
