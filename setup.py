from pathlib import Path
from agent import Agent
from environment import Environment

URL = "http://127.0.0.1:11434/api/chat"
MODEL = "llama3.1:8b-instruct-q4_K_M"

roles = {
    "Ash": "keeper of the Copper Lantern tavern",
    "Brook": "keeper of the Wayfarer Hotel",
    "Clay": "Sovereign of Veyr",
    "Dok": "Marshal of Veyr",
    "Igra": "Chancellor of Veyr",
    "Zovi": "keeper of the Riverside Hall",
    "Yu": "keeper of the Lantern Library",
    "Mako": "independent inhabitant",
    "Teko": "keeper of the Open Bench workshop",
    "Joahn": "Keeper of the Seal",
    "Marcos": "keeper of the Veyr Press",
    "Lian": "independent inhabitant",
}
agents = {
    name.casefold(): Agent(name=name, instruction=f"You are {name}, {role}.",
                           memory=Path("kingdom.md").read_text(encoding="utf-8"),
                           url=URL, model=MODEL, credits=100)
    for name, role in roles.items()
}

compressor = Agent(
    name="Compressor",
    instruction="Compress memory while preserving concrete facts and receipts.",
    memory="",
    url=URL,
    model=MODEL,
    credits=0,
)

action_taking = ""
with open("instruction/action_taking.md", "r", encoding="utf-8") as file:
    action_taking = file.read()

environment = Environment(
    shared_path=Path("shared"),
    agents=agents,
    standard_instruction=(
        Path("instruction/basic_rules.md").read_text(encoding="utf-8")
        + "\n"
        + Path("instruction/world.md").read_text(encoding="utf-8")
    ),
    thinking_instruction="<Think about what happened, reflect and make a plan on the following actions",
    action_instruction=f"{action_taking}\r\n<Take an action>",
    compressor=compressor,
    compress_interval=10,
    compress_pedict=500,
    thinking_predict=150,
    action_predict=100
)
