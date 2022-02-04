# wordlePuzzles

Quick Python project to mess around with deterministically solving wordle puzzles.
The code is *designed by intent* to **ONLY** solve puzzles where you can provide the actual answer (ie: not wordle of the day that you have not solved yet), though you can certainly play with the code to learn good starting words and strategies. The code does not "cheat" and only consults the correct answer to give the algorithm feedback on its guesses.

Dependencies:

* Tested on Python 3.8, should be compatible with most Python 3.x
* NLTK and its corpus->words list; the script can help you get this set up.
  + If you have your own words list, you can circumvent this requirement. Word lists should be newline-delimited and have consistent length (5-letters/word)

Demo:

```
$ python3 wordle.py;
Target word: guess
1/6 = tarie:  6/25 [1/10422]
2/6 = belee:  6/25 [1/643]
3/6 = nosey:  7/25 [1/119]
4/6 = specs: 14/25 [1/7]
5/6 = guess: 25/25 [1/1]
SOLVED!
```

The format in the output is `attempt`/`limit` = `<guessed word>`: `<entropy score>`/`<max entropy>` [1/`<vocabulary size>`]

Entropy scores represent "bits" of information gained by the guess, but are not used as part of scoring the next guess.

For further information on options available, see `python3 wordle.py --help;`
