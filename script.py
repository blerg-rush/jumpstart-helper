import enum
import random
import json
import csv
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Self


class Colour(enum.Enum):
    WHITE = "W"
    BLUE = "U"
    BLACK = "B"
    RED = "R"
    GREEN = "G"

    def __str__(self):
        return self.value


class CreatureType(enum.Enum):
    BIRD = "Bird"
    RAT = "Rat"
    LIZARD = "Lizard"
    RACCOON = "Raccoon"
    RABBIT = "Rabbit"
    BAT = "Bat"
    OTTER = "Otter"
    SQUIRREL = "Squirrel"
    MOUSE = "Mouse"
    FROG = "Frog"

    def __str__(self):
        return self.value


class Playability(enum.Enum):
    UNPLAYABLE = "Unplayable"
    WEAK = "Weak"
    MEDIUM = "Medium"
    STRONG = "Strong"

    def __str__(self):
        return self.value


@dataclass(eq=True, frozen=True)
class Pack:
    name: str
    colours: set[Colour]
    creature_types: set[CreatureType]

    def __str__(self):
        return f"{''.join(self.colours)} {self.name}"

    def matching_types(self, pack_two: Self) -> set[CreatureType]:
        return {
            creature_type
            for creature_type in self.creature_types
            if creature_type in pack_two.creature_types
        }

    def synergistic_types(
        self, pack_two: Self, synergistic_type_pairs: set[frozenset[CreatureType]]
    ) -> set[frozenset[CreatureType]]:
        matches_with_pack_two = {
            type_pair
            for type_pair in synergistic_type_pairs
            if any(
                creature_type in type_pair for creature_type in pack_two.creature_types
            )
        }
        matches_with_both_packs = {
            type_pair
            for type_pair in matches_with_pack_two
            if any(creature_type in type_pair for creature_type in self.creature_types)
        }
        return matches_with_both_packs

    def matching_colours(self, pack_two: Self) -> set[Colour]:
        return {colour for colour in self.colours if colour in pack_two.colours}

    def pair_playability(
        self, pack_two: Self, synergistic_type_pairs: set[frozenset[CreatureType]]
    ) -> Playability:
        if self.matching_colours(pack_two):
            if self.matching_types(pack_two) or self.synergistic_types(
                pack_two, synergistic_type_pairs
            ):
                # e.g. WU Birds and W Lifecreed; GW Rabbits and RW Mice
                return Playability.STRONG
            else:
                if max(len(self.colours), len(pack_two.colours)) == 1:
                    # e.g., U Lightshell and U Skyskipper
                    return Playability.MEDIUM
                else:
                    # e.g. GR Raccoons and R Kindlespark or U Lightshell and U Skyskipper
                    return Playability.WEAK
        else:
            if self.matching_types(pack_two) or self.synergistic_types(
                pack_two, synergistic_type_pairs
            ):
                if max(len(self.colours), len(pack_two.colours)) == 1:
                    # e.g., R Roughshod and G Treeguard (Mouse and Rabbit are synergistic through W Brave-Kin)
                    return Playability.MEDIUM
                else:
                    # e.g., UG Frogs and W Lifecreed (Frog and Bird are synergistic through U Skyskipper)
                    return Playability.WEAK
            else:
                if max(len(self.colours), len(pack_two.colours)) == 1:
                    # e.g., B Daggerfang and G Treeguard (Rat and Squirrel have no synergistic links to Frog and Rabbit)
                    return Playability.WEAK
                else:
                    # three-colour deck with no synergistic links is just flat-out unplayable
                    return Playability.UNPLAYABLE

    def creature_type(self) -> CreatureType:
        if len(self.creature_types) == 1:
            return list(self.creature_types)[0]
        else:
            raise AttributeError("Pack does not have exactly one creature type")

    def colour(self) -> Colour:
        if len(self.colours) == 1:
            return list(self.colours)[0]
        else:
            raise AttributeError("Pack does not have exactly one creature type")


def get_packs() -> list[Pack]:
    with open("input/packs.json") as file:
        pack_dicts = json.load(file)
    return [Pack(**pack_data) for pack_data in pack_dicts]


PACKS: list[Pack] = get_packs()
STRONG_MATCHES: set[frozenset[str]] = set()
MEDIUM_MATCHES: set[frozenset[str]] = set()
WEAK_MATCHES: set[frozenset[str]] = set()
UNPLAYABLE_MATCHES: set[frozenset[str]] = set()
SYNERGISTIC_TYPE_PAIRS: set[frozenset[CreatureType]] = set()


def initialize() -> None:
    for pack in PACKS:
        if len(pack.creature_types) == 2 and len(pack.colours) == 1:
            SYNERGISTIC_TYPE_PAIRS.add(frozenset(pack.creature_types))
    for number, pack_one in enumerate(PACKS, start=1):
        if number > len(PACKS):
            break
        remaining_packs = PACKS[number:]
        for pack_two in remaining_packs:
            playability = pack_one.pair_playability(pack_two, SYNERGISTIC_TYPE_PAIRS)
            if playability == Playability.STRONG:
                STRONG_MATCHES.add(frozenset({str(pack_one), str(pack_two)}))
            if playability == Playability.MEDIUM:
                MEDIUM_MATCHES.add(frozenset({str(pack_one), str(pack_two)}))
            if playability == Playability.WEAK:
                WEAK_MATCHES.add(frozenset({str(pack_one), str(pack_two)}))
            if playability == Playability.UNPLAYABLE:
                UNPLAYABLE_MATCHES.add(frozenset({str(pack_one), str(pack_two)}))


def write_to_file() -> None:
    packs = get_packs()
    playability_matrix_fieldnames: list[str] = [""]
    playability_matrix_rows: list[list[str]] = []
    for pack in packs:
        playability_matrix_fieldnames.append(str(pack))
        if len(pack.creature_types) == 2 and len(pack.colours) == 1:
            SYNERGISTIC_TYPE_PAIRS.add(frozenset(pack.creature_types))
    for number, pack_one in enumerate(packs, start=1):
        if number > len(packs):
            break
        playability_matrix_row: list[str] = [str(pack_one)] + [
            "" for _ in range(number)
        ]
        remaining_packs = packs[number:]
        for pack_two in remaining_packs:
            playability = pack_one.pair_playability(pack_two, SYNERGISTIC_TYPE_PAIRS)
            playability_matrix_row.append(playability.value)
            if playability == Playability.STRONG:
                STRONG_MATCHES.add(frozenset({str(pack_one), str(pack_two)}))
            if playability == Playability.MEDIUM:
                MEDIUM_MATCHES.add(frozenset({str(pack_one), str(pack_two)}))
            if playability == Playability.WEAK:
                WEAK_MATCHES.add(frozenset({str(pack_one), str(pack_two)}))
            if playability == Playability.UNPLAYABLE:
                UNPLAYABLE_MATCHES.add(frozenset({str(pack_one), str(pack_two)}))
        playability_matrix_rows.append(playability_matrix_row)
    with open("output/playability_matrix.csv", "w") as playability_matrix_file:
        csv_writer = csv.writer(playability_matrix_file)
        csv_writer.writerow(playability_matrix_fieldnames)
        csv_writer.writerows(playability_matrix_rows)


@dataclass
class TotalResults:
    total_runs: int = 0
    strong_or_better: int = 0
    medium_or_better: int = 0
    weak_or_better: int = 0
    unplayable_or_better: int = 0

    def strong_or_better_chance(self):
        return self.strong / self.total_runs

    def medium_or_better_chance(self):
        return (self.strong + self.mediumn) / self.total_runs

    def weak_or_better_chance(self):
        return (self.strong + self.medium + self.weak) / self.total_runs


@dataclass
class DraftResult:
    strong: int = 0
    medium: int = 0
    weak: int = 0
    unplayable: int = 0


class DraftStrategy(ABC):
    def __init__(self):
        self.results = TotalResults()

    @abstractmethod
    def draft(self, packs: list[Pack]) -> list[Pack] | tuple[Pack, list[Pack]]:
        pass

    def get_draft_result(self, packs) -> DraftResult:
        drafted_packs = self.draft(packs)
        draft_result = DraftResult()
        if type(drafted_packs) is tuple:
            pack_one, remaining_packs = drafted_packs
            for pack_two in remaining_packs:
                pair = frozenset({str(pack_one), str(pack_two)})
                if pair in STRONG_MATCHES:
                    draft_result.strong += 1
                elif pair in MEDIUM_MATCHES:
                    draft_result.medium += 1
                elif pair in WEAK_MATCHES:
                    draft_result.weak += 1
                elif pair in UNPLAYABLE_MATCHES:
                    draft_result.unplayable += 1
        elif type(drafted_packs) is list:
            for number, pack_one in enumerate(drafted_packs, start=1):
                if number == len(drafted_packs):
                    break
                remaining_packs = drafted_packs[number:]
                for pack_two in remaining_packs:
                    pair = frozenset({str(pack_one), str(pack_two)})
                    if pair in STRONG_MATCHES:
                        draft_result.strong += 1
                    elif pair in MEDIUM_MATCHES:
                        draft_result.medium += 1
                    elif pair in WEAK_MATCHES:
                        draft_result.weak += 1
                    elif pair in UNPLAYABLE_MATCHES:
                        draft_result.unplayable += 1
        return draft_result

    def test(self, packs) -> TotalResults:
        for _ in range(100000):
            draft_result = self.get_draft_result(packs)
            self.results.total_runs += 1
            if draft_result.strong:
                self.results.strong_or_better += 1
            if draft_result.strong or draft_result.medium:
                self.results.medium_or_better += 1
            if draft_result.strong or draft_result.medium or draft_result.weak:
                self.results.weak_or_better += 1
            if (
                draft_result.strong
                or draft_result.medium
                or draft_result.weak
                or draft_result.unplayable
            ):
                self.results.unplayable_or_better += 1
        return self.results


class DrawThreeStrategy(DraftStrategy):
    def draft(self, packs: list[Pack]):
        return random.sample(packs, 3)


class DrawFourStrategy(DraftStrategy):
    def draft(self, packs: list[Pack]):
        return random.sample(packs, 4)


class DrawFiveStrategy(DraftStrategy):
    def draft(self, packs: list[Pack]):
        return random.sample(packs, 5)


class DrawSixStrategy(DraftStrategy):
    def draft(self, packs: list[Pack]):
        return random.sample(packs, 6)


class DrawThreeTwiceStrategy(DraftStrategy):
    """
    Mathematically speaking this is roughly the same as DrawFour, but there's an opportunity for slightly improving a player's success by
    """

    def draft(self, packs: list[Pack]) -> tuple[Pack, list[Pack]]:
        first_three = random.sample(packs, 3)
        rest = [pack for pack in packs if pack not in first_three]
        first_pick = random.choice(first_three)
        second_three = random.sample(rest, 3)
        return (first_pick, second_three)


if __name__ == "__main__":
    initialize()
    print(f"Draw Three results: {DrawThreeStrategy().test(PACKS)}")
    print(f"Draw Four results: {DrawFourStrategy().test(PACKS)}")
    print(f"Draw Five results: {DrawFiveStrategy().test(PACKS)}")
    print(f"Draw Six results: {DrawSixStrategy().test(PACKS)}")
    print(f"Draw Three Twice results: {DrawThreeTwiceStrategy().test(PACKS)}")
