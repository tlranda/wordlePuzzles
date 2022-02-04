import os
from copy import deepcopy as dcpy
import argparse


"""
Strategy
	Pick a random word that has 5 unique letters that have not been guessed
		Pick should go in priority order based on overlap with other letters
	Once a yellow is identified, should kill all words that don't satisfy the yellow (lack the letter OR have the letter in that spot)
	Once a green is identified, kill everything that lacks the letter in that spot
"""


# Gather valid words for the puzzle (cache-able)
def load_vocab(cached=True, cache_target='5lw.txt'):
	# Prefer cached list
	if cached and os.path.exists(cache_target):
		with open(cache_target, 'r') as words:
			vocab = [_.rstrip() for _ in words.readlines()]
	else:
		# Gracefully navigate partial setups, informing as best as possible
		try:
			import nltk
		except ImportError as e:
			print("You do not appear to have nltk installed for the 5-letter wordlist!")
			print("You may supply your own via --cache_target or install the nltk module via:")
			print("$ pip install nltk;")
			raise e
		try:
			words = nltk.corpus.words.words()
		except Exception as e:
			print("Try this: python -c 'import nltk; ntlk.download()', then navigate to corpus tab in the GUI and download the 'words' package (~5MB)")
			raise e
		vocab = [_.lower() for _ in words if len(_) == 5]
		with open(cache_target, 'w') as f:
			f.write("\n".join(vocab)+"\n")
	return vocab

def add_to_vocab(vocab, new_word, cache_target):
	char = ''
	while char not in ['y', 'n']:
		print(f"Vocabulary does not know the word '{args.solution}' and will be unable to guess it. Learn it? y/n: ")
		char = input()
	if char == 'y':
		vocab.append(new_word)
		with open(cache_target, 'a') as f:
			f.write(new_word+"\n")
	return vocab

def score(word, presence_dict, position_pres_dict, unique_bias):
	value = 0
	for idx, letter in enumerate(word):
		value = value + presence_dict[letter] + position_pres_dict[idx][letter]
	# Bias towards having unique letters
	if len(set(word)) == len(word):
		value = value + unique_bias
	return value

# Initial vocabulary scoring based on letter-presence frequency
def vocab_scoring(vocab, presence_weight=0, positional_weight=1, unique_bias=1):
	alphabet = dict((letter,0) for letter in [chr(ord('a')+_) for _ in range(26)])
	# Discriminator in order should be based on POSITION as well
	pos_alphabet = [dcpy(alphabet) for _ in range(5)]
	for idx, word in enumerate(vocab):
		# Count letter presence
		wordset = set(word)
		for letter in wordset:
			alphabet[letter] = alphabet[letter]+1
		for idx, letter in enumerate(word):
			pos_alphabet[idx][letter] = pos_alphabet[idx][letter]+1
	# Normalize
	norm_factor = presence_weight * len(vocab)
	if norm_factor != 0:
		for letter in alphabet.keys():
			alphabet[letter] = alphabet[letter] / norm_factor
	else:
		for letter in alphabet.keys():
			alphabet[letter] = 0
	norm_factor = positional_weight * len(vocab)
	if norm_factor != 0:
	  for idx in range(5):
		  for letter in pos_alphabet[idx].keys():
			  pos_alphabet[idx][letter] = pos_alphabet[idx][letter] / norm_factor
	else:
	  for idx in range(5):
		  for letter in pos_alphabet[idx].keys():
			  pos_alphabet[idx][letter] = 0
	# Score all words
	word2scr = dict((word, score(word, alphabet, pos_alphabet, unique_bias)) for word in vocab)
	return alphabet, pos_alphabet, word2scr

def make_guess(scoredict, vocab, correct, scoreWeight):
	# Make max-guess
	maxscore = max(scoredict.values())
	candidates = [key for (key, value) in scoredict.items() if value == maxscore]
	guess = candidates[0]
	guess_score = 0
	# Learn from guess
	# Remove words containing a letter we learned wasn't present
	invalid_letters = [_ for _ in guess if _ not in correct]
	guess_score += scoreWeight[0] * len(invalid_letters)
	for bad_letter in invalid_letters:
		vocab = [_ for _ in vocab if bad_letter not in _]
	# Remove words with a mispositioned letter and those that lack the letter since it should be somewhere
	almost_position = [_ for _ in guess if _ in correct and correct.index(_) != guess.index(_)]
	for almost_letter in almost_position:
		vocab = [_ for _ in vocab if almost_letter in _ and _.index(almost_letter) != guess.index(almost_letter)]
	guess_score += scoreWeight[1] * len(almost_position)
	# Remove words that don't have the correct letter in the correct spot
	correct_position = [_ for _ in guess if _ in correct and correct.index(_) == guess.index(_)]
	for correct_letter in correct_position:
		vocab = [_ for _ in vocab if correct_letter in _ and _.index(correct_letter) == guess.index(correct_letter)]
	guess_score += scoreWeight[2] * len(correct_position)
	return vocab, guess, guess_score

def main(args):
	vocab = load_vocab(args.cached, args.cache_target)
	# Anti-cheat check
	if args.solution not in vocab:
		vocab = add_to_vocab(vocab, args.solution, args.cache_target)
	vocab_size = []
	history = []
	guess_score = []
	entropy_max = args.cscore * 5
	for attempt in range(1, 1+args.guess_limit):
		vocab_size.append(len(vocab))
		alphabet, pos_alphabet, word2scr = vocab_scoring(vocab, args.presence_weight, args.position_weight, args.unique_bias)
		vocab, guess, score = make_guess(word2scr, vocab, args.solution, args.scoreWeight)
		history.append(guess)
		guess_score.append(score)
		print(f"{attempt}/{args.guess_limit} = {guess}: {score:2}/{entropy_max} [1/{vocab_size[-1]}]")
		if guess == args.solution:
			break
	if guess != args.solution:
		print(f"OUT OF GUESSES. {len(vocab)} words remained")
		char = ''
		while char not in ['y', 'n']:
			print("Show remaining words? y/n: ")
			char = input()
		if char == 'y':
			print(", ".join(vocab))
	else:
		print("SOLVED!")

def build():
	prs = argparse.ArgumentParser(description='Dynamic Wordle Solver')
	prs.add_argument('--no_cache', dest='cached', action='store_false', help='Do not use cached vocabulary')
	prs.add_argument('--cache_file', dest='cache_target', type=str, default='5lw.txt', help='Filepath to cached vocabulary (default 5lw.txt)')
	prs.add_argument('--presence_weight', '--presence', type=float, default=1, help='Weight assigned to letters APPEARING in a word (default 1)')
	prs.add_argument('--position_weight', '--position', type=float, default=1, help='Weight assigned to order of letters that appear in a word (default 1)')
	prs.add_argument('--unique_bias', '--unique', type=float, default=1, help='Bias weight towards words that have all unique letters (default 1)')
	prs.add_argument('--guess_limit', '--guess', type=int, default=6, help='Maximum number of allowed guesses (default 6)')
	prs.add_argument('--solution', '--word', type=str, help='Correct word to guess (default guess)', default='guess')
	prs.add_argument('--not_present_score' '--np_score', dest='npscore', type=float, default=1, help='Entropy score for guessing a letter not present in the solution (default: 1pts)')
	prs.add_argument('--present_score' '--p_score', dest='pscore', type=float, default=2, help='Entropy score for guessing a letter present in the solution, but in the wrong space (default: 2pts)')
	prs.add_argument('--correct_score' '--c_score', dest='cscore', type=float, default=5, help='Entropy score for guessing a letter correctly from the solution (default: 5pts)')
	return prs

def parse(prs, args=None):
	args = prs.parse_args(args)
	args.scoreWeight = [args.npscore, args.pscore, args.cscore]
	return args

if __name__ == '__main__':
	main(parse(build()))

