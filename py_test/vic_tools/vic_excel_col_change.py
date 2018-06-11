def dec_to_excel_col(x):
    map_ = {0: '', 1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H', 9: 'I', 10: 'J', 11: 'K', 12: 'L',
            13: 'M', 14: 'N', 15: 'O', 16: 'P', 17: 'Q', 18: 'R', 19: 'S', 20: 'T', 21: 'U', 22: 'V', 23: 'W', 24: 'X',
            25: 'Y', 26: 'Z'}
    x_ = {}
    i = 1
    if x < 27:
        x_[1] = x
    else:
        while i > 0:
            y = int(x / 26)
            z = x % 26
            if z == 0:
                z = 26
                y = y - 1
            if y < 26:
                x_[i] = z
                x_[i + 1] = y
                i = 0
            else:
                x = y
                x_[i] = z
                i += 1
    value = ''
    for j in range(1, len(x_) + 1):
        value = value + map_[x_[len(x_) + 1 - j]]
    return value


def excel_col_to_dec(x):
    map_ = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 13,
            'N': 14, 'O': 15, 'P': 16, 'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21, 'V': 22, 'W': 23, 'X': 24, 'Y': 25,
            'Z': 26}
    x = x.upper()
    value = 0
    j = 0
    for i in x[::-1]:
        value = value + map_[i] * 26 ** j
        j += 1
    return value
