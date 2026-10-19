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
personalities = {
    "Ash": "warm, observant, practical, and protective of ordinary people",
    "Brook": "patient, hospitable, cautious, and good at reading motives",
    "Clay": "commanding, proud, strategic, and sensitive to challenges to authority",
    "Dok": "direct, skeptical, disciplined, and focused on concrete evidence",
    "Igra": "diplomatic, calculating, persuasive, and attentive to consequences",
    "Zovi": "social, energetic, curious, and eager to connect competing interests",
    "Yu": "quiet, analytical, independent, and protective of accurate records",
    "Mako": "restless, inventive, self-reliant, and suspicious of official promises",
    "Teko": "hands-on, blunt, resourceful, and focused on workable solutions",
    "Joahn": "formal, meticulous, principled, and reluctant to rule without evidence",
    "Marcos": "inquisitive, skeptical, articulate, and interested in public accountability",
    "Lian": "adaptable, observant, ambitious, and careful about choosing allies",
}
world = Path("instruction/world.md").read_text(encoding="utf-8")
agents = {
    name.casefold(): Agent(
                           name=name,
                           instruction=(
                               f"{world}\n\nYou are {name}, {role}. "
                               f"Your personality is {personalities[name]}."
                           ),
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
    ),
    thinking_instruction="<Think about what happened, reflect and make a plan on the following actions",
    action_instruction=f"{action_taking}\r\n<Take an action based on your thoughts and plans>",
    compressor=compressor,
    compress_threshold=6000,
    compress_pedict=500,
    thinking_predict=150,
    action_predict=180
)
