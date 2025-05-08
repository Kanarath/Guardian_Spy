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

# guardian_spy/browser_manager.py
import subprocess
import platform
import os
import shutil
import tempfile
import time
import json # For loading/saving Chrome bookmarks if we get more advanced

# --- (get_os_specific_browser_path - sin cambios respecto a la última versión) ---
def get_os_specific_browser_path(browser_type, specific_name=None):
    """
    Gets the typical executable name or path for a browser based on OS.
    This function primarily *suggests* names to be found in PATH or common install locations.
    The actual existence check and PATH searching is better handled by shutil.which.

    Args:
        browser_type (str): "firefox", "chrome", or "chromium".
        specific_name (str, optional): A specific executable name to return, overriding defaults. Useful for Linux Chromium variants.

    Returns:
        str: A suggested executable name or path, or None.
    """
    system = platform.system()

    if specific_name: # If a specific name is provided, just return that.
        return specific_name

    if browser_type == "firefox":
        if system == "Windows":
            possible_paths = [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return "firefox.exe" 
        elif system == "Darwin": 
            path = "/Applications/Firefox.app/Contents/MacOS/firefox"
            if os.path.exists(path):
                return path
            return "firefox" 
        else: 
            return "firefox"

    elif browser_type == "chrome": 
        if system == "Windows":
            possible_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return "chrome.exe"
        elif system == "Darwin":
            path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            if os.path.exists(path):
                return path
            return "Google Chrome" 
        else: 
            return "google-chrome"

    elif browser_type == "chromium": 
        if system == "Windows":
            return "chrome.exe" 
        elif system == "Darwin":
            return "Chromium" 
        else: 
            return "chromium-browser" 
    return None

# --- (load_bookmarks_to_profile - NUEVA y MODIFICADA) ---
def load_bookmarks_to_profile(browser_type, profile_path, bookmarks_template_name, console=None):
    """
    Copies a predefined bookmarks file to the browser profile.

    Args:
        browser_type (str): "firefox", "chrome", or "chromium".
        profile_path (str): Path to the profile directory.
        bookmarks_template_name (str): Name of the template (e.g., "default").
                                      Expects files like assets/default_bookmarks_chrome.json
        console (rich.console.Console, optional): For logging.

    Returns:
        bool: True if successful, False otherwise.
    """
    # Determine template file path - assumes 'assets' dir is relative to script execution or a known base path
    # For robustness, construct path from this script's location or a passed-in assets_dir
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Goes up to guardian-spy project root
    assets_dir = os.path.join(base_dir, "assets")

    source_bookmarks_file = None
    dest_bookmarks_path = None

    if browser_type in ["chrome", "chromium"]:
        source_bookmarks_file = os.path.join(assets_dir, f"{bookmarks_template_name}_bookmarks_chrome.json")
        # Chrome bookmarks are in a 'Bookmarks' file in the Default profile dir (or first profile dir)
        # The profile_path IS the user-data-dir. Chrome creates 'Default' inside it.
        default_profile_dir = os.path.join(profile_path, "Default")
        os.makedirs(default_profile_dir, exist_ok=True) # Ensure 'Default' directory exists
        dest_bookmarks_path = os.path.join(default_profile_dir, "Bookmarks")
    elif browser_type == "firefox":
        source_bookmarks_file = os.path.join(assets_dir, f"{bookmarks_template_name}_bookmarks_firefox.html")
        # For Firefox, we copy the HTML file into the profile root.
        # User imports it manually. places.sqlite is too complex for MVP.
        dest_bookmarks_path = os.path.join(profile_path, "bookmarks_to_import.html") # Give it a clear name
    else:
        if console:
            console.log(f"[yellow]Bookmarks loading not supported for browser type: {browser_type}[/yellow]")
        return False

    if not os.path.exists(source_bookmarks_file):
        if console:
            console.log(f"[bold red]Bookmarks template file not found: {source_bookmarks_file}[/bold red]")
        return False

    try:
        shutil.copy(source_bookmarks_file, dest_bookmarks_path)
        if console:
            console.log(f"Copied bookmarks template to [cyan]{dest_bookmarks_path}[/cyan]")
        if browser_type == "firefox" and console:
            console.log("[yellow]For Firefox, please import '[italic]bookmarks_to_import.html[/italic]' manually from the Bookmarks Manager (Ctrl+Shift+O).[/yellow]")
        return True
    except Exception as e:
        if console:
            console.log(f"[bold red]Error copying bookmarks template: {e}[/bold red]")
        return False

# --- (create_profile - MODIFICADA para llamar a load_bookmarks) ---
def create_profile(browser_type, profile_name_prefix="gs_temp_profile", bookmarks_template_name=None, console=None):
    """
    Creates a new, isolated browser profile directory in the system's temporary location.
    Optionally loads bookmarks.

    Args:
        browser_type (str): "firefox" or "chrome" (or "chromium").
        profile_name_prefix (str): Prefix for the temporary profile directory.
        bookmarks_template_name (str, optional): Name of the bookmarks template to load (e.g., "default").
        console (rich.console.Console, optional): For logging.

    Returns:
        str: Path to the created profile directory, or None on failure.
    """
    base_temp_dir = os.path.join(tempfile.gettempdir(), "guardian_spy_profiles")
    os.makedirs(base_temp_dir, exist_ok=True)
    
    unique_suffix = str(int(time.time() * 1000))
    profile_dir_name = f"{profile_name_prefix}_{browser_type}_{unique_suffix}"
    profile_path = os.path.join(base_temp_dir, profile_dir_name)

    try:
        if os.path.exists(profile_path):
            if console:
                console.log(f"[yellow]Warning: Profile path {profile_path} already exists. Removing.[/yellow]")
            shutil.rmtree(profile_path)
        os.makedirs(profile_path, exist_ok=True)

        if console:
            console.log(f"Creating new profile for {browser_type} at: {profile_path}")

        # Load bookmarks if requested
        if bookmarks_template_name:
            if console:
                console.log(f"Attempting to load '{bookmarks_template_name}' bookmarks...")
            load_bookmarks_to_profile(browser_type, profile_path, bookmarks_template_name, console=console)
        
        return profile_path

    except Exception as e:
        if console:
            console.log(f"[bold red]Error creating profile directory for {browser_type} at {profile_path}: {e}[/bold red]")
        if os.path.exists(profile_path):
            try:
                shutil.rmtree(profile_path)
            except Exception as e_cleanup:
                if console:
                    console.log(f"[bold red]Error cleaning up partially created profile {profile_path}: {e_cleanup}[/bold red]")
        return None

# --- (launch_browser_with_profile - sin cambios respecto a la última versión) ---
def launch_browser_with_profile(browser_type_requested, profile_path, console=None):
    from .utils import find_executable 

    actual_browser_type = browser_type_requested
    browser_executable = None

    if browser_type_requested == "firefox":
        path_suggestion = get_os_specific_browser_path("firefox")
        if os.path.isabs(path_suggestion) and os.path.exists(path_suggestion):
            browser_executable = path_suggestion
        else:
            browser_executable = find_executable(path_suggestion)
    
    elif browser_type_requested == "chrome": 
        path_suggestion_gc = get_os_specific_browser_path("chrome")
        if os.path.isabs(path_suggestion_gc) and os.path.exists(path_suggestion_gc):
            browser_executable = path_suggestion_gc
        else:
            browser_executable = find_executable(path_suggestion_gc)
        
        if not browser_executable and platform.system() == "Linux": 
            if console:
                console.log("[yellow]Google Chrome not found, trying Chromium as fallback for 'chrome' selection.[/yellow]")
            chromium_names = ["chromium-browser", "chromium"]
            for name in chromium_names:
                path_suggestion_cr = get_os_specific_browser_path("chromium", specific_name=name)
                browser_executable = find_executable(path_suggestion_cr)
                if browser_executable:
                    actual_browser_type = "chromium" 
                    break
    
    elif browser_type_requested == "chromium": 
        chromium_names_to_try = []
        if platform.system() == "Linux":
            chromium_names_to_try = ["chromium-browser", "chromium"]
        else:
            # For Win/Mac, get_os_specific_browser_path("chromium") returns one suggestion
            suggestion = get_os_specific_browser_path("chromium")
            if suggestion:
                chromium_names_to_try.append(suggestion)

        for name in chromium_names_to_try:
            # If get_os_specific_browser_path already gives a specific name for non-Linux chromium,
            # we don't need to pass specific_name again unless it's for Linux variants.
            path_suggestion_cr = get_os_specific_browser_path("chromium", specific_name=name if platform.system() == "Linux" else None)
            if os.path.isabs(path_suggestion_cr) and os.path.exists(path_suggestion_cr): # if full path suggested
                 browser_executable = path_suggestion_cr
            else: # if just a name
                 browser_executable = find_executable(path_suggestion_cr)

            if browser_executable:
                actual_browser_type = "chromium"
                break


    if not browser_executable:
        if console:
            console.log(f"[bold red]Could not find executable for selected browser: {browser_type_requested}[/bold red]")
        return None

    cmd = []
    if actual_browser_type == "firefox":
        cmd = [browser_executable, "-profile", profile_path, "-new-instance", "-no-remote"]
    elif actual_browser_type in ["chrome", "chromium"]:
        cmd = [browser_executable, f"--user-data-dir={profile_path}", "--no-first-run", "--no-default-browser-check"]
    
    if not cmd:
        if console:
            console.log(f"[bold red]Unsupported browser type for launching: {actual_browser_type}[/bold red]")
        return None

    try:
        if console:
            console.log(f"Executing: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        return process
    except FileNotFoundError: 
        if console:
            console.log(f"[bold red]Error: {actual_browser_type} executable not found at '{browser_executable}'. Is it in your PATH?[/bold red]")
    except Exception as e:
        if console:
            console.log(f"[bold red]Error launching {actual_browser_type}: {e}[/bold red]")
    return None

# --- (remove_profile - sin cambios respecto a la última versión) ---
def remove_profile(profile_path, console=None):
    if not profile_path or not os.path.exists(profile_path):
        if console:
            console.print(f"  [dim]Profile path '{profile_path}' does not exist or not provided. Nothing to remove.[/dim]")
        return True
    try:
        shutil.rmtree(profile_path)
        return True
    except Exception as e:
        if console:
            console.print(f"  [bold red][!] Error removing profile directory {profile_path}: {e}[/bold red]")
        return False