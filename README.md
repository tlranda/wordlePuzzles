# wordlePuzzles

Quick Python project to mess around with deterministically solving wordle puzzles.
The code is *designed by intent* to **ONLY** solve puzzles where you can provide the actual answer (ie: not wordle of the day that you have not solved yet), though you can certainly play with the code to learn good starting words and strategies. The code does not "cheat" and only consults the correct answer to give the algorithm feedback on its guesses.

## Dependencies:

* Tested on Python 3.8, should be compatible with most Python 3.x
* NLTK and its corpus->words list; the script can help you get this set up.
  + If you have your own words list, you can circumvent this requirement. Word lists should be newline-delimited and have consistent length (5-letters/word)

## Demo:

```
$ python3 wordle.py;
Target word: guess
1/6 = raise: 10/25 [1/9968]
2/6 = neese: 13/25 [1/45]
3/6 = blest: 13/25 [1/12]
4/6 = chess: 17/25 [1/3]
5/6 = guess: 25/25 [1/1]
SOLVED!
```

The format in the output is `attempt`/`limit` = `<guessed word>`: `<entropy score>`/`<max entropy>` [1/`<vocabulary size>`]

Entropy scores represent "bits" of information gained by the guess, but are not used as part of scoring the next guess.

For further information on options available, see `python3 wordle.py --help;`

## Fixing Word List Dictionaries

Some words in the NLTK dictionary end up being unacceptable input for wordle. In lieu of knowing these in advance, I'm building a static dictionary of banned words in 'ban\_words.txt'. You can use the Python script `validate_wordlist.py` to see if your wordlist contains any known banned words, and the same script can remove these words from the list for you. Use `python3 validate_wordlist.py --help` to see full options.

