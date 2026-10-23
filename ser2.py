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

def move_servo_with_power_bypass(angle):
    print("Flipping Relay 1 ON to feed 5V power to the servo...")
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Closes relay contacts, delivering power
    time.sleep(0.15)                   # Wait for the voltage rail to stabilize
    
    # Calculate Duty Cycle and push microsecond pulses over Pin 36
    duty = 2 + (angle / 180.0) * 10
    servo.ChangeDutyCycle(duty)
    
    # Give the physical servo arm ample time to finish its rotation sweep
    if angle == 180 or angle == 0:
        time.sleep(0.6)  # Longer physical transitions take slightly more time
    else:
        time.sleep(0.4)
    
    print("Flipping Relay 1 OFF to cut power and completely isolate the motor...")
    servo.ChangeDutyCycle(0)           # Turn off the PWM pulse stream
    GPIO.output(RELAY_PIN, GPIO.LOW)   # Opens the relay, killing the 5V line completely

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
        # Read incoming data fragments from the socket connection
        raw_bytes = client_socket.recv(1024)
        if not raw_bytes:
            break
            
        buffer += raw_bytes.decode('utf-8')
        
        # Pull separate command elements delimited by the newline indicator (\n)
        while "\n" in buffer:
            command, buffer = buffer.split("\n", 1)
            command = command.strip()
            
            # Match incoming data against mapped numerical values
            if command in angle_mapping:
                target_angle = angle_mapping[command]
                print("Key received. Moving to angle:")
                print(target_angle)
                move_servo_with_power_bypass(target_angle)
            
            # Break cleanly if the quit parameter is supplied
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
    GPIO.output(RELAY_PIN, GPIO.LOW)  # Ensure relay opens up on crash or close
    GPIO.cleanup()
