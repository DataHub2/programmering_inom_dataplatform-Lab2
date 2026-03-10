from confluent_kafka import Producer
import json

# Define the connection parameters to the local Docker Kafka instance
conf = {'bootstrap.servers': 'localhost:9092'}

# Initialize the Producer object
producer = Producer(conf)

def delivery_report(err, msg):
    """
    Callback function that triggers upon successful or failed message delivery.
    """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered successfully to topic '{msg.topic()}' at partition [{msg.partition()}]")

# Mock data simulating an event in the ETL pipeline
mock_event = {
    "event_type": "api_extraction",
    "status": "success",
    "source": "riksdagen_mock_data",
    "rows_processed": 349
}

# Serialize the dictionary to a JSON string and encode to UTF-8 bytes
serialized_event = json.dumps(mock_event).encode('utf-8')

print("Transmitting event to Kafka broker...")

# Dispatch the message to the specific topic 'pipeline_events'
producer.produce('pipeline_events', value=serialized_event, callback=delivery_report)

# Block execution to ensure the message is fully processed by the broker
producer.flush()