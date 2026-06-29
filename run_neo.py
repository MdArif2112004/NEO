"""
run_neo.py
==========
The A.V.E.N.G.E.R.S. Terminal Interface for NEO.
"""
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from neo.brain import NeoBrain

# Initialize the rich console
console = Console()

def boot_sequence():
    """Clears the screen and displays the startup UI."""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # The sci-fi header
    header = (
        "[bold cyan]A.V.E.N.G.E.R.S. COMMAND CENTER[/bold cyan]\n"
        "[blue]Neural Environment Operations (N.E.O.) - v2.0[/blue]\n"
        "[white]Status: Fully Operational | Modules: Dual-Engine AI[/white]"
    )
    console.print(Panel.fit(header, border_style="cyan", padding=(1, 4)))
    console.print("[bold green]SYSTEM ONLINE.[/bold green]\n")

if __name__ == "__main__":
    boot_sequence()
    
    # Initialize the brain silently before asking for input
    brain = NeoBrain()
    console.print("\n[dim]Type 'exit' or 'quit' to power down the system.[/dim]\n")
    
    # If you passed a command via the old method (e.g., python run_neo.py "Task")
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        console.print(f"[bold yellow]Executing Protocol:[/bold yellow] {task}\n")
        brain.run(task)
    else:
        # The New Interactive Loop!
        while True:
            # The custom sci-fi prompt input
            task = Prompt.ask("[bold cyan]Sir[/bold cyan]")
            
            if task.lower() in ['exit', 'quit']:
                console.print("\n[bold red]Powering down neural matrix... Goodbye.[/bold red]")
                break
            
            console.print("\n")
            brain.run(task)
            console.print("\n[bold green]➜ Standing by for next directive.[/bold green]\n")
