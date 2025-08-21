// Copyright 2025 Shreyas Manjunath

#include "bin_picking_mockup/door_handler.hpp"

#include <memory>

#include "bin_picking_mockup/srv/set_door_state.hpp"
#include "std_msgs/msg/bool.hpp"

namespace bin_picking_mockup {

DoorStateHandler::DoorStateHandler()
    : Node("door_state_handler"), is_door_closed(true) {
  door_state_pub_ =
      this->create_publisher<std_msgs::msg::Bool>("/door_closed", 10);

  timer_ = this->create_wall_timer(
      std::chrono::seconds(1),
      std::bind(&DoorStateHandler::publish_estop_state, this));
  service_handle_ = this->create_service<bin_picking_mockup::srv::SetDoorState>(
      "set_door_state",
      std::bind(&DoorStateHandler::handle_door_state, this,
                std::placeholders::_1, std::placeholders::_2));
}

auto DoorStateHandler::publish_estop_state() -> void {
  auto msg = std_msgs::msg::Bool();
  msg.data = is_door_closed;
  door_state_pub_->publish(msg);
}

auto DoorStateHandler::handle_door_state(
    const std::shared_ptr<bin_picking_mockup::srv::SetDoorState::Request>
        request,
    std::shared_ptr<bin_picking_mockup::srv::SetDoorState::Response> response)
    -> void {
  is_door_closed = request->closed;
  response->door_closed = is_door_closed;
}

}  // namespace bin_picking_mockup
