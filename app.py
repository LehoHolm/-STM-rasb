from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
import smbus
import time
import random

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# Uste info tehtud globaalseks muutujaks, ehk kui pärast interpret_status_bytes() muudetakse kastide staatust muutub siin automaatselt
door1_data = {"lock_status": False, "magnet_status": False, "ir_sensor_status": False}
door2_data = {"lock_status": False, "magnet_status": False, "ir_sensor_status": False}

# Annab STM-ile teada mis uksed tema peab lahti tegema. data_size on mitu ust tehakse lahti 
def open_door(data):
    command = 0x02  
    data_size = 3  
    data = [command, data] 
    slave_address = 21 
    bus = smbus.SMBus(1)  
    print("Sending to address:", slave_address)
    bus.write_i2c_block_data(slave_address, 0, data) 

# Restardib STM ja tema uste haldamis info. data_size on 1 ja kui sellele järngneb 0 annab teada, et tuleb restartida
def reboot_slave():
    command = 0x09  
    data_size = 3  
    data = [command, 0] 
    slave_address = 21  
    bus = smbus.SMBus(1) 
    print("Sending to address:", slave_address)
    bus.write_i2c_block_data(slave_address, 0, data) 

# Annab STM-ile teada mis uksed tema peab haldama. data_size on mitu ust hallatakse 
def send_data_to_slave():
    command = 0x08  
    data_size = 3  
    data = [command, 1, 2]   #hetkel on pandud 1 ja 2, kuidagi peaks tegema lihtsasti skaleeritavaks 
    slave_address = 21  
    bus = smbus.SMBus(1) 
    print("Sending to address:", slave_address)
    bus.write_i2c_block_data(slave_address, 0, data)

# alguses ütleme, et halda 2 ust id-ga 1 ja 2
send_data_to_slave

# iga sekundi tagant küsime infot
def heartbeat_loop():
    while True:
        # Perform any necessary tasks here
        print("Heartbeat")

        # Request response from the slave
        request_response_from_slave()

        # Sleep for 1 second
        time.sleep(1)

# Heartbeat init
heartbeat_thread = threading.Thread(target=heartbeat_loop)
heartbeat_thread.daemon = True  
heartbeat_thread.start()

# See hetkel ei tööta, aga siin küsitakse kappide staatust. Kutsutake ka interpret_status_bytes()
def request_response_from_slave():
    received_data = bus.read_i2c_block_data(SLAVE_ADDRESS, 0, 11)
    print("Received data:")
    print(received_data)
    interpret_status_bytes(received_data)

# Debugimiseks
# request_response_from_slave()

# Vastusaadud info tehakse arusaadavaks infoks ja muudetakse globaalseid muutujaid, ei ole testitud
# Näide: 1 5 2 2
# 1. byte door id
# 2. byte status. näiteks kui lock on 1, magnet on 0 ja IR on 1 tuleb 101 mis on 5
# 3. byte door id
# 4. byte status. näiteks kui lock on 0, magnet on 1 ja IR on 0 tuleb 010 mis on 2
def interpret_status_bytes(status_bytes):
    global door1_data, door2_data
    print("Door statuses:")
    i = 0
    while i < len(status_bytes) - 1:  # Subtract 1 to ensure there's at least one complete pair
        door_id = status_bytes[i]
        door_status = status_bytes[i + 1]  # Assuming door status byte follows door ID byte
        lock_status = bool(door_status & 0b00000001)
        magnet_status = bool((door_status >> 1) & 0b00000001)
        ir_sensor_status = bool((door_status >> 2) & 0b00000001)

        if door_id == 1:
            door1_data = {"lock_status": lock_status, "magnet_status": magnet_status, "ir_sensor_status": ir_sensor_status}
        elif door_id == 2:
            door2_data = {"lock_status": lock_status, "magnet_status": magnet_status, "ir_sensor_status": ir_sensor_status}
        else:
            print(f"Unknown door ID: {door_id}")

        i += 2  # mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm

    print("Door 1 data:", door1_data)
    print("Door 2 data:", door2_data)

#Vana kood kus open_door_admin on ka muudetud
#Appends pressed button numbers to the textbox field

#Removes the code once it has been used
def remove_code_from_file(code):
    filename = "codes.txt"
    temp_filename = "temp_codes.txt"  # Temporary file to store modified contents

    with open(filename, "r") as input_file, open(temp_filename, "w") as output_file:
        for line in input_file:
            if not line.startswith(code + ":"):  # Skip the line with the code to be removed
                output_file.write(line)

    # Rename temporary file to original filename to replace it
    os.replace(temp_filename, filename)

#Sends the data in the textbox
#Oleks vaja teha skaleeritavaks
@app.route('/process_data', methods=['POST'])
def process_data():
    entered_code = request.form['code']
    used_codes = load_used_codes()
   
    if entered_code == "":
        return jsonify({'message': 'No code was entered'})
   
    if entered_code == "0000":
        return jsonify({'message': 'Admin panel deactivated', 'hide_admin_panel': True})

    if entered_code in used_codes:
        if code_expired(entered_code):
            remove_code_from_file(entered_code)
            return jsonify({'message': 'Code has expired'})
        else:
            door_number = used_codes[entered_code]
            open_door(door_number)  # Open the door linked with the entered code
            time.sleep(1)
           
            # Retrieve error state and IR sensor state for the specified door
            request_response_from_slave

           
            # Process the retrieved data for the specified door
            if door_number == 1:
                door_data = door1_data
            else:
                door_data = door2_data

            door = door_data.get("lock_status", None)
            ir_sensor_state = door_data.get("ir_sensor_status", None)
           
            if door == 0:
                return jsonify({'message': f'Door {door_number} did not open'})
            timestamp = generate_timestamp()
            code_timestamps[entered_code] = timestamp
            time.sleep(8)

            request_response_from_slave

            if door == 1:                
                return jsonify({'message': f'Door {door_number} did not close again'})
            elif door == 0:
                return jsonify({'message': f'Everything is OK for Door {door_number}'})
    elif entered_code == "1337":
        return jsonify({'message': 'Admin panel activated', 'show_admin_panel': True})
    else:
        return jsonify({'message': 'Wrong code'})


@app.route('/generate_new_code', methods=['POST'])
def generate_new_code():
    global used_codes
    if used_codes is None:
        used_codes = load_used_codes()

    selected_door_str = request.form.get('selected_door')  
    if selected_door_str is None:
        return jsonify({'message': 'No door selected'})

    try:
        selected_door = int(selected_door_str)  
    except ValueError:
        return jsonify({'message': 'Invalid door number'})

    random_code = str(random.randint(100000, 999999))  

    while random_code in used_codes:
        random_code = str(random.randint(100000, 999999))
       
    save_used_codes(random_code, selected_door)  # Save the code and its linked door
    return jsonify({'message': 'New code generated', 'code': random_code, 'door': selected_door})


@app.route('/open_door', methods=['POST'])
def open_door_route():
    door_number = int(request.form['door_number'])
    open_door(door_number)
    time.sleep(1)  # Add a delay to allow the door to open and close
   
    # Retrieve error state and IR sensor state for the specified door
    box1_data, box2_data = condition()
   
    # Process the retrieved data for the specified door
    if door_number == 1:
        error_state, _ = box1_data
    else:
        error_state, _ = box2_data
   
    if error_state == 1:
        return jsonify({'message': 'Door ' + str(door_number) + ' did not open'})
   
    time.sleep(10)
    # Retrieve error state again after waiting for the door to close
    box1_data, box2_data = condition()
   
    # Process the retrieved data for the specified door again
    if door_number == 1:
        error_state, _ = box1_data
    else:
        error_state, _ = box2_data
   
    if error_state == 2:
        return jsonify({'message': 'Door ' + str(door_number) + ' did not close again'})
    elif error_state == 0:
        return jsonify({'message': 'Door ' + str(door_number) + ' opened and closed successfully'})


# Define a route to provide sensor data, seda pole GUI-s. See näitab leheküljel kas midagi on sees
@app.route('/get_sensor_data')
def get_sensor_data():
    # Access the global variables containing sensor data for door 1 and door 2
    global door1_data, door2_data
    
    # Extract IR sensor states from the global variables
    box1_ir_sensor_state = door1_data.get("ir_sensor_status", None)
    box2_ir_sensor_state = door2_data.get("ir_sensor_status", None)
   
    # Return sensor data as JSON
    return jsonify({'ir_sensor_state_1': box1_ir_sensor_state, 'ir_sensor_state_2': box2_ir_sensor_state})
       

# Load used codes from a file
def load_used_codes():
    used_codes = {}
    filename = "codes.txt"
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                code, door = line.strip().split(":")
                used_codes[code] = int(door)
    return used_codes

# Save used codes to a file
def save_used_codes(code, door):
    filename = "codes.txt"
    with open(filename, "a") as file:
        file.write(f"{code}:{door}\n")

#Generate a timestamp for a code
def generate_timestamp():
    return datetime.now()

#Check if a code has expired
def code_expired(code):
    if code in code_timestamps:
        expiration_time = code_timestamps[code] + timedelta(minutes=1)
        return datetime.now() > expiration_time
    return False

@app.route('/view_codes')
def view_codes():
    try:
        with open('codes.txt', 'r') as file:
            codes = file.read()
        return codes
    except FileNotFoundError:
        return 'Error: codes.txt not found', 404



   
used_codes = set()

code_timestamps = {}

#Initialize the I2C bus
DEVICE_BUS = 1

#Device I2C address
#(will be left shifted to add the read write bit)
DEVICE_ADDR =10
bus = smbus.SMBus(DEVICE_BUS)
data = 1

if __name__ == '__main__':
    app.run(host='172.20.10.3', port=5000, debug=True)
