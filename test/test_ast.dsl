SPEAK "Welcome"
IF GPA > 3.5
    SPEAK "优秀学生"
ELIF GPA > 2.0
    SPEAK "继续努力"
    IF GPA < 3.0
        SPEAK "666"
        IF GPA > 3.0
            xxx
        ENDIF
    ENDIF
ELSE
    SPEAK "需要加油"
ENDIF
SPEAK "Done"