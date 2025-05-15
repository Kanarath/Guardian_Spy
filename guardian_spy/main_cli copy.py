# guardian_spy/main_cli.py
# ... (imports y configuraciones iniciales como antes) ...
import argparse
import sys
import time 
import subprocess 
import os 
from datetime import datetime 

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm, InvalidResponse
from rich.table import Table
from rich.box import ROUNDED, SIMPLE_HEAVY 
from rich.rule import Rule 
# from rich.live import Live # No estamos usando Live aún
from rich.align import Align 

from . import browser_manager
from . import network_checker
from . import utils 
from . import config_manager 
from . import __version__, __app_name__ 
from guardian_spy import DEBUG_MODE

console = Console() 

CURRENT_SESSION_SETUP = {
    "profile_type": "Temporary", 
    "gs_profile_name": None,     
    "browser_selected": None,    
    "bookmarks_set": None,       
    "network_checks_status": "Pending", 
    "browser_profile_on_disk_path": None, 
}

# --- Funciones de Display (banner, panel de estado, opciones de menú) ---
# (Estas se mantienen sin cambios significativos)
def display_banner_and_app_info():
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

def display_current_session_status_panel():
    status_table = Table(box=None, show_header=False, padding=(0, 1, 0, 1))
    status_table.add_column("Setting", style="bold dim blue")
    status_table.add_column("Value", style="bright_white")
    profile_type_display = CURRENT_SESSION_SETUP["profile_type"]
    if CURRENT_SESSION_SETUP["profile_type"] == "Persistent" and CURRENT_SESSION_SETUP["gs_profile_name"]:
        profile_type_display += f": [cyan]{CURRENT_SESSION_SETUP['gs_profile_name']}[/cyan]"
    elif CURRENT_SESSION_SETUP["profile_type"] == "Persistent":
         profile_type_display += ": [yellow](Not Loaded)[/yellow]"
    status_table.add_row("Profile Type:", profile_type_display)
    status_table.add_row("Browser:", f"[magenta]{CURRENT_SESSION_SETUP['browser_selected'] or '[Not Selected]'}[/magenta]")
    status_table.add_row("Bookmarks Set:", f"[yellow]{CURRENT_SESSION_SETUP['bookmarks_set'] or 'None'}[/yellow]")
    net_status_color = "yellow" 
    if "OK" in CURRENT_SESSION_SETUP["network_checks_status"]: net_status_color = "green"
    elif "Error" in CURRENT_SESSION_SETUP["network_checks_status"] or "Leak" in CURRENT_SESSION_SETUP["network_checks_status"]: net_status_color = "red"
    status_table.add_row("Network Checks:", f"[{net_status_color}]{CURRENT_SESSION_SETUP['network_checks_status']}[/{net_status_color}]")
    console.print(Panel(Align.center(status_table), title="[bold gold1]Current Session Setup[/bold gold1]", border_style="blue", expand=False))
    console.line()

def display_main_menu_options():
    console.print(Rule("[bold_yellow]Main Menu[/bold_yellow]", style="yellow"))
    menu_options = {
        "1": "Select/Toggle Profile Type",
        "2": "Select Browser",
        "3": "Select Bookmarks Set",
        "4": "Perform Network Checks",
        "5": "Launch Prepared Session",
        "6": "Manage Persistent Profiles",
        "7": "About / Help",
        "8": "Quit Guardian Spy"
    }
    for key, value in menu_options.items():
        console.print(f"  [bold cyan]{key}[/bold cyan]. {value}")
    console.line()

# --- Funciones Handler de las "Vistas" del Menú ---
# Cada función que representa una interacción/vista ahora limpia la pantalla,
# muestra su contenido, y si es necesario, pausa antes de retornar.

def view_toggle_profile_type(detected_browser_paths):
    console.clear(); display_banner_and_app_info()
    display_current_session_status_panel() # Mostrar estado actual antes de preguntar
    console.print(Rule("[bold green]Profile Type Selection[/bold green]", style="green"))

    previous_profile_type = CURRENT_SESSION_SETUP["profile_type"]
    if previous_profile_type == "Temporary":
        if Confirm.ask("Current is [bold]Temporary[/bold]. Switch to [bold]Persistent Profile[/bold] setup?", default=True, console=console):
            CURRENT_SESSION_SETUP["profile_type"] = "Persistent"
            # Resetear campos para el nuevo tipo de perfil
            CURRENT_SESSION_SETUP["gs_profile_name"] = None 
            CURRENT_SESSION_SETUP["browser_selected"] = None 
            CURRENT_SESSION_SETUP["bookmarks_set"] = None
            CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = None
            console.print("[green]Mode set to Persistent.[/green]")
            # Opcional: inmediatamente ofrecer cargar un perfil
            if Confirm.ask("Load an existing persistent profile now?", default=True, console=console):
                # Esta llamada es una "sub-vista"
                handle_load_persistent_profile_menu_action(detected_browser_paths, auto_load_to_session=True, called_from_main_menu=True)
            else: # Si no carga, necesita "Press Enter" para ver el mensaje de "Mode set to Persistent"
                 Prompt.ask("Press Enter to return to Main Menu...", console=console, default="", show_default=False)

        # else: No hacer nada si no cambia, vuelve al menú principal
    else: # Actualmente es Persistente
        if Confirm.ask(f"Current is [bold]Persistent ([cyan]{CURRENT_SESSION_SETUP['gs_profile_name'] or 'Not Loaded'}[/cyan])[/bold]. Switch to [bold]Temporary Profile[/bold] setup?", default=True, console=console):
            CURRENT_SESSION_SETUP["profile_type"] = "Temporary"
            CURRENT_SESSION_SETUP["gs_profile_name"] = None
            CURRENT_SESSION_SETUP["browser_selected"] = None 
            CURRENT_SESSION_SETUP["bookmarks_set"] = None
            CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = None
            console.print("[green]Mode set to Temporary.[/green]")
            Prompt.ask("Press Enter to return to Main Menu...", console=console, default="", show_default=False)
        # else: No hacer nada

def view_select_browser(detected_browser_paths):
    console.clear(); display_banner_and_app_info()
    display_current_session_status_panel()
    console.print(Rule("[bold green]Select Browser[/bold green]", style="green"))

    if not detected_browser_paths:
        console.print("[red]No browsers detected on your system.[/red]")
        Prompt.ask("Press Enter...", console=console, default="", show_default=False); return 

    if CURRENT_SESSION_SETUP["profile_type"] == "Persistent" and CURRENT_SESSION_SETUP["gs_profile_name"]:
        console.print(f"[yellow]Info: Current setup is based on persistent profile '[cyan]{CURRENT_SESSION_SETUP['gs_profile_name']}[/cyan]'.[/yellow]")
        console.print("[yellow]Changing browser will make this a [bold]new temporary setup[/bold] based on it.[/yellow]")
        if not Confirm.ask("Proceed?", default=False, console=console):
            return 
        CURRENT_SESSION_SETUP["profile_type"] = "Temporary" 
        CURRENT_SESSION_SETUP["gs_profile_name"] = f"(Modified: {CURRENT_SESSION_SETUP['gs_profile_name'] or 'Unsaved'})" 
        CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = None

    chosen_browser = select_browser_interactive(detected_browser_paths, prompt_message="Choose browser for current setup")
    if chosen_browser:
        CURRENT_SESSION_SETUP["browser_selected"] = chosen_browser
    # No "Press Enter", el cambio se ve en el panel de estado del menú principal

def view_select_bookmarks():
    console.clear(); display_banner_and_app_info()
    display_current_session_status_panel()
    console.print(Rule("[bold green]Select Bookmarks Set[/bold green]", style="green"))

    available_sets = { 
        "1": ("None (No bookmarks)", None),
        "2": ("Default OSINT (recommended)", "default")
    }
    console.print("Available bookmark sets:")
    for key, (desc, _) in available_sets.items():
        console.print(f"  [bold cyan]{key}[/bold cyan]. {desc}")
    
    choice_keys = list(available_sets.keys())
    current_bm_val = CURRENT_SESSION_SETUP["bookmarks_set"]
    default_key_choice = next((k for k, (_,v) in available_sets.items() if v == current_bm_val), choice_keys[0] if choice_keys else None)

    if not default_key_choice: console.print("[red]No bookmark sets defined.[/red]"); time.sleep(1); return

    chosen_key = Prompt.ask("Select a set (number):", choices=choice_keys, default=default_key_choice, console=console).upper()
    _, internal_value = available_sets.get(chosen_key, (None,None))
    CURRENT_SESSION_SETUP["bookmarks_set"] = internal_value
    # No "Press Enter", el cambio se ve en el panel de estado.

def view_perform_network_checks():
    console.clear(); display_banner_and_app_info()
    # Mostrar el panel de estado ANTES de los chequeos, para que se vea "Checking..."
    CURRENT_SESSION_SETUP["network_checks_status"] = "[yellow]Performing checks...[/yellow]"
    display_current_session_status_panel()
    console.print(Rule("[bold green]Network & Browser Checks[/bold green]", style="green"))

    utils.check_browser_executables(console=console) # Muestra detección de navegadores
    
    # initial_checks_display() hace los chequeos de red y muestra los paneles
    public_ip_val, dns_servers_val = initial_checks_display() 

    status_summary_parts = []
    if public_ip_val: status_summary_parts.append(f"IP: [green]{public_ip_val}[/green]")
    else: status_summary_parts.append("[red]IP: Error[/red]")
    if dns_servers_val: status_summary_parts.append(f"DNS: [green]OK ({len(dns_servers_val)} found)[/green]")
    else: status_summary_parts.append("[red]DNS: Error[/red]")
    CURRENT_SESSION_SETUP["network_checks_status"] = ", ".join(status_summary_parts)
    
    console.print(Rule("Checks Complete", style="blue"))
    Prompt.ask("Press Enter to return to the main menu...", console=console, default="", show_default=False)

def view_launch_prepared_session(detected_browser_paths):
    console.clear(); display_banner_and_app_info()
    display_current_session_status_panel() # Mostrar el estado antes de intentar lanzar
    console.print(Rule("[bold green]Launch Prepared Session[/bold green]", style="green"))

    if not CURRENT_SESSION_SETUP["browser_selected"]:
        if detected_browser_paths: console.print("[yellow]No browser selected. Please select one from the main menu (Option 2).[/yellow]")
        else: console.print("[red]No browsers detected on system. Cannot launch session.[/red]")
        Prompt.ask("Press Enter...", console=console, default="", show_default=False); return

    is_temp = (CURRENT_SESSION_SETUP["profile_type"] == "Temporary")
    browser_choice = CURRENT_SESSION_SETUP["browser_selected"]
    bookmarks_to_load = CURRENT_SESSION_SETUP["bookmarks_set"]
    gs_profile_name_for_disk = None
    if not is_temp and CURRENT_SESSION_SETUP.get("gs_profile_name") and \
       not CURRENT_SESSION_SETUP.get("gs_profile_name","").startswith("(Modified"):
        gs_profile_name_for_disk = CURRENT_SESSION_SETUP.get("gs_profile_name")
    
    actual_browser_profile_path = CURRENT_SESSION_SETUP.get("browser_profile_on_disk_path")
    should_create_browser_dir = False

    if is_temp: should_create_browser_dir = True
    elif gs_profile_name_for_disk: # Es un perfil persistente con nombre
        if not actual_browser_profile_path or not os.path.exists(actual_browser_profile_path):
            should_create_browser_dir = True # El dir del perfil del navegador no existe, hay que crearlo
            base_persistent_dir = config_manager.get_browser_profiles_base_dir()
            actual_browser_profile_path = os.path.join(base_persistent_dir, gs_profile_name_for_disk)
            # No actualizar CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] aquí,
            # se hace después de que create_profile confirme la creación.
    elif not is_temp and not gs_profile_name_for_disk: # Persistente pero sin nombre (ej. modificado)
        console.print("[yellow]Current setup is modified from a persistent profile or is a new unsaved persistent setup. Will create a temporary browser profile directory for this launch.[/yellow]")
        is_temp = True # Forzar temporal para este lanzamiento específico
        should_create_browser_dir = True
    
    if should_create_browser_dir:
        profile_name_for_creation = gs_profile_name_for_disk if not is_temp else None
        prefix_for_creation = "gs_temp_browser_profile" if is_temp else None
        
        with console.status(f"[spinner.dots] Creating browser profile directory...", spinner_style="blue"):
            newly_created_path = browser_manager.create_profile(
                browser_type=browser_choice, profile_custom_name=profile_name_for_creation,
                profile_name_prefix=prefix_for_creation, is_persistent=(not is_temp), 
                bookmarks_template_name=bookmarks_to_load, console=console
            )
        if not newly_created_path:
            console.print(f"[red][!] Failed to create browser profile directory.[/red]"); Prompt.ask("Press Enter..."); return
        actual_browser_profile_path = newly_created_path
        console.print(f"  [green][*] Browser profile directory ensured/created at: [cyan]{actual_browser_profile_path}[/cyan]")
        
        # Actualizar el path en CURRENT_SESSION_SETUP y en config si es un persistente que necesitaba crear su dir
        CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = actual_browser_profile_path
        if not is_temp and gs_profile_name_for_disk:
             profile_data_from_config = config_manager.get_profile_by_name(gs_profile_name_for_disk)
             if profile_data_from_config and profile_data_from_config.get("browser_profile_path") != actual_browser_profile_path:
                profile_data_from_config["browser_profile_path"] = actual_browser_profile_path
                all_profiles = config_manager.load_profiles_data()
                for i, p_conf in enumerate(all_profiles):
                    if p_conf["profile_name"] == gs_profile_name_for_disk: all_profiles[i] = profile_data_from_config; break
                config_manager.save_profiles_data(all_profiles, console=console)
    
    if not actual_browser_profile_path:
        console.print("[red]Error: Cannot determine browser profile path to launch.[/red]"); Prompt.ask("Press Enter..."); return

    start_session_flow(browser_choice, actual_browser_profile_path, is_temp, console) # Esta función tiene su "Press Enter"

    if is_temp: 
        CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = None 
        CURRENT_SESSION_SETUP["browser_selected"] = None
        CURRENT_SESSION_SETUP["bookmarks_set"] = None
        if not (CURRENT_SESSION_SETUP.get("gs_profile_name","").startswith("(Modified")): CURRENT_SESSION_SETUP["gs_profile_name"] = None
        CURRENT_SESSION_SETUP["profile_type"] = "Temporary"
    CURRENT_SESSION_SETUP["network_checks_status"] = "Pending"

def view_manage_persistent_profiles(detected_browser_paths):
    # Esta función tiene su propio bucle y limpieza, solo la llamamos
    manage_persistent_profiles_menu_loop(detected_browser_paths)

def view_show_about_info():
    console.clear(); display_banner_and_app_info()
    # ... (código de show_about_info como estaba, con su "Press Enter" al final) ...
    console.print(Rule("[bold green]About Guardian Spy[/bold green]", style="green"))
    console.print(Panel(Text.from_markup(f"""[bold]{__app_name__} v{__version__}[/bold]
An OPSEC Session Assistant for OSINT practitioners.
(Resto de la info...)"""),title="Information",border_style="blue",padding=(1,2)))
    Prompt.ask("Press Enter to return to the main menu...", console=console, default="", show_default=False)

# --- Bucle Principal del Menú ---
def main_loop(cli_args):
    detected_browser_paths = utils.check_browser_executables(console=None if not DEBUG_MODE else console) 
    if not detected_browser_paths:
        console.clear(); display_banner_and_app_info()
        console.print(Panel(Text.from_markup("[bold red]CRITICAL ERROR: No supported browsers found.[/bold red] Guardian Spy cannot manage browser sessions without a detected browser."),padding=1))
        Prompt.ask("Press Enter to exit.", console=console); return 

    if cli_args: 
        if cli_args.browser and cli_args.browser in detected_browser_paths :
            CURRENT_SESSION_SETUP["browser_selected"] = cli_args.browser
        if cli_args.no_bookmarks: CURRENT_SESSION_SETUP["bookmarks_set"] = None
        elif cli_args.bookmarks: CURRENT_SESSION_SETUP["bookmarks_set"] = cli_args.bookmarks
        else: CURRENT_SESSION_SETUP["bookmarks_set"] = "default"

    while True:
        console.clear() 
        display_banner_and_app_info()
        display_current_session_status_panel()
        display_main_menu_options()

        menu_choices_map = {"1":"T", "2":"B", "3":"K", "4":"C", "5":"L", "6":"M", "7":"A", "8":"Q"}
        try:
            raw_choice = Prompt.ask(Text.from_markup("Enter your choice (number):"), choices=list(menu_choices_map.keys()), show_choices=False, console=console)
            choice_action_key = menu_choices_map.get(raw_choice) 
        except (KeyboardInterrupt, EOFError): choice_action_key = "Q" 
        
        if choice_action_key == "T": view_toggle_profile_type(detected_browser_paths)
        elif choice_action_key == "B": view_select_browser(detected_browser_paths)
        elif choice_action_key == "K": view_select_bookmarks()
        elif choice_action_key == "C": view_perform_network_checks() 
        elif choice_action_key == "L": view_launch_prepared_session(detected_browser_paths) 
        elif choice_action_key == "M": view_manage_persistent_profiles(detected_browser_paths) 
        elif choice_action_key == "A": view_show_about_info() 
        elif choice_action_key == "Q":
            console.clear(); display_banner_and_app_info() # Limpiar para el prompt de salida
            if Confirm.ask("Are you sure you want to quit Guardian Spy?", default=True, console=console):
                console.print(Rule("[bold blue]Exiting Guardian Spy. Stay safe![/bold blue]", style="blue"))
                break 
    
# --- Funciones Auxiliares y de Gestión de Perfiles ---
# (initial_checks_display, select_browser_interactive, start_session_flow, 
#  handle_list_profiles_menu_action, handle_create_profile_menu_action, 
#  handle_load_persistent_profile_menu_action, handle_delete_profile_menu_action,
#  manage_persistent_profiles_menu_loop - asegúrate que todas estén definidas)

def initial_checks_display(): # Renombrada para evitar confusión con la lógica de network_checker
    # console.print("\n[bold blue][+] Performing initial OPSEC checks...[/bold blue]") # El título ya lo pone la vista
    public_ip, ip_info = None, None
    nc_console = console if DEBUG_MODE else None # Pasar consola solo si DEBUG
    with console.status("[spinner.dots] Checking network configuration...", spinner_style="blue"):
        try: public_ip, ip_info = network_checker.get_public_ip_info(console=nc_console)
        except: pass # Errores ya se loguean/imprimen en get_public_ip_info
    if public_ip:
        ip_display = Text(); ip_display.append("  [*] Your public IP: "); ip_display.append(public_ip, style="bold green")
        if ip_info and ip_info.get("country"):
            loc=f"{ip_info.get('city','N/A')}, {ip_info.get('region','N/A')}, {ip_info.get('country','N/A')}"; isp=ip_info.get('isp','N/A')
            ip_display.append("\n      Location: "); ip_display.append(loc, style="yellow")
            ip_display.append("\n      ISP: "); ip_display.append(isp, style="yellow")
        else: ip_display.append("\n      [dim]Could not retrieve detailed IP geolocation.[/dim]")
        console.print(Panel(ip_display, title=Text("Public IP",style="bold white"), expand=False, border_style="green"))
    else: console.print(Panel(Text("  [!] Could not retrieve public IP address.",style="bold red"),title=Text("Public IP",style="bold white"), expand=False, border_style="red"))
    dns_servers = []
    with console.status("[spinner.dots] Checking DNS servers...", spinner_style="blue"):
        try: dns_servers = network_checker.get_dns_servers(console=nc_console)
        except: pass
    if dns_servers:
        dns_text = Text("  [*] System DNS Servers:\n"); 
        for s_ip in dns_servers: dns_text.append(f"      - "); dns_text.append(s_ip, style="cyan"); dns_text.append("\n")
        if dns_text.plain.endswith("\n"): dns_text.truncate(len(dns_text.plain)-1)
        console.print(Panel(dns_text, title=Text("DNS Servers",style="bold white"), expand=False, border_style="cyan"))
    else: console.print(Panel(Text("  [!] Could not retrieve system DNS servers.",style="bold red"),title=Text("DNS Servers",style="bold white"), expand=False, border_style="red"))
    return public_ip, dns_servers

def select_browser_interactive(detected_browsers_paths, prompt_message="Select browser"):
    # ... (código de select_browser_interactive como antes)
    choices = []
    if "firefox" in detected_browsers_paths and detected_browsers_paths["firefox"]: choices.append("firefox")
    if "chrome" in detected_browsers_paths and detected_browsers_paths["chrome"]: choices.append("chrome")
    if "chromium" in detected_browsers_paths and detected_browsers_paths["chromium"] and "chrome" not in choices: choices.append("chromium")
    if not choices: console.print("[red]No supported browsers detected.[/red]"); return None
    default_choice = "firefox" if "firefox" in choices else choices[0]
    if len(choices) == 1: return choices[0] # Auto-select if only one
    return Prompt.ask(Text.from_markup(f"[bold gold1]{prompt_message}[/bold gold1]"), choices=choices, default=default_choice, console=console).lower()

def start_session_flow(browser_choice, profile_path, is_temp_profile, console_obj):
    # ... (código de start_session_flow como antes, con su "Press Enter" al final)
    console_obj.print(f"\n[bold blue][+] Launching [magenta]{browser_choice.capitalize()}[/magenta] with profile: [cyan]{profile_path}[/cyan][/bold blue]")
    if is_temp_profile: console_obj.print("    [italic]This is a temporary profile and will be deleted after the browser closes.[/italic]")
    else: console_obj.print("    [italic]This is a persistent profile. Close the browser to end the session monitoring.[/italic]")
    browser_process = None
    with console_obj.status(f"[spinner.dots] Waiting for {browser_choice.capitalize()} to launch...", spinner_style="blue"):
        browser_process = browser_manager.launch_browser_with_profile(browser_type_requested=browser_choice, profile_path=profile_path, console=console_obj)
        if browser_process: time.sleep(1)
    if browser_process:
        console_obj.print(f"  [green][*] [magenta]{browser_choice.capitalize()}[/magenta] launched. Waiting for it to close...[/green]")
        try:
            browser_process.wait() 
            console_obj.print(f"\n[green][+] Browser session for [magenta]{browser_choice.capitalize()}[/magenta] ended.[/green]")
        except KeyboardInterrupt:
            console_obj.print(f"\n[yellow][!] Browser session interrupted. Terminating browser...[/yellow]")
            browser_process.terminate(); 
            try: browser_process.wait(timeout=5) 
            except: pass 
            if is_temp_profile: console_obj.print("[yellow]Proceeding to cleanup temporary profile...[/yellow]")
        finally: 
            if is_temp_profile and profile_path and os.path.exists(profile_path):
                console_obj.print(f"\n[bold blue][+] Cleaning up temporary profile: [cyan]{profile_path}[/cyan][/bold blue]")
                if browser_manager.remove_profile(profile_path, console=console_obj): console_obj.print("  [green][*] Temporary profile successfully removed.[/green]")
                else: console_obj.print(f"  [bold red][!] Failed to remove temporary profile.[/bold red]")
            elif is_temp_profile and profile_path and not os.path.exists(profile_path):
                 if DEBUG_MODE: console_obj.log(f"[dim]Temporary profile {profile_path} seems removed already.[/dim]")
    else: 
        console_obj.print(f"[bold red][!] Failed to launch {browser_choice.capitalize()}.[/bold red]")
        if is_temp_profile and profile_path and os.path.exists(profile_path):
            if browser_manager.remove_profile(profile_path, console=console_obj):
                console_obj.print(f"[yellow]Cleaned up profile at {profile_path} due to launch failure.[/yellow]")
    Prompt.ask("Press Enter to return to the main menu...", console=console, default="", show_default=False)

def handle_list_profiles_menu_action(): 
    # console.clear(); display_banner_and_app_info() # Limpieza hecha por el menú que llama
    console.print(Rule("[bold underline green]Persistent Profiles[/bold underline green]", style="green"))
    profiles_data = config_manager.load_profiles_data()
    if not profiles_data:
        console.print("No persistent profiles found.");
    else:
        table = Table(title="Available Profiles", box=SIMPLE_HEAVY, show_lines=True, header_style="bold magenta")
        table.add_column("Profile Name", style="cyan", min_width=15); table.add_column("Browser", style="green", min_width=10)
        table.add_column("Bookmarks Set", style="yellow", min_width=15); table.add_column("Created At", style="dim", min_width=12)
        for profile in profiles_data:
            created_at_str = profile.get("created_at", "N/A")
            try:
                dt_obj = datetime.fromisoformat(created_at_str.replace('Z', '+00:00') if 'Z' in created_at_str else created_at_str)
                formatted_date = dt_obj.strftime("%Y-%m-%d")
            except ValueError: formatted_date = created_at_str.split("T")[0] if "T" in created_at_str else created_at_str
            table.add_row(profile.get("profile_name"), profile.get("browser_type","N/A").capitalize(), profile.get("bookmarks_set_name","None"), formatted_date)
        if table.row_count > 0: console.print(table)
    Prompt.ask("Press Enter to return to the profile menu...", console=console, default="", show_default=False)

def handle_create_profile_menu_action(detected_browser_paths):
    # ... (código como en la versión anterior, con su "Press Enter" al final)
    console.print(Rule("[bold green]Create New Persistent Profile[/bold green]", style="green"))
    if not detected_browser_paths:
        console.print("[red]No browsers detected. Cannot create a profile.[/red]")
        Prompt.ask("Press Enter...", console=console, default="", show_default=False); return
    try:
        profile_name = Prompt.ask("Enter a unique name for this new profile (e.g., 'project_alpha')")
        if not profile_name.strip(): console.print("[red]Profile name cannot be empty.[/red]"); Prompt.ask("Press Enter..."); return
        if config_manager.get_profile_by_name(profile_name): console.print(f"[red]Profile '{profile_name}' already exists.[/red]"); Prompt.ask("Press Enter..."); return
        browser_type = select_browser_interactive(detected_browser_paths, prompt_message="Select browser for this persistent profile")
        if not browser_type: Prompt.ask("Press Enter..."); return
        bookmarks_set = "default" if Confirm.ask("Load default OSINT bookmarks into this profile?", default=True, console=console) else None
        console.print(f"Summary - Name: [cyan]{profile_name}[/cyan], Browser: [magenta]{browser_type}[/magenta], Bookmarks: [yellow]{bookmarks_set or 'None'}[/yellow]")
        if not Confirm.ask("Proceed to create this persistent profile?", default=True, console=console):
            console.print("[yellow]Profile creation cancelled.[/yellow]"); Prompt.ask("Press Enter..."); return
        browser_profile_disk_path = browser_manager.create_profile(
            browser_type=browser_type, profile_custom_name=profile_name, 
            is_persistent=True, bookmarks_template_name=bookmarks_set, console=console
        )
        if not browser_profile_disk_path:
            console.print("[red]Failed to create browser profile directory.[/red]"); Prompt.ask("Press Enter..."); return
        new_profile_data = {"profile_name": profile_name, "browser_type": browser_type, "browser_profile_path": browser_profile_disk_path, "bookmarks_set_name": bookmarks_set, "created_at": datetime.now().isoformat()}
        profiles = config_manager.load_profiles_data(); profiles.append(new_profile_data)
        if config_manager.save_profiles_data(profiles, console=console): console.print(f"[green]Persistent profile '[cyan]{profile_name}[/cyan]' created successfully![/green]")
        else:
            console.print("[red]Failed to save profile metadata.[/red]")
            if os.path.exists(browser_profile_disk_path):
                if DEBUG_MODE: console.log(f"Cleaning up {browser_profile_disk_path} due to metadata save fail.")
                browser_manager.remove_profile(browser_profile_disk_path, console)      
    except InvalidResponse: console.print("\n[yellow]Profile creation cancelled.[/yellow]")
    except Exception as e: console.print(f"[red]Error during profile creation: {e}[/red]");
    Prompt.ask("Press Enter to return to the profile menu...", console=console, default="", show_default=False)


def handle_load_persistent_profile_menu_action(detected_browser_paths, auto_load_to_session=False, called_from_main_menu=False):
    # ... (código como en la versión anterior, con su "Press Enter" al final si no es auto_load desde main menu)
    console.print(Rule("[bold green]Load Persistent Profile[/bold green]", style="green"))
    profiles = config_manager.load_profiles_data()
    if not profiles:
        console.print("[yellow]No persistent profiles found.[/yellow]")
        Prompt.ask("Press Enter...", console=console, default="", show_default=False); return False

    profile_choices = {str(i+1): p["profile_name"] for i, p in enumerate(profiles)}
    profile_choices[str(len(profiles)+1)] = "(Cancel / Back)"
    console.print("Available profiles:")
    for key, name in profile_choices.items():
        if name != "(Cancel / Back)":
            browser = next((p['browser_type'] for p in profiles if p['profile_name'] == name), "N/A")
            console.print(f"  [cyan]{key}[/cyan]. {name} ([italic dim]{browser.capitalize()}[/italic dim])")
        else: console.print(f"  [cyan]{key}[/cyan]. {name}")
    choice_key = Prompt.ask("Select profile to load (number) or Cancel:", choices=list(profile_choices.keys()), console=console).upper()

    if profile_choices.get(choice_key) == "(Cancel / Back)":
        if not (auto_load_to_session and not called_from_main_menu): console.print("[yellow]Load profile cancelled.[/yellow]")
        if not auto_load_to_session or called_from_main_menu : Prompt.ask("Press Enter...", console=console, default="", show_default=False) # Pausar si no es una carga automática silenciosa desde un submenú
        return False

    selected_profile_name = profile_choices.get(choice_key)
    profile_data = config_manager.get_profile_by_name(selected_profile_name, console=console)
    if profile_data:
        CURRENT_SESSION_SETUP["profile_type"] = "Persistent"
        CURRENT_SESSION_SETUP["gs_profile_name"] = profile_data["profile_name"]
        CURRENT_SESSION_SETUP["browser_selected"] = profile_data["browser_type"]
        CURRENT_SESSION_SETUP["bookmarks_set"] = profile_data.get("bookmarks_set_name")
        CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = profile_data["browser_profile_path"]
        CURRENT_SESSION_SETUP["network_checks_status"] = "Pending"
        console.print(f"[green]Profile '[cyan]{selected_profile_name}[/cyan]' loaded into current session setup.[/green]")
        if not auto_load_to_session: Prompt.ask("Press Enter...", console=console, default="", show_default=False)
        return True
    else:
        console.print(f"[red]Error loading profile '{selected_profile_name}'.[/red]")
        if not auto_load_to_session: Prompt.ask("Press Enter...", console=console, default="", show_default=False)
        return False

def handle_delete_profile_menu_action():
    # ... (código como en la versión anterior, con su "Press Enter" al final)
    console.print(Rule("[bold red]Delete Persistent Profile[/bold red]", style="red"))
    profiles = config_manager.load_profiles_data()
    if not profiles: console.print("[yellow]No persistent profiles to delete.[/yellow]"); Prompt.ask("Press Enter..."); return
    profile_choices = {str(i+1): p["profile_name"] for i, p in enumerate(profiles)}
    profile_choices[str(len(profiles)+1)] = "(Cancel / Back)"
    console.print("Select profile to DELETE:")
    for key, name in profile_choices.items(): console.print(f"  [bold cyan]{key}[/bold cyan]. {name}")
    choice_key = Prompt.ask("Enter number or Cancel:", choices=list(profile_choices.keys()), console=console).upper()
    if profile_choices.get(choice_key) == "(Cancel / Back)": console.print("[yellow]Delete cancelled.[/yellow]"); Prompt.ask("Press Enter..."); return
    profile_name_to_delete = profile_choices.get(choice_key)
    profile_to_delete_data = config_manager.get_profile_by_name(profile_name_to_delete)
    if not profile_to_delete_data: console.print(f"[red]Profile '{profile_name_to_delete}' not found.[/red]"); Prompt.ask("Press Enter..."); return
    if Confirm.ask(f"DELETE profile '[bold red]{profile_name_to_delete}[/bold red]' and its browser data?", default=False, console=console):
        browser_dir_path = profile_to_delete_data.get("browser_profile_path")
        if browser_dir_path and os.path.exists(browser_dir_path):
            if browser_manager.remove_profile(browser_dir_path, console=console): console.print(f"  [green]Browser data deleted: [cyan]{browser_dir_path}[/cyan]")
            else: console.print(f"  [red]Failed to delete browser data.[/red]")
        updated_profiles = [p for p in profiles if p["profile_name"] != profile_name_to_delete]
        if config_manager.save_profiles_data(updated_profiles, console=console):
            console.print(f"  [green]Profile '{profile_name_to_delete}' removed from config.[/green]")
            if CURRENT_SESSION_SETUP.get("gs_profile_name") == profile_name_to_delete:
                CURRENT_SESSION_SETUP.update({"profile_type": "Temporary", "gs_profile_name": None, "browser_selected": None, "bookmarks_set": None, "browser_profile_on_disk_path": None, "network_checks_status": "Pending"})
                console.print("[yellow]Active session setup reset to temporary.[/yellow]")
        else: console.print(f"  [red]Failed to update config after deleting '{profile_name_to_delete}'.[/red]")
    else: console.print("[yellow]Deletion cancelled.[/yellow]")
    Prompt.ask("Press Enter to return to the profile menu...", console=console, default="", show_default=False)


def manage_persistent_profiles_menu_loop(detected_browser_paths): # Renombrada para bucle
    """Sub-bucle para la gestión de perfiles persistentes."""
    while True:
        console.clear(); display_banner_and_app_info()
        # No mostrar el panel de estado de sesión aquí, es irrelevante para la gestión de perfiles guardados.
        console.print(Rule("[bold green]Manage Persistent Profiles[/bold green]", style="green"))
        menu_items = {
            "1": "List Profiles", 
            "2": "Create New Profile", 
            "3": "Delete Profile", 
            "4": "Load Profile into Current Main Setup", # Carga y VUELVE al menú principal
            "5": "Back to Main Menu"
        }
        console.print("Available actions:")
        for key, text in menu_items.items(): console.print(f"  [bold cyan]{key}[/bold cyan]. {text}")
        console.line()
        
        choice_key = Prompt.ask(Text.from_markup("Choose an action (number):"), choices=list(menu_items.keys()), show_choices=False, console=console).upper()
        action_key = menu_items.get(choice_key, "") # Obtener el texto para un switch más legible si se quisiera

        if choice_key == "1": handle_list_profiles_menu_action() # Esta es una vista que pausa
        elif choice_key == "2": handle_create_profile_menu_action(detected_browser_paths) # Vista que pausa
        elif choice_key == "3": handle_delete_profile_menu_action() # Vista que pausa
        elif choice_key == "4": 
            loaded_successfully = handle_load_persistent_profile_menu_action(detected_browser_paths, auto_load_to_session=True, called_from_main_menu=False) # No es main menu, es submenú.
            if loaded_successfully: # Si se cargó, salir de este submenú para ver el efecto en el menú principal
                console.print("[green]Profile loaded. Returning to main menu to see changes in 'Current Session Setup'.[/green]")
                time.sleep(1.5) # Dar tiempo a leer
                break 
            # Si no se cargó (ej. canceló), el bucle de manage_profiles continúa.
        elif choice_key == "5": break 
        # else: No se necesita, Prompt valida

def start():
    # ... (código de start como en la versión anterior) ...
    parser = argparse.ArgumentParser(add_help=False)
    info_group = parser.add_argument_group('Informational Arguments')
    info_group.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    info_group.add_argument("-h", "--help", action="store_true")
    info_group.add_argument("--check-setup", action="store_true")
    action_group = parser.add_argument_group('Session Setup Arguments')
    action_group.add_argument("-b", "--browser", choices=['firefox', 'chrome', 'chromium'])
    action_group.add_argument("--no-bookmarks", action="store_true")
    action_group.add_argument("--bookmarks", help="Specify bookmarks set name.")
    
    args, _ = parser.parse_known_args()

    if args.help:
        console.clear(); display_banner_and_app_info()
        console.print(Panel(Text.from_markup("""[bold]Guardian Spy CLI Options:[/bold]
  (no args)              : Start interactive menu.
  -v, --version          : Show version.
  --check-setup        : Perform setup checks.
  -h, --help             : Show this help.
  -b, --browser BROWSER  : Pre-select BROWSER.
  --no-bookmarks         : Start with no bookmarks.
  --bookmarks SET        : Pre-select bookmarks SET."""), title="CLI Help", border_style="blue", padding=1))
        sys.exit(0)
    if args.check_setup:
        view_perform_network_checks() # Esta es la vista completa
        sys.exit(0) 
    main_loop(args)

if __name__ == '__main__': 
    start()