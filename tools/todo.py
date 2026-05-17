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
    return f"Added task #{todo['id']}: '{title}'" + (f" due {date}" if date else "")


def view_todos():
    todos = load_todos()
    if not todos:
        return "No todos yet."

    lines = []
    for todo in todos:
        done_label = "done" if todo["done"] else "pending"
        date_label = f" due {todo['date']}" if todo["date"] else ""
        lines.append(f"#{todo['id']} [{done_label}]{date_label} — {todo['title']}")

    return "\n".join(lines)


def get_todo(todo_id):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            date_label = todo["date"] if todo["date"] else "none"
            done_label = "done" if todo["done"] else "pending"
            return f"#{todo['id']}: '{todo['title']}' | due: {date_label} | status: {done_label}"

    return f"No todo found with ID {todo_id}."


def complete_todo(todo_id):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = True
            save_todos(todos)
            return f"Marked #{todo_id} '{todo['title']}' as done."

    return f"No todo found with ID {todo_id}."


def delete_todo(todo_id):
    todos = load_todos()
    updated = [todo for todo in todos if todo["id"] != todo_id]

    if len(updated) == len(todos):
        return f"No todo found with ID {todo_id}."

    save_todos(updated)
    return f"Deleted #{todo_id}."