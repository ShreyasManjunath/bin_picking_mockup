// Copyright 2025 Shreyas Manjunath

#pragma once

#include <atomic>
#include <cstdint>
#include <memory>
#include <rclcpp_action/server.hpp>
#include <string>

#include "bin_picking_mockup/action/fake_bin_pick.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/int32.hpp"

using FakeBinPick = bin_picking_mockup::action::FakeBinPick;

namespace bin_picking_mockup {

class BinPickServer : public rclcpp::Node {
 public:
  BinPickServer();
  ~BinPickServer() override = default;

 private:
  bool estop_pressed;
  bool door_closed;
  int32_t barcode;

  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr estop_sub_;
  rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr door_sub_;
  rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr barcode_sub_;

  rclcpp_action::Server<FakeBinPick>::SharedPtr action_server_;

  auto handle_goal(const rclcpp_action::GoalUUID &,
                   std::shared_ptr<const FakeBinPick::Goal> goal)
      -> rclcpp_action::GoalResponse;

  auto handle_cancel(
      const std::shared_ptr<rclcpp_action::ServerGoalHandle<FakeBinPick>>
          goal_handle) -> rclcpp_action::CancelResponse;

  auto handle_accepted(
      const std::shared_ptr<rclcpp_action::ServerGoalHandle<FakeBinPick>>
          goal_handle) -> void;
};
}  // namespace bin_picking_mockup
