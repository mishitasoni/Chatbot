import psutil
import socket

def get_listening_ports():
    connections = psutil.net_connections(kind='inet')
    listening = []
    for conn in connections:
        if conn.status == 'LISTEN' and conn.laddr.ip in ('127.0.0.1', '0.0.0.0', '::', '::1'):
            listening.append((conn.laddr.port, conn.pid))
            
    for port, pid in sorted(list(set(listening))):
        try:
            process = psutil.Process(pid)
            name = process.name()
        except:
            name = "Unknown"
        print(f"Port {port} is listening (Process: {name}, PID: {pid})")

if __name__ == "__main__":
    get_listening_ports()
