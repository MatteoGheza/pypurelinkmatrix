"""TUI for PureLink Matrix Simulator."""

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .core import MatrixSimulator

console = Console()


def create_matrix_table(simulator: MatrixSimulator) -> Table:
    """Create a table showing the video matrix routing."""
    table = Table(title="Video Matrix Routing")

    table.add_column("Output", justify="center", style="cyan")
    for i in range(1, 5):
        table.add_column(f"Input {i}\n({simulator.port_names[i-1]})", justify="center")

    for out in range(1, 5):
        row = [f"Output {out}\n({simulator.port_names[out+3]})"]
        current_in = simulator.video_mx[out - 1]
        for inp in range(1, 5):
            if current_in == inp:
                row.append("[bold green]●[/]")
            else:
                row.append("[dim]○[/]")
        table.add_row(*row)

    return table


def create_status_panel(simulator: MatrixSimulator) -> Panel:
    """Create a panel showing general device status."""
    status_table = Table.grid(expand=True)
    status_table.add_column(style="bold")
    status_table.add_column()

    status_table.add_row("IP Address:", simulator.ip)
    status_table.add_row("DHCP:", "Enabled" if simulator.dhcp == 0 else "Disabled")
    status_table.add_row("MCU Version:", simulator.mcu_version)
    status_table.add_row("MAC Address:", simulator.mac)

    return Panel(status_table, title="Device Status", border_style="blue")


def create_audio_table(simulator: MatrixSimulator) -> Table:
    """Create a table showing audio states."""
    table = Table(title="Audio States")
    table.add_column("Output", style="cyan")
    table.add_column("HDMI", justify="center")
    table.add_column("De-embed", justify="center")

    for i in range(4):
        table.add_row(
            f"Output {i+1}",
            "[green]ON[/]" if simulator.audio_hdmi[i] == 1 else "[red]OFF[/]",
            "[green]ON[/]" if simulator.audio_dec[i] == 1 else "[red]OFF[/]",
        )
    return table


def create_layout(simulator: MatrixSimulator) -> Layout:
    """Create the TUI layout."""
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3), Layout(name="main"), Layout(name="footer", size=3)
    )

    layout["main"].split_row(Layout(name="left", ratio=2), Layout(name="right", ratio=1))

    layout["left"].split_column(
        Layout(create_matrix_table(simulator)), Layout(create_audio_table(simulator))
    )

    layout["right"].update(create_status_panel(simulator))

    layout["header"].update(
        Panel("[bold magenta]PureLink PT-MA-HD44M Simulator[/]", border_style="magenta")
    )
    layout["footer"].update(
        Panel("Simulator running at http://localhost:80 | Press Ctrl+C to stop", border_style="dim")
    )

    return layout


def run_tui(simulator: MatrixSimulator):
    """Run the live TUI."""
    with Live(create_layout(simulator), refresh_per_second=2, screen=True) as live:
        while True:
            import time

            time.sleep(0.5)
            live.update(create_layout(simulator))
