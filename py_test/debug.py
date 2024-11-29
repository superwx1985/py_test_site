import re

r = re.findall(r'(?:^|,)re\[((?:[^\[\]]|\[[^\[\]]*\])*)\](?=,|$)', "re[1,3]", 0)

print(r)
