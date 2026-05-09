import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODO_FILE = os.path.join(BASE_DIR, "data", "todo.json")

def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, "r") as f:
        return json.load(f)


def save_todos(todos):
    os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=2)


def next_id(todos):
    if not todos:
        return 1
    return max(t["id"] for t in todos) + 1



def add_todo(title, date=None):
    todos = load_todos()

    todo = {
        "id":    next_id(todos),
        "title": title,
        "date":  date,
        "done":  False,
    }

    todos.append(todo)
    save_todos(todos)
    print(f"Added #{todo['id']}: {title}")
    return todo


def view_todos():
    todos = load_todos()

    if not todos:
        print("No todos yet.")
        return todos

    print("")
    print(f"  {'ID':<4} {'Done':<6} {'Date':<12} Title")
    print(f"  {'--':<4} {'----':<6} {'----':<12} -----")

    for todo in todos:
        if todo["done"] == True:
            done_label = "yes"
        else:
            done_label = "no"

        if todo["date"] == None:
            date_label = "none"
        else:
            date_label = todo["date"]

        print(f"  {todo['id']:<4} {done_label:<6} {date_label:<12} {todo['title']}")

    print("")
    return todos


def get_todo(todo_id):
    todos = load_todos()

    for todo in todos:
        if todo["id"] == todo_id:
            print("")
            print(f"  ID    : {todo['id']}")
            print(f"  Title : {todo['title']}")
            print(f"  Date  : {todo['date']}")
            print(f"  Done  : {todo['done']}")
            print("")
            return todo

    print(f"No todo found with ID {todo_id}.")
    return None


def complete_todo(todo_id):
    todos = load_todos()

    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = True
            save_todos(todos)
            print(f"Marked #{todo_id} as done.")
            return todo

    print(f"No todo found with ID {todo_id}.")
    return None


def delete_todo(todo_id):
    todos = load_todos()
    updated = [todo for todo in todos if todo["id"] != todo_id]

    if len(updated) == len(todos):
        print(f"No todo found with ID {todo_id}.")
        return False

    save_todos(updated)
    print(f"Deleted #{todo_id}.")
    return True



if __name__ == "__main__":
    view_todos()
    complete_todo(2)
    view_todos()