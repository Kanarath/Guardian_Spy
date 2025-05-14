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
import requests
import platform
import subprocess
import re
import os
import json # Necesario si usamos WMIC con formato JSON, aunque el enfoque actual usa PowerShell

DEFAULT_IP_SERVICE = "https://api.ipify.org?format=json"
GEO_IP_SERVICE = "http://ip-api.com/json/" 

def get_public_ip_info(console=None):
    """
    Retrieves the public IP address and attempts to get geolocation info.

    Returns:
        tuple: (public_ip_str, geo_info_dict) or (None, None) on failure.
    """
    public_ip = None 
    geo_info = None

    # First, get the public IP
    try:
        if console:
            console.log(f"Fetching public IP from {DEFAULT_IP_SERVICE}")
        response = requests.get(DEFAULT_IP_SERVICE, timeout=7) # Aumentado timeout un poco
        response.raise_for_status()
        data = response.json()
        public_ip = data.get("ip") 
        if console:
            # Limitar la longitud del log si la respuesta es muy grande
            log_data_str = str(data)
            console.log(f"Raw IP response: {log_data_str[:200]}{'...' if len(log_data_str) > 200 else ''}")

    except requests.exceptions.Timeout:
        if console:
            console.log(f"[dim]Timeout fetching public IP from {DEFAULT_IP_SERVICE}[/dim]")
    except requests.exceptions.RequestException as e:
        if console:
            console.log(f"[dim]Error fetching public IP from {DEFAULT_IP_SERVICE}: {e}[/dim]")
    
    # Try a fallback simple text IP service if primary failed
    if not public_ip:
        try:
            if console:
                console.log("Fetching public IP from fallback service icanhazip.com")
            response = requests.get("https://icanhazip.com", timeout=7) # Aumentado timeout
            response.raise_for_status()
            public_ip = response.text.strip()
        except requests.exceptions.Timeout:
            if console:
                console.log("[dim]Timeout fetching public IP from fallback service.[/dim]")
        except requests.exceptions.RequestException as e_fallback:
             if console:
                 console.log(f"[dim]Error fetching public IP from fallback service: {e_fallback}[/dim]")
             # public_ip remains None if both fail

    if not public_ip: 
        if console:
            console.log("[dim]Failed to retrieve public IP after primary and fallback attempts.[/dim]")
        return None, None 

    # Then, get geolocation info for the successfully retrieved public_ip
    try:
        if console:
            console.log(f"Fetching geolocation for IP: {public_ip} from {GEO_IP_SERVICE}{public_ip}")
        geo_response = requests.get(f"{GEO_IP_SERVICE}{public_ip}", timeout=7) # Aumentado timeout
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        if console:
            log_geo_data_str = str(geo_data)
            console.log(f"Raw GeoIP response: {log_geo_data_str[:500]}{'...' if len(log_geo_data_str) > 500 else ''}")

        if geo_data.get("status") == "success":
            geo_info = {
                "country": geo_data.get("country"),
                "region": geo_data.get("regionName"),
                "city": geo_data.get("city"),
                "isp": geo_data.get("isp"),
                "org": geo_data.get("org"), 
                "query_ip": geo_data.get("query") 
            }
        elif console:
            console.log(f"[dim]Geolocation status not 'success': {geo_data.get('status')} - Message: {geo_data.get('message')}[/dim]")

    except requests.exceptions.Timeout:
        if console:
            console.log(f"[dim]Timeout fetching geolocation data for {public_ip}[/dim]")
    except requests.exceptions.RequestException as e:
        if console:
            console.log(f"[dim]Error fetching geolocation data for {public_ip}: {e}[/dim]")
    except json.JSONDecodeError as e_json: 
        if console:
            console.log(f"[dim]Error decoding geolocation JSON response for {public_ip}: {e_json}[/dim]")
            if 'geo_response' in locals() and hasattr(geo_response, 'text'): # Check if geo_response exists
                console.log(f"[dim]Response content: {geo_response.text[:200]}...[/dim]") 
            else:
                console.log("[dim]Geo_response object not available for logging content.[/dim]")
                
    return public_ip, geo_info


def get_dns_servers(console=None):
    """
    Attempts to retrieve the list of DNS servers configured on the system.
    This is OS-dependent and can be tricky.

    Returns:
        list: A list of DNS server IP addresses, or an empty list if none found/error.
    """
    system = platform.system()
    dns_servers = []

    try:
        if system == "Windows":
            if console: console.log("[dim]Attempting to get DNS servers on Windows using PowerShell...")
            try:
                # PowerShell command to get DNS server addresses for active IPv4 and IPv6 interfaces
                ps_command_parts = [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy", "Bypass", # Attempt to bypass execution policy issues
                    "-Command",
                    "\"try { @(Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ServerAddresses -ErrorAction SilentlyContinue) + @(Get-DnsClientServerAddress -AddressFamily IPv6 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ServerAddresses -ErrorAction SilentlyContinue) | Where-Object { $_ -ne $null -and $_ -ne '' } | ForEach-Object { $_.Trim() } } catch { Write-Error $_; exit 1 }\""
                ]
                # shell=True can be a security risk if command parts are from untrusted input, but here they are fixed.
                # It's often needed for more complex PowerShell commands from Python on Windows.
                result = subprocess.run(" ".join(ps_command_parts), capture_output=True, text=True, check=False, shell=True, timeout=10, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                
                if result.returncode == 0 and result.stdout and result.stdout.strip():
                    if console: console.log(f"[dim]PowerShell Get-DnsClientServerAddress stdout:\n{result.stdout.strip()}[/dim]")
                    found_ips = result.stdout.strip().splitlines()
                    for ip in found_ips:
                        ip = ip.strip()
                        # Basic validation for an IP address format
                        if ip and (re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) or ':' in ip) and ip not in dns_servers:
                            dns_servers.append(ip)
                else:
                    if console: 
                        console.log(f"[dim]PowerShell Get-DnsClientServerAddress command failed or returned no suitable output.[/dim]")
                        console.log(f"[dim]RC: {result.returncode}, Stdout: '{result.stdout.strip()[:200]}', Stderr: '{result.stderr.strip()[:200]}'[/dim]")
                        
            except subprocess.TimeoutExpired:
                if console: console.log("[dim]PowerShell command for DNS timed out.[/dim]")
            except FileNotFoundError: # PowerShell not found
                if console: console.log("[dim]PowerShell executable not found. Cannot use Get-DnsClientServerAddress.[/dim]")
            except Exception as e_ps: # Other errors from PowerShell execution
                if console: console.log(f"[dim]Exception during PowerShell DNS command execution: {e_ps}[/dim]")

            # Fallback to ipconfig if PowerShell method yielded no results
            if not dns_servers:
                if console: console.log("[dim]Falling back to ipconfig /all for Windows DNS as PowerShell method yielded no results or failed...[/dim]")
                try:
                    ipconfig_result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', timeout=10, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    if ipconfig_result.returncode == 0:
                        # Simplified parsing looking for lines starting with "DNS Servers" or localized equivalent
                        # and then taking the IP after the colon. This is still fragile.
                        lines = ipconfig_result.stdout.splitlines()
                        for i, line in enumerate(lines):
                            # A more robust way would be to parse for the "DNS Servers" label in any language
                            # or look for specific adapter sections and their DNS entries.
                            # For now, a basic check:
                            normalized_line = line.lower()
                            # Check for common DNS server labels
                            if ("dns servers" in normalized_line or "servidores dns" in normalized_line) and ":" in line:
                                parts = line.split(":", 1)
                                if len(parts) > 1:
                                    first_ip_on_line = parts[1].strip()
                                    # Extract potential IPs from this line (could be multiple separated by space/comma)
                                    # This regex finds IPv4 and valid (simplified) IPv6 addresses
                                    potential_ips_on_line = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b(?:[0-9a-fA-F:]+:+[0-9a-fA-F\.:]+)\b', first_ip_on_line)
                                    for ip_addr in potential_ips_on_line:
                                        if ip_addr and ip_addr not in dns_servers:
                                            dns_servers.append(ip_addr)
                                    
                                    # Check subsequent lines for more IPs if the label line didn't list all
                                    for k in range(1, 3): # Check next 2 lines
                                        if (i + k) < len(lines):
                                            next_line = lines[i+k].strip()
                                            if next_line and not (":" in next_line and any(lbl in next_line.lower() for lbl in ["server","servidor"])): # if not a new label
                                                potential_ips_in_next_line = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b(?:[0-9a-fA-F:]+:+[0-9a-fA-F\.:]+)\b', next_line)
                                                for ip_addr_next in potential_ips_in_next_line:
                                                    if ip_addr_next and ip_addr_next not in dns_servers:
                                                        dns_servers.append(ip_addr_next)
                                            else: # It's a new label or empty line
                                                break 
                                        else: # Out of lines
                                            break
                    else:
                        if console: console.log(f"[dim]ipconfig /all fallback also failed with code {ipconfig_result.returncode}. Stderr: {ipconfig_result.stderr[:200]}[/dim]")
                except subprocess.TimeoutExpired:
                    if console: console.log("[dim]ipconfig /all command timed out.[/dim]")
                except Exception as e_ipconfig:
                    if console: console.log(f"[dim]Exception during ipconfig /all parsing: {e_ipconfig}[/dim]")


        elif system == "Darwin": 
            if console: console.log("[dim]Attempting to get DNS servers on macOS using scutil...")
            try:
                result = subprocess.run(["scutil", "--dns"], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', timeout=10)
                if result.returncode == 0 and result.stdout:
                    # scutil --dns output can be complex. We look for 'nameserver[<index>] : <ip>'
                    # and also 'reach    : <hex_ip_representation>' which might need conversion or ignore.
                    # The regex here focuses on the 'nameserver' lines.
                    matches = re.findall(r"nameserver\[\d+\]\s*:\s*([\d\.:a-fA-F]+)", result.stdout)
                    for ip in matches:
                        if ip and ip not in dns_servers:
                            dns_servers.append(ip)
                else:
                     if console: console.log(f"[dim]scutil --dns failed with code {result.returncode}. Stderr: {result.stderr[:200]}. Stdout: {result.stdout[:200]}[/dim]")
            except subprocess.TimeoutExpired:
                if console: console.log("[dim]scutil --dns command timed out.[/dim]")
            except Exception as e_darwin:
                if console: console.log(f"[dim]Exception during scutil --dns parsing: {e_darwin}[/dim]")
        
        else: # Linux and other Unix-like
            if console: console.log("[dim]Attempting to get DNS servers on Linux from /etc/resolv.conf or resolvectl...")
            # Try /etc/resolv.conf first
            if os.path.exists("/etc/resolv.conf"):
                try:
                    with open("/etc/resolv.conf", "r", encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("nameserver"):
                                parts = line.split()
                                if len(parts) > 1:
                                    ip_candidate = parts[1]
                                    # Validate it's a plausible IP and not already added
                                    if ('.' in ip_candidate or ':' in ip_candidate) and ip_candidate not in dns_servers:
                                        dns_servers.append(ip_candidate)
                except Exception as e_resolv:
                    if console: console.log(f"[dim]Error reading /etc/resolv.conf: {e_resolv}[/dim]")
            
            # If no servers from resolv.conf, or if it doesn't exist, try resolvectl
            if not dns_servers:
                if console and not os.path.exists("/etc/resolv.conf"):
                    console.log("[dim]/etc/resolv.conf not found, trying resolvectl...")
                elif console:
                    console.log("[dim]No DNS servers found in /etc/resolv.conf, or it was empty. Trying resolvectl...")
                try:
                    result_resolvectl = subprocess.run(["resolvectl", "dns"], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', timeout=10)
                    if result_resolvectl.returncode == 0 and result_resolvectl.stdout:
                        # Regex for IPv4 or IPv6 addresses from resolvectl output
                        ips_from_resolvectl = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F:]{1,}\b', result_resolvectl.stdout)
                        for ip_res in ips_from_resolvectl:
                            # Basic filtering
                            if ip_res not in dns_servers and \
                               ip_res != "::1" and \
                               not ip_res.startswith("127.") and \
                               not ip_res.lower().startswith("fe80::") and \
                               not ip_res.startswith("169.254.") and \
                               not (ip_res.count(':') > 1 and '%' in ip_res): # Avoid link-local IPv6 with scope ID
                                dns_servers.append(ip_res)
                    else:
                        if console: console.log(f"[dim]resolvectl dns failed with code {result_resolvectl.returncode}. Stderr: {result_resolvectl.stderr[:200]}. Stdout: {result_resolvectl.stdout[:200]}[/dim]")
                except subprocess.TimeoutExpired:
                     if console: console.log("[dim]resolvectl dns command timed out.[/dim]")
                except FileNotFoundError:
                    if console:
                        console.log("[dim]'resolvectl' not found. Cannot use it to determine DNS servers.[/dim]")
                except Exception as e_resolvectl: 
                    if console: console.log(f"[dim]Error running or parsing 'resolvectl dns': {e_resolvectl}[/dim]")

    except Exception as e_global: 
        if console:
            console.log(f"[dim]An unexpected error occurred in get_dns_servers (global handler): {e_global}[/dim]")
            import traceback
            console.log(f"[dim]{traceback.format_exc()}[/dim]")
        
    # Remove duplicates and return
    return list(set(dns_servers))