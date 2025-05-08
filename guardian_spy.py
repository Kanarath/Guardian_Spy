#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Guardian Spy: OPSEC Assistant for OSINT Practioners.
Entry point for the Guardian Spy CLI application.
"""

import sys
import subprocess # For browser_process.wait in KeyboardInterrupt (though main_cli now handles this specific part)
from guardian_spy import main_cli
from guardian_spy.main_cli import console # Import the console instance

if __name__ == "__main__":
    try:
        main_cli.start()
    except KeyboardInterrupt:
        # This will catch Ctrl+C if it happens outside the browser_process.wait()
        # or if re-raised from within main_cli.start() (which it is now)
        console.print("\n[bold yellow]Guardian Spy session terminated by user.[/bold yellow]")
        
        # Attempt to clean up profile if it was created and the session was interrupted
        # The main_cli.start() function's own try/finally for browser_process.wait()
        # should handle cleanup if interrupt happens *during* browser wait.
        # This block here is more for interrupts *before* browser launch or *after* browser close but before script end.
        # However, main_cli.start() also has cleanup logic for normal exit or its own KeyboardInterrupt.
        # This might be slightly redundant but acts as a final failsafe.
        profile_to_clean = main_cli.SESSION_CONFIG.get("profile_path")
        is_temp = main_cli.SESSION_CONFIG.get("is_temp_profile")

        if is_temp and profile_to_clean and os.path.exists(profile_to_clean): # Check os.path.exists
            console.print(f"[bold blue]Ensuring cleanup of temporary profile: {profile_to_clean}[/bold blue]")
            if main_cli.browser_manager.remove_profile(profile_to_clean, console=console):
                console.print("  [green][*] Temporary profile successfully removed during final cleanup.[/green]")
            else:
                console.print(f"  [bold red][!] Failed to remove temporary profile during final cleanup.[/bold red]")
                
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred in Guardian Spy main execution:[/bold red]")
        # console.print_exception(show_locals=True) # Rich's beautiful exception formatting, enable for debugging
        console.print(f"[italic red]{type(e).__name__}: {e}[/italic red]") # Simpler error for release
    finally:
        console.print("\n[bold blue]Exiting Guardian Spy.[/bold blue]")
        sys.exit(0)