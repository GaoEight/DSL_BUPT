# 仅登录后操作
REG NUM credit 3.0
OPEN_COURSE "Python" $credit
# 验证开课结果
GPA 1
REG BOOL ok GREATER $result 0
SPEAK "开课结果=" $ok