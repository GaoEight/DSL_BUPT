REG STRING name "Alice"
REG NUM    score 95.5
REG BOOL   flag True
REG STRING copy $name
REG BOOL   pass  EQUAL $score 95.5
REG BOOL   high   GREATER $score 90
REG BOOL   ok     GREATER_EQUAL $score 
SPEAK "Hello " "How are you! " "I am " $name
INPUT name
SPEAK "My name is" $name