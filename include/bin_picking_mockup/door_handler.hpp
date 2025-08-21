// Copyright 2025 Shreyas Manjunath

#pragma once

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/service.hpp>

#include "bin_picking_mockup/srv/set_door_state.hpp"
#include "std_msgs/msg/bool.hpp"

namespace bin_picking_mockup {

class DoorStateHandler : public rclcpp::Node {
 public:
  DoorStateHandler();
  ~DoorStateHandler() override = default;
  auto publish_estop_state() -> void;
  auto handle_door_state(
      const std::shared_ptr<bin_picking_mockup::srv::SetDoorState::Request>
          request,
      std::shared_ptr<bin_picking_mockup::srv::SetDoorState::Response> response)
      -> void;

 private:
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr door_state_pub_;
  bool is_door_closed;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Service<bin_picking_mockup::srv::SetDoorState>::SharedPtr
      service_handle_;
};

}  // namespace bin_picking_mockup
