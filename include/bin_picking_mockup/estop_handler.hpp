// Copyright 2025 Shreyas Manjunath

#pragma once

#include <cstdint>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/service.hpp>

#include "bin_picking_mockup/srv/set_e_stop_state.hpp"
#include "std_msgs/msg/bool.hpp"

namespace bin_picking_mockup {

class EStopHandler : public rclcpp::Node {
 public:
  EStopHandler();
  ~EStopHandler() override = default;
  auto publish_estop_state() -> void;
  auto handle_estop_button(
      const std::shared_ptr<bin_picking_mockup::srv::SetEStopState::Request>
          request,
      std::shared_ptr<bin_picking_mockup::srv::SetEStopState::Response>
          response) -> void;

 private:
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr estop_state_pub_;
  bool is_estop_pressed;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Service<bin_picking_mockup::srv::SetEStopState>::SharedPtr
      service_handle_;
};

}  // namespace bin_picking_mockup
