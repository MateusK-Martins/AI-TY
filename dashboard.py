import json

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label
from textual import work
from environment import Environment

class Dashboard(App):
    CSS = """
    #main {
        width: 70%;
        padding: 1 2;
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

    #action {
        height: 1fr;
        border: solid green;
        padding: 1;
    }

    #receipt {
        height: 1fr;
        border: solid yellow;
        padding: 1;
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
            with Vertical(id="main"):
                yield Static("No thoughts yet", id="thought")
                yield Static("No action yet", id="action")
                yield Static("No receipt yet", id="receipt")

            with Vertical(id="history_panel"):
                yield Button("Following live", id="follow-live")
                yield Button("Show full history", id="full-history")
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

    def on_list_view_selected(self, event: ListView.Selected):
        if event.list_view.index is not None:
            self.follow_live = False
            self.query_one("#follow-live", Button).label = "Follow live"
            self.show_event_details(self.events[event.list_view.index])

    def show_event_details(self, event):
        self.query_one("#thought", Static).update(event.get("thoughts", ""))
        self.query_one("#action", Static).update(
            json.dumps(event["action"], indent=2, ensure_ascii=False)
        )
        receipt = event["receipt"]
        status = "OK" if receipt.get("ok") else "FAILED"
        self.query_one("#receipt", Static).update(
            f"{status}\n{receipt.get('result', receipt.get('error', ''))}"
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
            history = self.query_one("#history", ListView)

            action_json = json.dumps(
                event["action"],
                indent=2,
                ensure_ascii=False,
            )

            self.events.append(event)
            if self.follow_live:
                thought.update(event.get("thoughts", "No thoughts recorded."))
            receipt_data = event["receipt"]
            status = "OK" if receipt_data.get("ok") else "FAILED"
            message = receipt_data.get("result", receipt_data.get("error", ""))

            if self.follow_live:
                action.update(
                f"[bold cyan]Step {event['step']} — "
                f"{event['agent']}[/bold cyan]\n\n"
                f"[bold]Action[/bold]\n"
                f"{action_json}"
                )

            color = "green" if receipt_data.get("ok") else "red"
            if self.follow_live:
                receipt.update(
                    f"[bold]Status:[/bold] [{color}]{status}[/{color}]\n{message}"
                )

            if event["action"].get("action").lower() == "read":
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
            action = self.query_one("#action", Static)
            receipt = self.query_one("#receipt", Static)
            history = self.query_one("#history", ListView)

            action.update(
                f"[bold cyan]Step {event['step']} — "
                f"{event['agent']}[/bold cyan]\n\n"
                f"[bold]Thinking...[/bold]\n"
            )

        elif event["type"] == "thoughts":
            action = self.query_one("#action", Static)
            receipt = self.query_one("#receipt", Static)
            history = self.query_one("#history", RichLog)

            action.update(
                f"[bold cyan]Step {event['step']} — "
                f"{event['agent']}[/bold cyan]\n\n"
                f"[bold]Thoughts[/bold]\n"
                f"{event['thoughts']}"
            )
