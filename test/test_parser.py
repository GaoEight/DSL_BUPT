import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from parser import VarStore, ExprEval, MiniInterp  

def main(file: Path):
    tmp_var = VarStore()
    interp = MiniInterp(tmp_var)
    print("=== 逐行执行 ===")
    with file.open(encoding="utf-8") as f:
        for no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            print(f"{no:02d}| {line}")
            interp.exec_line(line)
            # 每行成功后 dump 一次
            interp.vars.dump()
            print()

    print("=== 最终快照 ===")
    interp.vars.dump()

if __name__ == "__main__":
    main(Path("/media/gaoyunze/newspace/DSL_BUPT/test/test_parser.dsl"))