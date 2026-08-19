"""Typer CLI scaffold for headless OpenSearch Guardian workflows.

This package is the V1 CLI entrypoint. It wraps the
``guardian.connections.ConnectionManager`` and ``CollectionResult``
domain objects so that operators can manage profiles from a terminal
without the Electron frontend.

Entrypoint
----------
After installation with ``pip install -e .[cli]`` the ``guardian``
console_script is available.

$ guardian --help
$ guardian connection list
$ guardian connection test <profile-id>
$ guardian connection enable-write <profile-id>
"""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from guardian.connections import ConnectionManager
from guardian.core_types.connection_models import (
    AuthMethod,
    ConnectionStatus,
)

app = typer.Typer(
    name="guardian",
    help="OpenSearch Guardian — headless cluster operations console.",
    no_args_is_help=True,
)
console = Console()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _manager() -> ConnectionManager:
    """Singleton factory — in V1 the manager is process-local.

    Future multi-user or server modes replace this with a session-aware
    provider.
    """
    if not hasattr(_manager, "_instance"):
        _manager._instance = ConnectionManager()
    return _manager._instance


# ---------------------------------------------------------------------------
# connection sub-group
# ---------------------------------------------------------------------------

conn_app = typer.Typer(help="Connection profile management.")
app.add_typer(conn_app, name="connection")


@conn_app.command("list")
def connection_list() -> None:
    """List all saved connection profiles."""
    mgr = _manager()
    profiles = mgr.list_profiles()
    if not profiles:
        console.print("[yellow]No connection profiles found.[/yellow]")
        raise typer.Exit()

    table = Table(title="Connection Profiles")
    table.add_column("ID", style="dim", max_width=36)
    table.add_column("Name")
    table.add_column("URL")
    table.add_column("Mode")
    table.add_column("Status")
    table.add_column("Write?")

    for p in profiles:
        table.add_row(
            p.id[:8] + "…",
            p.name,
            str(p.opensearch_url),
            p.mode.value,
            p.status.value,
            "✅" if p.write_enabled else "❌",
        )
    console.print(table)


@conn_app.command("add")
def connection_add(
    name: Annotated[str, typer.Option(..., help="Human-readable label.")],
    url: Annotated[str, typer.Option(..., help="OpenSearch HTTPS URL, e.g. https://prod.example.com:9200")],
    credential_ref: Annotated[str, typer.Option(..., help="Keyring key for the credentials.")],
    auth: Annotated[AuthMethod, typer.Option(help="Auth adapter.")] = AuthMethod.BASIC,
    tls_verify: Annotated[bool, typer.Option(help="Verify TLS certificates.")] = True,
    mode: Annotated[ConnectionStatus, typer.Option(help="Initial connection mode.")] = ConnectionStatus.DISCONNECTED,
) -> None:
    """Add a new connection profile (credentials stored in OS keychain)."""
    mgr = _manager()
    try:
        profile = mgr.add(
            name=name,
            opensearch_url=url,
            auth_method=auth,
            credential_ref=credential_ref,
            tls_verify=tls_verify,
            mode=ConnectionMode.READ_ONLY,  # always starts read-only (ADR-002)
        )
    except Exception as exc:
        console.print(f"[red]Failed to create profile: {exc}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Profile '{profile.name}' created (id={profile.id}).[/green]")


@conn_app.command("test")
def connection_test(
    profile_id: Annotated[str, typer.Argument(help="Full connection profile ID.")],
) -> None:
    """Run the five-dimension connection test for a profile."""
    import asyncio

    mgr = _manager()
    try:
        profile = asyncio.get_event_loop().run_until_complete(mgr.test_connection(profile_id))
    except Exception as exc:
        console.print(f"[red]Test failed: {exc}[/red]")
        raise typer.Exit(1)
    res = profile.last_test_result
    if res and res.passed:
        console.print(f"[green]✓ Connection test PASSED[/green] (cluster: {res.identity.cluster_name}, version: {res.identity.version})")
    else:
        console.print(f"[red]✗ Connection test FAILED[/red]")
        if res:
            if res.fatal_errors:
                console.print("Fatal errors:")
                for e in res.fatal_errors:
                    console.print(f"  • {e}")
            if res.errors:
                console.print("Warnings:")
                for e in res.errors:
                    console.print(f"  • {e}")


@conn_app.command("enable-write")
def connection_enable_write(
    profile_id: Annotated[str, typer.Argument(help="Full connection profile ID.")],
) -> None:
    """Enable write mode on a connection profile (requires prior user confirmation)."""
    mgr = _manager()
    try:
        if typer.confirm(f"Enable write mode for profile {profile_id}? This requires write permissions."):
            profile = mgr.enable_write(profile_id)
            console.print(f"[green]Write mode enabled for '{profile.name}'.[/green]")
    except Exception as exc:
        console.print(f"[red]Failed: {exc}[/red]")
        raise typer.Exit(1)


@conn_app.command("enable-provisioning")
def connection_enable_provisioning(
    profile_id: Annotated[str, typer.Argument(help="Full connection profile ID.")],
) -> None:
    """Enable provisioning mode (superset of write; requires super-user OpenSearch role)."""
    mgr = _manager()
    try:
        if typer.confirm(
            f"Enable provisioning mode for {profile_id}? "
            "Requires cluster-wide admin access on the OpenSearch side."
        ):
            profile = mgr.enable_provisioning(profile_id)
            console.print(f"[green]Provisioning mode enabled for '{profile.name}'.[/green]")
    except Exception as exc:
        console.print(f"[red]Failed: {exc}[/red]")
        raise typer.Exit(1)


@conn_app.command("disable-write")
def connection_disable_write(
    profile_id: Annotated[str, typer.Argument(help="Full connection profile ID.")],
) -> None:
    """Revert a profile to read-only."""
    mgr = _manager()
    profile = mgr.disable_write(profile_id)
    console.print(f"[yellow]'{profile.name}' is now read-only.[/yellow]")


# ---------------------------------------------------------------------------
# status probe
# ---------------------------------------------------------------------------


@app.command()
def status(
    profile_id: Annotated[str | None, typer.Option(help="Show details for one profile.")] = None,
) -> None:
    """Show overall Guardian connection status."""
    mgr = _manager()
    if profile_id:
        try:
            p = mgr.get(profile_id)
            res = p.last_test_result
            console.print(f"Name       : {p.name}")
            console.print(f"ID         : {p.id}")
            console.print(f"URL        : {p.opensearch_url}")
            console.print(f"Mode       : {p.mode.value}")
            console.print(f"Status     : {p.status.value}")
            if res:
                console.print(f"Test passed: {res.passed}")
                if res.identity:
                    console.print(f"Cluster    : {res.identity.cluster_name} ({res.identity.version})")
        except Exception as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1)
    else:
        profiles = mgr.list_profiles()
        table = Table(title="Guardian Connection Status")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Mode")
        for p in profiles:
            table.add_row(p.name, p.status.value, p.mode.value)
        console.print(table)


# ---------------------------------------------------------------------------
# entrypoint guard
# ---------------------------------------------------------------------------


def main() -> None:
    app()


if __name__ == "__main__":
    main()