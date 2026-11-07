"""Exporta el perfil y el dossier a Word/PDF, conservando tablas y enlaces."""
from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import urlparse, unquote
from zipfile import ZipFile
import os
import re
import subprocess
import textwrap

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from markdown_it import MarkdownIt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'entregables'
PARSER=MarkdownIt('default')

ORDER=[
    'docs/perfil/Perfil_Proyecto_BUZON_Xpress.md',
    'docs/gestion/01_decisiones_y_correspondencia.md',
    'docs/metodologia/01_marcos_y_aplicacion.md',
    'docs/metodologia/02_bibliografia_verificada.md',
    'docs/negocio/BuzonExpress_Formulacion_Negocio.md',
    'docs/negocio/02_demanda_costos_y_evaluacion.md',
    'docs/ingenieria/BuzonExpress_Especificacion_Software.md',
    'docs/ingenieria/01_modelado_analisis_pressman.md',
    'docs/ingenieria/02_modelado_diseno_ui.md',
    'docs/ingenieria/03_modelado_datos_arquitectura.md',
    'docs/ingenieria/04_propuestas_wireframes_identidad.md',
    'docs/ingenieria/05_wireframes_estructurales_bn.md',
    'docs/ingenieria/06_casos_de_uso_alto_nivel_y_expandidos.md',
    'docs/ingenieria/07_contratos_api_y_seguridad.md',
    'docs/ingenieria/08_guia_tecnica_y_despliegue.md',
    'docs/operacion/01_manual_operativo.md',
    'docs/gestion/02_plan_implementacion.md',
    'docs/gestion/03_matriz_trazabilidad.md',
    'docs/validacion/01_plan_validacion.md',
]

DIAGRAMS={
    ('01_modelado_analisis_pressman.md',3):'estados_custodia',
    ('03_modelado_datos_arquitectura.md',1):'c4_contexto',
    ('03_modelado_datos_arquitectura.md',2):'c4_contenedores',
    ('03_modelado_datos_arquitectura.md',3):'c4_componentes',
    ('03_modelado_datos_arquitectura.md',4):'entidades_relaciones',
}


def setup(title,subtitle):
    doc=Document()
    sec=doc.sections[0]
    sec.page_width=Inches(8.27)
    sec.page_height=Inches(11.69)
    sec.top_margin=sec.bottom_margin=Inches(.72)
    sec.left_margin=sec.right_margin=Inches(.7)
    normal=doc.styles['Normal']
    normal.font.name='DejaVu Sans'
    normal.font.size=Pt(10)
    normal.paragraph_format.space_after=Pt(6)
    for name in ['Heading 1','Heading 2','Heading 3','Heading 4']:
        doc.styles[name].font.name='DejaVu Sans'
        doc.styles[name].font.color.rgb=RGBColor.from_string('0B368C')
    header=sec.header.paragraphs[0]
    header.text='BUZON Xpress · Custodia temporal asistida'
    header.style=doc.styles['Caption']
    footer=sec.footer.paragraphs[0]
    footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run('Propuesta documental 1.0 · ')
    fld=OxmlElement('w:fldSimple')
    fld.set(qn('w:instr'),'PAGE')
    footer._p.append(fld)
    doc.core_properties.title=title
    doc.core_properties.subject='Reformulación sin hardware externo'
    doc.core_properties.author='Documentación del proyecto BUZON Xpress'
    doc.add_paragraph('BUZON Xpress',style='Title')
    doc.add_paragraph(title,style='Subtitle')
    doc.add_paragraph(subtitle)
    doc.add_paragraph('26 de octubre de 2026 · La Paz, Bolivia')
    doc.add_paragraph('Custodia por personal, autorización digital y trazabilidad. Utiliza equipos y espacio existentes; no requiere integración con hardware externo.')
    doc.add_paragraph('Estado: diseño propuesto. Las pruebas de producto, demanda y resultados económicos permanecen pendientes de ejecución.')
    doc.add_page_break()
    return doc


def link(paragraph,text,target,source):
    if not urlparse(target).scheme:
        target=os.path.relpath((source.parent/unquote(target)).resolve(),OUT)
    rel=paragraph.part.relate_to(target,RT.HYPERLINK,is_external=True)
    hyp=OxmlElement('w:hyperlink')
    hyp.set(qn('r:id'),rel)
    run=OxmlElement('w:r')
    prop=OxmlElement('w:rPr')
    color=OxmlElement('w:color'); color.set(qn('w:val'),'0B368C'); prop.append(color)
    underline=OxmlElement('w:u'); underline.set(qn('w:val'),'single'); prop.append(underline)
    run.append(prop)
    value=OxmlElement('w:t'); value.text=text; run.append(value)
    hyp.append(run); paragraph._p.append(hyp)


def inline(paragraph,content,source):
    tokens=PARSER.parseInline(content)[0].children or []
    bold=italic=False
    i=0
    while i<len(tokens):
        t=tokens[i]
        if t.type=='strong_open': bold=True
        elif t.type=='strong_close': bold=False
        elif t.type=='em_open': italic=True
        elif t.type=='em_close': italic=False
        elif t.type=='link_open':
            text=''; j=i+1
            while j<len(tokens) and tokens[j].type!='link_close':
                text+=tokens[j].content; j+=1
            link(paragraph,text,t.attrGet('href'),source); i=j
        elif t.type in ['text','code_inline','softbreak','hardbreak']:
            value='\n' if t.type in ['softbreak','hardbreak'] else t.content
            run=paragraph.add_run(value)
            run.bold=bold; run.italic=italic
            if t.type=='code_inline': run.font.name='DejaVu Sans Mono'; run.font.size=Pt(8)
        i+=1


def picture(doc,path,width=6.65):
    from PIL import Image
    with Image.open(path) as im: w,h=im.size
    max_height=8.6
    actual=min(width,max_height*w/h)
    p=doc.add_paragraph()
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path),width=Inches(actual))


def render(doc,source):
    tokens=PARSER.parse(source.read_text())
    i=0; list_stack=[]; diagram_no=0
    while i<len(tokens):
        t=tokens[i]
        if t.type=='heading_open':
            level=min(4,int(t.tag[1:]))
            p=doc.add_paragraph(style=f'Heading {level}')
            inline(p,tokens[i+1].content,source); i+=2
        elif t.type in ['bullet_list_open','ordered_list_open']:
            list_stack.append(t.type)
        elif t.type in ['bullet_list_close','ordered_list_close']:
            list_stack.pop()
        elif t.type=='paragraph_open':
            if tokens[i+1].type=='inline':
                style='List Number' if list_stack and list_stack[-1]=='ordered_list_open' else 'List Bullet' if list_stack else 'Normal'
                p=doc.add_paragraph(style=style)
                inline(p,tokens[i+1].content,source)
                i+=2
        elif t.type=='table_open':
            rows=[]; row=[]; j=i+1
            while j<len(tokens) and tokens[j].type!='table_close':
                if tokens[j].type=='tr_open': row=[]
                elif tokens[j].type in ['th_open','td_open']:
                    row.append(tokens[j+1].content)
                elif tokens[j].type=='tr_close': rows.append(row)
                j+=1
            if rows:
                table=doc.add_table(rows=0,cols=max(map(len,rows)))
                table.style='Light Shading Accent 1'
                for ri,values in enumerate(rows):
                    cells=table.add_row().cells
                    for cell,value in zip(cells,values):
                        inline(cell.paragraphs[0],value,source)
                        for run in cell.paragraphs[0].runs: run.font.size=Pt(8)
                    if ri==0:
                        repeat=OxmlElement('w:tblHeader'); table.rows[-1]._tr.get_or_add_trPr().append(repeat)
                doc.add_paragraph()
            i=j
        elif t.type=='fence':
            if t.info.strip()=='mermaid':
                diagram_no+=1
                name=DIAGRAMS.get((source.name,diagram_no))
                if name:
                    picture(doc,ROOT/'docs/diagramas'/f'{name}.png')
                    doc.add_paragraph('Vista equivalente; fuente Mermaid editable en el proyecto.',style='Caption')
                else:
                    p=doc.add_paragraph()
                    p.paragraph_format.space_after=Pt(7)
                    run=p.add_run(t.content)
                    run.font.name='DejaVu Sans Mono'; run.font.size=Pt(7)
            else:
                p=doc.add_paragraph()
                p.paragraph_format.space_after=Pt(8)
                p.paragraph_format.line_spacing=1
                lines=[]
                for line in t.content.splitlines():
                    lines.extend(textwrap.wrap(line,105,replace_whitespace=False,drop_whitespace=False) or [''])
                run=p.add_run('\n'.join(lines))
                run.font.name='DejaVu Sans Mono'; run.font.size=Pt(7.5)
        i+=1


def main():
    OUT.mkdir(exist_ok=True)
    profile=setup('Perfil del proyecto reformulado','Plataforma web para la custodia temporal asistida y el intercambio asíncrono de objetos')
    render(profile,ROOT/ORDER[0])
    profile.save(OUT/'Perfil_Proyecto_BUZON_Xpress.docx')
    book=setup('Dossier de reformulación','Negocio, metodologías, ingeniería, interfaces, operación y validación')
    book.add_heading('Índice de documentos',1)
    for n,rel in enumerate(ORDER,1):
        title=(ROOT/rel).read_text().splitlines()[0].lstrip('# ')
        book.add_paragraph(f'{n}. {title}')
    book.add_paragraph(f'{len(ORDER)+1}. Galería de las cinco láminas de interfaz')
    for rel in ORDER:
        book.add_page_break()
        render(book,ROOT/rel)
    book.add_page_break()
    book.add_heading('Galería de interfaces',1)
    for name,label in [('landing_page_wireframe','Portada'),('corporate_identity_mockup','Identidad'),('manifesto_grid_mockup','Manifiesto y ejemplos'),('bw_wireframes_suite','Suite estructural'),('bw_auth_terminal_wireframes','Acceso y terminal')]:
        book.add_heading(label,2)
        picture(book,ROOT/'docs/wireframes'/f'{name}.png')
        book.add_paragraph('Diseño estático con datos ficticios. Archivo editable en docs/wireframes.',style='Caption')
        if name!='bw_auth_terminal_wireframes': book.add_page_break()
    book.save(OUT/'Dossier_Reformulacion_BUZON_Xpress.docx')
    profile_dir=Path(mkdtemp(prefix='buzon-xpress-lo-'))
    command=['libreoffice','--headless',f'-env:UserInstallation={profile_dir.as_uri()}','--convert-to','pdf','--outdir',str(OUT),str(OUT/'Perfil_Proyecto_BUZON_Xpress.docx'),str(OUT/'Dossier_Reformulacion_BUZON_Xpress.docx')]
    result=subprocess.run(command,capture_output=True,text=True,timeout=180)
    if result.returncode:
        print('LibreOffice no completó la conversión; se utiliza la alternativa local de Qt.')
        from exportar_pdf_qt import main as qt_export
        qt_export()
    else:
        print(result.stdout)
    for name in ['Perfil_Proyecto_BUZON_Xpress','Dossier_Reformulacion_BUZON_Xpress']:
        assert (OUT/(name+'.pdf')).is_file(),name
    print('Perfil y dossier exportados a DOCX y PDF.')

if __name__=='__main__': main()
