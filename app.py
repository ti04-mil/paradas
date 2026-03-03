from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from datetime import datetime, timedelta
import os
import sqlite3
import threading
import time
import unicodedata
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_NETWORK_DB_PATH = Path(r"\\server\TI\Temp\Paradas\Sistema\Paradas.db")
_db_env = os.getenv("PARADAS_DB_PATH", "").strip()
if _db_env:
    DB_PATH = Path(_db_env)
elif DEFAULT_NETWORK_DB_PATH.exists():
    DB_PATH = DEFAULT_NETWORK_DB_PATH
else:
    DB_PATH = BASE_DIR / "Paradas.db"

app = Flask(__name__, static_folder="Imagens", static_url_path="/Imagens")
app.config["SECRET_KEY"] = "paradas-secret-key-change-me"

AUTO_SYNC_LOCK = threading.Lock()
AUTO_SYNC_LAST_EXEC = set()

DEFAULT_SETORES = [
    (1, "TI", 6),
    (2, "PROCESSOS", 5),
    (3, "GESTOR", 4),
    (4, "LIDER 1o TURNO", 1),
    (5, "LIDER 2o TURNO", 2),
    (6, "LIDER 3o TURNO", 3),
]

DEFAULT_TIPOS_TURNO = [
    (1, "1\u00ba TURNO"),
    (2, "2\u00ba TURNO"),
    (3, "3\u00ba TURNO"),
    (4, "TODOS"),
]

DIAS_SEMANA = [
    "Segunda-feira",
    "Ter\u00e7a-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "S\u00e1bado",
    "Domingo",
]

DEFAULT_MOTIVOS = [
    ("0001", "DESCANSO SEMANAL"),
    ("0003", "PROBLEMA EL\u00c9TRICO"),
    ("0005", "TROCA DE ARTIGOS"),
    ("0007", "FALTA FIO"),
    ("0008", "FALTA PROGRAMA\u00c7\u00c3O"),
    ("0009", "MANUTEN\u00c7\u00c3O"),
    ("0010", "FALTA OPERADOR"),
    ("0011", "AJUSTE DE MAQUINA"),
    ("0012", "LIMPEZA"),
    ("0013", "REUNI\u00c3O"),
    ("0014", "TESTE DE QUALIDADE"),
    ("0015", "F\u00c9RIAS COLETIVAS"),
    ("0016", "PROBLEMA MAT\u00c9RIA PRIMA"),
    ("0017", "CORTE DE MALHA"),
    ("0018", "DEGRADE"),
    ("0019", "FALTA ENERGIA E AR COMPRIMIDO"),
    ("0020", "TROCA DE LYCRA"),
    ("0021", "EMBALAN. OU ETIQUET. SEM PESAR"),
    ("0022", "AGUARDANDO ABASTECIMENTO"),
    ("0023", "NADA PARA PESAR"),
    ("0024", "TECENDO COM SALDO DE FIOS"),
    ("0025", "FERIADO"),
    ("0026", "AGUARDANDO MANUTEN\u00c7\u00c3O"),
    ("0027", "AMOSTRA DE MALHA"),
    ("0100", "HOR\u00c1RIO DO LANCHE/ALMO\u00c7O/JANTA"),
]

DEFAULT_TEARES = [
    ("TEAR", "01", "ORIZIO 24/30 - 2.220 AGULHAS"),
    ("TEAR", "50", "ORIZIO 28/42 - 3.660 - AGULHAS"),
    ("TEAR", "02", "PAI LUNG 24/30 - 2.256 AGULHAS"),
    ("TEAR", "03", "MAYER 20/38 - 2.376 AGULHAS"),
    ("TEAR", "04", "MAYER 24/30 - 2.256 AGULHAS"),
    ("TEAR", "05", "PAI LUNG 18/30 - 2X 1.680 AGULHAS"),
    ("TEAR", "06", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "07", "ORIZIO 28/30 - 2.580 AGULHAS"),
    ("TEAR", "08", "PAI LUNG 18/30 - 1680 AGULHAS"),
    ("TEAR", "16", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "10", "MAYER 24/30 - 2.268 AGULHAS"),
    ("TEAR", "12", "MAYER 20/38 - 2.376 AGULHAS"),
    ("TEAR", "13", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "14", "ORIZIO 18/34 - 1.920 AGULHAS"),
    ("TEAR", "15", "ORIZIO 24/30 - 2.220 AGULHAS"),
    ("TEAR", "38", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "17", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "19", "MAYER 28/30 - 2.580 AGULHAS"),
    ("TEAR", "20", "MAYER 18/30 - 1.680 AGULHAS"),
    ("TEAR", "21", "ORIZIO 20/38 - 2.272X2 AGULHAS"),
    ("TEAR", "22", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "23", "ORIZIO 20/38 - 2.376 AGULHAS"),
    ("TEAR", "24", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "25", "ORIZIO 20/36 - 2.136 AGULHAS"),
    ("TEAR", "26", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "28", "ORIZIO 24/30 - 2.220 AGULHAS"),
    ("TEAR", "29", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "18", "ORIZIO 18/34 - 1.920 AGULHAS"),
    ("TEAR", "31", "ORIZIO 22/32 - 2.220 AGULHAS"),
    ("TEAR", "32", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "33", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "34", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "35", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "36", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "37", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "39", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "41", "ORIZIO 22/32 - 2.220 AGULHAS"),
    ("TEAR", "42", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "40", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "44", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "45", "ORIZIO 22/32 - 2.220 AGULHAS"),
    ("TEAR", "46", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "47", "PAI LUNG 24/30 - 2.220 AGULHAS"),
    ("TEAR", "48", "JUMBER 20/30 - AGULHAS"),
    ("TEAR", "49", "JUMBER 20/30 - AGULHAS"),
    ("TEAR", "27", "ORIZIO 28/32 - 2.760 AGULHAS"),
    ("TEAR", "09", "PAI LUNG 18/30 - 1.680 AGULHAS"),
    ("TEAR", "30", "MAYER 20/38 - 2.376 AGULHAS"),
    ("TEAR", "53", "ORIZIO 28/42 - 3.660 - AGULHAS"),
]

TURNO_DESCRICOES = {
    "1º TURNO": "1º TURNO (05:00 - 13:30)",
    "2º TURNO": "2º TURNO (13:30 - 22:00)",
    "3º TURNO": "3º TURNO (22:00 - 00:00 do dia anterior e 00:00 - 05:00 do dia atual)",
    "2º TURNO RODIZIO SABADO": "2º TURNO RODÍZIO SÁBADO (13:00 - 22:00)",
    "3º TURNO RODIZIO SABADO-DOMINGO": "3º TURNO RODÍZIO SÁBADO-DOMINGO (22:00 - 00:00 e 00:00 - 05:00)",
    "1º TURNO RODIZIO DOMINGO": "1º TURNO RODÍZIO DOMINGO (05:00 - 13:30)",
    "2º TURNO RODIZIO DOMINGO": "2º TURNO RODÍZIO DOMINGO (13:30 - 22:00)",
}

OPERACIONAL_TURNOS = {
    "1º TURNO",
    "2º TURNO",
    "3º TURNO",
    "2º TURNO RODIZIO SABADO",
    "3º TURNO RODIZIO SABADO-DOMINGO",
    "1º TURNO RODIZIO DOMINGO",
    "2º TURNO RODIZIO DOMINGO",
}


def normalize_turno_nome(value: str) -> str:
    if value is None:
        return ""
    txt = unicodedata.normalize("NFKD", str(value))
    txt = txt.encode("ASCII", "ignore").decode("ASCII")
    return " ".join(txt.upper().split())


TURNOS_CANONICOS = {
    "1 TURNO": "1º TURNO",
    "2 TURNO": "2º TURNO",
    "3 TURNO": "3º TURNO",
    "2 TURNO RODIZIO SABADO": "2º TURNO RODIZIO SABADO",
    "3 TURNO RODIZIO SABADO-DOMINGO": "3º TURNO RODIZIO SABADO-DOMINGO",
    "1 TURNO RODIZIO DOMINGO": "1º TURNO RODIZIO DOMINGO",
    "2 TURNO RODIZIO DOMINGO": "2º TURNO RODIZIO DOMINGO",
    "TODOS": "TODOS",
}


def canonical_turno_nome(value: str) -> str:
    return TURNOS_CANONICOS.get(normalize_turno_nome(value), (value or "").strip())

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_hhmm_to_minutes(value: str):
    try:
        hour_str, minute_str = value.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
    except (ValueError, AttributeError):
        return None

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return (hour * 60) + minute


def normalize_motivo_codigo(value: str):
    if value is None:
        return None
    codigo = str(value).strip()
    if not codigo.isdigit():
        return None
    numero = int(codigo)
    if numero < 1 or numero > 9999:
        return None
    return f"{numero:04d}"


def calculate_total(inicio: str, fim: str) -> str:
    inicio_min = parse_hhmm_to_minutes(inicio)
    fim_min = parse_hhmm_to_minutes(fim)
    if inicio_min is None or fim_min is None:
        return "00:00"

    if fim_min < inicio_min:
        fim_min += 24 * 60

    total_min = fim_min - inicio_min
    hours = total_min // 60
    minutes = total_min % 60
    return f"{hours:02d}:{minutes:02d}"


def parse_status_datetime(data_str: str, hora_str: str):
    try:
        return datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
    except ValueError:
        return None


def parse_iso_datetime(date_iso: str, hour_hhmm: str):
    try:
        return datetime.strptime(f"{date_iso} {hour_hhmm}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def validate_descanso_periodo(data_de: str, hora_de: str, data_ate: str, hora_ate: str):
    dt_de = parse_iso_datetime(data_de, hora_de)
    dt_ate = parse_iso_datetime(data_ate, hora_ate)
    if dt_de is None or dt_ate is None:
        return None, None, "Período inválido."

    if dt_de > dt_ate:
        return None, None, "Data/Hora inicial deve ser menor ou igual à final."

    if not is_descanso_window(dt_de):
        return None, None, "Descanso semanal só pode iniciar no sábado (13:00-00:00) ou domingo (00:00-22:30)."

    if not is_descanso_window(dt_ate):
        return None, None, "Descanso semanal só pode terminar no sábado (13:00-00:00) ou domingo (00:00-22:30)."

    return dt_de, dt_ate, None


def format_duration_hhmm(delta: timedelta) -> str:
    total_seconds = int(max(delta.total_seconds(), 0))
    total_minutes = total_seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"


def format_duration_hhmmss(delta: timedelta) -> str:
    total_seconds = int(max(delta.total_seconds(), 0))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def pcfim_to_minutes(value) -> int:
    if value is None:
        return 0
    text = str(value).strip()
    if not text:
        return 0
    if ":" in text:
        parts = text.split(":")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            return (int(parts[0]) * 60) + int(parts[1])
        return 0
    try:
        horas = float(text.replace(",", "."))
    except ValueError:
        return 0
    return max(int(round(horas * 60)), 0)


def format_pcfim_display(value) -> str:
    mins = pcfim_to_minutes(value)
    horas = mins // 60
    minutos = mins % 60
    return f"{horas:02d}h:{minutos:02d}min"


def get_user_turnos(conn: sqlite3.Connection, user_id: int):
    rows = conn.execute(
        """
        SELECT t.nome
        FROM usuario_tipos_turno ut
        INNER JOIN turnos t ON t.id = ut.turno_id
        WHERE ut.usuario_id = ?
        """,
        (user_id,),
    ).fetchall()
    turnos = {canonical_turno_nome(row["nome"]) for row in rows}
    if "TODOS" in turnos:
        return set(OPERACIONAL_TURNOS)
    return turnos


def get_horarios_permitidos_texto(turnos_permitidos: set[str]) -> str:
    partes = []
    if "1º TURNO" in turnos_permitidos:
        partes.append("1º TURNO: 05:00 às 13:30")
    if "2º TURNO" in turnos_permitidos:
        partes.append("2º TURNO: 13:30 às 22:00")
    if "3º TURNO" in turnos_permitidos:
        partes.append("3º TURNO: 22:00 às 00:00 do dia anterior e 00:00 às 05:00 do dia atual")
    if "2º TURNO RODIZIO SABADO" in turnos_permitidos:
        partes.append("2º TURNO RODÍZIO SÁBADO: 13:00 às 22:00")
    if "3º TURNO RODIZIO SABADO-DOMINGO" in turnos_permitidos:
        partes.append("3º TURNO RODÍZIO SÁBADO-DOMINGO: sábado 22:00 às 00:00 e domingo 00:00 às 05:00")
    if "1º TURNO RODIZIO DOMINGO" in turnos_permitidos:
        partes.append("1º TURNO RODÍZIO DOMINGO: 05:00 às 13:30")
    if "2º TURNO RODIZIO DOMINGO" in turnos_permitidos:
        partes.append("2º TURNO RODÍZIO DOMINGO: 13:30 às 22:00")
    return ", ".join(partes) if partes else "Sem turno permitido."


def has_turno_operacional(turnos_permitidos: set[str]) -> bool:
    return bool(turnos_permitidos.intersection(OPERACIONAL_TURNOS))


def is_descanso_window(dt: datetime) -> bool:
    minutos = dt.hour * 60 + dt.minute
    # Sábado: 13:00 até 23:59
    if dt.weekday() == 5:
        return minutos >= 780
    # Domingo: 00:00 até 22:30
    if dt.weekday() == 6:
        return minutos <= 1350
    return False


def third_turn_start_minutes_for_previous_day(prev_day) -> int:
    return 1320


def third_turn_start_hhmm_for_day(day_ref) -> str:
    return "22:00"


def resolve_turno_by_horario(
    horario: str,
    data_evento,
    turnos_permitidos: set[str],
    hoje: datetime,
):
    minutos = parse_hhmm_to_minutes(horario)
    if minutos is None:
        return None, None, "Horário inválido."

    if not has_turno_operacional(turnos_permitidos):
        return None, None, "Você não possui turno operacional cadastrado."

    data_hoje = hoje.date()
    data_ontem = data_hoje - timedelta(days=1)

    # Pode registrar apenas no dia atual.
    # Exceção: faixa de início do 3º turno até 00:00 pode ser registrada no dia seguinte.
    inicio_3o_ontem = third_turn_start_minutes_for_previous_day(data_ontem)
    if data_evento == data_hoje:
        pass
    elif data_evento == data_ontem and minutos >= inicio_3o_ontem:
        pass
    else:
        return None, None, "A data deve ser o dia atual (ou dia anterior apenas para a faixa inicial do 3º turno)."

    # Fim de semana (sábado e domingo): regras específicas.
    if data_evento.weekday() == 5:
        if data_evento != data_hoje:
            return None, None, "No sábado, a data deve ser o dia atual."
        if 0 <= minutos < 300:
            if "3º TURNO" in turnos_permitidos:
                return "3º TURNO", data_evento, None
            return None, None, "Você só pode operar teares no seu turno."
        if 300 <= minutos < 540:
            if "1º TURNO" in turnos_permitidos:
                return "1º TURNO", data_evento, None
            return None, None, "Você só pode operar teares no seu turno."
        if 540 <= minutos < 780:
            if "2º TURNO" in turnos_permitidos:
                return "2º TURNO", data_evento, None
            return None, None, "Você só pode operar teares no seu turno."
        if 780 <= minutos < 1320:
            if "2º TURNO RODIZIO SABADO" in turnos_permitidos:
                return "2º TURNO RODIZIO SABADO", data_evento, None
            return None, None, "Você só pode operar teares no seu turno."
        if minutos >= 1320:
            if "3º TURNO RODIZIO SABADO-DOMINGO" in turnos_permitidos:
                return "3º TURNO RODIZIO SABADO-DOMINGO", data_evento, None
            return None, None, "Você só pode operar teares no seu turno."
        return None, None, "Horário fora da janela permitida de turnos."

    if data_evento.weekday() == 6:
        if data_evento != data_hoje:
            return None, None, "No domingo, a data deve ser o dia atual."
        if 0 <= minutos < 300:
            if "3º TURNO RODIZIO SABADO-DOMINGO" in turnos_permitidos:
                return "3º TURNO RODIZIO SABADO-DOMINGO", data_evento, None
            return None, None, "Você só pode operar teares no seu turno."
        if 300 <= minutos < 810:
            if "1º TURNO RODIZIO DOMINGO" in turnos_permitidos:
                return "1º TURNO RODIZIO DOMINGO", data_evento, None
            return None, None, "Você só pode operar teares no seu turno."
        if 810 <= minutos < 1320:
            if "2º TURNO RODIZIO DOMINGO" in turnos_permitidos:
                return "2º TURNO RODIZIO DOMINGO", data_evento, None
            return None, None, "Você só pode operar teares no seu turno."
        return None, None, "No domingo após 22:00 não há turno operacional cadastrado."

    # Dias úteis (segunda a sexta).
    if 300 <= minutos < 810:
        if "1º TURNO" not in turnos_permitidos:
            return None, None, "Você só pode operar teares no seu turno."
        if data_evento != data_hoje:
            return None, None, "No 1º turno, a data deve ser o dia atual."
        return "1º TURNO", data_evento, None

    if 810 <= minutos < 1320:
        if "2º TURNO" not in turnos_permitidos:
            return None, None, "Você só pode operar teares no seu turno."
        if data_evento != data_hoje:
            return None, None, "No 2º turno, a data deve ser o dia atual."
        return "2º TURNO", data_evento, None

    inicio_3o_hoje = third_turn_start_minutes_for_previous_day(data_hoje)
    if minutos >= inicio_3o_hoje:
        if "3º TURNO" not in turnos_permitidos:
            return None, None, "Você só pode operar teares no seu turno."
        if data_evento != data_ontem:
            return None, None, "No 3º turno entre início da faixa noturna e 00:00, selecione o dia anterior."
        return "3º TURNO", data_evento, None

    if minutos < 300:
        if "3º TURNO" not in turnos_permitidos:
            return None, None, "Você só pode operar teares no seu turno."
        if data_evento != data_hoje:
            return None, None, "No 3º turno entre 00:00 e 05:00, selecione o dia atual."
        return "3º TURNO", data_evento, None

    return None, None, "Horário fora da janela permitida de turnos."


def ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing_names = {column[1] for column in columns}
    if column_name not in existing_names:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def get_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT u.id, u.login, u.email, u.nivel, u.setor_id, s.nome AS setor_nome
            FROM usuarios u
            LEFT JOIN setores s ON s.id = u.setor_id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchone()

    if user is None:
        session.clear()
    return user


def is_level_6(user) -> bool:
    return user is not None and int(user["nivel"]) == 6


def can_operate_teares(user) -> bool:
    if user is None:
        return False
    try:
        return int(user["nivel"]) in {1, 2, 3, 6}
    except (TypeError, ValueError):
        return False


def can_access_enviar_turno(user, turno_nivel: int) -> bool:
    if user is None:
        return False
    try:
        nivel = int(user["nivel"])
    except (TypeError, ValueError):
        return False
    return nivel == 6 or nivel == turno_nivel


def can_access_enviar(user) -> bool:
    if user is None:
        return False
    try:
        return int(user["nivel"]) == 6
    except (TypeError, ValueError):
        return False


def fetch_producao_turno(data_iso: str, turno_nivel: int):
    if turno_nivel == 1:
        filtro_hora = "hora_ini >= '05:00:00' AND hora_ini < '13:30:00'"
    elif turno_nivel == 2:
        filtro_hora = "hora_ini >= '13:30:00' AND hora_ini < '22:00:00'"
    else:
        filtro_hora = "(hora_ini >= '22:00:00' OR hora_ini < '05:00:00')"

    query = """
        SELECT
            p.data_emi,
            p.funcionario,
            COALESCE(u.login, '') AS funcionario_nome,
            p.operacao,
            p.numero,
            COALESCE(m.descricao, '') AS motivo_descricao,
            p.hora_ini,
            p.hora_fim,
            p.pcfim
        FROM producao1_001 p
        LEFT JOIN usuarios u ON u.id_usuario = p.funcionario
        LEFT JOIN motivos m ON m.codigo = p.numero
        WHERE data_emi = ?
          AND """ + filtro_hora + """
        ORDER BY p.hora_ini ASC, p.numero ASC
    """
    with get_connection() as conn:
        rows = conn.execute(query, (data_iso,)).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["pcfim_display"] = format_pcfim_display(item.get("pcfim"))
        out.append(item)
    return out


def fetch_producao_dia(data_iso: str):
    query = """
        SELECT
            p.data_emi,
            p.funcionario,
            COALESCE(u.login, '') AS funcionario_nome,
            p.operacao,
            p.numero,
            COALESCE(m.descricao, '') AS motivo_descricao,
            p.hora_ini,
            p.hora_fim,
            p.pcfim
        FROM producao1_001 p
        LEFT JOIN usuarios u ON u.id_usuario = p.funcionario
        LEFT JOIN motivos m ON m.codigo = p.numero
        WHERE p.data_emi = ?
        ORDER BY p.hora_ini ASC, p.operacao ASC, p.numero ASC
    """
    with get_connection() as conn:
        rows = conn.execute(query, (data_iso,)).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["pcfim_display"] = format_pcfim_display(item.get("pcfim"))
        out.append(item)
    return out


def get_turno_nivel_from_nome(turno_nome: str) -> int:
    nome = canonical_turno_nome(turno_nome)
    if nome.startswith("1º"):
        return 1
    if nome.startswith("2º"):
        return 2
    if nome.startswith("3º"):
        return 3
    return 0


def get_dia_nome(data_ref) -> str:
    return DIAS_SEMANA[data_ref.weekday()]


def get_turno_windows_for_end_date(data_ref):
    dia_atual = get_dia_nome(data_ref)
    dia_anterior_data = data_ref - timedelta(days=1)
    dia_anterior = get_dia_nome(dia_anterior_data)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT te.dia, te.inicio, te.fim, t.nome AS turno_nome
            FROM turnos_empresa te
            INNER JOIN turnos t ON t.id = te.tipo_turno_id
            WHERE te.dia IN (?, ?)
            """,
            (dia_atual, dia_anterior),
        ).fetchall()

    windows = []
    for row in rows:
        inicio = str(row["inicio"])
        fim = str(row["fim"])
        turno_nome = canonical_turno_nome(row["turno_nome"] or "")
        inicio_min = parse_hhmm_to_minutes(inicio)
        fim_min = parse_hhmm_to_minutes(fim)
        if inicio_min is None or fim_min is None:
            continue

        cruza_meia_noite = fim_min < inicio_min
        if row["dia"] == dia_atual and not cruza_meia_noite:
            dt_inicio = datetime.combine(data_ref, datetime.strptime(inicio, "%H:%M").time())
            dt_fim = datetime.combine(data_ref, datetime.strptime(fim, "%H:%M").time())
        elif row["dia"] == dia_anterior and cruza_meia_noite:
            dt_inicio = datetime.combine(dia_anterior_data, datetime.strptime(inicio, "%H:%M").time())
            dt_fim = datetime.combine(data_ref, datetime.strptime(fim, "%H:%M").time())
        else:
            continue

        windows.append(
            {
                "turno_nome": turno_nome,
                "turno_nivel": get_turno_nivel_from_nome(turno_nome),
                "inicio": inicio,
                "fim": fim,
                "inicio_dt": dt_inicio,
                "fim_dt": dt_fim,
                "tipo_envio": f"window|{normalize_turno_nome(turno_nome)}|{inicio}-{fim}",
            }
        )

    windows.sort(key=lambda w: w["fim_dt"])
    return windows


def get_turno_window(data_iso: str, turno_nivel: int):
    dia_ref = datetime.strptime(data_iso, "%Y-%m-%d").date()
    if turno_nivel == 1:
        inicio = datetime.combine(dia_ref, datetime.strptime("05:00", "%H:%M").time())
        fim = datetime.combine(dia_ref, datetime.strptime("13:30", "%H:%M").time())
    elif turno_nivel == 2:
        inicio = datetime.combine(dia_ref, datetime.strptime("13:30", "%H:%M").time())
        fim = datetime.combine(dia_ref, datetime.strptime("22:00", "%H:%M").time())
    else:
        inicio_terceiro = third_turn_start_hhmm_for_day(dia_ref)
        inicio = datetime.combine(dia_ref - timedelta(days=1), datetime.strptime(inicio_terceiro, "%H:%M").time())
        fim = datetime.combine(dia_ref, datetime.strptime("05:00", "%H:%M").time())
    return inicio, fim


def delete_producao_in_window(conn: sqlite3.Connection, inicio: datetime, fim: datetime):
    conn.execute(
        """
        DELETE FROM producao1_001
        WHERE datetime(data_emi || ' ' || substr(hora_ini, 1, 8)) < ?
          AND datetime(
                (CASE
                    WHEN substr(hora_fim, 1, 8) < substr(hora_ini, 1, 8)
                    THEN date(data_emi, '+1 day')
                    ELSE data_emi
                 END) || ' ' || substr(hora_fim, 1, 8)
          ) > ?
        """,
        (fim.strftime("%Y-%m-%d %H:%M:%S"), inicio.strftime("%Y-%m-%d %H:%M:%S")),
    )


def insert_producao_interval(
    conn: sqlite3.Connection,
    inicio: datetime,
    fim: datetime,
    codigo_funcionario: str,
    numero_tear: str,
    cod_motivo: str,
):
    if fim <= inicio:
        return 0

    total = 0
    cursor = inicio
    while cursor < fim:
        prox_meia_noite = datetime.combine(cursor.date() + timedelta(days=1), datetime.min.time())
        parte_fim = min(fim, prox_meia_noite)
        duracao_horas = round((parte_fim - cursor).total_seconds() / 3600.0, 2)

        conn.execute(
            """
            INSERT INTO producao1_001
            (data_emi, funcionario, operacao, numero, qtde, pcini, hora_ini, hora_fim, pcfim, partida, observacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(data_emi, funcionario, operacao, numero, hora_ini, hora_fim)
            DO UPDATE SET
                qtde = excluded.qtde,
                pcini = excluded.pcini,
                pcfim = excluded.pcfim,
                partida = excluded.partida,
                observacao = excluded.observacao
            """,
            (
                cursor.strftime("%Y-%m-%d"),
                codigo_funcionario[:8],
                numero_tear[:3],
                cod_motivo[:6],
                1,
                None,
                cursor.strftime("%H:%M:%S"),
                parte_fim.strftime("%H:%M:%S"),
                duracao_horas,
                "",
                "",
            ),
        )
        total += 1
        cursor = parte_fim

    return total


def sync_producao_window(janela_inicio: datetime, janela_fim: datetime, cutoff_dt=None):
    efetivo_fim = janela_fim
    if cutoff_dt is not None and cutoff_dt < efetivo_fim:
        efetivo_fim = cutoff_dt
    if efetivo_fim <= janela_inicio:
        return 0
    with get_connection() as conn:
        teares_rows = conn.execute("SELECT id, numero FROM teares ORDER BY numero ASC").fetchall()
        usuarios_rows = conn.execute("SELECT login, id_usuario FROM usuarios").fetchall()
        status_rows = conn.execute(
            """
            SELECT id, tipo, tear_id, hora, data, cod_motivo, motivo, turno, responsavel
            FROM status_teares
            ORDER BY tear_id ASC, id ASC
            """
        ).fetchall()
        id_usuario_por_login = {str(row["login"]).lower(): (row["id_usuario"] or "") for row in usuarios_rows}

        status_por_tear = {}
        for row in status_rows:
            dt = parse_status_datetime(row["data"], row["hora"])
            if dt is None:
                continue
            if dt > efetivo_fim:
                continue
            status_por_tear.setdefault(int(row["tear_id"]), []).append((dt, row))

        delete_producao_in_window(conn, janela_inicio, efetivo_fim)

        total_inseridos = 0

        for tear in teares_rows:
            tear_id = int(tear["id"])
            numero_tear = str(tear["numero"]).zfill(3)
            eventos = status_por_tear.get(tear_id, [])
            if not eventos:
                continue

            funcionando = True
            parada_inicio = None
            parada_meta = None

            for dt, row in eventos:
                if dt <= janela_inicio:
                    if int(row["tipo"]) == 0:
                        funcionando = False
                        parada_meta = row
                    else:
                        funcionando = True
                        parada_meta = None
                    continue
                break

            if not funcionando:
                parada_inicio = janela_inicio

            for dt, row in eventos:
                if dt <= janela_inicio or dt > efetivo_fim:
                    continue

                tipo = int(row["tipo"])
                if funcionando:
                    if tipo == 0:
                        funcionando = False
                        parada_inicio = dt
                        parada_meta = row
                else:
                    if tipo == 1:
                        if parada_inicio is not None and dt > parada_inicio:
                            login_resp = str(parada_meta["responsavel"] or "").strip().lower() if parada_meta else ""
                            total_inseridos += insert_producao_interval(
                                conn,
                                parada_inicio,
                                dt,
                                str(id_usuario_por_login.get(login_resp, "")),
                                numero_tear,
                                str(parada_meta["cod_motivo"] or ""),
                            )
                        funcionando = True
                        parada_inicio = None
                        parada_meta = None
                    elif tipo == 0:
                        # Se houver nova parada dentro da própria parada, fecha a anterior e abre outra.
                        if parada_inicio is not None and dt > parada_inicio:
                            login_resp = str(parada_meta["responsavel"] or "").strip().lower() if parada_meta else ""
                            total_inseridos += insert_producao_interval(
                                conn,
                                parada_inicio,
                                dt,
                                str(id_usuario_por_login.get(login_resp, "")),
                                numero_tear,
                                str(parada_meta["cod_motivo"] or ""),
                            )
                        parada_inicio = dt
                        parada_meta = row

            if not funcionando and parada_inicio is not None and efetivo_fim > parada_inicio:
                login_resp = str(parada_meta["responsavel"] or "").strip().lower() if parada_meta else ""
                total_inseridos += insert_producao_interval(
                    conn,
                    parada_inicio,
                    efetivo_fim,
                    str(id_usuario_por_login.get(login_resp, "")),
                    numero_tear,
                    str(parada_meta["cod_motivo"] or ""),
                )

        conn.commit()
        return total_inseridos


def sync_producao_from_status(data_iso: str, turno_nivel: int, cutoff_dt=None):
    janela_inicio, janela_fim = get_turno_window(data_iso, turno_nivel)
    return sync_producao_window(janela_inicio, janela_fim, cutoff_dt=cutoff_dt)


def envio_turno_ja_executado(data_ref: str, turno_nivel: int, tipo: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM envios_turno
            WHERE data_ref = ? AND turno_nivel = ? AND tipo = ?
            LIMIT 1
            """,
            (data_ref, int(turno_nivel), tipo),
        ).fetchone()
    return row is not None


def registrar_envio_turno(data_ref: str, turno_nivel: int, tipo: str):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO envios_turno (data_ref, turno_nivel, tipo, enviado_em)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(data_ref, turno_nivel, tipo)
            DO UPDATE SET enviado_em = excluded.enviado_em
            """,
            (data_ref, int(turno_nivel), tipo, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()


def render_enviar_turno_page(user, turno_nivel: int, turno_titulo: str, faixa_horario: str, endpoint_name: str):
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_access_enviar_turno(user, turno_nivel):
        flash(f"Acesso permitido apenas para nivel 6 e nivel {turno_nivel}.")
        return redirect(url_for("sistema"))

    data_ref = request.args.get("data", "").strip()
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")

    try:
        datetime.strptime(data_ref, "%Y-%m-%d")
    except ValueError:
        flash("Data invalida.")
        return redirect(url_for(endpoint_name))

    if request.args.get("atualizar", "") == "1":
        agora = datetime.now()
        data_turno = datetime.strptime(data_ref, "%Y-%m-%d").date()
        hoje = agora.date()

        permitido = False
        if data_turno < hoje:
            permitido = True
        elif data_turno == hoje:
            minutos = (agora.hour * 60) + agora.minute
            if turno_nivel == 1 and minutos >= 810:  # 13:30
                permitido = True
            elif turno_nivel == 2 and minutos >= 1320:  # 22:00
                permitido = True
            elif turno_nivel == 3 and minutos >= 300:  # 05:00
                permitido = True

        if not permitido:
            flash("Turno ainda não finalizado para envio manual.")
        else:
            total = sync_producao_from_status(data_ref, turno_nivel)
            flash(f"{total} registro(s) atualizado(s) em producao1_001.")

    rows = fetch_producao_turno(data_ref, turno_nivel)
    return render_template(
        "enviar_turno.html",
        turno_nivel=turno_nivel,
        turno_titulo=turno_titulo,
        faixa_horario=faixa_horario,
        data_ref=data_ref,
        rows=rows,
        endpoint_name=endpoint_name,
        is_auto_mode=False,
    )


def can_manual_send_turno(data_ref: str, turno_nivel: int, now: datetime):
    data_turno = datetime.strptime(data_ref, "%Y-%m-%d").date()
    hoje = now.date()
    if data_turno < hoje:
        return True
    if data_turno > hoje:
        return False

    minutos = (now.hour * 60) + now.minute
    if turno_nivel == 1:
        return minutos >= 810  # 13:30
    if turno_nivel == 3:
        return minutos >= 300  # 05:00
    return False


def run_auto_sync_for_time(now: datetime):
    hhmm = now.strftime("%H:%M")
    data_ref = now.date()
    windows = get_turno_windows_for_end_date(data_ref)

    for window in windows:
        if window["fim"] != hhmm:
            continue
        ref_iso = window["fim_dt"].strftime("%Y-%m-%d")
        turno_nivel = int(window["turno_nivel"])
        tipo_envio = str(window["tipo_envio"])
        if envio_turno_ja_executado(ref_iso, turno_nivel, tipo_envio):
            continue
        sync_producao_window(window["inicio_dt"], window["fim_dt"])
        registrar_envio_turno(ref_iso, turno_nivel, tipo_envio)


def auto_sync_scheduler_loop():
    while True:
        try:
            now = datetime.now().replace(second=0, microsecond=0)
            key = now.strftime("%Y-%m-%d %H:%M")
            hhmm = now.strftime("%H:%M")
            if hhmm in {"00:00", "05:00", "09:00", "13:00", "13:30", "22:00"}:
                with AUTO_SYNC_LOCK:
                    if key not in AUTO_SYNC_LAST_EXEC:
                        run_auto_sync_for_time(now)
                        AUTO_SYNC_LAST_EXEC.add(key)
                        if len(AUTO_SYNC_LAST_EXEC) > 1000:
                            AUTO_SYNC_LAST_EXEC.clear()
        except Exception:
            # Mantém o loop ativo mesmo se uma execução falhar.
            pass
        time.sleep(20)


def start_auto_sync_scheduler():
    worker = threading.Thread(target=auto_sync_scheduler_loop, daemon=True)
    worker.start()


def get_setor_nivel(conn: sqlite3.Connection, setor_id: int) -> int:
    row = conn.execute("SELECT nivel FROM setores WHERE id = ?", (setor_id,)).fetchone()
    return int(row["nivel"]) if row else 1


def sync_session_level() -> None:
    user = get_current_user()
    if user is not None:
        session["nivel"] = user["nivel"]


def set_status_modal_feedback(
    tear_id: int,
    mensagem: str,
    horario: str = "",
    cod_motivo: str = "",
    data_evento: str = "",
    acao: str = "parar",
) -> None:
    session["status_modal_feedback"] = {
        "tear_id": int(tear_id),
        "mensagem": mensagem,
        "horario": horario,
        "cod_motivo": cod_motivo,
        "data_evento": data_evento,
        "acao": acao,
    }


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
            """
        )
        ensure_column(conn, "usuarios", "nivel", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(conn, "usuarios", "setor_id", "INTEGER")
        ensure_column(conn, "usuarios", "id_usuario", "TEXT")
        conn.execute("UPDATE usuarios SET id_usuario = CAST(id AS TEXT) WHERE id_usuario IS NULL OR TRIM(id_usuario) = ''")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_id_usuario ON usuarios(id_usuario)")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS setores (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE,
                nivel INTEGER NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS turnos (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS turnos_empresa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_turno_id INTEGER NOT NULL,
                dia TEXT NOT NULL,
                inicio TEXT NOT NULL,
                fim TEXT NOT NULL,
                total TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuario_tipos_turno (
                usuario_id INTEGER NOT NULL,
                turno_id INTEGER NOT NULL,
                PRIMARY KEY (usuario_id, turno_id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS motivos (
                codigo TEXT PRIMARY KEY,
                descricao TEXT NOT NULL UNIQUE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS teares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                numero TEXT NOT NULL UNIQUE,
                descricao TEXT
            )
            """
        )
        ensure_column(conn, "teares", "descricao", "TEXT")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS status_teares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo INTEGER NOT NULL CHECK (tipo IN (0, 1)),
                tear_id INTEGER NOT NULL,
                hora TEXT NOT NULL,
                data TEXT NOT NULL,
                cod_motivo TEXT,
                motivo TEXT,
                turno TEXT,
                responsavel TEXT
            )
            """
        )

        motivos_info = conn.execute("PRAGMA table_info(motivos)").fetchall()
        motivos_codigo_type = ""
        for col in motivos_info:
            if col["name"] == "codigo":
                motivos_codigo_type = str(col["type"] or "").upper()
                break
        if "INT" in motivos_codigo_type:
            conn.execute("ALTER TABLE motivos RENAME TO motivos_old")
            conn.execute(
                """
                CREATE TABLE motivos (
                    codigo TEXT PRIMARY KEY,
                    descricao TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.execute(
                """
                INSERT INTO motivos (codigo, descricao)
                SELECT printf('%04d', CAST(codigo AS INTEGER)), descricao
                FROM motivos_old
                """
            )
            conn.execute("DROP TABLE motivos_old")

        status_info = conn.execute("PRAGMA table_info(status_teares)").fetchall()
        status_cod_type = ""
        for col in status_info:
            if col["name"] == "cod_motivo":
                status_cod_type = str(col["type"] or "").upper()
                break
        if "INT" in status_cod_type:
            conn.execute("ALTER TABLE status_teares RENAME TO status_teares_old")
            conn.execute(
                """
                CREATE TABLE status_teares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo INTEGER NOT NULL CHECK (tipo IN (0, 1)),
                    tear_id INTEGER NOT NULL,
                    hora TEXT NOT NULL,
                    data TEXT NOT NULL,
                    cod_motivo TEXT,
                    motivo TEXT,
                    turno TEXT,
                    responsavel TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO status_teares (id, tipo, tear_id, hora, data, cod_motivo, motivo, turno, responsavel)
                SELECT
                    id,
                    tipo,
                    tear_id,
                    hora,
                    data,
                    CASE
                        WHEN cod_motivo IS NULL THEN NULL
                        ELSE printf('%04d', CAST(cod_motivo AS INTEGER))
                    END,
                    motivo,
                    turno,
                    responsavel
                FROM status_teares_old
                """
            )
            conn.execute("DROP TABLE status_teares_old")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS producao1_001 (
                data_emi DATE NULL,
                funcionario VARCHAR(8) NULL,
                operacao VARCHAR(5) NULL,
                numero VARCHAR(6) NULL,
                qtde NUMERIC(10, 2) DEFAULT 0 NULL,
                pcini NUMERIC(10, 2) DEFAULT 0 NULL,
                hora_ini VARCHAR(8) NULL,
                hora_fim VARCHAR(8) NULL,
                pcfim NUMERIC(10, 2) DEFAULT 0 NULL,
                partida VARCHAR(7) NULL,
                observacao VARCHAR(250) NULL
            )
            """
        )
        conn.execute(
            """
            UPDATE producao1_001
            SET pcfim = ROUND(
                (
                    (CAST(substr(CAST(pcfim AS TEXT), 1, 2) AS INTEGER) * 60) +
                    (CAST(substr(CAST(pcfim AS TEXT), 4, 2) AS INTEGER))
                ) / 60.0,
                2
            )
            WHERE CAST(pcfim AS TEXT) GLOB '[0-9][0-9]:[0-9][0-9]:[0-9][0-9]'
            """
        )
        conn.execute(
            """
            UPDATE producao1_001
            SET pcfim = ROUND(
                (
                    (CAST(substr(CAST(pcfim AS TEXT), 1, 2) AS INTEGER) * 60) +
                    (CAST(substr(CAST(pcfim AS TEXT), 4, 2) AS INTEGER))
                ) / 60.0,
                2
            )
            WHERE CAST(pcfim AS TEXT) GLOB '[0-9][0-9]:[0-9][0-9]'
            """
        )
        conn.execute(
            """
            DELETE FROM producao1_001
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM producao1_001
                GROUP BY data_emi, funcionario, operacao, numero, hora_ini, hora_fim
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_producao1_001_evento
            ON producao1_001 (data_emi, funcionario, operacao, numero, hora_ini, hora_fim)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS envios_turno (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_ref TEXT NOT NULL,
                turno_nivel INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                enviado_em TEXT NOT NULL,
                UNIQUE (data_ref, turno_nivel, tipo)
            )
            """
        )

        total_setores = conn.execute("SELECT COUNT(*) AS total FROM setores").fetchone()["total"]
        if total_setores == 0:
            conn.executemany(
                "INSERT INTO setores (id, nome, nivel) VALUES (?, ?, ?)",
                DEFAULT_SETORES,
            )

        total_turnos = conn.execute("SELECT COUNT(*) AS total FROM turnos").fetchone()["total"]
        if total_turnos == 0:
            conn.executemany(
                "INSERT INTO turnos (id, nome) VALUES (?, ?)",
                DEFAULT_TIPOS_TURNO,
            )
        else:
            # Normaliza registros antigos para o formato correto.
            conn.execute("UPDATE turnos SET nome = '1\u00ba TURNO' WHERE nome = '1o TURNO'")
            conn.execute("UPDATE turnos SET nome = '2\u00ba TURNO' WHERE nome = '2o TURNO'")
            conn.execute("UPDATE turnos SET nome = '3\u00ba TURNO' WHERE nome = '3o TURNO'")

        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_turnos_empresa_faixa
            ON turnos_empresa (tipo_turno_id, dia, inicio, fim)
            """
        )

        tipos = conn.execute("SELECT id, nome FROM turnos").fetchall()
        tipo_id_por_nome = {canonical_turno_nome(row["nome"]): int(row["id"]) for row in tipos}

        tipo_1 = tipo_id_por_nome.get("1º TURNO")
        tipo_2 = tipo_id_por_nome.get("2º TURNO")
        tipo_3 = tipo_id_por_nome.get("3º TURNO")
        tipo_rodizio_sab_2 = tipo_id_por_nome.get("2º TURNO RODIZIO SABADO")
        tipo_rodizio_sab_dom_3 = tipo_id_por_nome.get("3º TURNO RODIZIO SABADO-DOMINGO")
        tipo_rodizio_dom_1 = tipo_id_por_nome.get("1º TURNO RODIZIO DOMINGO")
        tipo_rodizio_dom_2 = tipo_id_por_nome.get("2º TURNO RODIZIO DOMINGO")

        conn.execute("DELETE FROM turnos_empresa")

        def add_turno_empresa(tipo_id: int | None, dia: str, inicio: str, fim: str) -> None:
            if tipo_id is None:
                return
            conn.execute(
                """
                INSERT INTO turnos_empresa (tipo_turno_id, dia, inicio, fim, total)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tipo_id, dia, inicio, fim, calculate_total(inicio, fim)),
            )

        # Segunda a sexta (normal)
        for dia in ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]:
            add_turno_empresa(tipo_1, dia, "05:00", "13:30")
            add_turno_empresa(tipo_2, dia, "13:30", "22:00")
            add_turno_empresa(tipo_3, dia, "22:00", "00:00")

        # Madrugadas de terça a sábado (normal)
        for dia in ["Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"]:
            add_turno_empresa(tipo_3, dia, "00:00", "05:00")

        # Sábado (regras novas)
        add_turno_empresa(tipo_1, "Sábado", "05:00", "09:00")
        add_turno_empresa(tipo_2, "Sábado", "09:00", "13:00")
        add_turno_empresa(tipo_rodizio_sab_2, "Sábado", "13:00", "22:00")
        add_turno_empresa(tipo_rodizio_sab_dom_3, "Sábado", "22:00", "00:00")

        # Domingo (rodízio)
        add_turno_empresa(tipo_rodizio_sab_dom_3, "Domingo", "00:00", "05:00")
        add_turno_empresa(tipo_rodizio_dom_1, "Domingo", "05:00", "13:30")
        add_turno_empresa(tipo_rodizio_dom_2, "Domingo", "13:30", "22:00")

        for codigo, descricao in DEFAULT_MOTIVOS:
            conn.execute(
                """
                INSERT INTO motivos (codigo, descricao)
                VALUES (?, ?)
                ON CONFLICT(codigo) DO UPDATE SET descricao = excluded.descricao
                """,
                (codigo, descricao),
            )

        # Normaliza registros legados de status com texto corrompido.
        conn.execute(
            """
            UPDATE status_teares
            SET motivo = (
                SELECT m.descricao
                FROM motivos m
                WHERE m.codigo = status_teares.cod_motivo
            )
            WHERE cod_motivo IS NOT NULL
            """
        )
        conn.execute("UPDATE status_teares SET turno = '1º TURNO' WHERE turno LIKE '1%TURNO'")
        conn.execute("UPDATE status_teares SET turno = '2º TURNO' WHERE turno LIKE '2%TURNO'")
        conn.execute("UPDATE status_teares SET turno = '3º TURNO' WHERE turno LIKE '3%TURNO'")

        for nome_tear, numero_tear, descricao_tear in DEFAULT_TEARES:
            tear_existente = conn.execute(
                "SELECT id FROM teares WHERE numero = ?",
                (numero_tear,),
            ).fetchone()
            if tear_existente is None:
                conn.execute(
                    "INSERT INTO teares (nome, numero, descricao) VALUES (?, ?, ?)",
                    (nome_tear, numero_tear, descricao_tear),
                )
            else:
                conn.execute(
                    "UPDATE teares SET nome = ?, descricao = ? WHERE numero = ?",
                    (nome_tear, descricao_tear, numero_tear),
                )

        admin = conn.execute("SELECT id FROM usuarios WHERE login = ?", ("admin",)).fetchone()
        if admin is None:
            conn.execute(
                "INSERT INTO usuarios (login, senha, email, nivel) VALUES (?, ?, ?, ?)",
                ("admin", generate_password_hash("123456"), "ti1@malhariaindaial.com.br", 6),
            )

        admin_id = conn.execute("SELECT id FROM usuarios WHERE login = ?", ("admin",)).fetchone()["id"]
        ti = conn.execute("SELECT id, nivel FROM setores WHERE nome = ?", ("TI",)).fetchone()

        if ti:
            conn.execute(
                "UPDATE usuarios SET senha = ?, email = ?, nivel = ?, setor_id = ? WHERE login = ?",
                (
                    generate_password_hash("123456"),
                    "ti1@malhariaindaial.com.br",
                    int(ti["nivel"]),
                    int(ti["id"]),
                    "admin",
                ),
            )

        turnos_admin = conn.execute(
            "SELECT COUNT(*) AS total FROM usuario_tipos_turno WHERE usuario_id = ?",
            (admin_id,),
        ).fetchone()["total"]
        if int(turnos_admin) == 0:
            todos = conn.execute("SELECT id FROM turnos WHERE nome = ?", ("TODOS",)).fetchone()
            if todos:
                conn.execute(
                    "INSERT OR IGNORE INTO usuario_tipos_turno (usuario_id, turno_id) VALUES (?, ?)",
                    (admin_id, int(todos["id"])),
                )

        conn.commit()


def get_user_by_login(login: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, login, senha, email, nivel, setor_id FROM usuarios WHERE login = ?",
            (login,),
        ).fetchone()


@app.get("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        senha = request.form.get("senha", "")
        user = get_user_by_login(login_value)

        if user and check_password_hash(user["senha"], senha):
            session["user_id"] = user["id"]
            session["login"] = user["login"]
            session["nivel"] = user["nivel"]
            flash("Login realizado.")
            return redirect(url_for("sistema"))

        flash("Usuario ou senha invalidos.")

    return render_template("login.html")


@app.get("/sistema")
def sistema():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))

    return render_template("sistema.html", login=user["login"], nivel=user["nivel"])


@app.get("/enviar-1-turno")
def enviar_1_turno():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_access_enviar(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))
    return redirect(url_for("enviar"))


@app.get("/enviar-2-turno")
def enviar_2_turno():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_access_enviar(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))
    return redirect(url_for("enviar"))


@app.get("/enviar-3-turno")
def enviar_3_turno():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_access_enviar(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))
    return redirect(url_for("enviar"))


@app.get("/enviar")
def enviar():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_access_enviar(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    data_ref = request.args.get("data", "").strip()
    if not data_ref:
        data_ref = datetime.now().strftime("%Y-%m-%d")

    try:
        datetime.strptime(data_ref, "%Y-%m-%d")
    except ValueError:
        flash("Data invalida.")
        return redirect(url_for("enviar"))

    rows = fetch_producao_dia(data_ref)
    return render_template(
        "enviar_turno.html",
        turno_nivel=0,
        turno_titulo="Enviar",
        faixa_horario="00:00 - 23:59",
        data_ref=data_ref,
        rows=rows,
        endpoint_name="enviar",
        is_auto_mode=True,
    )


@app.post("/enviar/manual")
def enviar_manual():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_access_enviar(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    data_ref = request.form.get("data", "").strip()

    try:
        datetime.strptime(data_ref, "%Y-%m-%d")
    except ValueError:
        flash("Data invalida.")
        return redirect(url_for("enviar"))

    agora = datetime.now()
    hoje = agora.date()
    data_sel = datetime.strptime(data_ref, "%Y-%m-%d").date()
    total_geral = 0
    passos = []

    def enviar_janela(ref_iso: str, turno: int, tipo: str, inicio_dt: datetime, fim_dt: datetime, rotulo=""):
        nonlocal total_geral
        if envio_turno_ja_executado(ref_iso, turno, tipo):
            return
        total = sync_producao_window(inicio_dt, fim_dt)
        registrar_envio_turno(ref_iso, turno, tipo)
        total_geral += total
        if rotulo:
            passos.append(rotulo)

    if data_sel > hoje:
        flash("Envio manual permitido apenas para hoje ou datas anteriores.")
        return redirect(url_for("enviar", data=data_ref))

    windows = get_turno_windows_for_end_date(data_sel)
    for window in windows:
        if data_sel == hoje and window["fim_dt"] > agora:
            continue
        ref_iso = window["fim_dt"].strftime("%Y-%m-%d")
        turno_nivel = int(window["turno_nivel"])
        tipo_envio = str(window["tipo_envio"])
        rotulo = f"{window['turno_nome']} ({window['inicio']}-{window['fim']})"
        enviar_janela(ref_iso, turno_nivel, tipo_envio, window["inicio_dt"], window["fim_dt"], rotulo)

    if passos:
        flash(f"Envio manual executado ({', '.join(passos)}). {total_geral} registro(s) processado(s).")
    else:
        flash("Nada para enviar agora (turnos já enviados ou ainda não aplicáveis).")
    return redirect(url_for("enviar", data=data_ref))


@app.get("/usuarios")
def usuarios():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                u.id,
                u.id_usuario,
                u.login,
                u.email,
                u.setor_id,
                u.nivel,
                COALESCE(s.nome, '-') AS setor_nome,
                COALESCE(GROUP_CONCAT(t.nome, ', '), '-') AS tipos_turno,
                COALESCE(GROUP_CONCAT(t.id, ','), '') AS tipos_turno_ids
            FROM usuarios u
            LEFT JOIN setores s ON s.id = u.setor_id
            LEFT JOIN usuario_tipos_turno ut ON ut.usuario_id = u.id
            LEFT JOIN turnos t ON t.id = ut.turno_id
            GROUP BY u.id, u.id_usuario, u.login, u.email, u.setor_id, u.nivel, s.nome
            ORDER BY u.login COLLATE NOCASE
            """
        ).fetchall()

        setores_rows = conn.execute("SELECT id, nome, nivel FROM setores ORDER BY nome ASC").fetchall()
        tipos_turno_rows = conn.execute("SELECT id, nome FROM turnos ORDER BY id ASC").fetchall()

    return render_template(
        "usuarios.html",
        usuarios=rows,
        setores=setores_rows,
        tipos_turno=tipos_turno_rows,
        current_user_id=user["id"],
    )


@app.post("/usuarios/adicionar")
def adicionar_usuario():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    id_usuario_raw = request.form.get("id_usuario", "").strip()
    login_value = request.form.get("login", "").strip()
    senha = request.form.get("senha", "")
    email = request.form.get("email", "").strip().lower()
    setor_id = request.form.get("setor_id", "").strip()
    tipos_turno_ids = request.form.getlist("tipos_turno_ids")

    if not login_value or not senha or not email or not setor_id:
        flash("Preencha usuario, senha, e-mail e setor.")
        return redirect(url_for("usuarios"))

    if not setor_id.isdigit():
        flash("Setor invalido.")
        return redirect(url_for("usuarios"))

    turno_ids_int = [int(x) for x in tipos_turno_ids if x.isdigit()]
    if not turno_ids_int:
        flash("Selecione ao menos um tipo de turno.")
        return redirect(url_for("usuarios"))

    id_usuario = ""
    if id_usuario_raw:
        if not id_usuario_raw.isdigit():
            flash("ID do usuario deve conter apenas numeros.")
            return redirect(url_for("usuarios"))
        id_usuario = id_usuario_raw

    with get_connection() as conn:
        if id_usuario:
            id_exists = conn.execute(
                "SELECT id FROM usuarios WHERE id_usuario = ?",
                (id_usuario,),
            ).fetchone()
            if id_exists:
                flash(f"ID de usuario ja cadastrado: {id_usuario}.")
                return redirect(url_for("usuarios"))

        login_exists = conn.execute(
            "SELECT id, login FROM usuarios WHERE LOWER(login) = LOWER(?)",
            (login_value,),
        ).fetchone()
        if login_exists:
            flash(f"Login ja cadastrado: {login_exists['login']}.")
            return redirect(url_for("usuarios"))

        email_exists = conn.execute(
            "SELECT id, email FROM usuarios WHERE LOWER(email) = LOWER(?)",
            (email,),
        ).fetchone()
        if email_exists:
            flash(f"E-mail ja cadastrado: {email_exists['email']}.")
            return redirect(url_for("usuarios"))

        setor_id_int = int(setor_id)
        nivel = get_setor_nivel(conn, setor_id_int)
        cursor = conn.execute(
            "INSERT INTO usuarios (id_usuario, login, senha, email, nivel, setor_id) VALUES (?, ?, ?, ?, ?, ?)",
            (id_usuario or None, login_value, generate_password_hash(senha), email, nivel, setor_id_int),
        )
        new_user_id = int(cursor.lastrowid)

        if not id_usuario:
            conn.execute("UPDATE usuarios SET id_usuario = ? WHERE id = ?", (str(new_user_id), new_user_id))

        conn.execute("DELETE FROM usuario_tipos_turno WHERE usuario_id = ?", (new_user_id,))
        for turno_id in sorted(set(turno_ids_int)):
            conn.execute(
                "INSERT OR IGNORE INTO usuario_tipos_turno (usuario_id, turno_id) VALUES (?, ?)",
                (new_user_id, turno_id),
            )
        conn.commit()

    flash("Usuario adicionado com sucesso.")
    return redirect(url_for("usuarios"))


@app.post("/usuarios/<int:usuario_id>/editar")
def editar_usuario(usuario_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    id_usuario_raw = request.form.get("id_usuario", "").strip()
    login_value = request.form.get("login", "").strip()
    senha = request.form.get("senha", "")
    email = request.form.get("email", "").strip().lower()
    setor_id = request.form.get("setor_id", "").strip()
    tipos_turno_ids = request.form.getlist("tipos_turno_ids")

    if not login_value or not email or not setor_id:
        flash("Preencha usuario, e-mail e setor.")
        return redirect(url_for("usuarios"))

    if not setor_id.isdigit():
        flash("Setor invalido.")
        return redirect(url_for("usuarios"))

    turno_ids_int = [int(x) for x in tipos_turno_ids if x.isdigit()]
    if not turno_ids_int:
        flash("Selecione ao menos um tipo de turno.")
        return redirect(url_for("usuarios"))

    novo_id_usuario = ""
    if id_usuario_raw:
        if not id_usuario_raw.isdigit():
            flash("ID do usuario deve conter apenas numeros.")
            return redirect(url_for("usuarios"))
        novo_id_usuario = id_usuario_raw

    with get_connection() as conn:
        atual = conn.execute("SELECT id_usuario FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        if atual is None:
            flash("Usuario nao encontrado.")
            return redirect(url_for("usuarios"))

        if not novo_id_usuario:
            novo_id_usuario = atual["id_usuario"] or str(usuario_id)

        id_exists = conn.execute(
            "SELECT id FROM usuarios WHERE id <> ? AND id_usuario = ?",
            (usuario_id, novo_id_usuario),
        ).fetchone()
        if id_exists:
            flash(f"ID de usuario ja cadastrado: {novo_id_usuario}.")
            return redirect(url_for("usuarios"))

        login_exists = conn.execute(
            """
            SELECT id, login
            FROM usuarios
            WHERE id <> ? AND LOWER(login) = LOWER(?)
            """,
            (usuario_id, login_value),
        ).fetchone()
        if login_exists:
            flash(f"Login ja cadastrado: {login_exists['login']}.")
            return redirect(url_for("usuarios"))

        email_exists = conn.execute(
            """
            SELECT id, email
            FROM usuarios
            WHERE id <> ? AND LOWER(email) = LOWER(?)
            """,
            (usuario_id, email),
        ).fetchone()
        if email_exists:
            flash(f"E-mail ja cadastrado: {email_exists['email']}.")
            return redirect(url_for("usuarios"))

        setor_id_int = int(setor_id)
        nivel = get_setor_nivel(conn, setor_id_int)

        if senha:
            conn.execute(
                "UPDATE usuarios SET id_usuario = ?, login = ?, senha = ?, email = ?, nivel = ?, setor_id = ? WHERE id = ?",
                (novo_id_usuario, login_value, generate_password_hash(senha), email, nivel, setor_id_int, usuario_id),
            )
        else:
            conn.execute(
                "UPDATE usuarios SET id_usuario = ?, login = ?, email = ?, nivel = ?, setor_id = ? WHERE id = ?",
                (novo_id_usuario, login_value, email, nivel, setor_id_int, usuario_id),
            )

        conn.execute("DELETE FROM usuario_tipos_turno WHERE usuario_id = ?", (usuario_id,))
        for turno_id in sorted(set(turno_ids_int)):
            conn.execute(
                "INSERT OR IGNORE INTO usuario_tipos_turno (usuario_id, turno_id) VALUES (?, ?)",
                (usuario_id, turno_id),
            )
        conn.commit()

    if int(user["id"]) == int(usuario_id):
        sync_session_level()

    flash("Usuario atualizado com sucesso.")
    return redirect(url_for("usuarios"))


@app.post("/usuarios/<int:usuario_id>/excluir")
def excluir_usuario(usuario_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    if int(user["id"]) == int(usuario_id):
        flash("Nao e permitido excluir o proprio usuario em uso.")
        return redirect(url_for("usuarios"))

    with get_connection() as conn:
        conn.execute("DELETE FROM usuario_tipos_turno WHERE usuario_id = ?", (usuario_id,))
        conn.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conn.commit()

    flash("Usuario excluido com sucesso.")
    return redirect(url_for("usuarios"))


@app.get("/setores")
def setores():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        rows = conn.execute("SELECT id, nome, nivel FROM setores ORDER BY nome ASC").fetchall()

    return render_template("setores.html", setores=rows)


@app.post("/setores/adicionar")
def adicionar_setor():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    nome = request.form.get("nome", "").strip().upper()
    nivel = request.form.get("nivel", "").strip()

    if not nome or not nivel.isdigit():
        flash("Informe nome e nivel valido para adicionar setor.")
        return redirect(url_for("setores"))

    with get_connection() as conn:
        conn.execute("INSERT INTO setores (nome, nivel) VALUES (?, ?)", (nome, int(nivel)))
        conn.commit()

    flash("Setor adicionado com sucesso.")
    return redirect(url_for("setores"))


@app.post("/setores/<int:setor_id>/editar")
def editar_setor(setor_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    nome = request.form.get("nome", "").strip().upper()
    nivel = request.form.get("nivel", "").strip()

    if not nome or not nivel.isdigit():
        flash("Informe nome e nivel valido para editar setor.")
        return redirect(url_for("setores"))

    with get_connection() as conn:
        conn.execute(
            "UPDATE setores SET nome = ?, nivel = ? WHERE id = ?",
            (nome, int(nivel), setor_id),
        )
        conn.commit()

    flash("Setor atualizado com sucesso.")
    return redirect(url_for("setores"))


@app.post("/setores/<int:setor_id>/excluir")
def excluir_setor(setor_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        conn.execute("DELETE FROM setores WHERE id = ?", (setor_id,))
        conn.commit()

    flash("Setor excluido com sucesso.")
    return redirect(url_for("setores"))


@app.get("/turnos-empresa")
def turnos_empresa():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                te.id,
                te.tipo_turno_id,
                te.dia,
                te.inicio,
                te.fim,
                te.total,
                t.nome AS tipo_nome
            FROM turnos_empresa te
            INNER JOIN turnos t ON t.id = te.tipo_turno_id
            ORDER BY
                te.tipo_turno_id,
                CASE te.dia
                    WHEN 'Segunda-feira' THEN 1
                    WHEN 'Terça-feira' THEN 2
                    WHEN 'Quarta-feira' THEN 3
                    WHEN 'Quinta-feira' THEN 4
                    WHEN 'Sexta-feira' THEN 5
                    WHEN 'Sábado' THEN 6
                    WHEN 'Domingo' THEN 7
                    ELSE 8
                END,
                te.inicio
            """
        ).fetchall()
        tipos_turno_rows = conn.execute("SELECT id, nome FROM turnos ORDER BY id ASC").fetchall()

    return render_template(
        "turnos_empresa.html",
        turnos_empresa=rows,
        tipos_turno=tipos_turno_rows,
        dias_semana=DIAS_SEMANA,
    )


@app.post("/turnos-empresa/adicionar")
def adicionar_turno_empresa():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    tipo_turno_id = request.form.get("tipo_turno_id", "").strip()
    dia = request.form.get("dia", "").strip()
    inicio = request.form.get("inicio", "").strip()
    fim = request.form.get("fim", "").strip()

    if not tipo_turno_id.isdigit() or dia not in DIAS_SEMANA:
        flash("Informe tipo de turno e dia validos.")
        return redirect(url_for("turnos_empresa"))

    if parse_hhmm_to_minutes(inicio) is None or parse_hhmm_to_minutes(fim) is None:
        flash("Informe horarios validos no formato HH:MM.")
        return redirect(url_for("turnos_empresa"))

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO turnos_empresa (tipo_turno_id, dia, inicio, fim, total)
            VALUES (?, ?, ?, ?, ?)
            """,
            (int(tipo_turno_id), dia, inicio, fim, calculate_total(inicio, fim)),
        )
        conn.commit()

    flash("Turno cadastrado com sucesso.")
    return redirect(url_for("turnos_empresa"))


@app.post("/turnos-empresa/<int:registro_id>/editar")
def editar_turno_empresa(registro_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    tipo_turno_id = request.form.get("tipo_turno_id", "").strip()
    dia = request.form.get("dia", "").strip()
    inicio = request.form.get("inicio", "").strip()
    fim = request.form.get("fim", "").strip()

    if not tipo_turno_id.isdigit() or dia not in DIAS_SEMANA:
        flash("Informe tipo de turno e dia validos.")
        return redirect(url_for("turnos_empresa"))

    if parse_hhmm_to_minutes(inicio) is None or parse_hhmm_to_minutes(fim) is None:
        flash("Informe horarios validos no formato HH:MM.")
        return redirect(url_for("turnos_empresa"))

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE turnos_empresa
            SET tipo_turno_id = ?, dia = ?, inicio = ?, fim = ?, total = ?
            WHERE id = ?
            """,
            (int(tipo_turno_id), dia, inicio, fim, calculate_total(inicio, fim), registro_id),
        )
        conn.commit()

    flash("Turno atualizado com sucesso.")
    return redirect(url_for("turnos_empresa"))


@app.post("/turnos-empresa/<int:registro_id>/excluir")
def excluir_turno_empresa(registro_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        conn.execute("DELETE FROM turnos_empresa WHERE id = ?", (registro_id,))
        conn.commit()

    flash("Turno excluido com sucesso.")
    return redirect(url_for("turnos_empresa"))


@app.get("/tipos-turno")
def tipos_turno():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        rows = conn.execute("SELECT id, nome FROM turnos ORDER BY id ASC").fetchall()

    return render_template("turnos.html", turnos=rows)


@app.get("/turnos")
def turnos_legacy():
    return redirect(url_for("tipos_turno"))


@app.post("/tipos-turno/adicionar")
@app.post("/turnos/adicionar")
def adicionar_turno():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    nome = request.form.get("nome", "").strip().upper()

    if not nome:
        flash("Informe o nome do tipo de turno.")
        return redirect(url_for("tipos_turno"))

    with get_connection() as conn:
        conn.execute("INSERT INTO turnos (nome) VALUES (?)", (nome,))
        conn.commit()

    flash("Tipo de turno adicionado com sucesso.")
    return redirect(url_for("tipos_turno"))


@app.post("/tipos-turno/<int:turno_id>/editar")
@app.post("/turnos/<int:turno_id>/editar")
def editar_turno(turno_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    nome = request.form.get("nome", "").strip().upper()
    if not nome:
        flash("Informe o nome do tipo de turno.")
        return redirect(url_for("tipos_turno"))

    with get_connection() as conn:
        conn.execute("UPDATE turnos SET nome = ? WHERE id = ?", (nome, turno_id))
        conn.commit()

    flash("Tipo de turno atualizado com sucesso.")
    return redirect(url_for("tipos_turno"))


@app.post("/tipos-turno/<int:turno_id>/excluir")
@app.post("/turnos/<int:turno_id>/excluir")
def excluir_turno(turno_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        conn.execute("DELETE FROM usuario_tipos_turno WHERE turno_id = ?", (turno_id,))
        conn.execute("DELETE FROM turnos WHERE id = ?", (turno_id,))
        conn.commit()

    flash("Tipo de turno excluido com sucesso.")
    return redirect(url_for("tipos_turno"))


@app.get("/motivos")
def motivos():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        rows = conn.execute("SELECT codigo, descricao FROM motivos ORDER BY codigo ASC").fetchall()

    return render_template("motivos.html", motivos=rows)


@app.get("/motivos/novo")
def novo_motivo():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    return render_template("motivo_form.html", modo="novo", motivo=None)


@app.post("/motivos/novo")
def criar_motivo():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    codigo_raw = request.form.get("codigo", "").strip()
    descricao = request.form.get("descricao", "").strip().upper()
    codigo = normalize_motivo_codigo(codigo_raw)
    if codigo is None or not descricao:
        flash("Informe codigo numerico de 1 a 9999 e descricao.")
        return redirect(url_for("novo_motivo"))

    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO motivos (codigo, descricao) VALUES (?, ?)",
                (codigo, descricao),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        flash("Codigo ou descricao ja cadastrada.")
        return redirect(url_for("novo_motivo"))

    flash("Motivo adicionado com sucesso.")
    return redirect(url_for("motivos"))


@app.get("/motivos/<codigo>/editar")
def editar_motivo_form(codigo: str):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        motivo = conn.execute(
            "SELECT codigo, descricao FROM motivos WHERE codigo = ?",
            (codigo,),
        ).fetchone()

    if motivo is None:
        flash("Motivo nao encontrado.")
        return redirect(url_for("motivos"))

    return render_template("motivo_form.html", modo="editar", motivo=motivo)


@app.post("/motivos/<codigo>/editar")
def atualizar_motivo(codigo: str):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    novo_codigo_raw = request.form.get("codigo", "").strip()
    descricao = request.form.get("descricao", "").strip().upper()
    novo_codigo = normalize_motivo_codigo(novo_codigo_raw)
    if novo_codigo is None or not descricao:
        flash("Informe codigo numerico de 1 a 9999 e descricao.")
        return redirect(url_for("editar_motivo_form", codigo=codigo))

    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE motivos SET codigo = ?, descricao = ? WHERE codigo = ?",
                (novo_codigo, descricao, codigo),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        flash("Codigo ou descricao ja cadastrada.")
        return redirect(url_for("editar_motivo_form", codigo=codigo))

    flash("Motivo atualizado com sucesso.")
    return redirect(url_for("motivos"))


@app.post("/motivos/<codigo>/excluir")
def excluir_motivo(codigo: str):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        conn.execute("DELETE FROM motivos WHERE codigo = ?", (codigo,))
        conn.commit()

    flash("Motivo excluido com sucesso.")
    return redirect(url_for("motivos"))


@app.get("/teares")
def teares():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        rows = conn.execute("SELECT id, nome, numero, descricao FROM teares ORDER BY numero ASC").fetchall()

    return render_template("teares.html", teares=rows)


@app.get("/teares/novo")
def novo_tear():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    return render_template("tear_form.html", modo="novo", tear=None)


@app.post("/teares/novo")
def criar_tear():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    nome = request.form.get("nome", "").strip().upper()
    numero = request.form.get("numero", "").strip()
    descricao = request.form.get("descricao", "").strip().upper()
    if not nome or not numero or not descricao:
        flash("Informe nome, numero e descricao.")
        return redirect(url_for("novo_tear"))

    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO teares (nome, numero, descricao) VALUES (?, ?, ?)",
                (nome, numero, descricao),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        flash("Numero de tear ja cadastrado.")
        return redirect(url_for("novo_tear"))

    flash("Tear adicionado com sucesso.")
    return redirect(url_for("teares"))


@app.get("/teares/<int:tear_id>/editar")
def editar_tear_form(tear_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        tear = conn.execute("SELECT id, nome, numero, descricao FROM teares WHERE id = ?", (tear_id,)).fetchone()

    if tear is None:
        flash("Tear nao encontrado.")
        return redirect(url_for("teares"))

    return render_template("tear_form.html", modo="editar", tear=tear)


@app.post("/teares/<int:tear_id>/editar")
def atualizar_tear(tear_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    nome = request.form.get("nome", "").strip().upper()
    numero = request.form.get("numero", "").strip()
    descricao = request.form.get("descricao", "").strip().upper()
    if not nome or not numero or not descricao:
        flash("Informe nome, numero e descricao.")
        return redirect(url_for("editar_tear_form", tear_id=tear_id))

    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE teares SET nome = ?, numero = ?, descricao = ? WHERE id = ?",
                (nome, numero, descricao, tear_id),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        flash("Numero de tear ja cadastrado.")
        return redirect(url_for("editar_tear_form", tear_id=tear_id))

    flash("Tear atualizado com sucesso.")
    return redirect(url_for("teares"))


@app.post("/teares/<int:tear_id>/excluir")
def excluir_tear(tear_id: int):
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not is_level_6(user):
        flash("Acesso permitido apenas para nivel 6.")
        return redirect(url_for("sistema"))

    with get_connection() as conn:
        conn.execute("DELETE FROM teares WHERE id = ?", (tear_id,))
        conn.commit()

    flash("Tear excluido com sucesso.")
    return redirect(url_for("teares"))


@app.get("/status-teares")
def status_teares():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))

    agora = datetime.now()
    with get_connection() as conn:
        teares_rows = conn.execute("SELECT id, nome, numero FROM teares ORDER BY numero ASC").fetchall()
        motivos_rows = conn.execute("SELECT codigo, descricao FROM motivos ORDER BY codigo ASC").fetchall()
        latest_rows = conn.execute(
            """
            SELECT st.*, mo.descricao AS motivo_oficial
            FROM status_teares st
            LEFT JOIN motivos mo ON mo.codigo = st.cod_motivo
            INNER JOIN (
                SELECT tear_id, MAX(id) AS max_id
                FROM status_teares
                GROUP BY tear_id
            ) mx ON mx.max_id = st.id
            """
        ).fetchall()
        turnos_usuario = get_user_turnos(conn, int(user["id"]))

    latest_por_tear = {int(row["tear_id"]): row for row in latest_rows}
    cards = []
    for tear in teares_rows:
        latest = latest_por_tear.get(int(tear["id"]))
        titulo = f"{tear['nome'].title()} {tear['numero']}"

        if latest is None:
            funcionando = True
            tempo = "0:00"
            motivo = "SEM REGISTRO"
            desde = agora
        else:
            desde = parse_status_datetime(latest["data"], latest["hora"]) or agora
            tempo = format_duration_hhmm(agora - desde)
            funcionando = int(latest["tipo"]) == 1
            motivo = latest["motivo_oficial"] or latest["motivo"] or "SEM REGISTRO"

        cards.append(
            {
                "tear_id": tear["id"],
                "titulo": titulo,
                "funcionando": funcionando,
                "numero_ordem": int("".join(ch for ch in str(tear["numero"]) if ch.isdigit()) or "0"),
                "tempo": tempo,
                "motivo": motivo,
                "funcionando_desde": desde.strftime("%d/%m/%Y %H:%M"),
                "parado_desde": desde.strftime("%d/%m/%Y %H:%M"),
            }
        )

    cards.sort(key=lambda c: (1 if c["funcionando"] else 0, c["numero_ordem"]))

    horarios_permitidos_texto = get_horarios_permitidos_texto(turnos_usuario)
    modal_feedback = session.pop("status_modal_feedback", None)
    data_iso_atual = agora.strftime("%Y-%m-%d")
    inicio_semana = (agora - timedelta(days=agora.weekday())).strftime("%Y-%m-%d")
    fim_semana = (agora + timedelta(days=(6 - agora.weekday()))).strftime("%Y-%m-%d")

    return render_template(
        "status_teares.html",
        cards=cards,
        motivos=motivos_rows,
        hora_atual=agora.strftime("%H:%M"),
        data_iso_atual=data_iso_atual,
        data_iso_inicio_semana=inicio_semana,
        data_iso_fim_semana=fim_semana,
        horarios_permitidos_texto=horarios_permitidos_texto,
        modal_feedback=modal_feedback,
        can_operar=can_operate_teares(user),
        nivel=user["nivel"],
    )


@app.post("/status-teares/parar")
def parar_tear_status():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_operate_teares(user):
        flash("Seu nível possui apenas visualização de status.")
        return redirect(url_for("status_teares"))

    tear_id = request.form.get("tear_id", "").strip()
    data_evento_iso = request.form.get("data_evento", "").strip()
    horario = request.form.get("horario", "").strip()
    cod_motivo = request.form.get("cod_motivo", "").strip()
    agora = datetime.now()

    if not tear_id.isdigit():
        flash("Tear inválido.")
        return redirect(url_for("status_teares"))
    if parse_hhmm_to_minutes(horario) is None:
        set_status_modal_feedback(int(tear_id), "Informe um horário válido.", horario, cod_motivo, data_evento_iso, "parar")
        return redirect(url_for("status_teares"))
    cod_motivo_norm = normalize_motivo_codigo(cod_motivo)
    if cod_motivo_norm is None:
        set_status_modal_feedback(int(tear_id), "Informe um motivo válido.", horario, cod_motivo, data_evento_iso, "parar")
        return redirect(url_for("status_teares"))
    try:
        data_evento = datetime.strptime(data_evento_iso, "%Y-%m-%d").date()
    except ValueError:
        set_status_modal_feedback(int(tear_id), "Informe uma data válida.", horario, cod_motivo, data_evento_iso, "parar")
        return redirect(url_for("status_teares"))

    inicio_semana = (agora - timedelta(days=agora.weekday())).date()
    fim_semana = inicio_semana + timedelta(days=6)
    if data_evento < inicio_semana or data_evento > fim_semana:
        set_status_modal_feedback(
            int(tear_id),
            "A data deve estar dentro da semana atual.",
            horario,
            cod_motivo,
            data_evento_iso,
            "parar",
        )
        return redirect(url_for("status_teares"))

    with get_connection() as conn:
        tear = conn.execute("SELECT id, nome, numero FROM teares WHERE id = ?", (int(tear_id),)).fetchone()
        if tear is None:
            flash("Tear não encontrado.")
            return redirect(url_for("status_teares"))

        motivo = conn.execute(
            "SELECT codigo, descricao FROM motivos WHERE codigo = ?",
            (cod_motivo_norm,),
        ).fetchone()
        if motivo is None:
            set_status_modal_feedback(int(tear_id), "Motivo inválido.", horario, cod_motivo, data_evento_iso, "parar")
            return redirect(url_for("status_teares"))

        latest = conn.execute(
            "SELECT id, tipo FROM status_teares WHERE tear_id = ? ORDER BY id DESC LIMIT 1",
            (int(tear_id),),
        ).fetchone()
        if latest is not None and int(latest["tipo"]) == 0:
            set_status_modal_feedback(int(tear_id), "Esse tear já está parado.", horario, cod_motivo, data_evento_iso, "parar")
            return redirect(url_for("status_teares"))

        turnos_permitidos = get_user_turnos(conn, int(user["id"]))

        turno_nome, data_evento_valida, erro = resolve_turno_by_horario(
            horario,
            data_evento,
            turnos_permitidos,
            agora,
        )
        if erro:
            set_status_modal_feedback(int(tear_id), erro, horario, cod_motivo, data_evento_iso, "parar")
            return redirect(url_for("status_teares"))

        conn.execute(
            """
            INSERT INTO status_teares (tipo, tear_id, hora, data, cod_motivo, motivo, turno, responsavel)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                0,
                int(tear_id),
                horario,
                data_evento_valida.strftime("%d/%m/%Y"),
                cod_motivo_norm,
                motivo["descricao"],
                turno_nome,
                user["login"],
            ),
        )
        conn.commit()

    flash("Tear parado com sucesso.")
    return redirect(url_for("status_teares"))


@app.post("/status-teares/iniciar")
def iniciar_tear_status():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_operate_teares(user):
        flash("Seu nível possui apenas visualização de status.")
        return redirect(url_for("status_teares"))

    tear_id = request.form.get("tear_id", "").strip()
    data_evento_iso = request.form.get("data_evento", "").strip()
    horario = request.form.get("horario", "").strip()
    agora = datetime.now()

    if not tear_id.isdigit():
        flash("Tear inválido.")
        return redirect(url_for("status_teares"))
    if parse_hhmm_to_minutes(horario) is None:
        set_status_modal_feedback(int(tear_id), "Informe um horário válido.", horario, "", data_evento_iso, "iniciar")
        return redirect(url_for("status_teares"))
    try:
        data_evento = datetime.strptime(data_evento_iso, "%Y-%m-%d").date()
    except ValueError:
        set_status_modal_feedback(int(tear_id), "Informe uma data válida.", horario, "", data_evento_iso, "iniciar")
        return redirect(url_for("status_teares"))

    inicio_semana = (agora - timedelta(days=agora.weekday())).date()
    fim_semana = inicio_semana + timedelta(days=6)
    if data_evento < inicio_semana or data_evento > fim_semana:
        set_status_modal_feedback(
            int(tear_id),
            "A data deve estar dentro da semana atual.",
            horario,
            "",
            data_evento_iso,
            "iniciar",
        )
        return redirect(url_for("status_teares"))

    with get_connection() as conn:
        tear = conn.execute("SELECT id FROM teares WHERE id = ?", (int(tear_id),)).fetchone()
        if tear is None:
            flash("Tear não encontrado.")
            return redirect(url_for("status_teares"))

        latest = conn.execute(
            """
            SELECT id, tipo, cod_motivo, motivo
            FROM status_teares
            WHERE tear_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(tear_id),),
        ).fetchone()
        if latest is None or int(latest["tipo"]) == 1:
            set_status_modal_feedback(int(tear_id), "Esse tear já está funcionando.", horario, "", data_evento_iso, "iniciar")
            return redirect(url_for("status_teares"))

        turnos_permitidos = get_user_turnos(conn, int(user["id"]))
        turno_nome, data_evento_valida, erro = resolve_turno_by_horario(
            horario,
            data_evento,
            turnos_permitidos,
            agora,
        )
        if erro:
            set_status_modal_feedback(int(tear_id), erro, horario, "", data_evento_iso, "iniciar")
            return redirect(url_for("status_teares"))

        motivo_oficial = None
        if latest["cod_motivo"] is not None:
            motivo_row = conn.execute(
                "SELECT descricao FROM motivos WHERE codigo = ?",
                (latest["cod_motivo"],),
            ).fetchone()
            if motivo_row is not None:
                motivo_oficial = motivo_row["descricao"]

        conn.execute(
            """
            INSERT INTO status_teares (tipo, tear_id, hora, data, cod_motivo, motivo, turno, responsavel)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                int(tear_id),
                horario,
                data_evento_valida.strftime("%d/%m/%Y"),
                latest["cod_motivo"],
                motivo_oficial or latest["motivo"],
                turno_nome,
                user["login"],
            ),
        )
        conn.commit()

    flash("Tear iniciado com sucesso.")
    return redirect(url_for("status_teares"))


@app.get("/descanso-semanal")
def descanso_semanal():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_operate_teares(user):
        flash("Seu nível possui apenas visualização de status.")
        return redirect(url_for("status_teares"))

    agora = datetime.now()
    inicio_semana = (agora - timedelta(days=agora.weekday())).date()
    sabado = inicio_semana + timedelta(days=5)
    domingo = inicio_semana + timedelta(days=6)

    with get_connection() as conn:
        teares_rows = conn.execute("SELECT id, nome, numero FROM teares ORDER BY numero ASC").fetchall()
        latest_rows = conn.execute(
            """
            SELECT st.*
            FROM status_teares st
            INNER JOIN (
                SELECT tear_id, MAX(id) AS max_id
                FROM status_teares
                GROUP BY tear_id
            ) mx ON mx.max_id = st.id
            """
        ).fetchall()

    latest_por_tear = {int(row["tear_id"]): row for row in latest_rows}
    teares = []
    for tear in teares_rows:
        latest = latest_por_tear.get(int(tear["id"]))
        parado_por_descanso = bool(latest is not None and int(latest["tipo"]) == 0 and (latest["cod_motivo"] or "") == "0001")
        teares.append(
            {
                "id": tear["id"],
                "label": f"{tear['nome']} {tear['numero']}",
                "parado_por_descanso": parado_por_descanso,
            }
        )

    return render_template(
        "descanso_semanal.html",
        teares=teares,
        data_de=sabado.strftime("%Y-%m-%d"),
        data_ate=domingo.strftime("%Y-%m-%d"),
        hora_de="13:00",
        hora_ate="22:30",
        data_min=sabado.strftime("%Y-%m-%d"),
        data_max=domingo.strftime("%Y-%m-%d"),
    )


@app.post("/descanso-semanal/desativar")
def descanso_desativar():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_operate_teares(user):
        flash("Seu nível possui apenas visualização de status.")
        return redirect(url_for("status_teares"))

    tear_ids = [int(x) for x in request.form.getlist("tear_ids_parar") if x.isdigit()]
    if not tear_ids:
        tear_ids = [int(x) for x in request.form.getlist("tear_ids") if x.isdigit()]
    data_de = request.form.get("data_de", "").strip()
    hora_de = request.form.get("hora_de", "").strip()
    data_ate = request.form.get("data_ate", "").strip()
    hora_ate = request.form.get("hora_ate", "").strip()
    agora = datetime.now()

    if not is_descanso_window(agora):
        flash("Descanso semanal só pode ser executado no sábado (13:00-00:00) e domingo (00:00-22:30).")
        return redirect(url_for("descanso_semanal"))

    if not tear_ids:
        flash("Selecione ao menos um tear.")
        return redirect(url_for("descanso_semanal"))

    dt_de, dt_ate, erro_periodo = validate_descanso_periodo(data_de, hora_de, data_ate, hora_ate)
    if erro_periodo:
        flash(erro_periodo)
        return redirect(url_for("descanso_semanal"))

    with get_connection() as conn:
        for tear_id in tear_ids:
            latest = conn.execute(
                "SELECT tipo FROM status_teares WHERE tear_id = ? ORDER BY id DESC LIMIT 1",
                (tear_id,),
            ).fetchone()
            if latest is not None and int(latest["tipo"]) == 0:
                continue

            conn.execute(
                """
                INSERT INTO status_teares (tipo, tear_id, hora, data, cod_motivo, motivo, turno, responsavel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    0,
                    tear_id,
                    dt_de.strftime("%H:%M"),
                    dt_de.strftime("%d/%m/%Y"),
                    "0001",
                    "DESCANSO SEMANAL",
                    "DESCANSO",
                    user["login"],
                ),
            )
        conn.commit()

    flash("Descanso semanal ativado para os teares selecionados.")
    return redirect(url_for("descanso_semanal"))


@app.post("/descanso-semanal/ativar")
def descanso_ativar():
    user = get_current_user()
    if user is None:
        flash("Faca login para acessar o sistema.")
        return redirect(url_for("login"))
    if not can_operate_teares(user):
        flash("Seu nível possui apenas visualização de status.")
        return redirect(url_for("status_teares"))

    tear_ids = [int(x) for x in request.form.getlist("tear_ids_ativar") if x.isdigit()]
    if not tear_ids:
        tear_ids = [int(x) for x in request.form.getlist("tear_ids") if x.isdigit()]
    data_de = request.form.get("data_de", "").strip()
    hora_de = request.form.get("hora_de", "").strip()
    data_ate = request.form.get("data_ate", "").strip()
    hora_ate = request.form.get("hora_ate", "").strip()
    agora = datetime.now()

    if not is_descanso_window(agora):
        flash("Descanso semanal só pode ser executado no sábado (13:00-00:00) e domingo (00:00-22:30).")
        return redirect(url_for("descanso_semanal"))

    if not tear_ids:
        flash("Selecione ao menos um tear.")
        return redirect(url_for("descanso_semanal"))

    dt_de, dt_ate, erro_periodo = validate_descanso_periodo(data_de, hora_de, data_ate, hora_ate)
    if erro_periodo:
        flash(erro_periodo)
        return redirect(url_for("descanso_semanal"))

    total_ativados = 0
    with get_connection() as conn:
        for tear_id in tear_ids:
            latest = conn.execute(
                """
                SELECT tipo, cod_motivo
                FROM status_teares
                WHERE tear_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (tear_id,),
            ).fetchone()

            if latest is None:
                continue
            if int(latest["tipo"]) != 0 or (latest["cod_motivo"] or "") != "0001":
                continue

            conn.execute(
                """
                INSERT INTO status_teares (tipo, tear_id, hora, data, cod_motivo, motivo, turno, responsavel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    1,
                    tear_id,
                    dt_ate.strftime("%H:%M"),
                    dt_ate.strftime("%d/%m/%Y"),
                    1,
                    "DESCANSO SEMANAL",
                    "DESCANSO",
                    user["login"],
                ),
            )
            total_ativados += 1
        conn.commit()

    flash(f"{total_ativados} tear(es) ativado(s) do descanso semanal.")
    return redirect(url_for("descanso_semanal"))




@app.get("/listaparadas")
def listaparadas():
    user = get_current_user()
    if user is None:
        return jsonify({"erro": "Nao autenticado."}), 401
    if not is_level_6(user):
        return jsonify({"erro": "Acesso negado para este usuario."}), 403

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                data_emi,
                funcionario,
                operacao,
                numero,
                qtde,
                pcini,
                hora_ini,
                hora_fim,
                pcfim,
                partida,
                observacao
            FROM producao1_001
            ORDER BY data_emi DESC, hora_ini DESC
            """
        ).fetchall()

    return jsonify([dict(row) for row in rows])

@app.get("/logout")
def logout():
    session.clear()
    flash("Sessao encerrada.")
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        start_auto_sync_scheduler()
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)

