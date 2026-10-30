def grade_calculator(marks):
    
    a = b = c = s = w = 0

    for mark in marks:
        if mark is None:
            continue

        if mark >= 75:
            a += 1
        elif mark >= 65:
            b += 1
        elif mark >= 55:
            c += 1
        elif mark >= 35:
            s += 1
        else:
            w += 1

    return [a, b, c, s, w]