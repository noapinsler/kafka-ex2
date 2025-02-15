from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json
import random
from datetime import datetime
import os
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Kafka connection details
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
producer = KafkaProducer(
  bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
  value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

KAFKA_TOPIC = 'order_updates'

# In-memory set to track processed order IDs
processed_order_ids = set()

@app.route('/create-order', methods=['POST'])
def create_order():
  try:
    # Input validation
    data = request.json
    required_fields = ["orderId", "customerId", "orderDate", "items", "totalAmount", "currency", "status"]
    if not all(field in data for field in required_fields):
      return jsonify({"error": "Invalid input. Missing one or more required fields."}), 400

    order_id = data['orderId']

    # Check for duplicate order ID
    if order_id in processed_order_ids:
      logging.warning(f"Duplicate order ID detected: {order_id}")
      return jsonify({"error": f"Order ID {order_id} has already been processed."}), 400

    processed_order_ids.add(order_id)

    # Validate and process items
    items = data['items']
    if not isinstance(items, list) or len(items) == 0:
      return jsonify({"error": "Items must be a non-empty list."}), 400

    total_amount_calculated = 0
    for item in items:
      if not all(k in item for k in ["itemId", "quantity", "price"]):
        return jsonify({"error": "Each item must have itemId, quantity, and price."}), 400
      if item['quantity'] <= 0 or item['price'] <= 0:
        return jsonify({"error": "Quantity and price must be positive numbers."}), 400
      total_amount_calculated += item['quantity'] * item['price']

    # Validate total amount
    if round(total_amount_calculated, 2) != round(data['totalAmount'], 2):
      return jsonify({"error": "totalAmount does not match sum of item prices."}), 400

    # Construct the order
    order = {
      "orderId": data["orderId"],
      "customerId": data["customerId"],
      "orderDate": data["orderDate"],
      "items": data["items"],
      "totalAmount": data["totalAmount"],
      "currency": data["currency"],
      "status": data["status"],
      "timestamp": int(time.time() * 1000)
    }

    # Publish to Kafka
    try:
      producer.send(KAFKA_TOPIC, order)
      logging.info(f"Order published: {order}")
      return jsonify(order), 200
    except Exception as e:
      logging.error(f"Kafka publishing error: {e}")
      return jsonify({"error": "Failed to publish order to Kafka.", "details": str(e)}), 500

  except Exception as e:
    logging.error(f"Error processing order: {str(e)}")
    return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

@app.route('/update-order', methods=['PUT'])
def update_order():
  try:
    data = request.json
    required_fields = ["orderId", "status"]
    if not all(field in data for field in required_fields):
      return jsonify({"error": "Invalid input. Missing orderId or status."}), 400

    order_id = data.get('orderId')
    status = data.get('status')

    if order_id not in processed_order_ids:
      return jsonify({"error": "Order ID not found"}), 404

    order_update = {
      "orderId": order_id,
      "status": status,
      "timestamp": int(time.time() * 1000)
    }

    try:
      producer.send(KAFKA_TOPIC, order_update)
      logging.info(f"Order status updated: {order_update}")
      return jsonify({"message": f"Order {order_id} updated to {status}"}), 200
    except Exception as e:
      logging.error(f"Kafka publishing error: {e}")
      return jsonify({"error": "Failed to publish order update to Kafka.", "details": str(e)}), 500

  except Exception as e:
    logging.error(f"Error updating order: {str(e)}")
    return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
