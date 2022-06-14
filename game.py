from random import randint, choice
from enum import Enum
from string import punctuation, whitespace
import re

WORDS = re.compile(f"[-{punctuation.replace('-', '')}{whitespace}]*[-'\\w]+(?:\\b|$)")
LAST_PONCTUATION = re.compile(f"\\b[-{punctuation.replace('-', '')}{whitespace}]*$(?:[\r\n]|\r\n)?")

class GameMode(Enum):
    WHOLE_SENTENCE: int = 0
    FIRST_WORDS: int = 1
    LAST_WORDS: int = 2
    RANDOM_WORDS: int = 3


class GameError(Enum):
    OK: int = 0

    ALREADY_STARTED: int = 1
    NOT_ENOUGH_PLAYERS: int = 2

    TOO_MUCH_CHARS: int = 3
    WRONG_PARTICIPENT: int = 4

    ALREADY_JOINED: int = 5
    NOT_STARTED: int = 6


def get_cut_sentence(sentence: str, pos: int = 0, count: int = 1) -> str:
    result: str = ""
    words: list[str] = decompose_words(sentence)
    
    if count >= 0:
        for i in range(pos, pos + count):
            if i >= len(words):
                break
            result += words[i]
    
        if pos + count - 1 >= len(words):
            for end in LAST_PONCTUATION.findall(sentence):
                result += end
    if count <= 0:
        for i in range(pos + count + 1, pos + 1):
            if i < 0:
                continue
            if i >= len(words):
                break
            result += words[i]

        if pos + 1 >= len(words):
            for end in LAST_PONCTUATION.findall(sentence):
                result += end
    
    return result


def decompose_words(sentence: str) -> list[str]:
    return WORDS.findall(sentence)


class ExquisiteCadaver:

    game_id: int
    participents: list

    mode: GameMode
    word_count: int
    character_limit: int

    current_turn: int = -1
    order_of_participents: list[int] = []

    tale: list = []
    given_info: str = ""


    def __init__(self, game_mode: GameMode, game_admin, word_count: int = 3, character_limit: int = 120):
        #get 64 bit game id
        self.game_id = randint(0, 0xffffffffffffffff)
        self.participents = []
        self.game_admin = game_admin

        self.mode = game_mode
        self.word_count = word_count
        self.character_limit = character_limit

        self.current_turn = -1
        self.order_of_participents = []
        self.tale = []
        self.given_info = ""


    def register_participent(self, participent) -> GameError:
        if self.has_joined(participent):
            return GameError.ALREADY_JOINED
        if self.started():
            return GameError.ALREADY_STARTED
        self.participents.append(participent)
        return GameError.OK


    def is_game(self, game_id: int) -> bool:
        return self.game_id == game_id


    def get_game_id(self) -> int:
        return self.game_id


    def started(self):
        return self.current_turn != -1


    def has_joined(self, player) -> bool:
        return player in self.participents


    def start_game(self) -> GameError:
        #ignore command if the game has been initiamized
        if self.started():
            return GameError.ALREADY_STARTED
        if len(self.participents) <= 1:
            return GameError.NOT_ENOUGH_PLAYERS
        indecies: list[int] = [i for i in range(len(self.participents))]
        

        while len(indecies) > 0:
            next_p: int = choice(indecies)
            self.order_of_participents.append(next_p)
            indecies.remove(next_p)

        self.current_turn = 0
        return GameError.OK


    def get_next_player(self):
        return self.participents[self.order_of_participents[self.current_turn % len(self.order_of_participents)]]
    

    def push_sentence(self, participent, sentence: str) -> (GameError, dict):
        if not self.started():
            return GameError.NOT_STARTED, {}
        if participent != self.get_next_player():
            return GameError.WRONG_PARTICIPENT, {}
        if len(sentence) > self.character_limit:
            return GameError.TOO_MUCH_CHARS, {"diff": len(sentence) - self.character_limit}
        
        self.tale += [sentence]
        self.current_turn += 1

        words: list[str] = decompose_words(sentence)

        if self.mode == GameMode.WHOLE_SENTENCE:
            self.given_info = sentence
        elif self.mode == GameMode.FIRST_WORDS:
            self.given_info = get_cut_sentence(sentence, count = self.word_count)
        elif self.mode == GameMode.LAST_WORDS:
            self.given_info = get_cut_sentence(sentence, pos = len(words)-1, count = -self.word_count)
        elif self.mode == GameMode.RANDOM_WORDS:
            self.given_info = get_cut_sentence(sentence, pos = randint(0, len(words) - self.word_count), count = self.word_count)

        return GameError.OK, {}
    

    def get_tale(self, char_limit: int = 1500):
        res: list = []
        curr: str = ""
        for t in self.tale:
            if len(curr) + len(t) > char_limit:
                res += [curr]
                curr = t
            else:
                curr += t
        res += [curr]
        return res


    def get_given_info(self) -> str:
        return self.given_info
