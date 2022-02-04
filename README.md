# wordlePuzzles

Quick Python project to mess around with deterministically solving word puzzles.
The code is *designed by intent* to **NOT** solve puzzles which you do not know the solution to, though you can certainly play with it to learn good starting words and strategies.

Dependencies:

* Tested on Python 3.8, should be compatible with most Python 3.x
* NLTK and its corpus->words list; the script can help you get this set up.
  + If you have your own words list, you can circumvent this requirement. Word lists should be newline-delimited and have consistent length (5-letters/word)

Demo:

```
$ python3 wordle.py;
1/6 = tarie: 6 [1/10422]
2/6 = belee: 8 [1/643]
3/6 = nosed: 7 [1/177]
4/6 = speck: 10 [1/17]
5/6 = guess: 25 [1/1]
SOLVED!
```

The format in the output is `attempt`/`limit` = `<guessed word>`: `<entropy score>` [1/`<vocabulary size>`]

Entropy scores represent "bits" of information gained by the guess, but are not used as part of scoring the next guess.

For further information on options available, see `python3 wordle.py --help;`
