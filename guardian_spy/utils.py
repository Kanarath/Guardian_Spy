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

# guardian_spy/utils.py
import platform
import os
import shutil # Para shutil.which

def get_user_home_dir():
    """Returns the user's home directory."""
    return os.path.expanduser("~")

def get_os_type():
    """Returns a simplified OS type string: 'windows', 'macos', 'linux', 'unknown'."""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    elif system == "Linux":
        return "linux"
    else:
        return "unknown"

def find_executable(name):
    """Cross-platform way to find an executable in PATH."""
    return shutil.which(name)

def check_browser_executables(console=None):
    """Checks for Firefox and Chrome/Chromium executables and prints their paths if found."""
    # Import locally to avoid circular dependencies if utils is imported early by browser_manager
    # This assumes browser_manager.py exists in the same directory or package.
    # If Guardian Spy grows, a more structured import might be needed.
    from . import browser_manager 

    if console:
        console.print("\n[bold gold1]Checking Browser Executables:[/bold gold1]")
    
    browsers_found = {}
    detected_paths = {} # To store the actual found path for later use if needed

    # --- Check Firefox ---
    firefox_path_suggestion = browser_manager.get_os_specific_browser_path("firefox")
    firefox_exe = None
    if firefox_path_suggestion:
        # If the suggestion is an absolute path, check if it exists
        if os.path.isabs(firefox_path_suggestion) and os.path.exists(firefox_path_suggestion):
            firefox_exe = firefox_path_suggestion
        else: # It's a name like 'firefox', try to find it in PATH
            firefox_exe = find_executable(firefox_path_suggestion)

    if firefox_exe:
        browsers_found["firefox"] = True
        detected_paths["firefox"] = firefox_exe
        if console:
            console.print(f"  [green]:heavy_check_mark: Firefox found at:[/green] [cyan]{firefox_exe}[/cyan]")
    else:
        browsers_found["firefox"] = False
        if console:
            console.print(f"  [red]:x: Firefox executable ('{firefox_path_suggestion or 'firefox'}') not found in common locations or PATH.[/red]")

    # --- Check Chrome / Chromium ---
    # Try 'chrome' first (which get_os_specific_browser_path should return for chrome type)
    chrome_path_suggestion = browser_manager.get_os_specific_browser_path("chrome")
    chrome_exe = None
    if chrome_path_suggestion:
        if os.path.isabs(chrome_path_suggestion) and os.path.exists(chrome_path_suggestion):
            chrome_exe = chrome_path_suggestion
        else:
            # .split()[0] in case the suggestion includes arguments (though it shouldn't from get_os_specific_browser_path)
            chrome_exe = find_executable(chrome_path_suggestion.split()[0]) 

    if chrome_exe:
        browsers_found["chrome"] = True # Generic "chrome" even if it's chromium found via google-chrome alias
        detected_paths["chrome"] = chrome_exe
        if console:
            console.print(f"  [green]:heavy_check_mark: Google Chrome found at:[/green] [cyan]{chrome_exe}[/cyan]")
    else:
        # If 'google-chrome' (or platform specific default) failed, try for 'chromium' specifically on Linux
        browsers_found["chrome"] = False # Explicitly set to false before trying chromium
        if platform.system() == "Linux":
            if console:
                 console.print(f"  [yellow]:information_source: Google Chrome ('{chrome_path_suggestion or 'google-chrome'}') not found. Checking for Chromium...[/yellow]")
            
            chromium_names = ["chromium-browser", "chromium"]
            chromium_exe_found = None
            for name in chromium_names:
                chromium_path_suggestion_alt = browser_manager.get_os_specific_browser_path("chromium", specific_name=name)
                chromium_exe_alt = find_executable(chromium_path_suggestion_alt)
                if chromium_exe_alt:
                    chromium_exe_found = chromium_exe_alt
                    break # Found one

            if chromium_exe_found:
                browsers_found["chromium"] = True # Mark that chromium was found
                detected_paths["chromium"] = chromium_exe_found
                if console:
                    console.print(f"  [green]:heavy_check_mark: Chromium found at:[/green] [cyan]{chromium_exe_found}[/cyan]")
            else:
                browsers_found["chromium"] = False
                if console:
                    console.print(f"  [red]:x: Chromium (tried {', '.join(chromium_names)}) also not found in PATH.[/red]")
        elif console: # If not Linux and chrome_exe was not found
             console.print(f"  [red]:x: Google Chrome executable ('{chrome_path_suggestion or 'chrome'}') not found in common locations or PATH.[/red]")


    if not any(browsers_found.values()) and console: # If no browser at all was found
        console.print("[bold red]No supported browsers detected automatically.[/bold red]")
        console.print("[yellow]You might need to ensure Firefox or Chrome/Chromium is installed and in your system's PATH,[/yellow]")
        console.print("[yellow]or configure paths manually (feature not yet implemented).[/yellow]")
    
    return detected_paths # Return a dict of found paths: {'firefox': '/path/to/ff', 'chrome': '/path/to/chrome'}