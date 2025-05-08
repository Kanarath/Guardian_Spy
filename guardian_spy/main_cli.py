# guardian_spy/main_cli.py
import argparse
import sys
import time 
import subprocess # For browser_process.wait in KeyboardInterrupt

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm 
from rich.table import Table
# from rich.live import Live # Not used yet

from . import browser_manager
from . import network_checker
from . import utils # Ensure this import is present
from . import __version__, __app_name__ 

# Initialize Rich Console
console = Console()

SESSION_CONFIG = {
    "browser_selected": None, # e.g. "firefox" or "chrome" (user's choice)
    "browser_actual_type": None, # e.g. "firefox", "chrome", "chromium" (what was actually launched)
    "profile_path": None,
    "is_temp_profile": True,
    "bookmarks_set": None,
}

def display_banner():
    """Displays the Guardian Spy banner using Rich."""
    banner_text = Text.from_markup(f"""
[bold cyan]
        .--""--.
       /        \\
      |  ______  |
      | |[orange1]  GS  [/orange1]| |  GS for Guardian Spy
      | |______| |
       \\  ----  /
        `------'
[/bold cyan]
      [bold green]{__app_name__}[/bold green]
    [italic]OPSEC Session Assistant[/italic]
    Version: [yellow]{__version__}[/yellow]
    """)
    console.print(Panel(banner_text, title="[bold magenta]Guardian Spy[/bold magenta]", expand=False, border_style="blue"))

def initial_checks():
    """Performs initial network and environment checks using Rich."""
    console.print("\n[bold blue][+] Performing initial OPSEC checks...[/bold blue]")
    
    with console.status("[spinner.dots] Checking network configuration...", spinner_style="blue"):
        public_ip, ip_info = network_checker.get_public_ip_info(console=console) # Pass console
        time.sleep(0.2) # Simulate work if needed, or remove if checks are fast

    if public_ip:
        ip_display = Text(f"  [*] Your public IP: [bold green]{public_ip}[/bold green]")
        if ip_info and ip_info.get("country"): # Check if ip_info is not None and has country
            ip_display.append(f"\n      Location: [yellow]{ip_info.get('city', 'N/A')}, {ip_info.get('region', 'N/A')}, {ip_info.get('country', 'N/A')}[/yellow]")
            ip_display.append(f"\n      ISP: [yellow]{ip_info.get('isp', 'N/A')}[/yellow]") # Changed from 'org' to 'isp' as per ip-api.com typical field
        else:
            ip_display.append("\n      [dim]Could not retrieve detailed IP geolocation.[/dim]")
        console.print(Panel(ip_display, title="[bold]Public IP[/bold]", expand=False, border_style="green"))
    else:
        console.print(Panel("[bold red]  [!] Could not retrieve public IP address.[/bold red]", title="[bold]Public IP[/bold]", expand=False, border_style="red"))

    with console.status("[spinner.dots] Checking DNS servers...", spinner_style="blue"):
        dns_servers = network_checker.get_dns_servers(console=console) # Pass console
        time.sleep(0.2)

    if dns_servers:
        dns_text = Text("  [*] System DNS Servers:\n")
        for server in dns_servers:
            dns_text.append(f"      - [cyan]{server}[/cyan]\n")
        # Remove trailing newline if any
        if dns_text.plain.endswith("\n"):
            dns_text.truncate(len(dns_text.plain)-1)
        console.print(Panel(dns_text, title="[bold]DNS Servers[/bold]", expand=False, border_style="cyan"))
    else:
        console.print(Panel("[bold red]  [!] Could not retrieve system DNS servers.[/bold red]", title="[bold]DNS Servers[/bold]", expand=False, border_style="red"))

def select_browser_interactive(detected_browsers):
    """Allows user to select a browser using Rich Prompt, showing only detected ones."""
    choices = []
    if detected_browsers.get("firefox"):
        choices.append("firefox")
    if detected_browsers.get("chrome"): # This key means Google Chrome was found
        choices.append("chrome")
    if detected_browsers.get("chromium") and not detected_browsers.get("chrome"): # Only add chromium if chrome wasn't an option
        choices.append("chromium")

    if not choices:
        console.print("[bold red]No supported browsers were detected by the setup check.[/bold red]")
        console.print("[yellow]Please ensure Firefox, Google Chrome, or Chromium is installed and accessible.[/yellow]")
        return None

    # Set a sensible default
    default_choice = "firefox" if "firefox" in choices else choices[0] if choices else None

    if len(choices) == 1:
        console.print(f"[yellow]Only one browser type detected: [bold]{choices[0]}[/bold]. Selecting it automatically.[/yellow]")
        return choices[0]
        
    choice = Prompt.ask(
        Text.from_markup("[bold gold1]Select browser to use for this session[/bold gold1]"),
        choices=choices,
        default=default_choice,
        console=console
    )
    return choice.lower()


def start():
    """Main function to start the Guardian Spy CLI."""
    display_banner()

    parser = argparse.ArgumentParser(
        description=f"{__app_name__} - OSINT Session Guardian.",
        formatter_class=argparse.RawTextHelpFormatter 
    )
    parser.add_argument("--browser", choices=['firefox', 'chrome', 'chromium'], help="Specify browser to use (firefox, chrome, or chromium).")
    parser.add_argument("--quick", action="store_true", help="Quick start with default settings (not fully implemented yet).")
    parser.add_argument(
        "--check-setup",
        action="store_true",
        help="Perform a setup check (e.g., detect browsers, network) and exit."
    )
    args = parser.parse_args()

    # Perform pre-flight checks for browser executables first
    # This returns a dict like {'firefox': '/path/to/ff', 'chrome': '/path/to/chrome'}
    detected_browser_paths = utils.check_browser_executables(console=console if args.check_setup else None)

    if args.check_setup:
        # Banner was already displayed
        console.print("\n[bold underline]Guardian Spy Setup Check[/bold underline]")
        if not detected_browser_paths: # Check if any browser was found by check_browser_executables
             console.print("[yellow]Browser check was run, but no browsers were found. Network checks will proceed.[/yellow]")
        initial_checks() 
        console.print("\n[green]Setup check complete.[/green]")
        sys.exit(0)

    if args.quick:
        console.print("[yellow]Quick mode selected (not fully implemented yet). Using defaults...[/yellow]")
        # For quick mode, try to pick a detected browser or default to firefox
        if args.browser and detected_browser_paths.get(args.browser):
            SESSION_CONFIG["browser_selected"] = args.browser
        elif detected_browser_paths.get("firefox"):
            SESSION_CONFIG["browser_selected"] = "firefox"
        elif detected_browser_paths.get("chrome"):
            SESSION_CONFIG["browser_selected"] = "chrome"
        elif detected_browser_paths.get("chromium"):
            SESSION_CONFIG["browser_selected"] = "chromium"
        else:
            console.print("[bold red]No suitable browser found for quick mode. Please run interactively or check setup.[/bold red]")
            sys.exit(1)
    else:
        initial_checks() # Regular initial checks
        # For interactive mode, let user choose from detected browsers
        SESSION_CONFIG["browser_selected"] = args.browser if args.browser and detected_browser_paths.get(args.browser) else select_browser_interactive(detected_browser_paths)
        if not SESSION_CONFIG["browser_selected"]:
            console.print("[bold red]No browser selected or available. Exiting.[/bold red]")
            sys.exit(1)


    console.print(f"\n[bold blue][+] Preparing [magenta]{SESSION_CONFIG['browser_selected']}[/magenta] session...[/bold blue]")

    profile_type = "temp"
    profile_name_prefix = "gs_temp_profile"
    
    profile_path = None
    with console.status(f"[spinner.dots] Creating temporary profile for {SESSION_CONFIG['browser_selected']}...", spinner_style="blue"):
        profile_path = browser_manager.create_profile(
            browser_type=SESSION_CONFIG['browser_selected'], # Pass the user's choice
            profile_name_prefix=profile_name_prefix,
            console=console 
        )
        time.sleep(0.2) 

    if not profile_path:
        console.print(f"[bold red][!] Failed to create browser profile for {SESSION_CONFIG['browser_selected']}. Exiting.[/bold red]")
        sys.exit(1)
    
    SESSION_CONFIG["profile_path"] = profile_path
    console.print(f"  [green][*] Temporary profile created at: [cyan]{profile_path}[/cyan][/green]")

    console.print(f"\n[bold blue][+] Launching [magenta]{SESSION_CONFIG['browser_selected']}[/magenta] with the new profile...[/bold blue]")
    console.print("    [italic]Please close the browser window when your session is complete.[/italic]")
    console.print("    [italic]Guardian Spy will then clean up the temporary profile.[/italic]")
    
    browser_process = None
    # browser_manager.launch_browser_with_profile will determine the actual type (chrome vs chromium)
    with console.status(f"[spinner.dots] Waiting for {SESSION_CONFIG['browser_selected']} to launch...", spinner_style="blue"):
        browser_process = browser_manager.launch_browser_with_profile(
            browser_type_requested=SESSION_CONFIG['browser_selected'], # Pass the user's choice
            profile_path=profile_path,
            console=console 
        )
        if browser_process: time.sleep(1) # Give a sec for window to appear

    if browser_process:
        # Update actual browser type if launch_browser_with_profile modified it (e.g. chose chromium for 'chrome' request)
        # This requires launch_browser_with_profile to potentially return the actual_browser_type or for SESSION_CONFIG to be updated within it.
        # For now, we assume browser_selected is close enough for display messages.
        actual_launched_browser_name = SESSION_CONFIG['browser_selected'] # Simple assumption for now

        console.print(f"  [green][*] [magenta]{actual_launched_browser_name.capitalize()}[/magenta] launched. Waiting for it to close...[/green]")
        try:
            browser_process.wait() 
            console.print(f"\n[green][+] Browser session for [magenta]{actual_launched_browser_name.capitalize()}[/magenta] ended.[/green]")
        except KeyboardInterrupt:
            console.print(f"\n[yellow][!] Browser session interrupted by user. Terminating browser and cleaning up...[/yellow]")
            browser_process.terminate()
            try:
                browser_process.wait(timeout=5)
            except subprocess.TimeoutExpired: # Rich uses this internally
                console.print(f"[red][!] Browser process for {actual_launched_browser_name.capitalize()} did not terminate gracefully. It might need manual closing.[/red]")
            # Let the main KeyboardInterrupt handler in __main__ do the final cleanup.
            raise # Re-raise to trigger cleanup in __main__
    else:
        console.print(f"[bold red][!] Failed to launch {SESSION_CONFIG['browser_selected']}.[/bold red]")

    if SESSION_CONFIG["is_temp_profile"] and SESSION_CONFIG["profile_path"]:
        console.print(f"\n[bold blue][+] Cleaning up temporary profile: [cyan]{SESSION_CONFIG['profile_path']}[/cyan][/bold blue]")
        with console.status(f"[spinner.dots] Removing profile...", spinner_style="blue"):
            removed_ok = browser_manager.remove_profile(SESSION_CONFIG["profile_path"], console=console)
            time.sleep(0.2)

        if removed_ok:
            console.print("  [green][*] Temporary profile successfully removed.[/green]")
        else:
            console.print(f"  [bold red][!] Failed to remove temporary profile: [cyan]{SESSION_CONFIG['profile_path']}[/cyan][/bold red]")
            console.print("      [yellow]You may need to remove it manually.[/yellow]")
    
    # console.print("\n[bold green]Guardian Spy session finished.[/bold green]") # Moved to finally block in guardian_spy.py