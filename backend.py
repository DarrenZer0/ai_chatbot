import ollama

messages = []

def chat_with_ai(prompt):
    try:
        messages.append({"role": "user", "content": prompt})

        response = ollama.chat(
            model="llama3.1",
            messages=messages
        )

        messages.append(response["message"])
        return response["message"]["content"]

    except Exception as e:
        return f"[Error] Ollama is not running.\n{e}"