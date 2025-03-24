from prometheus_client import start_http_server, Gauge
import asyncio
from toyota import credentials  # Import credentials as a dictionary
from toyota import MyT  
from datetime import timedelta

# Fetch credentials from toyota.py
creds = credentials  # Access the dictionary directly

# Initialize Toyota API
toyota = MyT(username=creds["username"], password=creds["password"])

# Dictionary to store Prometheus metrics dynamically
metrics = {}

async def get_information():
    """Fetch data from Toyota API and update Prometheus metrics."""
    try:
        # Retrieve all vehicles
        cars = await toyota.get_vehicles()

        for car in cars:
            # Update car data
            await car.update()

            # Collect data from the car object
            car_data = {
                "dashboard": car.dashboard.model_dump() if car.dashboard else {},
                "electric_status": car.electric_status.model_dump() if car.electric_status else {},
                "location": car.location.model_dump() if car.location else {},
                "lock_status": car.lock_status.model_dump() if car.lock_status else {},
                "last_trip": car.last_trip.model_dump() if car.last_trip else {},
            }

            # Flatten the car_data dictionary for Prometheus metrics
            for category, data in car_data.items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        # Handle timedelta objects by converting them to seconds
                        if isinstance(value, timedelta):
                            value = value.total_seconds()

                        # Ensure the value is numeric before setting it in Prometheus
                        if isinstance(value, (int, float)):
                            metric_name = f"toyota_{category}_{key}"
                            if metric_name not in metrics:
                                metrics[metric_name] = Gauge(metric_name, f"Metric for {category} - {key}")
                            metrics[metric_name].set(value)
                        else:
                            print(f"Skipping non-numeric value for {category}_{key}: {value}")

            print(f"Updated metrics for car: {car_data}")

    except Exception as e:
        print(f"Error in get_information: {e}")

async def main():
    """Main asynchronous function."""
    try:
        # Log in to the Toyota API
        await toyota.login()
        print("Login successful!")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # Start HTTP server on port 8000
    start_http_server(8000)
    print("Prometheus exporter running on http://localhost:8000/metrics")

    # Periodically fetch and update metrics
    while True:
        try:
            await get_information()
        except Exception as e:
            print(f"Error fetching information: {e}")
        await asyncio.sleep(10)  # Fetch data every 10 seconds

if __name__ == "__main__":
    # Run the main asynchronous function
    asyncio.run(main())
