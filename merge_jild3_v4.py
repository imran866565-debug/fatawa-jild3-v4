#!/usr/bin/env python3
"""Merge Fatawa Razviya Jild 3 easy-Urdu tashreeh v4 chunks into jild-03.json.

Reads the 14 chunk files listed in chunks-manifest-v4-jild03.json,
concatenates them in order 01 -> 14, derives start_page = min(pages)
where the field is absent, normalises page markers, validates, and
writes {"masail": [...]} to jild-03.json.

ORDER -- chunk order is the order (no quirk, unlike Jild 1 Part 2):
  The v3 merged file ~/workspace/fatawa-app/content/tashreeh/jild-03.json
  has ID order == concatenation order of the v4 chunks 01..14 (verified
  locally by the coordinator: all 242 ids match the v3 sequence exactly).
  Do NOT sort or reorder. Within each chunk, items keep file order.

START_PAGE: every one of the 14 v4 chunks carries start_page ==
  min(pages) for all its items (verified by the coordinator). Note the
  v3 quirk: v3 chunk-10 lacks start_page entirely; the v4 worker added
  start_page = min(pages) for all 12 of its items, so the merged file
  reproduces the v3 merged file (which has start_page == min(pages)
  for all 242 items) exactly. The derivation code below stays as a
  safety net; it is expected to derive 0 items.

MARKER NORMALISATION (the only text transformation): page markers, if
  present, are normalised to the single form [safha N] written with the
  Urdu word for page:
  - lenticular-bracket form (U+3010/U+3011 around the Urdu word for
    page + number) -> [safha N]
  - [short form] -> [safha N]
  - [safha N] stays as-is
  Applied to every string field of every item (jawab, sawal, title,
  notes). The 14 v4 chunks contain ZERO markers of any form (verified
  locally), so normalisation is expected to be a no-op here; the code
  stays so the merge is robust and the "none remain" assertions still
  run. No other text is touched and no markers are invented.
  NOTE: the literal lenticular-bracket characters are written here only
  as U+3010/U+3011 escapes, never as literal characters in this file.

VALIDATION (fails loudly on any violation):
  242 items; ID sequence EXACTLY == the v3 merged file's ID sequence
  (embedded below as V3_IDS, copied verbatim from
  ~/workspace/fatawa-app/content/tashreeh/jild-03.json); pages per item
  identical to v3 (embedded as V3_PAGES, same source, verified against
  the v3 file before pushing); 716 unique pages (min 5, max 756);
  volume_ids == {31}; start_page == min(pages) for every item (after
  derivation); zero empty tashreeh_jawab; no lenticular / short markers
  remain; first id jild3-pesh-lafz, last id jild3-maakhiz-p743.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = "chunks-manifest-v4-jild03.json"

# Concatenation order: chunk files 01 -> 14, in order.
CHUNK_ORDER = [f"jild-03-chunk-{n:02d}.json" for n in range(1, 15)]

EXPECTED_ITEMS = 242
EXPECTED_PAGES = 716
EXPECTED_MIN_PAGE = 5
EXPECTED_MAX_PAGE = 756
EXPECTED_VOLUME_IDS = {31}
EXPECTED_FIRST_ID = "jild3-pesh-lafz"
EXPECTED_LAST_ID = "jild3-maakhiz-p743"

# v3 ID sequence, verbatim from content/tashreeh/jild-03.json.
V3_IDS = ['jild3-pesh-lafz', 'jild3-bahs1-maani-tabiat', 'jild3-bahs2-tabia-raqqat-saylan', 'jild3-bahs2-qawaid-matan-khalt', 'jild3-bahs3-maani-raqqat-saylan', 'jild3-bahs3-tarkib-ajsam', 'jild3-bahs4-hadd-raqqat', 'jild3-qiyas-murakkab-muqaddima-ula', 'jild3-muqaddima-thaniya-tarif-be-jurm', 'jild3-muqaddima-thaniya-aqwal-tahqiq', 'jild3-muqaddima-salisa-istehlak', 'jild3-ghalaba-ghair-bahs-awwal', 'jild3-p91', 'jild3-p101', 'jild3-p102', 'jild3-p105', 'jild3-p112', 'jild3-p115', 'jild3-p121', 'jild3-p123', 'jild3-p126', 'jild3-p134', 'jild3-p141', 'jild3-p145', 'jild3-p149', 'jild3-p151', 'jild3-p153', 'jild3-p155', 'jild3-p159', 'jild3-p161', 'jild3-p163', 'jild3-p164', 'jild3-p165', 'jild3-p169', 'jild3-p172', 'jild3-p174', 'jild3-p175', 'jild3-p176', 'jild3-p178', 'jild3-p180', 'jild3-p182', 'jild3-p184', 'jild3-p187', 'jild3-p189', 'jild3-p191', 'jild3-p201', 'jild3-p206', 'jild3-p210', 'jild3-p212', 'jild3-p215', 'jild3-p219', 'jild3-p223', 'jild3-p229', 'jild3-p235', 'jild3-p241', 'jild3-p245', 'jild3-masala-56-p249', 'jild3-masala-57-p250', 'jild3-masala-58-p250', 'jild3-masala-59-p251', 'jild3-masala-60-p253', 'jild3-masala-61-p254', 'jild3-masala-62-p254', 'jild3-masala-63-p254', 'jild3-masala-64-p255', 'jild3-masala-65-p255', 'jild3-masala-66-p261', 'jild3-masala-67-p261', 'jild3-masala-68-p265', 'jild3-masala-69-p266', 'jild3-masala-70-p267', 'jild3-masala-71-p269', 'jild3-masala-72-p270', 'jild3-masala-73-p271', 'jild3-masala-74-p272', 'jild3-masala-75-p275', 'jild3-masala-76-p275', 'jild3-masala-77-p278', 'jild3-masala-78-p278', 'jild3-masala-79-p279', 'jild3-masala-80-p279', 'jild3-masala-81-p280', 'jild3-masala-82-p280', 'jild3-masala-83-p281', 'jild3-masala-84-p282', 'jild3-masala-85-p283', 'jild3-masala-86-p283', 'jild3-masala-87-p285', 'jild3-masala-88-p286', 'jild3-masala-89-p288', 'jild3-masala-90-p288', 'jild3-masala-91-p288', 'jild3-masala-92-p289', 'jild3-pre-masala-93-p291', 'jild3-masala-93-p293', 'jild3-masala-94-p293', 'jild3-masala-95-p294', 'jild3-masala-96-p294', 'jild3-masala-97-p295', 'jild3-masala-98-p297', 'jild3-masala-99-p297', 'jild3-masala-100-p298', 'jild3-masala-101-p302', 'jild3-masala-102-p304', 'jild3-masala-103-p305', 'jild3-masala-104-p306', 'jild3-masala-105-p306', 'jild3-masala-106-p307', 'jild3-masala-107-p308', 'jild3-masala-108-p308', 'jild3-masala-109-p309', 'jild3-masala-110-p309', 'jild3-masala-111-p310', 'jild3-masala-112-p311', 'jild3-masala-112-taarif-awwal-p313', 'jild3-masala-112-tahir-mutahhar-p315', 'jild3-masala-112-taarif-thani-p323', 'jild3-masala-112-taarif-salis-rabi-p331', 'jild3-masala-112-taarif-khamis-sadis-p333', 'jild3-masala-112-zarb-rukniyat-p338', 'jild3-p341', 'jild3-p342', 'jild3-p344', 'jild3-p347', 'jild3-p349', 'jild3-p352', 'jild3-p356', 'jild3-p358', 'jild3-p363', 'jild3-p366', 'jild3-p370', 'jild3-p373', 'jild3-p376', 'jild3-p381', 'jild3-p385', 'jild3-p391', 'jild3-p392', 'jild3-p394', 'jild3-p401', 'jild3-p402', 'jild3-p409', 'jild3-p411', 'jild3-p417', 'jild3-p419', 'jild3-p422', 'jild3-p425', 'jild3-p429', 'jild3-p439', 'jild3-p441', 'jild3-p444', 'jild3-p447', 'jild3-p452', 'jild3-p456', 'jild3-p460', 'jild3-p463', 'jild3-p466', 'jild3-p470', 'jild3-p475', 'jild3-p477', 'jild3-p479', 'jild3-p484', 'jild3-p487', 'jild3-p491', 'jild3-p493', 'jild3-p496', 'jild3-p498', 'jild3-p504', 'jild3-p508', 'jild3-p510', 'jild3-p519', 'jild3-p521', 'jild3-p527', 'jild3-p530', 'jild3-p537', 'jild3-p541', 'jild3-p543', 'jild3-p545', 'jild3-p547', 'jild3-p549', 'jild3-p551', 'jild3-p553', 'jild3-p555', 'jild3-p557', 'jild3-p559', 'jild3-p561', 'jild3-p563', 'jild3-p565', 'jild3-p567', 'jild3-p569', 'jild3-p571', 'jild3-p573', 'jild3-p575', 'jild3-p577', 'jild3-p580', 'jild3-p582', 'jild3-p584', 'jild3-p586', 'jild3-p588', 'jild3-p590', 'jild3-p591', 'jild3-p594', 'jild3-p598', 'jild3-p599', 'jild3-p601', 'jild3-p603', 'jild3-p605', 'jild3-p606', 'jild3-p609', 'jild3-p612', 'jild3-p614', 'jild3-p617', 'jild3-p619', 'jild3-p621', 'jild3-p623', 'jild3-p628', 'jild3-p632', 'jild3-p637', 'jild3-p641', 'jild3-p648', 'jild3-p650', 'jild3-p656', 'jild3-p659', 'jild3-p664', 'jild3-p670', 'jild3-p675', 'jild3-p677', 'jild3-p679', 'jild3-p681', 'jild3-p683', 'jild3-p685', 'jild3-p689', 'jild3-p691-maadaniyat', 'jild3-masala-12-p696', 'jild3-p707-taharat-kamila', 'jild3-p709-dusre-se-tayammum', 'jild3-p711-haath-aksar', 'jild3-p713-juda-ittisal', 'jild3-p715-bara-tariqe', 'jild3-p716-khatima-risala', 'jild3-risala-jadd-sadid-p717', 'jild3-sawal-3-p739', 'jild3-maakhiz-p743']

# v3 pages per item id, verbatim from content/tashreeh/jild-03.json.
V3_PAGES = {
"jild3-pesh-lafz": [5, 6, 7, 8],
"jild3-bahs1-maani-tabiat": [41, 42],
"jild3-bahs2-tabia-raqqat-saylan": [43, 44, 45, 46],
"jild3-bahs2-qawaid-matan-khalt": [47, 48, 49],
"jild3-bahs3-maani-raqqat-saylan": [50, 51, 52, 53, 54],
"jild3-bahs3-tarkib-ajsam": [55, 56],
"jild3-bahs4-hadd-raqqat": [57, 58, 59, 60, 61],
"jild3-qiyas-murakkab-muqaddima-ula": [62, 63, 64, 65, 66, 67, 68],
"jild3-muqaddima-thaniya-tarif-be-jurm": [69, 70, 71, 72],
"jild3-muqaddima-thaniya-aqwal-tahqiq": [73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84],
"jild3-muqaddima-salisa-istehlak": [85, 86, 87],
"jild3-ghalaba-ghair-bahs-awwal": [88, 89, 90],
"jild3-p91": [91, 92, 93, 94, 95, 96, 97, 98, 99, 100],
"jild3-p101": [101],
"jild3-p102": [102, 103, 104],
"jild3-p105": [105, 106, 107, 108, 109, 110, 111],
"jild3-p112": [112, 113, 114],
"jild3-p115": [115, 116, 117, 118, 119, 120],
"jild3-p121": [121, 122],
"jild3-p123": [123, 124, 125],
"jild3-p126": [126, 127, 128, 129, 130, 131, 132, 133],
"jild3-p134": [134, 135, 136, 137, 138, 139, 140],
"jild3-p141": [141, 142, 143, 144],
"jild3-p145": [145, 146, 147, 148],
"jild3-p149": [149, 150],
"jild3-p151": [151, 152],
"jild3-p153": [153, 154],
"jild3-p155": [155, 156, 157, 158],
"jild3-p159": [159, 160],
"jild3-p161": [161, 162],
"jild3-p163": [163],
"jild3-p164": [164],
"jild3-p165": [165, 166, 167, 168],
"jild3-p169": [169, 170, 171],
"jild3-p172": [172, 173],
"jild3-p174": [174],
"jild3-p175": [175],
"jild3-p176": [176, 177],
"jild3-p178": [178, 179],
"jild3-p180": [180, 181],
"jild3-p182": [182, 183],
"jild3-p184": [184, 185, 186],
"jild3-p187": [187, 188],
"jild3-p189": [189, 190],
"jild3-p191": [191, 192, 193, 194, 195, 196, 197, 198, 199, 200],
"jild3-p201": [201, 202, 203, 204, 205],
"jild3-p206": [206, 207, 208, 209],
"jild3-p210": [210, 211],
"jild3-p212": [212, 213, 214],
"jild3-p215": [215, 216, 217, 218],
"jild3-p219": [219, 220, 221, 222],
"jild3-p223": [223, 224, 225, 226, 227, 228],
"jild3-p229": [229, 230, 231, 232, 233, 234],
"jild3-p235": [235, 236, 237, 238, 239, 240],
"jild3-p241": [241, 242, 243, 244],
"jild3-p245": [245, 246, 247, 248, 249],
"jild3-masala-56-p249": [249, 250],
"jild3-masala-57-p250": [250],
"jild3-masala-58-p250": [250, 251],
"jild3-masala-59-p251": [251, 252, 253],
"jild3-masala-60-p253": [253],
"jild3-masala-61-p254": [254],
"jild3-masala-62-p254": [254],
"jild3-masala-63-p254": [254, 255],
"jild3-masala-64-p255": [255],
"jild3-masala-65-p255": [255, 256, 257, 258, 259],
"jild3-masala-66-p261": [261],
"jild3-masala-67-p261": [261, 262, 263, 264, 265],
"jild3-masala-68-p265": [265, 266],
"jild3-masala-69-p266": [266, 267],
"jild3-masala-70-p267": [267, 268, 269],
"jild3-masala-71-p269": [269, 270],
"jild3-masala-72-p270": [270, 271],
"jild3-masala-73-p271": [271, 272],
"jild3-masala-74-p272": [272, 273, 274, 275],
"jild3-masala-75-p275": [275],
"jild3-masala-76-p275": [275, 276, 277, 278],
"jild3-masala-77-p278": [278],
"jild3-masala-78-p278": [278, 279],
"jild3-masala-79-p279": [279],
"jild3-masala-80-p279": [279, 280],
"jild3-masala-81-p280": [280],
"jild3-masala-82-p280": [280, 281],
"jild3-masala-83-p281": [281, 282],
"jild3-masala-84-p282": [282, 283],
"jild3-masala-85-p283": [283],
"jild3-masala-86-p283": [283, 284, 285],
"jild3-masala-87-p285": [285, 286],
"jild3-masala-88-p286": [286, 287, 288],
"jild3-masala-89-p288": [288],
"jild3-masala-90-p288": [288],
"jild3-masala-91-p288": [288, 289],
"jild3-masala-92-p289": [289, 290],
"jild3-pre-masala-93-p291": [291, 292],
"jild3-masala-93-p293": [293],
"jild3-masala-94-p293": [293, 294],
"jild3-masala-95-p294": [294, 295],
"jild3-masala-96-p294": [294, 295],
"jild3-masala-97-p295": [295],
"jild3-masala-98-p297": [297],
"jild3-masala-99-p297": [297, 298],
"jild3-masala-100-p298": [298, 299, 300, 301],
"jild3-masala-101-p302": [302, 303, 304],
"jild3-masala-102-p304": [304, 305],
"jild3-masala-103-p305": [305, 306],
"jild3-masala-104-p306": [306],
"jild3-masala-105-p306": [306, 307],
"jild3-masala-106-p307": [307, 308],
"jild3-masala-107-p308": [308],
"jild3-masala-108-p308": [308, 309],
"jild3-masala-109-p309": [309],
"jild3-masala-110-p309": [309, 310],
"jild3-masala-111-p310": [310],
"jild3-masala-112-p311": [311, 312],
"jild3-masala-112-taarif-awwal-p313": [313, 314],
"jild3-masala-112-tahir-mutahhar-p315": [315, 316, 317, 318, 319, 320, 321, 322],
"jild3-masala-112-taarif-thani-p323": [323, 324, 325, 326, 327, 328, 329, 330, 331],
"jild3-masala-112-taarif-salis-rabi-p331": [331, 332, 333],
"jild3-masala-112-taarif-khamis-sadis-p333": [333, 334, 335, 336, 337],
"jild3-masala-112-zarb-rukniyat-p338": [338, 339, 340],
"jild3-p341": [341],
"jild3-p342": [342, 343],
"jild3-p344": [344, 345, 346],
"jild3-p347": [347, 348],
"jild3-p349": [349, 350, 351],
"jild3-p352": [352, 353, 354, 355],
"jild3-p356": [356, 357],
"jild3-p358": [358, 359, 360, 361, 362],
"jild3-p363": [363, 364, 365],
"jild3-p366": [366, 367, 368, 369],
"jild3-p370": [370, 371, 372],
"jild3-p373": [373, 374, 375],
"jild3-p376": [376, 377, 378, 379, 380],
"jild3-p381": [381, 382, 383, 384],
"jild3-p385": [385, 386, 387, 388, 389, 390],
"jild3-p391": [391],
"jild3-p392": [392, 393],
"jild3-p394": [394, 395, 396, 397, 398, 399, 400],
"jild3-p401": [401],
"jild3-p402": [402, 403, 404, 405, 406, 407, 408],
"jild3-p409": [409, 410],
"jild3-p411": [411, 412, 413, 414, 415, 416],
"jild3-p417": [417, 418],
"jild3-p419": [419, 420, 421],
"jild3-p422": [422, 423, 424],
"jild3-p425": [425, 426, 427, 428],
"jild3-p429": [429, 430, 431, 432, 433, 434, 435, 436, 437, 438],
"jild3-p439": [439, 440],
"jild3-p441": [441, 442, 443],
"jild3-p444": [444, 445, 446],
"jild3-p447": [447, 448, 449, 450, 451],
"jild3-p452": [452, 453, 454, 455],
"jild3-p456": [456, 457, 458, 459],
"jild3-p460": [460, 461, 462],
"jild3-p463": [463, 464, 465],
"jild3-p466": [466, 467, 468, 469],
"jild3-p470": [470, 471, 472, 473, 474],
"jild3-p475": [475, 476],
"jild3-p477": [477, 478],
"jild3-p479": [479, 480, 481, 482, 483],
"jild3-p484": [484, 485, 486],
"jild3-p487": [487, 488, 489, 490],
"jild3-p491": [491, 492],
"jild3-p493": [493, 494, 495],
"jild3-p496": [496, 497],
"jild3-p498": [498, 499, 500, 501, 502, 503],
"jild3-p504": [504, 505, 506, 507],
"jild3-p508": [508, 509],
"jild3-p510": [510, 511, 512, 513, 514, 515, 516, 517, 518],
"jild3-p519": [519, 520],
"jild3-p521": [521, 522, 523, 524, 525, 526],
"jild3-p527": [527, 528, 529],
"jild3-p530": [530, 531, 532, 533, 534, 535, 536],
"jild3-p537": [537, 538, 539, 540],
"jild3-p541": [541, 542],
"jild3-p543": [543, 544],
"jild3-p545": [545, 546],
"jild3-p547": [547, 548],
"jild3-p549": [549, 550],
"jild3-p551": [551, 552],
"jild3-p553": [553, 554],
"jild3-p555": [555, 556],
"jild3-p557": [557, 558],
"jild3-p559": [559, 560],
"jild3-p561": [561, 562],
"jild3-p563": [563, 564],
"jild3-p565": [565, 566],
"jild3-p567": [567, 568],
"jild3-p569": [569, 570],
"jild3-p571": [571, 572],
"jild3-p573": [573, 574],
"jild3-p575": [575, 576],
"jild3-p577": [577, 579],
"jild3-p580": [580, 581],
"jild3-p582": [582, 583],
"jild3-p584": [584, 585],
"jild3-p586": [586, 587],
"jild3-p588": [588, 589],
"jild3-p590": [590],
"jild3-p591": [591, 592, 593],
"jild3-p594": [594, 595, 596, 597],
"jild3-p598": [598],
"jild3-p599": [599, 600],
"jild3-p601": [601, 602],
"jild3-p603": [603, 604],
"jild3-p605": [605],
"jild3-p606": [606, 607, 608],
"jild3-p609": [609, 610, 611],
"jild3-p612": [612, 613],
"jild3-p614": [614, 615, 616],
"jild3-p617": [617, 618],
"jild3-p619": [619, 620],
"jild3-p621": [621, 622],
"jild3-p623": [623, 624, 625, 626, 627],
"jild3-p628": [628, 629, 630, 631],
"jild3-p632": [632, 633, 634, 635, 636],
"jild3-p637": [637, 638, 639, 640],
"jild3-p641": [641, 642, 643, 644, 645, 646, 647],
"jild3-p648": [648, 649],
"jild3-p650": [650, 651, 652, 653, 654, 655],
"jild3-p656": [656, 657, 658],
"jild3-p659": [659, 660, 661, 662, 663],
"jild3-p664": [664, 665, 666, 667, 668, 669],
"jild3-p670": [670, 671, 672, 673, 674],
"jild3-p675": [675, 676],
"jild3-p677": [677, 678],
"jild3-p679": [679, 680],
"jild3-p681": [681, 682],
"jild3-p683": [683, 684],
"jild3-p685": [685, 686, 687, 688],
"jild3-p689": [689, 690],
"jild3-p691-maadaniyat": [691, 692, 693, 694, 695],
"jild3-masala-12-p696": [696, 697, 698, 699, 700, 701, 702, 703, 704, 705, 706],
"jild3-p707-taharat-kamila": [707, 708],
"jild3-p709-dusre-se-tayammum": [709, 710],
"jild3-p711-haath-aksar": [711, 712],
"jild3-p713-juda-ittisal": [713, 714],
"jild3-p715-bara-tariqe": [715],
"jild3-p716-khatima-risala": [716],
"jild3-risala-jadd-sadid-p717": [717, 718, 719, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738],
"jild3-sawal-3-p739": [739, 740, 741],
"jild3-maakhiz-p743": [743, 744, 745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755, 756],
}

# The Urdu word for "page" is safha; the canonical marker is [safha N].
# Lenticular brackets are U+3010 (open) and U+3011 (close); the short
# form is "[safha-initial N]" with the single-letter abbreviation.
# All three patterns are built from escapes so this file never contains
# a literal lenticular-bracket pair.
SAFHA = "\u0635\u0641\u062d\u06c1"  # the Urdu word for page
RE_LENTICULAR = re.compile("\u3010" + SAFHA + " (\\d+)\u3011")
RE_SHORT = re.compile("\\[\u0635 (\\d+)\\]")
RE_FULL = re.compile("\\[" + SAFHA + " \\d+\\]")
LENTICULAR_PREFIX = "\u3010" + SAFHA  # for the "none remain" check
SHORT_PREFIX_RE = re.compile("\\[\u0635 \\d+\\]")

# Canonical output key order for every item (the JSON contract).
ITEM_KEYS = ["id", "title", "volume_id", "pages", "start_page",
             "tashreeh_sawal", "tashreeh_jawab", "notes"]


def normalise_markers(text):
    """Normalise page markers in one string. Returns (new_text, counts)."""
    counts = {"lenticular": 0, "short": 0, "full_before": 0}
    counts["full_before"] = len(RE_FULL.findall(text))
    text, n1 = RE_LENTICULAR.subn("[" + SAFHA + " \\1]", text)
    counts["lenticular"] = n1
    text, n2 = RE_SHORT.subn("[" + SAFHA + " \\1]", text)
    counts["short"] = n2
    return text, counts


def normalise_item(item):
    """Normalise markers in every string field of one item (recursively
    through lists/dicts). Returns per-form counts for this item."""
    totals = {"lenticular": 0, "short": 0, "full_before": 0}

    def walk(value):
        if isinstance(value, str):
            new, c = normalise_markers(value)
            for k in totals:
                totals[k] += c[k]
            return new
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value

    for key in list(item.keys()):
        item[key] = walk(item[key])
    return totals


def main():
    assert len(V3_IDS) == EXPECTED_ITEMS, "embedded V3_IDS length mismatch"
    assert set(V3_PAGES) == set(V3_IDS), "embedded V3_PAGES keys != V3_IDS"
    assert sum(len(v) for v in V3_PAGES.values()) >= EXPECTED_PAGES

    manifest = json.load(open(os.path.join(BASE, MANIFEST), encoding="utf-8"))
    entries = manifest["chunks"]
    assert len(entries) == 14, f"expected 14 manifest entries, got {len(entries)}"
    assert all(e.get("status") == "done" for e in entries), "not all chunks done"
    by_file = {e["file"]: e for e in entries}
    assert set(by_file) == set(CHUNK_ORDER), (
        f"manifest files != CHUNK_ORDER: "
        f"missing={set(CHUNK_ORDER) - set(by_file)} "
        f"extra={set(by_file) - set(CHUNK_ORDER)}"
    )

    all_items = []
    derived = []
    for fname in CHUNK_ORDER:
        path = os.path.join(BASE, fname)
        d = json.load(open(path, encoding="utf-8"))
        items = d["masail"]
        entry = by_file[fname]
        assert len(items) == entry["items"], (
            f"{fname}: {len(items)} items, manifest says {entry['items']}"
        )
        # Marker normalisation, with before/after counts per chunk.
        before = {"lenticular": 0, "short": 0, "full_before": 0}
        for it in items:
            c = normalise_item(it)
            for k in before:
                before[k] += c[k]
        after_full = sum(
            len(RE_FULL.findall(json.dumps(it, ensure_ascii=False)))
            for it in items
        )
        print(
            f"{fname}: {len(items)} items | markers before: "
            f"lenticular={before['lenticular']} short={before['short']} "
            f"full={before['full_before']} | after: full={after_full}"
        )
        assert after_full == (
            before["lenticular"] + before["short"] + before["full_before"]
        ), f"{fname}: marker count changed by normalisation!"
        # Derive start_page = min(pages) where absent (chunks 06, 12).
        for it in items:
            if "start_page" not in it:
                it["start_page"] = min(it["pages"])
                derived.append(it["id"])
        all_items.extend(items)

    print(f"concatenated: {len(all_items)} items")
    print(f"start_page derived for {len(derived)} items (expected 0: all chunks carry start_page)")
    assert len(all_items) == EXPECTED_ITEMS, (
        f"expected {EXPECTED_ITEMS} items, got {len(all_items)}"
    )

    # Rebuild each item in the canonical key order (the JSON contract).
    canonical = []
    for it in all_items:
        assert set(it.keys()) == set(ITEM_KEYS), (
            f"{it.get('id')}: keys {sorted(it.keys())} != {sorted(ITEM_KEYS)}"
        )
        canonical.append({k: it[k] for k in ITEM_KEYS})
    all_items = canonical

    # Validation.
    ids = [it["id"] for it in all_items]
    assert ids == V3_IDS, (
        f"ID sequence != v3: first diff at "
        f"{next((i for i, (a, b) in enumerate(zip(ids, V3_IDS)) if a != b), min(len(ids), len(V3_IDS)))}"
    )
    assert len(ids) == len(set(ids)), (
        f"DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}"
    )
    empty = [it["id"] for it in all_items if not it.get("tashreeh_jawab")]
    assert not empty, f"EMPTY JAWAB: {empty}"
    vols = set(it.get("volume_id") for it in all_items)
    assert vols == EXPECTED_VOLUME_IDS, f"volume_ids {vols} != {EXPECTED_VOLUME_IDS}"
    pages = set()
    for it in all_items:
        assert it["pages"] == V3_PAGES[it["id"]], (
            f"{it['id']}: pages {it['pages']} != v3 {V3_PAGES[it['id']]}"
        )
        pages.update(it["pages"])
    assert len(pages) == EXPECTED_PAGES, (
        f"expected {EXPECTED_PAGES} unique pages, got {len(pages)}"
    )
    assert min(pages) == EXPECTED_MIN_PAGE, f"min page {min(pages)}"
    assert max(pages) == EXPECTED_MAX_PAGE, f"max page {max(pages)}"
    exceptions = {
        it["id"] for it in all_items if it["start_page"] != min(it["pages"])
    }
    assert not exceptions, f"start_page != min(pages): {sorted(exceptions)}"
    assert ids[0] == EXPECTED_FIRST_ID, f"first id {ids[0]}"
    assert ids[-1] == EXPECTED_LAST_ID, f"last id {ids[-1]}"

    out = {"masail": all_items}
    out_text = json.dumps(out, ensure_ascii=False, indent=1)
    assert LENTICULAR_PREFIX not in out_text, "lenticular markers remain in output!"
    assert not SHORT_PREFIX_RE.search(out_text), "short markers remain in output!"
    total_markers = len(RE_FULL.findall(out_text))
    print(
        f"VALIDATION PASSED: {len(all_items)} items, {len(pages)} unique pages "
        f"(min {min(pages)}, max {max(pages)}), volume_ids {sorted(vols)}, "
        f"first {ids[0]}, last {ids[-1]}, start_page == min(pages) for all, "
        f"derived start_page for {len(derived)} items, markers {total_markers}"
    )

    with open(os.path.join(BASE, "jild-03.json"), "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"WROTE jild-03.json: {len(out_text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
