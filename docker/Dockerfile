FROM ros:jazzy-ros-core AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    ca-certificates \
    lsb-release \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN rm -f /etc/apt/sources.list.d/ros2-latest.list \
    /etc/apt/sources.list.d/ros* || true

# Add updated ROS2 apt key + repo
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/ros2.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws
RUN mkdir -p /opt/task /ws/src

COPY . /ws/src/bin_picking_mockup

RUN /bin/bash -c "source /opt/ros/jazzy/setup.bash && \
    rm -f /etc/ros/rosdep/sources.list.d/20-default.list && \
    rosdep init && \
    rosdep update && \
    rosdep install -t build -t buildtool --from-paths . -riy && \
    colcon build --parallel-workers 16 \
        --merge-install \
        --install-base /opt/task \
        --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
        --packages-up-to bin_picking_mockup"


FROM ros:jazzy-ros-core

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    ca-certificates \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

RUN rm -f /etc/apt/sources.list.d/ros2-latest.list \
    /etc/apt/sources.list.d/ros2* || true

# Add refreshed ROS2 repo
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/ros2.list


COPY --from=builder /opt/task /opt/task

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-rosdep python3-rospkg python3-pip nginx\
    libtar-dev \
    && rm -f /etc/ros/rosdep/sources.list.d/20-default.list \
    && rosdep init \
    && rosdep update \
    && rosdep install -t exec \
       --skip-keys=rviz \
       --skip-keys=rviz2 \
       --from-paths /opt/task/share -riy \
    && export SUDO_FORCE_REMOVE=yes \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /root/.ros/rosdep /var/lib/apt/lists/* /etc/apt/apt.conf.d/proxy

COPY api/ /opt/api/
ENV PYTHONPATH="/opt/api:$PYTHONPATH"

RUN PIP_BREAK_SYSTEM_PACKAGES=1 \
    python3 -m pip install \
      --target /opt/task/lib/$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')/site-packages \
      -r /opt/api/requirements.txt

COPY hmi/ /var/www/html/
COPY hmi/nginx.conf /etc/nginx/conf.d/default.conf


COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
