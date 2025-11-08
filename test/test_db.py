
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


from src.db import SchoolDB   

# 测试代码
# if __name__ == "__main__":
#    db = SchoolDB("school.db")
#    db.ensure_tables()
#    print("数据库与表已就绪")

# if __name__ == "__main__":
#     db = SchoolDB("school.db")
#     db.ensure_tables()
#     db.register_student("Alice", "123456", "alice@x.com")
#     print(db.login_student("Alice", "123456"))  # True
#     print(db.login_student("Alice", "wrong"))   # False
# if __name__ == "__main__":
#     db = SchoolDB("school.db")
#     db.ensure_tables()
#     sid = db.register_student("Alice1", "pwd", "alice1@x.com")
#     tid = db.register_teacher("Bob1", "pwd", "bob1@x.com")
#     db.create_course("Python", tid, 3.0)
#     db.create_course("Python", tid, 3.5)  # 同名第二门
#     eid = db.enroll_by_name(sid, "Python")
#     print("选课 id =", eid)

# if __name__ == "__main__":
#    db = SchoolDB("school.db")
#    db.ensure_tables()
#    tid = db.register_teacher("Bob", "pwd", "bob@x.com")
#    db.create_course("Python", tid, 3.0)
#    db.create_course("Math",  tid, 4.0)
#    courses = db.list_courses()
#    list_courses_cli(courses)

if __name__ == "__main__":
    db = SchoolDB("school.db")
    db.ensure_tables()

    # 1. 注册
    tid = db.register_teacher("Bob", "pwd", "bob@x.com")
    sid = db.register_student("Alice", "pwd", "alice@x.com")

    # 2. 老师开课
    cid = db.create_course("Python", tid, 3.0)
    print(f"开课成功，课程 id = {cid}")

    # 3. 学生选课（按名字选第一门）
    eid = db.enroll_by_name(sid, "Python")
    print(f"选课成功，选课记录 id = {eid}")

    # 4. 考勤（正常 → 迟到）
    db.record_attendance("Alice", cid, "normal")
    print("第一次考勤：normal")
    db.record_attendance("Alice", cid, "late_or_early")
    print("第二次考勤：late_or_early（已更新）")

    print("done")