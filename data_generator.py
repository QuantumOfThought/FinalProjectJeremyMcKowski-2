import random
from faker import Faker
from datetime import datetime

# Step 1: Initialize Faker
# We use Faker to generate realistic-looking data like MAC addresses and IPs.
fake = Faker()


class NetworkTrafficGenerator:
    def __init__(self):
        """
        Initialize the generator with 3 specific devices as requested.
        """
        # Step 2: Define our static devices
        # We are creating a list of dictionaries, where each dictionary represents a device.
        self.devices = [
            {
                "name": "Ubiquiti Dream Machine",
                "type": "Router",
                "ip": "192.168.1.1",
                "mac": fake.mac_address(),  # Generate a random MAC address
                "status": "ONLINE",
                "upload_bytes": 0,
                "download_bytes": 0,
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "Home Desktop PC",
                "type": "Desktop",
                "ip": "192.168.1.15",
                "mac": fake.mac_address(),
                "status": "ONLINE",
                "upload_bytes": 0,
                "download_bytes": 0,
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "User iPhone",
                "type": "Mobile",
                "ip": "192.168.1.22",
                "mac": fake.mac_address(),
                "status": "ONLINE",
                "upload_bytes": 0,
                "download_bytes": 0,
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "Home Printer",
                "type": "Printer",
                "ip": "192.168.1.50",
                "mac": fake.mac_address(),
                "status": "OFFLINE",
                "upload_bytes": 0,
                "download_bytes": 0,
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "Guest Android",
                "type": "Mobile",
                "ip": "192.168.1.23",
                "mac": fake.mac_address(),
                "status": "ONLINE",
                "upload_bytes": 0,
                "download_bytes": 0,
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]

    def _simulate_traffic(self):
        """
        Internal method to simulate traffic changes and connection status.
        """
        for device in self.devices:
            # Randomly toggle status for Printer and Android
            if device["name"] in ["Home Printer", "Guest Android"]:
                # 10% chance to flip status
                if random.random() < 0.1:
                    if device["status"] == "ONLINE":
                        device["status"] = "OFFLINE"
                    else:
                        device["status"] = "ONLINE"
                        # Reset timestamp when coming online
                        device["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Only generate traffic if ONLINE
            if device["status"] == "ONLINE":
                if device["type"] == "Router":
                    added_upload = random.randint(1000, 5000000)
                    added_download = random.randint(5000, 10000000)
                elif device["type"] == "Printer":
                    added_upload = random.randint(0, 1000)
                    added_download = random.randint(0, 1000)
                else:
                    added_upload = random.randint(100, 1000000)
                    added_download = random.randint(500, 5000000)

                device["upload_bytes"] += added_upload
                device["download_bytes"] += added_download

                # Update timestamp while active
                device["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_devices(self):
        """
        Public method to get the current state of devices.
        Triggers a traffic simulation update before returning.
        """
        # Step 4: Update traffic before returning data
        self._simulate_traffic()
        return self.devices

    def generate_external_connections(self):
        """
        Generates random external connections for the map visualization.
        Weighted by country as requested:
        - 50% US
        - 10% China
        - 10% Russia
        - 30% EU
        """
        connections = []
        # Generate a random number of active connections (e.g., 10-20)
        num_connections = random.randint(10, 20)

        for _ in range(num_connections):
            r = random.random()

            if r < 0.5:
                # US (Approx Center: 37, -95)
                lat = 37.0 + random.uniform(-10, 10)
                lon = -95.0 + random.uniform(-20, 20)
            elif r < 0.6:
                # China (Approx Center: 35, 104)
                lat = 35.0 + random.uniform(-5, 5)
                lon = 104.0 + random.uniform(-10, 10)
            elif r < 0.7:
                # Russia (Approx Center: 61, 105)
                lat = 61.0 + random.uniform(-10, 10)
                lon = 105.0 + random.uniform(-20, 20)
            else:
                # EU (Approx Center: 50, 10)
                lat = 50.0 + random.uniform(-5, 10)
                lon = 10.0 + random.uniform(-10, 20)

            connections.append({
                "lat": lat,
                "lon": lon
            })

        return connections
