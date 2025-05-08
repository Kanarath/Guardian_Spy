# guardian_spy/browser_manager.py
import subprocess
import platform
import os
import shutil
import tempfile
import time
# No need to import Console here if passed as an argument

# Default profile directory names used by browsers (less relevant for temp profiles in system temp dir)
# FIREFOX_PROFILE_DIR_NAME = ".mozilla/firefox" 
# CHROME_PROFILE_DIR_NAME_LINUX = ".config/google-chrome" 
# CHROME_PROFILE_DIR_NAME_MACOS = "Library/Application Support/Google/Chrome"
# CHROME_PROFILE_DIR_NAME_WINDOWS = "AppData/Local/Google/Chrome/User Data"

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
            # Common paths, shutil.which will check PATH too if these fail
            # Using raw strings for paths
            possible_paths = [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            return "firefox.exe" # Fallback to PATH
        elif system == "Darwin": # macOS
            path = "/Applications/Firefox.app/Contents/MacOS/firefox"
            if os.path.exists(path):
                return path
            return "firefox" # Fallback for custom installs or if not in default location
        else: # Linux, BSD, etc.
            return "firefox" # Assumes it's in PATH

    elif browser_type == "chrome": # This implies Google Chrome primarily
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
            return "Google Chrome" # Fallback to PATH (name might vary slightly)
        else: # Linux
            return "google-chrome" # Common name for Google Chrome package

    elif browser_type == "chromium": # For explicitly requesting Chromium
        if system == "Windows":
            # Chromium doesn't have a standard installer as much, often portable or custom builds
            # Suggest common names, user might need to ensure it's in PATH
            return "chrome.exe" # Often Chromium builds use 'chrome.exe' too
        elif system == "Darwin":
            # Similar to Windows, less standard install path
            # return "/Applications/Chromium.app/Contents/MacOS/Chromium" # A common community build path
            return "Chromium" # Name if installed via Homebrew cask or similar
        else: # Linux
            # Could be 'chromium-browser' or 'chromium'
            return "chromium-browser" # Debian/Ubuntu often use this
            # 'chromium' is used by Arch and others. check_browser_executables will try both.

    return None


def create_profile(browser_type, profile_name_prefix="gs_temp_profile", bookmarks_file=None, console=None):
    """
    Creates a new, isolated browser profile directory in the system's temporary location.

    Args:
        browser_type (str): "firefox" or "chrome" (or "chromium").
        profile_name_prefix (str): Prefix for the temporary profile directory.
        bookmarks_file (str, optional): Path to a bookmarks file to import.
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

        # Browser specific initialization if needed (e.g. creating subdirs for Chrome)
        if browser_type in ["chrome", "chromium"]:
            # Chrome expects certain subdirectories like 'Default' for some things,
            # but --user-data-dir should create what it needs.
            # For bookmarks, we'd place them in profile_path/Default/Bookmarks
            pass
        elif browser_type == "firefox":
            # Firefox will initialize the profile structure when launched with -profile.
            pass
        
        # TODO: Implement bookmark loading if bookmarks_file is provided
        # if bookmarks_file:
        #    load_bookmarks_to_profile(browser_type, profile_path, bookmarks_file, console=console)

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


def launch_browser_with_profile(browser_type_requested, profile_path, console=None):
    """
    Launches the specified browser with the given profile.
    It will try to find the actual executable path.

    Args:
        browser_type_requested (str): "firefox", "chrome", or "chromium".
        profile_path (str): Path to the profile directory.
        console (rich.console.Console, optional): For logging.

    Returns:
        subprocess.Popen object or None on failure.
    """
    from .utils import find_executable # Local import

    # Determine the actual browser type and executable based on what was found
    actual_browser_type = browser_type_requested
    browser_executable = None

    if browser_type_requested == "firefox":
        path_suggestion = get_os_specific_browser_path("firefox")
        if os.path.isabs(path_suggestion) and os.path.exists(path_suggestion):
            browser_executable = path_suggestion
        else:
            browser_executable = find_executable(path_suggestion)
    
    elif browser_type_requested == "chrome": # User selected "chrome"
        # Try Google Chrome first
        path_suggestion_gc = get_os_specific_browser_path("chrome")
        if os.path.isabs(path_suggestion_gc) and os.path.exists(path_suggestion_gc):
            browser_executable = path_suggestion_gc
        else:
            browser_executable = find_executable(path_suggestion_gc)
        
        if not browser_executable and platform.system() == "Linux": # If Google Chrome not found on Linux, try Chromium
            if console:
                console.log("[yellow]Google Chrome not found, trying Chromium as fallback for 'chrome' selection.[/yellow]")
            chromium_names = ["chromium-browser", "chromium"]
            for name in chromium_names:
                path_suggestion_cr = get_os_specific_browser_path("chromium", specific_name=name)
                browser_executable = find_executable(path_suggestion_cr)
                if browser_executable:
                    actual_browser_type = "chromium" # Update actual type
                    break
    
    elif browser_type_requested == "chromium": # User explicitly selected "chromium"
        chromium_names = ["chromium-browser", "chromium"] if platform.system() == "Linux" else [get_os_specific_browser_path("chromium")]
        for name in chromium_names:
            path_suggestion_cr = get_os_specific_browser_path("chromium", specific_name=name if platform.system() == "Linux" else None)
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
        # Consider adding --disable-extensions if you want a truly clean slate unless user loads some.
        # Consider --incognito as an alternative for Chrome if not managing full profiles, but user-data-dir is better for isolation.
    
    if not cmd:
        if console:
            console.log(f"[bold red]Unsupported browser type for launching: {actual_browser_type}[/bold red]")
        return None

    try:
        if console:
            console.log(f"Executing: {' '.join(cmd)}")
        # On Windows, Popen might need shell=True if paths have spaces and are not perfectly handled,
        # but it's generally safer to avoid shell=True. Python's list of args usually handles spaces.
        # For detached process or more control, consider creationflags on Windows (e.g., subprocess.CREATE_NEW_CONSOLE)
        process = subprocess.Popen(cmd)
        return process
    except FileNotFoundError: # Should be caught by find_executable, but as a fallback
        if console:
            console.log(f"[bold red]Error: {actual_browser_type} executable not found at '{browser_executable}'. Is it in your PATH?[/bold red]")
    except Exception as e:
        if console:
            console.log(f"[bold red]Error launching {actual_browser_type}: {e}[/bold red]")
    return None


def remove_profile(profile_path, console=None):
    """
    Removes the browser profile directory.

    Args:
        profile_path (str): Path to the profile directory.
        console (rich.console.Console, optional): For logging.

    Returns:
        bool: True if successful or path doesn't exist, False on error.
    """
    if not profile_path or not os.path.exists(profile_path):
        if console:
            # Using print directly if it's a simple info message not part of a status
            console.print(f"  [dim]Profile path '{profile_path}' does not exist or not provided. Nothing to remove.[/dim]")
        return True
    try:
        shutil.rmtree(profile_path)
        return True
    except Exception as e:
        if console:
            console.print(f"  [bold red][!] Error removing profile directory {profile_path}: {e}[/bold red]")
        return False

# TODO:
# def load_bookmarks_to_profile(browser_type, profile_path, bookmarks_source_file, console=None):
# ...