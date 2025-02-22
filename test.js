
var nres = 50;
var srcStr = "cuchuuuuhuuuhuuhchhuuuuhcuhhuuucuhhuhuuuuhuuhhuuhh";
var idArr = [
    0, 140772, 1302313,
    140771, 330324, 1179755,
    650642, 799390, 905885,
    160532, 890964, 1046904,
    865310, 160533, 1259523,
    1218951, 277009, 146248,
    315278, 325579, 371495,
    371502, 371501, 371500,
    330330, 140769, 707794,
    341632, 248125, 1179739,
    1180249, 1036034, 140768,
    1521150, 330328, 330329,
    371662, 330336, 1174118,
    627480, 627119, 1179734,
    330337, 1521148, 605625,
    330338, 330340, 715206,
    926968, 330343, 330344
];

var c1Arr = [
    "", "aquatic", "water",

    // Nouns
    "water", "aqua", "water",
    "waters", "fisherman\'s daughter", "water to blood / rivers",

    // 2 Words: Others
    "at the water", "by the water", "on the waterfront",
    "waterfront", "waterside", "plumb",
    "level", "waterless", "afloat",
    "awash", "waterlogged", "hygroscopic",
    "hygroscopical", "water-absorbing", "water-attracting",
    "dehydrating", "water-retentive", "by sea",
    "by water",

    // 2 Words: Verbs
    "to serve sb. with water", "to dehydrate",
    "to transpire", "to strain off water", "to scoop out water",
    "to conserve water", "to soften water", "to dehydrate",
    "to dewater", "to boil water", "to micturate",
    "to urinate", "to pass water", "to void urine",
    "to supply water", "to conserve water", "to save water",
    "to spout", "to carry water", "to tread water",
    "to spin one\'s wheels", "to waste water", "to shed water"
];

var c2Arr = [
    "", "Wasser-", "Wasser-",

    // Nouns
    "Wasser", "Wasser", "Wasser",
    "Wasser", "Wasser", "Wasser",

    // 2 Words: Others
    "am Wasser", "am Wasser", "am Wasser",
    "am Wasser", "am Wasser", "im Wasser",
    "im Wasser", "ohne Wasser", "über Wasser",
    "unter Wasser", "voll Wasser", "Wasser anziehend",
    "Wasser anziehend", "Wasser anziehend", "Wasser anziehend",
    "Wasser entziehend", "Wasser speichernd", "zu Wasser",
    "zu Wasser",

    // 2 Words: Verbs
    "jdm. Wasser liefern", "Wasser abgeben",
    "Wasser abgeben", "Wasser abgießen", "Wasser ausschöpfen",
    "Wasser einsparen", "Wasser enthärten", "Wasser entziehen",
    "Wasser entziehen", "Wasser kochen", "Wasser lassen",
    "Wasser lassen", "Wasser lassen", "Wasser lassen",
    "Wasser liefern", "Wasser sparen", "Wasser sparen",
    "Wasser speien", "Wasser tragen", "Wasser treten",
    "Wasser treten", "Wasser vergeuden", "Wasser vergießen"
]

var hlRows = true;
var retrDC = true;
window.setTimeout("add_js_extras()", 100);

