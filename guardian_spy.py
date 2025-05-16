#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Guardian Spy: OPSEC Assistant for OSINT Practioners.
Entry point for the Guardian Spy CLI application.
"""
import sys 
print("DEBUG: guardian_spy.py - Top of script", file=sys.stderr) # DEBUG 1

import os 
from datetime import datetime 
import traceback 

# Variable global para la instancia de consola, se intentará poblar desde main_cli
# Esto es para que los bloques except puedan intentar usarla si está disponible.
# Pero no debe causar un error si main_cli falla al importar.
effective_console_instance = sys.stderr # Fallback inicial

# --- Intento de Importación de Módulos Guardian Spy ---
print("DEBUG: guardian_spy.py - About to import guardian_spy specific modules", file=sys.stderr) # DEBUG 2
try:
    from guardian_spy import main_cli # Intenta importar el módulo primero
    print("DEBUG: guardian_spy.py - main_cli module imported successfully", file=sys.stderr) # DEBUG 3
    try:
        # Intentar obtener la consola de Rich desde main_cli DESPUÉS de importar main_cli
        if hasattr(main_cli, 'console') and main_cli.console is not None:
            effective_console_instance = main_cli.console
            print("DEBUG: guardian_spy.py - Rich console instance obtained from main_cli", file=sys.stderr) # DEBUG 4
        else:
            print("DEBUG: guardian_spy.py - main_cli.console not found or is None, using stderr", file=sys.stderr) # DEBUG 4b
    except Exception as e_console_fetch:
        print(f"DEBUG: guardian_spy.py - Error fetching console from main_cli: {e_console_fetch}, using stderr", file=sys.stderr) # DEBUG 4c

    from guardian_spy import DEBUG_MODE
    print(f"DEBUG: guardian_spy.py - DEBUG_MODE is {DEBUG_MODE}", file=sys.stderr) # DEBUG 5

except ImportError as e_import_gs:
    print(f"FATAL IMPORT ERROR in guardian_spy.py: Could not import core modules: {e_import_gs}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    # No podemos usar Rich console aquí porque la importación falló
    input("FATAL IMPORT ERROR. Press Enter to exit...") # Pausa para ver el error
    sys.exit(1)
except Exception as e_early_init: # Capturar otros errores durante la inicialización de imports
    print(f"FATAL EARLY INIT ERROR in guardian_spy.py: {e_early_init}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    input("FATAL EARLY INIT ERROR. Press Enter to exit...")
    sys.exit(1)
# --- Fin de Importaciones ---


if __name__ == "__main__":
    print("DEBUG: guardian_spy.py - Entered __main__ block", file=sys.stderr) # DEBUG 6
    
    def _print_error_banner_fallback(): # Para errores si Rich no está disponible
        print("="*50, file=sys.stderr)
        print(" GUARDIAN SPY - CRITICAL ERROR ".center(50, "="), file=sys.stderr)
        print("="*50, file=sys.stderr)

    try:
        print("DEBUG: guardian_spy.py - In __main__, about to call main_cli.start()", file=sys.stderr) # DEBUG 7
        main_cli.start() 
        print("DEBUG: guardian_spy.py - Returned from main_cli.start() (Program should have self-exited)", file=sys.stderr) # DEBUG 8

    except KeyboardInterrupt:
        # ... (bloque KeyboardInterrupt como antes, usando effective_console_instance) ...
        if hasattr(effective_console_instance, 'print') and effective_console_instance is not sys.stderr:
            if hasattr(effective_console_instance, 'clear'): effective_console_instance.clear()
            if hasattr(main_cli, 'display_initial_banner_and_app_info'): main_cli.display_initial_banner_and_app_info()
            effective_console_instance.print("\n[bold yellow]Guardian Spy session terminated by user.[/bold yellow]")
        else:
            print("\nGuardian Spy session terminated by user.", file=sys.stderr)
        sys.exit(130) 

    except SystemExit as e_sys_exit:
        print(f"DEBUG: guardian_spy.py - Caught SystemExit (code: {e_sys_exit.code}). Exiting.", file=sys.stderr) # DEBUG 9
        sys.exit(e_sys_exit.code if e_sys_exit.code is not None else 0)

    except Exception as e:
        print(f"DEBUG: guardian_spy.py - Caught UNHANDLED top-level Exception: {type(e).__name__}", file=sys.stderr) # DEBUG 10
        _print_error_banner_fallback()
        print(f"CRITICAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        
        error_log_path = os.path.join(os.path.expanduser("~"), "guardian_spy_crash.log")
        try:
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n--- CRASH AT {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                traceback.print_exc(file=f)
            print(f"Crash details logged to: {error_log_path}", file=sys.stderr)
        except Exception as log_e:
            print(f"Failed to write crash log: {log_e}", file=sys.stderr)

        if DEBUG_MODE:
            traceback.print_exc(file=sys.stderr) # Imprimir traceback a stderr si DEBUG_MODE
        
        input("Press Enter to exit...") # Pausar para ver el error
        sys.exit(1)

    finally:
        print("DEBUG: guardian_spy.py - Reached final 'finally' block.", file=sys.stderr) # DEBUG 11
        # El programa debería haber salido con sys.exit() antes de este punto en la mayoría de los casos.
        # Si llegamos aquí, es una salida "natural" del try block sin un exit explícito.
        pass