import base64
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("api", ROOT / "api_demo_fluig.py")
api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api)


class MemoryConnection:
    def __init__(self, request):
        self.request = request
        self.output = bytearray()

    def makefile(self, *args, **kwargs):
        return io.BytesIO(self.request)

    def sendall(self, content):
        self.output.extend(content)


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.previous = (api.USER, api.PASSWORD)
        api.USER, api.PASSWORD = "fluig", "123456"
        self.auth = "Basic " + base64.b64encode(b"fluig:123456").decode("ascii")

    def tearDown(self):
        api.USER, api.PASSWORD = self.previous

    def test_all_and_both_boolean_filters(self):
        status, all_rows = api.route("/fornecedores", self.auth)
        self.assertEqual(status, 200)
        self.assertEqual(len(all_rows), 15)
        yes = api.route("/fornecedores?homologado=true", self.auth)[1]
        no = api.route("/fornecedores?homologado=false", self.auth)[1]
        self.assertEqual(len(yes), 10)
        self.assertEqual(len(no), 5)
        self.assertTrue(all(row["homologado"] is True for row in yes))
        self.assertTrue(all(row["homologado"] is False for row in no))
        self.assertEqual({r["codigo"] for r in all_rows}, {r["codigo"] for r in yes + no})
        self.assertTrue(all(type(r["homologado"]) is bool for r in all_rows))

    def test_blank_filter_and_normalization(self):
        self.assertEqual(len(api.route("/fornecedores?homologado=", self.auth)[1]), 15)
        self.assertEqual(len(api.route("/fornecedores?homologado=%20TRUE%20", self.auth)[1]), 10)

    def test_invalid_filter(self):
        for value in ["talvez", "1", "null"]:
            self.assertEqual(api.route("/fornecedores?homologado=" + value, self.auth)[0], 400)

    def test_authentication(self):
        bad = "Basic " + base64.b64encode(b"fluig:incorreta").decode("ascii")
        for header in ["", "Bearer teste", "Basic !!!", bad]:
            self.assertEqual(api.route("/fornecedores", header)[0], 401)
        self.assertEqual(api.route("/basic-auth", self.auth), (200, {"authenticated": True, "user": "fluig"}))

    def test_existing_colleagues(self):
        self.assertEqual(len(api.route("/colaboradores", self.auth)[1]), 15)
        self.assertEqual(len(api.route("/colaboradores?departamento=TI", self.auth)[1]), 3)
        self.assertEqual(len(api.route("/colaboradores?ativo=false", self.auth)[1]), 3)

    def test_public_and_missing_routes(self):
        self.assertEqual(api.route("/health")[0], 200)
        self.assertEqual(api.route("/swagger.json")[0], 200)
        self.assertEqual(api.route("/")[1]["fornecedores"], "/fornecedores")
        self.assertEqual(api.route("/inexistente")[0], 404)

    def test_swagger_matches_payload_and_query(self):
        spec = api.swagger("api-fluig-demo.onrender.com", "https")
        self.assertEqual(spec["swagger"], "2.0")
        self.assertEqual(spec["schemes"], ["https"])
        self.assertEqual(spec["security"], [{"BasicAuth": []}])
        operation = spec["paths"]["/fornecedores"]["get"]
        self.assertEqual(operation["operationId"], "listarFornecedores")
        self.assertEqual(operation["parameters"][0]["default"], "")
        self.assertFalse(operation["parameters"][0]["required"])
        self.assertEqual(spec["definitions"]["Fornecedor"]["properties"]["homologado"]["type"], "boolean")
        row = api.load_suppliers()[0]
        self.assertEqual(set(row), set(spec["definitions"]["Fornecedor"]["required"]))

    def test_file_updates_and_validation(self):
        original = api.SUPPLIERS_FILE
        rows = api.load_suppliers()
        try:
            with tempfile.TemporaryDirectory() as directory:
                api.SUPPLIERS_FILE = pathlib.Path(directory) / "fornecedores.json"
                api.SUPPLIERS_FILE.write_text(json.dumps(rows + [dict(rows[0], codigo="F016")]), encoding="utf-8")
                self.assertEqual(len(api.route("/fornecedores", self.auth)[1]), 16)
                rows[0]["homologado"] = "false"
                api.SUPPLIERS_FILE.write_text(json.dumps(rows), encoding="utf-8")
                with self.assertRaises(ValueError):
                    api.load_suppliers()
        finally:
            api.SUPPLIERS_FILE = original

    def test_http_wire_response_and_render_scheme(self):
        previous_log = api.Handler.log_message
        api.Handler.log_message = lambda *args: None
        try:
            cases = [("/fornecedores", "", 401), ("/fornecedores?homologado=true", self.auth, 200), ("/swagger.json", "", 200)]
            for path, auth, expected in cases:
                request = "GET " + path + " HTTP/1.1\r\nHost: api-fluig-demo.onrender.com\r\nX-Forwarded-Proto: https\r\nConnection: close\r\n"
                if auth:
                    request += "Authorization: " + auth + "\r\n"
                connection = MemoryConnection((request + "\r\n").encode("ascii"))
                api.Handler(connection, ("127.0.0.1", 1), None)
                headers, body = bytes(connection.output).split(b"\r\n\r\n", 1)
                self.assertIn((" " + str(expected) + " ").encode(), headers)
                self.assertIn(b"application/json; charset=utf-8", headers)
                payload = json.loads(body)
                if expected == 401:
                    self.assertIn(b"WWW-Authenticate: Basic", headers)
                elif path == "/swagger.json":
                    self.assertEqual(payload["schemes"], ["https"])
                    self.assertEqual(payload["host"], "api-fluig-demo.onrender.com")
                else:
                    self.assertEqual(len(payload), 10)
        finally:
            api.Handler.log_message = previous_log


if __name__ == "__main__":
    unittest.main()
