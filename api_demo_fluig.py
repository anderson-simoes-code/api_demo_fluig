#!/usr/bin/env python3
"""API de demonstracao Fluig: colaboradores e fornecedores. Dados ficticios."""
import argparse
import base64
import binascii
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

DATA_FILE = Path(__file__).with_name("colaboradores.json")
SUPPLIERS_FILE = Path(__file__).with_name("fornecedores.json")
USER = os.environ.get("DEMO_API_USER", "fluig")
PASSWORD = os.environ.get("DEMO_API_PASSWORD", "123456")


def authenticated(header):
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "basic":
        return False
    try:
        supplied = base64.b64decode(token, validate=True)
    except (binascii.Error, ValueError):
        return False
    expected = (USER + ":" + PASSWORD).encode("utf-8")
    return hmac.compare_digest(supplied, expected)


def swagger(host, scheme="http"):
    error_response = {"description": "Nao autorizado", "schema": {"$ref": "#/definitions/Erro"}}
    return {
        "swagger": "2.0", "info": {"title": "API Fluig Demo - Fornecedores", "version": "1.1.0"},
        "host": host, "basePath": "/", "schemes": [scheme],
        "produces": ["application/json"],
        "securityDefinitions": {"BasicAuth": {"type": "basic"}},
        "security": [{"BasicAuth": []}],
        "paths": {
            "/basic-auth": {"get": {
                "operationId": "validarAutenticacao", "summary": "Validar autenticacao",
                "responses": {"200": {"description": "Autenticado", "schema": {
                    "type": "object", "properties": {
                        "authenticated": {"type": "boolean"}, "user": {"type": "string"}
                    }}}, "401": error_response}
            }},
            "/fornecedores": {"get": {
                "operationId": "listarFornecedores", "summary": "Consultar fornecedores ficticios",
                "description": "Sem filtro, retorna todos. homologado=true retorna somente homologados.",
                "parameters": [{
                    "name": "homologado", "in": "query", "required": False,
                    "type": "string", "default": "",
                    "description": "Informe true ou false. Vazio ou omitido retorna todos os fornecedores."
                }],
                "responses": {
                    "200": {"description": "Lista de fornecedores", "schema": {
                        "type": "array", "items": {"$ref": "#/definitions/Fornecedor"}}},
                    "400": {"description": "Filtro invalido", "schema": {"$ref": "#/definitions/Erro"}},
                    "401": error_response
                }
            }},
            "/colaboradores": {"get": {
                "operationId": "listarColaboradores", "summary": "Listar colaboradores ficticios",
                "parameters": [
                    {"name": "departamento", "in": "query", "required": False, "type": "string"},
                    {"name": "ativo", "in": "query", "required": False, "type": "boolean"}
                ],
                "responses": {
                    "200": {"description": "Lista de colaboradores", "schema": {
                        "type": "array", "items": {"$ref": "#/definitions/Colaborador"}}},
                    "400": {"description": "Filtro invalido", "schema": {"$ref": "#/definitions/Erro"}},
                    "401": error_response
                }
            }}
        },
        "definitions": {
            "Fornecedor": {
                "type": "object",
                "required": ["codigo", "razaoSocial", "categoria", "cidade", "uf", "email", "homologado"],
                "properties": {
                    "codigo": {"type": "string"}, "razaoSocial": {"type": "string"},
                    "categoria": {"type": "string"}, "cidade": {"type": "string"},
                    "uf": {"type": "string"}, "email": {"type": "string"},
                    "homologado": {"type": "boolean", "description": "true: homologado; false: nao homologado"}
                }
            },
            "Colaborador": {
                "type": "object", "required": ["matricula", "nome", "departamento", "cargo", "email", "ativo"],
                "properties": {
                    "matricula": {"type": "string"}, "nome": {"type": "string"},
                    "departamento": {"type": "string"}, "cargo": {"type": "string"},
                    "email": {"type": "string"}, "ativo": {"type": "boolean"}
                }
            },
            "Erro": {"type": "object", "properties": {"erro": {"type": "string"}}}
        }
    }


def route(target, authorization="", host="localhost:8765", scheme="http"):
    url = urlsplit(target)
    if url.path == "/swagger.json":
        return 200, swagger(host, scheme)
    if url.path == "/health":
        return 200, {"status": "ok"}
    if url.path == "/":
        return 200, {
            "servico": "API Fluig Demo - Fornecedores", "swagger": "/swagger.json",
            "dados": "/colaboradores", "fornecedores": "/fornecedores"
        }
    if url.path not in ("/basic-auth", "/colaboradores", "/fornecedores"):
        return 404, {"erro": "Rota nao encontrada"}
    if not authenticated(authorization):
        return 401, {"erro": "Usuario ou senha invalidos"}
    if url.path == "/basic-auth":
        return 200, {"authenticated": True, "user": USER}
    filters = parse_qs(url.query, keep_blank_values=True)
    if url.path == "/fornecedores":
        homologated = filters.get("homologado", [""])[0].strip().lower()
        if homologated not in ("", "true", "false"):
            return 400, {"erro": "O filtro homologado deve ser true ou false"}
        rows = load_suppliers()
        if homologated != "":
            rows = [row for row in rows if row["homologado"] is (homologated == "true")]
        return 200, rows
    active = filters.get("ativo", [""])[0].strip().lower()
    if active not in ("", "true", "false"):
        return 400, {"erro": "O filtro ativo deve ser true ou false"}
    department = filters.get("departamento", [""])[0].strip().casefold()
    rows = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if department:
        rows = [row for row in rows if row["departamento"].casefold() == department]
    if active:
        rows = [row for row in rows if row["ativo"] == (active == "true")]
    return 200, rows


def load_suppliers():
    rows = json.loads(SUPPLIERS_FILE.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("fornecedores.json deve conter uma lista")
    seen = set()
    required = ("codigo", "razaoSocial", "categoria", "cidade", "uf", "email")
    for row in rows:
        if not isinstance(row, dict) or any(not isinstance(row.get(field), str) or not row[field].strip() for field in required):
            raise ValueError("Fornecedor com campo obrigatorio invalido")
        if type(row.get("homologado")) is not bool:
            raise ValueError("homologado deve ser true ou false, sem aspas")
        if row["codigo"] in seen:
            raise ValueError("Codigo de fornecedor duplicado")
        seen.add(row["codigo"])
    return rows


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # O Render termina o HTTPS e informa o protocolo original neste header.
            scheme = self.headers.get("X-Forwarded-Proto", "http").split(",")[0].strip().lower()
            if scheme not in ("http", "https"):
                scheme = "http"
            status, payload = route(self.path, self.headers.get("Authorization", ""), self.headers.get("Host", "localhost:8765"), scheme)
        except (OSError, ValueError, KeyError):
            status, payload = 500, {"erro": "Nao foi possivel ler os dados; verifique os arquivos JSON no servidor"}
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if status == 401:
            self.send_header("WWW-Authenticate", 'Basic realm="Fluig Demo"')
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0" if os.environ.get("RENDER") else "127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()
    # Valida os dados antes de iniciar o servidor.
    json.loads(DATA_FILE.read_text(encoding="utf-8"))
    load_suppliers()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print("API de demonstracao iniciada. Interrompa com Ctrl+C.")
    print("Swagger: http://localhost:%s/swagger.json" % args.port)
    print("Colaboradores: http://localhost:%s/colaboradores" % args.port)
    print("Fornecedores: http://localhost:%s/fornecedores" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

