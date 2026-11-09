"""Modelo gráfico UML editable de los casos de uso de BUZON Xpress."""

from collections import Counter
from html import escape
from math import sqrt
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parents[1] / "docs/diagramas"
LEFT = 530
RIGHT = 982
RX = 186
RY = 39

# Los nombres y las asociaciones representan roles externos al software.
ACTORS = {
    "cuenta": (134, 195, ("Persona con cuenta",)),
    "visitante": (134, 340, ("Visitante",)),
    "emisor": (134, 570, ("Emisor",)),
    "destinatario": (134, 790, ("Destinatario",)),
    "operador": (1380, 410, ("Operador", "del punto")),
    "admin": (1380, 820, ("Administrador", "del punto")),
    "auditor": (1380, 1045, ("Auditor",)),
}

CASES = {
    "CU-01": (LEFT, 211, ("Acceder y gestionar el contacto",)),
    "CU-04a": (LEFT, 315, ("Consultar seguimiento público",)),
    "CU-09a": (LEFT, 419, ("Consultar puntos y cotizar",)),
    "CU-02": (LEFT, 523, ("Registrar una entrega futura",)),
    "CU-04b": (LEFT, 627, ("Consultar custodia privada",)),
    "CU-08": (LEFT, 731, ("Recibir avisos de la custodia",)),
    "CU-05": (LEFT, 835, ("Obtener código de retiro",)),
    "CU-10a": (LEFT, 983, ("Registrar incidencia o", "solicitar excepción")),
    "CU-03": (RIGHT, 211, ("Registrar recepción y ubicación",)),
    "CU-06": (RIGHT, 315, ("Verificar y preparar el retiro",)),
    "CU-07": (RIGHT, 419, ("Confirmar entrega realizada",)),
    "CU-09b": (RIGHT, 523, ("Registrar prórroga y cobro",)),
    "CU-10c": (RIGHT, 731, ("Registrar devolución aprobada",)),
    "CU-10b": (RIGHT, 835, ("Revisar y decidir", "incidencia o excepción")),
    "CU-11": (RIGHT, 939, ("Configurar punto y capacidad",)),
    "CU-12": (RIGHT, 1043, ("Consultar auditoría e indicadores",)),
}

# Los desplazamientos separan asociaciones que llegan al mismo óvalo.
ASSOCIATIONS = (
    ("cuenta", "CU-01", -10),
    ("visitante", "CU-01", 10),
    ("visitante", "CU-04a", 0),
    ("visitante", "CU-09a", 0),
    ("emisor", "CU-02", 0),
    ("emisor", "CU-04b", -10),
    ("destinatario", "CU-04b", 10),
    ("emisor", "CU-08", -10),
    ("destinatario", "CU-08", 10),
    ("destinatario", "CU-05", 0),
    ("emisor", "CU-10a", -10),
    ("destinatario", "CU-10a", 10),
    ("operador", "CU-03", 0),
    ("operador", "CU-06", 0),
    ("operador", "CU-07", 0),
    ("operador", "CU-09b", 0),
    ("operador", "CU-04b", -12),
    ("admin", "CU-04b", 0),
    ("auditor", "CU-04b", 12),
    ("operador", "CU-10a", -8),
    ("admin", "CU-10a", 8),
    ("operador", "CU-10c", 0),
    ("admin", "CU-10b", 0),
    ("admin", "CU-11", 0),
    ("admin", "CU-12", -10),
    ("auditor", "CU-12", 10),
)

SVG_START = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1514 1164" width="1514" height="1164" role="img" aria-labelledby="title desc">
<title id="title">Casos de uso de alto nivel de BUZON Xpress</title>
<desc id="desc">Actores humanos fuera del sistema y metas dentro. El seguimiento público está separado de la custodia privada. El destinatario obtiene el código, el operador verifica y confirma, y el administrador decide excepciones.</desc>
<style>
  text { font-family: 'DejaVu Sans', sans-serif; fill: #102342; }
  .title { font-size: 34px; font-weight: 700; }
  .sub { font-size: 17px; fill: #405578; }
  .system { fill: #fff; stroke: #102342; stroke-width: 2; }
  .system-name { font-size: 23px; font-weight: 700; }
  .association { fill: none; stroke: #60728f; stroke-width: 1.45; }
  .figure { fill: none; stroke: #102342; stroke-width: 2.25; stroke-linecap: round; stroke-linejoin: round; }
  .actor-label { font-size: 17px; font-weight: 700; text-anchor: middle; }
  .case { fill: #f0f5fe; stroke: #3560a9; stroke-width: 1.5; }
  .case-id { font-size: 13px; font-weight: 700; letter-spacing: 0.65px; fill: #214f9b; text-anchor: middle; }
  .case-name { font-size: 17px; text-anchor: middle; }
</style>
<rect width="1514" height="1164" fill="#f4f6fa"/>
<text class="title" x="48" y="57">Casos de uso de alto nivel</text>
<text class="sub" x="48" y="85">Vista UML 2.5.1 de las metas de los actores humanos</text>
<rect class="system" x="306" y="115" width="904" height="994"/>
<text class="system-name" x="330" y="154">BUZON Xpress</text>
"""


def association(actor, case, offset, lane):
    actor_x, actor_y, _ = ACTORS[actor]
    case_x, case_y, _ = CASES[case]
    from_left = actor_x < case_x
    start = actor_x + (23 if from_left else -23)
    target_y = case_y + offset
    horizontal_radius = RX * sqrt(1 - (offset / RY) ** 2)
    target_x = case_x + (-horizontal_radius if from_left else horizontal_radius)
    branch = 224 if from_left else 1293
    departure_y = actor_y - 6 + lane * 4
    bend = 286 if from_left else 1228
    return (
        f'<path class="association" data-actor="{actor}" data-case="{case}" '
        f'd="M {start} {actor_y - 6} L {branch} {departure_y:g} L {bend} {target_y} H {target_x:.2f}"/>'
    )


def actor_figure(x, y, lines):
    labels = "".join(
        f'<text class="actor-label" y="{49 + i * 22}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return (
        f'<g transform="translate({x} {y})"><circle class="figure" cy="-25" r="9"/>'
        '<path class="figure" d="M0 -16V12 M-23 -6H23 M0 12L-15 32 M0 12L15 32"/>'
        f'{labels}</g>'
    )


def use_case(case, x, y, lines):
    labels = "".join(
        f'<text class="case-name" x="{x}" y="{y + (7 if len(lines) == 1 else 1) + i * 19}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return (
        f'<g id="{case}"><ellipse class="case" cx="{x}" cy="{y}" rx="{RX}" ry="{RY}"/>'
        f'<text class="case-id" x="{x}" y="{y - 16}">{case}</text>{labels}</g>'
    )


def render():
    parts = [SVG_START]
    counts = Counter(actor for actor, _, _ in ASSOCIATIONS)
    lanes = Counter()
    for actor, case, offset in ASSOCIATIONS:
        lane = lanes[actor] - (counts[actor] - 1) / 2
        parts.append(association(actor, case, offset, lane))
        lanes[actor] += 1
    parts.extend(use_case(case, *layout) for case, layout in CASES.items())
    parts.extend(actor_figure(*layout) for layout in ACTORS.values())
    parts.append(
        '<path class="association" d="M306 1141H354"/>'
        '<text class="sub" x="367" y="1147">Asociación entre un actor y un caso de uso</text>\n</svg>\n'
    )
    svg = OUT / "casos_uso_alto_nivel.svg"
    svg.write_text("\n".join(parts), encoding="utf-8")
    subprocess.run(["rsvg-convert", str(svg), "-o", str(svg.with_suffix(".png"))], check=True)


if __name__ == "__main__":
    render()
