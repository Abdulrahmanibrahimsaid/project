from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

file = "bioethanol_data.xlsx"

feed_df = pd.read_excel(file, sheet_name="Feedstock")
conv_df = pd.read_excel(file, sheet_name="Conversion")

feed_df.columns = feed_df.columns.str.strip().str.lower()
conv_df.columns = conv_df.columns.str.strip().str.lower()

cell_frac = feed_df.loc[0, "cellulose fraction"]
hemi_frac = feed_df.loc[0, "hemicellulose fraction"]
moisture_default = feed_df.loc[0, "moisture"]/100

gluc_to_eth = conv_df.loc[0, "glucose_to_ethanol_yield"]
eth_density = conv_df.loc[0, "ethanol_density"]


def simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, ferment_eff,
                      eth_price, feed_cost, enzyme_cost, annual_operating_cost):

    dry_biomass = feed_rate * (1 - moisture_default)
    cellulose_kg = dry_biomass * cell_frac * 1000
    hemicell_kg  = dry_biomass * hemi_frac * 1000

    sugar_from_cell = cellulose_kg * pretreat_eff * hydroly_eff
    sugar_from_hemi = hemicell_kg * pretreat_eff * hydroly_eff
    total_sugar_kg  = sugar_from_cell + sugar_from_hemi

    fermentable_sugar = total_sugar_kg * ferment_eff
    ethanol_L = fermentable_sugar * gluc_to_eth
    ethanol_kg = ethanol_L * eth_density

    daily_revenue = ethanol_L * eth_price
    daily_feed_cost = feed_rate * feed_cost
    daily_enzyme_cost = total_sugar_kg * enzyme_cost
    daily_operating = annual_operating_cost / 365

    total_daily_cost = daily_feed_cost + daily_enzyme_cost + daily_operating
    daily_profit = daily_revenue - total_daily_cost

    return ethanol_L, daily_profit


@app.route("/", methods=["GET", "POST"])
def index():

    result = None
    chart_path = None

    if request.method == "POST":

        feed_rate = float(request.form["feed_rate"])
        pretreat_eff = float(request.form["pretreat_eff"])
        hydroly_eff = float(request.form["hydroly_eff"])
        ferment_eff = float(request.form["ferment_eff"])
        eth_price = float(request.form["eth_price"])
        feed_cost = float(request.form["feed_cost"])
        enzyme_cost = float(request.form["enzyme_cost"])
        annual_operating_cost = float(request.form["annual_operating_cost"])

        ethanol_L, daily_profit = simulate_scenario(
            feed_rate, pretreat_eff, hydroly_eff, ferment_eff,
            eth_price, feed_cost, enzyme_cost, annual_operating_cost
        )

        result = {
            "ethanol_L": round(ethanol_L,2),
            "daily_profit": round(daily_profit,2)
        }

        eff_range = np.linspace(0.7,1.0,31)
        profits = []

        for e in eff_range:
            _, p = simulate_scenario(
                feed_rate, e, hydroly_eff, ferment_eff,
                eth_price, feed_cost, enzyme_cost, annual_operating_cost
            )
            profits.append(p)

        plt.figure()
        plt.plot(eff_range*100, profits)
        plt.xlabel("Pretreatment Efficiency (%)")
        plt.ylabel("Daily Profit ($)")
        plt.title("Sensitivity Analysis")

        chart_path = "static/chart.png"
        plt.savefig(chart_path)
        plt.close()

    return render_template("index.html", result=result, chart=chart_path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)