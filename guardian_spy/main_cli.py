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

# guardian_spy/main_cli.py
import argparse
import sys
import time 
import subprocess 
import os 

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm 
from rich.table import Table

from . import browser_manager
from . import network_checker
from . import utils 
from . import __version__, __app_name__ 

console = Console()

SESSION_CONFIG = {
    "browser_selected": None, 
    "browser_actual_type": None, 
    "profile_path": None,
    "is_temp_profile": True,
    "bookmarks_set": None, # Will store "default" or None
}

# --- (display_banner, initial_checks, select_browser_interactive - sin cambios) ---
def display_banner():
    """Displays the Guardian Spy banner using Rich."""
    # Tu nuevo y flamante banner ASCII irá aquí
    # Por ahora, mantenemos el placeholder
    banner_text_content = SESSION_CONFIG.get("custom_banner", f"""
[bold cyan]
##########################################################################################################################################
#                                                                                                                                        #
#       ::::::::  :::    :::     :::     :::::::::  ::::::::: :::::::::::     :::     ::::    :::         ::::::::  :::::::::  :::   ::: #
#     :+:    :+: :+:    :+:   :+: :+:   :+:    :+: :+:    :+:    :+:       :+: :+:   :+:+:   :+:        :+:    :+: :+:    :+: :+:   :+:  #
#    +:+        +:+    +:+  +:+   +:+  +:+    +:+ +:+    +:+    +:+      +:+   +:+  :+:+:+  +:+        +:+        +:+    +:+  +:+ +:+    #
#   :#:        +#+    +:+ +#++:++#++: +#++:++#:  +#+    +:+    +#+     +#++:++#++: +#+ +:+ +#+        +#++:++#++ +#++:++#+    +#++:      #
#  +#+   +#+# +#+    +#+ +#+     +#+ +#+    +#+ +#+    +#+    +#+     +#+     +#+ +#+  +#+#+#               +#+ +#+           +#+        #
# #+#    #+# #+#    #+# #+#     #+# #+#    #+# #+#    #+#    #+#     #+#     #+# #+#   #+#+#        #+#    #+# #+#           #+#         #
# ########   ########  ###     ### ###    ### ######### ########### ###     ### ###    ####         ########  ###           ###          #
#                                                                                                                                        #
##########################################################################################################################################
[/bold cyan]
      [bold green]{__app_name__}[/bold green]
    [italic]OPSEC Session Assistant[/italic]
    Version: [yellow]{__version__}[/yellow]
    """)
    
    banner_text = Text.from_markup(banner_text_content)
    console.print(Panel(banner_text, title="[bold magenta]Guardian Spy[/bold magenta]", expand=False, border_style="blue"))

def initial_checks():
    """Performs initial network and environment checks using Rich."""
    console.print("\n[bold blue][+] Performing initial OPSEC checks...[/bold blue]")
    
    public_ip = None 
    ip_info = None   

    with console.status("[spinner.dots] Checking network configuration...", spinner_style="blue"):
        try:
            public_ip, ip_info = network_checker.get_public_ip_info(console=console)
        except Exception as e:
            console.log(f"[bold red]Error during get_public_ip_info: {e}[/bold red]")
        time.sleep(0.2) 

    if public_ip:
        ip_display = Text(f"  [*] Your public IP: [bold green]{public_ip}[/bold green]")
        if ip_info and ip_info.get("country"): 
            ip_display.append(f"\n      Location: [yellow]{ip_info.get('city', 'N/A')}, {ip_info.get('region', 'N/A')}, {ip_info.get('country', 'N/A')}[/yellow]")
            ip_display.append(f"\n      ISP: [yellow]{ip_info.get('isp', 'N/A')}[/yellow]")
        else:
            ip_display.append("\n      [dim]Could not retrieve detailed IP geolocation or ip_info is empty/None.[/dim]")
        console.print(Panel(ip_display, title="[bold]Public IP[/bold]", expand=False, border_style="green"))
    else:
        console.print(Panel("[bold red]  [!] Could not retrieve public IP address.[/bold red]", title="[bold]Public IP[/bold]", expand=False, border_style="red"))

    dns_servers = [] 
    with console.status("[spinner.dots] Checking DNS servers...", spinner_style="blue"):
        try:
            dns_servers = network_checker.get_dns_servers(console=console)
        except Exception as e:
            console.log(f"[bold red]Error during get_dns_servers: {e}[/bold red]")
        time.sleep(0.2)

    if dns_servers:
        dns_text = Text("  [*] System DNS Servers:\n")
        for server in dns_servers:
            dns_text.append(f"      - [cyan]{server}[/cyan]\n")
        if dns_text.plain.endswith("\n"):
            dns_text.truncate(len(dns_text.plain)-1)
        console.print(Panel(dns_text, title="[bold]DNS Servers[/bold]", expand=False, border_style="cyan"))
    else:
        console.print(Panel("[bold red]  [!] Could not retrieve system DNS servers.[/bold red]", title="[bold]DNS Servers[/bold]", expand=False, border_style="red"))

def select_browser_interactive(detected_browsers_paths):
    choices = []
    if "firefox" in detected_browsers_paths:
        choices.append("firefox")
    if "chrome" in detected_browsers_paths: 
        choices.append("chrome")
    if "chromium" in detected_browsers_paths and "chrome" not in detected_browsers_paths:
        choices.append("chromium")

    if not choices:
        console.print("[bold red]No supported browsers were detected by the setup check.[/bold red]")
        console.print("[yellow]Please ensure Firefox, Google Chrome, or Chromium is installed and accessible.[/yellow]")
        return None

    default_choice = "firefox" if "firefox" in choices else choices[0] if choices else None

    if len(choices) == 1:
        return choices[0]
        
    choice = Prompt.ask(
        Text.from_markup("[bold gold1]Select browser to use for this session[/bold gold1]"),
        choices=choices,
        default=default_choice,
        console=console
    )
    return choice.lower()

# --- (start - MODIFICADA para bookmarks) ---
def start():
    # Placeholder for your custom banner if you create one as a multiline string
    # custom_ascii_banner = """
    # Your ASCII art here
    # """
    # SESSION_CONFIG["custom_banner"] = custom_ascii_banner 
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
    parser.add_argument(
        "--no-bookmarks",
        action="store_true",
        help="Do not attempt to load any default bookmarks into the new profile." # NUEVO ARGUMENTO
    )
    args = parser.parse_args()

    console_for_browser_check = console if args.check_setup else None
    detected_browser_paths = utils.check_browser_executables(console=console_for_browser_check)

    if args.check_setup:
        console.print("\n[bold underline]Guardian Spy Setup Check[/bold underline]")
        initial_checks() 
        console.print("\n[green]Setup check complete.[/green]")
        sys.exit(0)

    if not detected_browser_paths:
        console.print("[bold red]No browsers were detected. Guardian Spy cannot proceed.[/bold red]")
        console.print("[yellow]Try running with '--check-setup' for more details or ensure a supported browser is installed.[/yellow]")
        sys.exit(1)

    load_default_bookmarks = False # NUEVA VARIABLE

    if args.quick:
        console.print("[yellow]Quick mode selected (not fully implemented yet). Using defaults...[/yellow]")
        if args.browser and args.browser in detected_browser_paths:
            SESSION_CONFIG["browser_selected"] = args.browser
        elif "firefox" in detected_browser_paths:
            SESSION_CONFIG["browser_selected"] = "firefox"
        # ... (más lógica para quick mode browser selection) ...
        else:
            console.print("[bold red]No suitable browser found for quick mode.[/bold red]")
            sys.exit(1)
        load_default_bookmarks = not args.no_bookmarks # En quick mode, carga bookmarks a menos que se especifique lo contrario

    else: # Modo Interactivo
        initial_checks() 
        SESSION_CONFIG["browser_selected"] = args.browser if args.browser and args.browser in detected_browser_paths else select_browser_interactive(detected_browser_paths)
        if not SESSION_CONFIG["browser_selected"]:
            console.print("[bold red]No browser selected or available. Exiting.[/bold red]")
            sys.exit(1)
        
        if not args.no_bookmarks: # Si no se pasó --no-bookmarks
            load_default_bookmarks = Confirm.ask(
                Text.from_markup("[bold gold1]Load default OSINT bookmarks into the new session?[/bold gold1]"), 
                default=True, 
                console=console
            )
    
    if load_default_bookmarks:
        SESSION_CONFIG["bookmarks_set"] = "default" # Usaremos "default" como nombre de la plantilla
    else:
        SESSION_CONFIG["bookmarks_set"] = None


    console.print(f"\n[bold blue][+] Preparing [magenta]{SESSION_CONFIG['browser_selected'].capitalize()}[/magenta] session...[/bold blue]")
    if SESSION_CONFIG["bookmarks_set"]:
        console.print(f"  [dim]Will attempt to load '{SESSION_CONFIG['bookmarks_set']}' bookmarks set.[/dim]")

    profile_name_prefix = "gs_temp_profile"
    
    profile_path = None
    with console.status(f"[spinner.dots] Creating temporary profile for {SESSION_CONFIG['browser_selected'].capitalize()}...", spinner_style="blue"):
        profile_path = browser_manager.create_profile(
            browser_type=SESSION_CONFIG['browser_selected'], 
            profile_name_prefix=profile_name_prefix,
            bookmarks_template_name=SESSION_CONFIG["bookmarks_set"], # Pasar el nombre de la plantilla
            console=console 
        )
        time.sleep(0.2) 

    if not profile_path:
        console.print(f"[bold red][!] Failed to create browser profile for {SESSION_CONFIG['browser_selected'].capitalize()}. Exiting.[/bold red]")
        sys.exit(1)
    
    SESSION_CONFIG["profile_path"] = profile_path
    SESSION_CONFIG["is_temp_profile"] = True 
    console.print(f"  [green][*] Temporary profile created at: [cyan]{profile_path}[/cyan][/green]")

    console.print(f"\n[bold blue][+] Launching [magenta]{SESSION_CONFIG['browser_selected'].capitalize()}[/magenta] with the new profile...[/bold blue]")
    console.print("    [italic]Please close the browser window when your session is complete.[/italic]")
    console.print("    [italic]Guardian Spy will then clean up the temporary profile.[/italic]")
    
    browser_process = None
    with console.status(f"[spinner.dots] Waiting for {SESSION_CONFIG['browser_selected'].capitalize()} to launch...", spinner_style="blue"):
        browser_process = browser_manager.launch_browser_with_profile(
            browser_type_requested=SESSION_CONFIG['browser_selected'], 
            profile_path=profile_path,
            console=console 
        )
        if browser_process: time.sleep(1) 

    if browser_process:
        actual_launched_browser_name = SESSION_CONFIG['browser_selected'] 
        console.print(f"  [green][*] [magenta]{actual_launched_browser_name.capitalize()}[/magenta] launched. Waiting for it to close...[/green]")
        try:
            browser_process.wait() 
            console.print(f"\n[green][+] Browser session for [magenta]{actual_launched_browser_name.capitalize()}[/magenta] ended.[/green]")
        except KeyboardInterrupt:
            console.print(f"\n[yellow][!] Browser session interrupted by user. Terminating browser and cleaning up...[/yellow]")
            browser_process.terminate() 
            try:
                browser_process.wait(timeout=5) 
            except subprocess.TimeoutExpired: 
                console.print(f"[red][!] Browser process for {actual_launched_browser_name.capitalize()} did not terminate gracefully.[/red]")
            except Exception as e_wait: 
                console.log(f"[dim]Exception during browser_process.wait after terminate: {e_wait}[/dim]")
            console.print("[yellow]Proceeding to cleanup profile (if applicable)...[/yellow]")
        finally: 
            if SESSION_CONFIG["is_temp_profile"] and SESSION_CONFIG["profile_path"] and os.path.exists(SESSION_CONFIG["profile_path"]):
                console.print(f"\n[bold blue][+] Cleaning up temporary profile: [cyan]{SESSION_CONFIG['profile_path']}[/cyan][/bold blue]")
                with console.status(f"[spinner.dots] Removing profile...", spinner_style="blue"):
                    removed_ok = browser_manager.remove_profile(SESSION_CONFIG["profile_path"], console=console)
                    time.sleep(0.2)
                if removed_ok:
                    console.print("  [green][*] Temporary profile successfully removed.[/green]")
                else:
                    console.print(f"  [bold red][!] Failed to remove temporary profile.[/bold red]")
            elif SESSION_CONFIG["profile_path"] and not os.path.exists(SESSION_CONFIG["profile_path"]):
                 console.print(f"\n[dim]Temporary profile {SESSION_CONFIG['profile_path']} seems to have been removed already or path is invalid.[/dim]")
    else: 
        console.print(f"[bold red][!] Failed to launch {SESSION_CONFIG['browser_selected'].capitalize()}.[/bold red]")
        if SESSION_CONFIG["is_temp_profile"] and SESSION_CONFIG["profile_path"] and os.path.exists(SESSION_CONFIG["profile_path"]):
            console.print(f"[yellow]Attempting to clean up profile created at {SESSION_CONFIG['profile_path']} due to launch failure...[/yellow]")
            if browser_manager.remove_profile(SESSION_CONFIG["profile_path"], console=console):
                console.print("  [green][*] Profile successfully removed.[/green]")
            else:
                console.print("  [bold red][!] Failed to remove the profile.[/bold red]")