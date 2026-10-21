import json
import os

# Классификатор адреса (временные значения, заменить на реальные)
INDEX = "000000"      # почтовый индекс
NASP = "xx"           # код населённого пункта из словаря
ULICA = "bulvar-khudozhnikov"
DOM = "12"            # номер дома (уточнить)
ETAZHI = 10
SEKCII = [("1", 8), ("2", 7), ("3", 6)]  # мельче квартиры -> больше на этаже
NEAKTIVNYE = {210}    # пустые квартиры: окно серое, заявки нельзя

PREF = f"{INDEX}-{NASP}-{ULICA}-{DOM}"

dom = {
    "klassifikator": {
        "indeks": INDEX,
        "nasp": NASP,
        "ulica": ULICA,
        "dom": DOM,
        "format_kod": "indeks-nasp-ulica-dom-sekciya-etazh-kvartira-okno"
    },
    "funkcii": {
        "nablyudateli_vklyucheny": False,
        "obshchiy_chat_doma": True,
        "primechanie": "Наблюдатели из соседних домов отключены, но модель данных их уже поддерживает"
    },
    "dom": {
        "kod": PREF,
        "etazhi": ETAZHI,
        "kvartir_po_dannym": 209,
        "kvartir_v_modeli": 0,
        "primechanie": "Черновик. Расхождение с 209 уточнить по планировке."
    },
    "sekcii": [],
    "territoriya": [
        {"kod": f"{PREF}-dvor-parkovka", "tip": "parkovka"},
        {"kod": f"{PREF}-dvor-shlagbaum", "tip": "vezdnaya_gruppa"},
        {"kod": f"{PREF}-dvor-podval", "tip": "podval"},
        {"kod": f"{PREF}-dvor-ploshchadki", "tip": "detskie_ploshchadki"},
        {"kod": f"{PREF}-dvor-osveshchenie", "tip": "ulichnoe_osveshchenie"},
        {"kod": f"{PREF}-dvor-poliv", "tip": "zona_avtopoliva"},
        {"kod": f"{PREF}-dvor-besedka", "tip": "besedka"},
        {"kod": f"{PREF}-dvor-urny", "tip": "urny"},
        {"kod": f"{PREF}-dvor-lavochki", "tip": "lavochki"},
        {"kod": f"{PREF}-dvor-gazony", "tip": "gazony"}
    ],
    "pravila_vidimosti": {
        "avariya": {
            "cvet": "krasnyi",
            "opisanie_vidno": "vsem",
            "skryt_avtorom": False,
            "kommentarii": "otkryty",
            "uvedomlenie_sekcii": True,
            "ponizit_mozhet": "tolko_moderator"
        },
        "zamechanie": {
            "cvet": "zheltyi",
            "opisanie_vidno": "po_zhelaniyu_avtora",
            "rezhim_tolko_cvet": True,
            "kommentarii": "otkryty"
        },
        "zamki_i_dveri": {
            "cvet": "zheltyi_ili_krasnyi",
            "opisanie_vidno": "tolko_moderatoru_i_zhilcam_kvartiry",
            "primechanie": "Чтобы описание не показывало, что квартира пустует"
        },
        "predlozhenie": {
            "cvet": None,
            "opisanie_vidno": "vsem",
            "spisok": "otdelnyi_spisok_doma_ili_territorii",
            "kommentarii": "otkryty"
        },
        "zelenyi": {
            "vychislyaetsya": "avtomaticheski",
            "uslovie": "vse_zayavki_zakryty_i_podtverzhdeny"
        }
    },
    "gruppy": [
        {
            "kod": f"{INDEX}-{NASP}-{ULICA}",
            "nazvanie": "Бульвар Художников",
            "doma": [DOM, "уточнить_2", "уточнить_3", "уточнить_4", "уточнить_5"],
            "obshchie_obekty": [
                {
                    "kod": f"{INDEX}-{NASP}-{ULICA}-gr-bomboubezhishche-1",
                    "tip": "bombouboezhishche",
                    "obsluzhivaet": [DOM, "уточнить_2"]
                }
            ]
        }
    ]
}

OBSHCHIE = ["vhod", "tambur", "lift", "lestnica", "okna-podezda", "dveri-podezda"]
TIPY = {"vhod": "vkhodnaya_gruppa", "tambur": "tambur", "lift": "lift",
        "lestnica": "lestnica", "okna-podezda": "okna_v_podezde",
        "dveri-podezda": "dveri_v_podezde"}

nomer = 1
for sid, kv in SEKCII:
    s_kod = f"{PREF}-s{sid}"
    sek = {
        "kod": s_kod,
        "nomer": int(sid),
        "kvartir_na_etazh": kv,
        "obshchie_zony": [
            {"kod": f"{s_kod}-{z}", "tip": TIPY[z]} for z in OBSHCHIE
        ],
        "etazhi": []
    }
    for e in range(1, ETAZHI + 1):
        e_kod = f"{s_kod}-e{e}"
        kvs = []
        for _ in range(kv):
            k_kod = f"{e_kod}-k{nomer}"
            kvs.append({
                "kod": k_kod,
                "nomer": nomer,
                "aktivna": nomer not in NEAKTIVNYE,
                "dostup_mest": 2,
                "okna": [{"kod": f"{k_kod}-o1", "storona": "fasad", "zaglushka": True}]
            })
            nomer += 1
        sek["etazhi"].append({
            "kod": e_kod,
            "etazh": e,
            "koridor": {"kod": f"{e_kod}-koridor", "tip": "koridor"},
            "kvartiry": kvs
        })
    dom["sekcii"].append(sek)

dom["dom"]["kvartir_v_modeli"] = nomer - 1

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "dom_draft.json")
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(dom, f, ensure_ascii=False, indent=2)

print("kvartir:", nomer - 1, "neaktivnyh:", len(NEAKTIVNYE))
