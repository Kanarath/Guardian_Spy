# guardian_spy/main_cli.py
import argparse
import sys
import time 
import os 
from datetime import datetime 

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.rule import Rule 
from rich.align import Align
from rich.box import SIMPLE_HEAVY

try:
    from . import browser_manager
    from . import network_checker
    from . import utils 
    from . import config_manager 
    from . import __version__, __app_name__ 
    from guardian_spy import DEBUG_MODE
except ImportError:
    import browser_manager, network_checker, utils, config_manager
    try: from __init__ import __version__, __app_name__, DEBUG_MODE
    except ImportError: __version__ = "0.0.0e"; __app_name__ = "GS(Error)"; DEBUG_MODE = True

console = Console(force_terminal=True) 

CURRENT_SESSION_SETUP = {
    "profile_type": "Temporary", 
    "gs_profile_name": None,     
    "browser_selected": None,    
    "bookmarks_set": "default", 
    "network_checks_status": "Pending", 
    "browser_profile_on_disk_path": None, 
}

ORIGINAL_BANNER_ASCII = """[bold cyan]
################################################################################################
#                                                                                              #
#  ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗    ███████╗██████╗ ██╗   ██╗ #
# ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║    ██╔════╝██╔══██╗╚██╗ ██╔╝ #
# ██║  ███╗██║   ██║███████║██████╔╝██║  ██║██║███████║██╔██╗ ██║    ███████╗██████╔╝ ╚████╔╝  #
# ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██║██╔══██║██║╚██╗██║    ╚════██║██╔═══╝   ╚██╔╝   #
# ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║    ███████║██║        ██║    #
#  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝    ╚══════╝╚═╝        ╚═╝    #
#                                                                                              #
################################################################################################
[/bold cyan]"""

LAUNCH_ACTIVE_SHIELD_ASCII = """[bold blue]
                                              =@##%@@@=                                             
                                         =+#%##*++:%%%@@@@#                                         
                                    .@*+%#**++=---.#*****#@@@@@%.                                   
                                %%***+++=-=---=*#*.#%#******##%@@@@@@                               
                         :-*%###+====-----=+*#+.   +--+*%##******##%@@@@@@#                         
                    %=*#**++===-------=+*#*.  .-== %%**+=:+%%%###*****###@@@@@@@#                   
                   @ ++==-----:-=+*#*+-.  :-=====- #***##***:.=*%%@@%#*****###%@@                   
                   @ =:--+*####+:     :-==-====--- %#******####*-:...+#%%@%%#**%@                   
                   @ :-+#-      :---===-=-=-----== ##*********####%%#*+=...+%@#@@                   
                   @: -#  =+++==---------------=-- %#***********###*###%%%#% *#@@                   
                   @% +%  *----:---::-------====-- %#**********###*##*#####@ @%@%                   
                   -@ +*: +-:::--------------=---- %#********#***********##% @#@*                   
                    @ #=% +=---:::-----------=--=- %##***######*#***##****%@ @%@-                   
                    @ ==@ :+---:::-:-------===--=- %#*##********####***####* @%@                    
                    @# +%  +-::----------------==- %#*###***#****#****#*###+*@%@                    
                    @@ +#- =:--==--=-----=--===-== @#*****###*####**####**##%%@@                    
                     @ -+# =-++*+++#%**-**=%**#+*+:@%##**@**#########%##*##*%#@%                    
                     @* =% ==+   @@   @%=  @  .@-  *@@.+#@:##@+*##@@.*@%###*%#@-                    
                     @@ +# :-=@  @@ .  @  @+-  @# -*@@:*@%#=+@+*.*@*#*@#**#*%%@                     
                      @ .*: :.+  =: @. @ -@%@= @: @-%=+%%*%+*@-#@-@:#%@***#+@@@                     
                      @= :  :=#@ =.:@@ . %@+%+ : @@:**+@#*@=**+@@-%**@#####+@@-                     
                      :@ @@+###@   @%@   @#+*@   @**=+*@**%+***@##-*+@*####*@@                      
                       @.*@-=*+*%@@%+#@@@%***%@@@#*%@@@##*##@@@##%@@@###*#+@@%                       
                       %@ @@:++++==++==+++++++++++=#****###***********####+@@                       
                        @% @:+****++*********#**##*####*#######*########%*@@@                       
                        %@ #@-***********+*********#########*############*%@                        
                         @@-@==****+*********#*****#################*####*@@                        
                          @=*#-****+******#***#****#####*################@@                         
                          .@ %***+*******#*********#################*####@.                         
                           @@:#+#+*####***###**###*###################%%@@                          
                            @@:=#%*****##*#**#####*################*%%#@@                           
                             @@+*###**##****##*##**##%#######%###*#%#%@@                            
                              @@ ##%@#**##########*############**@%#%@@                             
                               @@=**#%%*####################***%%###@@                              
                                @@*+####%+*#######*#%%#######%%##*@@@                               
                                  @@.####%%-+%#%########**#@%%###@@.                                
                                   @@**####%@-.#%%####**#@%#*##%@@                                  
                                     @@:*%#*#%@%-=*#*#%@%#####@@@                                   
                                      @@@-#%%###%@##@#######@@@                                     
                                        @@@.%#############@@@                                       
                                          @@@=*%%###*###@@@                                         
                                            @@@-+%%%##@@@                                           
                                              -@@=-%@@@                                             
                                                 @@@=                                               
[/bold blue]"""

def display_initial_banner_and_app_info(): 
    console.print(Text.from_markup(ORIGINAL_BANNER_ASCII)) 
    app_info_text = Text.from_markup(f"""[bold green]{__app_name__}[/bold green]
[italic]OPSEC Session Assistant[/italic]
Version: [yellow]{__version__}[/yellow]""")
    console.print(app_info_text, justify="center")
    console.line()

def display_session_status_sequential():
    console.print(Rule("[gold1]Current Session Setup[/gold1]", style="blue"))
    pt = CURRENT_SESSION_SETUP['profile_type']
    pt_display = f"  Profile Type: [bold]{pt}[/bold]"
    if pt == "Persistent" and CURRENT_SESSION_SETUP['gs_profile_name']: 
        pt_display += f" ([cyan]{CURRENT_SESSION_SETUP['gs_profile_name']}[/cyan])"
    elif pt == "Persistent": pt_display += " [yellow](Not Loaded)[/yellow]"
    console.print(pt_display)
    bs_display = f"  Browser: [magenta]{CURRENT_SESSION_SETUP['browser_selected'] or '[Not Selected]'}[/magenta]"
    console.print(bs_display)
    bms_display = f"  Bookmarks Set: [yellow]{CURRENT_SESSION_SETUP['bookmarks_set'] or 'None'}[/yellow]"
    console.print(bms_display)
    ncs = CURRENT_SESSION_SETUP['network_checks_status']
    nc_color = "yellow"; 
    if "OK" in ncs: nc_color = "green"; 
    elif "Error" in ncs or "Leak" in ncs: nc_color = "red"
    ncs_display = f"  Network Checks: [{nc_color}]{ncs}[/{nc_color}]"
    console.print(ncs_display)
    console.line()

def display_command_menu_sequential():
    console.print(Rule("[bold_yellow]Available Commands[/bold_yellow]", style="yellow"))
    commands = {
        "setup": "Configure current session (profile, browser, bookmarks)",
        "check": "Perform network & browser checks",
        "launch": "Launch browser with current session setup",
        "profiles": "Manage persistent profiles (list, create, delete, load)",
        "status": "Show current session setup summary",
        "about": "Show information about Guardian Spy",
        "help": "Show this command menu again", # Comando HELP
        # "clear": "Clear the screen and show initial display", # Comando CLEAR eliminado
        "quit": "Exit Guardian Spy"
    }
    for cmd, desc in commands.items():
        console.print(f"  [bold cyan]{cmd:<10}[/bold cyan] - {desc}")
    console.line()

def initial_checks_display_sequential(): 
    nc_console = console if DEBUG_MODE else None
    public_ip, ip_info = None, None
    console.print("[+] Performing OPSEC network checks...")
    # CORRECCIÓN: Quitar console=console de console.status
    with console.status("[spinner.dots]Checking network...", spinner_style="blue"):
        try: public_ip, ip_info = network_checker.get_public_ip_info(console=nc_console)
        except: pass 
    if public_ip:
        ip_display = Text(); ip_display.append("  [*] Public IP: "); ip_display.append(public_ip, style="bold green")
        if ip_info and ip_info.get("country"):
            loc=f"{ip_info.get('city','N/A')}, {ip_info.get('region','N/A')}, {ip_info.get('country','N/A')}"; isp=ip_info.get('isp','N/A')
            ip_display.append("\n      Location: "); ip_display.append(loc, style="yellow")
            ip_display.append("\n      ISP: "); ip_display.append(isp, style="yellow")
        else: ip_display.append("\n      [dim]Could not retrieve detailed IP geolocation.[/dim]")
        console.print(Panel(ip_display, title="Public IP", border_style="green", expand=False))
    else: console.print(Panel(Text("  [!] Could not retrieve public IP address.",style="bold red"),title="Public IP", border_style="red"))
    
    dns_servers = []
    # CORRECCIÓN: Quitar console=console de console.status
    with console.status("[spinner.dots]Checking DNS...", spinner_style="blue"):
        try: dns_servers = network_checker.get_dns_servers(console=nc_console)
        except: pass
    if dns_servers:
        dns_text = Text("  [*] System DNS Servers:\n"); 
        for s_ip in dns_servers: dns_text.append(f"      - "); dns_text.append(s_ip, style="cyan"); dns_text.append("\n")
        if dns_text.plain.endswith("\n"): dns_text.truncate(len(dns_text.plain)-1)
        console.print(Panel(dns_text, title="DNS Servers", border_style="cyan", expand=False))
    else: console.print(Panel(Text("  [!] Could not retrieve system DNS servers.",style="bold red"),title="DNS Servers",border_style="red"))
    return public_ip, dns_servers

def select_browser_interactive_sequential(detected_browsers_paths, current_selection=None):
    choices = []; 
    if "firefox" in detected_browsers_paths and detected_browsers_paths["firefox"]: choices.append("firefox")
    if "chrome" in detected_browsers_paths and detected_browsers_paths["chrome"]: choices.append("chrome")
    if "chromium" in detected_browsers_paths and detected_browsers_paths["chromium"] and "chrome" not in choices: choices.append("chromium")
    if not choices: console.print("[red]No supported browsers detected.[/red]"); return current_selection
    default_choice = current_selection if current_selection in choices else ("firefox" if "firefox" in choices else choices[0])
    console.print("Available browsers:")
    for i, browser_name in enumerate(choices): console.print(f"  [cyan]{i+1}[/cyan]. {browser_name.capitalize()}")
    console.print(f"  [cyan]C[/cyan]. Cancel")
    prompt_choices = [str(i+1) for i in range(len(choices))] + ["c", "C"]
    default_prompt_val = "c" 
    if default_choice in choices:
        try: default_prompt_val = str(choices.index(default_choice)+1)
        except ValueError: pass 
    raw_user_choice = Prompt.ask(f"Select browser number or C (current: [magenta]{current_selection or 'None'}[/magenta], default: {default_choice.capitalize()})", choices=prompt_choices, default=default_prompt_val ,console=console).lower()
    if raw_user_choice == "c": console.print("[yellow]Browser selection cancelled.[/yellow]"); return current_selection
    try:
        choice_index = int(raw_user_choice) - 1
        if 0 <= choice_index < len(choices): return choices[choice_index]
    except ValueError: pass
    console.print("[red]Invalid selection.[/red]"); return current_selection

def start_session_flow_sequential(browser_choice, profile_path, is_temp_profile, console_obj):
    console_obj.print(f"\n[bold blue][+] Launching [magenta]{browser_choice.capitalize()}[/magenta] with profile: [cyan]{profile_path}[/cyan][/bold blue]")
    if is_temp_profile: console_obj.print("    [italic]This is a temporary profile and will be deleted after the browser closes.[/italic]")
    else: console_obj.print("    [italic]This is a persistent profile.[/italic]")
    
    browser_process = None
    # CORRECCIÓN: Quitar console=console_obj de console_obj.status
    with console_obj.status(f"[spinner.dots]Waiting for {browser_choice.capitalize()} to launch...", spinner_style="blue"):
        browser_process = browser_manager.launch_browser_with_profile(browser_type_requested=browser_choice, profile_path=profile_path, console=console_obj)
        if browser_process: time.sleep(1) 

    if browser_process:
        # --- Mostrar Escudo ASCII Estático ---
        console_obj.line() 
        console_obj.print(Text.from_markup(LAUNCH_ACTIVE_SHIELD_ASCII)) 
        console_obj.print(Align.center(Text.from_markup(f"[bold green]Guardian Spy Shield ACTIVE[/bold green] - Browser: [magenta]{browser_choice.capitalize()}[/magenta]")))
        console_obj.print(Align.center(Text.from_markup("[dim](Close browser window or press Ctrl+C here to return to Guardian Spy prompt)[/dim]")))
        console_obj.line()
        
        session_interrupted_by_user = False
        try:
            while browser_process.poll() is None:
                time.sleep(0.5) 
        except KeyboardInterrupt:
            session_interrupted_by_user = True
            # Imprimir en una nueva línea, el escudo ya no se ve porque la terminal hizo scroll o se interrumpió
            console_obj.print(f"\n[yellow][!] Browser session wait interrupted by user.[/yellow]") 
        
        # No limpiar pantalla aquí. Los mensajes de salida se añaden debajo.
        # display_initial_banner_and_app_info() # No mostrar banner aquí

        if session_interrupted_by_user:
            console_obj.print(f"\n[yellow][!] Terminating browser due to interruption...[/yellow]")
            browser_process.terminate()
            try: browser_process.wait(timeout=3)
            except: pass 
        else: 
            console_obj.print(f"\n[green][+] Browser session for [magenta]{browser_choice.capitalize()}[/magenta] ended.[/green]")
        
        if is_temp_profile and profile_path and os.path.exists(profile_path):
            console_obj.print(f"\n[bold blue][+] Cleaning up temporary profile: [cyan]{profile_path}[/cyan][/bold blue]")
            if browser_manager.remove_profile(profile_path, console=console_obj): 
                console_obj.print("  [green][*] Temporary profile successfully removed.[/green]")
            else: 
                console_obj.print(f"  [bold red][!] Failed to remove temporary profile.[/bold red]")
        elif is_temp_profile and profile_path and not os.path.exists(profile_path):
                 if DEBUG_MODE and hasattr(console_obj, 'log'): console_obj.log(f"[dim]Temp profile {profile_path} seems removed.[/dim]")
    else: 
        console_obj.print(f"[bold red][!] Failed to launch {browser_choice.capitalize()}.[/bold red]")
        if is_temp_profile and profile_path and os.path.exists(profile_path):
            if browser_manager.remove_profile(profile_path, console=console_obj):
                console_obj.print(f"[yellow]Cleaned up profile {profile_path} due to launch failure.[/yellow]")
    
    print("DEBUG: start_session_flow_sequential - About to Prompt 'Press Enter to continue'", file=sys.stderr) 
    Prompt.ask("Press Enter to continue...", console=console, default="", show_default=False)
    print("DEBUG: start_session_flow_sequential - AFTER Prompt 'Press Enter to continue'", file=sys.stderr) 


# --- Handlers de Comandos Secuenciales ---
def handle_command_setup_seq(detected_browser_paths):
    console.print(Rule("[green]Session Setup[/green]", style="green"))
    display_session_status_sequential() 
    console.print(f"1. Profile Type (Current: [bold]{CURRENT_SESSION_SETUP['profile_type']}[/bold])")
    if Confirm.ask("Toggle Profile Type (Temporary/Persistent)?", default=False, console=console):
        if CURRENT_SESSION_SETUP["profile_type"] == "Temporary":
            CURRENT_SESSION_SETUP["profile_type"] = "Persistent"; CURRENT_SESSION_SETUP["gs_profile_name"] = None
            CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = None
            console.print("Switched to: [bold]Persistent[/bold]. Use 'profiles load' or 'profiles create'.")
        else:
            CURRENT_SESSION_SETUP["profile_type"] = "Temporary"; CURRENT_SESSION_SETUP["gs_profile_name"] = None
            CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = None
            console.print("Switched to: [bold]Temporary[/bold].")
    console.line()
    console.print(f"2. Browser (Current: [magenta]{CURRENT_SESSION_SETUP['browser_selected'] or '[Not Selected]'}[/magenta])")
    old_browser = CURRENT_SESSION_SETUP["browser_selected"]
    new_browser = select_browser_interactive_sequential(detected_browser_paths, old_browser)
    if new_browser != old_browser and new_browser is not None:
        CURRENT_SESSION_SETUP["browser_selected"] = new_browser
        if CURRENT_SESSION_SETUP["profile_type"] == "Persistent" and CURRENT_SESSION_SETUP["gs_profile_name"]:
            console.print("[yellow]Browser changed. This setup is now like a new temporary one based on the persistent profile.[/yellow]")
            CURRENT_SESSION_SETUP["gs_profile_name"] = f"(Mod: {CURRENT_SESSION_SETUP['gs_profile_name'] or 'Unsaved'})"
            CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = None
    console.line()
    console.print(f"3. Bookmarks Set (Current: [yellow]{CURRENT_SESSION_SETUP['bookmarks_set'] or 'None'}[/yellow])")
    available_sets = {"1": ("None", None), "2": ("Default OSINT", "default")}
    console.print("Available bookmark sets:")
    for key, (desc, _) in available_sets.items(): console.print(f"  [cyan]{key}[/cyan]. {desc}")
    console.print(f"  [cyan]C[/cyan]. Cancel (keep current)")
    current_bm_val = CURRENT_SESSION_SETUP["bookmarks_set"]
    default_key_choice = next((k for k, (_,v) in available_sets.items() if v == current_bm_val), "c")
    prompt_choices_bm = list(available_sets.keys()) + ["c", "C"]
    bm_choice_key = Prompt.ask("Select bookmarks set number or C to Cancel:", choices=prompt_choices_bm, default=default_key_choice, console=console).upper()
    if bm_choice_key != "C":
        _, internal_value = available_sets.get(bm_choice_key, (None,None))
        if internal_value is not None or bm_choice_key == "1": 
            CURRENT_SESSION_SETUP["bookmarks_set"] = internal_value
            console.print(f"Bookmarks set to: [yellow]{ (internal_value or 'None').capitalize() }[/yellow]")
    console.print(Rule("Setup Configuration Complete", style="green"))
    display_session_status_sequential()

def handle_command_check_seq():
    console.print(Rule("[green]Network & Browser Checks[/green]", style="green"))
    utils.check_browser_executables(console=console)
    console.line()
    public_ip_val, dns_servers_val = initial_checks_display_sequential() 
    status_summary_parts = []
    if public_ip_val: status_summary_parts.append(f"IP: [green]{public_ip_val}[/green]")
    else: status_summary_parts.append("[red]IP: Error[/red]")
    if dns_servers_val: status_summary_parts.append(f"DNS: [green]OK ({len(dns_servers_val)} found)[/green]")
    else: status_summary_parts.append("[red]DNS: Error[/red]")
    CURRENT_SESSION_SETUP["network_checks_status"] = ", ".join(status_summary_parts)
    console.print(Rule("Checks Complete", style="green"))

def handle_command_launch_seq(detected_browser_paths):
    console.print(Rule("[green]Launch Session[/green]", style="green"))
    if not CURRENT_SESSION_SETUP["browser_selected"]:
        console.print("[yellow]No browser selected. Please run 'setup' command first.[/yellow]"); return
    is_temp = (CURRENT_SESSION_SETUP["profile_type"] == "Temporary")
    browser_choice = CURRENT_SESSION_SETUP["browser_selected"]
    bookmarks_to_load = CURRENT_SESSION_SETUP["bookmarks_set"]
    gs_profile_name_for_disk = None
    if not is_temp and CURRENT_SESSION_SETUP.get("gs_profile_name") and \
       not (CURRENT_SESSION_SETUP.get("gs_profile_name") or "").startswith("(Mod"): 
        gs_profile_name_for_disk = CURRENT_SESSION_SETUP.get("gs_profile_name")
    actual_browser_profile_path = CURRENT_SESSION_SETUP.get("browser_profile_on_disk_path")
    should_create_browser_dir = False
    if is_temp: should_create_browser_dir = True
    elif gs_profile_name_for_disk: 
        if not actual_browser_profile_path: 
            base_persistent_dir = config_manager.get_browser_profiles_base_dir()
            actual_browser_profile_path = os.path.join(base_persistent_dir, gs_profile_name_for_disk)
        if not os.path.exists(actual_browser_profile_path): should_create_browser_dir = True
    elif not is_temp and not gs_profile_name_for_disk: 
        is_temp = True; should_create_browser_dir = True
    if should_create_browser_dir:
        profile_name_arg_for_create = gs_profile_name_for_disk if not is_temp else None
        prefix_arg_for_create = "gs_temp_browser_profile" if is_temp else None
        # CORRECCIÓN: Quitar console=console de console.status
        with console.status(f"[spinner.dots]Creating browser profile dir...", spinner_style="blue"):
            newly_created_path = browser_manager.create_profile(
                browser_type=browser_choice, profile_custom_name=profile_name_arg_for_create,
                profile_name_prefix=prefix_arg_for_create, is_persistent=(not is_temp), 
                bookmarks_template_name=bookmarks_to_load, console=console
            )
        if not newly_created_path: console.print(f"[red][!] Failed to create browser profile dir.[/red]"); return
        actual_browser_profile_path = newly_created_path
        console.print(f"  [green][*] Browser profile dir created: [cyan]{actual_browser_profile_path}[/cyan]")
        CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = actual_browser_profile_path
        if not is_temp and gs_profile_name_for_disk:
             profile_data_from_config = config_manager.get_profile_by_name(gs_profile_name_for_disk)
             if profile_data_from_config and profile_data_from_config.get("browser_profile_path") != actual_browser_profile_path:
                profile_data_from_config["browser_profile_path"] = actual_browser_profile_path
                all_profiles = config_manager.load_profiles_data()
                for i, p_conf in enumerate(all_profiles):
                    if p_conf["profile_name"] == gs_profile_name_for_disk: all_profiles[i] = profile_data_from_config; break
                config_manager.save_profiles_data(all_profiles, console=console)
    if not actual_browser_profile_path: console.print("[red]Error: Cannot determine browser profile path.[/red]"); return
    start_session_flow_sequential(browser_choice, actual_browser_profile_path, is_temp, console) 
    if is_temp: 
        CURRENT_SESSION_SETUP.update({"browser_profile_on_disk_path": None, "browser_selected": None, "bookmarks_set": None, "profile_type": "Temporary"})
        gs_profile_name_val = CURRENT_SESSION_SETUP.get("gs_profile_name") or ""
        if not gs_profile_name_val.startswith("(Mod"): 
            CURRENT_SESSION_SETUP["gs_profile_name"] = None
    CURRENT_SESSION_SETUP["network_checks_status"] = "Pending"

def handle_command_profiles_seq(detected_browser_paths):
    console.print(Rule("[green]Manage Persistent Profiles[/green]", style="green"))
    while True: 
        profile_commands = {"list": "List", "create": "Create", "delete": "Delete", "load": "Load to Main Setup", "back": "Back to Main"}
        for cmd, desc in profile_commands.items(): console.print(f"  [cyan]{cmd:<8}[/cyan] - {desc}")
        console.line()
        sub_command = Prompt.ask(Text.from_markup("[bold gold1]Profile >[/bold gold1]"), choices=list(profile_commands.keys()), default="back", console=console).lower()
        console.line()
        if sub_command == "list":
            console.print(Rule("[underline green]Persistent Profiles[/underline green]", style="green"))
            profiles_data = [] 
            try: profiles_data = config_manager.load_profiles_data()
            except Exception as e_load: console.print(f"[bold red]Error loading profiles: {e_load}[/bold red]");
            if not profiles_data: console.print("No persistent profiles found.")
            else:
                table = Table(title="Available Profiles", box=SIMPLE_HEAVY, show_lines=True, header_style="bold magenta")
                table.add_column("Name",style="cyan",min_width=15); table.add_column("Browser"); table.add_column("Bookmarks"); table.add_column("Created")
                if DEBUG_MODE: table.add_column("Browser Dir Path", style="dim", overflow="fold")
                valid_profiles_displayed = 0
                for profile_item in profiles_data:
                    if not isinstance(profile_item, dict): 
                        if DEBUG_MODE and hasattr(console, 'log'): console.log(f"[dim red]Skipping invalid profile entry: {profile_item}[/dim red]")
                        continue
                    created_at_str = profile_item.get("created_at","N/A"); browser_profile_path_val = profile_item.get("browser_profile_path", "[Not Set]")
                    formatted_date = created_at_str
                    if created_at_str != "N/A" and "T" in created_at_str:
                        try:
                            timestamp_part = created_at_str.split('.')[0].replace('Z', '+00:00')
                            dt_obj = datetime.fromisoformat(timestamp_part); formatted_date = dt_obj.strftime("%Y-%m-%d")
                        except ValueError: formatted_date = created_at_str.split("T")[0] 
                    row_data = [profile_item.get("profile_name", "[N/A]"), profile_item.get("browser_type","N/A").capitalize(), profile_item.get("bookmarks_set_name","None"), formatted_date]
                    if DEBUG_MODE: row_data.append(browser_profile_path_val)
                    table.add_row(*row_data); valid_profiles_displayed += 1
                if valid_profiles_displayed > 0: console.print(table)
                else: console.print("No valid profiles found to display.")
            console.line()
            # No "Press Enter" aquí, el prompt "Profile >" reaparecerá.
        elif sub_command == "create":
            console.print(Rule("[green]Create New Persistent Profile[/green]", style="green"))
            if not detected_browser_paths: console.print("[red]No browsers detected.[/red]"); console.line(); continue
            try:
                profile_name = Prompt.ask("Enter unique name for new profile", default=f"profile_{int(time.time())%10000}")
                if not profile_name.strip() or not profile_name.replace('_','').isalnum(): console.print("[red]Invalid name.[/red]"); console.line(); continue
                if config_manager.get_profile_by_name(profile_name): console.print(f"[red]Profile '{profile_name}' exists.[/red]"); console.line(); continue
                browser_type = select_browser_interactive_sequential(detected_browser_paths, None)
                if not browser_type: console.line(); continue
                bookmarks_set = "default" if Confirm.ask("Load default OSINT bookmarks?", default=True, console=console) else None
                console.print(f"Summary - Name: [cyan]{profile_name}[/cyan], Browser: [magenta]{browser_type}[/magenta], Bookmarks: [yellow]{bookmarks_set or 'None'}[/yellow]")
                if not Confirm.ask("Create profile?", default=True, console=console): console.print("[yellow]Cancelled.[/yellow]"); console.line(); continue
                browser_profile_disk_path = browser_manager.create_profile(browser_type=browser_type, profile_custom_name=profile_name, is_persistent=True, bookmarks_template_name=bookmarks_set, console=console)
                if not browser_profile_disk_path: console.print("[red]Failed to create browser profile directory.[/red]"); console.line(); continue
                new_profile_data = {"profile_name": profile_name, "browser_type": browser_type, "browser_profile_path": browser_profile_disk_path, "bookmarks_set_name": bookmarks_set, "created_at": datetime.now().isoformat()}
                profiles = config_manager.load_profiles_data(); profiles.append(new_profile_data)
                if config_manager.save_profiles_data(profiles, console=console): console.print(f"[green]Profile '[cyan]{profile_name}[/cyan]' created.[/green]")
                else:
                    console.print("[red]Failed to save profile metadata.[/red]")
                    if os.path.exists(browser_profile_disk_path): browser_manager.remove_profile(browser_profile_disk_path, console)      
            except Exception as e: console.print(f"[red]Error: {e}[/red]");
            console.line()
        elif sub_command == "delete":
            console.print(Rule("[red]Delete Persistent Profile[/red]", style="red"))
            profiles = config_manager.load_profiles_data()
            if not profiles: console.print("[yellow]No profiles to delete.[/yellow]"); console.line(); continue
            profile_choices = {str(i+1): p["profile_name"] for i, p in enumerate(profiles)}
            profile_choices[str(len(profiles)+1)] = "(Cancel)"
            for k, n in profile_choices.items(): console.print(f"  [cyan]{k}[/cyan]. {n}")
            choice_key = Prompt.ask("Select profile to DELETE:", choices=list(profile_choices.keys()), console=console).upper()
            if profile_choices.get(choice_key) == "(Cancel)": console.print("[yellow]Cancelled.[/yellow]"); console.line(); continue
            profile_name_to_delete = profile_choices.get(choice_key)
            profile_to_delete_data = config_manager.get_profile_by_name(profile_name_to_delete)
            if not profile_to_delete_data: console.print(f"[red]Profile '{profile_name_to_delete}' not found.[/red]"); console.line(); continue
            if Confirm.ask(f"DELETE profile '[bold red]{profile_name_to_delete}[/bold red]' and its browser data ({profile_to_delete_data.get('browser_profile_path','N/A')})?", default=False, console=console):
                browser_dir_path = profile_to_delete_data.get("browser_profile_path")
                if browser_dir_path and os.path.exists(browser_dir_path):
                    if browser_manager.remove_profile(browser_dir_path, console=console): console.print(f"  [green]Browser data deleted.[/green]")
                updated_profiles = [p for p in profiles if p["profile_name"] != profile_name_to_delete]
                if config_manager.save_profiles_data(updated_profiles, console=console):
                    console.print(f"  [green]Profile '{profile_name_to_delete}' removed from config.[/green]")
                    if CURRENT_SESSION_SETUP.get("gs_profile_name") == profile_name_to_delete:
                        CURRENT_SESSION_SETUP.update({"profile_type": "Temporary", "gs_profile_name": None, "browser_selected": None, "bookmarks_set": "default", "browser_profile_on_disk_path": None, "network_checks_status": "Pending"})
                        console.print("[yellow]Active session setup reset.[/yellow]")
            console.line()
        elif sub_command == "load":
            console.print(Rule("[green]Load Persistent Profile to Current Setup[/green]", style="green"))
            profiles = config_manager.load_profiles_data()
            if not profiles: console.print("[yellow]No profiles to load.[/yellow]"); console.line(); continue
            profile_choices = {str(i+1): p["profile_name"] for i, p in enumerate(profiles)}
            profile_choices[str(len(profiles)+1)] = "(Cancel)"
            for k, n in profile_choices.items():
                 browser = next((p['browser_type'] for p in profiles if p['profile_name'] == n), "N/A")
                 console.print(f"  [cyan]{k}[/cyan]. {n} ([italic dim]{browser.capitalize()}[/italic dim])")
            choice_key = Prompt.ask("Select profile to load:", choices=list(profile_choices.keys()), console=console).upper()
            if profile_choices.get(choice_key) == "(Cancel)": console.print("[yellow]Cancelled.[/yellow]"); console.line(); continue
            selected_profile_name = profile_choices.get(choice_key)
            profile_data = config_manager.get_profile_by_name(selected_profile_name)
            if profile_data:
                CURRENT_SESSION_SETUP["profile_type"] = "Persistent"; CURRENT_SESSION_SETUP["gs_profile_name"] = profile_data["profile_name"]
                CURRENT_SESSION_SETUP["browser_selected"] = profile_data["browser_type"]; CURRENT_SESSION_SETUP["bookmarks_set"] = profile_data.get("bookmarks_set_name")
                CURRENT_SESSION_SETUP["browser_profile_on_disk_path"] = profile_data["browser_profile_path"]; CURRENT_SESSION_SETUP["network_checks_status"] = "Pending"
                console.print(f"[green]Profile '[cyan]{selected_profile_name}[/cyan]' loaded to current setup.[/green]")
                console.print("[italic]Returning to main command prompt...[/italic]"); time.sleep(0.5); break 
            console.line()
        elif sub_command == "back":
            break 
        else: console.print("[red]Unknown profile command.[/red]"); console.line()

def handle_command_about_seq():
    console.print(Rule("[green]About Guardian Spy[/green]", style="green"))
    console.print(Panel(Text.from_markup(f"""[bold]{__app_name__} v{__version__}[/bold]
(Resto de la info...)"""),padding=(1,2), border_style="blue"))
    console.line()

# --- Bucle Principal Secuencial ---
def main_loop_sequential(cli_args):
    detected_browser_paths = utils.check_browser_executables(console=None if not DEBUG_MODE else console) 
    if not detected_browser_paths:
        # console.clear() # No limpiar aquí, solo imprimir error y salir
        display_initial_banner_and_app_info()
        console.print(Panel(Text.from_markup("[bold red]ERROR: No supported browsers found.[/bold red]"),padding=1))
        return 
    if cli_args: 
        if cli_args.browser and cli_args.browser in detected_browser_paths : CURRENT_SESSION_SETUP["browser_selected"] = cli_args.browser
        if cli_args.no_bookmarks: CURRENT_SESSION_SETUP["bookmarks_set"] = None
        elif cli_args.bookmarks: CURRENT_SESSION_SETUP["bookmarks_set"] = cli_args.bookmarks
    
    # Pantalla de bienvenida inicial
    console.clear() 
    display_initial_banner_and_app_info() 
    display_session_status_sequential() 
    display_command_menu_sequential() 

    while True:
        print("DEBUG: main_loop_sequential - Top of loop, before Prompt.ask", file=sys.stderr) 
        try:
            command_input = Prompt.ask(Text.from_markup("[bold deep_sky_blue1]GuardianSpy >[/bold deep_sky_blue1]"), console=console).strip().lower()
        except (KeyboardInterrupt, EOFError): command_input = "quit"
        
        print(f"DEBUG: main_loop_sequential - Command received: {command_input}", file=sys.stderr)
        
        # La salida de cada comando se añade debajo.
        # El comando "clear" explícito limpiará la pantalla.

        if command_input == "setup": handle_command_setup_seq(detected_browser_paths)
        elif command_input == "check": handle_command_check_seq()
        elif command_input == "launch": handle_command_launch_seq(detected_browser_paths)
        elif command_input == "profiles": 
            handle_command_profiles_seq(detected_browser_paths)
            # Después de salir de 'profiles', mostrar el menú principal de nuevo
            console.line() 
            display_session_status_sequential() 
            display_command_menu_sequential()
        elif command_input == "status": 
            display_session_status_sequential()
        elif command_input == "about": 
            handle_command_about_seq()
        elif command_input == "help": # CAMBIO: 'menu' a 'help'
            display_command_menu_sequential()
        elif command_input == "clear": # CAMBIO: Comando 'clear' NO se elimina
            console.clear() 
            display_initial_banner_and_app_info() 
            display_session_status_sequential() 
            display_command_menu_sequential() 
        elif command_input in ["quit", "exit", "q"]:
            if Confirm.ask("Are you sure you want to quit?", default=True, console=console):
                console.print(Rule("[blue]Exiting Guardian Spy. Stay safe![/blue]", style="blue"))
                sys.exit(0) # Salir directamente del programa
        elif not command_input: 
            pass # Si solo presiona Enter, no hacer nada, el prompt reaparece
        else:
            console.print(f"[red]Unknown command: '{command_input}'. Type 'help' for commands.[/red]")
        
        console.line() # Línea en blanco antes del siguiente prompt
        print("DEBUG: main_loop_sequential - End of loop iteration.", file=sys.stderr)


def start():
    print("DEBUG: main_cli.py - Entered start() function", file=sys.stderr)
    parser = argparse.ArgumentParser(add_help=False)
    info_group = parser.add_argument_group('Informational Arguments')
    info_group.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    info_group.add_argument("-h", "--help", action="store_true")
    info_group.add_argument("--check-setup", action="store_true")
    action_group = parser.add_argument_group('Session Setup Arguments')
    action_group.add_argument("-b", "--browser", choices=['firefox', 'chrome', 'chromium'])
    action_group.add_argument("--no-bookmarks", action="store_true")
    action_group.add_argument("--bookmarks", help="Specify bookmarks set name.")
    args, unknown_args = parser.parse_known_args()
    print(f"DEBUG: main_cli.py - Args parsed: {args}, Unknown: {unknown_args}", file=sys.stderr)

    if args.help:
        console.clear(); display_initial_banner_and_app_info() 
        console.print(Panel(Text.from_markup("""[bold]Guardian Spy CLI Options:[/bold]..."""),padding=1))
        sys.exit(0)
    if args.check_setup:
        console.clear(); display_initial_banner_and_app_info() 
        handle_command_check_seq() 
        Prompt.ask("Press Enter to exit.", default="",show_default=False,console=console)
        sys.exit(0) 
    if unknown_args:
        console.print(f"[yellow]Warning: Unrecognized arguments: {unknown_args}. These will be ignored.[/yellow]")
        console.print("[yellow]Please use the interactive command prompt. Type 'help' for commands.[/yellow]") # Cambiado a 'help'
        time.sleep(2)
    
    # El console.clear() principal se hace aquí, UNA VEZ al inicio del programa interactivo.
    # console.clear() # Ya no es necesario aquí, se hace en start() o al inicio de main_loop_sequential
    print("DEBUG: main_cli.py - About to call main_loop_sequential()", file=sys.stderr)
    main_loop_sequential(args) 
    print("DEBUG: main_cli.py - Returned from main_loop_sequential (this means quit was selected)", file=sys.stderr)


if __name__ == '__main__': 
    print("DEBUG: main_cli.py - Running as script (__main__)", file=sys.stderr)
    start()