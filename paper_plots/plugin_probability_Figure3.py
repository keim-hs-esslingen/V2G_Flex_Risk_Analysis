import numpy as np
import matplotlib.pyplot as plt

# Parameter
SOCn = 60  # Schwelle (kannst du anpassen)
alphas = [5000, 1000, 500, 80, 40, 20, 10, 5, 2.5, 1, 0.5, 0.25, 0.1]

# X-Achse: SOC von 0 bis 100
SOC = np.linspace(0, 100, 500)

plt.figure(figsize=(10, 6))

for alpha in alphas:
    Ppl = np.where(
        SOC < SOCn,
        1,
        1 - ((SOC - SOCn) / (100 - SOCn))**alpha
    )
    plt.plot(SOC, Ppl, label=f"α={alpha}")

plt.xlabel("SOC (%)", fontsize = 20)

soc_ref = 90

if False:
    # vertikale Linie durch den gesamten Plot
    plt.axvline(
        x=soc_ref,
        color="gray",
        linestyle="--",
        linewidth=1.2
    )

    # Beschriftung auf der x-Achse
    plt.text(
        soc_ref,
        0,
        "90",
        ha="center",
        va="top",
        fontsize=16,
        color="gray"
    )

    for alpha in [2.5, 10]:

        ppl = 1 - ((soc_ref - SOCn) / (100 - SOCn))**alpha

        # horizontale Linie
        plt.hlines(
            y=ppl,
            xmin=0,
            xmax=soc_ref,
            colors="gray",
            linestyles="--",
            linewidth=1.2
        )

        # Schnittpunkt markieren
        plt.plot(soc_ref, ppl, "ko", markersize=5)

        # Beschriftung an der y-Achse
        plt.text(
            0,
            ppl,
            f"{ppl:.2f}",
            ha="right",
            va="center",
            fontsize=16,
            color="gray"
        )

plt.xticks(fontsize=20)
plt.yticks(fontsize=20)

plt.ylabel("Plug-in Probability", fontsize = 20)
#plt.title("Plug-in Probability vs SOC")
plt.legend(fontsize = 20, loc = "center left", ncol = 2)
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("figures/plugin_probability_Figure3.png", dpi=300)