import os
from copy import deepcopy as dcpy
import argparse


"""
Strategy:
	Pick a random word that eliminates the most words from vocabulary whenever any bit of information is wrong
		Priority between finding presence of letters and leveraging letter positioning in the word can be adjusted
		Bias towards words with all unique letters can be adjusted to help cull the alphabet faster
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
			print("Try this: python -c 'import nltk; ntlk.download()', then download the 'words' package (~5MB, under the 'corpus' tab in the GUI version)")
			raise e
		vocab = sorted(set([_.lower() for _ in words if len(_) == 5]))
		with open(cache_target, 'w') as f:
			f.write("\n".join(vocab)+"\n")
	return vocab

# Determine if an unknown word should be 'learned' and cache it for future use
def add_to_vocab(vocab, new_word, cache_target):
	char = ''
	while char not in ['y', 'n']:
		print(f"Vocabulary does not know the word '{new_word}' and will be unable to guess it. Learn it? y/n: ", end='')
		char = input()
	if char == 'y':
		vocab.append(new_word)
		with open(cache_target, 'a') as f:
			f.write(new_word+"\n")
	return vocab

# Identify the value of guessing a word by how much information it encodes for the vocabulary
def score(word, presence_dict, position_pres_dict, unique_bias):
	value = 0
	# Vocabulary-based scores
	for idx, letter in enumerate(word):
		value = value + presence_dict[letter] + position_pres_dict[idx][letter]
	# Bias towards having all unique letters
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
		# Count letter presence wrt position
		for idx, letter in enumerate(word):
			pos_alphabet[idx][letter] = pos_alphabet[idx][letter]+1
	# Normalize so scores are loosely comparable between iterations
	norm_factor =  len(vocab) / presence_weight
	for letter in alphabet.keys():
		alphabet[letter] = alphabet[letter] / norm_factor
	norm_factor =  len(vocab) / positional_weight
	for idx in range(5):
		for letter in pos_alphabet[idx].keys():
			pos_alphabet[idx][letter] = pos_alphabet[idx][letter] / norm_factor
	# Score all words
	word2scr = dict((word, score(word, alphabet, pos_alphabet, unique_bias)) for word in vocab)
	return alphabet, pos_alphabet, word2scr

# Feedback encodes positions as:
# -1 = letter guessed more than it appears
#  0 = letter NOT in correct word at all
#  1 = letter in correct word, but not in that position
#  2 = letter in correct word at the given position
def get_feedback(guess, correct):
	# Default: assume letter not present at all
	reply = [0 for _ in range(5)]
	# Track per-letter counts in correct word
	total = dict((letter, correct.count(letter)) for letter in set(correct))
	# FIRST tell the player which letters are correct
	for idx, (expect, actual) in enumerate(zip(correct, guess)):
		if expect == actual:
			reply[idx] = 2
			total[expect] -= 1 # Mark as used
	# To correctly tell the player about mispositioned letters, we mark them based on the total count
	# available to be wrong (so they can see the same letter be misplaced multiple times)
	# and so they can see when they guessed too many copies of a letter that is in the word (just not
	# that often)
	for idx, actual in enumerate(guess):
		if reply[idx] != 0:
			continue
		if actual in total.keys():
			if total[actual] > 0:
				reply[idx] = 1
				total[actual] -= 1 # Mark as used
			else:
				# All occurrences of that word have been reported as correctly placed or mispositioned
				reply[idx] = -1
	return reply

# Make max-guess from scored dictionary
def make_guess(scoredict):
	maxscore = max(scoredict.values())
	candidates = [key for (key, value) in scoredict.items() if value == maxscore]
	return candidates[0]

# Use feedback to improve the vocabulary based on new possibilities
def improve_from_guess(guess, feedback, vocab, entropyWeight):
	entropy_score = 0
	# Remove words containing a letter we learned wasn't present
	invalid_letters = [ltr for idx, ltr in enumerate(guess) if feedback[idx] == 0]
	entropy_score += entropyWeight[0] * len(invalid_letters)
	for bad_letter in invalid_letters:
		vocab = [_ for _ in vocab if bad_letter not in _]

	# Remove words that don't have the correct letter in the correct spot
	correct_position = [(ltr,idx) for idx, ltr in enumerate(guess) if feedback[idx] == 2]
	for (correct_letter, correct_idx) in correct_position:
		vocab = [_ for _ in vocab if correct_letter in _ and _[correct_idx] == correct_letter]
	entropy_score += entropyWeight[2] * len(correct_position)

	# Remove words with a mispositioned letter and those that lack the letter since it should be somewhere
	almost_position = [ltr for idx, ltr in enumerate(guess) if feedback[idx] == 1]
	# See if you got the same letter multiple times and handle that complicated case
	if len(set(almost_position)) != len(almost_position):
		# Find repeated letters
		repeats = set([_ for _ in almost_position if almost_position.count(_) > 1])
		# Require words to have at least this count and 2nd+ occurrences to NOT be misplaced like this one
		for repeat_letter in repeats:
			vocab = [_ for _ in vocab if _.count(repeat_letter) >= almost_position.count(repeat_letter)]
			# Trim words with late mispositioned instances (follow-up will only consider first index)
			new_vocab = []
			# 2nd+ repeated indices to avoid
			bad_idx = set([idx for idx, ltr in enumerate(guess) if ltr == repeat_letter][1:])
			for word in vocab:
				# Grab second and later occurrence positions
				found_idx = set([idx for idx, ltr in enumerate(word) if idx == repeat_letter][1:])
				# When no intersection, these later occurrences may be OK
				if len(bad_idx.intersection(found_idx)) == 0:
					new_vocab.append(word)
			vocab = new_vocab
	# Easier case where letter is unique (or 1st) and you can use .index() to find and remove
	for almost_letter in almost_position:
		vocab = [_ for _ in vocab if almost_letter in _ and _.index(almost_letter) != guess.index(almost_letter)]
	entropy_score += entropyWeight[1] * len(almost_position)

	# If you get -1's, you should be able to remove words that over-use a letter
	overused_letter = [ltr for idx, ltr in enumerate(guess) if feedback[idx] == -1]
	# Create mapping letter -> exact occurrence count based on guess and feedback
	for overused in set(overused_letter):
		correct_count = guess.count(overused) - overused_letter.count(overused)
		vocab = [_ for _ in vocab if _.count(overused) == correct_count]
	entropy_score += entropyWeight[3] * len(overused_letter)
	return vocab, entropy_score

def main(args):
	vocab = load_vocab(args.cached, args.cache_target)
	# Anti-cheat check
	if args.solution not in vocab:
		vocab = add_to_vocab(vocab, args.solution, args.cache_target)
	entropy_max = args.cscore * 5 # Full entropy per letter
	print(f"Target word: {args.solution}")
	for attempt in range(1, 1+args.guess_limit):
		guess_vocab_size = len(vocab)
		if guess_vocab_size == 0:
			print(f"Vocabulary exhausted. Unable to guess another word")
			break
		# Score vocabulary and rank each word in it
		alphabet, pos_alphabet, word2scr = vocab_scoring(vocab, args.presence_weight, args.position_weight, args.unique_bias)
		# Make a guess based on scores
		guess = make_guess(word2scr)
		# Get wordle-style feedback
		feedback = get_feedback(guess, args.solution)
		# Improve vocabulary and log entropy for the guess
		vocab, entropy = improve_from_guess(guess, feedback, vocab, args.entropyWeight)
		print(f"{attempt}/{args.guess_limit} = {guess}: {entropy:2}/{entropy_max} [1/{guess_vocab_size}]")
		if guess == args.solution:
			break
	if guess != args.solution and guess_vocab_size > 0:
		print(f"OUT OF GUESSES. {len(vocab)} words remained")
		char = ''
		while char not in ['y', 'n']:
			print("Show remaining words? y/n: ", end='')
			char = input()
		if char == 'y':
			print(", ".join(vocab))
	elif guess == args.solution:
		print("SOLVED!")

def build():
	prs = argparse.ArgumentParser(description='Dynamic Wordle Solver')
	prs.add_argument('--guess_limit', '--guess', type=int, default=6,
					 help='Maximum number of allowed guesses (default 6)')
	prs.add_argument('--solution', '--word', type=str,
					 help='Correct word to guess (default guess)', default='guess')
	prs.add_argument('--presence_weight', '--presence', type=float, default=1,
					 help='Algorithmic weight assigned to letters APPEARING in a word (default 1)')
	prs.add_argument('--position_weight', '--position', type=float, default=1,
					 help='Algorithmic weight assigned to order of letters that appear in a word (default 1)')
	prs.add_argument('--unique_bias', '--unique', type=float, default=1,
					 help='Algorithmic biasing weight towards words that do not repeat any letters (default 1)')
	prs.add_argument('--not_present_score', '--np_score', dest='npscore', type=float, default=1,
					 help='Entropy score for guessing a letter not present in the solution (default: 1pts)')
	prs.add_argument('--present_score', '--p_score', dest='pscore', type=float, default=2,
					 help='Entropy score for guessing a letter present in the solution, but in the wrong space (default: 2pts)')
	prs.add_argument('--correct_score', '--c_score', dest='cscore', type=float, default=5,
					 help='Entropy score for guessing a letter correctly from the solution (default: 5pts)')
	prs.add_argument('--excess_score', '--e_score', dest='escore', type=float, default=1,
					 help='Entropy score for guessing too many of a letter from the solution (default: 1pts)')
	prs.add_argument('--no_cache', dest='cached', action='store_false',
					 help='Do not use cached vocabulary')
	prs.add_argument('--cache_file', dest='cache_target', type=str, default='5lw.txt',
					 help='Filepath to cached vocabulary (default 5lw.txt)')
	return prs

def parse(prs, args=None):
	args = prs.parse_args(args)
	args.entropyWeight = [args.npscore, args.pscore, args.cscore, args.escore]
	return args

if __name__ == '__main__':
	main(parse(build()))

