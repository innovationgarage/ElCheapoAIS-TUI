def strw(s, x, y, c):
    y -= 1
    x -= 1
    lines = s.split("\n")
    return "\n".join(lines[:y] + [lines[y][:x] + c + lines[y][x+len(c):]] + lines[y+1:])
