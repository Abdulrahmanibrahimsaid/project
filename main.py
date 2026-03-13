from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# ------------------------------
# Step 1: Read fixed data from Excel
# ------------------------------
file = "bioethanol_data.xlsx"

feed_df = pd.read_excel(file, sheet_name="Feedstock")
conv_df = pd.read_excel(file, sheet_name="Conversion")

# تنظيف أسماء الأعمدة
feed_df.columns = feed_df.columns.str.strip().str.lower()
conv_df.columns = conv_df.columns.str.strip().str.lower()

# قيم ثابتة من الملف
cell_frac = feed_df.loc[0, "cellulose fraction"]
hemi_frac = feed_df.loc[0, "hemicellulose fraction"]
lign_frac = feed_df.loc[0, "lignin fraction"]
moisture_default = feed_df.loc[0, "moisture"]/100  # decimal

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

    # Economics
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

# ------------------------------
# Step 3: Flask routes
# ------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    pretreat_plot = None
    hydroly_plot = None
    ferment_plot = None
    ethanol_plot = None
    profit_plot = None

    if request.method == "POST":
        # قراءة مدخلات المستخدم
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
        # Sensitivity Analysis: Efficiencies
        # ------------------------------
        eff_range = np.linspace(0.5, 1.0, 31)

        pretreat_profits = [simulate_scenario(feed_rate, p, hydroly_eff, ferment_eff,
                                             eth_price, feed_cost, enzyme_cost, annual_operating_cost)["daily_profit"] for p in eff_range]
        hydroly_profits  = [simulate_scenario(feed_rate, pretreat_eff, h, ferment_eff,
                                             eth_price, feed_cost, enzyme_cost, annual_operating_cost)["daily_profit"] for h in eff_range]
        ferment_profits  = [simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, f,
                                             eth_price, feed_cost, enzyme_cost, annual_operating_cost)["daily_profit"] for f in eff_range]

        pretreat_plot = plot_to_img(eff_range*100, pretreat_profits, "Pretreatment Efficiency", "Efficiency (%)", "Daily Profit ($)", "red")
        hydroly_plot  = plot_to_img(eff_range*100, hydroly_profits, "Hydrolysis Efficiency", "Efficiency (%)", "Daily Profit ($)", "blue")
        ferment_plot  = plot_to_img(eff_range*100, ferment_profits, "Fermentation Efficiency", "Efficiency (%)", "Daily Profit ($)", "green")

        # ------------------------------
        # Sensitivity vs Feed Rate
        # ------------------------------
        feed_range = np.linspace(feed_rate*0.7, feed_rate*1.3, 10)
        ethanol_prod = []
        profit_list = []

        for f in feed_range:
            sim = simulate_scenario(f, pretreat_eff, hydroly_eff, ferment_eff,
                                    eth_price, feed_cost, enzyme_cost, annual_operating_cost)
            ethanol_prod.append(sim["ethanol_L"])
            profit_list.append(sim["daily_profit"])

        ethanol_plot = plot_to_img(feed_range, ethanol_prod, "Ethanol Production vs Feedstock Rate",
                                   "Feedstock Rate (ton/day)", "Ethanol Production (L/day)", "blue", marker='o')
        profit_plot = plot_to_img(feed_range, profit_list, "Daily Profit vs Feedstock Rate",
                                   "Feedstock Rate (ton/day)", "Daily Profit ($)", "orange", marker='o')

    return render_template("index.html",
                           results=results,
                           pretreat_plot=pretreat_plot,
                           hydroly_plot=hydroly_plot,
                           ferment_plot=ferment_plot,
                           ethanol_plot=ethanol_plot,
                           profit_plot=profit_plot)

# ------------------------------
# Helper function to convert plot to image
# ------------------------------
def plot_to_img(x, y, title, xlabel, ylabel, color='blue', marker=None):
    plt.figure(figsize=(8,5))
    if marker:
        plt.plot(x, y, marker=marker, color=color)
    else:
        plt.plot(x, y, color=color)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_base64

# ------------------------------
# Run Flask
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)
