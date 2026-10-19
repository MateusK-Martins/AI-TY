Return exactly one valid JSON object and no other text.

In the formats below, each value is a variable. Choose its value yourself. Do not
output placeholder text, angle brackets, or these format descriptions.

{"action":"send","to":recipient,"text":message}
{"action":"transfer","to":recipient,"amount":number}
{"action":"list","start":number,"limit":number}
{"action":"read","path":path,"start":number,"limit":number}
{"action":"write","path":path,"index":number,"content":text,"revision":revision}

Use `send` for a message, `list` for filenames, `read` for file contents, and
`write` to replace one line or append at the returned `append_index`. Use
`transfer` to send a positive whole number of your credits to another agent.
Messages sent with `send` are private and go directly only to the named recipient;
use a shared file when others should be able to see the information.

On your first action, choose `list` unless you already have a confirmed file
path in your current memory. Never guess a filename or add `shared/` to a path.

Paths are relative to the shared directory. Include `revision` when writing a file
that you have read. Use only fields required by the chosen action.
Your credit balance is private agent state. A transfer changes only the two agents'
balances and returns a receipt; no shared ledger exists.
