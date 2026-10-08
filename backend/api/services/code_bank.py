from copy import deepcopy
from ..db import uid

STARTERS = {
 'Python': 'import sys\n\ndef solve(data):\n    # Parse input and return the required output.\n    return ""\n\nif __name__ == "__main__":\n    print(solve(sys.stdin.read()))\n',
 'JavaScript': 'const fs = require("fs");\nconst input = fs.readFileSync(0, "utf8");\nfunction solve(input) {\n  // Parse input and return the required output.\n  return "";\n}\nconsole.log(solve(input));\n',
 'Java': 'import java.io.*;\nimport java.util.*;\n\npublic class Main {\n  public static void main(String[] args) throws Exception {\n    Scanner sc = new Scanner(System.in);\n    // Read input and print the required output.\n  }\n}\n',
 'C++': '#include <bits/stdc++.h>\nusing namespace std;\nint main() {\n  ios::sync_with_stdio(false);\n  cin.tie(nullptr);\n  // Read input and print the required output.\n  return 0;\n}\n',
}

def problem(title, description, constraints, cases):
    return {'title': title, 'description': description, 'constraints': constraints,
            'tests': [{'stdin': a, 'expected': b} for a, b in cases]}

BANK = {
'easy': [
 problem('Sum the sequence', 'The first line contains n. The second line contains n space-separated integers. Print their sum.', '1 ≤ n ≤ 1000; each value is between -100000 and 100000.', [('4\n1 2 3 4\n','10'),('1\n-5\n','-5'),('5\n0 0 0 0 0\n','0'),('4\n-10 10 -2 2\n','0'),('3\n100000 100000 100000\n','300000')]),
 problem('Mirror word', 'Read one nonempty lowercase English word. Print YES if it reads the same forwards and backwards; otherwise print NO.', '1 ≤ word length ≤ 10000. Only lowercase a-z.', [('level\n','YES'),('python\n','NO'),('a\n','YES'),('abba\n','YES'),('abca\n','NO')]),
 problem('Vowel counter', 'Read a single line of English text, possibly empty. Count a, e, i, o, u in either case. Print the count. Spaces and punctuation are ignored.', '0 ≤ line length ≤ 10000; ASCII text.', [('Hello World\n','3'),('AEIOUaeiou\n','10'),('rhythm\n','0'),('\n','0'),('An example, indeed!\n','7')]),
],
'medium': [
 problem('Best contiguous sum', 'Read n on the first line and n integers on the second. Print the maximum sum of a nonempty contiguous subarray.', '1 ≤ n ≤ 100000; -10000 ≤ each value ≤ 10000. Aim for O(n).', [('9\n-2 1 -3 4 -1 2 1 -5 4\n','6'),('3\n-8 -2 -6\n','-2'),('1\n5\n','5'),('4\n1 2 3 4\n','10'),('4\n0 -1 0 -1\n','0')]),
 problem('Balanced brackets', 'Read one line containing only (), [], and {} (possibly empty). Print YES if every bracket is correctly paired and nested; otherwise print NO.', '0 ≤ length ≤ 100000. An empty string is balanced.', [('([]{})\n','YES'),('([)]\n','NO'),('(((\n','NO'),('\n','YES'),('{[()]}()\n','YES')]),
 problem('Distinct window', 'Read one lowercase English word. Print the length of its longest contiguous substring containing no repeated characters.', '1 ≤ length ≤ 100000. Aim for O(n).', [('abcabcbb\n','3'),('bbbbb\n','1'),('pwwkew\n','3'),('abcdef\n','6'),('abba\n','2')]),
],
'hard': [
 problem('Fewest coins', 'First line: n and target. Second line: n positive coin denominations. You may use each denomination any number of times. Print the minimum number of coins summing to target, or -1 if impossible.', '1 ≤ n ≤ 100; 0 ≤ target ≤ 10000; 1 ≤ coin ≤ 10000. Aim for O(n × target).', [('3 11\n1 2 5\n','3'),('1 3\n2\n','-1'),('2 0\n3 7\n','0'),('3 6\n1 3 4\n','2'),('2 14\n3 7\n','2')]),
 problem('Longest common subsequence', 'Read two nonempty lowercase English words, one per line. Print the length of their longest common subsequence. A subsequence preserves order but need not be contiguous.', '1 ≤ each length ≤ 500. Aim for O(n × m) time.', [('abcde\nace\n','3'),('abc\ndef\n','0'),('abc\nabc\n','3'),('aaaa\naa\n','2'),('aggtab\ngxtxayb\n','4')]),
 problem('Shortest unweighted path', 'First line: n m. Next m lines: undirected edges u v. Last line: source target. Vertices are numbered 0 to n-1. Print the fewest edges in a path from source to target, or -1 if unreachable.', '1 ≤ n ≤ 10000; 0 ≤ m ≤ 20000. Aim for O(n + m).', [('4 4\n0 1\n1 2\n2 3\n0 3\n0 2\n','2'),('3 1\n0 1\n0 2\n','-1'),('1 0\n0 0\n','0'),('4 3\n0 1\n1 2\n2 3\n0 3\n','3'),('3 2\n0 1\n1 2\n2 0\n','2')]),
]}


def get_problems(language, difficulty):
    return [{**deepcopy(q), 'id': uid(), 'starter': STARTERS[language]} for q in BANK[difficulty]]
