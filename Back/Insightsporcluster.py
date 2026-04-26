"""
Hey Banco — Visualizador de Insights por Cluster
================================================
Genera un reporte visual con insights y recomendaciones para el chatbot
del banco, clasificados por cluster de cliente.

Uso:
    python hey_cluster_insights.py
    python hey_cluster_insights.py --cluster "Cliente premium"
    python hey_cluster_insights.py --chatbot --cluster "Jóvenes digitales"
"""

import argparse
import textwrap
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import numpy as np

matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.spines.top'] = False
matplotlib.rcParams['axes.spines.right'] = False

# ─────────────────────────────────────────────
# DATOS POR CLUSTER
# ─────────────────────────────────────────────

CLUSTERS = {
    "Jóvenes digitales": {
        "color": "#7F77DD",
        "color_light": "#EEEDFE",
        "emoji": "📱",
        "n": 4882,
        "pct": 32.5,
        "metricas": {
            "Edad promedio": "32 años",
            "Ingreso mensual": "$19,339 MXN",
            "Transacciones": "56.6 / mes",
            "Score Buró": "577",
            "Satisfacción": "7.4 / 10",
            "Saldo total": "$75,216 MXN",
            "Hey Pro": "51.2%",
            "Cashback total": "$80 MXN",
            "Días sin login": "14 días",
            "Seguro activo": "19.9%",
        },
        "kpis": [
            ("Ingreso", 19339, 53329),
            ("Cashback", 80, 483),
            ("Score Buró", 577, 850),
            ("Satisfacción", 7.4, 10),
            ("Hey Pro %", 51.2, 100),
        ],
        "gasto_categorias": {
            "Servicios digitales": 58.9,
            "Supermercado": 34.5,
            "Transporte": 4.2,
            "Salud": 1.2,
            "Ropa": 1.2,
        },
        "insights": [
            {
                "tipo": "🎯 Comportamiento",
                "titulo": "Nativo 100% digital",
                "detalle": (
                    "El 90% usa iOS o Android. Gasta principalmente en "
                    "servicios digitales (59%) y supermercado (35%). "
                    "Patrón de consumo joven: streaming, apps, vida cotidiana."
                ),
            },
            {
                "tipo": "💳 Crédito",
                "titulo": "Score bajo pero alta actividad",
                "detalle": (
                    "Con score buró de 577 (el más bajo del portafolio), "
                    "pero 56 transacciones mensuales. Ideal para modelos de "
                    "crédito alternativo basados en comportamiento transaccional."
                ),
            },
            {
                "tipo": "📈 Oportunidad",
                "titulo": "Alta adopción Hey Pro, baja en seguros",
                "detalle": (
                    "El 51% ya usa Hey Pro. Sin embargo, solo el 20% tiene "
                    "seguro activo. Ventana para seguros embedded en el flujo "
                    "digital: microseguros, seguro de celular, de viaje."
                ),
            },
            {
                "tipo": "🔔 Retención",
                "titulo": "14 días promedio sin login — monitorear",
                "detalle": (
                    "Aunque es el cluster más grande, el enganche es moderado. "
                    "Acciones push personalizadas (cashback, retos de ahorro) "
                    "pueden aumentar la frecuencia de uso."
                ),
            },
        ],
        "recomendaciones_chatbot": [
            "¡Hola! Veo que usas mucho servicios digitales. ¿Sabías que con Hey Pro puedes obtener cashback en Spotify, Netflix y más?",
            "Tu historial de transacciones te hace candidato a una tarjeta de crédito Hey. ¿Quieres conocer tus opciones sin afectar tu buró?",
            "Tienes $75,216 en saldo. Con Hey Inversiones podrías ganar rendimientos sin moverlo. ¿Te explico cómo funciona?",
            "Protege tu celular por menos de $50/mes con nuestro seguro de dispositivo. ¿Lo activamos en 2 clics?",
            "¿Sabías que con nómina domiciliada en Hey puedes recibir tu sueldo un día antes? Platícame dónde trabajas.",
        ],
    },

    "Empleado de nómina domiciliada": {
        "color": "#1D9E75",
        "color_light": "#E1F5EE",
        "emoji": "🏢",
        "n": 3493,
        "pct": 23.3,
        "metricas": {
            "Edad promedio": "37 años",
            "Ingreso mensual": "$20,573 MXN",
            "Transacciones": "52.3 / mes",
            "Score Buró": "565",
            "Satisfacción": "7.0 / 10",
            "Saldo total": "$82,532 MXN",
            "Nómina dom.": "59.5%",
            "Cashback total": "$61 MXN",
            "Utilización cred.": "54%",
            "Seguro activo": "20.1%",
        },
        "kpis": [
            ("Ingreso", 20573, 53329),
            ("Cashback", 61, 483),
            ("Score Buró", 565, 850),
            ("Satisfacción", 7.0, 10),
            ("Nómina dom. %", 59.5, 100),
        ],
        "gasto_categorias": {
            "Gobierno": 55.7,
            "Restaurante": 41.7,
            "Entretenimiento": 1.4,
            "Retiro cajero": 0.8,
            "Hogar": 0.2,
        },
        "insights": [
            {
                "tipo": "💰 Riesgo",
                "titulo": "Utilización de crédito al 54% — la más alta",
                "detalle": (
                    "Con ingreso estable pero alta utilización, este cluster "
                    "está al límite. Riesgo de mora si hay un choque de ingreso. "
                    "Oportunidad de ofrecer reestructura preventiva o crédito de nómina."
                ),
            },
            {
                "tipo": "🏛️ Comportamiento",
                "titulo": "Gasto concentrado en gobierno y restaurantes",
                "detalle": (
                    "55.7% en pagos de gobierno (impuestos, servicios) y 41.7% "
                    "en restaurantes. Perfil de empleado formal que paga obligaciones "
                    "y come fuera. Poca diversidad de gasto."
                ),
            },
            {
                "tipo": "📈 Oportunidad",
                "titulo": "Solo 20% tiene seguro — el más desprotegido",
                "detalle": (
                    "Siendo asalariados formales, son el segmento con mayor necesidad "
                    "de seguros: vida, gastos médicos, accidentes. La propuesta "
                    "de seguro de nómina es natural y de alta conversión."
                ),
            },
            {
                "tipo": "🎯 Cross-sell",
                "titulo": "Hey Pro solo en 36% — mucho margen",
                "detalle": (
                    "64% aún no tiene Hey Pro. Con ingreso estable y nómina "
                    "domiciliada, la mensualidad de Hey Pro es fácil de absorber. "
                    "Enfocar en beneficios de acceso a crédito preferencial."
                ),
            },
        ],
        "recomendaciones_chatbot": [
            "Tu nómina está domiciliada en Hey. ¡Eso te da acceso a préstamos de nómina con la tasa más baja del mercado!",
            "Veo que tu utilización de crédito está alta. ¿Te ayudo a hacer un plan para bajarla y mejorar tu score?",
            "¿Sabías que con Hey Pro tienes seguro de desempleo incluido? Perfecta protección para un empleado como tú.",
            "Cada quincena que entra tu nómina, Hey puede apartar automáticamente un porcentaje para tu fondo de emergencia. ¿Lo configuramos?",
            "Tienes $82k en cuenta. Si los mueves a Hey Ahorro ganas hasta 11% anual. ¿Cuánto quieres apartar?",
        ],
    },

    "Cliente premium": {
        "color": "#378ADD",
        "color_light": "#E6F1FB",
        "emoji": "⭐",
        "n": 3249,
        "pct": 21.6,
        "metricas": {
            "Edad promedio": "41 años",
            "Ingreso mensual": "$44,734 MXN",
            "Transacciones": "60.4 / mes",
            "Score Buró": "723",
            "Satisfacción": "8.5 / 10",
            "Saldo total": "$279,982 MXN",
            "Hey Pro": "71.4%",
            "Cashback total": "$332 MXN",
            "Txn internac.": "3.0 / mes",
            "Seguro activo": "47.0%",
        },
        "kpis": [
            ("Ingreso", 44734, 53329),
            ("Cashback", 332, 483),
            ("Score Buró", 723, 850),
            ("Satisfacción", 8.5, 10),
            ("Hey Pro %", 71.4, 100),
        ],
        "gasto_categorias": {
            "Supermercado": 59.3,
            "Servicios digitales": 18.6,
            "Viajes": 8.9,
            "Salud": 4.9,
            "Ropa y acc.": 4.5,
            "Tecnología": 2.8,
        },
        "insights": [
            {
                "tipo": "🏆 Valor",
                "titulo": "El cliente más rentable del portafolio",
                "detalle": (
                    "Saldo $280k, cashback $332, satisfacción 8.5/10, Hey Pro 71%. "
                    "Concentra el mayor LTV. Prioridad #1: retención y "
                    "profundización de relación."
                ),
            },
            {
                "tipo": "✈️ Viajes",
                "titulo": "Perfil viajero con 3 txn internacionales/mes",
                "detalle": (
                    "8.9% de gasto en viajes. Demanda beneficios: sala VIP, "
                    "seguro de viaje, sin comisión por tipo de cambio, "
                    "asistencia en el extranjero."
                ),
            },
            {
                "tipo": "💼 Inversión",
                "titulo": "Solo 1.2% usa Hey Inversiones — gran brecha",
                "detalle": (
                    "Con $280k promedio en cuenta débito, hay una oportunidad "
                    "inmediata de mover liquidez a inversión. Un nudge de $10k "
                    "en rendimientos podría ser el detonante."
                ),
            },
            {
                "tipo": "🛡️ Seguros",
                "titulo": "47% con seguro — el más alto, pero ampliable",
                "detalle": (
                    "53% aún sin seguro premium. Con este nivel de activos, "
                    "seguros patrimoniales, de vida con inversión y de salud "
                    "con cobertura amplia son el siguiente paso natural."
                ),
            },
        ],
        "recomendaciones_chatbot": [
            "Como cliente premium, tienes acceso a nuestra sala VIP en el aeropuerto. ¿Tu próximo viaje es pronto?",
            "Tus $280k en cuenta están trabajando poco. Con Hey Inversiones CETES ganas ~11% anual. ¿Movemos una parte?",
            "Veo que viajaste al extranjero recientemente. ¿Sabías que con nuestro seguro de viaje estás cubierto por $0 adicionales?",
            "Tu cashback acumulado es de $332. Puedes canjearlo en viajes, transferirlo o usarlo en Hey Shop. ¿Cuál prefieres?",
            "Tenemos una tarjeta Black con límite de $500k, sin anualidad para clientes premium. ¿Te interesa conocerla?",
        ],
    },

    "Profesionalista de alto ingreso": {
        "color": "#BA7517",
        "color_light": "#FAEEDA",
        "emoji": "👔",
        "n": 2040,
        "pct": 13.6,
        "metricas": {
            "Edad promedio": "42 años",
            "Ingreso mensual": "$53,329 MXN",
            "Transacciones": "64.9 / mes",
            "Score Buró": "694",
            "Satisfacción": "8.2 / 10",
            "Saldo total": "$236,604 MXN",
            "Hey Pro": "56.2%",
            "Cashback total": "$483 MXN",
            "Límite crédito": "$197,618 MXN",
            "Nómina dom.": "11.2%",
        },
        "kpis": [
            ("Ingreso", 53329, 53329),
            ("Cashback", 483, 483),
            ("Score Buró", 694, 850),
            ("Satisfacción", 8.2, 10),
            ("Hey Pro %", 56.2, 100),
        ],
        "gasto_categorias": {
            "Gobierno": 64.5,
            "Restaurante": 21.9,
            "Educación": 4.9,
            "Entretenimiento": 4.7,
            "Hogar": 4.1,
        },
        "insights": [
            {
                "tipo": "💼 Perfil",
                "titulo": "Mayor ingreso ($53k) pero sin nómina domiciliada",
                "detalle": (
                    "Solo 11% tiene nómina domiciliada. Probablemente independientes "
                    "o dueños de negocio. Oportunidad de captura de flujo empresarial: "
                    "cuenta de negocio, nómina de empleados, factoraje."
                ),
            },
            {
                "tipo": "🎓 Educación",
                "titulo": "Gasto en educación diferencia a este cluster",
                "detalle": (
                    "4.9% en educación y 4.7% en entretenimiento cultural. "
                    "Perfil intelectual, receptivo a contenidos de educación financiera, "
                    "inversiones sofisticadas y planificación patrimonial."
                ),
            },
            {
                "tipo": "📊 Crédito",
                "titulo": "Límite de $197k con utilización del 27%",
                "detalle": (
                    "Muy por debajo de su capacidad de endeudamiento. Tiene margen "
                    "para créditos de inversión, hipotecas o líneas empresariales. "
                    "El riesgo crediticio es bajo."
                ),
            },
            {
                "tipo": "📈 Inversión",
                "titulo": "El de mayor cashback ($483) — muy activo",
                "detalle": (
                    "64.9 transacciones al mes con tickets altos ($9,459 promedio). "
                    "El perfil ideal para una tarjeta de crédito con cashback alto "
                    "en restaurantes y educación."
                ),
            },
        ],
        "recomendaciones_chatbot": [
            "Con tus ingresos, un plan de retiro personalizado en Hey puede ahorrarte hasta $180k en impuestos al año. ¿Agendamos una asesoría?",
            "¿Tienes empleados? Con Hey Empresas puedes pagar nómina gratis y dar tarjetas corporativas a tu equipo.",
            "Veo gasto frecuente en educación. Hey tiene planes de ahorro universitario para tus hijos con rendimientos superiores al 10%.",
            "Tu límite de crédito tiene mucho margen. ¿Estás pensando en alguna inversión grande? Podemos ofrecerte un crédito a tasa preferencial.",
            "¿Sabías que puedes deducir el uso de tu tarjeta Hey en gastos de negocio? Te ayudo a configurar una cuenta fiscal.",
        ],
    },

    "Cliente poco activo": {
        "color": "#888780",
        "color_light": "#F1EFE8",
        "emoji": "💤",
        "n": 1361,
        "pct": 9.1,
        "metricas": {
            "Edad promedio": "40 años",
            "Ingreso mensual": "$20,015 MXN",
            "Transacciones": "10.8 / mes",
            "Score Buró": "542",
            "Satisfacción": "5.5 / 10",
            "Saldo total": "$45,533 MXN",
            "Días sin login": "104 días",
            "Hey Pro": "8.8%",
            "Productos activos": "0.7",
            "Seguro activo": "19.3%",
        },
        "kpis": [
            ("Ingreso", 20015, 53329),
            ("Cashback", 1.6, 483),
            ("Score Buró", 542, 850),
            ("Satisfacción", 5.5, 10),
            ("Hey Pro %", 8.8, 100),
        ],
        "gasto_categorias": {
            "Gobierno": 74.6,
            "Restaurante": 10.7,
            "Salud": 5.4,
            "Ropa": 4.5,
            "Supermercado": 4.5,
        },
        "insights": [
            {
                "tipo": "🚨 Churn",
                "titulo": "104 días sin login — riesgo de abandono crítico",
                "detalle": (
                    "El promedio de días sin abrir la app es 7x mayor que otros "
                    "clusters. Satisfacción de 5.5/10. Acción urgente: campaña "
                    "de reactivación con incentivo económico inmediato."
                ),
            },
            {
                "tipo": "📱 Fricción",
                "titulo": "40% usa Huawei — posible barrera de app",
                "detalle": (
                    "Huawei no tiene Google Play desde 2020. La experiencia de "
                    "descarga e instalación es compleja. Evaluar mini-app o "
                    "versión web progresiva (PWA) para este segmento."
                ),
            },
            {
                "tipo": "🏛️ Comportamiento",
                "titulo": "Hey como cuenta de paso (74% en gobierno)",
                "detalle": (
                    "Usan Hey exclusivamente para pagar trámites gubernamentales. "
                    "No han descubierto el ecosistema. El mensaje de valor no ha "
                    "llegado. Se requiere comunicación básica y onboarding reactivo."
                ),
            },
            {
                "tipo": "🛒 Activación",
                "titulo": "0.7 productos activos — casi sin engagement",
                "detalle": (
                    "Solo cuenta débito. Ofrecer un producto de fácil adopción "
                    "como Hey Shop con cupón, o ahorro automático de $50/semana, "
                    "puede ser el primer gancho para retenerlos."
                ),
            },
        ],
        "recomendaciones_chatbot": [
            "¡Hola, te extrañamos! Han pasado más de 3 meses desde tu última visita. Por regresar, te regalamos $50 de cashback en tu próxima compra.",
            "Notamos que usas Hey principalmente para pagos de gobierno. ¿Sabías que también puedes pagar servicios, recargas y más sin salir de la app?",
            "¿Todo bien? Tu satisfacción nos importa. Si tuviste algún problema, cuéntanoslo y lo resolvemos ahora mismo.",
            "Configura tu pago de CFE, Telmex o agua en Hey y nunca más te quedas sin servicio por olvidar pagar.",
            "¿Cuál es la razón por la que no has usado Hey últimamente? Tu feedback nos ayuda a mejorar.",
        ],
    },
}

ORDEN_CLUSTERS = [
    "Jóvenes digitales",
    "Empleado de nómina domiciliada",
    "Cliente premium",
    "Profesionalista de alto ingreso",
    "Cliente poco activo",
]


# ─────────────────────────────────────────────
# HELPERS DE VISUALIZACIÓN
# ─────────────────────────────────────────────

def wrap(text, width=62):
    return "\n".join(textwrap.wrap(text, width))


def draw_rounded_box(ax, x, y, w, h, color, alpha=1.0, lw=0):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.01",
        facecolor=color, alpha=alpha,
        edgecolor="none", linewidth=lw,
        transform=ax.transAxes, clip_on=False,
    )
    ax.add_patch(box)


def ax_off(ax):
    ax.axis("off")


# ─────────────────────────────────────────────
# PÁGINA DE RESUMEN GENERAL
# ─────────────────────────────────────────────

def plot_resumen_general():
    fig = plt.figure(figsize=(16, 10), facecolor="#FAFAF8")
    fig.suptitle(
        "Hey Banco — Análisis de Clusters de Clientes",
        fontsize=20, fontweight="bold", color="#1a1a1a", y=0.97,
    )

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35,
                           top=0.90, bottom=0.07, left=0.06, right=0.97)

    # ── Gráfico de distribución (donut) ─────────────────
    ax_donut = fig.add_subplot(gs[0, 0])
    sizes = [d["n"] for d in [CLUSTERS[c] for c in ORDEN_CLUSTERS]]
    colors = [d["color"] for d in [CLUSTERS[c] for c in ORDEN_CLUSTERS]]
    labels_short = ["Jóvenes\ndigitales", "Nómina\ndom.", "Premium", "Profesionalista", "Poco\nactivo"]
    wedges, _ = ax_donut.pie(
        sizes, colors=colors, startangle=90,
        wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2),
    )
    ax_donut.text(0, 0, "15,025\nclientes", ha="center", va="center",
                  fontsize=11, fontweight="bold", color="#333")
    ax_donut.set_title("Distribución por cluster", fontsize=11, pad=8, color="#444")
    legend_handles = [mpatches.Patch(color=colors[i], label=f"{labels_short[i].replace(chr(10),' ')} ({CLUSTERS[ORDEN_CLUSTERS[i]]['pct']}%)")
                      for i in range(5)]
    ax_donut.legend(handles=legend_handles, loc="lower center",
                    bbox_to_anchor=(0.5, -0.28), ncol=2, fontsize=8,
                    frameon=False, labelcolor="#444")

    # ── Ingreso mensual promedio ─────────────────────────
    ax_ing = fig.add_subplot(gs[0, 1])
    nombres = [ORDEN_CLUSTERS[i].replace(" de ", "\nde ").replace("Profesionalista de\nalto ingreso", "Profesionalista\nalto ingreso") for i in range(5)]
    ingresos = [CLUSTERS[c]["metricas"].get("Ingreso mensual", "$0 MXN") for c in ORDEN_CLUSTERS]
    vals_ing = [19339, 20573, 44734, 53329, 20015]
    barras = ax_ing.barh(range(5), vals_ing, color=colors, height=0.6, edgecolor="none")
    ax_ing.set_yticks(range(5))
    ax_ing.set_yticklabels(nombres, fontsize=8, color="#444")
    ax_ing.invert_yaxis()
    ax_ing.set_xlabel("MXN / mes", fontsize=8, color="#888")
    ax_ing.tick_params(axis="x", labelsize=8, colors="#888")
    ax_ing.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
    ax_ing.spines["left"].set_visible(False)
    ax_ing.spines["bottom"].set_color("#ddd")
    ax_ing.set_title("Ingreso mensual promedio", fontsize=11, color="#444", pad=8)
    for i, v in enumerate(vals_ing):
        ax_ing.text(v + 500, i, f"${v:,.0f}", va="center", fontsize=8, color="#444")

    # ── Satisfacción y Hey Pro ────────────────────────────
    ax_sat = fig.add_subplot(gs[0, 2])
    sats = [7.4, 7.0, 8.5, 8.2, 5.5]
    hey_pro = [51.2, 36.0, 71.4, 56.2, 8.8]
    x = np.arange(5)
    w = 0.35
    ax_sat.bar(x - w/2, sats, w, label="Satisfacción (/10)", color=colors, alpha=0.9, edgecolor="none")
    ax_sat.bar(x + w/2, [h/10 for h in hey_pro], w, label="Hey Pro % (/100→/10)", color=colors, alpha=0.45, edgecolor="none")
    ax_sat.set_xticks(x)
    ax_sat.set_xticklabels(["Jóvenes", "Nómina", "Premium", "Prof.", "Inactivo"], fontsize=8, color="#444")
    ax_sat.set_ylim(0, 10.5)
    ax_sat.tick_params(axis="y", labelsize=8, colors="#888")
    ax_sat.spines["bottom"].set_color("#ddd")
    ax_sat.set_title("Satisfacción vs Hey Pro", fontsize=11, color="#444", pad=8)
    legend_bars = [
        mpatches.Patch(color="#555", alpha=0.9, label="Satisfacción /10"),
        mpatches.Patch(color="#555", alpha=0.4, label="Hey Pro % ÷10"),
    ]
    ax_sat.legend(handles=legend_bars, fontsize=7, frameon=False, loc="upper left")

    # ── Cashback promedio ─────────────────────────────────
    ax_cash = fig.add_subplot(gs[1, 0])
    cashbacks = [79.8, 61.4, 332.3, 482.9, 1.6]
    bars2 = ax_cash.bar(range(5), cashbacks, color=colors, edgecolor="none", width=0.6)
    ax_cash.set_xticks(range(5))
    ax_cash.set_xticklabels(["Jóvenes", "Nómina", "Premium", "Prof.", "Inactivo"], fontsize=8, color="#444")
    ax_cash.set_ylabel("MXN promedio", fontsize=8, color="#888")
    ax_cash.tick_params(axis="y", labelsize=8, colors="#888")
    ax_cash.spines["bottom"].set_color("#ddd")
    ax_cash.set_title("Cashback total promedio", fontsize=11, color="#444", pad=8)
    for i, v in enumerate(cashbacks):
        ax_cash.text(i, v + 6, f"${v:.0f}", ha="center", fontsize=8, color="#444", fontweight="bold")

    # ── Días sin login ───────────────────────────────────
    ax_login = fig.add_subplot(gs[1, 1])
    dias = [14, 9, 7, 7, 104.6]
    bar_colors = [c if d < 30 else "#E24B4A" for c, d in zip(colors, dias)]
    ax_login.bar(range(5), dias, color=bar_colors, edgecolor="none", width=0.6)
    ax_login.set_xticks(range(5))
    ax_login.set_xticklabels(["Jóvenes", "Nómina", "Premium", "Prof.", "Inactivo"], fontsize=8, color="#444")
    ax_login.set_ylabel("Días promedio", fontsize=8, color="#888")
    ax_login.tick_params(axis="y", labelsize=8, colors="#888")
    ax_login.spines["bottom"].set_color("#ddd")
    ax_login.set_title("Días promedio sin login", fontsize=11, color="#444", pad=8)
    for i, v in enumerate(dias):
        ax_login.text(i, v + 1.5, f"{v:.0f}d", ha="center", fontsize=8,
                      color="#E24B4A" if v > 30 else "#444", fontweight="bold")

    # ── Score Buró ────────────────────────────────────────
    ax_buro = fig.add_subplot(gs[1, 2])
    scores = [577, 565, 723, 694, 542]
    ax_buro.barh(range(5), scores, color=colors, edgecolor="none", height=0.6)
    ax_buro.set_yticks(range(5))
    ax_buro.set_yticklabels(["Jóvenes", "Nómina", "Premium", "Prof.", "Inactivo"],
                             fontsize=8, color="#444")
    ax_buro.invert_yaxis()
    ax_buro.set_xlabel("Score Buró (850 = máx)", fontsize=8, color="#888")
    ax_buro.tick_params(axis="x", labelsize=8, colors="#888")
    ax_buro.spines["left"].set_visible(False)
    ax_buro.spines["bottom"].set_color("#ddd")
    ax_buro.axvline(700, color="#E24B4A", lw=1.2, ls="--", alpha=0.6)
    ax_buro.set_title("Score Buró promedio", fontsize=11, color="#444", pad=8)
    ax_buro.set_xlim(500, 800)
    for i, v in enumerate(scores):
        ax_buro.text(v + 4, i, str(v), va="center", fontsize=8, color="#444")

    plt.savefig("/mnt/user-data/outputs/hey_resumen_general.png", dpi=150,
                bbox_inches="tight", facecolor="#FAFAF8")
    plt.close()
    print("✓ Guardado: hey_resumen_general.png")


# ─────────────────────────────────────────────
# PÁGINA DE CLUSTER INDIVIDUAL
# ─────────────────────────────────────────────

def plot_cluster(nombre_cluster):
    data = CLUSTERS[nombre_cluster]
    color = data["color"]
    color_light = data["color_light"]

    fig = plt.figure(figsize=(16, 12), facecolor="#FAFAF8")

    # Header
    fig.text(0.04, 0.96, f"{data['emoji']}  {nombre_cluster}",
             fontsize=22, fontweight="bold", color=color, va="top")
    fig.text(0.04, 0.925,
             f"{data['n']:,} clientes  ·  {data['pct']}% de la base",
             fontsize=13, color="#777", va="top")

    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.38,
                           top=0.88, bottom=0.05, left=0.04, right=0.97)

    # ── Métricas clave (10 KPIs en grid 2x5) ────────────
    ax_met = fig.add_subplot(gs[0, :2])
    ax_off(ax_met)
    metricas = list(data["metricas"].items())
    cols, rows = 5, 2
    for idx, (label, val) in enumerate(metricas[:10]):
        col = idx % cols
        row = idx // cols
        x0 = col / cols
        y0 = 1 - (row + 1) / rows
        w, h = 0.92 / cols, 0.42
        rect = FancyBboxPatch((x0 + 0.005, y0 + 0.04), w - 0.01, h,
                               boxstyle="round,pad=0.02",
                               facecolor=color_light, edgecolor="none",
                               transform=ax_met.transAxes, clip_on=False)
        ax_met.add_patch(rect)
        ax_met.text(x0 + w/2, y0 + 0.04 + h * 0.72, val,
                    ha="center", va="center", fontsize=11, fontweight="bold",
                    color=color, transform=ax_met.transAxes)
        ax_met.text(x0 + w/2, y0 + 0.04 + h * 0.22, label,
                    ha="center", va="center", fontsize=8, color="#666",
                    transform=ax_met.transAxes)
    ax_met.set_title("Métricas clave", fontsize=11, color="#444", pad=6, loc="left")

    # ── Radar / KPIs relativos ────────────────────────────
    ax_kpi = fig.add_subplot(gs[0, 2])
    kpis = data["kpis"]
    labels_kpi = [k[0] for k in kpis]
    vals_norm = [k[1] / k[2] for k in kpis]
    x = np.arange(len(kpis))
    bars = ax_kpi.barh(x, vals_norm, color=color, edgecolor="none", height=0.55, alpha=0.85)
    ax_kpi.set_yticks(x)
    ax_kpi.set_yticklabels(labels_kpi, fontsize=9, color="#444")
    ax_kpi.set_xlim(0, 1.15)
    ax_kpi.set_xlabel("vs máximo del portafolio", fontsize=8, color="#888")
    ax_kpi.tick_params(axis="x", labelsize=8, colors="#888")
    ax_kpi.spines["left"].set_visible(False)
    ax_kpi.spines["bottom"].set_color("#ddd")
    ax_kpi.invert_yaxis()
    for i, v in enumerate(vals_norm):
        ax_kpi.text(v + 0.02, i, f"{v*100:.0f}%", va="center", fontsize=8, color="#444")
    ax_kpi.set_title("Posición relativa al portafolio", fontsize=11, color="#444", pad=6)

    # ── Gasto por categoría ───────────────────────────────
    ax_gasto = fig.add_subplot(gs[1, 0])
    cats = list(data["gasto_categorias"].keys())
    vals_g = list(data["gasto_categorias"].values())
    pal = [color] + [color + "99", color + "66", color + "44", color + "22"]
    # usa distintos niveles de opacidad
    alphas = np.linspace(0.95, 0.3, len(cats))
    for i in range(len(cats)):
        ax_gasto.barh(i, vals_g[i], color=color, alpha=float(alphas[i]),
                      edgecolor="none", height=0.6)
    ax_gasto.set_yticks(range(len(cats)))
    ax_gasto.set_yticklabels(cats, fontsize=9, color="#444")
    ax_gasto.invert_yaxis()
    ax_gasto.set_xlabel("% del gasto total", fontsize=8, color="#888")
    ax_gasto.tick_params(axis="x", labelsize=8, colors="#888")
    ax_gasto.spines["left"].set_visible(False)
    ax_gasto.spines["bottom"].set_color("#ddd")
    ax_gasto.set_title("Distribución de gasto (MCC)", fontsize=11, color="#444", pad=6)
    for i, v in enumerate(vals_g):
        ax_gasto.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=8, color="#444")

    # ── Insights ──────────────────────────────────────────
    insights = data["insights"]
    for idx, ins in enumerate(insights):
        col = idx % 2 + 1
        row = idx // 2 + 1
        ax_ins = fig.add_subplot(gs[row, col])
        ax_off(ax_ins)

        # Caja de fondo
        rect = FancyBboxPatch((0, 0), 1, 1,
                               boxstyle="round,pad=0.02",
                               facecolor=color_light, edgecolor=color,
                               linewidth=0.8,
                               transform=ax_ins.transAxes, clip_on=False)
        ax_ins.add_patch(rect)

        ax_ins.text(0.04, 0.92, ins["tipo"],
                    transform=ax_ins.transAxes, fontsize=8,
                    color=color, va="top", fontweight="bold")
        ax_ins.text(0.04, 0.78, ins["titulo"],
                    transform=ax_ins.transAxes, fontsize=10,
                    color="#222", va="top", fontweight="bold",
                    wrap=True)
        # Línea separadora
        ax_ins.plot([0.04, 0.96], [0.68, 0.68], color=color, lw=0.6, alpha=0.5,
                    transform=ax_ins.transAxes)
        lines = textwrap.wrap(ins["detalle"], 52)
        y_txt = 0.60
        for line in lines:
            ax_ins.text(0.04, y_txt, line, transform=ax_ins.transAxes,
                        fontsize=8.5, color="#444", va="top")
            y_txt -= 0.115

    plt.savefig(f"/mnt/user-data/outputs/hey_cluster_{nombre_cluster.replace(' ','_').replace('ó','o').replace('é','e').replace('ó','o')}.png",
                dpi=150, bbox_inches="tight", facecolor="#FAFAF8")
    plt.close()
    nombre_safe = nombre_cluster.replace(' ', '_')
    print(f"✓ Guardado: hey_cluster_{nombre_safe}.png")


# ─────────────────────────────────────────────
# TARJETA DE CHATBOT
# ─────────────────────────────────────────────

def plot_chatbot(nombre_cluster):
    data = CLUSTERS[nombre_cluster]
    color = data["color"]
    color_light = data["color_light"]
    recs = data["recomendaciones_chatbot"]

    fig, ax = plt.subplots(figsize=(10, 9), facecolor="#FAFAF8")
    ax_off(ax)

    # Header
    fig.text(0.05, 0.97, f"🤖  Recomendaciones para el chatbot",
             fontsize=16, fontweight="bold", color="#222", va="top")
    fig.text(0.05, 0.915, f"Cluster: {data['emoji']} {nombre_cluster}  ·  {data['n']:,} clientes",
             fontsize=11, color=color, va="top", fontweight="bold")

    # Burbuja de usuario (simulación de chat)
    n = len(recs)
    total_h = 0.78
    step = total_h / n
    y_start = 0.86

    for i, rec in enumerate(recs):
        y = y_start - i * step
        lines = textwrap.wrap(rec, 72)
        box_h = max(0.07, len(lines) * 0.033 + 0.045)

        # Burbuja del bot
        bubble = FancyBboxPatch(
            (0.05, y - box_h), 0.88, box_h,
            boxstyle="round,pad=0.015",
            facecolor=color_light, edgecolor=color,
            linewidth=0.8,
            transform=fig.transFigure, clip_on=False,
        )
        fig.add_artist(bubble)

        # Número
        fig.text(0.065, y - box_h / 2, f"{i+1}",
                 fontsize=11, fontweight="bold", color=color,
                 va="center", ha="center", transform=fig.transFigure)

        # Texto
        y_txt = y - 0.022
        for line in lines:
            fig.text(0.10, y_txt, line, fontsize=9.5, color="#333",
                     va="top", transform=fig.transFigure)
            y_txt -= 0.032

    # Footer
    fig.text(0.05, 0.02,
             f"Generado por: hey_cluster_insights.py  |  Cluster detectado automáticamente por el modelo ML",
             fontsize=7.5, color="#aaa", va="bottom")

    nombre_safe = nombre_cluster.replace(' ', '_').replace('ó','o').replace('é','e')
    fname = f"/mnt/user-data/outputs/hey_chatbot_{nombre_safe}.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight", facecolor="#FAFAF8")
    plt.close()
    print(f"✓ Guardado: hey_chatbot_{nombre_safe}.png")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Visualizador de insights por cluster — Hey Banco"
    )
    parser.add_argument(
        "--cluster",
        type=str,
        default=None,
        help="Nombre del cluster a visualizar (si no se especifica, genera todos)",
    )
    parser.add_argument(
        "--chatbot",
        action="store_true",
        help="Genera la tarjeta de recomendaciones para chatbot",
    )
    parser.add_argument(
        "--resumen",
        action="store_true",
        default=False,
        help="Genera solo el resumen general",
    )
    args = parser.parse_args()

    if args.resumen:
        plot_resumen_general()
        return

    if args.cluster:
        # Validar nombre
        matches = [c for c in CLUSTERS if args.cluster.lower() in c.lower()]
        if not matches:
            print(f"Cluster '{args.cluster}' no encontrado.")
            print(f"Opciones: {list(CLUSTERS.keys())}")
            return
        nombre = matches[0]
        if args.chatbot:
            plot_chatbot(nombre)
        else:
            plot_cluster(nombre)
        return

    # Genera todo
    print("Generando visualizaciones completas...")
    plot_resumen_general()
    for c in ORDEN_CLUSTERS:
        plot_cluster(c)
        plot_chatbot(c)
    print("\n✅ Listo. Archivos generados en /mnt/user-data/outputs/")


if __name__ == "__main__":
    main()