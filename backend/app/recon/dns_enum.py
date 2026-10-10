import dns.exception
import dns.resolver

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]


def enumerate_dns_records(domain: str) -> dict[str, list[str]]:
    """Query common DNS record types for a domain. Returns an empty list for
    any type that has no records or times out, rather than raising."""
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5

    results: dict[str, list[str]] = {}
    for record_type in RECORD_TYPES:
        try:
            answers = resolver.resolve(domain, record_type)
            results[record_type] = [str(r).rstrip(".") for r in answers]
        except (
            dns.resolver.NoAnswer,
            dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers,
        ):
            results[record_type] = []
        except dns.exception.Timeout:
            results[record_type] = []
    return results
