from dataclasses import dataclass

@dataclass
class Persona:
    name: str
    description: str
    user_role: str = ""
    reply_style: str = ""
    avatar_path: str = ""

    def system_prompt(self) -> str:
        prompt = f"You are {self.name}.\n\n"
        prompt += self.description.strip() + "\n\n"

        if self.user_role:
            prompt += f"The user is: {self.user_role}\n\n"

        if self.reply_style:
            prompt += f"Reply style rules:\n{self.reply_style}\n\n"

        prompt += "You must stay in character at all times."
        return prompt