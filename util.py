p = 115792089237316195423570985008687907853269984665640564039457584007908834671663
a = 0
b = 7
E = {"a": a, "b": b, "p": p}

G = [
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
]

shared = "e444aab09d543fa56b9ab9f8b5eaf00e16f66f938b36c76e0e5a8fbbe919993d" # ECDHKE

O = "Origin"
def eea(r0, r1):
    if r0 == 0:
        return (r1, 0, 1)
    else:
        g, s, t = eea(r1 % r0, r0)
        return (g, t - (r1 // r0) * s, s)


def add(P, Q, a, m):
    if (P == O):
        return Q
    elif (Q == O):
        return P
    elif ((P[0] == Q[0]) and (P[1] == m - Q[1])):
        return O
    else:
        if (P[0] == Q[0] and P[1] == Q[1]):
            S = ((3 * (pow(P[0], 2)) + a) * eea(2 * P[1], m)[1]) % m
        else:
            S = ((Q[1] - P[1]) * eea((Q[0] - P[0]) % m, m)[1]) % m
        x3 = (pow(S, 2) - P[0] - Q[0]) % m
        y3 = (S * (P[0] - x3) - P[1]) % m
        Q[0], Q[1] = x3, y3
        return [x3, y3]
    
def multiply(s, P, E):
    s = list(int(k) for k in "{0:b}".format(s))
    a, p = E["a"], E["p"]
    del s[0]
    T = P.copy()
    for i in range(len(s)):
        T = add(T, T, a, p)
        if (s[i] == 1):
            T = add(P, T, a, p)
    return T