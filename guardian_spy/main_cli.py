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

console = Console(force_terminal=True)

SESSION_CONFIG = {
    "browser_selected": None,
    "browser_actual_type": None,
    "profile_path": None,
    "is_temp_profile": True,
    "bookmarks_set": None,
}

def display_banner():
    banner_art_string = """[bold cyan]
################################################################################################
#                                                                                              #
#  ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗    ███████╗██████╗ ██╗   ██╗ #
# ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║    ██╔════╝██╔══██╗╚██╗ ██╔╝ #
# ██║  ███╗██║   ██║███████║██████╔╝██║  ██║██║███████║██╔██╗ ██║    ███████╗██████╔╝ ╚████╔╝  #
# ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██║██╔══██║██║╚██╗██║    ╚════██║██╔═══╝   ╚██╔╝   #
# ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║    ███████║██║        ██║    #
#  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝    ╚══════╝╚═╝        ╚═╝    #
#                                                                                              #
################################################################################################[/bold cyan]"""
    
    console.print(Text.from_markup(banner_art_string))
    
    app_info_text = Text.from_markup(f"""[bold green]{__app_name__}[/bold green]
[italic]OPSEC Session Assistant[/italic]
Version: [yellow]{__version__}[/yellow]""")
    console.print(app_info_text, justify="center")
    console.line()

def initial_checks():
    """Performs initial network and environment checks using Rich."""
    # Comentamos o eliminamos las líneas de depuración de Rich si ya no las necesitamos inmediatamente
    # if console:
    #     console.rule("[bold]Rich Console Debug Info[/bold]")
    #     # ... (líneas de print de debug) ...
    #     console.rule()

    console.print("\n[bold blue][+] Performing initial OPSEC checks...[/bold blue]")
    
    public_ip = None
    ip_info = None

    with console.status("[spinner.dots] Checking network configuration...", spinner_style="blue"): # spinner_style usa colores de Rich
        try:
            public_ip, ip_info = network_checker.get_public_ip_info(console=console)
        except Exception as e:
            console.log(f"[bold red]Error during get_public_ip_info: {e}[/bold red]")
        time.sleep(0.2)

    if public_ip:
        ip_display = Text()
        ip_display.append("  [*] Your public IP: ", style="default") # Texto normal
        ip_display.append(public_ip, style="bold green") # Verde y negrita para la IP

        if ip_info and ip_info.get("country"):
            location_str = f"{ip_info.get('city', 'N/A')}, {ip_info.get('region', 'N/A')}, {ip_info.get('country', 'N/A')}"
            isp_str = ip_info.get('isp', 'N/A')
            
            ip_display.append("\n      Location: ", style="default")
            ip_display.append(location_str, style="yellow") # Amarillo para localización
            
            ip_display.append("\n      ISP: ", style="default")
            ip_display.append(isp_str, style="yellow") # Amarillo para ISP
        else:
            # 'dim' debería funcionar bien como un gris/atenuado
            ip_display.append("\n      [dim]Could not retrieve detailed IP geolocation or ip_info is empty/None.[/dim]", style="default") 
        
        # El título del panel y el borde ya usan colores que parecían funcionar
        console.print(Panel(ip_display, title=Text("Public IP", style="bold white"), expand=False, border_style="green"))
    else:
        console.print(Panel(Text("  [!] Could not retrieve public IP address.", style="bold red"), title=Text("Public IP", style="bold white"), expand=False, border_style="red"))

    dns_servers = []
    with console.status("[spinner.dots] Checking DNS servers...", spinner_style="blue"):
        try:
            dns_servers = network_checker.get_dns_servers(console=console)
        except Exception as e:
            console.log(f"[bold red]Error during get_dns_servers: {e}[/bold red]")
        time.sleep(0.2)

    if dns_servers:
        dns_text = Text("  [*] System DNS Servers:\n", style="default")
        for server in dns_servers:
            dns_text.append(f"      - ", style="default")
            dns_text.append(server, style="cyan") # Cyan para los servidores DNS
            dns_text.append("\n", style="default")
            
        if dns_text.plain.endswith("\n"):
            dns_text.truncate(len(dns_text.plain)-1)
            
        console.print(Panel(dns_text, title=Text("DNS Servers", style="bold white"), expand=False, border_style="cyan"))
    else:
        console.print(Panel(Text("  [!] Could not retrieve system DNS servers.", style="bold red"), title=Text("DNS Servers", style="bold white"), expand=False, border_style="red"))

# ... (resto de main_cli.py sin cambios significativos para este problema) ...
# (select_browser_interactive, start)
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

def start():
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
        help="Do not attempt to load any default bookmarks into the new profile."
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

    load_default_bookmarks = False

    if args.quick:
        console.print("[yellow]Quick mode selected (not fully implemented yet). Using defaults...[/yellow]")
        if args.browser and args.browser in detected_browser_paths:
            SESSION_CONFIG["browser_selected"] = args.browser
        elif "firefox" in detected_browser_paths:
            SESSION_CONFIG["browser_selected"] = "firefox"
        elif "chrome" in detected_browser_paths: # Prioritize chrome if available
             SESSION_CONFIG["browser_selected"] = "chrome"
        elif "chromium" in detected_browser_paths:
             SESSION_CONFIG["browser_selected"] = "chromium"
        else:
            console.print("[bold red]No suitable browser found for quick mode.[/bold red]")
            sys.exit(1)
        load_default_bookmarks = not args.no_bookmarks

    else:
        initial_checks()
        SESSION_CONFIG["browser_selected"] = args.browser if args.browser and args.browser in detected_browser_paths else select_browser_interactive(detected_browser_paths)
        if not SESSION_CONFIG["browser_selected"]:
            console.print("[bold red]No browser selected or available. Exiting.[/bold red]")
            sys.exit(1)
        
        if not args.no_bookmarks:
            load_default_bookmarks = Confirm.ask(
                Text.from_markup("[bold gold1]Load default OSINT bookmarks into the new session?[/bold gold1]"), 
                default=True,
                console=console
            )
    
    if load_default_bookmarks:
        SESSION_CONFIG["bookmarks_set"] = "default"
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
            bookmarks_template_name=SESSION_CONFIG["bookmarks_set"],
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