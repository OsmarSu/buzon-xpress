"""Genera anexos y trazabilidad desde la especificación y el SQL documentados."""
from pathlib import Path
import json
import csv
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'docs/ingenieria'
ANNEX = ENG / 'anexos'

MAPPING = {
    1: ('users sessions mfa_login_challenges mfa_recovery_codes', 'UI-03 UI-04', '/auth/register /auth/login /auth/logout /auth/mfa /auth/mfa/setup /auth/mfa/confirm /auth/mfa/verify /auth/mfa/disable /auth/mfa/recovery-codes'),
    2: ('users staff_assignments sessions', 'UI-03 UI-08', '/auth/me'),
    3: ('custody_orders custody_events', 'UI-06', '/custodies'),
    4: ('custody_orders storage_assignments storage_locations service_payments', 'UI-08', '/custodies/{custody_id}/receive'),
    5: ('storage_assignments storage_locations', 'UI-08', '/inventory'),
    6: ('custody_orders custody_events', 'UI-02 UI-05 UI-07', '/custodies/{custody_id} /public-tracking/{reference}'),
    7: ('pickup_credentials', 'UI-07', '/custodies/{custody_id}/credentials'),
    8: ('pickup_credentials pickup_authorizations custody_orders', 'UI-08', '/custodies/{custody_id}/verify'),
    9: ('handovers pickup_authorizations storage_assignments custody_orders', 'UI-08', '/custodies/{custody_id}/handover'),
    10: ('recovery_requests pickup_authorizations handovers', 'UI-09', '/custodies/{custody_id}/return-authorization /custodies/{custody_id}/return-handover'),
    11: ('notifications', 'UI-12', '/notifications'),
    12: ('tariff_versions service_payments custody_orders', 'UI-08', '/points/{point_id}/quote /custodies/{custody_id}/receive /custodies/{custody_id}/extend'),
    13: ('custody_orders notifications service_payments', 'UI-07 UI-08', '/custodies/{custody_id}/extend'),
    14: ('incidents recovery_requests', 'UI-09', '/custodies/{custody_id}/incidents /recovery-requests /recovery-requests/{request_id}/decision'),
    15: ('custody_events', 'UI-11', '/audit/events'),
    16: ('service_points storage_locations staff_assignments tariff_versions', 'UI-10', '/admin/points /admin/locations /admin/staff-assignments /admin/tariffs'),
    17: ('custody_orders custody_events handovers incidents', 'UI-11', '/reports'),
    18: ('idempotency_keys handovers', 'UI-08 UI-09', '/custodies/{custody_id}/handover /custodies/{custody_id}/abort-handover'),
}


def catalogs():
    source = (ENG / 'BuzonExpress_Especificacion_Software.md').read_text()
    with (ROOT / 'docs/validacion/resultados_pruebas.csv').open() as source_results:
        results = {row['prueba']: row for row in csv.DictReader(source_results)}
    requirements = []
    for rid, priority, statement, case in re.findall(r'^\| (RF-\d{2}) \| (P[01]) \| (.*?) \| (CU-\d{2}) \|$', source, re.M):
        n = int(rid[-2:])
        tables, screens, endpoints = MAPPING[n]
        requirements.append(dict(id=rid, priority=priority, statement=statement, use_case=case,
                                 tables=tables.split(), screens=screens.split(), paths=endpoints.split(),
                                 test=f'T-{n:02}', status=results[f'T-{n:02}']['resultado']))
    quality = [dict(id=rid, category=cat, statement=statement, test=f'T-{int(rid[-2:])+18:02}', status=results[f'T-{int(rid[-2:])+18:02}']['resultado'])
               for rid, cat, statement in re.findall(r'^\| (RNF-\d{2}) \| (.*?) \| (.*?) \|$', source, re.M)]
    rules = [dict(id=rid, statement=text) for rid, text in re.findall(r'^\| (RN-\d{2}) \| (.*?) \|$', source, re.M)]
    assert len(requirements) == 18 and len(quality) == 12 and len(rules) == 14
    (ANNEX / 'catalogo_requisitos.json').write_text(json.dumps(dict(version='1.2', requirements=requirements, quality=quality, rules=rules), ensure_ascii=False, indent=2) + '\n')
    # Conservar las notas y evidencias vigentes; regenerar solo la tabla funcional.
    matrix_path = ROOT / 'docs/gestion/03_matriz_trazabilidad.md'
    matrix = matrix_path.read_text()
    rows = ['## Requisitos funcionales', '', '| Requisito | Caso | Datos | Pantalla | API | Prueba |',
            '|---|---|---|---|---|---|']
    for requirement in requirements:
        rows.append(f"| {requirement['id']} | {requirement['use_case']} | {', '.join(requirement['tables'])} | {', '.join(requirement['screens'])} | {'; '.join(requirement['paths'])} | {requirement['test']} |")
    rows += ['', '']
    matrix = re.sub(r'## Requisitos funcionales\n.*?(?=## Calidad)', lambda _: '\n'.join(rows),
                    matrix, flags=re.S)
    matrix_path.write_text(matrix)


def dictionary():
    sql = (ANNEX / 'modelo_propuesto.sql').read_text()
    parts = []
    for name, block in re.findall(r'CREATE TABLE (\w+) \((.*?)\n\);', sql, re.S):
        parts += [f'### Tabla `{name}`', '', '| Campo | Definición SQL | Propósito |', '|---|---|---|']
        for line in block.splitlines():
            if '--' not in line:
                continue
            declaration, description = line.strip().split('--', 1)
            field, definition = declaration.rstrip(' ,').split(None, 1)
            parts.append(f'| `{field}` | `{definition}` | {description.strip()} |')
        parts.append('')
    assert len(re.findall(r'^### Tabla', '\n'.join(parts), re.M)) == len(re.findall(r'CREATE TABLE ', sql))
    p = ENG / '03_modelado_datos_arquitectura.md'
    text = p.read_text()
    marker = '<!-- DICCIONARIO_GENERADO -->'
    p.write_text(text.split(marker)[0] + marker + '\n\n' + '\n'.join(parts))


def api():
    """OpenAPI es fuente canónica: validar sin reconstruir contratos obsoletos."""
    from openapi_spec_validator import validate
    validate(yaml.safe_load((ANNEX / 'openapi.yaml').read_text()))


if __name__ == '__main__':
    catalogs()
    dictionary()
    api()
    print('Catálogo, trazabilidad y diccionario actualizados; OpenAPI canónico validado.')
