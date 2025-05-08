# Copyright (C) 2025 Kanarath.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Guardian Spy: OPSEC Assistant for OSINT Practioners.
Entry point for the Guardian Spy CLI application.
"""

import sys
import os # Needed for os.path.exists
# subprocess is not directly needed here anymore as main_cli handles its part
from guardian_spy import main_cli
from guardian_spy.main_cli import console # Import the console instance

if __name__ == "__main__":
    profile_to_clean_on_exit = None
    is_temp_profile_on_exit = False

    try:
        main_cli.start()
        # After main_cli.start() finishes normally, capture profile info for final cleanup if needed
        # This is more for unexpected exits after start() but before finally.
        # Normal cleanup is handled within start() or its own try/except/finally for browser ops.
        if hasattr(main_cli, 'SESSION_CONFIG'):
             profile_to_clean_on_exit = main_cli.SESSION_CONFIG.get("profile_path")
             is_temp_profile_on_exit = main_cli.SESSION_CONFIG.get("is_temp_profile", False)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Guardian Spy session terminated by user (main level).[/bold yellow]")
        
        # Attempt to clean up profile if it was created and the session was interrupted
        # Check if SESSION_CONFIG exists and has the required keys
        if hasattr(main_cli, 'SESSION_CONFIG'):
            profile_to_clean = main_cli.SESSION_CONFIG.get("profile_path")
            is_temp = main_cli.SESSION_CONFIG.get("is_temp_profile", False) # Default to False if key missing

            if is_temp and profile_to_clean and os.path.exists(profile_to_clean):
                console.print(f"[bold blue]Ensuring cleanup of temporary profile due to interruption: {profile_to_clean}[/bold blue]")
                # Ensure browser_manager is available for cleanup
                if hasattr(main_cli, 'browser_manager'):
                    if main_cli.browser_manager.remove_profile(profile_to_clean, console=console):
                        console.print("  [green][*] Temporary profile successfully removed during interrupt cleanup.[/green]")
                    else:
                        console.print(f"  [bold red][!] Failed to remove temporary profile during interrupt cleanup.[/bold red]")
                else:
                    console.print("[yellow]Could not access browser_manager for cleanup. Manual removal might be needed.[/yellow]")
            elif profile_to_clean:
                console.print(f"[dim]Profile at {profile_to_clean} was not temporary or path no longer exists. No cleanup action taken here.[/dim]")
        else:
            console.print("[dim]Session configuration not available for interrupt cleanup (likely interrupted very early).[/dim]")
                
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred in Guardian Spy main execution:[/bold red]")
        # Use this for detailed debugging:
        # console.print_exception(show_locals=True, word_wrap=True) 
        # Use this for a cleaner error message in "production":
        console.print(f"[italic red]{type(e).__name__}: {e}[/italic red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]") # Print minimal traceback for context

    finally:
        # This 'finally' block will run regardless of how the 'try' block exits (normal, exception, interrupt)
        # However, if KeyboardInterrupt occurs, its own cleanup runs first.
        # This is a last-resort cleanup for profiles if main_cli.start() was running and exited unexpectedly
        # without its own cleanup completing, and profile_to_clean_on_exit was set.
        if is_temp_profile_on_exit and profile_to_clean_on_exit and os.path.exists(profile_to_clean_on_exit):
            # Check if it wasn't already cleaned by an interrupt handler or normal flow within main_cli.start()
            # This check might be complex. For simplicity, we can just try to remove again.
            # shutil.rmtree is idempotent in the sense that if the path doesn't exist, it won't error hard.
            # browser_manager.remove_profile handles non-existence gracefully.
            console.print(f"\n[bold blue]Performing final check for temporary profile cleanup: {profile_to_clean_on_exit}[/bold blue]")
            if hasattr(main_cli, 'browser_manager'):
                 if main_cli.browser_manager.remove_profile(profile_to_clean_on_exit, console=console):
                    console.print("  [green][*] Temporary profile confirmed clean or was removed in final check.[/green]")
            else:
                console.print("[yellow]Could not access browser_manager for final cleanup check.[/yellow]")


        console.print("\n[bold blue]Exiting Guardian Spy.[/bold blue]")
        sys.exit(0)