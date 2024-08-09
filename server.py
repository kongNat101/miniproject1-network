import socket
import json
import os
import signal
import sys
import threading
import time
from datetime import datetime

PORT = 12345
BUFFER_SIZE = 1024
backup_file = 'backup_file.json'
backup_time = 120

reservations = {}
menu ={"lunch": ['chicken soup','mashed potatoes','ribeye steak','cheese cake','wine'],
       "dinner": ['corn soup','french fries','picanha steak','pudding','whiskey']}
num_table = [1,2,3,4,5,6]

OWNER_USERNAME = 'owner'
OWNER_PASSWORD = '1234'

def load_reser():
    "Load reservation from backup file"
    global reservations
    if os.path.exists(backup_file):
        try:
            with open(backup_file,"r") as f:
                reservations = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print("Error loading backup file or file is empty. Starting with an empty reservations dictionary")
            reservations = {}

def save_reser():
    "Save reservation to the backup file"
    with open(backup_file,'w') as f:
        json.dump(reservations, f, indent=4)
        
def backup_data():
    "Periodically back up reservation data"
    while True:
        time.sleep(backup_time)
        print("Backing up data complete")
        save_reser()
    
def handle_c(client_socket):
    "Handle client data"
    try:
        request = client_socket.recv(BUFFER_SIZE).decode()
        request_data = json.loads(request)
        command = request_data.get("command")
        role = request_data.get("role")
        username = request_data.get("username")
        password = request_data.get("password")
        
        if role == "owner":
            while username != OWNER_USERNAME or password != OWNER_PASSWORD:
                response = {"status code":"403 Forbidden","message":"Invalid please try again"}
                client_socket.send(json.dumps(response).encode())
                request = client_socket.recv(BUFFER_SIZE).decode()
                request_data = json.loads(request)
                username = request_data.get("username")
                password = request_data.get("password")
            response = owner_command(request_data)
        elif role == "client":
            response = client_command(request_data)
        else:
            response = {"status code":"400 Bad request","messaga":"Type wrong role"}
        print("Sending response",response)
        client_socket.send(json.dumps(response).encode())
    
    except Exception as e:
        print(f"Error handling client: {e}")
        response = {"status code":"500 Internal Server Error","message":"An error occurred."}
        client_socket.send(json.dumps(response).encode())
    finally:
        client_socket.close()
        
def owner_command(data):
    "Process command owner"
    command = data.get("command")
        
    if command == "rename_food":
        return rename_food(data)
    elif command == "cancel_reser":
        return cancel_reser(data)
    elif command == "view_reser":
        return view_reser()
    elif command == "backup":
        save_reser()
        return {"status code":"200 OK","message":"Manual backup"}
    elif command == "exit":
        return {"status code": "200 OK","message": 'Exiting application.'}
    else:
        return {"status code":"400 Bad request","message":"Unknow command"}
    
def client_command(data):
    "Process command client" 
    command = data.get("command")
    
    if command == "reser":
        return reser(data)
    elif command == "view_course":
        return {"status code":"200 OK","menu":menu}
    elif command == "exit":
        return {"status code":"200 OK","message":'Exiting application.'}
    else:
        return {"status code":"400 Bad request","message":"Unknow command"}
    
def rename_food(data):
    "Rename food in menu"    
    meal_type = data.get("meal_type")
    old_food_name = data.get("old_food_name")
    new_food_name = data.get("new_food_name")
    
    if meal_type in menu:
        if old_food_name in menu[meal_type]:
            menu[meal_type][menu[meal_type].index(old_food_name)] = new_food_name
            return {"status code":"200 OK","message":"Rename food complete"}
        else:
            return {"status code":"400 Bad request","message":"Wrong food name"}
    else:
        return {"status code":"400 Bad request","message":"Unknow meal"}
    
def cancel_reser(data):
    "Cancel reservation with date and table number"
    date = data.get("date")
    table = data.get("table")
    
    if not date or not table:
        return {"status code":"400 Bad request","message":"Date and table number required"}
    if date in reservations:
        if table in reservations[date]:
            del reservations[date][table]
            if not reservations[date]:
                del reservations[date]
            return {"status code":"200 OK","message":"Reservation cancel complete"}
        else:
            return {"status code":"404 Not found","message":"No reservation found for this table"}
    else:
        return {"status code":"404 Not found","message":"No reservations found for this date"}
    
def view_reser():
    "View all reservations."
    formatted_reservations = {
        date: {
            table: f"{details['meal_type']} - {details['client_name']}"
            for table, details in reservations.get(date, {}).items()
        }
        for date in reservations
    }
    return {"status code": "200 OK", "reservations": formatted_reservations}

def reser(data):
    "Reserve a table for client"
    client_name = data.get("client_name")
    date = data.get("date")
    table = data.get("table")
    meal_type = data.get("meal_type")

    if client_name and date and table in num_table and meal_type in menu:    
        if date in reservations and table in reservations[date] and reservations[date][table]["meal_type"] == meal_type:
            return {"status code":"409 Conflict","message":"Table already reserved with the same meal type"}
        else:
            reservations.setdefault(date, {})[table] = {"meal_type": meal_type, "client_name": client_name}
            return {"status code":"200 OK","message":"Reservation complete"}
    else:
        return {"status code":"400 Bad request","message":"Invalid reservation"}
    
def shutdown(signum,frame):
    "Handle server shutdown"
    print("Shutdown server complete \|'u'|/")
    save_reser()
    sys.exit(0)
    
def main():
    load_reser()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    backup_thread = threading.Thread(target=backup_data, daemon=True)
    backup_thread.start()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', PORT))
    server.listen(5)
    print(f"Server listening on port {PORT}")
    
    while True:
        client_socket, _ = server.accept()
        handle_c(client_socket)
        
if __name__ == "__main__":
    main()