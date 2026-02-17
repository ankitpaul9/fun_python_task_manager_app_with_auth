import json
import hashlib
import os
import getpass
import base64
from dataclasses import dataclass
from enum import Enum
from collections import OrderedDict

ITERATIONS = 100_000


class MenuItem:
    def __init__(self, label: str, option: int):
        self.label = label
        self.option = option


class LoginMenu(Enum):
    LOGIN = MenuItem("Login", 1)
    REGISTER = MenuItem("Registeration", 2)
    LOGOUT = MenuItem("Logout", 3)
 
class NavMenu(Enum):
    ADD = MenuItem("Add a Task", 1)
    VIEW = MenuItem("View Tasks", 2)
    CHECKOFF = MenuItem("Mark a Task as Completed", 3)
    DELETE = MenuItem("Delete Task", 4)
    EXIT = MenuItem("Session menu", 5)


class TaskStatus(Enum):
    PENDING = MenuItem("Pending", 1)
    COMPLETED = MenuItem("Completed", 2)
    

@dataclass
class Task:

    def __init__(self, task_id: int, description: str, status: str = "Pending"):
        self.task_id = task_id
        self.description = description
        self.status = status
        
    @staticmethod
    def attribute():
        return ["task_id", "description", "status"]
    
    def completed(self):
        self.status = "Completed"

    def to_dict(self):
        od = OrderedDict()
        od['task_id'] = self.task_id
        od['description'] = self.description
        od['status'] = self.status

        return dict(od)
    

@dataclass
class User:
    def __init__(self, username: str, password: str, salt: str):
        self.username = username
        self.password = password
        self.salt = salt
        self.tasks = []
    

@dataclass
class DB:
    def __init__(self, data={}):
        self.users = []
        users = data.get("users", [])
        if users:
            tasks = data.get("tasks", {})
            users_tasks = {}
            for user, task_list in tasks.items():
                users_tasks[user] = [Task(task["task_id"], task["description"], task["status"]) for task in task_list] 
            self.users = [User(user["username"], user["password"], user["salt"]) for user in users]
            for user in self.users:
                if user.username in users_tasks:
                    user.tasks = users_tasks[user.username]

    def get_users(self):
        return self.users
    
    def get_user(self, username):
        for user in self.users:
            if user.username == username:
                return user
        return None
    
    def add_user(self, username, password, salt):
        if self.get_user(username) is not None:
            return False
        user = User(username, password, salt)
        self.users.append(user)
        return True
    
    def add_user_task(self, username, description):
        user = self.get_user(username)
        if user is not None:
            task_id = len(user.tasks) + 1
            task = Task(task_id, description)
            user.tasks.append(task)
            return True
        return False
    
    def update_user_task(self, username: str, task_id: int, status: TaskStatus):
        user = self.get_user(username)
        if user is not None:
            for task in user.tasks:
                if task.task_id == task_id:
                    task.status = status.value.label
                    return True
        return False
    
    def delete_user_task(self, username: str, task_id: int):
        user = self.get_user(username)
        if user is not None:
            for task in user.tasks:
                if task.task_id == task_id:
                    user.tasks.remove(task)
                    return True
        return False
        

class TaskManagerApp:
    def __init__(self):
        self.tasks = []
        self.filename = 'data.json'
        self.cwdr = os.getcwd()
        self.db_path = os.path.join(self.cwdr, self.filename)
        self.db = self.read_create_db()
        self.user = None
        self.start()

    def register(self):
        print("=== Register ===")
        username = input("Enter username: ")
        user_check = False
        for user in self.db.get_users():
            if user.username == username:
                print("Username already exists. Please choose a different username and try again.")
                user_check = True
        
        if not user_check:
            password = getpass.getpass("Enter password: ").encode()
            salt = os.urandom(16)

            # create hash
            pwd_hash = hashlib.pbkdf2_hmac(
                'sha256',      # hash algorithm
                password,      # password
                salt,          # salt
                ITERATIONS     # iterations
            )

            new_user = User(username, base64.b64encode(pwd_hash).decode(), base64.b64encode(salt).decode())
            self.db.users.append(new_user)

            self.write_create_db()
            print("Password saved!\n")

    def login(self):
        print("=== Login ===")
        username = input("Enter username: ")
        user_check = False
        for user in self.db.get_users():
            if user.username == username:
                user_check = True
                password = getpass.getpass("Enter password: ").encode()
                salt = base64.b64decode(user.salt)

                new_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    password,
                    salt,
                    ITERATIONS
                )

                if base64.b64encode(new_hash).decode() == user.password:
                    print("Login successful ✅")
                    self.user = user
                    self.main_menu()
                    break
                else:
                    print("Wrong password ❌. Please try again.")
                    continue

        if not user_check:
            print(f"User with username {username} not found. Please try again.")
    
    def logout(self):
        self.write_create_db()
        print("Logged out successfully.")
        self.user = None
    
    def start(self):
        while True:
            print("\nLogin Menu:")
            for item in LoginMenu:
                if self.user is None and item == LoginMenu.LOGOUT:
                    continue
                print(f"{item.value.option}. {item.value.label}")
            choice = input("Select an option: ")

            if choice == str(LoginMenu.LOGIN.value.option):
                self.login()
            elif choice == str(LoginMenu.REGISTER.value.option):
                self.register()
            elif choice == str(LoginMenu.LOGOUT.value.option):
                self.logout()
                print("Goodbye!")
                break
            else:
                print("Invalid option. Please try again.")

    def main_menu(self):
        while True:
            print("\nMain Menu:")
            for item in NavMenu:
                print(f"{item.value.option}. {item.value.label}")
            choice = input("Select an option: ")

            if choice == str(NavMenu.ADD.value.option):
                description = input("\nEnter task description: ")
                if self.db.add_user_task(self.user.username, description):
                    print("Task added successfully.")
                else:
                    print("Failed to add task.")
            elif choice == str(NavMenu.VIEW.value.option):
                self.view_tasks()
            elif choice == str(NavMenu.CHECKOFF.value.option):
                self.mark_task_completed()
            elif choice == str(NavMenu.DELETE.value.option):
                self.delete_task()
            elif choice == str(NavMenu.EXIT.value.option):
                print("Back to login menu.")
                break
            else:
                print("Invalid option. Please try again.")
    
    def db_create(self):
        if not os.path.exists(self.db_path):
            print("Database file does not exist. Creating new database file.")
            data = {
                "users": [],
                "tasks": {}
            }
            with open(self.db_path, 'w') as file:
                json.dump(data, file, indent=4)
            print("Database file created.")
        else:
            print("Database file already exists.")

    def read_create_db(self):    
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as file:
                    data = json.load(file)
                    return DB(data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        else:
            self.db_create()
            return DB()

    def write_create_db(self,):
        if os.path.exists(self.db_path):
            data = {
                "users": [{"username": user.username, "password": user.password, "salt": user.salt} for user in self.db.get_users()],
                "tasks": {user.username: [task.to_dict() for task in user.tasks] for user in self.db.get_users()}
            }
            with open(self.db_path, 'w') as file:
                json.dump(data, file, indent=4)
        else:
            self.db_create()
            return DB()

    def view_tasks(self):
        if not self.user:
            print("\nNo user is logged in.")
            return
        user = self.user
        if not user.tasks:
            print("\nNo tasks to display.")
            return
        
        # Print headers
        headers = Task.attribute()
        print(f"{headers[0]:10} {headers[1]:30} {headers[2]:15}")
        print("-" * 60)
        
        # Print tasks
        for task in user.tasks:
            task_id = str(getattr(task, 'task_id'))[:10]
            description = str(getattr(task, 'description'))[:30]
            status = str(getattr(task, 'status'))[:15]
            print(f"{task_id:10} {description:30} {status:15}")

    def mark_task_completed(self):
        if not self.user:
            print("\nNo user is logged in.")
            return
        user = self.user
        if not user.tasks:
            print("\nNo tasks to mark as completed.")
            return

        while True:
            try:
                task_id = int(input("\nEnter task ID to mark as completed: "))
                if self.db.update_user_task(user.username, task_id, TaskStatus.COMPLETED):
                    print(f"\nTask {task_id} marked as completed.")
                    break
                else:
                    print(f"\nTask with ID {task_id} not found.")
            except ValueError:
                print("\nInvalid input. Please enter a valid task ID.")

    def delete_task(self):
        if not self.user:
            print("\nNo user is logged in.")
            return
        user = self.user
        if not user.tasks:
            print("\nNo tasks to delete.")
            return

        while True:
            try:
                task_id = int(input("\nEnter task ID to delete: "))
                if self.db.delete_user_task(user.username, task_id):
                    print(f"\nTask {task_id} deleted.")
                    break
                else:
                    print(f"\nTask with ID {task_id} not found.")
            except ValueError:
                print("\nInvalid input. Please enter a valid task ID.")


if __name__ == "__main__":
    TaskManagerApp()