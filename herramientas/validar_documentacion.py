"""Comprueba integridad y coherencia documental; no prueba la aplicación."""
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree
from zipfile import ZipFile
import csv
import hashlib
import json
import re
import yaml
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors=[]
    checks=[]
    def check(condition,message):
        (checks if condition else errors).append(message)
    report_path = ROOT / 'docs/validacion/03_verificacion_linea_base.md'
    docs = sorted(ROOT.glob('*.md'))
    for directory in ('docs', 'entregables', 'herramientas'):
        docs.extend(sorted((ROOT / directory).rglob('*.md')))
    docs = [p for p in docs if p != report_path]
    broken=[]
    for p in docs:
        content=p.read_text()
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',content):
            target=target.strip().strip('<>')
            if re.match(r'^(https?://|mailto:|#)',target): continue
            local=unquote(target.split('#')[0])
            if not (p.parent/local).exists(): broken.append(f'{p.relative_to(ROOT)} -> {local}')
        check(content.count('```')%2==0,f'Bloques de código equilibrados: {p.relative_to(ROOT)}')
    check(not broken,'Enlaces locales vigentes: '+('; '.join(broken) if broken else 'sin enlaces rotos'))
    manifest=json.loads((ROOT/'referencias/manifest_fuentes.json').read_text())
    expected_gaps = {
        'referencias/original/backend/database/schema.sql',
        'referencias/original/docker-compose.yml',
    }
    observations = []
    verified_archives = 0
    for item in manifest:
        archive = ROOT / item['archive']
        if not archive.is_file() and item['archive'] in expected_gaps:
            observations.append(f"Copia histórica ausente: {item['archive']}")
        elif archive.is_file() and hashlib.sha256(archive.read_bytes()).hexdigest() == item['sha256']:
            verified_archives += 1
        else:
            errors.append(f"Copia histórica ausente o con hash diferente: {item['archive']}")
    checks.append(f'Copias históricas verificadas: {verified_archives} de {len(manifest)}')
    originals=list((ROOT/'referencias/original/docs').rglob('*.md'))
    check(len(originals)==8 and all((ROOT/'docs'/p.relative_to(ROOT/'referencias/original/docs')).exists() for p in originals),'Ocho documentos principales con equivalente reformulado')
    catalog=json.loads((ROOT/'docs/ingenieria/anexos/catalogo_requisitos.json').read_text())
    check(len(catalog['requirements'])==18 and len(catalog['quality'])==12 and len(catalog['rules'])==14,'Catálogo: 18 RF, 12 RNF y 14 reglas')
    cases=(ROOT/'docs/ingenieria/06_casos_de_uso_alto_nivel_y_expandidos.md').read_text()
    check(len(re.findall(r'^## \d+\. CU-\d{2} —',cases,re.M))==12,'Doce casos de uso expandidos')
    sql=(ROOT/'docs/ingenieria/anexos/modelo_propuesto.sql').read_text()
    tables=set(re.findall(r'CREATE TABLE (\w+)',sql))
    dictionary=(ROOT/'docs/ingenieria/03_modelado_datos_arquitectura.md').read_text()
    check(len(tables)==17 and all(f'### Tabla `{t}`' in dictionary for t in tables),'Diecisiete tablas en SQL y diccionario')
    missing_tables=[(r['id'],t) for r in catalog['requirements'] for t in r['tables'] if t not in tables]
    check(not missing_tables,'Tablas de la matriz presentes en el modelo')
    referenced=set(re.findall(r'REFERENCES (\w+)\(',sql))
    check(referenced <= tables,'Referencias de tablas SQL resueltas')
    # Balance léxico: no constituye validación por un motor PostgreSQL.
    clean=re.sub(r'--[^\n]*','',sql)
    clean=re.sub(r'\$\$.*?\$\$','',clean,flags=re.S)
    clean=re.sub(r"'(?:''|[^'])*'",'',clean)
    balance=0
    valid=True
    for c in clean:
        balance+=(c=='(')-(c==')')
        valid=valid and balance>=0
    check(valid and balance==0,'Delimitadores SQL equilibrados; sin ejecución en motor')
    spec=yaml.safe_load((ROOT/'docs/ingenieria/anexos/openapi.yaml').read_text())
    validate(spec)
    checks.append(f"Contrato conforme al esquema OpenAPI {spec['openapi']}")
    refs=[]
    def walk(node):
        if isinstance(node,dict):
            if '$ref' in node: refs.append(node['$ref'])
            for v in node.values(): walk(v)
        elif isinstance(node,list):
            for v in node: walk(v)
    walk(spec)
    missing=[]
    for ref in refs:
        cur=spec
        try:
            for key in ref.removeprefix('#/').split('/'):
                cur=cur[key.replace('~1','/').replace('~0','~')]
        except (KeyError,TypeError): missing.append(ref)
    check(not missing,'Referencias internas OpenAPI resueltas')
    operation_ids=[]
    route_errors=[]
    for path,item in spec['paths'].items():
        for method,op in item.items():
            operation_ids.append(op['operationId'])
            actual={p['name'] for p in op.get('parameters',[]) if isinstance(p,dict) and p.get('in')=='path' and p.get('required')}
            if actual!=set(re.findall(r'\{(\w+)\}',path)): route_errors.append(path)
    check(len(operation_ids)==len(set(operation_ids)) and not route_errors,'Operaciones OpenAPI únicas y parámetros de ruta completos')
    missing_paths=[path for r in catalog['requirements'] for path in r['paths'] if path not in spec['paths']]
    check(not missing_paths,'Rutas de trazabilidad presentes en OpenAPI')
    with (ROOT/'docs/validacion/resultados_pruebas.csv').open() as file: results=list(csv.DictReader(file))
    expected={r['test'] for r in catalog['requirements']+catalog['quality']}
    check({r['prueba'] for r in results}==expected and all(r['resultado']=='PENDIENTE' for r in results),'Treinta pruebas catalogadas como pendientes; sin resultados fabricados')
    svg=list((ROOT/'docs/wireframes').glob('*.svg'))
    for p in svg: ElementTree.parse(p)
    check(len(svg)==5 and all(p.with_suffix('.png').exists() for p in svg),'Cinco wireframes SVG válidos con copias PNG')
    docx=list((ROOT/'entregables').glob('*.docx'))
    for p in docx:
        with ZipFile(p) as z:
            check(z.testzip() is None and 'word/document.xml' in z.namelist(),'DOCX íntegro: '+p.name)
    check(len(docx)==2 and len(list((ROOT/'entregables').glob('*.pdf')))==2,'Perfil y dossier disponibles en Word y PDF')
    status = 'ERROR' if errors else 'APROBADA_CON_OBSERVACIONES' if observations else 'APROBADA'
    summary = {
        'baseline': '1.1',
        'status': status,
        'document_checks': len(checks),
        'errors': errors,
        'observations': observations,
        'verified_historical_copies': verified_archives,
        'expected_historical_copies': len(manifest),
        'functional_requirements': len(catalog['requirements']),
        'quality_requirements': len(catalog['quality']),
        'business_rules': len(catalog['rules']),
        'tables': len(tables),
        'api_operations': len(operation_ids),
        'planned_product_tests': len(results),
        'product_tests_executed': 0,
    }
    output = ROOT / 'docs/validacion/revision_linea_base.json'
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = [
        '# Verificación de la línea base 1.1', '',
        f'Estado documental **{status}**.', '',
        'La verificación reúne la especificación, el contrato OpenAPI, el diccionario, los entregables y la trazabilidad.',
        'El ensayo de restricciones en PostgreSQL se ejecuta con [verificar-esquema.sh](../../infra/verificar-esquema.sh).',
        'Las treinta pruebas funcionales del futuro producto siguen pendientes.', '',
        '## Comprobaciones', '',
        *[f'- {message}' for message in checks],
    ]
    if observations:
        report.extend(['', '## Observaciones de procedencia', '', *[f'- {message}' for message in observations]])
    if errors:
        report.extend(['', '## Errores', '', *[f'- {message}' for message in errors]])
    report_path.write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)

if __name__=='__main__': main()
