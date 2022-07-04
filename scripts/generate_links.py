import re
import os
import argparse

function_pattern = re.compile("^def (\w+)")
class_pattern = re.compile("^class (\w+)")

html = """<!DOCTYPE html>
<meta charset="utf-8">
<title>Redirecting to {url}</title>
<meta http-equiv="refresh" content="0; URL={url}">
<link rel="canonical" href="{url}">
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
                match = re.match(function_pattern, line) or re.match(class_pattern, line)
                if match:
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
