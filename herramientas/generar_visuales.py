"""Crea wireframes SVG editables y sus PNG con herramientas locales."""
from pathlib import Path
from html import escape
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/wireframes'


class Sheet:
    def __init__(self, title, width=1440, height=1320, mono=False):
        self.width, self.height, self.mono = width, height, mono
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
                      f'<title>{escape(title)}</title><desc>Propuesta estática con datos ficticios. Custodia asistida, sin hardware externo.</desc>',
                      '<style>text{font-family:DejaVu Sans,sans-serif} .bold{font-weight:700}</style>']
        self.rect(0, 0, width, height, '#F4F6FA' if not mono else '#F3F3F3', stroke='none', radius=0)
        self.rect(0, 0, width, 108, '#0B368C' if not mono else '#202020', stroke='none', radius=0)
        self.text(40, 46, 'BUZON Xpress', 27, '#FFFFFF', True)
        self.text(40, 82, title, 17, '#FFFFFF')
        self.text(40, height - 26, 'DISEÑO ESTÁTICO · DATOS DE EJEMPLO · ATENCIÓN POR PERSONAL · SIN DISPOSITIVOS EXTERNOS', 13, '#444444')

    def rect(self, x, y, w, h, fill='#FFFFFF', stroke='#CBD2DF', radius=12):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

    def text(self, x, y, value, size=18, color='#172033', bold=False):
        cls = ' class="bold"' if bold else ''
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}"{cls}>{escape(value)}</text>')

    def paragraph(self, x, y, value, width, size=18, color='#172033', bold=False):
        lines = textwrap.wrap(value, width=max(10, int(width / (size * .62))))
        for line in lines:
            self.text(x, y, line, size, color, bold)
            y += size * 1.48
        return y

    def button(self, x, y, w, label, primary=False):
        fill = '#202020' if self.mono else '#0B368C'
        self.rect(x, y, w, 44, fill if primary else '#FFFFFF', '#606060' if self.mono else '#0B368C', 7)
        self.text(x+14, y+28, label, 15, '#FFFFFF' if primary else '#172033', True)

    def field(self, x, y, w, label, placeholder=''):
        self.text(x, y, label, 14, '#444444', True)
        self.rect(x, y+10, w, 42, '#FAFAFA', '#A9B2C1', 5)
        self.text(x+12, y+37, placeholder, 14, '#555555')

    def card(self, x, y, w, h, title, subtitle=''):
        self.rect(x, y, w, h)
        self.text(x+22, y+36, title, 20, '#172033', True)
        if subtitle:
            self.paragraph(x+22, y+66, subtitle, w-44, 14, '#555555')

    def save(self, name):
        p = OUT / f'{name}.svg'
        p.write_text('\n'.join(self.parts + ['</svg>']))
        subprocess.run(['rsvg-convert', '-o', str(p.with_suffix('.png')), str(p)], check=True)


def landing():
    s = Sheet('Portada: propuesta, horario y recorrido asistido', height=1310)
    s.text(44, 153, 'Cómo funciona       Puntos y horarios       Condiciones', 17)
    s.button(1140, 124, 250, 'Acceder a mi cuenta')
    s.card(40, 202, 1360, 310, 'Tu entrega, a su tiempo')
    s.paragraph(68, 292, 'Deja un objeto con constancia y permite que su destinatario lo recoja después.', 800, 31, '#0B368C', True)
    s.paragraph(68, 394, 'Custodia atendida por personal. El registro previo no reserva espacio.', 770, 19)
    s.button(68, 438, 230, 'Registrar objeto', True)
    s.button(320, 438, 240, 'Consultar estado')
    s.rect(967, 260, 400, 195, '#EDF2FC')
    s.text(987, 295, 'Punto de ejemplo', 21, '#0B368C', True)
    s.paragraph(987, 338, 'Horario ilustrativo: lunes a viernes, 09:00 a 18:00. Confirmar antes de acudir.', 360, 18)
    steps=[('1. Registra', 'Indica destinatario, descripción y punto desde tu cuenta.'),
           ('2. Déjalo en el punto', 'El operador confirma capacidad, tarifa y recepción.'),
           ('3. Retiro autorizado', 'El destinatario presenta su código y el personal entrega.')]
    for i,(title,body) in enumerate(steps):
        x=40+i*460
        s.card(x,548,440,235,title)
        s.paragraph(x+22,615,body,395,19)
    s.card(40,820,870,230,'Antes de dejar el objeto')
    for i,line in enumerate(['Consulta horario, tamaño y plazo.','La custodia empieza con la recepción confirmada.','El plazo vencido se gestiona con personal.','Guarda tu constancia y consulta el historial.']):
        s.text(64, 890+i*35, '• '+line, 18)
    s.card(940,820,460,230,'Información clara')
    s.paragraph(964,895,'La tarifa depende del tamaño y tiempo contratado. Se informa y acepta antes de recibir.',405,19)
    s.card(40,1084,1360,135,'¿Necesitas ayuda con una entrega?')
    s.text(64,1158,'Consulta tu cuenta o solicita atención al responsable del punto.',19)
    s.save('landing_page_wireframe')


def identity():
    s=Sheet('Identidad: confianza sustentada en el proceso', height=1180)
    s.card(40,145,1360,210,'BUZON Xpress · Tu entrega, a su tiempo')
    s.paragraph(65,220,'Servicio de custodia temporal asistida e intercambio asíncrono de objetos.',1100,30,'#0B368C',True)
    colors=[('#0B368C','Marca y navegación'),('#D91438','Acción principal'),('#172033','Texto'),('#F4F6FA','Fondo')]
    for i,(color,label) in enumerate(colors):
        x=40+i*345
        s.rect(x,395,325,125,color,'#AAB2C0')
        s.text(x+12,549,color,18,'#172033',True)
        s.text(x+12,582,label,16)
    s.card(40,620,660,270,'Misión propuesta')
    s.paragraph(65,700,'Facilitar intercambios de objetos mediante custodia atendida, verificación y constancia digital.',600,22)
    s.card(730,620,670,270,'Compromisos operativos')
    for i,line in enumerate(['Condiciones antes de recibir.','Constancia de cada movimiento.','Verificación antes de entregar.','Responsable ante diferencias.']):
        s.text(755,700+i*37,'• '+line,20)
    s.rect(40,930,1360,130,'#EDF2FC')
    s.paragraph(65,975,'El horario acompaña la promesa de marca. La evidencia proviene de operadores y registros; el sistema no controla físicamente el almacenamiento.',1300,21)
    s.save('corporate_identity_mockup')


def manifesto():
    s=Sheet('Manifiesto y ejemplos: objetos personales y compras locales',height=1220)
    s.text(44,165,'Una solución para dejar y recoger en momentos distintos',28,'#0B368C',True)
    cards=[('Objetos prestados','Devuelve un objeto aunque no coincidan los horarios. El destinatario lo recoge con autorización.'),
           ('Documentos y entregas personales','Deja un bulto identificable en un punto atendido y conserva una constancia.'),
           ('Compras locales','Una compra puede usar el servicio. BUZON Xpress cobra custodia; no liquida el precio al vendedor.'),
           ('Un proceso comprobable','Personal responsable, ubicación interna, verificación y registro de entrega. Sin dispositivos externos.')]
    for i,(title,body) in enumerate(cards):
        x=40+(i%2)*690; y=210+(i//2)*305
        s.card(x,y,665,275,title)
        s.paragraph(x+24,y+92,body,615,21)
    s.card(40,850,1360,255,'Antes de utilizar el servicio')
    s.paragraph(65,928,'1. Consulta el punto y su horario.   2. Revisa el plazo y la tarifa.   3. Registra un destinatario comprobado.',1280,21)
    s.paragraph(65,1010,'El prerregistro no reserva espacio. El retiro lo realiza personal después de verificar la autorización.',1280,20)
    s.save('manifesto_grid_mockup')


def suite():
    s=Sheet('Suite estructural: consulta, cuentas, custodias y supervisión',1600,1540,True)
    w=740; h=405
    for x,y,title,sub in [(40,140,'UI-02 · Consulta pública','Sin nombre, teléfono, código o ubicación interna.'),
                          (820,140,'UI-05 · Mis custodias','Participación: deposité / recibiré.'),
                          (40,580,'UI-06 · Registrar objeto','La capacidad se confirma al recibir.'),
                          (820,580,'UI-07 · Detalle privado','Visible solo a participantes y personal autorizado.'),
                          (40,1020,'UI-09 · Incidencias','Revisión separada de solicitud y aprobación.'),
                          (820,1020,'UI-10/11 · Supervisión','Datos ficticios para explicar la estructura.')]:
        s.card(x,y,w,h,title,sub)
    s.field(65,250,685,'Referencia pública','Referencia opaca de ejemplo')
    s.button(65,325,230,'Consultar estado',True)
    s.text(65,419,'RECIBIDA · Punto de ejemplo',22,bold=True)
    s.text(65,459,'Consulta horario y accede a tu cuenta para detalles.',16)
    s.text(845,252,'[Deposité]             [Recibiré]',20,bold=True)
    s.rect(845,280,685,90,'#F7F7F7')
    s.text(865,318,'Custodia de ejemplo · EN CUSTODIA',20,bold=True)
    s.text(865,349,'Punto y plazo contratado · Ver detalle',16)
    s.rect(845,395,685,90,'#F7F7F7')
    s.text(865,431,'Custodia de ejemplo · REGISTRADA',20,bold=True)
    s.text(865,462,'Pendiente de recepción; sin ubicación asignada.',16)
    s.field(65,690,685,'Destinatario','Contacto exacto de cuenta comprobada')
    s.field(65,768,685,'Descripción y tamaño','Bulto de prueba · PEQUEÑO')
    s.text(65,867,'Punto y condiciones antes de confirmar.',17)
    s.button(65,903,260,'Revisar y registrar',True)
    s.text(845,693,'EN CUSTODIA · Plazo visible',23,bold=True)
    s.paragraph(845,738,'Código de retiro: solo el destinatario puede generarlo. Se muestra una vez y tiene vigencia.',680,18)
    s.button(845,835,260,'Generar código',True)
    s.text(845,920,'Historial: recepción, avisos y comprobantes.',17)
    s.text(65,1130,'Custodia · Hechos · Responsable',20,bold=True)
    s.paragraph(65,1179,'Solicitud: pendiente. Otra persona autorizada revisa la evidencia antes de decidir.',670,18)
    s.button(65,1280,290,'Registrar solicitud',True)
    s.text(65,1358,'Sin decisión: mantener objeto y bloqueo.',17)
    s.text(845,1130,'Punto | Periodo | Calidad de datos',20,bold=True)
    s.text(845,1182,'Inventario: ubicaciones y custodias activas.',18)
    s.text(845,1230,'Indicadores: numerador y denominador.',18)
    s.text(845,1278,'Eventos: actor, fecha y correlación.',18)
    s.button(845,1332,270,'Consultar evidencia',True)
    s.save('bw_wireframes_suite')


def auth_terminal():
    s=Sheet('Acceso y terminal: verificar y confirmar son acciones distintas',1600,1450,True)
    for x,y,title,sub in [(40,140,'UI-03 · Acceso','Sin cuentas compartidas ni contraseñas universales.'),
                          (820,140,'UI-04 · Registro general','El registro público no concede roles de personal.'),
                          (40,650,'UI-08 · Recepción','Operador y punto identificados.'),
                          (820,650,'UI-08 · Retiro asistido','El personal realiza la entrega física.')]:
        s.card(x,y,740,470 if y==140 else 650,title,sub)
    s.field(65,254,685,'Correo','cuenta de ejemplo')
    s.field(65,332,685,'Contraseña','••••••••••••')
    s.button(65,418,250,'Acceder',True)
    s.text(65,526,'Sesión segura · Recuperar acceso',17)
    s.field(845,254,685,'Nombre y contacto','Datos de prueba')
    s.field(845,332,685,'Contraseña','Elegida por el usuario')
    s.button(845,418,300,'Crear cuenta general',True)
    s.text(845,526,'Comprobar contacto antes de operar.',17)
    s.field(65,764,685,'Guía de custodia','Buscar registro pendiente')
    s.field(65,842,685,'Ubicación interna','Seleccionar una ubicación disponible')
    s.text(65,946,'Revisar bulto, destinatario y condición externa.',18)
    s.text(65,990,'Confirmar tarifa, plazo y pago del servicio.',18)
    s.button(65,1042,300,'Confirmar recepción',True)
    s.paragraph(65,1158,'El éxito se muestra después de persistir. Si hay conflicto de capacidad, revisar antes de aceptar.',670,18)
    s.field(845,764,685,'Guía y código de retiro','Código ingresado manualmente')
    s.text(845,858,'[ ] Comprobación visual del destinatario',18)
    s.button(845,893,320,'1. Verificar autorización',True)
    s.text(845,980,'Autorizado para entregar · Bulto y ubicación',19,bold=True)
    s.paragraph(845,1025,'El objeto sigue bajo responsabilidad del punto hasta la entrega humana.',675,17)
    s.button(845,1100,685,'2. Confirmar que ya entregué el objeto',True)
    s.paragraph(845,1193,'Si falla después de entregar: confirmación pendiente. No repetir entrega; abrir conciliación.',670,17)
    s.text(40,1370,'Avisos e incidencias conservan hechos y responsables; no incluyen códigos secretos.',18)
    s.save('bw_auth_terminal_wireframes')


if __name__ == '__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    for make in [landing, identity, manifesto, suite, auth_terminal]: make()
    print('Cinco láminas SVG y cinco PNG generadas.')
