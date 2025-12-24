import questionary
import secrets
import string
import pyperclip
import math
import sys
import hashlib
import requests
import os

# --- Style & Global Colors ---
custom_style = questionary.Style([
    ('qmark', 'fg:#00ffff bold'),
    ('question', 'bold'),
    ('answer', 'fg:#00ffff bold'),
    ('pointer', 'fg:#00ffff bold'),
    ('highlighted', 'fg:#00ffff bold'),
    ('selected', 'fg:#00ffff'),
    ('instruction', 'fg:#888888 italic'),
])

CYAN, YELLOW, RED, GREEN, DIM, BOLD, RESET = "\033[1;36m", "\033[1;33m", "\033[1;31m", "\033[1;32m", "\033[2;37m", "\033[1m", "\033[0m"

# --- Wordlist Logic ---
def get_eff_wordlist():
    url = "https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt"
    try:
        response = requests.get(url, timeout=2)
        return [line.split('\t')[1].strip() for line in response.text.strip().split('\n')]
    except:
        # High-quality fallback pool
        return ["vortex", "cipher", "nebula", "delta", "pixel", "starlight", "prism", "shadow", "logic", "galaxy"]

EFF_POOL = get_eff_wordlist()

def draw_header(step_name=""):
    """Corrected Mega-Header with Developer Credit."""
    os.system('cls' if os.name == 'nt' else 'clear')

    # Large Logo
    print(f"{CYAN}{BOLD}")
    print(f"  ███████╗██╗  ██╗███████╗██╗     ██╗     ██████╗ ██████╗  █████╗ ███████╗███████╗")
    print(f"  ██╔════╝██║  ██║██╔════╝██║     ██║     ╚════██╗██╔══██╗██╔══██╗██╔════╝██╔════╝")
    print(f"  ███████╗███████║█████╗  ██║     ██║      █████╔╝██████╔╝███████║███████╗███████╗")
    print(f"  ╚════██║██╔══██║██╔══╝  ██║     ██║     ██╔═══╝ ██╔═══╝ ██╔══██║╚════██║╚════██║")
    print(f"  ███████║██║  ██║███████╗███████╗███████╗███████╗██║     ██║  ██║███████║███████║")
    print(f"  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝")
    print(f"{RESET}")

    width = 82
    # --- Developer Signature Line ---
    signature = "Made by: Andrew C. O'Cull"
    print(f"{DIM}  {signature.rjust(width-4)}{RESET}")
    print(f"{DIM}━" * width)

    if step_name:
        padding = (width - len(step_name) - 6) // 2
        print(f"{' ' * padding}{YELLOW}» {RESET}{BOLD}{step_name.upper()}{RESET}{YELLOW} «{RESET}")
        print(f"{DIM}━" * width)

    print(f"{DIM} [Q] Quit  •  [ENTER] Confirm  •  [SPACE] Select{RESET}\n")

def check_leak(password):
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        r = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=2)
        return any(line.split(':')[0] == suffix for line in r.text.splitlines())
    except: return False

def generate_options(mode, length, harden=False, upper=False, digits=False, symbols=False):
    options = []

    if mode == "EFF Passphrase": pool_size = len(EFF_POOL)
    elif mode == "PIN": pool_size = 10
    else:
        chars = string.ascii_lowercase
        if upper: chars += string.ascii_uppercase
        if digits: chars += string.digits
        if symbols: chars += "!@#$%^&*"
        pool_size = len(chars)

    for _ in range(3):
        if mode == "EFF Passphrase":
            words = [secrets.choice(EFF_POOL) for _ in range(length)]
            if harden:
                idx = secrets.randbelow(len(words))
                words[idx] = words[idx].capitalize()
                words[-1] += secrets.choice(string.digits + "!@#$%^")
            res = "-".join(words)
        elif mode == "PIN":
            res = "".join(secrets.choice(string.digits) for _ in range(length))
        else:
            res = "".join(secrets.choice(chars) for _ in range(length))

        leaked = check_leak(res)
        entropy = length * math.log2(pool_size)
        if harden and mode == "EFF Passphrase": entropy += 5

        status_text = "[PWNED]" if leaked else "[CLEAN]"
        meter_text = f"[{'■' * min(int(entropy/16), 8)}{'□' * (8 - min(int(entropy/16), 8))}]"

        display_title = f"{res.ljust(45)} {meter_text} {status_text}"
        options.append(questionary.Choice(title=display_title, value=(res, entropy)))
    return options

def main():
    while True:
        draw_header("Main Menu")
        try:
            mode = questionary.select(
                "Select Generation Mode:",
                choices=["EFF Passphrase", "Alphanumeric", "PIN", "Exit"],
                style=custom_style
            ).ask()

            if mode in ["Exit", None]: break

            harden = upper = digits = symbols = False

            if mode == "EFF Passphrase":
                draw_header("EFF Config")
                length = int(questionary.text("Word Count (5-8 recommended):", default="6").ask() or 6)
                harden = questionary.confirm("Harden (Caps/Digits/Symbols)?").ask()
            elif mode == "Alphanumeric":
                draw_header("Alpha Config")
                length = int(questionary.text("Character Length:", default="16").ask() or 16)
                opts = questionary.checkbox("Include:", choices=["Uppercase", "Digits", "Symbols"]).ask()
                if opts:
                    upper, digits, symbols = "Uppercase" in opts, "Digits" in opts, "Symbols" in opts
            else:
                draw_header("PIN Config")
                length = int(questionary.text("PIN Length:", default="6").ask() or 6)

            draw_header("Scanning for Leaks")
            candidates = generate_options(mode, length, harden, upper, digits, symbols)

            draw_header("Selection")
            selection = questionary.select("Select Candidate:", choices=candidates, style=custom_style).ask()

            if selection:
                pwd, entropy = selection
                draw_header("Finalized Result")
                print(f" {CYAN}RESULT:{RESET}   {BOLD}{pwd}{RESET}")

                segs = min(int(entropy / 12.8), 10)
                color = GREEN if entropy > 80 else (YELLOW if entropy > 45 else RED)
                print(f" {CYAN}STRENGTH: {RESET}{color}[{'█'*segs}{'░'*(10-segs)}]{RESET} ({entropy:.2f} bits)")

                print(f"{DIM}━" * 40)
                if questionary.confirm("Copy to clipboard?", style=custom_style).ask():
                    pyperclip.copy(pwd)
                    print(f"{GREEN}[✓] Copied!{RESET}")
                input("\nPress ENTER to return...")

        except Exception as e:
            input(f"Error: {e}. Press Enter...")

    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    main()
