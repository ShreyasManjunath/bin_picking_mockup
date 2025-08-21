cmake_minimum_required(VERSION 3.10)
project(bin_picking_mockup)

set(CMAKE_CXX_STANDARD 23)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(rosidl_default_runtime REQUIRED)

set(srv_files
  "srv/GetBarcode.srv"
  "srv/SetEStopState.srv"
  "srv/SetDoorState.srv"
)
set(action_files
  "action/FakeBinPick.action"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${srv_files}
  ${action_files}
)

add_library(${PROJECT_NAME}_lib SHARED
  src/barcode_publisher.cpp
  src/estop_handler.cpp
  src/door_handler.cpp
  src/stack_light_handler.cpp
  src/fake_bin_picking.cpp
)

target_include_directories(${PROJECT_NAME}_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(${PROJECT_NAME}_lib
  rclcpp
  rclcpp_action
  std_msgs
  rosidl_default_runtime
)

rosidl_get_typesupport_target(cpp_typesupport_target "${PROJECT_NAME}" "rosidl_typesupport_cpp")
target_link_libraries(${PROJECT_NAME}_lib "${cpp_typesupport_target}")

add_executable(${PROJECT_NAME}_node
  src/main.cpp
)

target_include_directories(${PROJECT_NAME}_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

target_link_libraries(${PROJECT_NAME}_node
  ${PROJECT_NAME}_lib
)

ament_target_dependencies(${PROJECT_NAME}_node
  rclcpp
  rclcpp_action
  std_msgs
  rosidl_default_runtime
)

install(DIRECTORY include/
  DESTINATION include
)
install(DIRECTORY srv
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY action
  DESTINATION share/${PROJECT_NAME}
)

install(TARGETS
  ${PROJECT_NAME}_lib
  ${PROJECT_NAME}_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
