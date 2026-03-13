import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

file = "bioethanol_data.xlsx"

def get_data():
    f_df = pd.read_excel(file, sheet_name="Feedstock")
    c_df = pd.read_excel(file, sheet_name="Conversion")
    f_df.columns = f_df.columns.str.strip().str.lower()
    c_df.columns = c_df.columns.str.strip().str.lower()
    return f_df, c_df

def simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, ferment_eff, 
                      eth_price, feed_cost, enzyme_cost, annual_operating_cost):
    f_df, c_df = get_data()
    
    # المعاملات من الإكسيل
    cell_frac = f_df.loc[0, "cellulose fraction"]
    hemi_frac = f_df.loc[0, "hemicellulose fraction"]
    moisture = f_df.loc[0, "moisture"] / 100
    gluc_to_eth = c_df.loc[0, "glucose_to_ethanol_yield"]
    eth_density = c_df.loc[0, "ethanol_density"]

    # الحسابات التفصيلية
    dry_biomass = feed_rate * (1 - moisture)
    cellulose_kg = dry_biomass * cell_frac * 1000
    hemicell_kg = dry_biomass * hemi_frac * 1000
    
    sugar_from_cell = cellulose_kg * pretreat_eff * hydroly_eff
    sugar_from_hemi = hemicell_kg * pretreat_eff * hydroly_eff
    total_sugar_kg = sugar_from_cell + sugar_from_hemi
    
    fermentable_sugar = total_sugar_kg * ferment_eff
    ethanol_L = fermentable_sugar * gluc_to_eth
    ethanol_kg = ethanol_L * eth_density
    
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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/simulate", methods=["POST"])
def simulate():
    d = request.json
    try:
        main_res = simulate_scenario(
            float(d["feed_rate"]), float(d["pretreat_eff"]), float(d["hydroly_eff"]), 
            float(d["ferment_eff"]), float(d["eth_price"]), float(d["feed_cost"]), 
            float(d["enzyme_cost"]), float(d["annual_operating_cost"])
        )
        
        sensitivity = []
        for eff in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            s_res = simulate_scenario(
                float(d["feed_rate"]), float(d["pretreat_eff"]), float(d["hydroly_eff"]), 
                eff, float(d["eth_price"]), float(d["feed_cost"]), 
                float(d["enzyme_cost"]), float(d["annual_operating_cost"])
            )
            sensitivity.append({"efficiency": eff, "profit": s_res["daily_profit"]})
            
        return jsonify({"main": main_res, "sensitivity": sensitivity})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
