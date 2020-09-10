from collections import Counter, namedtuple

MSA = namedtuple('MSA', 'index state principals pop')


def process_data():
    with open('msa.txt') as fp:
        for line in fp:
            idx, msa, pop_str, *_ = line.strip().split('\t')
            assert msa.endswith(' MSA')
            msa = msa[:-4]
            msa, state = msa.rsplit(', ', 1)
            msa = msa.split('-')
            pop = int(pop_str.replace(',', ''))
            idx = int(idx)
            yield MSA(idx, state, msa, pop)


class Tracker:
    """Object tracking data and answers for MSA Madness.

    >>> test_msas = []
    >>> t = Tracker([MSA(index=1, principals=['New York', 'Newark'],
    ...                   state='NY-NJ', pop=40),
    ...               MSA(index=2, principals=['Boston'], state='MA', pop=39),
    ...               MSA(index=3, principals=['Albany'], state='NY', pop=38),
    ...             ], cutoff=4)
    >>> t.status()
    STATUS: 0/3
    """

    def __init__(self, data, cutoff):
        self._data = list(data)
        self._results = {num: None for num in range(1, cutoff + 1)}
        self.cutoff = cutoff

    @property
    def maximum(self):
        return min(self.cutoff, len(self._data))

    @property
    def data(self):
        return self._data

    @property
    def players(self):
        return set(x.upper() for x in self._results.values() if x is not None)

    @property
    def answered_count(self):
        return sum(1 for x in self._results.values() if x is not None)

    def status(self):
        print(f'STATUS: {self.answered_count}/{self.maximum}')
        for player in self.players:
            score = sum(k for k, v in self._results.items() if v == player)
            print('{:>8}: {}'.format(player.upper(), score))

    def input(self, player, entry):
        self._results[entry[0]] = player.upper()

    def report(self):
        with open('report.txt', 'w') as f:
            for k, v in self._results.items():
                if v is not None:
                    f.write("{} {}\n".format(k, v))
        print('REPORT WRITTEN')

    def import_from_file(self):
        with open('report.txt') as f:
            for line in f:
                idx, player = line.split()
                self._results[int(idx)] = player

    def __getitem__(self, idx):
        return self._results[idx]

    def __contains__(self, idx):
        return idx in self._results


def get_index(guess, tracker):
    for entry in tracker.data:
        idx, state, msa, *_ = entry
        if idx in tracker and tracker[idx] is not None:
            continue
        if guess.lower() in (x.lower() for x in msa):
            break
    else:
        raise IndexError
    return entry


def post_answers(tracker):
    for k in sorted(tracker._results):
        if tracker[k] is not None:
            idx, state, msa, *_ = tracker.data[k -1]
            print(str(idx) + ' ' + '-'.join(msa) + ' ' + state)


def print_pops(tracker):
    for entry in tracker.data:
        if entry.index > tracker.cutoff:
            continue
        if tracker[entry.index] is None:
            print(f'{entry.index:3}|{entry.state:^11}|{entry.pop:,}')


def print_unanswered(tracker):
    """
    for entry in data:
        idx, state, msa, *_ = entry
        if idx > CUTOFF:
            continue
        if tracker[idx] is None:
            print(idx, state, msa)
    """


def print_state_info(tracker):
    states = Counter(entry.state.split('-')[0] for entry in tracker.data
                     if entry.index < tracker.cutoff
                     and tracker[entry.index] is None)
    for state, count in states.most_common():
        print(state, count)


def main():
    tracker = Tracker(process_data(), 110)
    while True:
        print('GUESS?')
        guess = input()
        if guess.upper() == 'REPORT':
            tracker.report()
        elif guess.upper() == 'IMPORT':
            tracker.import_from_file()
        elif guess.upper() == 'ANSWER':
            post_answers(tracker)
        elif guess.upper() == 'POP':
            print_pops(tracker)
        elif guess.upper() == 'STATES':
            print_state_info(tracker)
        elif guess.upper() == 'SCORE':
            tracker.status()
        else:
            try:
                entry = get_index(guess, tracker)
                print(f'#{entry.index} - {"-".join(entry.principals)}, '
                      f'{entry.state} ({entry.pop:,})')
                if entry[0] < 111:
                    player = input('PLAYER? ')
                    tracker.input(player, entry)
                    tracker.status()
                    #tracker.report()
            except IndexError:
                print('NOT IN TOP 384')
            print()
            tracker.status()

if __name__ == "__main__":
    main()
