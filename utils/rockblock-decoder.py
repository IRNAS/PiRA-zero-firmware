import struct 

# Simple decoder for messages sent via Iridium

message = "0000001d41e434f7419e0000420900000000001c4062a503405947ae40647ae10000001d42326996414f23c942bb7f49"

def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    for start in range(0, len(s), n):
        yield s[start:start+n]

def hex2float(s):
    bins = ''.join(chr(int(s[x:x+2], 16)) for x in range(0, len(s), 2))
    return struct.unpack('!Lfff', bins)

measurements = []

for chunk in chunks(message, 32):
    measurements.append(chunk)


print "['count', 'average', '  min ', '  max ']"
for s in measurements:
  a = hex2float(s)
  print ["%06.2f" % i for i in a]
