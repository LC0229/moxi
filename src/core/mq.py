"""RabbitMQ message queue connector (similar to llm-twin-course)."""

from typing import Optional, Self

import pika

from core import get_logger, settings

logger = get_logger(__name__)


class RabbitMQConnection:
    """Singleton class to manage RabbitMQ connection (similar to llm-twin-course)."""

    _instance: Optional["RabbitMQConnection"] = None

    def __new__(cls, *args, **kwargs) -> Self:
        """Singleton pattern."""
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        virtual_host: str = "/",
        fail_silently: bool = False,
    ):
        """Initialize RabbitMQ connection."""
        self.host = host or settings.RABBITMQ_HOST
        self.port = port or settings.RABBITMQ_PORT
        self.username = username or settings.RABBITMQ_DEFAULT_USERNAME
        self.password = password or settings.RABBITMQ_DEFAULT_PASSWORD
        self.virtual_host = virtual_host
        self.fail_silently = fail_silently
        self._connection: Optional[pika.BlockingConnection] = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def connect(self):
        """Connect to RabbitMQ."""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    virtual_host=self.virtual_host,
                    credentials=credentials,
                )
            )
            logger.info("Connected to RabbitMQ",
                       host=self.host,
                       port=self.port)
        except pika.exceptions.AMQPConnectionError as e:
            logger.exception("Failed to connect to RabbitMQ")
            if not self.fail_silently:
                raise e

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connection is not None and self._connection.is_open

    def get_channel(self):
        """Get channel."""
        if self.is_connected():
            return self._connection.channel()
        return None

    def close(self):
        """Close connection."""
        if self.is_connected():
            self._connection.close()
            self._connection = None
            logger.info("RabbitMQ connection closed")


def publish_to_rabbitmq(queue_name: str, data: str):
    """Publish data to RabbitMQ queue (similar to llm-twin-course)."""
    try:
        rabbitmq_conn = RabbitMQConnection()
        
        with rabbitmq_conn:
            channel = rabbitmq_conn.get_channel()
            if not channel:
                logger.error("Failed to get RabbitMQ channel")
                return
            
            # Ensure queue exists
            channel.queue_declare(queue=queue_name, durable=True)
            
            # Delivery confirmation
            channel.confirm_delivery()
            
            # Publish message
            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=data,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                ),
            )
            logger.info("Published message to queue", queue=queue_name)
    except pika.exceptions.UnroutableError:
        logger.warning("Message could not be routed", queue=queue_name)
    except Exception as e:
        logger.exception("Error publishing to RabbitMQ", error=str(e))

