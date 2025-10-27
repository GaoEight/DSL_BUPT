# school_db.py
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


class SchoolDB:
    """
    面向对象封装 school 数据库的初始化与基础连接管理。
    用法示例：
        db = SchoolDB("school.db")
        db.ensure_tables()          # 建表
        with db as cur:             # 自动提交/回滚
            cur.execute("select * from students")
    """

    # -------------------- 表结构常量 --------------------
    STUDENT_TABLE = "students"
    TEACHER_TABLE = "teachers"
    COURSE_TABLE = "courses"
    ENROLL_TABLE = "enrollments"
    ATTEND_TABLE = "attendance"

    # ---------------------------------------------------
    def __init__(self, db_path: Union[str, Path] = "school.db"):
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None

    # -------------- 连接管理 --------------
    def open(self) -> sqlite3.Connection:
        """手动获取连接（后续需自行 close）"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> sqlite3.Cursor:
        """上下文管理器入口：返回游标，退出时自动 commit / close"""
        self.open()
        self._conn.__enter__()          # 开始事务
        return self._conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self.close()

    # -------------- 业务接口 --------------
    def ensure_tables(self):
        """若表不存在则创建"""
        with self as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.STUDENT_TABLE} (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    name    TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email   TEXT UNIQUE NOT NULL,
                    balance REAL DEFAULT 0.0,
                    gpa     REAL DEFAULT 0.0
                );
                """
            )

            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TEACHER_TABLE} (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    name    TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email   TEXT UNIQUE NOT NULL,
                    balance REAL DEFAULT 0.0
                );
                """
            )

            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.COURSE_TABLE} (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    name       TEXT NOT NULL,
                    teacher_id INTEGER,
                    credit     REAL DEFAULT 0.0,
                    FOREIGN KEY (teacher_id) REFERENCES {self.TEACHER_TABLE}(id)
                        ON DELETE SET NULL
                );
                """
            )

            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.ENROLL_TABLE} (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    course_id  INTEGER,
                    score      REAL DEFAULT NULL,
                    FOREIGN KEY (student_id) REFERENCES {self.STUDENT_TABLE}(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (course_id)  REFERENCES {self.COURSE_TABLE}(id)
                        ON DELETE CASCADE
                );
                """
            )

            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.ATTEND_TABLE} (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    enrollment_id INTEGER,
                    status        TEXT CHECK(status IN ('normal', 'absent', 'late_or_early')),
                    timestamp     TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (enrollment_id) REFERENCES {self.ENROLL_TABLE}(id)
                        ON DELETE CASCADE
                );
                """
            )


# 测试代码
# if __name__ == "__main__":
#    db = SchoolDB("school.db")
#    db.ensure_tables()
#    print("数据库与表已就绪")