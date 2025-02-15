# Order Processing System - Kafka Producer & Consumer

## 1. Full Name and ID Number
- Yarin Baslo - 209344589 
- Noa Pinsler - 313133498

## 2. Kafka Topics Used
- **Kafka Topic:** `order_updates`  
  - **Purpose:** This topic is used for sending and receiving order updates (both order creation and status updates) between the producer and consumer.

## 3. Key Used in the Message
- **Key:** No explicit key is used in the messages.  
  - **Reason:** The system doesn't require message ordering between producers and consumers, so Kafka's default partitioning mechanism is sufficient.

## 4. Error Handling
### Producer:
- **Retry Logic:** The producer attempts to reconnect to Kafka up to 10 times with a 5-second delay, ensuring transient issues don’t cause immediate failure.
- **Missing Fields & Validation:** Ensures required fields are present and valid; returns `400` errors for missing or invalid data.
- **Duplicate Order ID:** Checks for duplicate order IDs and returns an error to prevent re-processing.
- **Kafka Publishing Failures:** If publishing fails, a `500` error is returned to notify the user.

### Consumer:
- **Deserialization Failures:** Logs errors but continues processing valid messages.
- **Order Processing Errors:** Logs errors during processing but continues processing other orders.
- **Missing Order ID:** Returns a `400` or `404` error for missing or invalid order IDs in requests.

### General:
- **Logging & Status Codes:** Errors are logged and appropriate HTTP status codes (`400`, `500`) are returned, providing clear feedback to users.
