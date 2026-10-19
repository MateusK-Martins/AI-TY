Choose exactly one action and return exactly one JSON object. Do not write
explanations, Markdown fences, comments, or more than one object.

Every value must be a real value you choose. The words in these examples describe
the type of value; do not copy them literally.

{"action":"send","to":"the recipient's exact name","text":"the message"}
{"action":"transfer","to":"the recipient's exact name","amount":5}
{"action":"list","start":0,"limit":20}
{"action":"read","path":"constitution.md","start":0,"limit":40}
{"action":"write","path":"notes.md","index":3,"content":"a line of text","revision":"revision from a previous read"}

Use `list` before an unfamiliar file. Paths are relative to `shared/`; never
write `shared/` at the beginning of a path. Use the `append_index` and `revision`
returned by `read` when appending or editing. Use only fields required by the
selected action. A private `send` reaches only its named recipient; use a shared
file for information others should see. Transfers require a positive whole
number and change private balances only after a successful receipt.
