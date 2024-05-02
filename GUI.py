from guizero import App, Text, TextBox, PushButton, Picture, ButtonGroup, Box, Window, info
import random
import os
from datetime import datetime, timedelta
import time
import smbus
import threading


# Uste info tehtud globaalseks muutujaks, ehk kui pärast interpret_status_bytes() muudetakse kastide staatust muutub siin automaatselt
door1_data = {"lock_status": False, "magnet_status": False, "ir_sensor_status": False}
door2_data = {"lock_status": False, "magnet_status": False, "ir_sensor_status": False}

# Annab STM-ile teada mis uksed tema peab lahti tegema. data_size on mitu ust tehakse lahti 
def open_door(data):
    command = 0x02 
    data_size = 1 
    data = [data_size, data] 
    slave_address = 21  
    bus = smbus.SMBus(1)  
    print("Sending to address:", slave_address)
    bus.write_i2c_block_data(slave_address, command, data) 

# Restardib STM ja tema uste haldamis info. data_size on 1 ja kui sellele järngneb 0 annab teada, et tuleb restartida
def reboot_slave():
    command = 0x09  
    data_size = 1  
    data = [data_size, 0]  
    slave_address = 21  
    bus = smbus.SMBus(1)  
    print("Sending to address:", slave_address)
    bus.write_i2c_block_data(slave_address, command, data)

# Annab STM-ile teada mis uksed tema peab haldama. data_size on mitu ust hallatakse 
def send_data_to_slave():
    command = 0x08  
    data_size = 2 
    data = [data_size, 1, 2] #hetkel on pandud 1 ja 2, kuidagi peaks tegema lihtsasti skaleeritavaks 
    slave_address = 21  
    bus = smbus.SMBus(1)  
    print("Sending to address:", slave_address)
    bus.write_i2c_block_data(slave_address, command, data) 

# alguses ütleme, et halda 2 ust id-ga 1 ja 2
send_data_to_slave()

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
    command = 0x02  
    data_size = 1  
    data = [data_size, 11]  
    slave_address = 21  
    bus = smbus.SMBus(1)  
    slave_address = 21  
    received_data = bus.read_i2c_block_data(slave_address, 11)
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

        i += 2  

    print("Door 1 data:", door1_data)
    print("Door 2 data:", door2_data)


#Vana kood kus open_door_admin on ka muudetud
#Appends pressed button numbers to the textbox field

#Removes the code once it has been used
def input_to_textbox(user_input):
    text_box.append(user_input)

#Function to clear the textbox
def clear_textbox():
    text_box.clear()

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
def send_data():
    entered_code = text_box.value.strip()
    used_codes = load_used_codes()
    check_code(entered_code)
    if entered_code == "":
        print("Entered code is empty.")
        app.error("VIGA", "     Tühi kood!     ")
    elif entered_code in used_codes:
        if code_expired(entered_code):
            print("Code has expired:", entered_code)
            app.error("VIGA", "     Kood on aegunud!     ")
            remove_code_from_file(entered_code)
        else:
            print("Processing code:", entered_code)
            door_number = used_codes[entered_code]
            print("door nmber:", door_number)
            open_door(door_number)
            time.sleep(1)
            request_response_from_slave

            if door_number == 1:
                door_data = door1_data
            else:
                door_data = door2_data

            door = door_data.get("lock_status", None)
            ir_sensor_state = door_data.get("ir_sensor_status", None)

            if door == 0:
                app.info("INFO", "     Uks ei lainud lahti, ime munni ja hakka nutma pede!     ")
                return  # Exit function if door didn't open
            
            timestamp = generate_timestamp()
            code_timestamps[entered_code] = timestamp
            app.info("INFO", "     Kapp avatud!     ")
            time.sleep(8)

            request_response_from_slave
            door = door_data.get("lock_status", None)
            ir_sensor_state = door_data.get("ir_sensor_status", None)

            if door == 0:
                app.info("INFO", "     Uks ei lainud kinni tagasi!     ")
            elif door == 1:
                app.info("INFO", "     Kõik ok!     ")

    elif entered_code == "1337":
        print("Processing code:", entered_code)
    else:
        print("Wrong code:", entered_code)
        app.error("VIGA", "     Vale kood!     ")
       
    text_box.clear()


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

#Function to change the screen when admin code is entered
def check_code(code):
    #Function that opens the selected box
    def open_box():
        radioBoxValue = int(radioBoxes.value)
        adminWindow.info("AVA KAPP", "Avasid kapi {}".format(radioBoxValue))
    def open_door_admin():
        data = int(radioBoxes.value)
        command = 0x02  
        data_size = 1  
        data = [data_size, data]  
        slave_address = 21  
        bus = smbus.SMBus(1)  
        print("Sending to address:", slave_address)
        bus.write_i2c_block_data(slave_address, command, data) 
       
    #Generate a random 6-digit code
    def generate_code():
        random_code = str(random.randint(100000, 999999))
       
        #Check if the code has been used before generating a new one
        while random_code in used_codes:
            random_code = str(random.randint(100000, 999999))
        radioBoxValue = int(radioBoxes.value)
        save_used_codes(random_code,radioBoxValue)
       

        adminWindow.info("INFO", "Genereeritud kapile {} kood {}".format(radioBoxValue, random_code))
       
    if code == '1337':
        adminWindow = Window(app, title = "ADMINI KAPP", width= 400, height = 300)
        window_box = Box(adminWindow, layout = "grid")
        radioBoxes = ButtonGroup(window_box, options=[["KAPP 1", 1], ["KAPP 2", 2]], grid=[0,1], align = "left")
        buttonOpenBox = PushButton(window_box, text="AVA KAPP", grid=[0,0], align = "top", width=15, command=open_door_admin)
        generate_button = PushButton(window_box, text="Generate Code", grid=[0, 2], align="top", width=15, command=generate_code)
    if code == '0000':
        exit()



app = App(title = "NUTIKAPP", width= 1920, height = 1080)
#Used for creating empty space at the top of the screen
center_pad = Box(app, align="top", height=150, width="fill")
#Used for putting all the buttons, picture etc. to a container
center_box = Box(app, layout = "grid")

welcome_message = Text(center_box, text = "SISESTA KOOD", font = "Times New Roman", grid = [1,0], size=30)

text_box = TextBox(center_box, grid = [1,1], width=6)
text_box.text_size = 30
text_box.text_color = "#f3941c"
text_box.bg = "#e0dcdc"

used_codes = set()

code_timestamps = {}

#Initialize the I2C bus
DEVICE_BUS = 1

#Device I2C address
#(will be left shifted to add the read write bit)
DEVICE_ADDR =10
bus = smbus.SMBus(DEVICE_BUS)
data = 1

button_width = 5
button_height = 2

#When a button is pressed the function in 'command' is executed and arguments given is in 'args'
button1 = PushButton(center_box, text="1", grid=[0,2], align = "right", width=button_width,height=button_height, command=input_to_textbox, args=['1'])
button2 = PushButton(center_box, text="2", grid=[1,2], width=button_width,height=button_height,  command=input_to_textbox, args=['2'])
button3 = PushButton(center_box, text="3", grid=[2,2], width=button_width,height=button_height,  command=input_to_textbox, args=['3'])
button4 = PushButton(center_box, text="4", grid=[0,3], align = "right", width=button_width,height=button_height,  command=input_to_textbox, args=['4'])
button5 = PushButton(center_box, text="5", grid=[1,3], width=button_width, height=button_height, command=input_to_textbox, args=['5'])
button6 = PushButton(center_box, text="6", grid=[2,3], width=button_width,height=button_height,  command=input_to_textbox, args=['6'])
button7 = PushButton(center_box, text="7", grid=[0,4], align = "right", width=button_width, height=button_height, command=input_to_textbox, args=['7'])
button8 = PushButton(center_box, text="8", grid=[1,4], width=button_width,height=button_height,  command=input_to_textbox, args=['8'])
button9 = PushButton(center_box, text="9", grid=[2,4], width=button_width,height=button_height,  command=input_to_textbox, args=['9'])
buttonD = PushButton(center_box, text="DEL", grid=[0,5], align = "right", width=button_width,height=button_height,  command=clear_textbox)
button0 = PushButton(center_box, text="0", grid=[1,5], width=button_width,height=button_height, command=input_to_textbox, args=['0'])
buttonE = PushButton(center_box, text="ENT", grid=[2,5], width=button_width,height=button_height, command=send_data)

button1.text_size=20
button2.text_size=20
button3.text_size=20
button4.text_size=20
button5.text_size=20
button6.text_size=20
button7.text_size=20
button8.text_size=20
button9.text_size=20
buttonD.text_size=20
button0.text_size=20
buttonE.text_size=20

picture = Picture(center_box, image = "logo.gif", grid = [1,6])

app.full_screen = True
app.display()
