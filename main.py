import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# --- الخطوة 1: قراءة البيانات من الإكسيل ---
file = "bioethanol_data.xlsx"
def get_excel_data():
    f_df = pd.read_excel(file, sheet_name="Feedstock")
    c_df = pd.read_excel(file, sheet_name="Conversion")
    f_df.columns = f_df.columns.str.strip().str.lower()
    c_df.columns = c_df.columns.str.strip().str.lower()
    return f_df, c_df

# --- الخطوة 2: دالة المحاكاة بمعايير NREL ---
def simulate_scenario(feed_rate, pretreat_eff, hydroly_eff, ferment_eff,
                      eth_price, feed_cost, enzyme_cost, annual_operating_cost):
    
    f_df, c_df = get_excel_data()
    
    # المعاملات الفنية
    moisture = f_df.loc[0, "moisture"] / 100
    cell_frac = f_df.loc[0, "cellulose fraction"]
    hemi_frac = f_df.loc[0, "hemicellulose fraction"]
    
    # معاملات التحويل الكيميائية (NREL Factors)
    c_to_g = 1.111  # Cellulose to Glucose
    h_to_x = 1.136  # Hemicellulose to Xylose
    theoretical_yield = 0.511 # g ethanol / g sugar
    eth_density = 0.789 # kg/L

    # الحسابات
    dry_biomass = feed_rate * (1 - moisture)
    cellulose_kg = dry_biomass * cell_frac * 1000
    hemicell_kg = dry_biomass * hemi_frac * 1000
    
    glucose_kg = cellulose_kg * c_to_g * pretreat_eff * hydroly_eff
    xylose_kg = hemicell_kg * h_to_x * pretreat_eff * hydroly_eff
    total_sugar_kg = glucose_kg + xylose_kg
    
    fermentable_sugar = total_sugar_kg * ferment_eff
    ethanol_kg = fermentable_sugar * theoretical_yield
    ethanol_L = ethanol_kg / eth_density
    
    # الحسابات المالية
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
        # النتيجة الأساسية
        res = simulate_scenario(float(d["feed_rate"]), float(d["pretreat_eff"]), 
                                float(d["hydroly_eff"]), float(d["ferment_eff"]),
                                float(d["eth_price"]), float(d["feed_cost"]), 
                                float(d["enzyme_cost"]), float(d["annual_operating_cost"]))
        
        # تحليل الحساسية للكفاءات
        eff_range = np.linspace(0.5, 1.0, 11)
        sens_eff = {
            "labels": (eff_range * 100).tolist(),
            "pretreat": [simulate_scenario(float(d["feed_rate"]), e, float(d["hydroly_eff"]), float(d["ferment_eff"]), float(d["eth_price"]), float(d["feed_cost"]), float(d["enzyme_cost"]), float(d["annual_operating_cost"]))["daily_profit"] for e in eff_range],
            "hydroly": [simulate_scenario(float(d["feed_rate"]), float(d["pretreat_eff"]), e, float(d["ferment_eff"]), float(d["eth_price"]), float(d["feed_cost"]), float(d["enzyme_cost"]), float(d["annual_operating_cost"]))["daily_profit"] for e in eff_range],
            "ferment": [simulate_scenario(float(d["feed_rate"]), float(d["pretreat_eff"]), float(d["hydroly_eff"]), e, float(d["eth_price"]), float(d["feed_cost"]), float(d["enzyme_cost"]), float(d["annual_operating_cost"]))["daily_profit"] for e in eff_range]
        }
        
        return jsonify({"main": res, "sens_eff": sens_eff})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
