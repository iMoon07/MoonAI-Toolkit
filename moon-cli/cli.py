import os
import sys
import time
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from dotenv import load_dotenv

from llm.client import MoonLLM
from llm.memory import Memory
from llm.stabilizer import stabilize_output

load_dotenv()

sys.stdout.reconfigure(encoding='utf-8')
console = Console()
style = Style.from_dict({'prompt': 'bold white'})


# =========================
# CONFIG VALIDATION
# =========================
def validate_config():
    required = ["OPENAI_API_KEY", "API_BASE_URL", "MODEL_NAME"]
    missing = [k for k in required if not os.getenv(k)]

    if missing:
        console.print(f"[red]Missing Config:[/red] {', '.join(missing)}")
        sys.exit(1)


# =========================
# UI RENDER
# =========================
def render_header(model):
    console.print("[bold cyan]🌙 Moon CLI[/bold cyan]")
    console.print(f"[dim]{model}[/dim]\n")


def render_prompt_header():
    console.print("\n[bold cyan]🌙 Moon[/bold cyan]\n")


def render_footer(text, start):
    elapsed = time.time() - start
    words = len(text.split())
    speed = words / elapsed if elapsed > 0 else 0

    console.print(f"\n[dim]✓ {elapsed:.1f}s | ~{words} words | {speed:.1f} words/s[/dim]\n")


# =========================
# TIMER
# =========================
class Timer:
    def __init__(self):
        self.running = False
        self.thread = None
        self.start_time = 0

    def spin(self):
        while self.running:
            elapsed = time.time() - self.start_time
            sys.stdout.write(f"\r\033[2m[{elapsed:.1f}s] Loading data...\033[0m")
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self.spin, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(0.1)
        sys.stdout.write("\r\033[K")


# =========================
# MAIN LOOP
# =========================
def run():
    validate_config()

    llm = MoonLLM()
    # Read system prompt from the new architecture
    prompt_path = os.path.join(os.path.dirname(__file__), "prompt", "system.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except:
        system_prompt = "You are Moon."
        
    base_system_prompt = system_prompt
    
    memory = Memory(base_system_prompt)
    session = PromptSession()
    spinner = Timer()

    os.system("cls" if os.name == "nt" else "clear")
    render_header(f"{llm.model} | [bold green]Auto-Sync 🧠[/bold green]")

    while True:
        try:
            user = session.prompt("Raja > ", style=style)
            
            # SANITIZER: Clean text from broken unicode/surrogates from Windows copy-paste
            user = user.encode('utf-8', 'replace').decode('utf-8')

            # TRUNCATOR: Prevent LM Studio Token Overflow (Max ~15,000 characters for n_ctx: 4096)
            if len(user) > 15000:
                console.print("\n[dim yellow]⚠️ Text is too long! Auto-truncating to prevent crash (Context Overflow)...[/dim yellow]")
                user = user[:15000] + "\n... [TRUNCATED BY MOON CLI]"

            if not user.strip():
                continue

            if user in ["exit", "quit"]:
                break

            if user == "/clear":
                os.system("cls" if os.name == "nt" else "clear")
                memory.reset()
                render_header(f"{llm.model} | [bold green]Auto-Sync 🧠[/bold green]")
                continue

            # Use pure system prompt without silly intent/mood analysis
            memory.system = base_system_prompt
            
            # Remove Intent/Mood log printing on screen
            # console.print(...) -> Removed to keep it clean

            start = time.time()
            spinner.start()

            # Natural input without forced context
            memory.add("user", user)
            stream = llm.stream(memory.build())

            output = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    output += delta

            spinner.stop()
            
            # Execute Stabilizer Engine
            final_output = stabilize_output(output)
            
            render_prompt_header()
            console.print(final_output)

            memory.add("assistant", final_output)
            render_footer(final_output, start)

        except KeyboardInterrupt:
            spinner.stop()
            console.print("\n[dim]Interrupted[/dim]\n")
            continue

        except Exception as e:
            spinner.stop()
            
            # ROLLBACK MEMORY: Remove the last message from memory so giant texts/errors don't get stuck forever!
            if len(memory.messages) > 0 and memory.messages[-1]["role"] == "user":
                memory.messages.pop()

            err_str = str(e).lower()
            if "authentication" in err_str or "api key" in err_str or "401" in err_str:
                msg = "Authentication failed. Please check your OPENAI_API_KEY."
            elif "connection" in err_str or "failed to connect" in err_str or "refused" in err_str:
                msg = "Connection error. Is your local AI server running?"
            elif "timeout" in err_str:
                msg = "Request timed out."
            else:
                msg = f"API Error: {e}"
            console.print(f"\n[bold red]{msg}[/bold red]\n")

if __name__ == "__main__":
    run()
