"""Tkinter presenter: UI logic, worker thread, queue polling. TODO(step 6).

Rules: run the pipeline in a worker thread, post messages to a queue.Queue, poll with
root.after(100, ...), never touch widgets from the worker, disable Run while running.
"""
