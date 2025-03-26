import ssl
import socket
import whois
import datetime
from urllib.parse import urlparse

# Get SSL Certificate Expiry
def get_ssl_expiry(url):
    try:
        hostname = urlparse(url).netloc
        if ":" in hostname:
            hostname = hostname.split(":")[0]

        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_date = datetime.datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y GMT")
                return expiry_date > datetime.datetime.utcnow()  # Returns True if valid
    except:
        return False  # Failed to retrieve SSL, assume invalid

# Get WHOIS Domain Age in Years
def get_domain_age(url):
    try:
        domain = urlparse(url).netloc
        whois_info = whois.whois(domain)
        creation_date = whois_info.creation_date

        if isinstance(creation_date, list):  # Some WHOIS servers return lists
            creation_date = creation_date[0]

        age = (datetime.datetime.now() - creation_date).days // 365  # Convert days to years
        return age
    except:
        return -1  # Failed to retrieve WHOIS
