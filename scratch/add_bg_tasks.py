import re
import os

ROUTER_PATH = "backend/app/domains/tickets/router.py"
with open(ROUTER_PATH, "r") as f:
    content = f.read()

# Add to function definitions
for func_name in ["create_ticket", "create_message", "assign_ticket", "update_ticket_status"]:
    pattern = rf"(def {func_name}\([^)]*?)(\)\s*->\s*Any:)"
    # only add if not already there
    def repl(m):
        sig = m.group(1)
        if "background_tasks" not in sig:
            return f"{sig}, background_tasks: BackgroundTasks" + m.group(2)
        return m.group(0)
    content = re.sub(pattern, repl, content)

with open(ROUTER_PATH, "w") as f:
    f.write(content)
print("Done adding BackgroundTasks")
