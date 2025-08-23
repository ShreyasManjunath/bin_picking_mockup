# Bin Picking Mockup

## Overview

The **Bin Picking Mockup** is a ROS2-based package designed to simulate a bin picking task environment. It integrates Human-Machine Interface (HMI), ROS2 nodes, and REST APIs to provide a complete mockup system for testing and prototyping.

This package provides:

- **ROS2 package** for bin picking mockup simulation
- **API services** for robot and WMS (Warehouse Management System) integration
- **HMI elements** to visualize and control the mockup

---

## ROS2 Package

The ROS2 package simulates the bin picking task environment with the following features:

- **Barcode simulation** – Mock barcode generation for picked parts
- **Stacklight indication** – Emulates industrial stacklight signals (red, yellow, green)
- **E-stop simulation** – Emergency stop trigger and reset handling
- **Door indication and controls** – Simulates door status and interlocks
- **Bin picking task mockup** – Provides a virtual bin picking workflow for integration and testing

---

## API Layer

The API layer provides REST endpoints and ROS2 adapters for external system integration. It contains:

### Robot Adapter

- A ROS2-to-API adapter that exposes ROS2 functionality through REST endpoints
- Allows external systems to control and monitor the robot mockup

### WMS API

- Provides endpoints for **pick actions** and **status updates**
- Designed to integrate with a Warehouse Management System (WMS) to simulate realistic bin picking task flow

---

## Installation

### Prerequisites

- [ROS2 Jazzy](https://docs.ros.org/en/jazzy/index.html) installed
- A working ROS2 workspace (e.g., `ros2_ws`)
- Python 3 and `virtualenv` for API environment

---

### Option 1: Clone via GitHub

```bash
cd ~/ros2_ws/src
git clone https://github.com/ShreyasManjunath/bin_picking_mockup.git

```

- ### Option 2: Download ZIP file

  ```
  cd ~/ros2_ws/src
  unzip /path/to/bin_picking_mockup.zip -d .
  ```

---

- ### Build ROS2 Workspace

  ```
  source /opt/ros/jazzy/setup.bash
  cd ~/ros2_ws
  rosdep install --from-paths . --ignore-src -y --rosdistro jazzy
  colcon build \
  --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo \
                -DCMAKE_CXX_FLAGS=-fdiagnostics-color=always \
                -DBUILD_TESTING=OFF \
  --parallel-workers 16 \
  --event-handler console_direct+
  source ~/ros2_ws/install/setup.bash
  ```

---

- ## API Environment Setup

  ```
  cd ~/ros2_ws/src/bin_picking_mockup
  virtualenv --python=python3.12 venv
  source venv/bin/activate
  pip install -r api/requirements.txt
  ```

  >

  Adjust Python version according to your system.

---

- ## Usage (Local Setup)

  This section explains how to run the bin picking mockup locally on Linux.

- ### 1. Source the ROS2 Workspace

  ```
  source ~/ros2_ws/install/setup.bash
  ```

  >

  Must be done in every terminal used.

---

- ### 2. Launch the Bin Picking Mockup ROS2 Node

  Open a **new terminal**:

  ```
  source ~/ros2_ws/install/setup.bash
  ros2 launch bin_picking_mockup bin_picking_mockup.launch.py
  ```

  This starts the ROS2 nodes for the mockup (HMI simulation, stacklight, barcode, E-stop, and door indications).

---

- ### 3. Run Robot Adapter

  Open another **new terminal**:

  ```
  cd ~/ros2_ws/src/bin_picking_mockup
  source venv/bin/activate
  source ~/ros2_ws/install/setup.bash
  uvicorn robot_adapter:app --host 0.0.0.0 --port 8081
  ```

---

- ### 4. Run WMS API

  Open **another new terminal**:

  ```
  cd ~/ros2_ws/src/bin_picking_mockup
  source venv/bin/activate
  source ~/ros2_ws/install/setup.bash
  ROBOT_BASE_URL=http://localhost:8081 uvicorn wms_api:app --host 0.0.0.0 --port 8080
  ```

---

- ### 5. Run the HMI

  Open **another new terminal**:

  ```
  cd ~/ros2_ws/src/bin_picking_mockup/hmi
  python3 -m http.server 8082
  ```

- Access the HMI in your browser at [http://localhost:8082](http://localhost:8082)
- ⚠️ Make sure the ROS2 nodes and API services are running first.

  **Optional:** Start server from anywhere:

  ```
  python3 -m http.server 8082 --directory ~/ros2_ws/src/bin_picking_mockup/hmi
  ```

---

- ### Terminals Needed
- ROS2 nodes (`ros2 launch ...`)
- Robot Adapter (`uvicorn ...`)
- WMS API (`uvicorn ...`)
- HMI (`python3 -m http.server 8082`)

  >

  ⚠️ Make sure to **source the ROS2 workspace in each terminal** before running any service.
