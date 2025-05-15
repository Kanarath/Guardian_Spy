#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Guardian Spy: OPSEC Assistant for OSINT Practioners.
Entry point for the Guardian Spy CLI application.
"""
import sys 
print("DEBUG: guardian_spy.py - Script started", file=sys.stderr)

import os 
from datetime import datetime 
import traceback 

try:
    print("DEBUG: guardian_spy.py - Attempting to import main_cli", file=sys.stderr)
    from guardian_spy import main_cli 
    print("DEBUG: guardian_spy.py - main_cli imported", file=sys.stderr)
    try:
        print("DEBUG: guardian_spy.py - Attempting to import console from main_cli", file=sys.stderr)
        # Acceder a la consola de main_cli de forma segura
        console_instance = getattr(main_cli, 'console', None)
        print(f"DEBUG: guardian_spy.py - console from main_cli is {'present' if console_instance else 'None'}", file=sys.stderr)
    except ImportError: 
        print("DEBUG: guardian_spy.py - Failed to import console from main_cli during initial import, setting to None", file=sys.stderr)
        console_instance = None 
except ImportError as e_import_main:
    print(f"FATAL ERROR: Could not import main application module (main_cli.py): {e_import_main}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

print("DEBUG: guardian_spy.py - Attempting to import DEBUG_MODE", file=sys.stderr)
from guardian_spy import DEBUG_MODE 
print(f"DEBUG: guardian_spy.py - DEBUG_MODE is {DEBUG_MODE}", file=sys.stderr)

if __name__ == "__main__":
    print("DEBUG: guardian_spy.py - Entered __main__ block", file=sys.stderr)
    
    # Usar console_instance que obtuvimos arriba de forma segura
    cli_console = console_instance 

    def _minimal_banner_for_error(): # Banner simple si Rich falla o no está listo
        print("="*40, file=sys.stderr)
        print(" GUARDIAN SPY - ERROR ".center(40, "="), file=sys.stderr)
        print("="*40, file=sys.stderr)

    try:
        print("DEBUG: guardian_spy.py - About to call main_cli.start()", file=sys.stderr)
        main_cli.start() 
        print("DEBUG: guardian_spy.py - Returned from main_cli.start() (Program should have exited via sys.exit within main_cli)", file=sys.stderr)

    except KeyboardInterrupt:
        if cli_console and hasattr(cli_console, 'print'):
            if hasattr(cli_console, 'clear'): cli_console.clear()
            if hasattr(main_cli, 'display_banner_kis'): main_cli.display_banner_kis() # Intentar mostrar banner si está disponible
            cli_console.print("\n[bold yellow]Guardian Spy session terminated by user.[/bold yellow]")
        else:
            print("\nGuardian Spy session terminated by user.", file=sys.stderr)
        
        try:
            if hasattr(main_cli, 'CURRENT_SESSION_SETUP') and \
               main_cli.CURRENT_SESSION_SETUP.get("is_temp_profile") and \
               main_cli.CURRENT_SESSION_SETUP.get("browser_profile_on_disk_path") and \
               os.path.exists(main_cli.CURRENT_SESSION_SETUP["browser_profile_on_disk_path"]):
                profile_to_clean = main_cli.CURRENT_SESSION_SETUP["browser_profile_on_disk_path"]
                print(f"[Cleanup] Attempting final cleanup of: {profile_to_clean}", file=sys.stderr)
                if hasattr(main_cli, 'browser_manager'):
                    main_cli.browser_manager.remove_profile(profile_to_clean, console=cli_console)
        except Exception as e_final_cleanup:
            if DEBUG_MODE: print(f"[Debug] Error during final KbdInterrupt cleanup: {e_final_cleanup}", file=sys.stderr)
        sys.exit(130) 

    except SystemExit as e_sys_exit:
        print(f"DEBUG: guardian_spy.py - Caught SystemExit with code: {e_sys_exit.code}", file=sys.stderr)
        # El mensaje de "Exiting" se manejará en finally si es necesario, o el programa simplemente saldrá.
        sys.exit(e_sys_exit.code if e_sys_exit.code is not None else 0)

    except Exception as e:
        print("DEBUG: guardian_spy.py - Caught top-level Exception", file=sys.stderr)
        error_log_path = os.path.join(os.path.expanduser("~"), "guardian_spy_crash.log")
        timestamp_err = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg_written = False
        try:
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n--- CRASH AT {timestamp_err} ---\n")
                traceback.print_exc(file=f)
            log_msg = f"Crash details logged to: {error_log_path}"
            log_msg_written = True
        except Exception as log_e:
            log_msg = f"Failed to write crash log: {log_e}"
        
        _minimal_banner_for_error() # Banner simple para errores
        
        if cli_console and hasattr(cli_console, 'print_exception') and DEBUG_MODE:
            cli_console.print(f"[bold red]\nCRITICAL ERROR:[/bold red]")
            cli_console.print_exception(show_locals=True, word_wrap=True, max_frames=10)
        elif cli_console and hasattr(cli_console, 'print'):
            cli_console.print(f"[bold red]\nCRITICAL ERROR.[/bold red]")
            cli_console.print(f"[yellow]Type:[/yellow] {type(e).__name__}")
            cli_console.print(f"[yellow]Msg:[/yellow] {str(e)[:500]}")
        else: 
            print(f"\nCRITICAL ERROR: {type(e).__name__}: {e}", file=sys.stderr)
            traceback.print_exc() 
        
        if cli_console and hasattr(cli_console, 'print'):
            if log_msg_written: cli_console.print(f"\n[bold]Log:[/bold] [cyan]{error_log_path}[/cyan]")
            else: cli_console.print(f"\n[bold red]{log_msg}[/bold red]")
            if not DEBUG_MODE: cli_console.print("\n[italic]Set DEBUG_MODE=True in __init__.py for more console output.[/italic]")
            cli_console.input("Press Enter to exit...") # Pausar para ver el error
        else:
            print(log_msg, file=sys.stderr)
            input("Press Enter to exit...")
        sys.exit(1)

    finally:
        print("DEBUG: guardian_spy.py - Entering guardian_spy.py finally block", file=sys.stderr)
        # El mensaje de "Exiting" se imprime desde main_cli o aquí si hay un error muy temprano
        # No imprimir doble si ya se salió con sys.exit()
        # Este finally se ejecuta incluso después de sys.exit() en algunos casos,
        # por lo que es mejor manejar los mensajes de salida dentro de los bloques try/except.
        # print("\nGuardian Spy is exiting (from guardian_spy.py finally).", file=sys.stderr)
        pass # Dejar que el flujo de salida natural o sys.exit() manejen el final.