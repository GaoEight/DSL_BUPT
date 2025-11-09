import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from pathlib import Path
from src.db import SchoolDB
from src.parser import VarStore
from src.parser import MiniInterp

def main():
    # 1. Python 侧：清空数据库并注册+登录老师
    db = SchoolDB("school.db")
    db.ensure_tables()          # 空库建表
    tid = db.register_teacher("Bob", "pwd", "bob@x.com")
    print(f"[Python] 注册并登录老师 Bob，id={tid}")

    # 2. DSL 侧：只执行登录后的操作
    dsl_file = Path("/media/gaoyunze/newspace/DSL_BUPT/test/test_open_course.dsl")
    if not dsl_file.exists():
        print("❌ 请先创建 test_open_course.dsl")
        return

    vars = VarStore()
    # 老师身份进入解释器
    interp = MiniInterp(vars, is_student=False, user_id=tid, db=db)

    print("=== 执行 DSL ===")
    with dsl_file.open(encoding="utf-8") as f:
        for no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            print(f"{no:02d}| {line}")
            interp.exec_line(line)
            vars.dump()
            print()

    # 3. 数据库侧验证
    courses = db.list_courses()
    print("=== 数据库验证 ===")
    for name, t_name, credit in courses:
        print(f"课程:{name} 教师:{t_name} 学分:{credit}")

if __name__ == "__main__":
    main()