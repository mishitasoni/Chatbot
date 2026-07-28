with open('openclaw_debug2.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    with open('tail_output.txt', 'w', encoding='utf-8') as out:
        out.write("".join(lines[-30:]))
