import json
import ollama

TOOLS_PATH = "tools.json"
PROMPT_PATH = "prompts/system_prompt.txt"
MODEL = "llama3.2"

def load_tools():
    with open(TOOLS_PATH) as f:
        return json.load(f)

def build_system_prompt(tools):
    with open(PROMPT_PATH) as f:
        template = f.read()

    if not tools["tools"]:
        tools_str = "No tools are currently available."
    else:
        tools_str = "\n".join(
            f"- {t['name']}: {t['description']}" for t in tools["tools"]
        )

    return template.replace("{{TOOLS_LIST}}", tools_str)

def main():
    tools = load_tools()
    system_prompt = build_system_prompt(tools)
    history = []

    print("Assistant ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            break

        history.append({"role": "user", "content": user_input})

        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "system", "content": system_prompt}] + history
        )

        reply = response["message"]["content"]
        history.append({"role": "assistant", "content": reply})

        print(f"\nAssistant: {reply}\n")

if __name__ == "__main__":
    main()