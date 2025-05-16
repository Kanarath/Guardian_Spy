# guardian_spy/browser_manager.py
# ... (imports como antes) ...
from . import bookmarks_handler # Asegurar que está importado

# ... (get_os_specific_browser_path como antes) ...

# MODIFICADA: load_bookmarks_to_profile
def load_bookmarks_to_profile(
    browser_type: str, 
    profile_path: str, 
    # Ahora toma la lista combinada de bookmarks, no un nombre de archivo de set
    combined_bookmarks_data: List[Dict], 
    console=None
):
    """
    Genera y escribe el archivo de bookmarks apropiado (Chrome/Firefox)
    a partir de una lista de datos de bookmarks ya cargada y combinada.
    """
    bm_console_for_logs = console if DEBUG_MODE else None

    if not combined_bookmarks_data: # Si la lista está vacía
        if bm_console_for_logs: bm_console_for_logs.log("[dim]No bookmark data provided to write to profile.[/dim]")
        return True # No es un error, simplemente no hay nada que escribir

    dest_path = None
    content_to_write = ""
    write_mode = "w"

    if browser_type in ["chrome", "chromium"]:
        default_profile_dir = os.path.join(profile_path, "Default")
        try: os.makedirs(default_profile_dir, exist_ok=True)
        except OSError as e:
            if console: console.print(f"[bold red]Error creating 'Default' subdir: {e}[/bold red]"); return False
        dest_path = os.path.join(default_profile_dir, "Bookmarks")
        chrome_json_content = bookmarks_handler.generate_chrome_bookmarks_content(combined_bookmarks_data)
        content_to_write = json.dumps(chrome_json_content, indent=4)
    elif browser_type == "firefox":
        dest_path = os.path.join(profile_path, "bookmarks_to_import.html")
        content_to_write = bookmarks_handler.generate_firefox_bookmarks_html(combined_bookmarks_data)
    else:
        if bm_console_for_logs: bm_console_for_logs.log(f"[yellow]Bookmarks writing not implemented for: {browser_type}[/yellow]")
        return False

    try:
        with open(dest_path, write_mode, encoding="utf-8") as f: f.write(content_to_write)
        if bm_console_for_logs: bm_console_for_logs.log(f"Bookmarks written to [cyan]{dest_path}[/cyan]")
        if browser_type == "firefox" and console: 
            console.print("[yellow]For Firefox, import '[italic]bookmarks_to_import.html[/italic]' manually (Ctrl+Shift+O).[/yellow]")
        return True
    except Exception as e:
        if console: console.print(f"[bold red]Error writing bookmarks to {dest_path}: {e}[/bold red]")
        return False

# create_profile ahora usa bookmark_set_identifier
def create_profile(browser_type: str, 
                   profile_name_prefix: str ="gs_temp_profile", 
                   profile_custom_name: Optional[str]=None, 
                   is_persistent: bool =False,      
                   # Ahora es un identificador de set, lista de sets, o flag especial
                   bookmark_set_identifier: Union[str, List[str], None] = None, 
                   console=None):
    cp_console_for_logs = console if DEBUG_MODE else None
    # ... (lógica de creación de path como antes) ...
    profile_path = None
    if is_persistent:
        if not profile_custom_name:
            if console: console.print("[bold red]Error: Custom name required for persistent profile.[/bold red]")
            return None
        base_dir = config_manager.get_browser_profiles_base_dir() 
        profile_dir_name = profile_custom_name 
        profile_path = os.path.join(base_dir, profile_dir_name)
        if cp_console_for_logs: cp_console_for_logs.log(f"Persistent browser profile directory target: {profile_path}")
    else: 
        base_dir = os.path.join(tempfile.gettempdir(), "guardian_spy_browser_profiles")
        try: os.makedirs(base_dir, exist_ok=True)
        except OSError as e:
            if console: console.print(f"[bold red]Error creating base temp dir {base_dir}: {e}[/bold red]"); return None
        unique_suffix = str(int(time.time() * 1000))
        profile_dir_name = f"{profile_name_prefix}_{browser_type}_{unique_suffix}"
        profile_path = os.path.join(base_dir, profile_dir_name)
        if cp_console_for_logs: cp_console_for_logs.log(f"Temporary browser profile directory target: {profile_path}")

    try:
        if os.path.exists(profile_path):
            if cp_console_for_logs: cp_console_for_logs.log(f"[yellow]Warning: Profile directory {profile_path} already exists. Removing and recreating.[/yellow]")
            shutil.rmtree(profile_path)
        os.makedirs(profile_path, exist_ok=True)
        if cp_console_for_logs:
            profile_type_str = "Persistent" if is_persistent else "Temporary"
            cp_console_for_logs.log(f"Creating new {profile_type_str} browser profile directory for {browser_type} at: {profile_path}")
        
        if bookmark_set_identifier is not None: # Si es None, no se cargan bookmarks
            if cp_console_for_logs: cp_console_for_logs.log(f"Attempting to load bookmarks for identifier: '{bookmark_set_identifier}'...")
            
            # Cargar todos los sets de bookmarks disponibles para pasarlos a load_multiple_bookmark_sets
            # Esto es un poco ineficiente si solo cargamos uno, pero simplifica la lógica
            all_available_sets = bookmarks_handler.get_available_bookmark_sets(console=console)
            
            combined_data = bookmarks_handler.load_multiple_bookmark_sets(
                bookmark_set_identifier, 
                all_available_sets, # Pasar el diccionario de todos los sets disponibles
                console=console
            )
            if combined_data: # Solo intentar escribir si hay datos
                load_bookmarks_to_profile(browser_type, profile_path, combined_data, console=console)
            elif bookmark_set_identifier is not None and cp_console_for_logs: # Si se especificó un set pero no se cargó nada
                 cp_console_for_logs.log(f"[yellow]No valid bookmarks found for identifier '{bookmark_set_identifier}'. No bookmarks loaded.[/yellow]")
        
        return profile_path
    except Exception as e:
        # ... (manejo de error como antes) ...
        if console: console.print(f"[bold red]Error creating browser profile directory at {profile_path}: {e}[/bold red]")
        if profile_path and os.path.exists(profile_path): 
            try: shutil.rmtree(profile_path)
            except Exception as e_clean:
                if cp_console_for_logs: cp_console_for_logs.log(f"[bold red]Error cleaning up {profile_path}: {e_clean}[/bold red]")
        return None

# ... (launch_browser_with_profile y remove_profile como antes) ...
def launch_browser_with_profile(browser_type_requested, profile_path, console=None):
    lp_console_for_logs = console if DEBUG_MODE else None
    actual_browser_type = browser_type_requested
    browser_executable = None
    if browser_type_requested == "firefox":
        path_suggestion = get_os_specific_browser_path("firefox")
        if os.path.isabs(path_suggestion) and os.path.exists(path_suggestion): browser_executable = path_suggestion
        else: browser_executable = utils.find_executable(path_suggestion)
    elif browser_type_requested == "chrome": 
        path_suggestion_gc = get_os_specific_browser_path("chrome")
        if os.path.isabs(path_suggestion_gc) and os.path.exists(path_suggestion_gc): browser_executable = path_suggestion_gc
        else: browser_executable = utils.find_executable(path_suggestion_gc)
        if not browser_executable and platform.system() == "Linux": 
            if lp_console_for_logs: lp_console_for_logs.log("[yellow]GC not found, trying Chromium.[/yellow]")
            for name in ["chromium-browser", "chromium"]:
                browser_executable = utils.find_executable(name)
                if browser_executable: actual_browser_type = "chromium"; break
    elif browser_type_requested == "chromium": 
        names_to_try = ["chromium-browser", "chromium"] if platform.system() == "Linux" else [get_os_specific_browser_path("chromium")]
        for name in names_to_try:
            browser_executable = utils.find_executable(name)
            if browser_executable: actual_browser_type = "chromium"; break
    if not browser_executable:
        if console: console.print(f"[bold red]Could not find executable for: {browser_type_requested}[/bold red]")
        return None
    cmd = []
    if actual_browser_type == "firefox": cmd = [browser_executable, "-profile", profile_path, "-new-instance", "-no-remote"]
    elif actual_browser_type in ["chrome", "chromium"]: cmd = [browser_executable, f"--user-data-dir={profile_path}", "--no-first-run", "--no-default-browser-check"]
    if not cmd:
        if console: console.print(f"[bold red]Unsupported browser for launch: {actual_browser_type}[/bold red]")
        return None
    try:
        if lp_console_for_logs: lp_console_for_logs.log(f"Executing: {' '.join(cmd)}")
        creationflags = 0
        if platform.system() == "Windows": creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) 
        process = subprocess.Popen(cmd, creationflags=creationflags)
        return process
    except FileNotFoundError: 
        if console: console.print(f"[bold red]Error: {actual_browser_type} executable not found at '{browser_executable}'.[/bold red]")
    except Exception as e:
        if console: console.print(f"[bold red]Error launching {actual_browser_type}: {e}[/bold red]")
    return None

def remove_profile(profile_path, console=None):
    rp_console_for_logs = console if DEBUG_MODE else None
    if not profile_path or not os.path.exists(profile_path):
        if rp_console_for_logs: rp_console_for_logs.log(f"Profile dir not found: {profile_path}.")
        return True 
    max_retries = 5; retry_delay = 0.5
    for attempt in range(max_retries):
        try:
            shutil.rmtree(profile_path)
            if rp_console_for_logs: rp_console_for_logs.log(f"Removed profile dir: {profile_path} (attempt {attempt+1})")
            return True 
        except PermissionError as e_perm: 
            if rp_console_for_logs: rp_console_for_logs.log(f"[dim y]Attempt {attempt+1} remove {profile_path} failed (in use). Retrying... Err: {e_perm.winerror if hasattr(e_perm, 'winerror') else e_perm}[/dim y]")
            if attempt < max_retries - 1: time.sleep(retry_delay)
            else: 
                if console: 
                    console.print(f"[bold red][!] Error removing {profile_path} after {max_retries} attempts.[/bold red]")
                    console.print(f"    Reason: File in use (e.g., {e_perm.filename}). Manual deletion may be needed.[/yellow]")
                return False
        except OSError as e_os:
            if rp_console_for_logs: rp_console_for_logs.log(f"[dim y]Attempt {attempt+1} remove {profile_path} failed (OSError). Retrying... Err: {e_os.errno}[/dim y]")
            if attempt < max_retries - 1: time.sleep(retry_delay)
            else:
                if console: console.print(f"[bold red][!] Error removing {profile_path}: {e_os}[/bold red]")
                return False
        except Exception as e: 
            if console: console.print(f"[bold red][!] Unexpected error removing {profile_path}: {e}[/bold red]")
            if rp_console_for_logs: import traceback; rp_console_for_logs.log(f"[dim r]{traceback.format_exc()}[/dim r]")
            return False
    if rp_console_for_logs: rp_console_for_logs.log(f"All {max_retries} retries failed for {profile_path}")
    return False 