// دالة المحاكاة الرئيسية - تتواصل مع الخلفية
async function runSimulation() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    
    try {
        // قراءة المدخلات
        const params = {
            feed_rate: parseFloat(document.getElementById('feedRate').value),
            pretreat_eff: parseFloat(document.getElementById('pretreatEff').value),
            hydroly_eff: parseFloat(document.getElementById('hydrolyEff').value),
            ferment_eff: parseFloat(document.getElementById('fermentEff').value),
            eth_price: parseFloat(document.getElementById('ethPrice').value),
            feed_cost: parseFloat(document.getElementById('feedCost').value),
            enzyme_cost: parseFloat(document.getElementById('enzymeCost').value),
            annual_operating_cost: parseFloat(document.getElementById('annualCost').value),
            sens_min: parseFloat(document.getElementById('sensMin').value),
            sens_max: parseFloat(document.getElementById('sensMax').value),
            feed_range: parseFloat(document.getElementById('feedRange').value)
        };
        
        // التحقق من المدخلات
        if (isNaN(params.feed_rate) || params.feed_rate <= 0) {
            throw new Error('الرجاء إدخال كمية مواد خام صحيحة');
        }
        if (params.pretreat_eff < 0.5 || params.pretreat_eff > 1.0) {
            throw new Error('كفاءة المعالجة يجب أن تكون بين 0.5 و 1.0');
        }
        
        // إرسال الطلب إلى الخادم
        const response = await fetch('/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        // عرض النتائج
        displayResults(data.results);
        drawCharts(data.sensitivity, data.feedAnalysis, data.results);
        
    } catch (error) {
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = error.message;
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// عرض النتائج
function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    const resultsContent = document.getElementById('resultsContent');
    const profitDisplay = document.getElementById('profitDisplay');
    
    profitDisplay.textContent = `$${results.dailyProfit.toFixed(2)}`;
    
    resultsContent.innerHTML = `
        <div class="result-card">
            <div class="result-title">📦 المواد الخام الجافة</div>
            <div class="result-value">${results.dryBiomass.toFixed(2)} <span class="result-unit">طن/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">🌾 السليلوز</div>
            <div class="result-value">${results.cellulose.toFixed(2)} <span class="result-unit">كجم/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">🌿 الهيميسليلوز</div>
            <div class="result-value">${results.hemicellulose.toFixed(2)} <span class="result-unit">كجم/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">🪵 اللجنين</div>
            <div class="result-value">${results.lignin.toFixed(2)} <span class="result-unit">كجم/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">🍬 الجلوكوز المنتج</div>
            <div class="result-value">${results.glucose.toFixed(2)} <span class="result-unit">كجم/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">🍬 الزايلوز المنتج</div>
            <div class="result-value">${results.xylose.toFixed(2)} <span class="result-unit">كجم/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">📊 إجمالي السكريات</div>
            <div class="result-value">${results.totalSugars.toFixed(2)}
