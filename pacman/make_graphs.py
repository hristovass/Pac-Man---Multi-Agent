import pandas as pd
import matplotlib.pyplot as plt

# Nalaganje CSV datoteke
df = pd.read_csv("experiment_results.csv")

# Krajša imena algoritmov
labels = ["Minimax", "AlphaBeta", "Expectimax", "MCTS", "HybridMCTS"]

# -----------------------------
# Graf povprečnega rezultata
# -----------------------------
plt.figure(figsize=(8, 5))

plt.bar(labels, df["average_score"])

plt.title("Primerjava povprečnega rezultata")
plt.xlabel("Algoritmi")
plt.ylabel("Povprečni rezultat")

plt.xticks(rotation=10)

plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

plt.savefig("average_score.png")

plt.close()

# -----------------------------
# Graf deleža zmag
# -----------------------------
plt.figure(figsize=(8, 5))

plt.bar(labels, df["win_rate"])

plt.title("Primerjava deleža zmag")
plt.xlabel("Algoritmi")
plt.ylabel("Delež zmag (%)")

plt.xticks(rotation=10)

plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

plt.savefig("win_rate.png")

plt.close()

# -----------------------------
# Graf časa izvajanja
# -----------------------------
plt.figure(figsize=(8, 5))

plt.bar(labels, df["average_time"])

plt.title("Primerjava časa izvajanja")
plt.xlabel("Algoritmi")
plt.ylabel("Povprečni čas izvajanja (s)")

plt.xticks(rotation=10)

plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()

plt.savefig("execution_time.png")

plt.close()

print("Grafi so bili uspešno ustvarjeni.")