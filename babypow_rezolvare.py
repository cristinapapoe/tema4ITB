import socket
import hashlib
import itertools
import string
import re

HOST = "202.61.227.83"
PORT = 31337
ALPHABET = string.ascii_letters + string.digits

HASH_FUNCS = {
    "sha256": hashlib.sha256,
    "md5": hashlib.md5,
    "keccak": hashlib.sha3_256
}

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def solve_round(line):
    algo_name, rest = line.split("(", 1)
    inside, target_hash = rest.split(") == ")
    target_hash = target_hash.strip()
    suffix = inside.split(" + ")[1]

    prefix_len = 20 - len(suffix)
    hash_fn = HASH_FUNCS[algo_name.strip()]

    valid_chars = [c for c in ALPHABET if c not in suffix]

    for comb in itertools.permutations(valid_chars, prefix_len):
        prefix = "".join(comb)
        candidate = (prefix + suffix).encode()
        if hash_fn(candidate).hexdigest() == target_hash:
            return prefix
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

with socket.create_connection((HOST, PORT), timeout=30) as s:
    buf = ""
    for r in range(15):
        challenge, buf = recv_until_prompt(s, buf)
        print(f"[Runda {r+1}/15] {challenge}")

        ans = solve_round(challenge)
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
