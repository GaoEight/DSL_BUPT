# school_db.py
import sqlite3
import hashlib

from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, Tuple


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
                    email   TEXT NOT NULL,
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
                    email   TEXT NOT NULL,
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
    def register_student(self, name: str, pwd: str, email: str) -> int:
        """返回新学生 id；不再检查邮箱唯一"""
        with self as cur:
            h = hashlib.sha256(pwd.encode()).hexdigest()
            cur.execute(
                f"INSERT INTO {self.STUDENT_TABLE} (name, password, email) VALUES (?,?,?)",
                (name, h, email),
            )
            return cur.lastrowid

    def register_teacher(self, name: str, pwd: str, email: str) -> int:
        """返回新老师 id；不再检查邮箱唯一"""
        with self as cur:
            h = hashlib.sha256(pwd.encode()).hexdigest()
            cur.execute(
                f"INSERT INTO {self.TEACHER_TABLE} (name, password, email) VALUES (?,?,?)",
                (name, h, email),
            )
            return cur.lastrowid
        
    def login_student(self, name: str, pwd: str) -> bool:
        h = hashlib.sha256(pwd.encode()).hexdigest()
        with self as cur:
            cur.execute(
                f"SELECT 1 FROM {self.STUDENT_TABLE} WHERE name=? AND password=? LIMIT 1",
                (name, h),
            )
            return cur.fetchone() is not None

    def login_teacher(self, name: str, pwd: str) -> bool:
        h = hashlib.sha256(pwd.encode()).hexdigest()
        with self as cur:
            cur.execute(
                f"SELECT 1 FROM {self.TEACHER_TABLE} WHERE name=? AND password=? LIMIT 1",
                (name, h),
            )
            return cur.fetchone() is not None
    
    def create_course(self, name: str, teacher_id: int, credit: float = 0.0) -> int:
        """返回新课程 id；外键检查失败抛 ValueError"""
        with self as cur:
            try:
                cur.execute(
                    f"INSERT INTO {self.COURSE_TABLE} (name, teacher_id, credit) VALUES (?,?,?)",
                    (name, teacher_id, credit),
                )
                return cur.lastrowid
            except sqlite3.IntegrityError as e:
                if "FOREIGN KEY" in str(e):
                    raise ValueError("教师 id 不存在") from e
                raise
    def enroll_by_name(self, stu_id: int, course_name: str) -> int:
        """返回新选课记录 id；课程不存在或已选都会抛 ValueError"""
        with self as cur:
            # 1. 找最小 course_id
            cur.execute(
                f"SELECT id FROM {self.COURSE_TABLE} WHERE name=? ORDER BY id LIMIT 1",
                (course_name,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"课程 '{course_name}' 不存在")
            course_id = row[0]

            # 2. 插选课
            try:
                cur.execute(
                    f"INSERT INTO {self.ENROLL_TABLE} (student_id, course_id, score) VALUES (?,?,NULL)",
                    (stu_id, course_id),
                )
                return cur.lastrowid
            except sqlite3.IntegrityError as e:
                if "UNIQUE" in str(e):
                    raise ValueError("重复选课") from e
                raise
    def list_courses(self) -> List[Tuple[str, str, float]]:
        """返回 [(课程名, 教师名, 学分), ...]"""
        with self as cur:
            cur.execute(f"""
                SELECT c.name, t.name, c.credit
                FROM {self.COURSE_TABLE} c
                LEFT JOIN {self.TEACHER_TABLE} t ON c.teacher_id = t.id
                ORDER BY c.id
            """)
            return cur.fetchall()
        

    def record_attendance(self, stu_name: str, course_id: int, status: str) -> bool:
        """插入一条考勤记录；可重复打卡"""
        if status not in {'normal', 'absent', 'late_or_early'}:
            raise ValueError("状态只能是 normal/absent/late_or_early")

        with self as cur:
            # 1. 反查学生 id
            cur.execute(
                f"SELECT id FROM {self.STUDENT_TABLE} WHERE name=? LIMIT 1",
                (stu_name,)
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"学生 '{stu_name}' 不存在")
            stu_id = row[0]

            # 2. 确认选过该课程
            cur.execute(
                f"SELECT id FROM {self.ENROLL_TABLE} WHERE student_id=? AND course_id=? LIMIT 1",
                (stu_id, course_id)
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("学生未选此课程")
            enroll_id = row[0]

            # 3. 插入新考勤（每调用一次就是一条记录）
            cur.execute(
                f"INSERT INTO {self.ATTEND_TABLE} (enrollment_id, status, timestamp) "
                f"VALUES (?,?,?)",
                (enroll_id, status,
                 datetime.now().isoformat(timespec='seconds'))
            )
            return True    
        

    def set_score(self, course_name: str, teacher_name: str, stu_name: str, score: float) -> bool:
        """根据课程名+教师名+学生名，给第一条匹配选课记录赋分；无记录抛 ValueError，score 的取值范围为 0 - 100"""
        
        with self as cur:
            # 1. 定位到第一条匹配课程
            cur.execute(
                f"SELECT c.id FROM {self.COURSE_TABLE} c "
                f"JOIN {self.TEACHER_TABLE} t ON c.teacher_id = t.id "
                f"WHERE c.name = ? AND t.name = ? "
                f"ORDER BY c.id LIMIT 1",
                (course_name, teacher_name)
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("未找到指定课程或教师")
            course_id = row[0]

            # 2. 定位学生 id
            cur.execute(
                f"SELECT id FROM {self.STUDENT_TABLE} WHERE name = ? LIMIT 1",
                (stu_name,)
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"学生 '{stu_name}' 不存在")
            stu_id = row[0]

            # 3. 更新选课成绩
            cur.execute(
                f"UPDATE {self.ENROLL_TABLE} SET score = ? "
                f"WHERE student_id = ? AND course_id = ?",
                (score, stu_id, course_id)
            )
            if cur.rowcount == 0:
                raise ValueError("学生未选此课程，无法赋分")
            return True
    def calc_gpa(self, stu_id: int) -> float:
        """
        输入学生 id，返回加权 GPA（0-100 且非 0 的成绩才参与）
        单门公式：4 - 3*(100-x)^2 / 1600
        整体：Σ(学分 * 单门GPA) / Σ学分
        """
        with self as cur:
            cur.execute(
                f"""
                SELECT c.credit, e.score
                FROM {self.ENROLL_TABLE} e
                JOIN {self.COURSE_TABLE} c ON e.course_id = c.id
                WHERE e.student_id = ? AND e.score IS NOT NULL AND e.score != 0
                """,
                (stu_id,)
            )
            rows = cur.fetchall()
            if not rows:
                return 0.0

            total_weight, total_credit = 0.0, 0.0
            for credit, score in rows:
                course_gpa = 4.0 - 3.0 * (100.0 - score) ** 2 / 1600.0
                total_weight += credit * course_gpa
                total_credit += credit

            return total_weight / total_credit if total_credit else 0.0

def list_courses_cli(courses: List[Tuple[str, str, float]]) -> None:
    if not courses:
        print("暂无课程")
        return
    # 简单表格
    print(f"{'课程名':<20} {'教师':<15} {'学分':>6}")
    print("-" * 43)
    for c_name, t_name, credit in courses:
        print(f"{c_name:<20} {t_name or '—':<15} {credit:>6.1f}")



