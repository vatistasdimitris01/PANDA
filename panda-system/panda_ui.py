from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich import box
import math
import time

class PandaUI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self._setup_layout()

    def _setup_layout(self):
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        self.layout["main"].split_row(
            Layout(name="radar", ratio=2),
            Layout(name="list", ratio=3),
        )

    def make_header(self):
        title = Text(" PANDA SYSTEM v1.0 - PASSIVE DEFENSE ", style="bold cyan")
        status = Text(" SYSTEM: ACTIVE | MODE: STEALTH | LOCAL ONLY ", style="dim cyan")
        return Panel(Align.center(title + "\n" + status), style="cyan", box=box.ROUNDED)

    def make_footer(self, message="Listening for signals..."):
        return Panel(Text(f"LOG: {message}", style="cyan"), style="cyan", box=box.ROUNDED)

    def make_radar(self, devices):
        # A simple character-based radar
        width = 40
        height = 15
        center_x = width // 2
        center_y = height // 2
        
        canvas = [[" " for _ in range(width)] for _ in range(height)]
        
        # Draw circles
        for r in [3, 6, 9]:
            for a in range(0, 360, 10):
                rad = math.radians(a)
                x = int(center_x + r * 2 * math.cos(rad))
                y = int(center_y + r * math.sin(rad))
                if 0 <= x < width and 0 <= y < height:
                    canvas[y][x] = "."

        # Draw devices
        for i, dev in enumerate(devices):
            dist = dev['distance']
            # Scale distance to radar r (max 20m -> r=9)
            r = min(9, (dist / 20.0) * 9)
            angle = (hash(dev['bssid']) % 360) # deterministic angle for BSSID
            rad = math.radians(angle)
            x = int(center_x + r * 2 * math.cos(rad))
            y = int(center_y + r * math.sin(rad))
            
            if 0 <= x < width and 0 <= y < height:
                symbol = "●"
                style = "bold green"
                if dev.get('risk', 0) > 50:
                    symbol = "▲"
                    style = "bold red"
                elif dev.get('risk', 0) > 20:
                    symbol = "◆"
                    style = "bold yellow"
                
                canvas[y][x] = f"[{style}]{symbol}[/{style}]"

        # Center point (Self)
        canvas[center_y][center_x] = "[bold white]X[/bold white]"

        radar_text = "\n".join(["".join(line) for line in canvas])
        return Panel(Align.center(Text.from_markup(radar_text)), title="HUD RADAR", style="cyan", box=box.ROUNDED)

    def make_list(self, devices):
        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("ID", style="dim cyan")
        table.add_column("SSID / IP", style="bold cyan")
        table.add_column("BSSID", style="cyan")
        table.add_column("DIST", justify="right", style="green")
        table.add_column("RISK", justify="right")

        for i, dev in enumerate(devices[:15]):
            risk = dev.get('risk', 0)
            risk_style = "green"
            if risk > 50: risk_style = "bold red"
            elif risk > 20: risk_style = "yellow"
            
            table.add_row(
                str(i+1),
                dev['ssid'][:20],
                dev['bssid'],
                f"{dev['distance']}m",
                f"[{risk_style}]{risk}%[/{risk_style}]"
            )
        
        return Panel(table, title="ACTIVE SIGNALS", style="cyan", box=box.ROUNDED)

    def update(self, devices, log_msg=""):
        self.layout["header"].update(self.make_header())
        self.layout["radar"].update(self.make_radar(devices))
        self.layout["list"].update(self.make_list(devices))
        self.layout["footer"].update(self.make_footer(log_msg))
        return self.layout
