



import bluetooth
import RPi.GPIO as GPIO
import time

# Pin Definitions based on your physical setup
SERVO_PIN = 36  # Direct PWM Signal Pin
RELAY_PIN = 38  # Controls Relay 1 (RL1) to switch 5V power

# Setup GPIO using BOARD mode
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Keep the relay open (OFF) initially so no power flows to the servo
GPIO.output(RELAY_PIN, GPIO.LOW)

# Initialize PWM at 50Hz on Pin 36
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

# Dictionary mapping keyboard keys to standard angles
angle_mapping = {
    "0": 0,
    "1": 90,
    "2": 180,
    "3": 180  # Capped at 180 for safety
}

def move_servo_with_persistent_power(angle):
    # Check if the relay is already on. If not, turn it on and keep it on permanently.
    if GPIO.input(RELAY_PIN) == GPIO.LOW:
        print("Flipping Relay 1 ON to feed persistent 5V power to the servo...")
        GPIO.output(RELAY_PIN, GPIO.HIGH)  # Closes relay contacts, delivering power
        time.sleep(0.3)                    # Give the power rail plenty of time to stabilize
    
    # Calculate Duty Cycle and push microsecond pulses over Pin 36
    duty = 2 + (angle / 180.0) * 10
    print(f"Sending PWM pulse stream to target angle: {angle} degrees")
    servo.ChangeDutyCycle(duty)
    
    # Give the physical servo arm ample time to finish its rotation sweep
    time.sleep(0.8)  
    
    # De-jitter the line but DO NOT turn off the relay
    servo.ChangeDutyCycle(0) 
    print("Movement complete. Holding position with relay power active.")

# Bluetooth Socket Setup matching your architecture
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
port = 3
server_socket.bind(("", port))
server_socket.listen(3)

print("Waiting for RoboRemo Bluetooth connection on port 3...")
client_socket, address = server_socket.accept()
print("Accepted connection from:")
print(address)

buffer = ""

try:
    while True:
        raw_bytes = client_socket.recv(1024)
        if not raw_bytes:
            break
            
        buffer += raw_bytes.decode('utf-8')
        
        while "\n" in buffer:
            command, buffer = buffer.split("\n", 1)
            command = command.strip()
            
            # Check for angle command keys (0, 1, 2, 3)
            if command in angle_mapping:
                target_angle = angle_mapping[command]
                print("\n--- New Position Command ---")
                print(f"Key received: {command}. Moving to angle: {target_angle}")
                move_servo_with_persistent_power(target_angle)
            
            # Explicit master power cutoff key
            elif command == "9":
                print("\n--- Power Cutoff Command ---")
                print("Key '9' received. Flipping Relay 1 OFF to cut servo power completely.")
                servo.ChangeDutyCycle(0)           # Safeguard: stop pulses
                GPIO.output(RELAY_PIN, GPIO.LOW)   # Opens the relay, killing the 5V line
            
            elif command == "q":
                print("Quit command received.")
                break
                
        if command == "q":
            break

except KeyboardInterrupt:
    print("Script manually interrupted by user.")

finally:
    print("Resetting pins and safely closing connection lines...")
    client_socket.close()
    server_socket.close()
    servo.stop()
    GPIO.output(RELAY_PIN, GPIO.LOW)  # Safety shutoff on exit
    GPIO.cleanup()
