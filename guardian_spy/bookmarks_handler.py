# guardian_spy/bookmarks_handler.py
import os
import json
import time # Ya lo habías añadido, ¡gracias!
from typing import List, Dict, Optional, Tuple, Union # Para type hints

# Asumir que este script está en guardian_spy/ y assets/ está en la raíz del proyecto
try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError: 
    PROJECT_ROOT = os.getcwd() 

BOOKMARKS_DIR = os.path.join(PROJECT_ROOT, "assets", "bookmarks")

# Definir qué sets componen el "General OSINT" (nombres de archivo JSON)
GENERAL_OSINT_SETS = [
    "00_opsec_checks.json",
    "01_search_general.json",
    "04_domain_ip_web.json",
    "07_images_videos_files.json",
    "09_archives_historical.json"
]

def get_available_bookmark_sets(console=None) -> Dict[str, str]:
    """
    Escanea el directorio de bookmarks y devuelve un diccionario de sets disponibles.
    {"Nombre Amigable": "nombre_archivo.json"}
    """
    sets = {}
    if not os.path.isdir(BOOKMARKS_DIR):
        if console:
            console.print(f"[red]Bookmarks directory not found: {BOOKMARKS_DIR}[/red]")
        return sets
        
    for filename in sorted(os.listdir(BOOKMARKS_DIR)): # Ordenar para consistencia
        if filename.endswith(".json"):
            friendly_name = filename.replace(".json", "").replace("_", " ")
            # Quitar prefijos numéricos como "00 "
            if len(friendly_name) > 2 and friendly_name[2] == ' ' and friendly_name[:2].isdigit():
                 friendly_name = friendly_name[3:]
            friendly_name = friendly_name.title()
            sets[friendly_name] = filename 
    return sets

def load_bookmark_set_data(filename: str, console=None) -> Optional[List[Dict]]:
    """
    Carga los datos de bookmarks de un archivo JSON específico.
    """
    file_path = os.path.join(BOOKMARKS_DIR, filename)
    if not os.path.exists(file_path):
        if console:
            console.print(f"[red]Bookmark set file not found: {file_path}[/red]")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            valid_data = []
            for item in data:
                if isinstance(item, dict) and "name" in item and "url" in item:
                    valid_data.append(item)
                elif console and hasattr(console, 'log') and DEBUG_MODE: # Asumiendo DEBUG_MODE importado
                    console.log(f"[dim yellow]Warning: Invalid bookmark item in {filename}: {item}. Skipping.[/dim yellow]")
            return valid_data
        else:
            if console: console.print(f"[red]Error: Bookmark set file {filename} does not contain a list.[/red]")
            return None
    except json.JSONDecodeError:
        if console: console.print(f"[red]Error decoding JSON from: {filename}[/red]")
        return None
    except Exception as e:
        if console: console.print(f"[red]Unexpected error loading {filename}: {e}[/red]")
        return None

def load_multiple_bookmark_sets(
    set_identifiers: Union[str, List[str], None], 
    available_sets: Dict[str,str], # {"Friendly Name": "filename.json"}
    console=None
) -> List[Dict]:
    """
    Carga y combina bookmarks de múltiples sets.
    set_identifiers puede ser:
        - None: Ningún bookmark.
        - "__ALL__": Todos los sets disponibles.
        - "__GENERAL__": Los sets definidos en GENERAL_OSINT_SETS.
        - Una lista de nombres de archivo JSON de sets específicos.
        - Un solo nombre de archivo JSON.
    """
    combined_bookmarks = []
    filenames_to_load = []

    if set_identifiers == "__ALL__":
        filenames_to_load = list(available_sets.values())
        if console: console.print(f"[italic]Loading ALL {len(filenames_to_load)} bookmark sets...[/italic]")
    elif set_identifiers == "__GENERAL__":
        filenames_to_load = [f for f in GENERAL_OSINT_SETS if f in available_sets.values()]
        if console: console.print(f"[italic]Loading GENERAL OSINT ({len(filenames_to_load)} sets)...[/italic]")
    elif isinstance(set_identifiers, list):
        filenames_to_load = [f for f in set_identifiers if f in available_sets.values()]
        if console: console.print(f"[italic]Loading {len(filenames_to_load)} selected bookmark sets...[/italic]")
    elif isinstance(set_identifiers, str) and set_identifiers in available_sets.values(): # Un solo archivo
        filenames_to_load = [set_identifiers]
        if console: console.print(f"[italic]Loading bookmark set: {set_identifiers}...[/italic]")
    elif set_identifiers is None:
        if console: console.print("[italic]No bookmark sets selected to load.[/italic]")
        return [] # Ningún bookmark

    # Cargar y combinar, evitando duplicados por URL
    loaded_urls = set()
    for filename in filenames_to_load:
        data = load_bookmark_set_data(filename, console=console)
        if data:
            for bm in data:
                if bm.get("url") not in loaded_urls:
                    combined_bookmarks.append(bm)
                    loaded_urls.add(bm.get("url"))
    
    return combined_bookmarks


def generate_chrome_bookmarks_content(bookmarks_list: List[Dict]) -> Dict:
    # ... (sin cambios respecto a la última versión)
    bookmark_bar_children = []
    current_id = 5 
    import uuid # Asegurar que uuid está importado
    for bm in bookmarks_list:
        guid = str(uuid.uuid4())
        bookmark_bar_children.append({
            "date_added": str(int(time.time() * 1_000_000)), 
            "guid": guid, "id": str(current_id),
            "name": bm.get("name", "Unnamed Bookmark"),
            "type": "url", "url": bm.get("url", "#")
        })
        current_id += 1
    return {
       "checksum": "0", 
       "roots": {
          "bookmark_bar": {"children": bookmark_bar_children, "date_added": str(int(time.time() * 1_000_000)), "date_modified": str(int(time.time() * 1_000_000)), "guid": str(uuid.uuid4()), "id": "1", "name": "Bookmarks bar", "type": "folder"},
          "other": {"children": [], "date_added": "0", "date_modified": "0", "guid": str(uuid.uuid4()), "id": "2", "name": "Other bookmarks", "type": "folder"},
          "synced": {"children": [], "date_added": "0", "date_modified": "0", "guid": str(uuid.uuid4()), "id": "3", "name": "Mobile bookmarks", "type": "folder"}
       }, "version": 1
    }

def generate_firefox_bookmarks_html(bookmarks_list: List[Dict]) -> str:
    # ... (sin cambios respecto a la última versión)
    current_ts = int(time.time())
    html_content = f"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks Menu</H1>
<DL><p>
    <DT><H3 ADD_DATE="{current_ts}" LAST_MODIFIED="{current_ts}" PERSONAL_TOOLBAR_FOLDER="true">Bookmarks Toolbar</H3>
    <DL><p>
"""
    for bm in bookmarks_list:
        bm_ts = int(time.time()) 
        name_escaped = bm.get("name", "Unnamed").replace("&", "&").replace("<", "<").replace(">", ">")
        url_escaped = bm.get("url", "#").replace("&", "&")
        html_content += f'        <DT><A HREF="{url_escaped}" ADD_DATE="{bm_ts}" LAST_MODIFIED="{bm_ts}">{name_escaped}</A>\n'
    html_content += """    </DL><p>
</DL><p>
"""
    return html_content

# Importar DEBUG_MODE al final para evitar problemas de importación circular si bookmarks_handler es importado por __init__
try:
    from guardian_spy import DEBUG_MODE
except ImportError:
    DEBUG_MODE = False # Fallback

if __name__ == '__main__':
    # ... (código de prueba como antes)
    pass