import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template
import os

app = Flask(__name__)

# --- الخطوة 1: قراءة البيانات من الإكسيل (نفس منطقك بالظبط) ---
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
cellulose_to_glucose = 1.111

# --- الخطوة 2: دالة المحاكاة (بدون أي تغيير في المعادلات) ---
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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.json
    try:
        f_rate = float(data["feed_rate"])
        p_eff = float(data["pretreat_eff"])
        h_eff = float(data["hydroly_eff"])
        f_eff = float(data["ferment_eff"])
        price = float(data["eth_price"])
        f_cost = float(data["feed_cost"])
        e_cost = float(data["enzyme_cost"])
        ann_cost = float(data["annual_operating_cost"])

        # النتيجة الأساسية
        main_res = simulate_scenario(f_rate, p_eff, h_eff, f_eff, price, f_cost, e_cost, ann_cost)

        # تحليل الحساسية للكفاءات (Step 5)
        eff_range = np.linspace(0.5, 1.0, 11) # قللت النقاط لسرعة الويب
        sens_eff = {
            "labels": (eff_range * 100).tolist(),
            "pretreat": [simulate_scenario(f_rate, e, h_eff, f_eff, price, f_cost, e_cost, ann_cost)["daily_profit"] for e in eff_range],
            "hydroly": [simulate_scenario(f_rate, p_eff, e, f_eff, price, f_cost, e_cost, ann_cost)["daily_profit"] for e in eff_range],
            "ferment": [simulate_scenario(f_rate, p_eff, h_eff, e, price, f_cost, e_cost, ann_cost)["daily_profit"] for e in eff_range]
        }

        # تحليل الحساسية للـ Feed Rate (Step 6)
        feed_range = np.linspace(f_rate*0.7, f_rate*1.3, 10)
        sens_feed = {
            "labels": feed_range.tolist(),
            "ethanol": [simulate_scenario(f, p_eff, h_eff, f_eff, price, f_cost, e_cost, ann_cost)["ethanol_L"] for f in feed_range],
            "profit": [simulate_scenario(f, p_eff, h_eff, f_eff, price, f_cost, e_cost, ann_cost)["daily_profit"] for f in feed_range]
        }

        return jsonify({"main": main_res, "sens_eff": sens_eff, "sens_feed": sens_feed})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
