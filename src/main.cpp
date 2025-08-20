// Copyright 2025 Shreyas Manjunath

#include <memory>

#include "bin_picking_mockup/barcode_publisher.hpp"

int main(int argc, char *argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<bin_picking_mockup::BarcodePublisher>());
  rclcpp::shutdown();
  return 0;
}
