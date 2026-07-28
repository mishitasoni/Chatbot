with open('openclaw_debug2.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print("".join(lines[-20:]))
