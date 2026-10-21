---
applyTo: "src/etl/interfaces/**"
---
# Interfaces layer rules (CLI and Tkinter)

- Call `application` through objects built by `etl.container`. Never import `etl.infrastructure` (A-10).
- No business logic here. Views are dumb; presenters hold UI logic (MVP).
- Tkinter: run the pipeline in a worker thread, send messages through a `queue.Queue`, poll with
  `root.after(100, ...)`. Never touch widgets from the worker thread. Disable Run while running.
- Show readable messages, never stack traces. Errors arrive as `RunSummary.error` or a message event.
- Output goes through `typer.echo` or the `ProgressReporter`, not `print` (C-5).
