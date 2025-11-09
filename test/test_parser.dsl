REG NUM score 85
REG BOOL ok GREATER $score 80
SPEAK "结果=" $ok
# 直接调用函数
GPA 1001
REG BOOL high GREATER $_ 3.5
SPEAK " 高GPA=" $high