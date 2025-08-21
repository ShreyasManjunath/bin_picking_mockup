// Copyright 2025 Shreyas Manjunath

#pragma once

#include <cstdint>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/service.hpp>
#include <std_msgs/msg/int32.hpp>

#include "bin_picking_mockup/srv/get_barcode.hpp"
namespace bin_picking_mockup {

class BarcodePublisher : public rclcpp::Node {
 public:
  BarcodePublisher();
  ~BarcodePublisher() override = default;
  auto publish_barcode() -> void;
  auto handle_get_barcode(
      const std::shared_ptr<bin_picking_mockup::srv::GetBarcode::Request>
      /*request*/,
      std::shared_ptr<bin_picking_mockup::srv::GetBarcode::Response> response)
      -> void;

 private:
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr barcode_pub_;
  int32_t last_barcode;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Service<bin_picking_mockup::srv::GetBarcode>::SharedPtr
      service_handle_;
};

}  // namespace bin_picking_mockup
