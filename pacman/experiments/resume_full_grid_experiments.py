import csv
import re
import statistics
import subprocess
import sys
import time
from itertools import product


# ============================================================
# SETTINGS
# ============================================================

GAMES_PER_CONFIGURATION = 50
GAME_TIMEOUT_SECONDS = 25

LAYOUTS = [
    "smallClassic",
    "mediumClassic",
    "openClassic",
    "trickyClassic",
    "minimaxClassic",
    "capsuleClassic",
]

CLASSIC_DEPTHS = [1, 2, 3]

MCTS_SIMULATIONS = [10, 20, 40]

MCTS_ROLLOUT_DEPTHS = [4, 6, 8]


# NOVI CSV - stari se neće dirati
OUTPUT_FILE = "full_grid_results_part2.csv"


# Poslednja konfiguracija koja je USPEŠNO završena
RESUME_AFTER_LAYOUT = "mediumClassic"
RESUME_AFTER_CONFIGURATION = "Hybrid_s40_r4"


# ============================================================
# CREATE CONFIGURATIONS
# ============================================================

def build_configurations():
    configs = []

    # Minimax
    for depth in CLASSIC_DEPTHS:
        configs.append({
            "configuration": f"Minimax_d{depth}",
            "agent": "MinimaxAgent",
            "depth": depth,
            "simulations": None,
            "rollout_depth": None,
            "args": f"depth={depth}"
        })

    # Alpha-Beta
    for depth in CLASSIC_DEPTHS:
        configs.append({
            "configuration": f"AlphaBeta_d{depth}",
            "agent": "AlphaBetaAgent",
            "depth": depth,
            "simulations": None,
            "rollout_depth": None,
            "args": f"depth={depth}"
        })

    # Expectimax
    for depth in CLASSIC_DEPTHS:
        configs.append({
            "configuration": f"Expectimax_d{depth}",
            "agent": "ExpectimaxAgent",
            "depth": depth,
            "simulations": None,
            "rollout_depth": None,
            "args": f"depth={depth}"
        })

    # MCTS
    for simulations, rollout_depth in product(
        MCTS_SIMULATIONS,
        MCTS_ROLLOUT_DEPTHS
    ):
        configs.append({
            "configuration":
                f"MCTS_s{simulations}_r{rollout_depth}",

            "agent":
                "MCTSAgent",

            "depth":
                None,

            "simulations":
                simulations,

            "rollout_depth":
                rollout_depth,

            "args":
                f"simulations={simulations},"
                f"rolloutDepth={rollout_depth}"
        })

    # HybridMCTS
    for simulations, rollout_depth in product(
        MCTS_SIMULATIONS,
        MCTS_ROLLOUT_DEPTHS
    ):
        configs.append({
            "configuration":
                f"Hybrid_s{simulations}_r{rollout_depth}",

            "agent":
                "HybridMCTSAgent",

            "depth":
                None,

            "simulations":
                simulations,

            "rollout_depth":
                rollout_depth,

            "args":
                f"simulations={simulations},"
                f"rolloutDepth={rollout_depth}"
        })

    return configs


# ============================================================
# PARSING
# ============================================================

def parse_scores(output):
    """
    Parsira listu rezultata kada pacman.py ispiše:
        Scores: 123, 456, ...
    """
    match = re.search(
        r"Scores:\s*(.*)",
        output,
        flags=re.IGNORECASE
    )

    if not match:
        return []

    scores = []

    for value in match.group(1).split(","):
        number = re.search(
            r"-?\d+(?:\.\d+)?",
            value
        )

        if number:
            scores.append(
                float(number.group(0))
            )

    return scores


def parse_average_score(output):
    """
    Fallback za varijante koje ispisuju samo:
        Average Score: 123.0
    """
    match = re.search(
        r"Average\s+Score:\s*(-?\d+(?:\.\d+)?)",
        output,
        flags=re.IGNORECASE
    )

    if match:
        return float(match.group(1))

    return None


def parse_single_score(output):
    """
    Za jednu igru mnoge verzije Pacman-a ne ispisuju 'Scores:',
    već završnu poruku tipa:
        Pacman emerges victorious! Score: 123
        Pacman died! Score: -456

    Uzimamo POSLEDNJI 'Score:' u outputu da izbegnemo eventualne
    debug poruke koje su se pojavile ranije.
    """
    matches = re.findall(
        r"(?<!Average\s)\bScore:\s*(-?\d+(?:\.\d+)?)",
        output,
        flags=re.IGNORECASE
    )

    if matches:
        return float(matches[-1])

    return None


def parse_win_rate(output):
    match = re.search(
        r"Win\s+Rate:\s*(\d+)/(\d+)\s*\(([\d.]+)\)",
        output,
        flags=re.IGNORECASE
    )

    if not match:
        return None, None

    wins = int(match.group(1))
    games = int(match.group(2))

    win_rate = 100.0 * wins / games

    return wins, win_rate


def parse_single_game_result(output):
    """
    Vraća:
        (score, won)

    score -> float ili None
    won   -> True / False / None
    """

    # 1) Najpre pokušaj standardni "Scores:" format.
    scores = parse_scores(output)

    if scores:
        score = scores[0]
    else:
        # 2) Zatim završni "Score:" jedne igre.
        score = parse_single_score(output)

        # 3) Poslednji fallback: "Average Score:" za -n 1.
        if score is None:
            score = parse_average_score(output)

    # Pobeda preko standardnog Win Rate reda.
    parsed_wins, _ = parse_win_rate(output)

    if parsed_wins is not None:
        won = parsed_wins > 0

    # Fallback na završnu Pacman poruku.
    elif re.search(
        r"Pacman\s+emerges\s+victorious",
        output,
        flags=re.IGNORECASE
    ):
        won = True

    elif re.search(
        r"Pacman\s+died",
        output,
        flags=re.IGNORECASE
    ):
        won = False

    # Dodatni fallback ako implementacija koristi Record: Win/Loss.
    else:
        record_match = re.search(
            r"Record:\s*(Win|Loss)",
            output,
            flags=re.IGNORECASE
        )

        if record_match:
            won = (
                record_match.group(1).lower()
                == "win"
            )
        else:
            won = None

    return score, won


# ============================================================
# STATISTICS
# ============================================================

def calculate_statistics(scores):
    if not scores:
        return {
            "median_score": None,
            "std_score": None,
            "min_score": None,
            "max_score": None
        }

    return {
        "median_score":
            statistics.median(scores),

        "std_score":
            statistics.stdev(scores)
            if len(scores) > 1 else 0.0,

        "min_score":
            min(scores),

        "max_score":
            max(scores)
    }


# ============================================================
# RUN CONFIGURATION
# ============================================================

def run_configuration(layout, config):
    print()
    print("=" * 90)

    print(
        f"Layout = {layout} | "
        f"Configuration = {config['configuration']} | "
        f"Games = {GAMES_PER_CONFIGURATION} | "
        f"Timeout/game = {GAME_TIMEOUT_SECONDS}s"
    )

    print("=" * 90)

    scores = []
    wins = 0
    known_outcomes = 0
    completed_games = 0
    timed_out_games = 0
    error_games = 0
    error_messages = []

    configuration_start_time = time.time()

    # Važno:
    # Svaka igra se pokreće kao poseban proces (-n 1), jer samo tako
    # možemo imati timeout od 25 sekundi PO IGRI.
    for game_number in range(1, GAMES_PER_CONFIGURATION + 1):

        command = [
            sys.executable,
            "pacman.py",

            "-p",
            config["agent"],

            "-l",
            layout,

            "-n",
            "1",

            "-q"
        ]

        if config["args"]:
            command.extend([
                "-a",
                config["args"]
            ])

        print(
            f"Game {game_number}/{GAMES_PER_CONFIGURATION} ... ",
            end="",
            flush=True
        )

        game_start_time = time.time()

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=GAME_TIMEOUT_SECONDS
            )

        except subprocess.TimeoutExpired:
            timed_out_games += 1

            print(
                f"TIMEOUT (> {GAME_TIMEOUT_SECONDS}s) -> skipped"
            )

            # Ova igra se preskače, a petlja automatski ide na sledeću.
            continue

        game_time = time.time() - game_start_time

        if process.returncode != 0:
            error_games += 1

            error_text = process.stderr.strip()

            if not error_text:
                error_text = (
                    f"Game {game_number} exited with "
                    f"return code {process.returncode}"
                )

            error_messages.append(
                f"Game {game_number}: {error_text}"
            )

            print("ERROR -> skipped")
            continue

        # Kombinujemo stdout i stderr jer neke verzije/projekti
        # mogu deo informacija ispisivati na stderr.
        output = (
            (process.stdout or "")
            + "\n"
            + (process.stderr or "")
        )

        game_score, game_won = parse_single_game_result(
            output
        )

        if game_score is None:
            error_games += 1

            error_messages.append(
                f"Game {game_number}: score could not be parsed."
            )

            print("PARSE ERROR -> skipped")

            # Da se problem odmah može videti, za prve 3 parse greške
            # ispisujemo sirovi Pacman output.
            if error_games <= 3:
                print("--- pacman.py output ---")
                print(
                    output.strip()
                    if output.strip()
                    else "[NO OUTPUT]"
                )
                print("------------------------")

            continue

        scores.append(game_score)

        if game_won is not None:
            known_outcomes += 1

            if game_won is True:
                wins += 1

        completed_games += 1

        if game_won is True:
            outcome = "WIN"
        elif game_won is False:
            outcome = "LOSS"
        else:
            outcome = "UNKNOWN"

        print(
            f"OK | score={game_score} | "
            f"{outcome} | "
            f"time={game_time:.2f}s"
        )

    total_time = time.time() - configuration_start_time

    stats = calculate_statistics(scores)

    if completed_games > 0:
        average_score = statistics.mean(scores)
    else:
        average_score = None

    if known_outcomes > 0:
        win_rate = 100.0 * wins / known_outcomes
    else:
        win_rate = None

    # Prosečno realno vreme po pokušanoj igri.
    average_time = (
        total_time / GAMES_PER_CONFIGURATION
        if GAMES_PER_CONFIGURATION > 0
        else None
    )

    if completed_games == 0:
        status = "FAILED"
    elif timed_out_games > 0 or error_games > 0:
        status = "PARTIAL"
    else:
        status = "OK"

    error_summary_parts = []

    if timed_out_games:
        error_summary_parts.append(
            f"{timed_out_games} game(s) timed out "
            f"after {GAME_TIMEOUT_SECONDS}s"
        )

    if error_games:
        error_summary_parts.append(
            f"{error_games} game(s) failed"
        )

    if error_messages:
        error_summary_parts.extend(error_messages)

    result = {
        "layout":
            layout,

        "configuration":
            config["configuration"],

        "agent":
            config["agent"],

        "depth":
            config["depth"],

        "simulations":
            config["simulations"],

        "rollout_depth":
            config["rollout_depth"],

        # Zadržano radi kompatibilnosti sa starim CSV-om:
        # broj igara koje smo pokušali da pokrenemo.
        "games":
            GAMES_PER_CONFIGURATION,

        "average_score":
            average_score,

        "median_score":
            stats["median_score"],

        "std_score":
            stats["std_score"],

        "min_score":
            stats["min_score"],

        "max_score":
            stats["max_score"],

        "wins":
            wins,

        "win_rate":
            win_rate,

        "total_time":
            total_time,

        "average_time":
            average_time,

        "status":
            status,

        "error":
            " | ".join(error_summary_parts)
    }

    print()
    print(
        f"Completed: {completed_games}/"
        f"{GAMES_PER_CONFIGURATION}"
    )

    print(
        f"Timed out: {timed_out_games}"
    )

    print(
        f"Errors: {error_games}"
    )

    print(
        f"Known win/loss outcomes: "
        f"{known_outcomes}/{completed_games}"
    )

    print(
        f"Average score: {average_score}"
    )

    if win_rate is None:
        print("Win rate: N/A")
    else:
        print(
            f"Win rate: {win_rate:.2f}%"
        )

    if average_time is None:
        print("Average time/game: N/A")
    else:
        print(
            f"Average time/game: "
            f"{average_time:.4f} s"
        )

    return result


# ============================================================
# CSV
# ============================================================

FIELDNAMES = [
    "layout",
    "configuration",
    "agent",
    "depth",
    "simulations",
    "rollout_depth",
    "games",

    "average_score",
    "median_score",
    "std_score",
    "min_score",
    "max_score",

    "wins",
    "win_rate",

    "total_time",
    "average_time",

    "status",
    "error"
]


def append_result(result):
    """
    Dodaje JEDAN rezultat odmah nakon što se eksperiment završi.

    Ovo je sigurnije od čuvanja svega tek na kraju.
    Ako se laptop ugasi, svi prethodno završeni redovi ostaju sačuvani.
    """

    try:
        with open(
            OUTPUT_FILE,
            "x",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=FIELDNAMES
            )

            writer.writeheader()

    except FileExistsError:
        pass

    with open(
        OUTPUT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES
        )

        writer.writerow(result)


# ============================================================
# MAIN
# ============================================================

def main():

    configurations = build_configurations()

    resume_point_found = False

    remaining_runs = []

    # --------------------------------------------------------
    # Find everything AFTER the last completed configuration
    # --------------------------------------------------------

    for layout in LAYOUTS:

        for config in configurations:

            if resume_point_found:
                remaining_runs.append(
                    (layout, config)
                )

            elif (
                layout == RESUME_AFTER_LAYOUT
                and
                config["configuration"]
                == RESUME_AFTER_CONFIGURATION
            ):
                resume_point_found = True

    if not resume_point_found:
        print(
            "ERROR: Resume configuration "
            "was not found."
        )

        return

    print()
    print("=" * 90)

    print(
        "NASTAVLJANJE PREKINUTOG EKSPERIMENTA"
    )

    print("=" * 90)

    print(
        "Poslednja završena konfiguracija:"
    )

    print(
        RESUME_AFTER_LAYOUT,
        "/",
        RESUME_AFTER_CONFIGURATION
    )

    print()

    print(
        "Sledeća konfiguracija:"
    )

    if remaining_runs:
        print(
            remaining_runs[0][0],
            "/",
            remaining_runs[0][1]["configuration"]
        )

    print()

    print(
        "Preostalih konfiguracija:",
        len(remaining_runs)
    )

    print(
        "Broj igara po konfiguraciji:",
        GAMES_PER_CONFIGURATION
    )

    print(
        "Ukupno preostalih igara:",
        len(remaining_runs)
        * GAMES_PER_CONFIGURATION
    )

    print(
        "Novi rezultati se čuvaju u:",
        OUTPUT_FILE
    )

    print("=" * 90)

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    for index, (layout, config) in enumerate(
        remaining_runs,
        start=1
    ):

        print()
        print(
            f"REMAINING RUN "
            f"{index}/{len(remaining_runs)}"
        )

        result = run_configuration(
            layout,
            config
        )

        # SAVE IMMEDIATELY
        append_result(result)

        print(
            "Result saved successfully."
        )

    print()
    print("=" * 90)
    print("ALL REMAINING EXPERIMENTS FINISHED")
    print("=" * 90)

    print(
        "Results:",
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()