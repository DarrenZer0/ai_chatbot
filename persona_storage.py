import json
from persona import Persona

def load_persona(path: str) -> Persona:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Persona(**data)

def save_persona(persona: Persona, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(persona.__dict__, f, indent=2)
