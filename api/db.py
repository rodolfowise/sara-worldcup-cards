"""
Camada de acesso ao banco SQLite para o app Figurinhas da Copa.
"""
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "figurinhas.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Catálogo completo das figurinhas do álbum
    cur.execute("""
        CREATE TABLE IF NOT EXISTS figurinhas (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            sigla    TEXT NOT NULL,       -- ex: BRA, ARG, FRA
            numero   INTEGER NOT NULL,    -- ex: 1, 42
            nome     TEXT,               -- ex: Vinicius Jr.
            UNIQUE(sigla, numero)
        )
    """)

    # Coleção do usuário: quantas cópias de cada figurinha ele tem
    cur.execute("""
        CREATE TABLE IF NOT EXISTS colecao (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            figurinha_id  INTEGER NOT NULL REFERENCES figurinhas(id),
            quantidade    INTEGER NOT NULL DEFAULT 0,
            UNIQUE(figurinha_id)
        )
    """)

    conn.commit()
    conn.close()
    _seed_if_empty()


def _seed_if_empty():
    """Popula o catálogo com um conjunto de exemplo se estiver vazio."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as n FROM figurinhas")
    if cur.fetchone()["n"] == 0:
        paises = {
            "BRA": ["Alisson", "Danilo", "Marquinhos", "Thiago Silva", "Renan Lodi",
                    "Casemiro", "Lucas Paquetá", "Antony", "Rodrygo", "Richarlison", "Vinicius Jr."],
            "ARG": ["Martinez", "Molina", "Romero", "Otamendi", "Acuña",
                    "De Paul", "Fernandez", "Mac Allister", "Di Maria", "Lautaro", "Messi"],
            "FRA": ["Maignan", "Pavard", "Varane", "Upamecano", "Theo",
                    "Tchouameni", "Camavinga", "Griezmann", "Dembele", "Giroud", "Mbappe"],
            "ENG": ["Pickford", "Alexander-Arnold", "Stones", "Maguire", "Shaw",
                    "Bellingham", "Rice", "Saka", "Foden", "Kane", "Rashford"],
            "POR": ["Costa", "Cancelo", "Pepe", "Dias", "Guerreiro",
                    "Moutinho", "Bruno", "Bernardo", "Leao", "Andre", "Ronaldo"],
            "ALE": ["Neuer", "Kimmich", "Rudiger", "Schlotterbeck", "Raum",
                    "Goretzka", "Kroos", "Musiala", "Gnabry", "Havertz", "Muller"],
            "ESP": ["Unai", "Carvajal", "Laporte", "Pau", "Alba",
                    "Busquets", "Pedri", "Gavi", "Olmo", "Morata", "Ferran"],
            "ITA": ["Donnarumma", "Di Lorenzo", "Bonucci", "Bastoni", "Spinazzola",
                    "Barella", "Jorginho", "Verratti", "Chiesa", "Belotti", "Immobile"],
        }
        rows = []
        for sigla, jogadores in paises.items():
            for i, nome in enumerate(jogadores, start=1):
                rows.append((sigla, i, nome))
        cur.executemany(
            "INSERT OR IGNORE INTO figurinhas (sigla, numero, nome) VALUES (?, ?, ?)",
            rows
        )
        conn.commit()
    conn.close()


# ── Queries ──────────────────────────────────────────────────────────────────

def buscar_figurinha(sigla: str, numero: int):
    """Retorna a figurinha e a quantidade que o usuário possui."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.sigla, f.numero, f.nome,
               COALESCE(c.quantidade, 0) AS quantidade
        FROM figurinhas f
        LEFT JOIN colecao c ON c.figurinha_id = f.id
        WHERE UPPER(f.sigla) = UPPER(?) AND f.numero = ?
    """, (sigla, numero))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def listar_pais(sigla: str):
    """Lista todas as figurinhas de um país com status do usuário."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.sigla, f.numero, f.nome,
               COALESCE(c.quantidade, 0) AS quantidade
        FROM figurinhas f
        LEFT JOIN colecao c ON c.figurinha_id = f.id
        WHERE UPPER(f.sigla) = UPPER(?)
        ORDER BY f.numero
    """, (sigla,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def listar_repetidas():
    """Retorna figurinhas com quantidade >= 2."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.sigla, f.numero, f.nome, c.quantidade
        FROM colecao c
        JOIN figurinhas f ON f.id = c.figurinha_id
        WHERE c.quantidade >= 2
        ORDER BY f.sigla, f.numero
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def listar_faltando():
    """Retorna figurinhas que o usuário ainda não tem."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.sigla, f.numero, f.nome
        FROM figurinhas f
        LEFT JOIN colecao c ON c.figurinha_id = f.id
        WHERE COALESCE(c.quantidade, 0) = 0
        ORDER BY f.sigla, f.numero
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def listar_paises():
    """Retorna lista de siglas distintas."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT sigla FROM figurinhas ORDER BY sigla")
    rows = [r["sigla"] for r in cur.fetchall()]
    conn.close()
    return rows


def resumo():
    """Totais da coleção."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM figurinhas")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as n FROM colecao WHERE quantidade >= 1")
    tenho = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM colecao WHERE quantidade >= 2")
    repetidas = cur.fetchone()["n"]
    conn.close()
    return {"total": total, "tenho": tenho, "faltam": total - tenho, "repetidas": repetidas}


def _set_quantidade(figurinha_id: int, delta: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO colecao (figurinha_id, quantidade)
        VALUES (?, MAX(0, ?))
        ON CONFLICT(figurinha_id) DO UPDATE
        SET quantidade = MAX(0, quantidade + ?)
    """, (figurinha_id, delta, delta))
    conn.commit()
    cur.execute("SELECT quantidade FROM colecao WHERE figurinha_id = ?", (figurinha_id,))
    row = cur.fetchone()
    conn.close()
    return row["quantidade"] if row else 0


def incluir_figurinha(figurinha_id: int):
    return _set_quantidade(figurinha_id, 1)


def excluir_repetida(figurinha_id: int):
    return _set_quantidade(figurinha_id, -1)


def registrar_troca(entregue_id: int, recebida_id: int):
    """Remove uma cópia da entregue e adiciona uma da recebida."""
    conn = get_conn()
    cur = conn.cursor()

    # Remove cópia entregue
    cur.execute("""
        INSERT INTO colecao (figurinha_id, quantidade) VALUES (?, 0)
        ON CONFLICT(figurinha_id) DO UPDATE
        SET quantidade = MAX(0, quantidade - 1)
    """, (entregue_id,))

    # Adiciona cópia recebida
    cur.execute("""
        INSERT INTO colecao (figurinha_id, quantidade) VALUES (?, 1)
        ON CONFLICT(figurinha_id) DO UPDATE
        SET quantidade = quantidade + 1
    """, (recebida_id,))

    conn.commit()
    conn.close()
