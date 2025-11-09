import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import re
from typing import List, Any, Dict, Union, Optional, Callable
from src.db import SchoolDB



Val = Union[str, float, bool]

class Runtime:
    user_id: int
    is_student: bool
    db: SchoolDB

    # 显式构造函数
    def __init__(self, user_id: int, is_student: bool, db: SchoolDB):
        self.user_id = user_id
        self.is_student = is_student
        self.db = db

class VarStore:
    """名字→值 单映射，类型仅运行时检查，拒绝重名"""
    def __init__(self) -> None:
        self._map: Dict[str, Val] = {}

    # ---------- 注册 ----------
    def reg(self, name: str, value: Val) -> bool:
        """成功返回 True；重名或非法名返回 False 并打印错误"""
        if not name or not name[0].isalpha() or not name.replace('_', '').isalnum():
            print(f"[ERROR] 非法变量名: {name}")
            return False
        if name in self._map:
            print(f"[ERROR] 变量 '{name}' 已存在")
            return False
        self._map[name] = value
        return True
    
    def update(self, name: str, value: Val) -> bool:
        """
        存在则覆盖（跨类型），不存在则新建。
        返回 True 表示覆盖，False 表示新建
        """
        # 1. 非法变量名直接拒
        if not name or not name[0].isalpha() or not name.replace('_', '').isalnum():
            print(f"[ERROR] 非法变量名: {name}")
            return False

        # 2. 已存在 → 直接覆盖（允许跨类型）
        if name in self._map:
            self._map[name] = value
            return True

        # 3. 不存在 → 新建
        self._map[name] = value
        return False
    
    # ---------- 取值 ----------
    def get(self, name: str) -> Optional[Val]:
        return self._map.get(name)          # 不存在返回 None

    # ---------- debug ----------
    def dump(self) -> None:
        for k, v in self._map.items():
            print(f"  {k} = {v!r}")



class Builtin:
    
    def __init__(self, rt: Runtime):
        self.rt = rt
    
    def equal(self, args: List[Any]) -> bool:
        if len(args) != 2:
            raise ValueError("EQUAL 需要 2 个参数")
        return args[0] == args[1]

    def greater(self, args: List[Any]) -> bool:
        if len(args) != 2:
            raise ValueError("GREATER 需要 2 个参数")
        a, b = args
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("GREATER 只支持 NUM 类型")
        return a > b

    def gpa(self, args: list[Any]) -> float:
        sid = str(args[0])
        return self.rt.db.calc_gpa(sid)  

    # ---------------- 新增：开课 ----------------
    def open_course(self, args: list[Any]) -> bool:
        if len(args) != 2:
            raise ValueError("OPEN_COURSE 需要 2 个参数")
        name, credit = args
        if not isinstance(name, str) or not isinstance(credit, (int, float)):
            raise ValueError("参数类型错误")
        if self.rt.is_student:
            print("[ERROR] 学生不允许开课")
            return False
        try:
            self.rt.db.create_course(name, self.rt.user_id, float(credit))
            print(f"[OPEN_COURSE] 开课成功：{name}（{credit}学分）")
            return True
        except Exception as e:
            print(f"[OPEN_COURSE] 数据库错误：{e}")
            return False
    @property
    def registry(self) -> dict[str, Callable]:
        return {
            "EQUAL": self.equal,
            "GREATER": self.greater,
            "GPA": self.gpa,
            "OPEN_COURSE": self.open_course,
        }
    
class ExprEval:
    def __init__(self, vars: VarStore, rt: Runtime):
        self.vars = vars
        self.rt   = rt
        self.builtin = Builtin(rt)
    # ---------- 单 token ----------
    def eval_token(self, tok: str) -> Any:
        tok = tok.strip()
        if tok.startswith('$'):
            val = self.vars.get(tok[1:])
            if val is None:
                raise ValueError(f"未定义变量: {tok}")
            return val
        if tok in ("True", "False"):
            return tok == "True"
        if tok.startswith('"') and tok.endswith('"'):
            return tok[1:-1]
        try:
            return float(tok)
        except ValueError:
            raise ValueError(f"无法解析的字面量: {tok}")

    # ---------- 整行入口 ----------
    def eval_expr(self, line: str) -> Any:
        tokens = line.strip().split()
        if not tokens:
            raise ValueError("空表达式")

        # 1. 单 token → 直接算
        if len(tokens) == 1:
            return self.eval_token(tokens[0])

        # 2. 函数调用 → 首 token 是函数名
        fname = tokens[0].upper()
        if fname in self.builtin.registry:
            args = [self.eval_token(t) for t in tokens[1:]]
            return self.builtin.registry[fname](args)
        raise ValueError(f"未知函数: {fname}")


class KeywordHub:
    def __init__(self):
        self._map: Dict[str, Callable[[str], None]] = {}

    def register(self, kw: str, handler: Callable[[str], None]):
        if kw in self._map:
            print(f"[WARN] 关键字 '{kw}' 被覆盖")
        self._map[kw] = handler

    def dispatch(self, first: str, tail: str):
        if first not in self._map:
            print(f"[ERROR] 未知关键字: {first}")
            return
        self._map[first](tail)


class MiniInterp:
    def __init__(self, vars: VarStore, is_student: bool, user_id: int, db: SchoolDB):
        self.vars = vars
        self.rt   = Runtime(user_id, is_student, db)

        # 2. 组装表达式求值器（Builtin 已在内部实例化）
        self.expr = ExprEval(vars, self.rt)

        # 3. 关键字注册
        self.kw = KeywordHub()
        self._register_builtins()

    def _register_builtins(self):
        self.kw.register("REG",   self._kw_reg)
        self.kw.register("SPEAK", self._kw_speak)
        self.kw.register("INPUT", self._kw_input)

    # 单入口：首单词 + 剩余整行
    def exec_line(self, line: str):
        line = line.strip()
        if not line or line.startswith("#"):
            return
        parts = line.split(maxsplit=1)
        first, tail = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")

        # 1. 关键字优先
        if first.upper() in self.kw._map:
            self.kw.dispatch(first.upper(), tail)
            return

        if first.upper() in self.expr.builtin.registry:
            try:
                result = self.expr.eval_expr(line)   # 内部调 registry
                self.vars.update("result", result)           # 落盘默认变量
            except Exception as e:
                print(f"[ERROR] 函数执行失败: {e}")
            return

        print(f"[ERROR] 未知指令: {first}")
    
       # ---------- 关键字处理 ----------
    def _kw_reg(self, tail: str):
        # tail = "STRING A hello"  或  "STRING A $str1"  或  "BOOL flag EQUAL $x 30"
        m = re.fullmatch(r'(STRING|NUM|BOOL)\s+([A-Za-z_]\w*)(?:\s+(.+))?', tail)
        if not m:
            print(f"[ERROR] REG 语法错误: {tail}")
            return
        typ, name, rhs = m.groups()
        if not rhs:                       # 缺右值
            print(f"[ERROR] REG {typ} 缺少表达式")
            return

        try:
            val = self.expr.eval_expr(rhs)
        except Exception as e:
            print(f"[ERROR] 表达式求值失败: {e}")
            return

        # 类型检查
        if typ == "STRING" and not isinstance(val, str):
            print(f"[ERROR] 期望 STRING，得到 {type(val).__name__}")
            return
        if typ == "NUM" and not isinstance(val, (int, float)):
            print(f"[ERROR] 期望 NUM，得到 {type(val).__name__}")
            return
        if typ == "BOOL" and not isinstance(val, bool):
            print(f"[ERROR] 期望 BOOL，得到 {type(val).__name__}")
            return

        # 落盘
        if not self.vars.reg(name, val):   # 内部已做重名校验
            print(f"[ERROR] 变量 '{name}' 注册失败")

    

    def _kw_input(self, tail: str):
        # tail = "name"
        name = tail.strip()
        if not name:
            print("[ERROR] INPUT 缺少变量名")
            return
        if name not in self.vars._map:
            print(f"[ERROR] 变量 '{name}' 未注册")
            return
        if not isinstance(self.vars._map[name], str):
            print(f"[ERROR] 变量 '{name}' 必须是 STRING 类型")
            return

        # 读一行（保留空格，去掉末尾换行）
        value = input().rstrip('\n')
        self.vars._map[name] = value

    # def _kw_speak(self, tail: str):
        # TODO: 后面再填
        # pass
    def _kw_speak(self, tail: str):
        try:
            tokens = tokenize(tail)
        except ValueError as e:
            print(f"[SPEAK] {e}")
            return

        parts = []
        for tok in tokens:
            if tok.startswith('$'):          # 变量
                val = self.vars.get(tok[1:])
                if val is None:
                    print(f"[SPEAK] 未定义变量: {tok}")
                    return
                # 类型格式化
                if isinstance(val, str):
                    parts.append(val)
                elif isinstance(val, (int, float)):
                    parts.append(f"{val:.2f}")
                elif isinstance(val, bool):
                    parts.append("true" if val else "false")
                else:
                    print(f"[SPEAK] 未知类型变量: {tok}")
                    return
            else:                            # 字符串字面量
                parts.append(tok)
        print(''.join(parts), end='')



_TOKEN_RE = re.compile(r'"(.*?)"|(\$\w+)')


def tokenize(line: str) -> list[str]:
    out, last = [], 0
    line = line.lstrip()          # 1. 行首空白直接丢
    for m in _TOKEN_RE.finditer(line):
        # 2. 当前匹配点前若全是空白，允许跳过
        if m.start() != last and line[last:m.start()].isspace():
            last = m.start()      # 游标跳到非空位置
        if m.start() != last:     # 3. 仍有非空垃圾 → 报错
            raise ValueError(f"非法片段: {line[last:m.start()]!r}")
        # 4. 记录 token
        last = m.end()
        out.append(m.group(1) if m.group(1) is not None else m.group(2))

    # 5. 尾部空白也允许
    if line[last:].isspace():
        return out
    if last != len(line):
        raise ValueError(f"非法片段: {line[last:]!r}")
    return out