from pathlib import Path

line = Path("wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js").read_text(encoding="utf-8").splitlines()[514]
print("len", len(line))
print("has_lf", "\n" in line)
print("has_cr", "\r" in line)
for i, ch in enumerate(line):
    o = ord(ch)
    if o < 32 or o > 126:
        if ch not in " \t":
            print("special", i, repr(ch), hex(o))
