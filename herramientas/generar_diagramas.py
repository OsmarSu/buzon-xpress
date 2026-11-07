"""Extrae Mermaid y genera vistas equivalentes con Graphviz para impresión."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/diagramas'
STYLE = '''graph [bgcolor="white",pad="0.4",nodesep="0.5",ranksep="0.8",fontname="DejaVu Sans"];
node [shape=box,style="rounded,filled",fillcolor="#EDF2FC",color="#0B368C",fontname="DejaVu Sans",fontsize=16,margin="0.2"];
edge [color="#556276",fontname="DejaVu Sans",fontsize=12];'''

def render(name, content):
    p=OUT/(name+'.dot')
    p.write_text('digraph G {\n'+STYLE+'\n'+content+'\n}\n')
    for ext in ['svg','png']:
        subprocess.run(['dot','-T'+ext,str(p),'-o',str(p.with_suffix('.'+ext))],check=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    mermaid=[]
    for file in sorted((ROOT/'docs/ingenieria').glob('*.md')):
        for i,block in enumerate(re.findall(r'```mermaid\n(.*?)```',file.read_text(),re.S),1):
            name=f'{file.stem}_{i:02}.mmd'
            (OUT/name).write_text(block)
            mermaid.append(name)
    render('c4_contexto','''rankdir=LR;
emisor [label="Emisor y destinatario"];
operador [label="Personal del punto"];
admin [label="Administración y auditoría"];
sistema [label="BUZON Xpress\nPlataforma de custodia asistida",fillcolor="#0B368C",fontcolor="white"];
correo [label="Correo configurable\nServicio de software"];
emisor -> sistema [label="registro, consulta y credencial"];
operador -> sistema [label="recepción y entrega registradas"];
admin -> sistema [label="configuración y revisión"];
sistema -> correo [label="aviso sin código secreto"];
operador -> emisor [style=dashed,label="entrega material por personal"];
''')
    render('c4_contenedores','''rankdir=LR;
navegador [label="Navegador\nEquipo existente"];
api [label="Aplicación FastAPI\nCasos de uso y permisos"];
db [label="PostgreSQL\nEstado y evidencia",shape=cylinder];
tarea [label="Tarea de la aplicación\nAvisos y vencimientos"];
correo [label="Correo configurado"];
navegador -> api [label="HTTPS, sesión y CSRF"];
api -> db [label="transacciones"];
tarea -> db [label="pendientes y resultado"];
tarea -> correo [label="envío y reintento"];
''')
    render('c4_componentes','''rankdir=TB;
http [label="Adaptador HTTP"];
aplicacion [label="Casos de uso\nPermisos y unidad de trabajo"];
dominio [label="Dominio\nCustodia, credencial, autorización"];
puertos [label="Puertos\nRepositorio, reloj, avisos"];
sql [label="Adaptador SQLAlchemy"];
mail [label="Adaptador de correo"];
http -> aplicacion;
aplicacion -> dominio;
aplicacion -> puertos;
sql -> puertos [style=dashed,label="implementa"];
mail -> puertos [style=dashed,label="implementa"];
''')
    render('estados_custodia','''rankdir=TB;
registrada [label="REGISTRADA\nSin ocupación"];
guardada [label="EN_CUSTODIA\nAsignación activa"];
curso [label="RETIRO_EN_CURSO\nPreparación retenida"];
retirada [label="RETIRADA\nSalida confirmada"];
devolucion [label="DEVOLUCION_EN_CURSO"];
devuelta [label="DEVUELTA"];
cancelada [label="CANCELADA"];
registrada -> guardada [label="recepción, ubicación y pago"];
registrada -> cancelada [label="antes de recibir"];
guardada -> curso [label="verificación válida"];
curso -> retirada [label="entrega humana confirmada"];
curso -> guardada [label="no entregado; anulación controlada"];
guardada -> devolucion [label="devolución aprobada"];
devolucion -> devuelta [label="entrega al emisor confirmada"];
devolucion -> guardada [label="no entregado; anulación"];
nota [shape=note,fillcolor="#FFF6D8",label="Vencimiento e incidencias no eliminan posesión.\nUn corte tras entregar requiere conciliación."];
nota -> curso [style=dashed,arrowhead=none];
''')
    relations='''rankdir=LR;
users -> sessions;
users -> staff_assignments;
service_points -> staff_assignments;
service_points -> storage_locations;
service_points -> tariff_versions;
users -> custody_orders [label="emisor / destinatario"];
service_points -> custody_orders;
tariff_versions -> custody_orders;
custody_orders -> storage_assignments;
storage_locations -> storage_assignments;
custody_orders -> pickup_credentials;
custody_orders -> pickup_authorizations;
pickup_credentials -> pickup_authorizations;
custody_orders -> recovery_requests;
recovery_requests -> pickup_authorizations;
pickup_authorizations -> handovers;
custody_orders -> custody_events;
custody_orders -> notifications;
custody_orders -> incidents;
custody_orders -> service_payments;
users -> idempotency_keys;
'''
    render('entidades_relaciones',relations)
    rows=['# Diagramas de arquitectura y análisis','','Los archivos Mermaid se extraen de los documentos de ingeniería. Las vistas DOT/SVG/PNG son representaciones equivalentes diseñadas para lectura e impresión; Graphviz no se presenta como un renderizador de Mermaid.','','| Vista | SVG | PNG | Fuente editable |','|---|---|---|---|']
    for name,label in [('c4_contexto','Contexto'),('c4_contenedores','Contenedores'),('c4_componentes','Componentes'),('estados_custodia','Estados'),('entidades_relaciones','Relaciones de datos')]:
        rows.append(f'| {label} | [Ver]({name}.svg) | [Ver]({name}.png) | [DOT]({name}.dot) |')
    rows+=['','## Fuentes Mermaid','']+[f'- [{name}]({name})' for name in mermaid]
    (OUT/'README.md').write_text('\n'.join(rows)+'\n')
    print(f'{len(mermaid)} fuentes Mermaid y cinco vistas DOT/SVG/PNG generadas.')

if __name__=='__main__': main()
