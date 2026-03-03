import unittest
from datetime import datetime

import app


class TestMinutosNoTurno(unittest.TestCase):
    def test_primeiro_turno_conta_somente_janela(self):
        dia_inicio = datetime(2026, 2, 25, 0, 0)
        inicio = datetime(2026, 2, 25, 4, 0)
        fim = datetime(2026, 2, 25, 6, 0)

        minutos = app.minutos_no_turno(inicio, fim, dia_inicio, "1º TURNO", "")

        self.assertEqual(minutos, 60)

    def test_terceiro_turno_conta_duas_janelas(self):
        dia_inicio = datetime(2026, 2, 25, 0, 0)
        inicio = datetime(2026, 2, 25, 21, 30)
        fim = datetime(2026, 2, 25, 22, 30)

        minutos = app.minutos_no_turno(inicio, fim, dia_inicio, "3º TURNO", "")

        self.assertEqual(minutos, 30)

    def test_turno_desconhecido_cai_para_correspondencia_por_nome(self):
        dia_inicio = datetime(2026, 2, 25, 0, 0)
        inicio = datetime(2026, 2, 25, 10, 0)
        fim = datetime(2026, 2, 25, 11, 0)

        minutos_ok = app.minutos_no_turno(inicio, fim, dia_inicio, "TURNO TESTE", "turno teste")
        minutos_zero = app.minutos_no_turno(inicio, fim, dia_inicio, "TURNO TESTE", "outro")

        self.assertEqual(minutos_ok, 60)
        self.assertEqual(minutos_zero, 0)


if __name__ == "__main__":
    unittest.main()
