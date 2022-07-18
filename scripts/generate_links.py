import re
import os
import argparse

patterns = [
    re.compile("^def (\w+)"),       # function pattern
    re.compile("^class (\w+)"),     # class pattern
    re.compile(".*# link: (\w+)")     # comment pattern
]

html = """<!DOCTYPE html>
<meta charset="utf-8">
<meta http-equiv="Refresh" content="0; URL={url}">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--url", default="https://github.com/alexflint/logical-induction/blob/master/{}#L{}")
    args = parser.parse_args()

    for path in args.sources:
        with open(path, "r") as f:
            for i, line in enumerate(f):
                for pattern in patterns:
                    match = re.match(pattern, line)
                    if not match:
                        continue

                    symbol = match.group(1)
                    if symbol.startswith("test_"):
                        continue

                    url = args.url.format(path, i+1)

                    print("{} at {}:{}".format(symbol, path, i+1))
                    print("  "+url)
                    print()

                    outpath = os.path.join(args.output, symbol + ".html")
                    with open(outpath, "w") as out:
                        out.write(html.format(url=url))


if __name__ == "__main__":
    main()
