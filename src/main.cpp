// Copyright 2025 Shreyas Manjunath

#include <memory>
#include <rclcpp/executors/multi_threaded_executor.hpp>

#include "bin_picking_mockup/barcode_publisher.hpp"
#include "bin_picking_mockup/door_handler.hpp"
#include "bin_picking_mockup/estop_handler.hpp"

int main(int argc, char *argv[]) {
  rclcpp::init(argc, argv);

  auto barcode_publisher =
      std::make_shared<bin_picking_mockup::BarcodePublisher>();
  auto estop_handler = std::make_shared<bin_picking_mockup::EStopHandler>();
  auto door_handler = std::make_shared<bin_picking_mockup::DoorStateHandler>();
  rclcpp::executors::MultiThreadedExecutor executor;

  executor.add_node(barcode_publisher);
  executor.add_node(estop_handler);
  executor.add_node(door_handler);

  executor.spin();
  rclcpp::shutdown();
  return 0;
}
