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