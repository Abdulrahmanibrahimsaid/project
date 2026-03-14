// القيم الثابتة المعتمدة على دراسات حقيقية
const CONSTANTS = {
    // تركيبة الكتلة الحيوية (نموذج لقش الذرة)
    celluloseFraction: 0.45,        // 45% سليلوز
    hemicelluloseFraction: 0.30,     // 30% هيميسليلوز
    ligninFraction: 0.15,            // 15% ليجنين
    otherFraction: 0.10,              // 10% مواد أخرى
    
    // محتوى الرطوبة الافتراضي
    moisture: 0.15,                   // 15% رطوبة
    
    // معاملات التحويل (حسب الدراسات)
    celluloseToGlucose: 1.111,        // (162/180) معامل البلمرة
    hemicelluloseToXylose: 1.136,      // (132/150) معامل تحويل الهيميسليلوز
    
    // كفاءات التحويل البيوكيميائية
    glucoseToEthanol: 0.511,           // 51.1% كفاءة تحويل (نظري 0.511)
    xyloseToEthanol: 0.481,            // 48.1% كفاءة تحويل الزايلوز
    
    // خواص فيزيائية
    ethanolDensity: 0.789,              // كثافة الإيثانول كجم/لتر عند 20°C
    sugarToEthanol: 0.51,               // معامل تحويل السكر لإيثانول
    
    // القيم الحرارية
    ethanolEnergy: 29.7,                 // MJ/kg الطاقة النوعية للإيثانول
};

// دوال الحسابات الأساسية
function calculateCarbohydrates(dryBiomass) {
    const cellulose = dryBiomass * CONSTANTS.celluloseFraction;
    const hemicellulose = dryBiomass * CONSTANTS.hemicelluloseFraction;
    const lignin = dryBiomass * CONSTANTS.ligninFraction;
    const others = dryBiomass * CONSTANTS.otherFraction;
    
    return { cellulose, hemicellulose, lignin, others };
}

function calculateSugars(cellulose, hemicellulose, pretreatEff, hydrolyEff) {
    // تحويل السليلوز إلى جلوكوز
    const glucose = cellulose * CONSTANTS.celluloseToGlucose * pretreatEff * hydrolyEff;
    
    // تحويل الهيميسليلوز إلى زايلوز وسكريات أخرى
    const xylose = hemicellulose * CONSTANTS.hemicelluloseToXylose * pretreatEff * hydrolyEff;
    
    // سكريات أخرى بنسبة 10% من الهيميسليلوز
    const otherSugars = hemicellulose * 0.10 * pretreatEff * hydrolyEff;
    
    return {
        glucose: glucose,
        xylose: xylose,
        otherSugars: otherSugars,
        total: glucose + xylose + otherSugars
    };
}

function calculateEthanol(sugars, fermentEff) {
    // تحويل الجلوكوز
    const ethanolFromGlucose = sugars.glucose * CONSTANTS.glucoseToEthanol * fermentEff;
    
    // تحويل الزايلوز (كفاءة أقل)
    const ethanolFromXylose = sugars.xylose * CONSTANTS.xyloseToEthanol * fermentEff * 0.85;
    
    // تحويل السكريات الأخرى
    const ethanolFromOthers = sugars.otherSugars * CONSTANTS.sugarToEthanol * fermentEff * 0.90;
    
    const ethanolKg = ethanolFromGlucose + ethanolFromXylose + ethanolFromOthers;
    const ethanolL = ethanolKg / CONSTANTS.ethanolDensity;
    
    return {
        kg: ethanolKg,
        liters: ethanolL,
        fromGlucose: ethanolFromGlucose,
        fromXylose: ethanolFromXylose,
        fromOthers: ethanolFromOthers
    };
}

function calculateEconomics(ethanol, feedRate, sugars, params) {
    // الإيرادات
    const dailyRevenue = ethanol.liters * params.ethPrice;
    
    // التكاليف
    const dailyFeedCost = feedRate * params.feedCost;
    const dailyEnzymeCost = sugars.total * params.enzymeCost;
    const dailyOperating = params.annualOperatingCost / 365;
    const dailyLaborCost = params.annualOperatingCost * 0.3 / 365; // 30% للعمالة
    const dailyUtilityCost = params.annualOperatingCost * 0.2 / 365; // 20% للطاقة
    
    const totalDailyCost = dailyFeedCost + dailyEnzymeCost + dailyOperating + 
                          dailyLaborCost + dailyUtilityCost;
    
    const dailyProfit = dailyRevenue - totalDailyCost;
    
    // مؤشرات اقتصادية
    const profitMargin = (dailyProfit / dailyRevenue) * 100;
    const breakEvenPoint = totalDailyCost / params.ethPrice;
    const roi = (dailyProfit * 365) / (params.annualOperatingCost * 2) * 100; // عائد الاستثمار
    
    return {
        revenue: dailyRevenue,
        feedCost: dailyFeedCost,
        enzymeCost: dailyEnzymeCost,
        operatingCost: dailyOperating,
        laborCost: dailyLaborCost,
        utilityCost: dailyUtilityCost,
        totalCost: totalDailyCost,
        profit: dailyProfit,
        profitMargin: profitMargin,
        breakEvenPoint: breakEvenPoint,
        roi: roi
    };
}

// دالة المحاكاة الرئيسية
function simulateScenario(feedRate, pretreatEff, hydrolyEff, fermentEff,
                          ethPrice, feedCost, enzymeCost, annualOperatingCost) {
    
    // 1. حساب الكتلة الحيوية الجافة
    const dryBiomass = feedRate * (1 - CONSTANTS.moisture);
    
    // 2. حساب مكونات الكتلة الحيوية
    const { cellulose, hemicellulose, lignin, others } = calculateCarbohydrates(dryBiomass);
    
    // 3. حساب السكريات المنتجة
    const sugars = calculateSugars(cellulose, hemicellulose, pretreatEff, hydrolyEff);
    
    // 4. حساب الإيثانول المنتج
    const ethanol = calculateEthanol(sugars, fermentEff);
    
    // 5. الحسابات الاقتصادية
    const economics = calculateEconomics(ethanol, feedRate, sugars, {
        ethPrice, feedCost, enzymeCost, annualOperatingCost
    });
    
    // 6. حسابات إضافية
    const yieldPerTon = ethanol.liters / feedRate;
    const sugarConversionEff = (ethanol.kg / sugars.total) * 100;
    const overallEff = (ethanol.kg / (dryBiomass * 1000 * 0.75)) * 100; // كفاءة كلية
    
    return {
        // المدخلات
        feedRate: feedRate,
        dryBiomass: dryBiomass,
        
        // المكونات
        cellulose: cellulose * 1000,
        hemicellulose: hemicellulose * 1000,
        lignin: lignin * 1000,
        
        // السكريات
        glucose: sugars.glucose,
        xylose: sugars.xylose,
        totalSugars: sugars.total,
        
        // الإيثانول
        ethanolKg: ethanol.kg,
        ethanolL: ethanol.liters,
        ethanolFromGlucose: ethanol.fromGlucose,
        ethanolFromXylose: ethanol.fromXylose,
        
        // الاقتصاد
        dailyRevenue: economics.revenue,
        dailyFeedCost: economics.feedCost,
        dailyEnzymeCost: economics.enzymeCost,
        dailyOperating: economics.operatingCost,
        dailyLaborCost: economics.laborCost,
        dailyUtilityCost: economics.utilityCost,
        totalDailyCost: economics.totalCost,
        dailyProfit: economics.profit,
        profitMargin: economics.profitMargin,
        breakEvenPoint: economics.breakEvenPoint,
        roi: economics.roi,
        
        // مؤشرات الأداء
        yieldPerTon: yieldPerTon,
        sugarConversionEff: sugarConversionEff,
        overallEff: overallEff,
        
        // طاقة الإيثانول
        energyOutput: ethanol.kg * CONSTANTS.ethanolEnergy
    };
}

// تحليل الحساسية المتقدم
function advancedSensitivity(baseParams) {
    const {
        feedRate, pretreatEff, hydrolyEff, fermentEff,
        ethPrice, feedCost, enzymeCost, annualCost,
        sensMin, sensMax
    } = baseParams;
    
    const steps = 20;
    const range = [];
    const stepSize = (sensMax - sensMin) / steps;
    
    for (let i = 0; i <= steps; i++) {
        range.push(sensMin + i * stepSize);
    }
    
    const pretreatProfits = [];
    const hydrolyProfits = [];
    const fermentProfits = [];
    const priceProfits = [];
    const costProfits = [];
    
    range.forEach(val => {
        // تأثير كفاءة المعالجة
        const sim1 = simulateScenario(feedRate, val, hydrolyEff, fermentEff,
                                     ethPrice, feedCost, enzymeCost, annualCost);
        pretreatProfits.push(sim1.dailyProfit);
        
        // تأثير كفاءة التحلل
        const sim2 = simulateScenario(feedRate, pretreatEff, val, fermentEff,
                                     ethPrice, feedCost, enzymeCost, annualCost);
        hydrolyProfits.push(sim2.dailyProfit);
        
        // تأثير كفاءة التخمير
        const sim3 = simulateScenario(feedRate, pretreatEff, hydrolyEff, val,
                                     ethPrice, feedCost, enzymeCost, annualCost);
        fermentProfits.push(sim3.dailyProfit);
        
        // تأثير سعر الإيثانول
        const sim4 = simulateScenario(feedRate, pretreatEff, hydrolyEff, fermentEff,
                                     val * 2, feedCost, enzymeCost, annualCost);
        priceProfits.push(sim4.dailyProfit);
        
        // تأثير تكلفة المواد
        const sim5 = simulateScenario(feedRate, pretreatEff, hydrolyEff, fermentEff,
                                     ethPrice, val * 100, enzymeCost, annualCost);
        costProfits.push(sim5.dailyProfit);
    });
    
    return {
        range: range.map(v => v * 100),
        pretreatProfits,
        hydrolyProfits,
        fermentProfits,
        priceProfits,
        costProfits
    };
}

// تحليل تأثير المواد الخام
function feedRateAnalysis(baseParams) {
    const {
        feedRate, pretreatEff, hydrolyEff, fermentEff,
        ethPrice, feedCost, enzymeCost, annualCost, feedRange
    } = baseParams;
    
    const minFeed = feedRate * (1 - feedRange/100);
    const maxFeed = feedRate * (1 + feedRange/100);
    const steps = 15;
    const stepSize = (maxFeed - minFeed) / steps;
    
    const feedValues = [];
    const ethanolValues = [];
    const profitValues = [];
    const revenueValues = [];
    const costValues = [];
    
    for (let i = 0; i <= steps; i++) {
        const f = minFeed + i * stepSize;
        const sim = simulateScenario(f, pretreatEff, hydrolyEff, fermentEff,
                                    ethPrice, feedCost, enzymeCost, annualCost);
        
        feedValues.push(f);
        ethanolValues.push(sim.ethanolL);
        profitValues.push(sim.dailyProfit);
        revenueValues.push(sim.dailyRevenue);
        costValues.push(sim.totalDailyCost);
    }
    
    return { feedValues, ethanolValues, profitValues, revenueValues, costValues };
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
            <div class="result-value">${results.totalSugars.toFixed(2)} <span class="result-unit">كجم/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">🧪 الإيثانول (كتلة)</div>
            <div class="result-value">${results.ethanolKg.toFixed(2)} <span class="result-unit">كجم/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">🧪 الإيثانول (حجم)</div>
            <div class="result-value">${results.ethanolL.toFixed(2)} <span class="result-unit">لتر/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">📈 الإنتاجية</div>
            <div class="result-value">${results.yieldPerTon.toFixed(2)} <span class="result-unit">لتر/طن</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">💰 الإيرادات اليومية</div>
            <div class="result-value">$${results.dailyRevenue.toFixed(2)}</div>
        </div>
        <div class="result-card">
            <div class="result-title">💸 تكلفة المواد</div>
            <div class="result-value">$${results.dailyFeedCost.toFixed(2)}</div>
        </div>
        <div class="result-card">
            <div class="result-title">🧪 تكلفة الإنزيمات</div>
            <div class="result-value">$${results.dailyEnzymeCost.toFixed(2)}</div>
        </div>
        <div class="result-card">
            <div class="result-title">⚡ تكلفة الطاقة</div>
            <div class="result-value">$${results.dailyUtilityCost.toFixed(2)}</div>
        </div>
        <div class="result-card">
            <div class="result-title">👷 تكلفة العمالة</div>
            <div class="result-value">$${results.dailyLaborCost.toFixed(2)}</div>
        </div>
        <div class="result-card">
            <div class="result-title">🏭 تكاليف تشغيلية</div>
            <div class="result-value">$${results.dailyOperating.toFixed(2)}</div>
        </div>
        <div class="result-card">
            <div class="result-title">📊 إجمالي التكاليف</div>
            <div class="result-value">$${results.totalDailyCost.toFixed(2)}</div>
        </div>
        <div class="result-card">
            <div class="result-title">💵 صافي الربح</div>
            <div class="result-value" style="color: ${results.dailyProfit >= 0 ? '#2e7d32' : '#c62828'}">
                $${results.dailyProfit.toFixed(2)}
            </div>
        </div>
        <div class="result-card">
            <div class="result-title">📊 هامش الربح</div>
            <div class="result-value">${results.profitMargin.toFixed(2)}%</div>
        </div>
        <div class="result-card">
            <div class="result-title">⚖️ نقطة التعادل</div>
            <div class="result-value">${results.breakEvenPoint.toFixed(2)} <span class="result-unit">لتر/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">📈 عائد الاستثمار</div>
            <div class="result-value">${results.roi.toFixed(2)}%</div>
        </div>
        <div class="result-card">
            <div class="result-title">⚡ الطاقة المنتجة</div>
            <div class="result-value">${results.energyOutput.toFixed(2)} <span class="result-unit">MJ/يوم</span></div>
        </div>
        <div class="result-card">
            <div class="result-title">🔄 كفاءة تحويل السكر</div>
            <div class="result-value">${results.sugarConversionEff.toFixed(2)}%</div>
        </div>
        <div class="result-card">
            <div class="result-title">🎯 الكفاءة الكلية</div>
            <div class="result-value">${results.overallEff.toFixed(2)}%</div>
        </div>
    `;
    
    resultsDiv.style.display = 'block';
}

// رسم الرسوم البيانية
function drawCharts(effData, feedData, results) {
    // رسم 1: تأثير الكفاءات
    const ctx1 = document.getElementById('efficiencyChart').getContext('2d');
    new Chart(ctx1, {
        type: 'line',
        data: {
            labels: effData.range.map(x => x.toFixed(0) + '%'),
            datasets: [
                { label: 'كفاءة المعالجة', data: effData.pretreatProfits, borderColor: '#ff6384', tension: 0.4 },
                { label: 'كفاءة التحلل', data: effData.hydrolyProfits, borderColor: '#36a2eb', tension: 0.4 },
                { label: 'كفاءة التخمير', data: effData.fermentProfits, borderColor: '#4bc0c0', tension: 0.4 },
                { label: 'تأثير السعر', data: effData.priceProfits, borderColor: '#ffce56', tension: 0.4 },
                { label: 'تأثير التكلفة', data: effData.costProfits, borderColor: '#9966ff', tension: 0.4 }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'تحليل الحساسية متعدد المتغيرات' },
                legend: { position: 'bottom' }
            },
            scales: { y: { beginAtZero: false, title: { display: true, text: 'الربح ($)' } } }
        }
    });
    
    // رسم 2: تأثير كمية المواد
    const ctx2 = document.getElementById('feedRateChart').getContext('2d');
    new Chart(ctx2, {
        type: 'line',
        data: {
            labels: feedData.feedValues.map(x => x.toFixed(0) + ' طن'),
            datasets: [
                { label: 'الإيثانول (لتر)', data: feedData.ethanolValues, borderColor: '#4bc0c0', yAxisID: 'y', tension: 0.4 },
                { label: 'الربح ($)', data: feedData.profitValues, borderColor: '#ff6384', yAxisID: 'y1', tension: 0.4 },
                { label: 'الإيرادات', data: feedData.revenueValues, borderColor: '#36a2eb', yAxisID: 'y1', tension: 0.4 },
                { label: 'التكاليف', data: feedData.costValues, borderColor: '#9966ff', yAxisID: 'y1', tension: 0.4 }
            ]
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: 'تحليل اقتصاديات الإنتاج' } },
            scales: {
                y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'الإيثانول (لتر)' } },
                y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'القيمة ($)' }, grid: { drawOnChartArea: false } }
            }
        }
    });
    
    // رسم 3: السكريات vs الإيثانول
    const ctx3 = document.getElementById('sugarEthanolChart').getContext('2d');
    new Chart(ctx3, {
        type: 'bar',
        data: {
            labels: ['الجلوكوز', 'الزايلوز', 'إجمالي السكريات', 'الإيثانول'],
            datasets: [{
                label: 'الكمية (كجم)',
                data: [results.glucose, results.xylose, results.totalSugars, results.ethanolKg],
                backgroundColor: ['#36a2eb', '#4bc0c0', '#ffce56', '#ff6384']
            }]
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: 'تحويل السكريات إلى إيثانول' } }
        }
    });
    
    // رسم 4: التكاليف والإيرادات
    const ctx4 = document.getElementById('costRevenueChart').getContext('2d');
    new Chart(ctx4, {
        type: 'doughnut',
        data: {
            labels: ['تكلفة المواد', 'الإنزيمات', 'الطاقة', 'العمالة', 'تكاليف أخرى', 'صافي الربح'],
            datasets: [{
                data: [
                    results.dailyFeedCost,
                    results.dailyEnzymeCost,
                    results.dailyUtilityCost,
                    results.dailyLaborCost,
                    results.dailyOperating,
                    Math.max(0, results.dailyProfit)
                ],
                backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#4caf50']
            }]
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: 'توزيع التكاليف والإيرادات' } }
        }
    });
    
    document.getElementById('chartEfficiency').style.display = 'block';
    document.getElementById('chartFeed').style.display = 'block';
    document.getElementById('additionalCharts').style.display = 'grid';
}

// الدالة الرئيسية
function runSimulation() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';
    
    try {
        // قراءة المدخلات
        const feedRate = parseFloat(document.getElementById('feedRate').value);
        const pretreatEff = parseFloat(document.getElementById('pretreatEff').value);
        const hydrolyEff = parseFloat(document.getElementById('hydrolyEff').value);
        const fermentEff = parseFloat(document.getElementById('fermentEff').value);
        const ethPrice = parseFloat(document.getElementById('ethPrice').value);
        const feedCost = parseFloat(document.getElementById('feedCost').value);
        const enzymeCost = parseFloat(document.getElementById('enzymeCost').value);
        const annualCost = parseFloat(document.getElementById('annualCost').value);
        const sensMin = parseFloat(document.getElementById('sensMin').value);
        const sensMax = parseFloat(document.getElementById('sensMax').value);
        const feedRange = parseFloat(document.getElementById('feedRange').value);
        
        // التحقق من المدخلات
        if (isNaN(feedRate) || feedRate <= 0) throw new Error('الرجاء إدخال كمية مواد خام صحيحة');
        if (pretreatEff < 0.5 || pretreatEff > 1.0) throw new Error('كفاءة المعالجة يجب أن تكون بين 0.5 و 1.0');
        
        // عرض القيم الثابتة
        document.getElementById('constants-display').innerHTML = `
            السليلوز: ${(CONSTANTS.celluloseFraction*100).toFixed(0)}% | 
            الهيميسليلوز: ${(CONSTANTS.hemicelluloseFraction*100).toFixed(0)}% | 
            اللجنين: ${(CONSTANTS.ligninFraction*100).toFixed(0)}% | 
            الرطوبة: ${(CONSTANTS.moisture*100).toFixed(0)}%
        `;
        
        // تشغيل المحاكاة الرئيسية
        const results = simulateScenario(feedRate, pretreatEff, hydrolyEff, fermentEff,
                                        ethPrice, feedCost, enzymeCost, annualCost);
        
        // تحليل الحساسية
        const effData = advancedSensitivity({
            feedRate, pretreatEff, hydrolyEff, fermentEff,
            ethPrice, feedCost, enzymeCost, annualCost,
            sensMin, sensMax
        });
        
        const feedData = feedRateAnalysis({
            feedRate, pretreatEff, hydrolyEff, fermentEff,
            ethPrice, feedCost, enzymeCost, annualCost, feedRange
        });
        
        // عرض النتائج والرسوم
        displayResults(results);
        drawCharts(effData, feedData, results);
        
    } catch (error) {
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = error.message;
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// تشغيل المحاكاة عند تحميل الصفحة
window.onload = function() {
    runSimulation();
};
