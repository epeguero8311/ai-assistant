import json
import importlib.util
import ollama

TOOLS_PATH = "tools.json"
PROMPT_PATH = "prompts/system_prompt.txt"
MODEL = "llama3.2-tool:latest"


def load_tools():
    with open(TOOLS_PATH) as f:
        return json.load(f)["tools"]


def load_system_prompt():
    with open(PROMPT_PATH) as f:
        return f.read()


def build_ollama_tools(tools):
    """
    Convert tools.json format into the format ollama expects.
    ollama needs a flat list of functions, not grouped by tool.
    """
    ollama_tools = []

    for tool in tools:
        for fn in tool["functions"]:
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": fn["name"],
                    "description": fn["description"],
                    "parameters": fn["parameters"]
                }
            })

    return ollama_tools


def get_function(tools, fn_name):
    """
    Find which file a function lives in, import it, and return the function.
    This lets us add new tools without touching run.py.
    """
    for tool in tools:
        for fn in tool["functions"]:
            if fn["name"] == fn_name:
                # dynamically import the python file for this tool
                spec = importlib.util.spec_from_file_location(fn_name, tool["file"])
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return getattr(module, fn_name)

    return None


def call_tool(tools, fn_name, fn_args):
    """Find the function and call it with the args the AI provided."""
    fn = get_function(tools, fn_name)

    if fn is None:
        return f"No function named '{fn_name}' found in any tool."

    result = fn(**fn_args)
    return str(result)


def main():
    tools = load_tools()
    system_prompt = load_system_prompt()
    ollama_tools = build_ollama_tools(tools)
    history = []

    print("Assistant ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            break

        history.append({"role": "user", "content": user_input})

        # first call — AI decides if it needs a tool
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "system", "content": system_prompt}] + history,
            tools=ollama_tools
        )

        message = response["message"]

        # if the AI called a tool, run it and send the result back
        if message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                fn_name = tool_call["function"]["name"]
                fn_args = tool_call["function"]["arguments"]

                tool_result = call_tool(tools, fn_name, fn_args)

                # add the tool call and result to history
                history.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
                history.append({"role": "tool", "content": tool_result})

            # second call — AI gives the user a natural reply after seeing the result
            final_response = ollama.chat(
                model=MODEL,
                messages=[{"role": "system", "content": system_prompt}] + history,
                tools=ollama_tools
            )

            reply = final_response["message"]["content"]

        else:
            # no tool needed, just use the reply directly
            reply = message["content"]

        history.append({"role": "assistant", "content": reply})
        print(f"\nAssistant: {reply}\n")


if __name__ == "__main__":
    main()