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


# guardian_spy/config_manager.py
import os
import platform
import json
import shutil # Para eliminar directorios de perfiles de navegador
from datetime import datetime

APP_NAME = "GuardianSpy" # O el nombre que prefieras para el directorio de config

def get_config_dir():
    """
    Returns the application's configuration directory path based on OS.
    Creates the directory if it doesn't exist.
    """
    system = platform.system()
    if system == "Windows":
        # %APPDATA%\GuardianSpy
        path = os.path.join(os.environ.get("APPDATA", ""), APP_NAME)
    elif system == "Darwin": # macOS
        # ~/Library/Application Support/GuardianSpy
        path = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else: # Linux and other Unix-like
        # ~/.config/guardian_spy (o APP_NAME)
        # Usamos minúsculas para Linux según convención
        path = os.path.join(os.path.expanduser("~"), ".config", APP_NAME.lower())
    
    os.makedirs(path, exist_ok=True)
    return path

def get_browser_profiles_base_dir():
    """
    Returns the base directory where persistent browser profiles will be stored.
    Creates the directory if it doesn't exist.
    E.g., ~/.config/guardian_spy/browser_profiles/
    """
    config_dir = get_config_dir()
    profiles_base_dir = os.path.join(config_dir, "browser_profiles")
    os.makedirs(profiles_base_dir, exist_ok=True)
    return profiles_base_dir

def _get_profiles_data_file_path():
    """Returns the full path to the profiles.json data file."""
    config_dir = get_config_dir()
    return os.path.join(config_dir, "profiles.json")

def load_profiles_data():
    """
    Loads the list of persistent profiles from profiles.json.
    Returns an empty list if the file doesn't exist or is invalid.
    """
    profiles_file = _get_profiles_data_file_path()
    if not os.path.exists(profiles_file):
        return []
    try:
        with open(profiles_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Validar que sea una lista (podría ser un archivo JSON corrupto)
            if isinstance(data, list):
                return data
            else:
                # console.log(f"[Warning] profiles.json does not contain a list. Returning empty list.") # Necesitaría pasar console
                print(f"[GuardianSpy Warning] profiles.json data is not a list. Re-initializing.")
                return []
    except json.JSONDecodeError:
        # console.log(f"[Warning] profiles.json is corrupted. Returning empty list.") # Necesitaría pasar console
        print(f"[GuardianSpy Warning] profiles.json is corrupted. Re-initializing.")
        return [] # Si el JSON está corrupto, tratar como si no hubiera perfiles
    except Exception as e:
        print(f"[GuardianSpy Error] Failed to load profiles data: {e}")
        return []

def save_profiles_data(profiles_list, console=None):
    """
    Saves the list of persistent profiles to profiles.json.

    Args:
        profiles_list (list): The list of profile dictionaries to save.
        console (rich.console.Console, optional): For logging.
    Returns:
        bool: True if successful, False otherwise.
    """
    profiles_file = _get_profiles_data_file_path()
    try:
        with open(profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles_list, f, indent=4, ensure_ascii=False)
        if console:
            console.log(f"Profiles data saved to {profiles_file}")
        return True
    except Exception as e:
        if console:
            console.log(f"[bold red]Error saving profiles data to {profiles_file}: {e}[/bold red]")
        else: # Si no hay consola, imprimir al stderr
            print(f"[GuardianSpy Error] Failed to save profiles data: {e}", file=sys.stderr)
        return False

def get_profile_by_name(profile_name, console=None):
    """
    Retrieves a specific profile by its name.

    Args:
        profile_name (str): The name of the profile to find.
        console (rich.console.Console, optional): For logging.

    Returns:
        dict: The profile dictionary if found, else None.
    """
    profiles = load_profiles_data()
    for profile in profiles:
        if profile.get("profile_name") == profile_name:
            return profile
    if console:
        console.log(f"Profile '{profile_name}' not found.")
    return None

# --- Funciones para gestionar perfiles (Añadir, Eliminar, etc.) ---
# Las implementaremos en los siguientes pasos.
# Por ahora, tenemos la base para cargar y guardar.

if __name__ == '__main__':
    # Pequeña prueba para verificar las rutas y la carga/guardado (ejecutar directamente config_manager.py)
    print(f"Config Directory: {get_config_dir()}")
    print(f"Browser Profiles Base Directory: {get_browser_profiles_base_dir()}")
    print(f"Profiles Data File: {_get_profiles_data_file_path()}")
    
    test_profiles = load_profiles_data()
    print(f"Loaded profiles: {test_profiles}")
    
    # Ejemplo de añadir un perfil (esto se haría de forma más estructurada)
    # test_profiles.append({
    #     "profile_name": "test_profile_1",
    #     "browser_type": "firefox",
    #     "browser_profile_path": os.path.join(get_browser_profiles_base_dir(), "test_profile_1_ff"),
    #     "bookmarks_set_name": "default",
    #     "created_at": datetime.now().isoformat()
    # })
    # save_profiles_data(test_profiles)
    # print(f"Saved profiles: {load_profiles_data()}")