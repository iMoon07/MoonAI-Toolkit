import os
import sys
import time
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console

from moon_core.runtime.router import moon_router
from moon_core.config import settings
from moon_core.models import ChatRequest, Module

sys.stdout.reconfigure(encoding='utf-8')
console = Console()
style = Style.from_dict({'prompt': 'bold white'})

# =========================
# UTILS & RENDERERS
# =========================
def sanitize_input(text):
    text = text.encode('utf-8', 'replace').decode('utf-8')
    text = text.replace('\x00', '').replace('\ufeff', '').replace('\u200b', '')
    return text.strip()

def render_header(model):
    console.print("[bold cyan]🌙 Moon CLI[/bold cyan]")
    console.print(f"[dim]{model}[/dim]\n")

def render_prompt_header():
    console.print("\n[bold cyan]🌙 Moon[/bold cyan]\n")

def render_footer(tokens, start):
    elapsed = time.time() - start
    speed = tokens / elapsed if elapsed > 0 else 0
    console.print(f"\n\n[dim]✓ {elapsed:.1f}s | {tokens} tokens | {speed:.1f} tokens/s[/dim]\n")

# =========================
# MAIN LOOP
# =========================
def run():
    session = PromptSession()

    console.clear()
    render_header(f"{settings.model_name} | [bold green]Developed By iMoon07[/bold green]")

    while True:
        try:
            raw_user = session.prompt("Raja > ", style=style)
            user_input = sanitize_input(raw_user)
            
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye", ":q"]:
                console.print("\n[dim]Sampai jumpa, Raja[/dim]")
                break

            if user_input == "/clear":
                console.clear()
                # Create a fresh session by passing a unique identifier or triggering logic
                # For now, restarting the CLI will just resume. To reset, we can build a /reset command
                render_header(f"{settings.model_name} | [bold green]Developed By iMoon07[/bold green]")
                continue
            
            start = time.time()
            tokens_generated = 0
            
            # Build Data Object
            request = ChatRequest(
                module=Module.CLI,
                platform_user_id="local_admin",
                display_name="Raja",
                content=user_input,
                intent="CHAT"
            )
            
            # Request LLM Stream via MoonAgent Pipeline
            stream = moon_router.chat_stream(request)
            
            # UX: Spinner while waiting for first byte
            status = console.status("[dim]🧠 Gemma is thinking...[/dim]", spinner="dots")
            status.start()
            
            first_token = True
            
            try:
                for delta in stream:
                    if first_token:
                        status.stop() # Kill spinner
                        first_token = False
                        render_prompt_header()
                        
                    # True Streaming: Print directly to stdout real-time
                    print(delta, end="", flush=True)
                    tokens_generated += 1
            finally:
                status.stop() # Safety catch if stream crashes early
            
            render_footer(tokens_generated, start)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Interrupted. Exiting...[/dim]\n")
            break
        except Exception as e:
            if 'status' in locals():
                status.stop()
            console.print(f"\n[bold red]Error: {e}[/bold red]\n")

if __name__ == "__main__":
    run()
