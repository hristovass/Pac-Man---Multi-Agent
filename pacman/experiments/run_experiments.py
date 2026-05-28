import csv
import subprocess
import time
import re


AGENTS = [
    ("MinimaxAgent", ""),
    ("AlphaBetaAgent", ""),
    ("ExpectimaxAgent", ""),
    ("MCTSAgent", "simulations=15,rolloutDepth=6"),
    ("HybridMCTSAgent", "simulations=20,rolloutDepth=8"),
]


NUMBER_OF_GAMES = 20
LAYOUT = "smallClassic"


def parse_score(output):
    average_match = re.search(r"Average Score:\s*(-?\d+\.?\d*)", output)
    if average_match:
        return float(average_match.group(1))

    score_matches = re.findall(r"Score:\s*(-?\d+)", output)
    if score_matches:
        return int(score_matches[-1])

    return None


def parse_win(output):
    if "Pacman emerges victorious" in output:
        return 1
    return 0


def run_single_game(agent_name, agent_args):
    command = [
        "python",
        "pacman.py",
        "-p",
        agent_name,
        "-n",
        "1",
        "-q",
        "-l",
        LAYOUT
    ]

    if agent_args:
        command.extend(["-a", agent_args])

    start = time.time()
    result = subprocess.run(command, capture_output=True, text=True)
    end = time.time()

    output = result.stdout
    error = result.stderr

    if result.returncode != 0:
        print("ERROR while running:", agent_name)
        print(error)
        return None

    score = parse_score(output)
    win = parse_win(output)

    if score is None:
        print("WARNING: Score nije pronađen za:", agent_name)
        print("OUTPUT:")
        print(output)

    return {
        "score": score,
        "win": win,
        "time": end - start
    }


def run_agent(agent_name, agent_args):
    scores = []
    wins = 0
    times = []

    print(f"\nRunning {agent_name}...")

    for game_index in range(NUMBER_OF_GAMES):
        result = run_single_game(agent_name, agent_args)

        if result is None:
            continue

        if result["score"] is not None:
            scores.append(result["score"])

        wins += result["win"]
        times.append(result["time"])

        print(f"Game {game_index + 1}/{NUMBER_OF_GAMES} finished.")

    if len(scores) == 0:
        average_score = None
    else:
        average_score = sum(scores) / len(scores)

    average_time = sum(times) / len(times) if times else None
    win_rate = (wins / NUMBER_OF_GAMES) * 100

    return {
        "agent": agent_name,
        "arguments": agent_args,
        "games": NUMBER_OF_GAMES,
        "average_score": average_score,
        "average_time": average_time,
        "win_rate": win_rate
    }


def main():
    all_results = []

    for agent_name, agent_args in AGENTS:
        result = run_agent(agent_name, agent_args)
        all_results.append(result)

    with open("experiment_results.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "agent",
                "arguments",
                "games",
                "average_score",
                "average_time",
                "win_rate"
            ]
        )

        writer.writeheader()
        writer.writerows(all_results)

    print("\nEksperimenti so končani.")
    print("Rezultati so shranjeni v experiment_results.csv")


if __name__ == "__main__":
    main()