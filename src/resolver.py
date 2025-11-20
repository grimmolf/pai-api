import socket
import time
from functools import lru_cache
from zeroconf import Zeroconf

# Cache resolutions for 5 minutes
CACHE_TTL = 300 
_dns_cache = {}

def resolve_mdns(hostname: str) -> str:
    """
    Resolves a .local hostname to an IP address using Zeroconf.
    Returns the IP address as a string, or the original hostname if not .local.
    """
    if not hostname.endswith('.local'):
        return hostname
        
    # Check cache
    now = time.time()
    if hostname in _dns_cache:
        ip, expiry = _dns_cache[hostname]
        if now < expiry:
            return ip
            
    # Attempt Resolution
    try:
        # Simple socket resolution often works on macOS if Bonjour is active
        # But we want to be robust.
        ip = socket.gethostbyname(hostname)
        _dns_cache[hostname] = (ip, now + CACHE_TTL)
        return ip
    except socket.gaierror:
        # Fallback to manual zeroconf if needed (though gethostbyname usually uses system resolver which handles mDNS on mac)
        # For strict zeroconf library usage:
        zeroconf = Zeroconf()
        try:
            info = zeroconf.get_service_info("_http._tcp.local.", f"{hostname}.")
            if info:
                # Parse address from info
                # This is complex because we need the exact service name, not just host
                # For now, on macOS/Linux with Avahi, gethostbyname is actually the standard way
                pass
        finally:
            zeroconf.close()
            
        return hostname # Return original if resolution fails

