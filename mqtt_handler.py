import json
import paho.mqtt.client as mqtt

fleet_data = {}

BROKER = "localhost"
PORT = 1883
TOPIC = "nmdc/fleet/vehicle"


def on_message(client, userdata, msg):

    try:
        message = json.loads(
            msg.payload.decode("utf-8")
        )

        vehicle_id = message.get(
            "vehicle_id",
            "UNKNOWN"
        )

        fleet_data[vehicle_id] = message

        road_risk = message.get(
            "road_risk",
            {}
        )

        risk_level = road_risk.get(
            "status",
            road_risk.get(
                "risk_level",
                "UNKNOWN"
            )
        )

        print(
            f"[SERVER] Received: "
            f"{vehicle_id} | "
            f"Risk: {risk_level}"
        )

    except Exception as e:
        print(
            "[SERVER] Error processing message:",
            e
        )


def start_mqtt():

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_message = on_message

    print("[SERVER] Connecting to MQTT broker...")

    client.connect(
        BROKER,
        PORT,
        60
    )

    client.subscribe(TOPIC)

    print("[SERVER] Connected to MQTT broker")
    print(f"[SERVER] Subscribed to: {TOPIC}")

    return client
