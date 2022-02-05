import argparse
import os


def build():
	prs = argparse.ArgumentParser()
	prs.add_argument('--ban-list', '--ban', type=str, default='ban_words.txt', help='Newline-delimited list of disallowed words (default "ban_words.txt")')
	prs.add_argument('--inspect', type=str, nargs='*', default=[], help='List of files to CHECK for validity')
	prs.add_argument('--fix', type=str, nargs='*', default=[], help='List of files to ENFORCE validity by removing banned words')
	prs.add_argument('--yes', action='store_true', help='Automatically answer y/n with YES')
	prs.add_argument('--no', action='store_true', help='Automatically answer y/n with NO')
	return prs

def parse(prs, args=None):
	if args is None:
		args = prs.parse_args()
	if not os.path.exists(args.ban_list):
		No_Ban_List = f"Ban list expected at '{args.ban_list}', file not found!"
		raise ValueError(No_Ban_List)
	for fname in args.inspect+args.fix:
		if not os.path.exists(fname):
			Input_Not_Found = f"Input file '{fname}' not found!"
			raise ValueError(Input_Not_Found)
	if args.yes and args.no:
		Contradiction = 'Cannot perform automatic YES and automatic NO simultaneously'
		raise ValueError(Contradiction)
	return args

def inspect(data, banned):
	if type(data) is not list:
		with open(data, 'r') as f:
			words = [_.rstrip() for _ in f.readlines() if len(_.rstrip()) > 0]
	else:
		words = data
	ok = True
	banned_instances = []
	for idx, word in enumerate(words):
		if word in banned:
			ok = False
			banned_instances.append(idx)
	return ok, banned_instances

def fix(fname, banned):
	with open(fname, 'r') as f:
		words = [_.rstrip() for _ in f.readlines() if len(_.rstrip()) > 0]
	ok, violations = inspect(words, banned)
	if not ok:
		preserved = [_ for idx, _ in enumerate(words) if idx not in violations]
		with open(fname, 'w') as f:
			f.write("\n".join(preserved)+"\n")

def main(args):
	with open(args.ban_list, 'r') as f:
		bans = [_.rstrip() for _ in f.readlines() if len(_.rstrip()) > 0]
	for fname in args.inspect:
		ok, bad_lines = inspect(fname, bans)
		if ok:
			print(f"File '{fname}' passes inspection")
		else:
			print(f"File '{fname}' FAILS inspection with {len(bad_lines)} violations")
			if not args.no:
				if not args.yes:
					check = ''
					while check not in ['n', 'y']:
						print("View violating words? y/n: ", end='')
						check = input()
				if args.yes or check == 'y':
					with open(fname, 'r') as f:
						words = [_.rstrip() for _ in f.readlines() if len(_.rstrip()) > 0]
					print("\n".join([words[linenum] for linenum in bad_lines]))
	for fname in args.fix:
		fix(fname, bans)

if __name__ == '__main__':
	main(parse(build()))
