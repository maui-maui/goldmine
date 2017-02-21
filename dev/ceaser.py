# ENCODE
(lambda s, k: s.translate(str.maketrans(('abcdefghijklmnopqrstuvwxyz' + 'abcdefghijklmnopqrstuvwxyz'.upper()), (lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))('abcdefghijklmnopqrstuvwxyz') + (lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))('abcdefghijklmnopqrstuvwxyz').upper())))('Hello, world! This works!', 3)

# DECODE
(lambda s, k: s.translate(str.maketrans((lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))('abcdefghijklmnopqrstuvwxyz') + (lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))('abcdefghijklmnopqrstuvwxyz').upper(), ('abcdefghijklmnopqrstuvwxyz' + 'abcdefghijklmnopqrstuvwxyz'.upper()))))('Khoor, zruog! Wklv zrunv!', 3)

'''
SOME HELPERS

# Alphabet aift function. argument (a) = alphabet
(lambda a: ''.join(a[(a.index(i) + k) % len(a)] for i in a))
'''

# MINIFIED
# ENCODE
(lambda s,k:s.translate(str.maketrans((a+a.upper()),(lambda:''.join(a[(a.index(i)+k)%26] for i in a))()+(lambda:''.join(a[(a.index(i)+k)%26] for i in a))().upper())))('Hello, world! This works!',3)

# DECODE
a,b=('abcdefghijklmnopqrstuvwxyz',(lambda:''.join(a[(a.index(i)+k)%26] for i in a))());(lambda s,k:s.translate(str.maketrans(b+b.upper(),(a+a.upper()))))('Khoor, zruog! Wklv zrunv!',3)

