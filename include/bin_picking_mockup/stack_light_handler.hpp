// Copyright 2025 Shreyas Manjunath

#pragma once

#include <cstdint>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/service.hpp>
#include <std_msgs/msg/int32.hpp>
#include <string>

#include "std_msgs/msg/bool.hpp"

namespace bin_picking_mockup {

enum class LightState : int { OPERATIONAL = 0, ESTOP = -1, PAUSED = 1 };

class StackLightHandler : public rclcpp::Node {
 public:
  StackLightHandler();
  ~StackLightHandler() override = default;
  auto publish_stack_light() -> void;
  auto update_state(const std::string &name,
                    const std_msgs::msg::Bool::SharedPtr msg) -> void;

 private:
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr stack_light_pub_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr estop_sub_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr door_sub_;
  LightState current_stack_light;
  bool door_closed;
  bool estop_pressed;
};

}  // namespace bin_picking_mockup
