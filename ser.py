import bluetooth
import RPi.GPIO as GPIO
import time

# Target Pin for Servo
SERVO_PIN = 36

# Setup GPIO using BOARD mode
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Initialize PWM at 50Hz on Pin 36
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

# Dictionary mapping keyboard keys to safe standard angles
angle_mapping = {
    "0": 0,
    "1": 90,
    "2": 180,
    "3": 180  # Capped at 180° for standard hobby servos
}

# Function to translate angle degrees to PWM duty cycle
def set_angle(angle):
    duty = 2 + (angle / 180.0) * 10
    servo.ChangeDutyCycle(duty)
    time.sleep(0.4)             # Give the motor time to physically turn
    servo.ChangeDutyCycle(0)   # Cut off pulse to eliminate holding jitter/buzzing

# Bluetooth Setup matching your architecture
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
port = 3
server_socket.bind(("", port))
server_socket.listen(3)

print("Waiting for RoboRemo Bluetooth connection on port 3...")
client_socket, address = server_socket.accept()
print("Accepted connection from ", address)

buffer = ""

try:
    while True:
        # Read incoming data chunks
        raw_bytes = client_socket.recv(1024)
        if not raw_bytes:
            break
            
        # Decode and add to buffer
        buffer += raw_bytes.decode('utf-8')
        
        # Process commands delimited by newline
        while "\n" in buffer:
            command, buffer = buffer.split("\n", 1)
            command = command.strip()
            
            # Direct check for the key mappings
            if command in angle_mapping:
                target_angle = angle_mapping[command]
                print(f"Key '{command}' pressed ➡️ Moving to {target_angle}°")
                set_angle(target_angle)
            
            # Handle quit command
            elif command == "q":
                print("Quit command received.")
                break
                
        if command == "q":
            break

except KeyboardInterrupt:
    print("\nScript manually interrupted.")

finally:
    print("Closing connections and cleaning up GPIO...")
    client_socket.close()
    server_socket.close()
    servo.stop()
    GPIO.cleanup()
