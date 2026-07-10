import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    importance REAL DEFAULT 0.5,
    created_at TEXT NOT NULL,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_facts_importance ON facts(importance DESC);
"""


class MemoryStore:
    """SQLite 记忆存储：对话记录 + 用户事实。"""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or config.DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── 对话管理 ─────────────────────────────────────────

    def create_conversation(self, title: str = "") -> str:
        conv_id = uuid.uuid4().hex[:12]
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conv_id, title or "新对话", now, now),
            )
            conn.commit()
        return conv_id

    def list_conversations(self) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, updated_at FROM conversations ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_conversation(self, conv_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            conn.commit()

    # ── 消息管理 ─────────────────────────────────────────

    def add_message(self, conversation_id: str, role: str, content: str):
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, now),
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
            conn.commit()

    def get_recent_messages(self, conversation_id: str, limit: int | None = None) -> list[dict]:
        limit = limit or config.RECENT_MESSAGE_LIMIT
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
                (conversation_id, limit),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def message_count(self, conversation_id: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
        return row["cnt"]

    def get_all_messages(self, conversation_id: str) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id ASC",
                (conversation_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── 事实提取与检索 ──────────────────────────────────

    def add_fact(self, content: str, category: str = "general", importance: float = 0.5):
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            # 避免重复
            existing = conn.execute(
                "SELECT id FROM facts WHERE content = ?", (content,)
            ).fetchone()
            if existing:
                return
            conn.execute(
                "INSERT INTO facts (content, category, importance, created_at, last_accessed) VALUES (?, ?, ?, ?, ?)",
                (content, category, importance, now, now),
            )
            conn.commit()

    def search_facts(self, query: str, limit: int | None = None) -> list[dict]:
        limit = limit or config.MAX_FACTS_IN_PROMPT
        # 把用户消息拆成关键词
        keywords = [w.strip() for w in query.replace("？", " ").replace("?", " ").replace("，", " ").split() if len(w.strip()) >= 2]

        with self._get_conn() as conn:
            if not keywords:
                # 没有能搜的关键词，返回最重要的事实
                rows = conn.execute(
                    "SELECT * FROM facts ORDER BY importance DESC, access_count DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                # 对每个关键词做 LIKE 查询
                conditions = " OR ".join(["content LIKE ?" for _ in keywords])
                params = [f"%{kw}%" for kw in keywords]
                rows = conn.execute(
                    f"SELECT * FROM facts WHERE {conditions} ORDER BY importance DESC, access_count DESC LIMIT ?",
                    [*params, limit],
                ).fetchall()

                # 把搜到的事实标记为已访问
                fact_ids = [r["id"] for r in rows]
                if fact_ids:
                    placeholders = ",".join("?" for _ in fact_ids)
                    now = datetime.now().isoformat()
                    conn.execute(
                        f"UPDATE facts SET last_accessed = ?, access_count = access_count + 1 WHERE id IN ({placeholders})",
                        [now, *fact_ids],
                    )
                    conn.commit()

        return [dict(r) for r in rows]

    def extract_and_store_facts(self, conversation_id: str, llm_client):
        """调用模型从最近对话中提取关于用户的事实。"""
        messages = self.get_all_messages(conversation_id)
        # 至少要有一些对话才提取
        if len(messages) < 6:
            return

        # 格式化最近的消息
        transcript = "\n".join(
            f"{'用户' if m['role'] == 'user' else 'Nova'}: {m['content']}" for m in messages[-20:]
        )

        extract_prompt = f"""你是一个事实提取器。从以下对话中提取 3-5 条关于用户的、值得记住的具体事实。
每条事实应该是简洁的一句话，方便以后对话时回忆起。

格式：
FACT: <事实内容> | CATEGORY: <user_info/preference/event/general> | IMPORTANCE: <0.0-1.0>

对话记录：
{transcript}

        请提取事实："""

        try:
            raw = llm_client.complete(
                system_prompt="",
                messages=[{"role": "user", "content": extract_prompt}],
                max_tokens=512,
            )

            # 解析提取结果
            for line in raw.strip().split("\n"):
                line = line.strip()
                if line.startswith("FACT:") or line.startswith("- FACT:"):
                    line = line.lstrip("- ").removeprefix("FACT:").strip()
                    parts = [p.strip() for p in line.split("|")]
                    content = parts[0] if parts else line
                    category = "general"
                    importance = 0.5
                    for part in parts[1:]:
                        if "CATEGORY:" in part.upper():
                            category = part.split(":", 1)[-1].strip().lower()
                        if "IMPORTANCE:" in part.upper():
                            try:
                                importance = float(part.split(":", 1)[-1].strip())
                            except ValueError:
                                pass
                    if content:
                        self.add_fact(content, category, importance)
        except Exception as e:
            # 事实提取失败不影响主流程
            print(f"[memory] 事实提取失败: {e}")

    def should_extract_facts(self, conversation_id: str) -> bool:
        """判断是否应该触发事实提取。"""
        count = self.message_count(conversation_id)
        if count == 0:
            return False
        return count % config.FACT_EXTRACTION_INTERVAL == 0

    def get_all_facts(self, limit: int = 50) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM facts ORDER BY importance DESC, access_count DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
