// Copyright 2025 Shreyas Manjunath

#include "bin_picking_mockup/stack_light_handler.hpp"

#include <cstdint>
#include <rclcpp/create_publisher.hpp>
#include <rclcpp/logging.hpp>

#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/int32.hpp"

namespace bin_picking_mockup {

StackLightHandler::StackLightHandler()
    : Node("stack_light_handler"),
      current_stack_light(LightState::OPERATIONAL),
      estop_pressed(false),
      door_closed(true) {
  stack_light_pub_ =
      this->create_publisher<std_msgs::msg::Int32>("/stack_light", 1);
  estop_sub_ = this->create_subscription<std_msgs::msg::Bool>(
      "/estop_pressed", 10, [this](std_msgs::msg::Bool::SharedPtr msg) {
        this->update_state("estop", msg);
      });
  door_sub_ = this->create_subscription<std_msgs::msg::Bool>(
      "/door_closed", 10, [this](std_msgs::msg::Bool::SharedPtr msg) {
        this->update_state("door", msg);
      });
}

auto StackLightHandler::update_state(
    const std::string &name, const std_msgs::msg::Bool::SharedPtr msg) -> void {
  if (name == "estop") {
    estop_pressed = msg->data;
  } else if (name == "door") {
    door_closed = msg->data;
  }
  publish_stack_light();
}

auto StackLightHandler::publish_stack_light() -> void {
  if (estop_pressed) {
    current_stack_light = LightState::ESTOP;
  } else if (!door_closed) {
    current_stack_light = LightState::PAUSED;
  } else {
    current_stack_light = LightState::OPERATIONAL;
  }
  std_msgs::msg::Int32 msg;
  msg.data = static_cast<int>(current_stack_light);
  RCLCPP_DEBUG(this->get_logger(), "StackLight state: %d",
               static_cast<int>(current_stack_light));
  stack_light_pub_->publish(msg);
}

}  // namespace bin_picking_mockup
