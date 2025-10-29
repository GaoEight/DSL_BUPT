from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
MAX_NODE = 300

class Node:
    __slots__ = ('text', 'nxt')
    def __init__(self, text: str, nxt: list[int]):
        self.text = text
        self.nxt = nxt  # [true, false]

class Tree:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.nodes: list[Node | None] = [None] * MAX_NODE
        self.size: int = 0

    def add_node(self, text: str, nxt=None) -> int:
        if self.size >= MAX_NODE:
            raise Exception("Too many nodes")
        if nxt is None:
            nxt = [-1, -1]
        self.nodes[self.size] = Node(text, nxt)
        self.size += 1
        return self.size - 1

    def load_from_file(self):
        """解析 DSL 文件并构建语法树"""
        with open(self.file_name, "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f if line.strip() != ""]
        stack = []   # (控制节点idx, indent)
        prev_idx = -1

        def get_indent(line: str) -> int:
            return len(line) - len(line.lstrip(" "))

        for raw in lines:
            indent = get_indent(raw)
            # indent 越大，层级越低
            text = raw.strip()
            cur_idx = self.add_node(text)

            if text.startswith("IF"):
                stack.append({"type": "IF", "idx": cur_idx, "indent": indent, "branches": []})
            elif text.startswith("ELIF") or text.startswith("ELSE"):
                # 前一个 IF/ELIF 连接到当前分支
                while stack and stack[-1]["indent"] > indent:
                    stack.pop()
                if not stack:
                    raise Exception("Unmatched ELIF/ELSE")
                top = stack[-1]
                self.nodes[top["idx"]].nxt[1] = cur_idx
                top["branches"].append(cur_idx)
                stack.append({"type": text.split()[0], "idx": cur_idx, "indent": indent, "branches": []})
            elif text.startswith("ENDIF"):
                # 闭合一个完整的 if 结构
                cur_block = []
                while stack and stack[-1]["type"] != "IF":
                    cur_block.append(stack.pop())
                if not stack:
                    raise Exception("Unmatched ENDIF")
                top_if = stack.pop()
                cur_block.append(top_if)

                top_idx = top_if["idx"]
                if self.nodes[top_idx].nxt[1] == -1:
                    self.nodes[top_idx].nxt[1] = cur_idx

                cur_block = sorted(cur_block, key=lambda x: x["idx"])

                # 找出各分支的终止语句，全部连向 ENDIF
                for branch in cur_block:
                    idx = branch["idx"]
                    # 找出该分支下的最后一条语句
                    j = idx + 1
                    while j < self.size and get_indent(lines[j]) > branch["indent"]:
                        j += 1
                    last_stmt = j - 1
                    if last_stmt >= idx:
                        self.nodes[last_stmt].nxt[0] = cur_idx  # 连到 ENDIF

            else:
                # 普通语句顺序执行
                if prev_idx != -1:
                    self.nodes[prev_idx].nxt[0] = cur_idx

            prev_idx = cur_idx

    def print_tree(self):
        print("语法树结构：")
        for i in range(self.size):
            n = self.nodes[i]
            print(f"[{i}] {n.text:25s} → nxt = {n.nxt}")



if __name__ == "__main__":
    test_tre =  Tree ("/media/gaoyunze/newspace/DSL_BUPT/test/test_ast.dsl")
    test_tre.load_from_file()
    test_tre.print_tree()