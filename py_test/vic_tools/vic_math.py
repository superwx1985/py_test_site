from decimal import Context, ROUND_HALF_UP


def vic_round(number, ndigits=0):
    str_number = str(number)
    int_digits = str_number.find('.')
    result = Context(prec=int_digits+ndigits, rounding=ROUND_HALF_UP).create_decimal(str_number)
    return float(result)