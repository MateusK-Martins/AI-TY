import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label
from textual import work
from environment import Environment

class Dashboard(App):
    CSS = """
    #main {
        width: 70%;
        padding: 1 2;
        overflow-y: scroll;
    }

    #history_panel {
        width: 30%;
        border-left: solid cyan;
        padding: 1;
    }

    #history {
        height: 1fr;
    }

    #full-history {
        width: 100%;
        margin-bottom: 1;
    }

    #thought {
        border: solid magenta;
        padding: 1;
        min-height: 8;
    }

    #action {
        border: solid green;
        padding: 1;
        min-height: 8;
    }

    #receipt {
        border: solid yellow;
        min-height: 5;
    }

    #memory {
        border: solid blue;
        padding: 1;
        height: 21;
        overflow-y: scroll;
    }
    """

    def __init__(self, environment: Environment):
        super().__init__()
        self.environment = environment
        self.events = []
        self.full_history = False
        self.follow_live = True

    def on_mount(self):
        self.run_simulation()

    @work(thread=True)
    def run_simulation(self):
        for event in self.environment.run():
            self.call_from_thread(
                self.show_event,
                event,
            )

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal():
            with ScrollableContainer(id="main"):
                yield Static("[bold]THOUGHTS[/bold]\nNo thoughts yet", id="thought")
                with ScrollableContainer(id="memory"):
                    yield Static("[bold]MEMORY[/bold]\nNo memory yet", id="memory-content")
                yield Static("[bold]ACTION[/bold]\nNo action yet", id="action")
                yield Static("[bold]RECEIPT[/bold]\nNo receipt yet", id="receipt")

            with Vertical(id="history_panel"):
                yield Button("Following live", id="follow-live")
                yield Button("Show full history", id="full-history")
                yield Button("Export events JSON", id="export-events")
                yield ListView(
                    id="history",
                )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "follow-live":
            self.follow_live = True
            if self.events:
                self.show_event_details(self.events[-1])
            return
        if event.button.id == "export-events":
            self.export_events()
            return
        if event.button.id != "full-history":
            return

        self.full_history = not self.full_history

        button = self.query_one("#full-history", Button)
        button.label = (
            "Show compact history"
            if self.full_history
            else "Show full history"
        )

        if self.full_history:
            self.show_full_history()
        else:
            self.show_compact_history()

    def export_events(self):
        path = Path("runs/events.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.events, indent=2, ensure_ascii=False), encoding="utf-8")
        self.query_one("#receipt", Static).update(f"Exported {len(self.events)} events to {path}")

    def on_list_view_selected(self, event: ListView.Selected):
        if event.list_view.index is not None:
            self.follow_live = False
            self.query_one("#follow-live", Button).label = "Follow live"
            self.show_event_details(self.events[event.list_view.index])

    def show_event_details(self, event):
        self.query_one("#thought", Static).update(
            f"[bold]THOUGHTS[/bold]\n{event.get('thoughts', 'No thoughts recorded.')}"
        )
        self.query_one("#memory-content", Static).update(
            f"[bold]MEMORY[/bold]\n{event.get('memory', 'No memory recorded.')}"
        )
        self.query_one("#action", Static).update(
            "[bold]ACTION[/bold]\n"
            + json.dumps(event["action"], indent=2, ensure_ascii=False)
        )
        receipt = event["receipt"]
        status = "OK" if receipt.get("ok") else "FAILED"
        self.query_one("#receipt", Static).update(
            f"[bold]RECEIPT — Status:[/bold] {status}\n"
            f"{receipt.get('result', receipt.get('error', ''))}"
        )

    def show_full_history(self):
        history = self.query_one("#history", ListView)

        # Remove the compact entries currently visible.
        history.clear()

        for event in self.events:
            action = json.dumps(
                event["action"],
                indent=2,
                ensure_ascii=False,
            )

            receipt = json.dumps(
                event["receipt"],
                indent=2,
                ensure_ascii=False,
            )

            status = "OK" if event["receipt"].get("ok") else "FAILED"

            history.append(ListItem(Label(
                f"[bold cyan]Step {event['step']} — "
                f"{event['agent']}[/bold cyan]\n"
                f"[bold]Thoughts:[/bold]\n"
                f"{event.get('thoughts', '')}\n"
                f"[bold]Action:[/bold]\n"
                f"{action}\n"
                f"[bold]Receipt:[/bold]\n"
                f"{status}\n"
                f"{'─' * 50}"
            )))

    def show_compact_history(self):
        history = self.query_one("#history", ListView)
        history.clear()

        for event in self.events:
            action = event["action"]
            receipt = event["receipt"]
            status = "OK" if receipt.get("ok") else "FAILED"

            history.append(ListItem(Label(
                f"Step {event['step']} | "
                f"{event['agent']} | "
                f"{action.get('action', 'invalid')} | "
                f"{status}"
            )))

    def show_event(self, event):

        if event["type"] == "action":
            action = self.query_one("#action", Static)
            receipt = self.query_one("#receipt", Static)
            thought = self.query_one("#thought", Static)
            memory = self.query_one("#memory-content", Static)
            history = self.query_one("#history", ListView)

            action_json = json.dumps(
                event["action"],
                indent=2,
                ensure_ascii=False,
            )

            self.events.append(event)
            if self.follow_live:
                thought.update(
                    f"[bold]THOUGHTS — Step {event['step']} — {event['agent']}[/bold]\n"
                    f"{event.get('thoughts', 'No thoughts recorded.')}"
                )
                memory.update(
                    f"[bold]MEMORY — {event['agent']}[/bold]\n"
                    f"{event.get('memory', 'No memory recorded.')}"
                )
            receipt_data = event["receipt"]
            status = "OK" if receipt_data.get("ok") else "FAILED"
            message = receipt_data.get("result", receipt_data.get("error", ""))

            if self.follow_live:
                action.update(
                f"[bold]ACTION — Step {event['step']} — "
                f"{event['agent']}[/bold]\n\n"
                f"{action_json}"
                )

            color = "green" if receipt_data.get("ok") else "red"
            if self.follow_live:
                receipt.update(
                    f"[bold]RECEIPT — Status:[/bold] [{color}]{status}[/{color}]\n{message}"
                )

            action_name = event["action"].get("action")
            if isinstance(action_name, str) and action_name.lower() == "read":
                history.append(ListItem(Label(
                    f"Step {event['step']} | "
                    f"{event['agent']} | "
                    f"{event['action'].get('action', 'invalid')} => {event['action'].get('path', 'invalid')} | {status}"
                )))
            else:
                history.append(ListItem(Label(
                    f"Step {event['step']} | "
                    f"{event['agent']} | "
                    f"{event['action'].get('action', 'invalid')} | {status}"
                )))
        elif event["type"] == "thinking":
            if self.follow_live:
                self.query_one("#thought", Static).update(
                    f"[bold]THOUGHTS — Step {event['step']} — "
                    f"{event['agent']}[/bold]\n\n"
                    f"Thinking...\n"
                )

        elif event["type"] == "thoughts":
            if self.follow_live:
                self.query_one("#thought", Static).update(
                    f"[bold]THOUGHTS — Step {event['step']} — "
                    f"{event['agent']}[/bold]\n\n"
                    f"{event['thoughts']}"
                )
