import socket
import json

PORT = 12345
BUFFER_SIZE = 1024
OWNER_USERNAME = 'owner'
OWNER_PASSWORD = '1234'

def send_request(role,command,params=None, username=None, password =None):
    "Send a request to server"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("127.0.0.1",PORT))
        request = {"role":role, "command":command}
        if params:
            request.update(params)
        if username and password:
            request["username"] = username
            request["password"] = password
        s.send(json.dumps(request).encode())
        response = s.recv(BUFFER_SIZE).decode()
        return json.loads(response)
    
def client_main():
    "Main for client command"
    while True:
        print("\nOption: reser,view_course,exit")
        command = input("Enter command: ").strip().lower()
        
        if command == "exit":
            response = send_request(role="client", command="exit")
            print("Response: ",response)
            break
        elif command == "reser":
            client_name = input("Enter your name: ").strip()
            date = input("Enter date (YYYY-MM-DD): ").strip()
            table = int(input("Enter table number: ").strip())
            meal_type = input("Enter meal type (lunch/dinner): ").strip().lower()
            params = {"client_name":client_name, "date":date, "table":table, "meal_type":meal_type}
            response = send_request(role="client", command="reser",params=params)
            
            if response.get("status code") == "409 Conflict":
                print(response.get("message"))
                continue
            print("Response",response)
        elif command == "view_course":
            response =send_request(role="client", command="view_course")
            print("Response",response)
        
        else:
            print("Invalid command. Please try again.")
            continue

def owner_main():
    "Main for owner command"
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    
    if username != OWNER_USERNAME or password != OWNER_PASSWORD:
        print("Invalid")
        return
    
    while True:
        print("\nOption: rename_food,cancel_reser,view_reser,backup,exit")
        command = input("Enter command: ").strip().lower()
        
        if command == "exit":
            response = send_request(role="owner", command="exit", username=username, password=password)
            print("Response: ",response)
            break
        elif command == "rename_food":
            meal_type = input("Enter meal type (lunch/dinner): ").strip().lower()
            old_food_name = input("Enter old food name: ").strip()
            new_food_name = input("Enter new food name: ").strip()
            params =  {"meal_type":meal_type,"old_food_name":old_food_name,"new_food_name":new_food_name}
            response = send_request(role="owner",command="rename_food",params=params,username=username,password=password)
            print("Response: ",response)
        elif command == "cancel_reser":
            date = input("Enter date (YYYY-MM-DD): ").strip()
            table = int(input("Enter table number: ").strip())
            params = {"date":date,"table":table}
            response = send_request(role="owner",command="cancel_reser",params=params,username=username,password=password)
            print("Response: ",response)
        elif command == 'view_reser':
            response = send_request(role='owner', command='view_reser', username=username, password=password)
            print("Response:", response)
        elif command == "backup":
            response = send_request(role="owner",command="backup",username=username,password=password)
        else:
            print("Invalid command. Please try again.")
            continue
if __name__ ==  "__main__":
    role = input("Enter role (client/owner): ").strip().lower()
    if role == "client":
        client_main()
    elif role == "owner":
        owner_main()
    else:
        print("Invalid role.Please try again")