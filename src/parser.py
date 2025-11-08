import re
from typing import List, Any, Dict, Union, Optional, Callable




Val = Union[str, float, bool]

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

    # ---------- 取值 ----------
    def get(self, name: str) -> Optional[Val]:
        return self._map.get(name)          # 不存在返回 None

    # ---------- debug ----------
    def dump(self) -> None:
        for k, v in self._map.items():
            print(f"  {k} = {v!r}")



class Builtin:
    @staticmethod
    def equal(args: List[Any]) -> bool:
        if len(args) != 2:
            raise ValueError("EQUAL 需要 2 个参数")
        return args[0] == args[1]

    @staticmethod
    def greater(args: List[Any]) -> bool:
        if len(args) != 2:
            raise ValueError("GREATER 需要 2 个参数")
        a, b = args
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValueError("GREATER 只支持 NUM 类型")
        return a > b

    @staticmethod
    def gpa(args: List[Any]) -> float:
        if len(args) != 1:
            raise ValueError("GPA 需要 1 个参数")
        sid = str(args[0])
        # Todo
        return # StudentsDB().get_gpa(sid) 后续实现

    REGISTRY = {
        "EQUAL": equal,
        "GREATER": greater,
        "GPA": gpa,
    }
    
class ExprEval:
    def __init__(self, vars: VarStore):
        self.vars = vars

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
        if fname not in Builtin.REGISTRY:
            raise ValueError(f"未知函数: {fname}")
        args = [self.eval_token(t) for t in tokens[1:]]
        return Builtin.REGISTRY[fname](args)


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
    def __init__(self, vars: VarStore):
        self.vars = vars
        self.kw   = KeywordHub()
        self._register_builtins()
        self.expr = ExprEval(vars)

    def _register_builtins(self):
        self.kw.register("REG",   self._kw_reg)
        self.kw.register("SPEAK", self._kw_speak)
        self.kw.register("INPUT", self._kw_input)

    # 单入口：首单词 + 剩余整行
    def exec_line(self, line: str):
        line = line.strip()
        if not line or line.startswith("#"):
            # 注释功能
            return
        parts = line.split(maxsplit=1)
        first, tail = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")
        self.kw.dispatch(first.upper(), tail)

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
            val = ExprEval(self.vars).eval_expr(rhs)
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

    def _kw_speak(self, tail: str):
        # TODO: 后面再填
        pass

    def _kw_input(self, tail: str):
        # TODO: 后面再填
        pass


