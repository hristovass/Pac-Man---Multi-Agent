import csv
import os
import re
import statistics
import subprocess
import sys
import time
from itertools import product


# ============================================================
# GLOBAL SETTINGS
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


OUTPUT_FILE = "full_grid_results.csv"


# ============================================================
# CREATE CONFIGURATIONS
# ============================================================

def build_configurations():
    configs = []

    # --------------------------------------------------------
    # Minimax
    # --------------------------------------------------------

    for depth in CLASSIC_DEPTHS:
        configs.append({
            "configuration": f"Minimax_d{depth}",
            "agent": "MinimaxAgent",
            "depth": depth,
            "simulations": None,
            "rollout_depth": None,
            "args": f"depth={depth}"
        })

    # --------------------------------------------------------
    # Alpha-Beta
    # --------------------------------------------------------

    for depth in CLASSIC_DEPTHS:
        configs.append({
            "configuration": f"AlphaBeta_d{depth}",
            "agent": "AlphaBetaAgent",
            "depth": depth,
            "simulations": None,
            "rollout_depth": None,
            "args": f"depth={depth}"
        })

    # --------------------------------------------------------
    # Expectimax
    # --------------------------------------------------------

    for depth in CLASSIC_DEPTHS:
        configs.append({
            "configuration": f"Expectimax_d{depth}",
            "agent": "ExpectimaxAgent",
            "depth": depth,
            "simulations": None,
            "rollout_depth": None,
            "args": f"depth={depth}"
        })

    # --------------------------------------------------------
    # MCTS
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Hybrid MCTS
    # --------------------------------------------------------

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
# OUTPUT PARSING
# ============================================================

def parse_scores(output):
    """
    Reads:
    Scores: 100, 200, ...
    """

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
    """
    Berkeley Pacman usually prints something like:

    Win Rate: 3/10 (0.30)
    """

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

    median_score = statistics.median(scores)

    if len(scores) > 1:
        std_score = statistics.stdev(scores)
    else:
        std_score = 0.0

    return {
        "median_score": median_score,
        "std_score": std_score,
        "min_score": min(scores),
        "max_score": max(scores)
    }


# ============================================================
# RUN ONE CONFIGURATION
# ============================================================

def run_configuration(layout, config):
    print()
    print("=" * 90)

    print(
        f"Layout={layout} | "
        f"Configuration={config['configuration']} | "
        f"Games={GAMES_PER_CONFIGURATION}"
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

        "-q",
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
        print("ERROR")
        print(process.stderr)

        return {
            "layout": layout,
            "configuration": config["configuration"],
            "agent": config["agent"],
            "depth": config["depth"],
            "simulations": config["simulations"],
            "rollout_depth": config["rollout_depth"],
            "games": GAMES_PER_CONFIGURATION,
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
        f"Average time/game: {average_time:.4f}s"
    )

    return result


# ============================================================
# SAVE CSV
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


def save_results(results):
    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES
        )

        writer.writeheader()

        writer.writerows(results)


# ============================================================
# MAIN
# ============================================================

def main():
    configurations = build_configurations()

    results = []

    total_runs = (
        len(LAYOUTS)
        * len(configurations)
    )

    print()
    print("FULL EXPERIMENT GRID")
    print("--------------------")

    print(
        "Layouts:",
        len(LAYOUTS)
    )

    print(
        "Configurations per layout:",
        len(configurations)
    )

    print(
        "Total configuration runs:",
        total_runs
    )

    print(
        "Games per configuration:",
        GAMES_PER_CONFIGURATION
    )

    print(
        "Approximate total number of games:",
        total_runs * GAMES_PER_CONFIGURATION
    )

    run_number = 0

    for layout in LAYOUTS:

        for config in configurations:

            run_number += 1

            print()
            print(
                f"RUN {run_number}/{total_runs}"
            )

            result = run_configuration(
                layout,
                config
            )

            results.append(result)

            # IMPORTANT:
            # Save after every run so nothing is lost
            save_results(results)

    print()
    print("=" * 90)
    print("ALL EXPERIMENTS FINISHED")
    print("=" * 90)

    print(
        "Results saved to:",
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()