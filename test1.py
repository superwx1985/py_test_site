from py_test.general import vic_method
import time
from socket import timeout

err = 3

try:
    if err == 1:
        raise ValueError(1)
    elif err == 2:
        raise IOError(2)
    else:
        raise KeyError(3)
except (ValueError, IOError) as e:
    print(1, type(e))
except IOError as e:
    print(2, type(e))
except KeyError as e:
    print(3, type(e))