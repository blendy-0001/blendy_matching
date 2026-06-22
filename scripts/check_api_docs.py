import requests
import json

resp = requests.get('http://localhost:8000/openapi.json')
schema = resp.json()

print('=== OpenAPI Documentation Summary ===\n')
print('Servers:')
for server in schema.get('servers', []):
    url = server.get('url', 'N/A')
    desc = server.get('description', 'N/A')
    print(f'  - {url}: {desc}')

print(f'\nTotal Endpoints: {len(schema.get("paths", {}))}')
print('\nEndpoints:')
for path in sorted(schema.get('paths', {}).keys()):
    methods = list(schema['paths'][path].keys())
    print(f'  {path}: {", ".join(methods)}')

print(f'\nOpenAPI Version: {schema.get("openapi", "N/A")}')
print(f'API Title: {schema.get("info", {}).get("title", "N/A")}')
print(f'Contact Name: {schema.get("info", {}).get("contact", {}).get("name", "N/A")}')
print(f'Contact Email: {schema.get("info", {}).get("contact", {}).get("email", "N/A")}')
print(f'License: {schema.get("info", {}).get("license", {}).get("name", "N/A")}')
print(f'\nSecurity Schemes: {list(schema.get("components", {}).get("securitySchemes", {}).keys())}')

print('\n=== Protected vs Unprotected Endpoints ===')
protected = []
unprotected = []
for path in schema.get('paths', {}):
    for method in schema['paths'][path]:
        has_security = 'security' in schema['paths'][path][method]
        if has_security:
            protected.append(f'{path} ({method.upper()})')
        else:
            unprotected.append(f'{path} ({method.upper()})')

print(f'\nProtected Endpoints ({len(protected)}):')
for ep in protected:
    print(f'  - {ep}')

print(f'\nUnprotected Endpoints ({len(unprotected)}):')
for ep in unprotected:
    print(f'  - {ep}')
