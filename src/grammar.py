import re

def parse_entity_command(line):
    """
    解析 ENTITY 命令: COMMAND ENTITY key=value key2=value2 ...
    """
    pattern = r'^(?P<cmd>\w+)\s+(?P<entity>\w+)\s*(?P<args>.*)$'
    match = re.match(pattern, line.strip())
    if not match:
        return None

    cmd = match.group('cmd').upper()
    entity = match.group('entity').upper()
    args_str = match.group('args')

    # 解析参数 key=value
    args = dict(re.findall(r'(\w+)=["\']?([\w@.\-]+)["\']?', args_str))
    return {"type": "command", "cmd": cmd, "entity": entity, "args": args}
