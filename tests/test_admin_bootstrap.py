import importlib
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path


class TestAdminBootstrap(unittest.TestCase):
    def test_db_zero_cria_admin_e_permite_acesso_motivos(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "Paradas.db"
            os.environ["PARADAS_DB_PATH"] = str(db_path)

            app_module = importlib.import_module("app")

            app_module.init_db()

            with sqlite3.connect(db_path) as conn:
                row = conn.execute(
                    "SELECT login, email, nivel FROM usuarios WHERE login = ?",
                    ("admin",),
                ).fetchone()

            self.assertIsNotNone(row, "Usuário admin deveria ser criado automaticamente")
            self.assertEqual(row[0], "admin")
            self.assertEqual(row[1], "ti1@malhariaindaial.com.br")
            self.assertEqual(row[2], 6)

            client = app_module.app.test_client()
            response_login = client.post(
                "/login",
                data={"login": "admin", "senha": "123456"},
                follow_redirects=True,
            )
            self.assertEqual(response_login.status_code, 200)
            self.assertIn("Login realizado.".encode("utf-8"), response_login.data)
            self.assertIn(b"Usuario: <strong>admin</strong>", response_login.data)

            response_motivo_form = client.get("/motivos/novo", follow_redirects=True)
            self.assertEqual(response_motivo_form.status_code, 200)
            self.assertIn("Novo motivo".encode("utf-8"), response_motivo_form.data)


if __name__ == "__main__":
    unittest.main()
