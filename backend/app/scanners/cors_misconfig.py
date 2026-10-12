import httpx

from app.scanners.base import FindingCandidate, Scanner

CANARY_ORIGIN = "https://jarvis-cors-canary.invalid"


class CorsMisconfigScanner(Scanner):
    """Safe, non-destructive CORS misconfiguration probe. Sends a request
    with a clearly-fake Origin header and checks whether the server
    reflects it back in Access-Control-Allow-Origin -- especially
    combined with Access-Control-Allow-Credentials: true, which would let
    any website read authenticated responses from this origin."""

    name = "cors_misconfig"
    category = "CORS misconfiguration"
    risk_level = "passive"

    def run(self, url: str, timeout: int = 10) -> list[FindingCandidate]:
        try:
            with httpx.Client(timeout=timeout, follow_redirects=False) as client:
                resp = client.get(url, headers={"Origin": CANARY_ORIGIN})
        except httpx.RequestError:
            return []

        acao = resp.headers.get("access-control-allow-origin")
        acac = resp.headers.get("access-control-allow-credentials", "").lower() == "true"

        if not acao:
            return []

        findings: list[FindingCandidate] = []

        if acao == CANARY_ORIGIN:
            findings.append(
                FindingCandidate(
                    category=self.category,
                    severity="high" if acac else "medium",
                    confidence=0.7,
                    observation=(
                        "The server reflects an arbitrary Origin header back in "
                        f"Access-Control-Allow-Origin (sent '{CANARY_ORIGIN}', got it echoed "
                        "back exactly)."
                        + (
                            " It also sends Access-Control-Allow-Credentials: true, meaning any "
                            "website could make authenticated cross-origin requests and read the "
                            "response -- this is a serious misconfiguration if the endpoint "
                            "returns sensitive or session-authenticated data."
                            if acac
                            else " Access-Control-Allow-Credentials was not set, which limits "
                            "impact to non-credentialed requests, but any origin can still read "
                            "the response body."
                        )
                    ),
                    evidence={
                        "url": url,
                        "sent_origin": CANARY_ORIGIN,
                        "access_control_allow_origin": acao,
                        "access_control_allow_credentials": acac,
                    },
                    remediation=(
                        "Reflect only an explicit allowlist of trusted origins, never the "
                        "request's Origin header verbatim. Never combine a wildcard or "
                        "reflected origin with Access-Control-Allow-Credentials: true."
                    ),
                    human_review_required=True,
                )
            )
        elif acao == "*" and acac:
            # Technically invalid per the Fetch spec (browsers reject this combination),
            # but a server sending it is still a real misconfiguration worth a human look.
            findings.append(
                FindingCandidate(
                    category=self.category,
                    severity="low",
                    confidence=0.4,
                    observation=(
                        "The server sends Access-Control-Allow-Origin: * together with "
                        "Access-Control-Allow-Credentials: true. Browsers reject this exact "
                        "combination, so it likely has no practical effect today, but it signals "
                        "a CORS policy that wasn't configured deliberately and is worth review."
                    ),
                    evidence={
                        "url": url,
                        "access_control_allow_origin": acao,
                        "access_control_allow_credentials": acac,
                    },
                    remediation=(
                        "Replace the wildcard with an explicit origin allowlist if credentialed "
                        "cross-origin requests are actually needed."
                    ),
                    human_review_required=True,
                )
            )

        return findings
