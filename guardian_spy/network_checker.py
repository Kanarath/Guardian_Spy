# guardian_spy/network_checker.py
import requests
import platform
import subprocess
import re
import os
import json

from guardian_spy import DEBUG_MODE 

DEFAULT_IP_SERVICE = "https://api.ipify.org?format=json"
GEO_IP_SERVICE = "http://ip-api.com/json/" 

def get_public_ip_info(console=None):
    public_ip = None 
    geo_info = None
    nc_console_for_logs = console if DEBUG_MODE else None # Usar esto para console.log

    try:
        if nc_console_for_logs: nc_console_for_logs.log(f"Fetching public IP from {DEFAULT_IP_SERVICE}")
        response = requests.get(DEFAULT_IP_SERVICE, timeout=7)
        response.raise_for_status()
        data = response.json()
        public_ip = data.get("ip") 
        if nc_console_for_logs:
            log_data_str = str(data); nc_console_for_logs.log(f"Raw IP response: {log_data_str[:200]}{'...' if len(log_data_str) > 200 else ''}")
    except requests.exceptions.Timeout:
        if console: console.print(f"[dim red]Network Timeout: Could not reach {DEFAULT_IP_SERVICE}[/dim red]")
    except requests.exceptions.RequestException as e:
        if console: console.print(f"[dim red]Network Error (IP Service 1): {type(e).__name__}[/dim red]")
    
    if not public_ip:
        try:
            if nc_console_for_logs: nc_console_for_logs.log("Fetching public IP from fallback service icanhazip.com")
            response = requests.get("https://icanhazip.com", timeout=7)
            response.raise_for_status()
            public_ip = response.text.strip()
        except requests.exceptions.Timeout:
            if console: console.print("[dim red]Network Timeout: Could not reach fallback IP service.[/dim red]")
        except requests.exceptions.RequestException as e_fallback:
             if console: console.print(f"[dim red]Network Error (IP Service 2): {type(e_fallback).__name__}[/dim red]")
    
    if not public_ip: 
        if nc_console_for_logs: nc_console_for_logs.log("[dim]Failed to retrieve public IP after all attempts.[/dim]")
        return None, None 

    try:
        if nc_console_for_logs: nc_console_for_logs.log(f"Fetching geolocation for IP: {public_ip} from {GEO_IP_SERVICE}{public_ip}")
        geo_response = requests.get(f"{GEO_IP_SERVICE}{public_ip}", timeout=7)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        if nc_console_for_logs:
            log_geo_data_str = str(geo_data); nc_console_for_logs.log(f"Raw GeoIP response: {log_geo_data_str[:500]}{'...' if len(log_geo_data_str) > 500 else ''}")
        if geo_data.get("status") == "success":
            geo_info = {"country": geo_data.get("country"), "region": geo_data.get("regionName"), "city": geo_data.get("city"), "isp": geo_data.get("isp"), "org": geo_data.get("org"), "query_ip": geo_data.get("query")}
        elif console: console.print(f"[dim yellow]GeoIP service status: {geo_data.get('status')} - Msg: {geo_data.get('message')}[/dim yellow]")
    except requests.exceptions.Timeout:
        if console: console.print(f"[dim red]Network Timeout: GeoIP service for {public_ip}[/dim red]")
    except requests.exceptions.RequestException as e:
        if console: console.print(f"[dim red]Network Error (GeoIP): {type(e).__name__}[/dim red]")
    except json.JSONDecodeError as e_json: 
        if console: console.print(f"[dim red]Data Error: Invalid GeoIP response for {public_ip}: {e_json}[/dim red]")
        if nc_console_for_logs and 'geo_response' in locals() and hasattr(geo_response, 'text'):
            nc_console_for_logs.log(f"[dim]GeoIP Response content: {geo_response.text[:200]}...[/dim]")                
    return public_ip, geo_info

def get_dns_servers(console=None):
    system = platform.system()
    dns_servers = []
    nc_console_for_logs = console if DEBUG_MODE else None
    try:
        if system == "Windows":
            if nc_console_for_logs: nc_console_for_logs.log("[dim]Attempting DNS via PowerShell (Windows)...[/dim]")
            try:
                ps_command_parts = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "\"try { @(Get-DnsClientServerAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ServerAddresses -ErrorAction SilentlyContinue) + @(Get-DnsClientServerAddress -AddressFamily IPv6 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ServerAddresses -ErrorAction SilentlyContinue) | Where-Object { $_ -ne $null -and $_ -ne '' } | ForEach-Object { $_.Trim() } } catch { exit 1 }\""]
                result = subprocess.run(" ".join(ps_command_parts), capture_output=True, text=True, check=False, shell=True, timeout=10, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                if result.returncode == 0 and result.stdout and result.stdout.strip():
                    if nc_console_for_logs: nc_console_for_logs.log(f"[dim]PS DNS stdout:\n{result.stdout.strip()}[/dim]")
                    found_ips = result.stdout.strip().splitlines()
                    for ip in found_ips:
                        ip = ip.strip()
                        if ip and (re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) or ':' in ip) and ip not in dns_servers: dns_servers.append(ip)
                elif nc_console_for_logs: nc_console_for_logs.log(f"[dim]PS DNS command failed/no output. RC: {result.returncode}, Stdout: '{result.stdout.strip()[:100]}', Stderr: '{result.stderr.strip()[:100]}'[/dim]")
            except subprocess.TimeoutExpired:
                if nc_console_for_logs: nc_console_for_logs.log("[dim]PS DNS command timed out.[/dim]")
            except FileNotFoundError:
                if nc_console_for_logs: nc_console_for_logs.log("[dim]PowerShell not found for DNS.[/dim]")
            except Exception as e_ps:
                if nc_console_for_logs: nc_console_for_logs.log(f"[dim]Exception in PS DNS: {e_ps}[/dim]")
            if not dns_servers: 
                if nc_console_for_logs: nc_console_for_logs.log("[dim]Falling back to ipconfig for Windows DNS...[/dim]")
                try:
                    ipconfig_result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', timeout=10, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    if ipconfig_result.returncode == 0:
                        lines = ipconfig_result.stdout.splitlines()
                        for i, line in enumerate(lines):
                            norm_line = line.lower()
                            if ("dns servers" in norm_line or "servidores dns" in norm_line) and ":" in line:
                                parts = line.split(":", 1)
                                if len(parts) > 1:
                                    potential_ips_on_line = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b(?:[0-9a-fA-F:]+:+[0-9a-fA-F\.:]+)\b', parts[1].strip())
                                    for ip_addr in potential_ips_on_line:
                                        if ip_addr and ip_addr not in dns_servers: dns_servers.append(ip_addr)
                                    for k in range(1, 3):
                                        if (i + k) < len(lines):
                                            next_l = lines[i+k].strip()
                                            if next_l and not (":" in next_l and any(lbl in next_l.lower() for lbl in ["server","servidor"])):
                                                potential_ips_in_next = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b(?:[0-9a-fA-F:]+:+[0-9a-fA-F\.:]+)\b', next_l)
                                                for ip_addr_n in potential_ips_in_next:
                                                    if ip_addr_n and ip_addr_n not in dns_servers: dns_servers.append(ip_addr_n)
                                            else: break 
                                        else: break
                    elif nc_console_for_logs: nc_console_for_logs.log(f"[dim]ipconfig failed. RC: {ipconfig_result.returncode}[/dim]")
                except subprocess.TimeoutExpired:
                    if nc_console_for_logs: nc_console_for_logs.log("[dim]ipconfig command timed out.[/dim]")
                except Exception as e_ipconfig:
                    if nc_console_for_logs: nc_console_for_logs.log(f"[dim]Exception in ipconfig: {e_ipconfig}[/dim]")
        elif system == "Darwin": 
            if nc_console_for_logs: nc_console_for_logs.log("[dim]Attempting DNS via scutil (macOS)...[/dim]")
            try:
                result = subprocess.run(["scutil", "--dns"], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', timeout=10)
                if result.returncode == 0 and result.stdout:
                    matches = re.findall(r"nameserver\[\d+\]\s*:\s*([\d\.:a-fA-F]+)", result.stdout)
                    for ip in matches:
                        if ip and ip not in dns_servers: dns_servers.append(ip)
                elif nc_console_for_logs: nc_console_for_logs.log(f"[dim]scutil failed. RC: {result.returncode}[/dim]")
            except subprocess.TimeoutExpired:
                if nc_console_for_logs: nc_console_for_logs.log("[dim]scutil command timed out.[/dim]")
            except Exception as e_darwin:
                if nc_console_for_logs: nc_console_for_logs.log(f"[dim]Exception in scutil: {e_darwin}[/dim]")
        else: # Linux
            if nc_console_for_logs: nc_console_for_logs.log("[dim]Attempting DNS via /etc/resolv.conf or resolvectl (Linux)...[/dim]")
            if os.path.exists("/etc/resolv.conf"):
                try:
                    with open("/etc/resolv.conf", "r", encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("nameserver"):
                                parts = line.split()
                                if len(parts) > 1 and ('.' in parts[1] or ':' in parts[1]) and parts[1] not in dns_servers:
                                    dns_servers.append(parts[1])
                except Exception as e_resolv:
                    if nc_console_for_logs: nc_console_for_logs.log(f"[dim]Error reading /etc/resolv.conf: {e_resolv}[/dim]")
            if not dns_servers:
                if nc_console_for_logs: nc_console_for_logs.log("[dim]No DNS from /etc/resolv.conf, trying resolvectl...[/dim]")
                try:
                    result_resolvectl = subprocess.run(["resolvectl", "dns"], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', timeout=10)
                    if result_resolvectl.returncode == 0 and result_resolvectl.stdout:
                        ips_from_resolvectl = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b|\b(?:[0-9a-fA-F]{1,4}:){1,7}[0-9a-fA-F:]{1,}\b', result_resolvectl.stdout)
                        for ip_res in ips_from_resolvectl:
                            if ip_res not in dns_servers and ip_res != "::1" and not ip_res.startswith("127.") and \
                               not ip_res.lower().startswith("fe80::") and not ip_res.startswith("169.254.") and \
                               not (ip_res.count(':') > 1 and '%' in ip_res): 
                                dns_servers.append(ip_res)
                    elif nc_console_for_logs: nc_console_for_logs.log(f"[dim]resolvectl failed. RC: {result_resolvectl.returncode}[/dim]")
                except subprocess.TimeoutExpired:
                     if nc_console_for_logs: nc_console_for_logs.log("[dim]resolvectl command timed out.[/dim]")
                except FileNotFoundError:
                    if nc_console_for_logs: nc_console_for_logs.log("[dim]'resolvectl' not found.[/dim]")
                except Exception as e_resolvectl: 
                    if nc_console_for_logs: nc_console_for_logs.log(f"[dim]Error with resolvectl: {e_resolvectl}[/dim]")
    except Exception as e_global: 
        if nc_console_for_logs: 
            nc_console_for_logs.log(f"[dim red]Unexpected global error in get_dns_servers: {e_global}[/dim red]")
            import traceback
            nc_console_for_logs.log(f"[dim]{traceback.format_exc()}[/dim]")
        elif console: 
             console.print(f"[dim red]An error occurred while retrieving DNS servers.[/dim red]")
    return list(set(dns_servers))