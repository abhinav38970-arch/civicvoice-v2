"""Durable catalog display strings for languages when live MT is unavailable.

Titles/snippets used by /api/notices and /api/ballots. Loaded into the
translation glossary and Postgres text_translations so language switches
do not depend on free-API quotas.
"""

from __future__ import annotations

import logging

from app.config import SUPPORTED_LANGUAGES
from app.translate import reset_circuits, store_translation, translate_text

logger = logging.getLogger(__name__)

# All dashboard languages except English (source language).
CATALOG_LANGS: tuple[str, ...] = tuple(lang for lang in SUPPORTED_LANGUAGES if lang != "en")

# English source → { lang: translation }
CATALOG_TITLES: dict[str, dict[str, str]] = {
    "Alameda County Registrar of Voters": {
        "hi": "अलामेडा काउंटी रजिस्ट्रार ऑफ़ वोटर्स",
        "es": "Registrador de votantes del condado de Alameda",
        "zh": "阿拉米达县选民登记处",
    },
    "California Vote by Mail information": {
        "hi": "मेल द्वारा कैलिफ़ोर्निया वोट की जानकारी",
        "es": "Información de voto por correo de California",
        "zh": "加州邮寄投票信息",
    },
    "California Voter Information Guides": {
        "hi": "कैलिफ़ोर्निया मतदाता सूचना मार्गदर्शिकाएँ",
        "es": "Guías de información para votantes de California",
        "zh": "加州选民信息指南",
    },
    "California Elections and Voter Information": {
        "hi": "कैलिफ़ोर्निया चुनाव और मतदाता जानकारी",
        "es": "Elecciones e información para votantes de California",
        "zh": "加州选举与选民信息",
    },
    "California Official Voter Information Guide": {
        "hi": "कैलिफ़ोर्निया आधिकारिक मतदाता सूचना गाइड",
        "es": "Guía oficial de información para votantes de California",
        "zh": "加州官方选民信息指南",
    },
    "November ballot: Measure H library funding overview": {
        "hi": "नवंबर मतपत्र: मेज़र H लाइब्रेरी फंडिंग अवलोकन",
        "es": "Boleta de noviembre: resumen del financiamiento de bibliotecas de la Medida H",
        "zh": "11月选票：措施 H 图书馆资金概览",
    },
    "Alameda County voter guide — Fremont contests": {
        "hi": "अलामेडा काउंटी मतदाता गाइड — फ़्रीमॉन्ट चुनाव",
        "es": "Guía del votante del condado de Alameda — contiendas de Fremont",
        "zh": "阿拉米达县选民指南 — 弗里蒙特竞选",
    },
    "Fremont City Council approves housing element update": {
        "hi": "फ़्रीमॉन्ट सिटी काउंसिल ने हाउसिंग एलिमेंट अपडेट मंज़ूर किया",
        "es": "El Concejo de Fremont aprueba la actualización del elemento de vivienda",
        "zh": "弗里蒙特市议会通过住房要素更新",
    },
    "Fremont launches street resurfacing on Warm Springs Boulevard": {
        "hi": "फ़्रीमॉन्ट ने वार्म स्प्रिंग्स बुलेवार्ड पर सड़क मरम्मत शुरू की",
        "es": "Fremont inicia el resurfacing en Warm Springs Boulevard",
        "zh": "弗里蒙特启动温泉大道道路重铺",
    },
    "Parks and Recreation opens Central Park picnic reservations": {
        "hi": "पार्क्स एंड रिक्रिएशन ने सेंट्रल पार्क पिकनिक आरक्षण खोले",
        "es": "Parques y Recreación abre reservas de picnic en Central Park",
        "zh": "公园与娱乐开放中央公园野餐预约",
    },
    "Council study session on downtown parking and transit": {
        "hi": "डाउनटाउन पार्किंग और ट्रांज़िट पर काउंसिल अध्ययन सत्र",
        "es": "Sesión de estudio del Concejo sobre estacionamiento y tránsito del centro",
        "zh": "市议会研究市中心停车与公交",
    },
    "Fremont Fire Department reminds residents of wildfire preparedness": {
        "hi": "फ़्रीमॉन्ट फायर विभाग ने जंगल की आग की तैयारी की याद दिलाई",
        "es": "Bomberos de Fremont recuerdan prepararse ante incendios forestales",
        "zh": "弗里蒙特消防局提醒居民做好野火准备",
    },
    "City job fair connects residents with local employers": {
        "hi": "शहर का जॉब फेयर निवासियों को स्थानीय नियोक्ताओं से जोड़ता है",
        "es": "Feria de empleo conecta a residentes con empleadores locales",
        "zh": "市招聘会连接居民与本地雇主",
    },
    "Unified School District updates after-school education programs": {
        "hi": "यूनिफ़ाइड स्कूल डिस्ट्रिक्ट ने आफ्टर-स्कूल शिक्षा कार्यक्रम अपडेट किए",
        "es": "El distrito escolar actualiza programas educativos después de clases",
        "zh": "联合学区更新课后教育项目",
    },
    "County health clinic expands walk-in hours": {
        "hi": "काउंटी स्वास्थ्य क्लिनिक ने वॉक-इन घंटे बढ़ाए",
        "es": "La clínica de salud del condado amplía horarios sin cita",
        "zh": "县卫生诊所延长无需预约时段",
    },
    "CalFresh and immigration assistance workshop at the library": {
        "hi": "लाइब्रेरी में कैलफ़्रेश और इमिग्रेशन सहायता कार्यशाला",
        "es": "Taller de CalFresh y asistencia de inmigración en la biblioteca",
        "zh": "图书馆举办 CalFresh 与移民协助讲座",
    },
    "City of Fremont (sample)": {
        "hi": "फ़्रीमॉन्ट शहर (नमूना)",
        "es": "Ciudad de Fremont (muestra)",
        "zh": "弗里蒙特市（示例）",
    },
    "California Official Voter Guide": {
        "hi": "कैलिफ़ोर्निया आधिकारिक मतदाता गाइड",
        "es": "Guía oficial del votante de California",
        "zh": "加州官方选民指南",
    },
    "California Secretary of State — Voter Information Guides": {
        "hi": "कैलिफ़ोर्निया राज्य सचिव — मतदाता सूचना मार्गदर्शिकाएँ",
        "es": "Secretario de Estado de California — Guías del votante",
        "zh": "加州州务卿 — 选民信息指南",
    },
    "California Secretary of State — Elections": {
        "hi": "कैलिफ़ोर्निया राज्य सचिव — चुनाव",
        "es": "Secretario de Estado de California — Elecciones",
        "zh": "加州州务卿 — 选举",
    },
    "Alameda County — Vote by Mail & ballot status": {
        "hi": "अलामेडा काउंटी — मेल द्वारा मतदान और मतपत्र स्थिति",
        "es": "Condado de Alameda — Voto por correo y estado de la boleta",
        "zh": "阿拉米达县 — 邮寄投票与选票状态",
    },
}

CATALOG_SNIPPETS: dict[str, dict[str, str]] = {
    "Measure H asks voters whether to renew a parcel tax that supports Fremont libraries. CivicVoice summarizes official language only and does not recommend how to vote.": {
        "hi": "मेज़र H मतदाताओं से पूछता है कि क्या वे फ़्रीमॉन्ट पुस्तकालयों के लिए पार्सल टैक्स नवीनीकृत करें। CivicVoice केवल आधिकारिक भाषा का सारांश देता है और वोट की सलाह नहीं देता।",
        "es": "La Medida H pregunta a los votantes si renovar un impuesto predial que apoya las bibliotecas de Fremont. CivicVoice solo resume el lenguaje oficial y no recomienda cómo votar.",
        "zh": "措施 H 询问选民是否续期支持弗里蒙特图书馆的地块税。CivicVoice 仅总结官方措辞，不建议如何投票。",
    },
    "This voter guide lists candidates and measures for Fremont residents. Check your ballot for the exact contests that appear in your precinct.": {
        "hi": "यह मतदाता गाइड फ़्रीमॉन्ट निवासियों के लिए उम्मीदवार और उपाय सूचीबद्ध करता है। अपने मतपत्र पर अपने प्रिसींक्ट के सटीक चुनाव देखें।",
        "es": "Esta guía del votante enumera candidatos y medidas para residentes de Fremont. Revise su boleta para las contiendas exactas de su precinto.",
        "zh": "本选民指南列出弗里蒙特居民的候选人和措施。请查看您选票上本选区的确切竞选项目。",
    },
    "Community services offers benefits enrollment help covering CalFresh, Medi-Cal, and immigration resource referrals.": {
        "hi": "सामुदायिक सेवाएँ कैलफ़्रेश, मेडी-कैल और इमिग्रेशन संसाधन रेफ़रल सहित लाभ नामांकन में मदद करती हैं।",
        "es": "Servicios comunitarios ofrecen ayuda para inscripción en beneficios, incluyendo CalFresh, Medi-Cal y referencias de inmigración.",
        "zh": "社区服务提供福利报名协助，涵盖 CalFresh、Medi-Cal 以及移民资源转介。",
    },
    "Fremont Economic Development hosts a jobs and business career fair at the community center for residents seeking employment.": {
        "hi": "फ़्रीमॉन्ट इकोनॉमिक डेवलपमेंट रोज़गार चाहने वाले निवासियों के लिए कम्युनिटी सेंटर में जॉब्स और बिज़नेस करियर फेयर आयोजित करता है।",
        "es": "Desarrollo Económico de Fremont organiza una feria de empleo y negocios en el centro comunitario para residentes que buscan trabajo.",
        "zh": "弗里蒙特经济发展部门在社区中心为求职居民举办就业与商业招聘会。",
    },
    "Council members reviewed options to expand downtown parking while improving transit access near the Fremont BART station.": {
        "hi": "काउंसिल सदस्यों ने फ़्रीमॉन्ट BART स्टेशन के पास ट्रांज़िट पहुँच सुधारते हुए डाउनटाउन पार्किंग बढ़ाने के विकल्पों की समीक्षा की।",
        "es": "Los miembros del Concejo revisaron opciones para ampliar el estacionamiento del centro mejorando el acceso al tránsito cerca de la estación BART de Fremont.",
        "zh": "市议员审议了在改善弗里蒙特 BART 站附近公交可达性的同时扩大市中心停车的方案。",
    },
    "Alameda County health services expand clinic hours for vaccines and wellness visits in Fremont.": {
        "hi": "अलामेडा काउंटी स्वास्थ्य सेवाएँ फ़्रीमॉन्ट में टीके और वेलनेस विज़िट के लिए क्लिनिक घंटे बढ़ाती हैं।",
        "es": "Los servicios de salud del condado de Alameda amplían el horario de clínicas para vacunas y visitas de bienestar en Fremont.",
        "zh": "阿拉米达县卫生服务延长弗里蒙特诊所时段，覆盖疫苗与健康就诊。",
    },
    "On March 10, the Fremont City Council approved an update to the Housing Element. The plan outlines how the city will meet state housing goals over the next eight years.": {
        "hi": "10 मार्च को फ़्रीमॉन्ट सिटी काउंसिल ने हाउसिंग एलिमेंट का अपडेट मंज़ूर किया। योजना बताती है कि शहर अगले आठ वर्षों में राज्य के आवास लक्ष्यों को कैसे पूरा करेगा।",
        "es": "El 10 de marzo, el Concejo de Fremont aprobó una actualización del Elemento de Vivienda. El plan indica cómo la ciudad cumplirá las metas estatales de vivienda en los próximos ocho años.",
        "zh": "3月10日，弗里蒙特市议会通过住房要素更新。该计划说明城市未来八年如何达成州住房目标。",
    },
    "The Fremont Fire Department urges public safety awareness during fire season. Keep emergency kits ready and clear brush near homes.": {
        "hi": "फ़्रीमॉन्ट फायर विभाग आग के मौसम में सार्वजनिक सुरक्षा के प्रति जागरूकता की अपील करता है। इमरजेंसी किट तैयार रखें और घरों के पास झाड़ियाँ साफ़ करें।",
        "es": "El Departamento de Bomberos de Fremont urge conciencia de seguridad pública durante la temporada de incendios. Mantenga kits de emergencia y despeje maleza cerca de las viviendas.",
        "zh": "弗里蒙特消防局敦促居民在火灾季提高公共安全意识。备好应急包，并清理房屋附近灌木。",
    },
    "Public Works will resurface Warm Springs Boulevard between South Grimmer and Mission Boulevard. Lane closures are expected on weekdays from 9 a.m. to 3 p.m.": {
        "hi": "पब्लिक वर्क्स साउथ ग्रिमर और मिशन बुलेवार्ड के बीच वार्म स्प्रिंग्स बुलेवार्ड की सड़क फिर से बिछाएगा। सप्ताह के दिनों में सुबह 9 से दोपहर 3 तक लेन बंद रहने की उम्मीद है।",
        "es": "Obras Públicas resurfacará Warm Springs Boulevard entre South Grimmer y Mission Boulevard. Se esperan cierres de carril entre semana de 9 a.m. a 3 p.m.",
        "zh": "市政工程将重铺南格里默与米申大道之间的温泉大道。预计工作日上午9点至下午3点封闭车道。",
    },
    "Residents can reserve picnic areas at Central Park online. Peak weekend slots for spring fill quickly after the reservation window opens.": {
        "hi": "निवासी सेंट्रल पार्क के पिकनिक क्षेत्र ऑनलाइन आरक्षित कर सकते हैं। वसंत के व्यस्त सप्ताहांत स्लॉट आरक्षण खुलते ही जल्दी भर जाते हैं।",
        "es": "Los residentes pueden reservar áreas de picnic en Central Park en línea. Los horarios de fin de semana de primavera se llenan rápido al abrirse la reserva.",
        "zh": "居民可在线预订中央公园野餐区。春季周末热门时段在预约开放后很快约满。",
    },
    "Fremont Unified shares education updates for students and families on after-school tutoring and campus safety drills.": {
        "hi": "फ़्रीमॉन्ट यूनिफ़ाइड छात्रों और परिवारों के लिए आफ्टर-स्कूल ट्यूशन और कैंपस सुरक्षा अभ्यास पर शिक्षा अपडेट साझा करता है।",
        "es": "Fremont Unified comparte actualizaciones educativas para estudiantes y familias sobre tutoría después de clases y simulacros de seguridad en el campus.",
        "zh": "弗里蒙特联合学区向学生和家庭分享课后辅导与校园安全演练的教育更新。",
    },
    # Display slice (left 220) from the SOS official voter guide ingest.
    "Official Voter Information Guide | California Secretary of State\n\nI, Shirley N. Weber, Secretary of State of the State of California, do hereby certify that the information included herein will be submitted to the electo": {
        "hi": "आधिकारिक मतदाता सूचना गाइड | कैलिफ़ोर्निया राज्य सचिव\n\nमैं, शर्ली एन. वेबर, कैलिफ़ोर्निया राज्य की राज्य सचिव, प्रमाणित करती हूँ कि यहाँ शामिल जानकारी मतदाताओं के समक्ष प्रस्तुत की जाएगी।",
        "es": "Guía oficial de información para votantes | Secretaria de Estado de California\n\nYo, Shirley N. Weber, Secretaria de Estado de California, certifico que la información incluida se presentará ante el electorado.",
        "zh": "官方选民信息指南 | 加州州务卿\n\n我，加州州务卿 Shirley N. Weber，兹证明此处所含信息将提交给选民。",
    },
}

# Fold in pa/ko/vi/tl/fa/ar/pt/ur curated strings.
from app.catalog_i18n_extra import EXTRA_SNIPPETS, EXTRA_TITLES, merge_extra  # noqa: E402

merge_extra(CATALOG_TITLES, EXTRA_TITLES)
merge_extra(CATALOG_SNIPPETS, EXTRA_SNIPPETS)


def register_catalog_glossary() -> int:
    """Merge curated catalog strings into the runtime glossary."""
    from app import translate as tr

    n = 0
    for source, by_lang in {**CATALOG_TITLES, **CATALOG_SNIPPETS}.items():
        for lang, translated in by_lang.items():
            table = tr._GLOSSARY.setdefault(lang, {})
            if table.get(source) != translated:
                table[source] = translated
                n += 1
    return n


def warm_catalog_translations(langs: tuple[str, ...] | None = None) -> dict[str, int]:
    """Persist curated catalog strings into Redis + Postgres + chunk rows."""
    if langs is None:
        langs = CATALOG_LANGS
    register_catalog_glossary()
    reset_circuits()
    stored = 0
    missing = 0
    for source, by_lang in {**CATALOG_TITLES, **CATALOG_SNIPPETS}.items():
        for lang in langs:
            text = by_lang.get(lang)
            if not text:
                missing += 1
                continue
            store_translation(lang, source, text, provider="catalog-seed")
            stored += 1
    if missing:
        logger.warning("catalog i18n missing %s lang entries", missing)
    # Warm active titles, source names, and first-chunk bodies (no live MT).
    try:
        from app.db import get_connection
        from app.translate import persist_chunk_translation

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT d.title AS text FROM documents d
                JOIN sources s ON s.id = d.source_id WHERE s.status = 'active'
                UNION
                SELECT DISTINCT s.name AS text FROM sources s WHERE s.status = 'active'
                """
            ).fetchall()
            chunks = conn.execute(
                """
                SELECT DISTINCT ON (c.document_id) c.id, c.text
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                JOIN sources s ON s.id = d.source_id
                WHERE s.status = 'active' AND c.is_active = true
                ORDER BY c.document_id, c.page NULLS LAST, c.created_at
                """
            ).fetchall()

        for lang in langs:
            for row in rows:
                text = row["text"]
                out = translate_text(text, lang, allow_live=False)
                if out != text:
                    stored += 1
            for ch in chunks:
                body = (ch["text"] or "").strip()
                if not body:
                    continue
                out = translate_text(body, lang, allow_live=False)
                if out == body:
                    # Retry display slice in case only left(220) was seeded.
                    slice220 = body[:220]
                    out220 = translate_text(slice220, lang, allow_live=False)
                    if out220 == slice220:
                        continue
                    store_translation(lang, slice220, out220, provider="catalog-warm")
                    persist_chunk_translation(
                        str(ch["id"]), lang, out220, "catalog-warm"
                    )
                    stored += 1
                    continue
                store_translation(lang, body, out, provider="catalog-warm")
                if len(body) > 220:
                    store_translation(
                        lang, body[:220], out[:220], provider="catalog-warm"
                    )
                persist_chunk_translation(str(ch["id"]), lang, out, "catalog-warm")
                stored += 1
    except Exception as exc:  # noqa: BLE001
        logger.warning("warm catalog scan failed: %s", exc)
    return {"stored": stored}
