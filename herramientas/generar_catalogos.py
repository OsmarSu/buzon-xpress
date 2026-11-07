"""Genera anexos y trazabilidad desde la especificación y el SQL documentados."""
from pathlib import Path
import json
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
ENG = ROOT / 'docs/ingenieria'
ANNEX = ENG / 'anexos'

MAPPING = {
    1: ('users sessions', 'UI-03 UI-04', '/auth/register /auth/login /auth/logout'),
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
    requirements = []
    for rid, priority, statement, case in re.findall(r'^\| (RF-\d{2}) \| (P[01]) \| (.*?) \| (CU-\d{2}) \|$', source, re.M):
        n = int(rid[-2:])
        tables, screens, endpoints = MAPPING[n]
        requirements.append(dict(id=rid, priority=priority, statement=statement, use_case=case,
                                 tables=tables.split(), screens=screens.split(), paths=endpoints.split(),
                                 test=f'T-{n:02}', status='PENDIENTE_IMPLEMENTACION_Y_PRUEBA'))
    quality = [dict(id=rid, category=cat, statement=statement, test=f'T-{int(rid[-2:])+18:02}', status='META_NO_MEDIDA')
               for rid, cat, statement in re.findall(r'^\| (RNF-\d{2}) \| (.*?) \| (.*?) \|$', source, re.M)]
    rules = [dict(id=rid, statement=text) for rid, text in re.findall(r'^\| (RN-\d{2}) \| (.*?) \|$', source, re.M)]
    assert len(requirements) == 18 and len(quality) == 12 and len(rules) == 14
    (ANNEX / 'catalogo_requisitos.json').write_text(json.dumps(dict(version='1.0', requirements=requirements, quality=quality, rules=rules), ensure_ascii=False, indent=2) + '\n')
    lines = ['# Matriz de trazabilidad', '', 'Estado: diseño; todas las pruebas de producto están pendientes de ejecución. Generada desde la especificación; los artefactos son diseños, no capacidades implementadas.', '',
             '## Objetivos del perfil', '', '| Objetivo | Requisitos principales | Evidencia complementaria |', '|---|---|---|',
             '| OE-01 | RF-03, RF-04, RF-14 | Diagnóstico, entrevistas y reglas revisadas con el personal. |',
             '| OE-02 | RF-05, RF-16, RNF-06, RNF-11 | Arquitectura, diccionario, organización del punto y wireframes. |',
             '| OE-03 | RF-01, RF-02, RF-07, RF-08 | Pruebas de identidad, permisos, vigencia y uso único. |',
             '| OE-04 | RF-03, RF-04, RF-05, RF-09, RF-10, RF-12 | Ciclo integrado y conciliación material. |',
             '| OE-05 | RF-06, RF-11, RF-15 | Avisos, eventos y consulta limitada. |',
             '| OE-06 | RF-17, RF-18 y RNF-01 a RNF-12 | Piloto, resultados, recuperación y evaluación económica. |', '',
             '## Requisitos funcionales', '', '| Requisito | Caso | Datos | Pantalla | API | Prueba |', '|---|---|---|---|---|---|']
    for r in requirements:
        lines.append(f"| {r['id']} | {r['use_case']} | {', '.join(r['tables'])} | {', '.join(r['screens'])} | {'; '.join(r['paths'])} | {r['test']} |")
    lines += ['', '## Calidad', '', '| Requisito | Categoría | Prueba | Estado |', '|---|---|---|---|']
    for r in quality:
        lines.append(f"| {r['id']} | {r['category']} | {r['test']} | Meta pendiente de medir. |")
    lines += ['', '## Control de cambios', '', 'Una modificación de una regla exige revisar requisito, caso, modelo, contrato, interfaz y prueba relacionados. Las reglas RN-01 a RN-14 se aplican transversalmente según la especificación y el manual. La prohibición de hardware corresponde a D-01, D-02 y RNF-11.', '',
              'Documentos: [especificación](../ingenieria/BuzonExpress_Especificacion_Software.md), [casos](../ingenieria/06_casos_de_uso_alto_nivel_y_expandidos.md), [datos](../ingenieria/03_modelado_datos_arquitectura.md), [API](../ingenieria/07_contratos_api_y_seguridad.md), [UI](../ingenieria/02_modelado_diseno_ui.md) y [pruebas](../validacion/01_plan_validacion.md).', '']
    (ROOT / 'docs/gestion/03_matriz_trazabilidad.md').write_text('\n'.join(lines))


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
    assert len(re.findall(r'^### Tabla', '\n'.join(parts), re.M)) == 17
    p = ENG / '03_modelado_datos_arquitectura.md'
    text = p.read_text()
    marker = '<!-- DICCIONARIO_GENERADO -->'
    p.write_text(text.split(marker)[0] + marker + '\n\n' + '\n'.join(parts))


def api():
    schemas = {}
    def ref(name): return {'$ref': f'#/components/schemas/{name}'}
    def obj(name, props, required=()):
        schemas[name] = dict(type='object', additionalProperties=False, properties=props, required=list(required))
    uid = {'type': 'string', 'format': 'uuid'}
    st = {'type': 'string'}
    dt = {'type': 'string', 'format': 'date-time'}
    integer = {'type': 'integer', 'minimum': 1}
    money = {'type': 'string', 'pattern': r'^\d+\.\d{2}$', 'description': 'BOB decimal, no float binario.'}
    size = {'type': 'string', 'enum': ['PEQUENO', 'MEDIANO', 'GRANDE']}
    version = {'type': 'integer', 'minimum': 1}
    payment = {'type': 'string', 'enum': ['EFECTIVO', 'REFERENCIA_MANUAL']}
    obj('Error', {'code': st, 'message': st, 'correlation_id': uid}, ('code', 'message', 'correlation_id'))
    obj('User', {'id': uid, 'full_name': st, 'role': {'type': 'string', 'enum': ['USUARIO','OPERADOR','ADMIN','AUDITOR']}, 'contact_verified': {'type': 'boolean'}}, ('id','full_name','role','contact_verified'))
    obj('Register', {'email': {'type':'string','format':'email'}, 'password': {'type':'string','writeOnly':True}, 'full_name': st, 'phone': st}, ('email','password','full_name'))
    obj('Login', {'email': {'type':'string','format':'email'}, 'password': {'type':'string','writeOnly':True}}, ('email','password'))
    obj('Session', {'user': ref('User'), 'expires_at': dt}, ('user','expires_at'))
    obj('Csrf', {'csrf_token': st}, ('csrf_token',))
    obj('TokenAction', {'token':{'type':'string','writeOnly':True}}, ('token',))
    obj('ResetRequest', {'email':{'type':'string','format':'email'}}, ('email',))
    obj('ResetComplete', {'token':{'type':'string','writeOnly':True},'password':{'type':'string','writeOnly':True}}, ('token','password'))
    obj('Reason', {'reason':st}, ('reason',))
    obj('VersionReason', {'reason':st,'expected_version':version}, ('reason','expected_version'))
    obj('Point', {'id': uid,'name': st,'address': st,'opening_hours': {'type':'object','additionalProperties':True},'is_active': {'type':'boolean'}}, ('id','name','address','opening_hours','is_active'))
    obj('CustodyCreate', {'recipient_contact': st,'point_id': uid,'description': {'type':'string','maxLength':255},'size_category':size}, ('recipient_contact','point_id','description','size_category'))
    states=['REGISTRADA','EN_CUSTODIA','RETIRO_EN_CURSO','RETIRADA','DEVOLUCION_EN_CURSO','DEVUELTA','CANCELADA']
    obj('Custody', {'id':uid,'tracking_number':st,'state':{'type':'string','enum':states},'point_id':uid,'description':st,'size_category':size,'version':version,'service_total':money,'due_at':{'type':['string','null'],'format':'date-time'},'received_at':{'type':['string','null'],'format':'date-time'}}, ('id','tracking_number','state','point_id','description','size_category','version','service_total'))
    obj('CustodyRegistered', {**schemas['Custody']['properties'],'public_reference':st}, schemas['Custody']['required'])
    obj('PublicReference', {'public_reference':st}, ('public_reference',))
    obj('PublicTracking', {'state': {'type':'string','enum':['PENDIENTE','RECIBIDA','FINALIZADA']},'point_name':st,'opening_hours':{'type':'object','additionalProperties':True}}, ('state','point_name','opening_hours'))
    obj('Quote', {'tariff_id':uid,'amount':money,'currency':{'const':'BOB'},'duration_hours':integer}, ('tariff_id','amount','currency','duration_hours'))
    obj('Receive', {'location_id':uid,'expected_version':version,'duration_hours':integer,'tariff_id':uid,'accepted_amount':money,'payment_method':payment,'payment_reference':st,'external_condition':st}, ('location_id','expected_version','duration_hours','tariff_id','accepted_amount','payment_method','external_condition'))
    obj('CredentialIssue', {'reissue':{'type':'boolean','default':False}}, ())
    obj('Credential', {'credential_id':uid,'code':{'type':'string','pattern':'^[0-9]{6}$','readOnly':True},'expires_at':dt}, ('credential_id','code','expires_at'))
    obj('Verify', {'code':{'type':'string','pattern':'^[0-9]{6}$','writeOnly':True},'expected_version':version,'recipient_check':{'const':'COMPROBACION_VISUAL_COMPLETADA'}}, ('code','expected_version','recipient_check'))
    obj('Authorization', {'authorization_id':uid,'custody_id':uid,'expires_at':dt,'state':{'const':'VALIDADA'},'location_code':st,'description':st,'version':version}, ('authorization_id','custody_id','expires_at','state','location_code','description','version'))
    obj('HandoverConfirm', {'authorization_id':uid,'expected_version':version,'physically_delivered':{'const':True}}, ('authorization_id','expected_version','physically_delivered'))
    obj('Handover', {'id':uid,'custody_id':uid,'kind':{'type':'string','enum':['RETIRO','DEVOLUCION']},'confirmed_at':dt,'operator_id':uid}, ('id','custody_id','kind','confirmed_at','operator_id'))
    obj('Abort', {'authorization_id':uid,'physically_delivered':{'const':False},'reason':st}, ('authorization_id','physically_delivered','reason'))
    obj('Extension', {'additional_hours':integer,'accepted_amount':money,'expected_version':version,'payment_method':payment,'payment_reference':st}, ('additional_hours','accepted_amount','expected_version','payment_method'))
    obj('IncidentCreate', {'kind':st,'description':st,'is_blocking':{'type':'boolean','default':True}}, ('kind','description'))
    obj('Incident', {'id':uid,'custody_id':uid,'state':{'type':'string','enum':['ABIERTA','EN_REVISION','RESUELTA']},'is_blocking':{'type':'boolean'}}, ('id','custody_id','state','is_blocking'))
    purposes=['REEMITIR_CREDENCIAL','CAMBIAR_DESTINATARIO','AUTORIZAR_DEVOLUCION','RECONCILIAR_ENTREGA']
    obj('RecoveryCreate', {'custody_id':uid,'purpose':{'type':'string','enum':purposes},'evidence':st,'target_recipient_id':uid}, ('custody_id','purpose','evidence'))
    obj('Recovery', {'id':uid,'custody_id':uid,'state':{'type':'string','enum':['PENDIENTE','APROBADA','RECHAZADA','EJECUTADA']}}, ('id','custody_id','state'))
    obj('Decision', {'decision':{'type':'string','enum':['APROBAR','RECHAZAR']},'note':st}, ('decision','note'))
    obj('ReturnAuthorization', {'recovery_request_id':uid,'expected_version':version,'sender_check':{'const':'COMPROBACION_VISUAL_COMPLETADA'}}, ('recovery_request_id','expected_version','sender_check'))
    obj('Resource', {'id':uid,'state':st}, ('id',))
    obj('Notification', {'id':uid,'subject':st,'body':st,'created_at':dt,'read_at':{'type':['string','null'],'format':'date-time'}}, ('id','subject','body','created_at'))
    obj('Location', {'id':uid,'point_id':uid,'code':st,'state':{'type':'string','enum':['DISPONIBLE','OCUPADA','BLOQUEADA','FUERA_SERVICIO']},'size_category':size,'version':version}, ('id','point_id','code','state','size_category','version'))
    obj('PointWrite', {'name':st,'address':st,'opening_hours':{'type':'object','additionalProperties':True},'is_active':{'type':'boolean'}}, ('name','address','opening_hours','is_active'))
    obj('LocationWrite', {'point_id':uid,'code':st,'size_category':size}, ('point_id','code','size_category'))
    obj('LocationState', {'state':{'type':'string','enum':['DISPONIBLE','BLOQUEADA','FUERA_SERVICIO']},'expected_version':version,'reason':st}, ('state','expected_version','reason'))
    obj('StaffWrite', {'point_id':uid,'user_id':uid,'role':{'type':'string','enum':['OPERADOR','ADMIN','AUDITOR']},'is_active':{'type':'boolean'}}, ('point_id','user_id','role','is_active'))
    obj('TariffWrite', {'point_id':uid,'valid_from':dt,'rules':{'type':'object','description':'Validar moneda, tamaños, horas y precios en servidor.','additionalProperties':True}}, ('point_id','valid_from','rules'))
    obj('Event', {'id':uid,'event_type':st,'created_at':dt,'correlation_id':uid,'actor_id':{'type':['string','null'],'format':'uuid'},'custody_id':{'type':['string','null'],'format':'uuid'}}, ('id','event_type','created_at','correlation_id'))
    obj('Report', {'point_id':uid,'from':dt,'to':dt,'available_locations':{'type':'integer','minimum':0},'occupied_locations':{'type':'integer','minimum':0},'completed_custodies':{'type':'integer','minimum':0},'data_quality_note':st}, ('point_id','from','to','available_locations','occupied_locations','completed_custodies','data_quality_note'))
    obj('Health', {'status':{'type':'string','enum':['OK','DEGRADADO']},'database_checked':{'type':'boolean'}}, ('status','database_checked'))
    paths = {}
    def add(path, method, title, response, *, request=None, public=False, idem=False, code='200', query=()):
        op={'summary':title,'operationId':method+'_'+re.sub(r'[^a-zA-Z0-9]+','_',path).strip('_'), 'responses':{code:{'description':'Resultado del contrato propuesto.','content':{'application/json':{'schema':response}}}}}
        if public: op['security']=[]
        params=[]
        for name in re.findall(r'\{(\w+)\}',path):
            params.append({'name':name,'in':'path','required':True,'schema':st if name=='reference' else uid})
        for name, schema, required in query:
            params.append({'name':name,'in':'query','required':required,'schema':schema})
        if method in ['post','put','patch','delete']:
            params.append({'$ref':'#/components/parameters/CsrfToken'})
        if idem: params.append({'$ref':'#/components/parameters/IdempotencyKey'})
        if params: op['parameters']=params
        if request: op['requestBody']={'required':True,'content':{'application/json':{'schema':ref(request)}}}
        for err in ['400','401','403','404','409','422','429','503']:
            op['responses'][err]={'description':'Error tipado; no contiene secretos.','content':{'application/json':{'schema':ref('Error')}}}
        paths.setdefault(path,{})[method]=op
    arr=lambda n: {'type':'array','items':ref(n)}
    add('/auth/csrf','get','Obtener token antifalsificación ligado al contexto del navegador.',ref('Csrf'),public=True)
    add('/auth/register','post','Crear cuenta general; no permite elegir rol privilegiado.',ref('User'),request='Register',public=True,code='201')
    add('/auth/login','post','Abrir sesión protegida mediante cookie.',ref('Session'),request='Login',public=True)
    add('/auth/logout','post','Revocar sesión actual.',ref('Resource'))
    add('/auth/me','get','Consultar identidad y permisos propios.',ref('User'))
    add('/auth/verify-contact','post','Consumir enlace de correo y comprobar contacto.',ref('Resource'),request='TokenAction',public=True)
    add('/auth/password-reset/request','post','Solicitar recuperación sin revelar existencia de cuenta.',ref('Resource'),request='ResetRequest',public=True)
    add('/auth/password-reset/complete','post','Consumir enlace y revocar sesiones anteriores.',ref('Resource'),request='ResetComplete',public=True)
    add('/admin/users/{user_id}/verify-contact','post','Registrar comprobación presencial con evidencia mínima.',ref('User'),request='Reason',idem=True)
    add('/points','get','Listar puntos activos y horarios publicados.',arr('Point'),public=True)
    add('/points/{point_id}/quote','get','Cotizar plazo y tamaño sin reservar espacio.',ref('Quote'),public=True,query=[('size_category',size,True),('duration_hours',integer,True)])
    add('/custodies','post','Registrar custodia sin reservar capacidad; referencia pública se muestra al crear.',ref('CustodyRegistered'),request='CustodyCreate',idem=True,code='201')
    add('/custodies','get','Listar custodias donde participa la cuenta.',arr('Custody'))
    add('/custodies/{custody_id}','get','Consultar detalle privado autorizado.',ref('Custody'))
    add('/custodies/{custody_id}/public-reference','post','Rotar referencia pública con autorización del participante.',ref('PublicReference'))
    add('/custodies/{custody_id}/cancel','post','Cancelar exclusivamente antes de recibir.',ref('Custody'),request='VersionReason',idem=True)
    add('/public-tracking/{reference}','get','Estado mínimo por referencia opaca; sin datos personales.',ref('PublicTracking'),public=True)
    add('/custodies/{custody_id}/receive','post','Recepción, ubicación y cobro transaccionales.',ref('Custody'),request='Receive',idem=True)
    add('/custodies/{custody_id}/credentials','post','Mostrar un código una sola vez al destinatario autenticado.',ref('Credential'),request='CredentialIssue',code='201')
    add('/custodies/{custody_id}/verify','post','Retener credencial y preparar entrega, sin confirmarla.',ref('Authorization'),request='Verify',idem=True)
    add('/custodies/{custody_id}/handover','post','Confirmar entrega física ya realizada.',ref('Handover'),request='HandoverConfirm',idem=True)
    add('/custodies/{custody_id}/abort-handover','post','Anular preparación solo si no hubo entrega física.',ref('Custody'),request='Abort',idem=True)
    add('/custodies/{custody_id}/extend','post','Registrar prórroga y cobro según contrato histórico.',ref('Custody'),request='Extension',idem=True)
    add('/custodies/{custody_id}/incidents','post','Abrir incidencia con control de alcance.',ref('Incident'),request='IncidentCreate',idem=True,code='201')
    add('/incidents/{incident_id}/resolve','post','Resolver con fundamento y comprobación de inventario.',ref('Incident'),request='Reason',idem=True)
    add('/recovery-requests','post','Solicitar excepción con evidencia.',ref('Recovery'),request='RecoveryCreate',idem=True,code='201')
    add('/recovery-requests/{request_id}/decision','post','Revisar con otra persona; ejecutar conciliación según propósito.',ref('Recovery'),request='Decision',idem=True)
    add('/custodies/{custody_id}/return-authorization','post','Preparar devolución aprobada al emisor.',ref('Authorization'),request='ReturnAuthorization',idem=True)
    add('/custodies/{custody_id}/return-handover','post','Confirmar devolución física ya realizada.',ref('Handover'),request='HandoverConfirm',idem=True)
    add('/notifications','get','Consultar bandeja propia.',arr('Notification'))
    add('/notifications/{notification_id}/read','post','Marcar aviso propio como leído.',ref('Resource'))
    add('/inventory','get','Inventario de un punto asignado al personal.',arr('Location'),query=[('point_id',uid,True)])
    add('/admin/points','post','Crear un punto atendido.',ref('Point'),request='PointWrite',idem=True,code='201')
    add('/admin/points/{point_id}','put','Actualizar horario y habilitación sin perder inventario.',ref('Point'),request='PointWrite',idem=True)
    add('/admin/locations','post','Registrar ubicación del espacio existente.',ref('Location'),request='LocationWrite',idem=True,code='201')
    add('/admin/locations/{location_id}','patch','Bloquear o retirar de servicio sin liberar un objeto ocupado.',ref('Location'),request='LocationState',idem=True)
    add('/admin/staff-assignments','post','Asignar o deshabilitar personal con auditoría.',ref('Resource'),request='StaffWrite',idem=True)
    add('/admin/tariffs','post','Publicar nueva versión tarifaria.',ref('Resource'),request='TariffWrite',idem=True,code='201')
    add('/audit/events','get','Consultar eventos dentro del alcance autorizado.',arr('Event'),query=[('point_id',uid,True)])
    add('/reports','get','Indicadores con periodo y calidad de datos.',ref('Report'),query=[('point_id',uid,True),('from',dt,True),('to',dt,True)])
    add('/health','get','Comprobar dependencias realmente consultadas.',ref('Health'),public=True)
    spec={'openapi':'3.1.0','info':{'title':'BUZON Xpress — contrato propuesto','version':'1.0.0','description':'Diseño documental sin servidor implementado. Entrega humana, sin hardware externo. Los permisos de negocio se detallan en la especificación.'},'servers':[{'url':'/api/v1','description':'Ruta relativa de la futura aplicación.'}], 'security':[{'sessionCookie':[]}], 'paths':paths,'components':{'securitySchemes':{'sessionCookie':{'type':'apiKey','in':'cookie','name':'buzon_session'}},'parameters':{'CsrfToken':{'name':'X-CSRF-Token','in':'header','required':True,'schema':st},'IdempotencyKey':{'name':'Idempotency-Key','in':'header','required':True,'schema':{'type':'string','minLength':16,'maxLength':120}}},'schemas':schemas}}
    (ANNEX/'openapi.yaml').write_text(yaml.safe_dump(spec,allow_unicode=True,sort_keys=False))


if __name__ == '__main__':
    catalogs()
    dictionary()
    api()
    print('Catálogos, trazabilidad, diccionario y OpenAPI generados.')
