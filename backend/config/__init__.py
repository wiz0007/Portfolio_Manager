import socket

_orig_getaddrinfo = socket.getaddrinfo


def _fallback_getaddrinfo(host, port, *args, **kwargs):
    try:
        return _orig_getaddrinfo(host, port, *args, **kwargs)
    except socket.gaierror:
        if isinstance(host, str) and 'neon.tech' in host:
            # Fallback IP for ap-southeast-1 Neon pooler when local DNS refuses
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('52.76.212.156', port))]
        raise


socket.getaddrinfo = _fallback_getaddrinfo
