import ollama
from persona import Persona

messages = []
current_persona = None

def set_persona(persona: Persona):
    global messages, current_persona
    current_persona = persona
    messages = [{
        "role": "system",
        "content": persona.system_prompt()
    }]

def chat_with_ai(text: str) -> str:
    messages.append({"role": "user", "content": text})

    response = ollama.chat(
        model="llama3.1",
        messages=messages
    )

    messages.append(response["message"])
    return response["message"]["content"]