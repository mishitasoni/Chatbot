import subprocess
try:
    process = subprocess.Popen(["openclaw.cmd", "channels", "login", "--help"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
    try:
        out, err = process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        out, err = process.communicate()
    with open("e:\\Chatbot\\help_out.txt", "w") as f:
        f.write(out)
except Exception as e:
    with open("e:\\Chatbot\\help_out.txt", "w") as f:
        f.write(str(e))

