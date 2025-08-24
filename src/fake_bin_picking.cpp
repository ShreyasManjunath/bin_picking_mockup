// Copyright 2025 Shreyas Manjunath

#include "bin_picking_mockup/fake_bin_picking.hpp"

#include <chrono>
#include <rclcpp_action/server.hpp>
#include <thread>

namespace bin_picking_mockup {

BinPickServer::BinPickServer()
    : Node("fake_bin_picking_node"), estop_pressed(false), door_closed(true) {
  estop_sub_ = create_subscription<std_msgs::msg::Bool>(
      "/estop_pressed", 10, [this](std_msgs::msg::Bool::SharedPtr msg) {
        estop_pressed = msg->data;
      });

  door_sub_ = create_subscription<std_msgs::msg::Bool>(
      "/door_closed", 10,
      [this](std_msgs::msg::Bool::SharedPtr msg) { door_closed = msg->data; });

  barcode_client_ =
      this->create_client<bin_picking_mockup::srv::GetBarcode>("/get_barcode");

  action_server_ = rclcpp_action::create_server<FakeBinPick>(
      this, "fake_bin_pick",
      std::bind(&BinPickServer::handle_goal, this, std::placeholders::_1,
                std::placeholders::_2),
      std::bind(&BinPickServer::handle_cancel, this, std::placeholders::_1),
      std::bind(&BinPickServer::handle_accepted, this, std::placeholders::_1));

  RCLCPP_INFO(this->get_logger(), "Fake BinPick action server started.");
}

auto BinPickServer::handle_goal(const rclcpp_action::GoalUUID &,
                                std::shared_ptr<const FakeBinPick::Goal> goal)
    -> rclcpp_action::GoalResponse {
  if (estop_pressed || !door_closed) {
    RCLCPP_WARN(this->get_logger(), "Rejecting goal (unsafe).");
    return rclcpp_action::GoalResponse::REJECT;
  }
  RCLCPP_INFO(this->get_logger(), "Accepting goal for taskID: %d",
              goal->task_id);
  return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
}

auto BinPickServer::handle_cancel(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<FakeBinPick>>
        goal_handle) -> rclcpp_action::CancelResponse {
  RCLCPP_WARN(this->get_logger(),
              "Received cancel request for goal. task_id: %d",
              goal_handle->get_goal()->task_id);
  return rclcpp_action::CancelResponse::ACCEPT;
}

auto BinPickServer::handle_accepted(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<FakeBinPick>>
        goal_handle) -> void {
  std::thread([this, goal_handle]() {
    auto feedback = std::make_shared<FakeBinPick::Feedback>();
    for (int i = 0; i <= 10; i += 1) {
      if (goal_handle->is_canceling()) {
        auto result = std::make_shared<FakeBinPick::Result>();
        result->success = false;
        result->message = "Canceled";
        result->barcode = get_barcode_from_service();
        goal_handle->canceled(result);
        return;
      }
      if (estop_pressed || !door_closed) {
        auto res = std::make_shared<FakeBinPick::Result>();
        res->success = false;
        res->message =
            estop_pressed ? "Aborted: ESTOP pressed" : "Aborted: Door opened";
        res->barcode = 0;
        RCLCPP_ERROR(this->get_logger(),
                     "Aborting goal (estop_pressed=%d, door_closed=%d)",
                     estop_pressed, door_closed);
        goal_handle->abort(res);
        return;
      }
      feedback->percent_complete = static_cast<uint8_t>(i * 10);
      goal_handle->publish_feedback(feedback);
      std::this_thread::sleep_for(std::chrono::milliseconds(500));
    }
    auto result = std::make_shared<FakeBinPick::Result>();
    result->success = true;
    result->message = "Pick Successful";
    result->barcode = get_barcode_from_service();
    goal_handle->succeed(result);
  }).detach();
}

auto BinPickServer::get_barcode_from_service() -> int {
  auto request =
      std::make_shared<bin_picking_mockup::srv::GetBarcode::Request>();

  if (!barcode_client_->wait_for_service(std::chrono::seconds(2))) {
    RCLCPP_ERROR(this->get_logger(), "Barcode service not available");
    return 0;  // fallback
  }

  auto future = barcode_client_->async_send_request(request);
  if (future.wait_for(std::chrono::seconds(2)) == std::future_status::ready) {
    return future.get()->barcode;
  } else {
    RCLCPP_ERROR(this->get_logger(),
                 "Timeout waiting for /get_barcode service");
    return 0;
  }
}

}  // namespace bin_picking_mockup
