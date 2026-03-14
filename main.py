from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__)

# ------------------------------
# Step 1: Read fixed data from Excel
# ------------------------------
file = "bioethanol_data.xlsx"

feed_df = pd.read_excel(file, sheet_name="Feedstock")
conv_df = pd.read_excel(file, sheet_name="Conversion")

feed_df.columns = feed_df.columns.str.strip().str.lower()
conv_df.columns = conv_df.columns.str.strip().str.lower()

cell_frac = feed_df.loc[0, "cellulose fraction"]
hemi_frac = feed_df.loc[0, "hemicellulose fraction"]
lign_frac = feed_df.loc[0, "lignin fraction"]
moisture_default = feed_df.loc[0, "moisture"]/100

gluc_to_eth = conv_df.loc[0, "glucose_to_ethanol_yield"]
eth_density = conv_df.loc[0, "ethanol_density"]

cellulose_to_glucose = 1.111

# ------------------------------
# Step 2: Simulation function
# ------------------------------
def simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, ferment_eff,
                      eth_price, feed_cost, enzyme_cost, annual_operating_cost):

    dry_biomass = feed_rate * (1 - moisture_default)
    cellulose_kg = dry_biomass * cell_frac * 1000
    hemicell_kg  = dry_biomass * hemi_frac * 1000

    glucose_from_cellulose = cellulose_kg * cellulose_to_glucose
    xylose_from_hemi = hemicell_kg * cellulose_to_glucose

    sugar_from_cell = glucose_from_cellulose * pretreat_eff * hydroly_eff
    sugar_from_hemi = xylose_from_hemi * pretreat_eff * hydroly_eff

    total_sugar_kg = sugar_from_cell + sugar_from_hemi
    fermentable_sugar = total_sugar_kg * ferment_eff

    ethanol_kg = fermentable_sugar * gluc_to_eth
    ethanol_L = ethanol_kg / eth_density

    daily_revenue = ethanol_L * eth_price
    daily_feed_cost = feed_rate * feed_cost
    daily_enzyme_cost = total_sugar_kg * enzyme_cost
    daily_operating = annual_operating_cost / 365

    total_daily_cost = daily_feed_cost + daily_enzyme_cost + daily_operating
    daily_profit = daily_revenue - total_daily_cost

    return {
        "dry_biomass": dry_biomass,
        "total_sugar_kg": total_sugar_kg,
        "fermentable_sugar_kg": fermentable_sugar,
        "ethanol_L": ethanol_L,
        "ethanol_kg": ethanol_kg,
        "daily_revenue": daily_revenue,
        "total_daily_cost": total_daily_cost,
        "daily_profit": daily_profit
    }


@app.route("/", methods=["GET","POST"])
def index():

    results = None
    eff_plot = None
    ethanol_plot = None
    profit_plot = None

    if request.method == "POST":

        feed_rate = float(request.form["feed_rate"])
        pretreat_eff = float(request.form["pretreat_eff"])
        hydroly_eff = float(request.form["hydroly_eff"])
        ferment_eff = float(request.form["ferment_eff"])

        eth_price = float(request.form["eth_price"])
        feed_cost = float(request.form["feed_cost"])
        enzyme_cost = float(request.form["enzyme_cost"])
        annual_operating_cost = float(request.form["annual_operating_cost"])

        results = simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, ferment_eff,
                                    eth_price, feed_cost, enzyme_cost, annual_operating_cost)

        # ------------------------------
        # Step 5: Sensitivity Analysis
        # ------------------------------
        eff_range = np.linspace(0.5, 1.0, 31)

        pretreat_profits = [simulate_scenario(feed_rate, p, hydroly_eff, ferment_eff,
                                              eth_price, feed_cost, enzyme_cost,
                                              annual_operating_cost)["daily_profit"] for p in eff_range]

        hydroly_profits  = [simulate_scenario(feed_rate, pretreat_eff, h, ferment_eff,
                                              eth_price, feed_cost, enzyme_cost,
                                              annual_operating_cost)["daily_profit"] for h in eff_range]

        ferment_profits  = [simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, f,
                                              eth_price, feed_cost, enzyme_cost,
                                              annual_operating_cost)["daily_profit"] for f in eff_range]

        plt.figure(figsize=(10,6))
        plt.plot(eff_range*100, pretreat_profits, label="Pretreatment Efficiency")
        plt.plot(eff_range*100, hydroly_profits, label="Hydrolysis Efficiency")
        plt.plot(eff_range*100, ferment_profits, label="Fermentation Efficiency")
        plt.xlabel("Efficiency (%)")
        plt.ylabel("Daily Profit ($)")
        plt.title("Sensitivity Analysis")
        plt.legend()
        plt.grid(True)
        eff_plot = "static_efficiency.png"
        plt.savefig(eff_plot)
        plt.close()

        # ------------------------------
        # Step 6: Feed Rate Analysis
        # ------------------------------
        feed_range = np.linspace(feed_rate*0.7, feed_rate*1.3, 10)
        ethanol_prod = []
        profit_list = []

        for f in feed_range:
            sim = simulate_scenario(f, pretreat_eff, hydroly_eff, ferment_eff,
                                    eth_price, feed_cost, enzyme_cost, annual_operating_cost)
            ethanol_prod.append(sim["ethanol_L"])
            profit_list.append(sim["daily_profit"])

        plt.figure(figsize=(10,6))
        plt.plot(feed_range, ethanol_prod, marker='o')
        plt.xlabel("Feedstock Rate (ton/day)")
        plt.ylabel("Ethanol Production (L/day)")
        plt.title("Ethanol Production vs Feedstock Rate")
        plt.grid(True)
        ethanol_plot = "static_ethanol.png"
        plt.savefig(ethanol_plot)
        plt.close()

        plt.figure(figsize=(10,6))
        plt.plot(feed_range, profit_list, marker='o')
        plt.xlabel("Feedstock Rate (ton/day)")
        plt.ylabel("Daily Profit ($)")
        plt.title("Daily Profit vs Feedstock Rate")
        plt.grid(True)
        profit_plot = "static_profit.png"
        plt.savefig(profit_plot)
        plt.close()

    return render_template("index.html",
                           results=results,
                           eff_plot=eff_plot,
                           ethanol_plot=ethanol_plot,
                           profit_plot=profit_plot)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
