# Repository Guidelines

## Project Structure & Module Organization
`src/` contains the ROS2 C++ node implementations, with public headers in `include/bin_picking_mockup/`. ROS interfaces live in `srv/` and `action/`, and the package entrypoint is `launch/bin_picking_mockup.launch.py`. The REST layer is in `api/` (`robot_adapter.py`, `wms_api.py`, `requirements.txt`). Static HMI assets are under `hmi/`, container setup is in `docker/` plus the compose files at the repo root, and screenshots/documentation assets live in `docs/images/`.

## Build, Test, and Development Commands
Build the ROS2 package from your workspace root:
```bash
colcon build --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=OFF
```
Source the workspace before running nodes or APIs:
```bash
source install/setup.bash
ros2 launch bin_picking_mockup bin_picking_mockup.launch.py
```
Set up the Python API environment:
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.robot_adapter:app --host 0.0.0.0 --port 8081
```
Run the full stack with containers when needed:
```bash
docker compose -f docker-compose.yaml --env-file .env -p task up -d
```
Run repository checks before committing:
```bash
pre-commit run --all-files
```

## Coding Style & Naming Conventions
C++ follows `.clang-format` (Google base, C++23, 2-space indentation) and is linted with `cpplint`. Keep filenames lowercase with underscores, matching the existing node layout such as `stack_light_handler.cpp`. Python is formatted with `black`; use 4-space indentation, `snake_case` for functions/variables, and Pydantic models in `PascalCase`.

## Testing Guidelines
This repository currently relies more on build validation and manual integration checks than on a dedicated `test/` tree. At minimum, verify `colcon build` succeeds, run `pre-commit`, and smoke-test the key flows: ROS launch, `robot_adapter`, `wms_api`, and the HMI. If you add automated tests, keep them close to the affected stack and name them for the behavior under test.

## Commit & Pull Request Guidelines
Follow the existing Conventional Commit style seen in history: `feat(setup): ...`, `docs(readme): ...`, `chore: ...`. Keep commits focused and imperative. Pull requests should describe the user-visible change, list local verification steps, and link the relevant issue. Include screenshots for HMI changes and sample requests/responses for API changes.
