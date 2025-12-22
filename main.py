import ollama

def chat(prompt):
    response = ollama.chat(
        model="llama3.1",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response["message"]["content"]

if __name__ == "__main__":
    while True:
        user = input("You: ")
        if user.lower() in ("exit", "quit", "bye"):
            break

        reply = chat(user)
        print("Bot:", reply)