"""Regression tests for the external tool adapters (app/tools/). These
mock subprocess.run so they never depend on network access or the
tools actually being installed -- they lock in the output-parsing
contract against known-good sample output captured from real runs."""
import subprocess
from unittest.mock import patch

from app.tools.amass import run_amass
from app.tools.base import is_tool_installed, resolve_binary, run_tool
from app.tools.dnsx import run_dnsx
from app.tools.subfinder import run_subfinder


def _completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(args=["x"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_resolve_binary_returns_none_when_not_found():
    assert resolve_binary("definitely-not-a-real-binary-xyz") is None


def test_is_tool_installed_false_for_missing_binary():
    assert is_tool_installed("definitely-not-a-real-binary-xyz") is False


def test_run_tool_returns_none_when_binary_missing():
    assert run_tool("definitely-not-a-real-binary-xyz", ["-v"]) is None


def test_run_tool_salvages_partial_output_on_timeout():
    with patch("app.tools.base.resolve_binary", return_value="/bin/true"):
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="x", timeout=5, output="partial data\n", stderr=""),
        ):
            result = run_tool("true", [], timeout=5)
    assert result is not None
    assert result.returncode == -1
    assert result.stdout == "partial data\n"


def test_run_tool_returns_none_on_timeout_with_no_output():
    with patch("app.tools.base.resolve_binary", return_value="/bin/true"):
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="x", timeout=5, output="", stderr=""),
        ):
            result = run_tool("true", [], timeout=5)
    assert result is None


def test_run_subfinder_parses_jsonl_output():
    sample = (
        '{"host":"demo.testfire.net","input":"testfire.net","source":"crtname"}\n'
        '{"host":"www.testfire.net","input":"testfire.net","source":"anubis"}\n'
    )
    with patch("app.tools.subfinder.run_tool", return_value=_completed(stdout=sample)):
        hosts = run_subfinder("testfire.net")
    assert hosts == ["demo.testfire.net", "www.testfire.net"]


def test_run_subfinder_empty_on_missing_tool():
    with patch("app.tools.subfinder.run_tool", return_value=None):
        assert run_subfinder("testfire.net") == []


def test_run_amass_parses_relationship_graph_and_filters_to_subdomains():
    sample = (
        "testfire.net (FQDN) --> ns_record --> usw2.akam.net (FQDN)\n"
        "ftp.testfire.net (FQDN) --> cname_record --> testfire.net (FQDN)\n"
        "demo.testfire.net (FQDN) --> a_record --> 65.61.137.117 (IPAddress)\n"
        "33070 (ASN) --> managed_by --> RMH-14 (RIROrganization)\n"
        "The enumeration has finished\n"
    )
    with patch("app.tools.amass.run_tool", return_value=_completed(stdout=sample)):
        hosts = run_amass("testfire.net")
    # usw2.akam.net is infrastructure, not a subdomain of testfire.net -- must be excluded.
    assert hosts == ["demo.testfire.net", "ftp.testfire.net", "testfire.net"]


def test_run_amass_accepts_salvaged_partial_output():
    sample = "demo.testfire.net (FQDN) --> a_record --> 1.2.3.4 (IPAddress)\n"
    with patch("app.tools.amass.run_tool", return_value=_completed(stdout=sample, returncode=-1)):
        hosts = run_amass("testfire.net")
    assert hosts == ["demo.testfire.net"]


def test_run_amass_empty_on_real_failure():
    with patch("app.tools.amass.run_tool", return_value=_completed(stdout="", stderr="boom", returncode=1)):
        assert run_amass("testfire.net") == []


def test_run_dnsx_parses_resolved_hosts():
    sample = (
        '{"host":"testfire.net","a":["65.61.137.117"]}\n'
        '{"host":"demo.testfire.net","a":["65.61.137.117","1.2.3.4"]}\n'
    )
    with patch("app.tools.dnsx.run_tool", return_value=_completed(stdout=sample)):
        resolved = run_dnsx(["testfire.net", "demo.testfire.net"])
    assert resolved == {
        "testfire.net": ["65.61.137.117"],
        "demo.testfire.net": ["65.61.137.117", "1.2.3.4"],
    }


def test_run_dnsx_empty_input_short_circuits():
    with patch("app.tools.dnsx.run_tool") as mock_run:
        assert run_dnsx([]) == {}
    mock_run.assert_not_called()


def test_run_dnsx_empty_on_missing_tool():
    with patch("app.tools.dnsx.run_tool", return_value=None):
        assert run_dnsx(["a.com"]) == {}
