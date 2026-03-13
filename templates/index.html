import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# إعداد البيانات من ملف الإكسيل
file = "bioethanol_data.xlsx"

def get_excel_data():
    feed_df = pd.read_excel(file, sheet_name="Feedstock")
    conv_df = pd.read_excel(file, sheet_name="Conversion")
    feed_df.columns = feed_df.columns.str.strip().str.lower()
    conv_df.columns = conv_df.columns.str.strip().str.lower()
    return feed_df, conv_df

def simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, ferment_eff,
                     eth_price, feed_cost, enzyme_cost, annual_operating_cost):
    
    feed_df, conv_df = get_excel_data()
    
    cell_frac = feed_df.loc[0, "cellulose fraction"]
    hemi_frac = feed_df.loc[0, "hemicellulose fraction"]
    moisture_default = feed_df.loc[0, "moisture"]/100
    gluc_to_eth = conv_df.loc[0, "glucose_to_ethanol_yield"]
    eth_density = conv_df.loc[0, "ethanol_density"]

    dry_biomass = feed_rate * (1 - moisture_default)
    cellulose_kg = dry_biomass * cell_frac * 1000
    hemicell_kg  = dry_biomass * hemi_frac * 1000

    sugar_from_cell = cellulose_kg * pretreat_eff * hydroly_eff
    sugar_from_hemi = hemicell_kg * pretreat_eff * hydroly_eff
    total_sugar_kg  = sugar_from_cell + sugar_from_hemi

    fermentable_sugar = total_sugar_kg * ferment_eff
    ethanol_L = fermentable_sugar * gluc_to_eth
    
    daily_revenue = ethanol_L * eth_price
    daily_feed_cost   = feed_rate * feed_cost
    daily_enzyme_cost = total_sugar_kg * enzyme_cost
    daily_operating   = annual_operating_cost / 365

    total_daily_cost = daily_feed_cost + daily_enzyme_cost + daily_operating
    daily_profit = daily_revenue - total_daily_cost

    return {
        "daily_profit": daily_profit,
        "ethanol_L": ethanol_L,
        "total_daily_cost": total_daily_cost
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.json
    try:
        results = simulate_scenario(
            float(data["feed_rate"]), float(data["pretreat_eff"]),
            float(data["hydroly_eff"]), float(data["ferment_eff"]),
            float(data["eth_price"]), float(data["feed_cost"]),
            float(data["enzyme_cost"]), float(data["annual_operating_cost"])
        )
        
        # إضافة تحليل الحساسية للكفاءة (Sensitivity Analysis)
        sensitivity = []
        for eff in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            s_res = simulate_scenario(
                float(data["feed_rate"]), float(data["pretreat_eff"]),
                float(data["hydroly_eff"]), eff,
                float(data["eth_price"]), float(data["feed_cost"]),
                float(data["enzyme_cost"]), float(data["annual_operating_cost"])
            )
            sensitivity.append({"efficiency": eff, "profit": s_res["daily_profit"]})
        
        return jsonify({"main": results, "sensitivity": sensitivity})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
