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
			print(len(vocab))
	else:
		# Gracefully navigate partial setups, informing as best as possible
		try:
			import nltk
		except ImportError as e:
			print("You do not appear to have nltk installed for the 5-letter wordlist!")
			raise e
		try:
			words = nltk.corpus.words.words()
		except Exception as e:
			print("Try this: python -c 'import nltk; ntlk.download()', then navigate to corpus tab in the GUI and download the 'words' package (~5MB)")
			raise e
		vocab = [_.lower() for _ in words if len(_) == 5]
		with open(cache_target, 'w') as f:
			f.write("\n".join(vocab))
	return vocab

def score(word, presence_dict, position_pres_dict):
	value = 0
	for idx, letter in enumerate(word):
		value = value + presence_dict[letter] + position_pres_dict[idx][letter]
	return value

# Initial vocabulary scoring based on letter-presence frequency
def vocab_scoring(vocab, presence_weight=0, positional_weight=1):
	alphabet = dict((letter,0) for letter in [chr(ord('a')+_) for _ in range(26)])
	# Discriminator in order should be based on POSITION as well
	pos_alphabet = [dcpy(alphabet) for _ in range(5)]
	uniques = []
	for idx, word in enumerate(vocab):
		# Count letter presence
		wordset = set(word)
		for letter in wordset:
			alphabet[letter] = alphabet[letter]+1
		for idx, letter in enumerate(word):
			pos_alphabet[idx][letter] = pos_alphabet[idx][letter]+1
		if len(wordset) == len(word):
			uniques.append(word)
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
	# Score uniques
	unq2scr = dict((word, score(word, alphabet, pos_alphabet)) for word in uniques)
	# Change unq2scr into OrderedDict on descending score
	maxscore = max(unq2scr.values())
	has_max = [key for (key, value) in unq2scr.items() if value == maxscore]
	print(f"Max score is {maxscore}, held by {len(has_max)} words; exemplar: {has_max[0]} {has_max}")
	return alphabet, unq2scr, uniques

def main(args):
	vocab = load_vocab(args.cached, args.cache_target)
	vocab_scoring(vocab, args.presence_weight, args.position_weight)

def build():
	prs = argparse.ArgumentParser(description='Dynamic Wordle Solver')
	prs.add_argument('--no_cache', dest='cached', action='store_false', help='Do not use cached vocabulary')
	prs.add_argument('--cache_file', dest='cache_target', type=str, default='5lw.txt', help='Filepath to cached vocabulary')
	prs.add_argument('--presence_weight', '--presence', type=float, default=1, help='Weight assigned to letters APPEARING in a word')
	prs.add_argument('--position_weight', '--position', type=float, default=1, help='Weight assigned to order of letters that appear in a word')
	return prs

def parse(prs, args=None):
	args = prs.parse_args(args)
	return args

if __name__ == '__main__':
	args = parse(build())
	main(args)

