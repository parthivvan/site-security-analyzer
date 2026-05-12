"""
SSRF protection — URL validation and safe HTTP adapter.

Protects against:
- DNS rebinding attacks (re-validates on every redirect)
- IPv6 bypass / NAT64 awareness
- Private IP access (loopback, link-local, multicast, reserved)
- Cloud metadata endpoint access (169.254.x.x)
- Protocol smuggling
"""
import socket
import ipaddress
import logging
from typing import Tuple, Optional
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)


def validate_url_safe(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Comprehensive URL validation to prevent SSRF attacks.

    Returns: (is_valid, normalized_url, error_message)
    """
    try:
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False, url, "Only HTTP/HTTPS protocols allowed"

        hostname = parsed.hostname
        if not hostname:
            return False, url, "Invalid hostname"

        if any(char in hostname for char in ["@", " ", "\n", "\r", "\t"]):
            return False, url, "Invalid characters in hostname"

        # Resolve DNS and validate ALL resolved IPs
        try:
            resolved_ips = socket.getaddrinfo(
                hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM
            )
        except socket.gaierror:
            return False, url, "Cannot resolve hostname"

        for ip_tuple in resolved_ips:
            try:
                ip_str = ip_tuple[4][0]
                if "%" in ip_str:
                    ip_str = ip_str.split("%")[0]

                ip_obj = ipaddress.ip_address(ip_str)

                # Allow NAT64 prefix (64:ff9b::/96)
                is_nat64 = isinstance(
                    ip_obj, ipaddress.IPv6Address
                ) and ip_obj in ipaddress.IPv6Network("64:ff9b::/96")

                if not is_nat64 and (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_multicast
                    or ip_obj.is_reserved
                ):
                    return (
                        False,
                        url,
                        f"Access to private/internal addresses not allowed ({ip_str})",
                    )

                # Cloud metadata services
                if isinstance(ip_obj, ipaddress.IPv4Address):
                    if ip_obj in ipaddress.ip_network("169.254.0.0/16"):
                        return (
                            False,
                            url,
                            "Access to cloud metadata services not allowed",
                        )
                    if ip_obj in ipaddress.ip_network("127.0.0.0/8"):
                        return False, url, "Access to localhost not allowed"

            except (ValueError, AttributeError) as e:
                logger.warning("IP validation error for %s: %s", ip_str, e)
                return False, url, "Invalid IP address"

        return True, url, None

    except Exception as e:
        logger.error("URL validation error: %s", e)
        return False, url, "Invalid URL format"


class SafeHTTPAdapter(HTTPAdapter):
    """Custom HTTP adapter that re-validates DNS on every redirect."""

    def send(self, request, **kwargs):
        hostname = urlparse(request.url).hostname

        if hostname:
            try:
                old_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(5)
                try:
                    resolved_ips = socket.getaddrinfo(hostname, None)
                finally:
                    socket.setdefaulttimeout(old_timeout)

                for ip_tuple in resolved_ips:
                    ip_str = ip_tuple[4][0]
                    if "%" in ip_str:
                        ip_str = ip_str.split("%")[0]

                    ip_obj = ipaddress.ip_address(ip_str)

                    is_nat64 = isinstance(
                        ip_obj, ipaddress.IPv6Address
                    ) and ip_obj in ipaddress.IPv6Network("64:ff9b::/96")

                    if not is_nat64 and (
                        ip_obj.is_private
                        or ip_obj.is_loopback
                        or ip_obj.is_link_local
                        or ip_obj.is_multicast
                        or ip_obj.is_reserved
                    ):
                        raise requests.exceptions.ConnectionError(
                            f"Blocked private IP in redirect: {ip_str}"
                        )
            except socket.gaierror:
                raise requests.exceptions.ConnectionError("DNS resolution failed")

        return super().send(request, **kwargs)
