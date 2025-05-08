# guardian_spy/network_checker.py
# ... (imports) ...

def get_public_ip_info(console=None): # Added console parameter
    # ...
    try:
        # ...
        pass
    except requests.exceptions.RequestException as e:
        if console:
            console.log(f"[dim]Error fetching public IP from {DEFAULT_IP_SERVICE}: {e}[/dim]")
        # ... (fallback logic) ...
            if console: # If fallback also fails
                 console.log(f"[dim]Error fetching public IP from fallback service: {e_fallback}[/dim]")
        return None, None
    # ... (geo_info logic) ...
    except requests.exceptions.RequestException as e:
        if console:
            console.log(f"[dim]Error fetching geolocation data for {public_ip}: {e}[/dim]")
    return public_ip, geo_info

def get_dns_servers(console=None): # Added console parameter
    # ...
    try:
        # ... (OS specific logic) ...
        if system == "Linux": # Example
            # ...
            if not os.path.exists("/etc/resolv.conf"):
                 try:
                    # ... resolvectl logic ...
                    pass
                 except FileNotFoundError:
                    if console:
                        console.log("[dim]'resolvectl' not found. Cannot determine DNS servers on this Linux system without /etc/resolv.conf.[/dim]")
                 except subprocess.CalledProcessError as e:
                    if console:
                        console.log(f"[dim]Error running 'resolvectl dns': {e}[/dim]")

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        if console:
            console.log(f"[dim]Error retrieving DNS servers: {e}[/dim]")
    except Exception as e_global:
        if console:
            console.log(f"[dim]An unexpected error occurred while getting DNS servers: {e_global}[/dim]")
    return list(set(dns_servers))