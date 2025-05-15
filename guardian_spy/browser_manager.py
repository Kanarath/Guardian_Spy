# guardian_spy/browser_manager.py
import subprocess
import platform
import os
import shutil
import tempfile
import time
import json

from guardian_spy import DEBUG_MODE 
from . import config_manager 
from . import utils 

def get_os_specific_browser_path(browser_type, specific_name=None):
    # ... (código sin cambios)
    system = platform.system()
    if specific_name: return specific_name
    if browser_type == "firefox":
        if system == "Windows":
            for p in [r"C:\Program Files\Mozilla Firefox\firefox.exe", r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"]:
                if os.path.exists(p): return p
            return "firefox.exe" 
        elif system == "Darwin": path = "/Applications/Firefox.app/Contents/MacOS/firefox"; return path if os.path.exists(path) else "firefox"
        else: return "firefox"
    elif browser_type == "chrome": 
        if system == "Windows":
            for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
                if os.path.exists(p): return p
            return "chrome.exe"
        elif system == "Darwin": path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; return path if os.path.exists(path) else "Google Chrome"
        else: return "google-chrome"
    elif browser_type == "chromium": 
        if system == "Windows": return "chrome.exe" 
        elif system == "Darwin": return "Chromium" 
        else: return "chromium-browser" 
    return None

def load_bookmarks_to_profile(browser_type, profile_path, bookmarks_template_name, console=None):
    # ... (código sin cambios)
    bm_console_for_logs = console if DEBUG_MODE else None
    try:
        project_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(project_root_dir, "assets")
    except NameError: 
        assets_dir = "assets" 
        if bm_console_for_logs: bm_console_for_logs.log("[yellow]Warning: __file__ not defined for bookmarks path.[/yellow]")
    source_bookmarks_file, dest_bookmarks_path = None, None
    if browser_type in ["chrome", "chromium"]:
        source_bookmarks_file = os.path.join(assets_dir, f"{bookmarks_template_name}_bookmarks_chrome.json")
        default_profile_dir = os.path.join(profile_path, "Default")
        try: os.makedirs(default_profile_dir, exist_ok=True)
        except OSError as e: 
            if console: console.print(f"[bold red]Error creating 'Default' profile subdir: {e}[/bold red]"); return False
        dest_bookmarks_path = os.path.join(default_profile_dir, "Bookmarks")
    elif browser_type == "firefox":
        source_bookmarks_file = os.path.join(assets_dir, f"{bookmarks_template_name}_bookmarks_firefox.html")
        dest_bookmarks_path = os.path.join(profile_path, "bookmarks_to_import.html") 
    else:
        if bm_console_for_logs: bm_console_for_logs.log(f"[yellow]Bookmarks loading not supported for: {browser_type}[/yellow]")
        return False
    if not os.path.exists(source_bookmarks_file):
        if console: console.print(f"[bold red]Bookmarks template file not found: {source_bookmarks_file}[/bold red]")
        return False
    try:
        shutil.copy(source_bookmarks_file, dest_bookmarks_path)
        if bm_console_for_logs: bm_console_for_logs.log(f"Copied bookmarks template to [cyan]{dest_bookmarks_path}[/cyan]")
        if browser_type == "firefox" and console: 
            console.print("[yellow]For Firefox, please import '[italic]bookmarks_to_import.html[/italic]' manually via Bookmarks Manager (Ctrl+Shift+O).[/yellow]")
        return True
    except Exception as e:
        if console: console.print(f"[bold red]Error copying bookmarks template: {e}[/bold red]")
        return False

def create_profile(browser_type, 
                   profile_name_prefix="gs_temp_profile", 
                   profile_custom_name=None, 
                   is_persistent=False,      
                   bookmarks_template_name=None, 
                   console=None):
    # ... (código sin cambios)
    cp_console_for_logs = console if DEBUG_MODE else None
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
            if cp_console_for_logs:
                cp_console_for_logs.log(f"[yellow]Warning: Profile directory {profile_path} already exists. Removing and recreating.[/yellow]")
            shutil.rmtree(profile_path)
        os.makedirs(profile_path, exist_ok=True)
        if cp_console_for_logs:
            profile_type_str = "Persistent" if is_persistent else "Temporary"
            cp_console_for_logs.log(f"Creating new {profile_type_str} browser profile directory for {browser_type} at: {profile_path}")
        if bookmarks_template_name:
            if cp_console_for_logs:
                cp_console_for_logs.log(f"Attempting to load '{bookmarks_template_name}' bookmarks...")
            load_bookmarks_to_profile(browser_type, profile_path, bookmarks_template_name, console=console)
        return profile_path
    except Exception as e:
        if console: console.print(f"[bold red]Error creating browser profile directory at {profile_path}: {e}[/bold red]")
        if profile_path and os.path.exists(profile_path): 
            try: shutil.rmtree(profile_path)
            except Exception as e_clean:
                if cp_console_for_logs: cp_console_for_logs.log(f"[bold red]Error cleaning up {profile_path}: {e_clean}[/bold red]")
        return None

def launch_browser_with_profile(browser_type_requested, profile_path, console=None):
    # ... (código sin cambios)
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
    """Removes the browser profile directory with retries for robustness."""
    rp_console_for_logs = console if DEBUG_MODE else None
    if not profile_path or not os.path.exists(profile_path):
        if rp_console_for_logs:
            rp_console_for_logs.log(f"Profile directory not found or not specified: {profile_path}. Nothing to remove.")
        return True 
    
    max_retries = 5
    retry_delay = 0.5 # seconds

    for attempt in range(max_retries):
        try:
            shutil.rmtree(profile_path)
            if rp_console_for_logs:
                rp_console_for_logs.log(f"Successfully removed profile directory: {profile_path} (attempt {attempt+1})")
            return True 
        except PermissionError as e_perm: 
            if rp_console_for_logs:
                rp_console_for_logs.log(f"[dim yellow]Attempt {attempt+1}/{max_retries} to remove {profile_path} failed (in use). Retrying in {retry_delay}s... Error: {e_perm.winerror if hasattr(e_perm, 'winerror') else e_perm}[/dim yellow]")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else: 
                if console: 
                    console.print(f"[bold red][!] Error removing profile directory {profile_path} after {max_retries} attempts.[/bold red]")
                    console.print(f"    Reason: File still in use (e.g., {e_perm.filename}).")
                    console.print(f"    [yellow]Tip: Ensure the browser and related processes are completely closed. The directory might need manual deletion.[/yellow]")
                return False
        except OSError as e_os: # Capturar otros errores de OS como directorio no vacío por otras razones
            if rp_console_for_logs:
                 rp_console_for_logs.log(f"[dim yellow]Attempt {attempt+1}/{max_retries} to remove {profile_path} failed (OSError). Retrying in {retry_delay}s... Error: {e_os.errno}[/dim yellow]")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                if console: 
                    console.print(f"[bold red][!] Error removing profile directory {profile_path} after {max_retries} attempts.[/bold red]")
                    console.print(f"    Reason: {e_os}")
                return False
        except Exception as e: 
            if console: 
                console.print(f"[bold red][!] Unexpected error removing profile directory {profile_path}: {e}[/bold red]")
            if rp_console_for_logs:
                import traceback
                rp_console_for_logs.log(f"[dim red]{traceback.format_exc()}[/dim red]")
            return False # Salir del bucle de reintentos si es una excepción inesperada
            
    if rp_console_for_logs: # Si el bucle termina sin retornar True
        rp_console_for_logs.log(f"All {max_retries} retries failed for {profile_path}")
    return False 