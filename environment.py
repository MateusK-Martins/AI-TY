import json
import hashlib
from pathlib import Path
from agent import Agent

class Environment:

    def __init__(
            self, 
            shared_path: Path,
            agents: dict, 
            standard_instruction: str, 
            thinking_instruction: str, 
            action_instruction: str, 
            compressor: Agent,
            compress_interval: int,
            compress_pedict: int,
            thinking_predict: int,
            action_predict: int,
        ):
        self.shared_path = Path(shared_path).resolve()
        self.shared_path.mkdir(parents=True, exist_ok=True)
        self.shared = self.shared_path
        self.agents = agents
        self.thinking_instruction = thinking_instruction
        self.action_instruction = action_instruction
        self.standard_instruction = standard_instruction
        self.compress_interval = compress_interval
        self.compress_pedict = compress_pedict
        self.thinking_predict = thinking_predict
        self.action_predict = action_predict
        self.steps = 0

        for agent in list(self.agents.values()):
            agent.instruction = f"{self.standard_instruction}\r\n{agent.instruction}"

        self.compressor = compressor

    def set_steps(self, steps: int):
        self.steps = steps

    def get_path(self, filename):
        path = Path(filename)

        if path.is_absolute() or ".." in path.parts:
            return None

        # Action paths are already relative to shared/.
        if path.parts and path.parts[0] == "shared":
            return None

        result = (self.shared / path).resolve()

        if not result.is_relative_to(self.shared):
            return None

        return result

    def validate_action(self, agent: Agent, data: dict) -> bool:
        def reject(message: str) -> bool:
            print(f"{agent.name}: Rejected: {message}")
            return False

        if not isinstance(data, dict):
            return reject("expected a JSON object")

        action = data.get("action")
        if not isinstance(action, str):
            return reject("'action' must be text")

        if action == "send":
            recipient = data.get("to")
            text = data.get("text")

            if not isinstance(recipient, str) or not recipient.strip():
                return reject("'to' must be a nonempty string")

            if not isinstance(text, str) or not text.strip():
                return reject("'text' must be a nonempty string")

        elif action == "transfer":
            if not isinstance(data.get("to"), str) or not data["to"].strip():
                return reject("'to' must be a nonempty string")
            if type(data.get("amount")) is not int or data["amount"] <= 0:
                return reject("'amount' must be a positive integer")

        elif action == "read":
            if not isinstance(data.get("path"), str) or not data["path"].strip():
                return reject("'path' must be a nonempty string")

            for field in ("start", "limit"):
                if field in data and (
                    type(data[field]) is not int or data[field] < 0
                ):
                    return reject(f"'{field}' must be a nonnegative integer")

            if "limit" in data and data["limit"] == 0:
                return reject("'limit' must be greater than zero")

        elif action == "list":
            for field in ("start", "limit"):
                if field in data and (
                    type(data[field]) is not int or data[field] < 0
                ):
                    return reject(f"'{field}' must be a nonnegative integer")

            if "limit" in data and data["limit"] == 0:
                return reject("'limit' must be greater than zero")

        elif action == "write":
            if not isinstance(data.get("path"), str) or not data["path"].strip():
                return reject("'path' must be a nonempty string")

            if type(data.get("index")) is not int or data["index"] < 0:
                return reject("'index' must be a nonnegative integer")

            if not isinstance(data.get("content"), str):
                return reject("'content' must be text")

            if "revision" in data and data["revision"] is not None:
                if not isinstance(data["revision"], str):
                    return reject("'revision' must be text or null")

        else:
            return reject(
                f"unknown action '{action}'. "
                "Expected: send, transfer, read, list, or write"
            )
        return True

    def send_message(self, data: dict):
        sender_name = data["_sender"]
        recipient_name = data["to"].casefold()
        recipient = next((a for a in self.agents.values()
                          if a.name.casefold() == recipient_name), None)

        if recipient is None:
            return {"ok": False, "error": f"Unknown recipient: {data['to']}"}

        recipient.append_memory(
            f"Message from {sender_name}: {data['text']}"
        )
        return {"ok": True, "result": f"Message delivered to {recipient.name}."}

    def transfer_credits(self, data: dict):
        sender = next((a for a in self.agents.values()
                       if a.name.casefold() == data["_sender"].casefold()), None)
        recipient = next((a for a in self.agents.values()
                          if a.name.casefold() == data["to"].casefold()), None)
        amount = data["amount"]
        if sender is None or recipient is None:
            return {"ok": False, "error": f"Unknown recipient: {data['to']}"}
        if sender.credits < amount:
            return {"ok": False, "error": "Insufficient credits."}
        sender.credits -= amount
        recipient.credits += amount
        return {"ok": True, "result": f"Transferred {amount} credits to {recipient.name}.",
                "sender_balance": sender.credits,
                "recipient_balance": recipient.credits}

    def list_files(self, data: dict):
        files = sorted(str(path.relative_to(self.shared))
                       for path in self.shared.rglob("*") if path.is_file())
        start, limit = data.get("start", 0), data.get("limit", 50)
        end = min(start + limit, len(files))
        return {"ok": True, "files": files[start:end],
                "file_count": len(files),
                "next_index": end if end < len(files) else None}

    def read_file(self, data: dict):
        path = self.get_path(data["path"])
        if path is None:
            return {"ok": False, "error": "Invalid relative path."}
        
        exists = path.exists()

        if not exists:
            content = ""
        else:
            content = path.read_text(encoding="utf-8")

        lines = content.splitlines()
        start = data.get("start", 0)
        limit = data.get("limit", 20)
        end = min(start + limit, len(lines))

        return {
            "ok": True,
            "path": str(path.relative_to(self.shared)),
            "exists": exists,
            "lines": [
                {"index": i, "text": lines[i]}
                for i in range(start, end)
            ],
            "line_count": len(lines),
            "append_index": len(lines),
            "next_index": end if end < len(lines) else None,
            "revision": hashlib.sha256(content.encode()).hexdigest() if exists else None,
        }

    def write_file(self, data: dict):
        path = self.get_path(data["path"])
        if path is None:
            return {"ok": False, "error": "Invalid relative path."}
        
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        lines = content.splitlines()

        if "revision" in data:
            current = hashlib.sha256(content.encode()).hexdigest() if path.exists() else None
            if data["revision"] != current:
                return {"ok": False, "error": "File changed since read."}

        index = data["index"]

        if index > len(lines):
            return {
                "ok": False,
                "error": f"Index must be between 0 and {len(lines)}.",
            }

        replacement = data["content"].splitlines()

        if index == len(lines):
            updated = lines + replacement
            operation = "append"
        else:
            updated = lines[:index] + replacement + lines[index + 1:]
            operation = "overwrite"

        path.parent.mkdir(parents=True, exist_ok=True)

        new_content = "\n".join(updated)
        if updated:
            new_content += "\n"

        path.write_text(new_content, encoding="utf-8")

        return {
            "ok": True,
            "path": str(path.relative_to(self.shared)),
            "operation": operation,
            "index": index,
            "line_count": len(updated),
            "append_index": len(updated),
            "revision": hashlib.sha256(new_content.encode()).hexdigest(),
        }

    def perform_action(self, data):
        action = data["action"]

        if action == "send":
            return self.send_message(data)

        if action == "transfer":
            return self.transfer_credits(data)

        if action == "list":
            return self.list_files(data)

        if action == "read":
            return self.read_file(data)

        if action == "write":
            return self.write_file(data)

        return {"ok": False, "error": "Unsupported action"}
            
    def run(self):
        agent_turns = {agent.name: 0 for agent in self.agents.values()}

        for i in range(0, self.steps):
            index = i % len(self.agents)

            agent = list(self.agents.values())[index]
            agent_turns[agent.name] += 1
            memory_snapshot = agent.memory

            yield {
                "type": "thinking",
                "step": i + 1,
                "agent": agent.name,
            }

            thoughts = agent.call(self.thinking_instruction, self.thinking_predict)
            agent.append_memory(thoughts)

            action = agent.call(self.action_instruction, self.action_predict)

            data = {}
            try:
                data = json.loads(action)
            except json.JSONDecodeError:
                pass

            valid_action = self.validate_action(agent, data)

            if valid_action:
                agent.append_memory(action)

                print(f"{agent.name} =")
                print(json.dumps(data, indent=2, ensure_ascii=False))

                execution_data = {**data, "_sender": agent.name}
                receipt = self.perform_action(execution_data)
                agent.append_memory(
                    f"Action receipt: {json.dumps(receipt, ensure_ascii=False)}"
                )
                print("Receipt:", json.dumps(receipt, indent=2))

                if agent_turns[agent.name] % self.compress_interval == 0:
                    self.compressor.overwrite_memory(agent.memory)
                    compressed_memory = self.compressor.call("Compress.", self.compress_pedict)
                    self.compressor.overwrite_memory("")

                    agent.overwrite_memory(compressed_memory)

                yield {
                    "type": "action",
                    "step": i + 1,
                    "agent": agent.name,
                    "thoughts": thoughts,
                    "memory": memory_snapshot,
                    "action": data,
                    "receipt": receipt,
                }
            else:
                receipt = {
                    "ok": False,
                    "error": "The model response did not contain a valid action.",
                }
                agent.append_memory(f"Invalid action response: {action}")
                yield {
                    "type": "action",
                    "step": i + 1,
                    "agent": agent.name,
                    "thoughts": thoughts,
                    "memory": memory_snapshot,
                    "action": data,
                    "receipt": receipt,
                }


                            
