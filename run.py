import json
import inspect
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
    for tool in tools:
        for fn in tool["functions"]:
            if fn["name"] == fn_name:
                spec = importlib.util.spec_from_file_location(fn_name, tool["file"])
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return getattr(module, fn_name)
    return None


def call_tool(tools, fn_name, fn_args):
    fn = get_function(tools, fn_name)

    if fn is None:
        return f"No function named '{fn_name}' found."

    # only pass args the function actually accepts
    valid_params = inspect.signature(fn).parameters
    filtered_args = {k: v for k, v in fn_args.items() if k in valid_params}

    result = fn(**filtered_args)
    return str(result)


def parse_text_tool_call(content):
    """
    Some models output tool calls as plain text JSON instead of structured tool_calls.
    This catches that and parses it manually.
    Example: {"name": "add_todo", "parameters": {"title": "math homework", "date": "2025-05-12"}}
    """
    content = content.strip()

    if not content.startswith("{"):
        return None

    try:
        parsed = json.loads(content)

        # support both "parameters" and "arguments" keys
        fn_name = parsed.get("name")
        fn_args = parsed.get("parameters") or parsed.get("arguments") or {}

        if not fn_name:
            return None

        # sometimes args values are themselves JSON strings, parse them
        if isinstance(fn_args, str):
            fn_args = json.loads(fn_args)

        clean_args = {}
        for k, v in fn_args.items():
            if isinstance(v, str):
                try:
                    clean_args[k] = json.loads(v)
                except Exception:
                    clean_args[k] = v
            else:
                clean_args[k] = v

        return fn_name, clean_args

    except Exception:
        return None


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

        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "system", "content": system_prompt}] + history,
            tools=ollama_tools
        )

        message = response["message"]
        reply = None

        # path 1: model used structured tool_calls (ideal)
        if message.get("tool_calls"):
            for tool_call in message["tool_calls"]:
                fn_name = tool_call["function"]["name"]
                fn_args = tool_call["function"]["arguments"]
                tool_result = call_tool(tools, fn_name, fn_args)
                history.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
                history.append({"role": "tool", "content": tool_result})

            final = ollama.chat(
                model=MODEL,
                messages=[{"role": "system", "content": system_prompt}] + history,
                tools=ollama_tools
            )
            reply = final["message"]["content"]

        # path 2: model output a JSON tool call as plain text
        elif parse_text_tool_call(message.get("content", "")):
            fn_name, fn_args = parse_text_tool_call(message["content"])
            tool_result = call_tool(tools, fn_name, fn_args)

            history.append({"role": "assistant", "content": message["content"]})
            history.append({"role": "tool", "content": tool_result})

            final = ollama.chat(
                model=MODEL,
                messages=[{"role": "system", "content": system_prompt}] + history,
                tools=ollama_tools
            )
            reply = final["message"]["content"]

        # path 3: no tool needed, plain response
        else:
            reply = message["content"]

        history.append({"role": "assistant", "content": reply})
        print(f"\nAssistant: {reply}\n")


if __name__ == "__main__":
    main()