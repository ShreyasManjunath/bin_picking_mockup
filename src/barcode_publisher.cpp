// Copyright 2025 Shreyas Manjunath

#include "bin_picking_mockup/barcode_publisher.hpp"

#include <cstdint>
#include <memory>
#include <random>

#include "bin_picking_mockup/srv/get_barcode.hpp"

namespace bin_picking_mockup {

BarcodePublisher::BarcodePublisher()
    : Node("barcode_publisher"), last_barcode(0) {
  barcode_pub_ = this->create_publisher<std_msgs::msg::Int32>("/barcode", 10);

  timer_ = this->create_wall_timer(
      std::chrono::seconds(1),
      std::bind(&BarcodePublisher::publish_barcode, this));
  service_handle_ = this->create_service<bin_picking_mockup::srv::GetBarcode>(
      "get_barcode", std::bind(&BarcodePublisher::handle_get_barcode, this,
                               std::placeholders::_1, std::placeholders::_2));
}

auto BarcodePublisher::publish_barcode() -> void {
  std::random_device rd;
  std::mt19937 gen(rd());
  std::uniform_int_distribution<> dist(100, 999);
  auto msg = std_msgs::msg::Int32();
  msg.data = dist(gen);
  barcode_pub_->publish(msg);
  last_barcode = msg.data;
}

auto BarcodePublisher::handle_get_barcode(
    const std::shared_ptr<
        bin_picking_mockup::srv::GetBarcode::Request> /*request*/,
    std::shared_ptr<bin_picking_mockup::srv::GetBarcode::Response> response)
    -> void {
  response->barcode = static_cast<int32_t>(last_barcode);
}

}  // namespace bin_picking_mockup
