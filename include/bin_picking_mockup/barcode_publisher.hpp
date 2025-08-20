// Copyright 2025 Shreyas Manjunath

#pragma once

#include <cstdint>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/int32.hpp>
#include <vector>

namespace bin_picking_mockup {

class BarcodePublisher : public rclcpp::Node {
 public:
  BarcodePublisher();
  ~BarcodePublisher() override = default;
  void publish_barcode();

 private:
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr barcode_pub_;
  std::vector<int16_t> barcodes = {123, 456, 789, 987, 654};
  int16_t last_barcode;
  rclcpp::TimerBase::SharedPtr timer_;
};

}  // namespace bin_picking_mockup
