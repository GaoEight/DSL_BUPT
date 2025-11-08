
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


from src.db import SchoolDB   

def main():
    db = SchoolDB("school.db")
    db.ensure_tables()          # 会建表，若已存在则复用

    # 1. 注册师生
    tid = db.register_teacher("Bob", "pwd", "bob@x.com")
    print(f"[注册] 教师 Bob  id={tid}")

    sid = db.register_student("Alice", "pwd", "alice@x.com")
    print(f"[注册] 学生 Alice id={sid}")

    # 2. 老师开课（学分随意）
    cid1 = db.create_course("Python", tid, 3.0)
    cid2 = db.create_course("Math",    tid, 4.0)
    cid3 = db.create_course("PE",      tid, 1.0)
    print(f"[开课] Python id={cid1}, Math id={cid2}, PE id={cid3}")

    # 3. 学生选课（按名字选第一门）
    db.enroll_by_name(sid, "Python")
    db.enroll_by_name(sid, "Math")
    db.enroll_by_name(sid, "PE")
    print("[选课] Alice 已选 Python、Math、PE")

    # 4. 赋分（PE 给 0 分，表示未结课）
    db.set_score("Python", "Bob", "Alice", 85)
    db.set_score("Math",   "Bob", "Alice", 92)
    db.set_score("PE",     "Bob", "Alice", 0)   # 0 分不参与 GPA
    print("[赋分] Python=85, Math=92, PE=0（未结课）")

    # 5. 计算 GPA
    gpa = db.calc_gpa(sid)
    print(f"[GPA]  Alice 加权 GPA = {gpa:.3f}")

    # 6. 验证公式
    # Python: 4 - 3*(100-85)^2/1600 = 3.953125
    # Math  : 4 - 3*(100-92)^2/1600  = 3.88
    # 加权: (3*3.953125 + 4*3.88) / (3+4) ≈ 3.911
    print("[验证] 手工公式结果 ≈ 3.911 ✅" if abs(gpa - 3.911) < 0.001 else "❌")

if __name__ == "__main__":
    main()