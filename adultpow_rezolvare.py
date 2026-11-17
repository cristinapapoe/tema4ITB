import socket
import hashlib
import itertools
import re
from multiprocessing import Pool, cpu_count

HOST = "202.61.227.83"
PORT = 31338
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn0123456789"
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def worker(args):
    first_char, target_hash = args
    remaining_chars = [c for c in ALPHABET if c != first_char]
    for comb in itertools.permutations(remaining_chars, 4):
        candidate = first_char + "".join(comb)
        if hashlib.sha256(candidate.encode()).hexdigest() == target_hash:
            return candidate
    return None

def solve_adult(target_hash, pool):
    tasks = [(c, target_hash) for c in ALPHABET]
    for res in pool.imap_unordered(worker, tasks):
        if res is not None:
            return res
    return None

def recv_until_prompt(sock, buffer):
    while True:
        clean_buf = ANSI_ESCAPE.sub('', buffer)
        if "Mine xxxx:" in clean_buf:
            for line in clean_buf.splitlines():
                if " == " in line:
                    idx = clean_buf.index("Mine xxxx:") + len("Mine xxxx:")
                    return line.strip(), clean_buf[idx:]
        data = sock.recv(4096)
        if not data:
            raise EOFError(f"Serverul a inchis conexiunea. Ultimul mesaj:\n{repr(clean_buf)}")
        buffer += data.decode("utf-8", errors="ignore")

if __name__ == "__main__":
    with Pool(cpu_count()) as pool:
        with socket.create_connection((HOST, PORT), timeout=60) as s:
            buf = ""
            for r in range(5):
                challenge, buf = recv_until_prompt(s, buf)
                print(f"[Runda {r+1}/5] {challenge}")

                target_hash = challenge.split(" == ")[1].strip()
                ans = solve_adult(target_hash, pool)
                print(f" -> Gasit: {ans}")

                s.sendall((ans + "\r").encode())

            s.settimeout(5.0)
            try:
                while True:
                    data = s.recv(4096)
                    if not data:
                        break
                    buf += data.decode("utf-8", errors="ignore")
            except socket.timeout:
                pass

            print("\n--- REZULTAT FINAL ---")
            print(ANSI_ESCAPE.sub('', buf).strip())
