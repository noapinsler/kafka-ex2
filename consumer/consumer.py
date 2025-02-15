from flask import Flask, request, jsonify
from kafka import KafkaConsumer
import json
import logging
import time
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Kafka connection details
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = 'order_updates'

# Consumer setup
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id="order_service_group",
    auto_offset_reset="earliest",  # Ensures we consume from the beginning (if needed)
)

# In-memory storage for order details
order_db = {}

def calculate_shipping_cost(order):
    # Shipping cost is 2% of the totalAmount
    return round(order['totalAmount'] * 0.02, 2)

def process_order(order):
    # Calculate shipping cost only for 'new' orders
    if order['status'].lower() == 'new':
        shipping_cost = calculate_shipping_cost(order)
        order['shippingCost'] = shipping_cost

        # Store the order in-memory
        order_db[order['orderId']] = order

        logging.info(f"Processed order: {order['orderId']} - Shipping Cost: {shipping_cost}")
    else:
        logging.info(f"Order {order['orderId']} status is not 'new', skipping...")

# Start the Kafka consumer in a separate thread
import threading

def consume_orders():
    for message in consumer:
        try:
            order = message.value
            process_order(order)
        except Exception as e:
            logging.error(f"Error processing order: {e}")

# Run the consumer in the background
thread = threading.Thread(target=consume_orders)
thread.daemon = True  # Allows the thread to exit when the main program exits
thread.start()

@app.route('/getAllOrderIdsFromTopic', methods=['GET'])
def get_all_order_ids():
    # Get all order IDs from the order_db in-memory storage
    order_ids = list(order_db.keys())
    return jsonify(orderIds=order_ids), 200

@app.route('/order-details', methods=['GET'])
def get_order_details():
    order_id = request.args.get('orderId')
    if not order_id:
        return jsonify({"error": "orderId is required"}), 400
    
    # Retrieve order from in-memory database
    order = order_db.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
