"""Alternativa local de PDF/HTML cuando LibreOffice no puede convertir."""
from pathlib import Path
from html import escape
import os
import re

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QTextDocument, QPageLayout, QPageSize
from PySide6.QtCore import QMarginsF, QUrl
from PySide6.QtPrintSupport import QPrinter
from markdown_it import MarkdownIt

from exportar_documentos import ROOT, OUT, ORDER, DIAGRAMS

CSS='''
body {font-family:"DejaVu Sans";font-size:10pt;color:#172033;}
h1 {font-size:19pt;color:#0B368C;margin-top:16pt;}
h2 {font-size:14pt;color:#0B368C;margin-top:14pt;}
h3 {font-size:11pt;color:#0B368C;}
p {margin-top:5pt;margin-bottom:7pt;}
table {border-collapse:collapse;width:100%;margin-top:8pt;margin-bottom:10pt;}
th {background-color:#E5ECF9;font-weight:bold;}
td,th {border:1px solid #B9C4D8;padding:5px;font-size:8pt;vertical-align:top;}
pre {font-family:"DejaVu Sans Mono";font-size:7pt;white-space:pre-wrap;background-color:#F4F6FA;}
code {font-family:"DejaVu Sans Mono";font-size:8pt;}
a {color:#0B368C;}
.chapter {page-break-before:always;}
.caption {font-size:8pt;color:#555555;}
'''


def picture(path,width=610):
    from PIL import Image
    with Image.open(path) as im: w,h=im.size
    # Píxeles CSS a 96 ppp; una lámina debe caber dentro de una página.
    width=min(width,int(800*w/h))
    return f'<p align="center"><img src="{escape(os.path.relpath(path,OUT))}" width="{width}"></p>'


def chapter(source):
    text=source.read_text()
    i=0
    def diagram(match):
        nonlocal i
        i+=1
        name=DIAGRAMS.get((source.name,i))
        if name:
            return picture(ROOT/'docs/diagramas'/f'{name}.png')+'\n\n'
        return match.group(0)
    text=re.sub(r'```mermaid\n.*?```',diagram,text,flags=re.S)
    parser=MarkdownIt('default',{'html':True})
    tokens=parser.parse(text)
    def walk(items):
        for t in items:
            if t.type in ['link_open','image']:
                attr='href' if t.type=='link_open' else 'src'
                target=t.attrGet(attr)
                if target and not re.match(r'^[a-zA-Z]+:|^#',target):
                    t.attrSet(attr,os.path.relpath((source.parent/target).resolve(),OUT))
            if t.children: walk(t.children)
    walk(tokens)
    return '<div class="chapter">'+parser.renderer.render(tokens,parser.options,{})+'</div>'


def cover(title):
    return f'''<h1>BUZON Xpress</h1><h2>{escape(title)}</h2>
    <p>Custodia temporal asistida e intercambio asíncrono de objetos</p>
    <p>26 de octubre de 2026 · La Paz, Bolivia · Versión documental 1.0</p>
    <p>La plataforma utiliza equipos y espacio existentes. La recepción y la entrega son realizadas por personal; no se integra hardware externo.</p>
    <p>Estado: diseño propuesto. Las pruebas de producto, demanda y resultados económicos están pendientes de ejecución.</p>'''


def export(name,body):
    full=f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'
    (OUT/(name+'.html')).write_text(full)
    doc=QTextDocument()
    doc.setBaseUrl(QUrl.fromLocalFile(str(OUT)+'/'))
    doc.setHtml(full)
    doc.setDocumentMargin(0)
    printer=QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setResolution(144)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(OUT/(name+'.pdf')))
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageMargins(QMarginsF(17,18,17,18),QPageLayout.Unit.Millimeter)
    printer.setDocName(name)
    doc.print_(printer)
    print(f'PDF generado mediante Qt: {name}')


def main():
    app=QApplication.instance() or QApplication(['buzon-documentos','-platform','offscreen'])
    export('Perfil_Proyecto_BUZON_Xpress',cover('Perfil del proyecto reformulado')+chapter(ROOT/ORDER[0]))
    index='<h1 class="chapter">Índice de documentos</h1><ol>'
    for rel in ORDER:
        index+='<li>'+escape((ROOT/rel).read_text().splitlines()[0].lstrip('# '))+'</li>'
    index+='<li>Galería de interfaces</li></ol>'
    content=cover('Dossier de reformulación')+index+''.join(chapter(ROOT/rel) for rel in ORDER)
    for name,label in [('landing_page_wireframe','Portada'),('corporate_identity_mockup','Identidad'),('manifesto_grid_mockup','Manifiesto y ejemplos'),('bw_wireframes_suite','Suite estructural'),('bw_auth_terminal_wireframes','Acceso y terminal')]:
        content+='<h1 class="chapter">'+label+'</h1>'+picture(ROOT/'docs/wireframes'/f'{name}.png')+'<p class="caption">Diseño estático con datos ficticios. SVG editable incluido en el proyecto.</p>'
    export('Dossier_Reformulacion_BUZON_Xpress',content)

if __name__=='__main__': main()
