from mqtt_handler import start_mqtt, fleet_data

print("======================================")
print("       NMDC CENTRAL SERVER")
print("======================================")

client = start_mqtt()

client.loop_forever()
