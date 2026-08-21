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
    match = re.search(
        r"Scores:\s*(.*)",
        output
    )

    if not match:
        return []

    scores = []

    for value in match.group(1).split(","):
        try:
            scores.append(float(value.strip()))
        except ValueError:
            pass

    return scores


def parse_average_score(output):
    match = re.search(
        r"Average Score:\s*(-?\d+(?:\.\d+)?)",
        output
    )

    if match:
        return float(match.group(1))

    return None


def parse_win_rate(output):
    match = re.search(
        r"Win Rate:\s*(\d+)/(\d+)\s*\(([\d.]+)\)",
        output
    )

    if not match:
        return None, None

    wins = int(match.group(1))
    games = int(match.group(2))

    win_rate = 100.0 * wins / games

    return wins, win_rate


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
        f"Games = {GAMES_PER_CONFIGURATION}"
    )

    print("=" * 90)

    command = [
        sys.executable,
        "pacman.py",

        "-p",
        config["agent"],

        "-l",
        layout,

        "-n",
        str(GAMES_PER_CONFIGURATION),

        "-q"
    ]

    if config["args"]:
        command.extend([
            "-a",
            config["args"]
        ])

    start_time = time.time()

    process = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    total_time = time.time() - start_time

    if process.returncode != 0:

        print("ERROR:")
        print(process.stderr)

        return {
            "layout": layout,
            "configuration": config["configuration"],
            "agent": config["agent"],
            "depth": config["depth"],
            "simulations": config["simulations"],
            "rollout_depth": config["rollout_depth"],
            "games": GAMES_PER_CONFIGURATION,

            "average_score": None,
            "median_score": None,
            "std_score": None,
            "min_score": None,
            "max_score": None,

            "wins": None,
            "win_rate": None,

            "total_time": total_time,
            "average_time": None,

            "status": "ERROR",
            "error": process.stderr.strip()
        }

    output = process.stdout

    scores = parse_scores(output)

    average_score = parse_average_score(output)

    wins, win_rate = parse_win_rate(output)

    stats = calculate_statistics(scores)

    average_time = (
        total_time / GAMES_PER_CONFIGURATION
    )

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
            "OK",

        "error":
            ""
    }

    print(
        f"Average score: {average_score}"
    )

    print(
        f"Win rate: {win_rate}%"
    )

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