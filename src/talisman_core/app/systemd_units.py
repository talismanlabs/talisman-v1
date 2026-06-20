"""Pure rendering for the TalisMan user systemd unit files."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemdUnitConfig:
    """Configuration values used to render TalisMan systemd user units."""

    gateway_unit_name: str = "talisman-gateway.service"
    orchestrator_unit_name: str = "talisman.service"
    working_directory: str = "%h/TalisMan"
    talisman_home: str = "%h/TalisMan"
    gateway_exec_start: str = (
        "%h/TalisMan/.venv-gateway/bin/uvicorn TalisMan_gateway:app "
        "--app-dir %h/TalisMan/src --host 127.0.0.1 --port 8787"
    )
    orchestrator_exec_start: str = (
        "%h/TalisMan/.venv/bin/python -m talisman_core.main --serve "
        "--config %h/TalisMan/config/config.yaml"
    )
    gateway_restart_sec: int = 5
    orchestrator_restart_sec: int = 10
    gateway_read_write_paths: tuple[str, ...] = ("%h/TalisMan/state", "%h/TalisMan/logs")
    orchestrator_read_write_paths: tuple[str, ...] = ("%h/TalisMan",)


@dataclass(frozen=True, slots=True)
class RenderedSystemdUnits:
    """Rendered filenames and contents for the TalisMan systemd user units."""

    gateway_unit_name: str
    gateway_unit: str
    orchestrator_unit_name: str
    orchestrator_unit: str


def render_gateway_unit(config: SystemdUnitConfig | None = None) -> str:
    """Render the host-side credential and budget gateway systemd unit."""

    resolved = _resolve_config(config)
    read_write_paths = " ".join(resolved.gateway_read_write_paths)
    return (
        "\n".join(
            [
                "[Unit]",
                "Description=TalisMan host-side credential and budget gateway",
                "After=network-online.target",
                "Wants=network-online.target",
                "",
                "[Service]",
                "Type=simple",
                f"WorkingDirectory={resolved.working_directory}",
                f"ExecStart={resolved.gateway_exec_start}",
                "Restart=on-failure",
                f"RestartSec={resolved.gateway_restart_sec}",
                f"Environment=TALISMAN_HOME={resolved.talisman_home}",
                "",
                _GATEWAY_SECRET_COMMENT,
                f"ReadWritePaths={read_write_paths}",
                "NoNewPrivileges=true",
                "PrivateTmp=true",
                "",
                "[Install]",
                "WantedBy=default.target",
            ]
        )
        + "\n"
    )


def render_orchestrator_unit(config: SystemdUnitConfig | None = None) -> str:
    """Render the TalisMan orchestration systemd unit."""

    resolved = _resolve_config(config)
    read_write_paths = " ".join(resolved.orchestrator_read_write_paths)
    return (
        "\n".join(
            [
                "[Unit]",
                "Description=TalisMan orchestration service",
                f"After={resolved.gateway_unit_name}",
                f"Wants={resolved.gateway_unit_name}",
                "",
                "[Service]",
                "Type=simple",
                f"WorkingDirectory={resolved.working_directory}",
                f"ExecStart={resolved.orchestrator_exec_start}",
                "Restart=on-failure",
                f"RestartSec={resolved.orchestrator_restart_sec}",
                "Environment=PYTHONUNBUFFERED=1",
                "",
                "# Keep the service constrained to the TalisMan workspace.",
                f"ReadWritePaths={read_write_paths}",
                "NoNewPrivileges=true",
                "PrivateTmp=true",
                "",
                "[Install]",
                "WantedBy=default.target",
            ]
        )
        + "\n"
    )


def render_systemd_units(config: SystemdUnitConfig | None = None) -> RenderedSystemdUnits:
    """Render both TalisMan systemd units from the same configuration."""

    resolved = _resolve_config(config)
    return RenderedSystemdUnits(
        gateway_unit_name=resolved.gateway_unit_name,
        gateway_unit=render_gateway_unit(resolved),
        orchestrator_unit_name=resolved.orchestrator_unit_name,
        orchestrator_unit=render_orchestrator_unit(resolved),
    )


_GATEWAY_SECRET_COMMENT = (
    "# Secrets are file-based and not committed to Git. For stronger hardening, "
    "migrate these to systemd LoadCredential."
)


def _resolve_config(config: SystemdUnitConfig | None) -> SystemdUnitConfig:
    return config if config is not None else SystemdUnitConfig()
