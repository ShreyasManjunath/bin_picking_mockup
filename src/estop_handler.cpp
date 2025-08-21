// Copyright 2025 Shreyas Manjunath

#include "bin_picking_mockup/estop_handler.hpp"

#include <cstdint>
#include <memory>
#include <random>

#include "bin_picking_mockup/srv/set_e_stop_state.hpp"
#include "std_msgs/msg/bool.hpp"

namespace bin_picking_mockup {

EStopHandler::EStopHandler() : Node("estop_handler"), is_estop_pressed(false) {
  estop_state_pub_ =
      this->create_publisher<std_msgs::msg::Bool>("/estop_pressed", 10);

  timer_ = this->create_wall_timer(
      std::chrono::seconds(1),
      std::bind(&EStopHandler::publish_estop_state, this));
  service_handle_ =
      this->create_service<bin_picking_mockup::srv::SetEStopState>(
          "set_estop_state",
          std::bind(&EStopHandler::handle_estop_button, this,
                    std::placeholders::_1, std::placeholders::_2));
}

auto EStopHandler::publish_estop_state() -> void {
  auto msg = std_msgs::msg::Bool();
  msg.data = is_estop_pressed;
  estop_state_pub_->publish(msg);
}

auto EStopHandler::handle_estop_button(
    const std::shared_ptr<bin_picking_mockup::srv::SetEStopState::Request>
        request,
    std::shared_ptr<bin_picking_mockup::srv::SetEStopState::Response> response)
    -> void {
  is_estop_pressed = request->pressed;
  response->estop_pressed = is_estop_pressed;
}

}  // namespace bin_picking_mockup
