#!/usr/bin/env python3
"""Builds addons/armenian/web/server/data/armenian.json — the /armenian deck: the Eastern Armenian alphabet (37 letters + և; ու is a digraph, Ւ is not listed)
followed by ~500 beginner words in packs of 50 (g = 1, 2, 3 … by difficulty), modern Armenia orthography.

No downloads: the data lives below as literals. Transliteration: ʼ marks aspirates (թ tʼ, փ pʼ, ք kʼ, ց tsʼ, չ chʼ),
ռ = rr, ր = r, ը = ə, word-initial ե = ye, ո = vo at the start of a word.
Word lines:  armenian | translit | meaning; meaning | example armenian | example translit | example english
Run: python3 -I addons/armenian/scripts/build-armenian.py
"""
import json, os, re

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web', 'server', 'data', 'armenian.json')

# glyph, upper+lower, sound, hint, example (hy, tr, en)
LETTERS = [
    ('ա', 'a', "like 'a' in father", ('աղ', 'agh', 'salt')),
    ('բ', 'b', "like 'b' in book", ('բարի', 'bari', 'good')),
    ('գ', 'g', "like 'g' in go", ('գիրք', 'girkʼ', 'book')),
    ('դ', 'd', "like 'd' in door", ('դուռ', 'durr', 'door')),
    ('ե', 'ye/e', "'ye' in yes at the start of a word, 'e' in bed inside", ('եղբայր', 'yeghbayr', 'brother')),
    ('զ', 'z', "like 'z' in zoo", ('զանգ', 'zang', 'bell, call')),
    ('է', 'e', "like 'e' in bed", ('էջ', 'ej', 'page')),
    ('ը', 'ə', "short schwa, like 'a' in about", ('ընկեր', 'ənker', 'friend')),
    ('թ', 'tʼ', "'t' in top, with a puff of air", ('թեյ', 'tʼey', 'tea')),
    ('ժ', 'zh', "like 's' in measure", ('ժամ', 'zham', 'hour')),
    ('ի', 'i', "like 'ee' in see, short", ('իմ', 'im', 'my')),
    ('լ', 'l', "like 'l' in lamp", ('լույս', 'luys', 'light')),
    ('խ', 'kh', "like 'ch' in Scottish loch", ('խնձոր', 'khndzor', 'apple')),
    ('ծ', 'ts', "like 'ts' in cats, no puff of air", ('ծառ', 'tsarr', 'tree')),
    ('կ', 'k', "like 'k' in sky, no puff of air", ('կատու', 'katu', 'cat')),
    ('հ', 'h', "like 'h' in hat", ('հաց', 'hatsʼ', 'bread')),
    ('ձ', 'dz', "like 'ds' in beds", ('ձի', 'dzi', 'horse')),
    ('ղ', 'gh', "French 'r' / a gargled g", ('աղջիկ', 'aghjik', 'girl')),
    ('ճ', 'ch', "like 'ch' in church, no puff of air", ('ճանապարհ', 'chanaparh', 'road')),
    ('մ', 'm', "like 'm' in mother", ('մայր', 'mayr', 'mother')),
    ('յ', 'y', "like 'y' in yes", ('յոթ', 'yotʼ', 'seven')),
    ('ն', 'n', "like 'n' in no", ('նավ', 'nav', 'ship')),
    ('շ', 'sh', "like 'sh' in shoe", ('շուն', 'shun', 'dog')),
    ('ո', 'vo', "'vo' at the start of a word, 'o' in more inside", ('ոչ', 'vochʼ', 'no')),
    ('չ', 'chʼ', "'ch' in church, with a puff of air", ('չորս', 'chʼors', 'four')),
    ('պ', 'p', "like 'p' in spin, no puff of air", ('պապ', 'pap', 'grandfather')),
    ('ջ', 'j', "like 'j' in jam", ('ջուր', 'jur', 'water')),
    ('ռ', 'rr', "strongly rolled 'r'", ('ռադիո', 'rradio', 'radio')),
    ('ս', 's', "like 's' in sun", ('սեղան', 'seghan', 'table')),
    ('վ', 'v', "like 'v' in van", ('վարդ', 'vard', 'rose')),
    ('տ', 't', "like 't' in star, no puff of air", ('տուն', 'tun', 'house')),
    ('ր', 'r', "soft single tap 'r', like Spanish 'pero'", ('րոպե', 'rope', 'minute')),
    ('ց', 'tsʼ', "'ts' in cats, with a puff of air", ('ցուրտ', 'tsʼurt', 'cold')),
    ('փ', 'pʼ', "'p' in pot, with a puff of air", ('փոքր', 'pʼokʼr', 'small')),
    ('ք', 'kʼ', "'k' in key, with a puff of air", ('քույր', 'kʼuyr', 'sister')),
    ('օ', 'o', "like 'o' in more", ('օր', 'or', 'day')),
    ('ֆ', 'f', "like 'f' in fun", ('ֆիլմ', 'film', 'film')),
    ('և', 'ev', "the word 'and' / the sound 'ev'", ('և', 'ev', 'and')),
]

# words, in study order; every block is one topic, g is cut into packs of 50
W = {}
W['greetings'] = """
Բարև|barev|hello|Բարև, ինչպես ես։|Barev, inchʼpes es?|Hello, how are you?
Բարի լույս|bari luys|good morning|Բարի լույս, մամա։|Bari luys, mama.|Good morning, mom.
Բարի երեկո|bari yereko|good evening|Բարի երեկո, պապիկ։|Bari yereko, papik.|Good evening, grandpa.
Բարի գիշեր|bari gisher|good night|Բարի գիշեր, տատիկ։|Bari gisher, tatik.|Good night, grandma.
Ողջույն|voghjuyn|greetings|Ողջույն բոլորին։|Voghjuyn bolorin.|Greetings to everyone.
Ցտեսություն|tsʼtesutyun|goodbye|Ցտեսություն, ընկեր։|Tsʼtesutyun, ənker.|Goodbye, friend.
Հաջողություն|hajoghutyun|good luck; success|Հաջողություն քեզ։|Hajoghutyun kʼez.|Good luck to you.
Շնորհակալություն|shnorhakalutyun|thank you|Շնորհակալություն օգնության համար։|Shnorhakalutyun ognutyan hamar.|Thank you for the help.
Խնդրեմ|khndrem|please; you're welcome|Մի բաժակ ջուր, խնդրեմ։|Mi bazhak jur, khndrem.|A glass of water, please.
Կներեք|knerekʼ|excuse me (formal)|Կներեք, որտեղ է կայարանը։|Knerekʼ, vortegh e kayaranə?|Excuse me, where is the station?
Ներողություն|neroghutyun|sorry; apology|Ներողություն, ուշացա։|Neroghutyun, ushatsʼa.|Sorry, I am late.
Այո|ayo|yes|Այո, ես հայ եմ։|Ayo, yes hay em.|Yes, I am Armenian.
Ոչ|vochʼ|no|Ոչ, շնորհակալություն։|Vochʼ, shnorhakalutyun.|No, thank you.
Լավ|lav|good; OK; well|Ամեն ինչ լավ է։|Amen inchʼ lav e.|Everything is fine.
Շատ|shat|very; a lot; many|Շատ համեղ է։|Shat hamegh e.|It is very tasty.
Ինչպես ես|inchʼpes es|how are you? (informal)|Ինչպես ես այսօր։|Inchʼpes es aysor?|How are you today?
Լավ եմ|lav em|I am fine|Լավ եմ, շնորհակալություն։|Lav em, shnorhakalutyun.|I am fine, thank you.
Բարի գալուստ|bari galust|welcome|Բարի գալուստ Հայաստան։|Bari galust Hayastan.|Welcome to Armenia.
Հաճելի է|hacheli e|nice to meet you; pleasant|Շատ հաճելի է։|Shat hacheli e.|Very nice to meet you.
Ես|yes|I|Ես ուսանող եմ։|Yes usanogh em.|I am a student.
Դու|du|you (informal)|Դու որտեղից ես։|Du vorteghitsʼ es?|Where are you from?
Նա|na|he; she|Նա իմ քույրն է։|Na im kʼuyrn e.|She is my sister.
Մենք|menkʼ|we|Մենք տանն ենք։|Menkʼ tann enkʼ.|We are at home.
Դուք|dukʼ|you (plural / formal)|Դուք հայ եք։|Dukʼ hay ekʼ.|You are Armenian.
Նրանք|nrankʼ|they|Նրանք ընկերներ են։|Nrankʼ ənkerner en.|They are friends.
Իմ|im|my|Սա իմ տունն է։|Sa im tunn e.|This is my house.
Քո|kʼo|your (informal)|Սա քո գիրքն է։|Sa kʼo girkʼn e.|This is your book.
մեկ|mek|one; 1|Ես ունեմ մեկ եղբայր։|Yes unem mek yeghbayr.|I have one brother.
երկու|yerku|two; 2|Ես ունեմ երկու քույր։|Yes unem yerku kʼuyr.|I have two sisters.
երեք|yerekʼ|three; 3|Սեղանի վրա երեք բաժակ կա։|Seghani vra yerekʼ bazhak ka.|There are three glasses on the table.
չորս|chʼors|four; 4|Մենք չորս հոգի ենք։|Menkʼ chʼors hogi enkʼ.|There are four of us.
հինգ|hing|five; 5|Հինգ րոպե սպասիր։|Hing rope spasir.|Wait five minutes.
վեց|vetsʼ|six; 6|Վեց ժամ քնեցի։|Vetsʼ zham kʼnetsʼi.|I slept six hours.
յոթ|yotʼ|seven; 7|Շաբաթում յոթ օր կա։|Shabatʼum yotʼ or ka.|There are seven days in a week.
ութ|utʼ|eight; 8|Ութ ժամ աշխատում եմ։|Utʼ zham ashkhatum em.|I work eight hours.
ինը|inə|nine; 9|Ինը ժամին կգամ։|Inə zhamin kgam.|I will come at nine o'clock.
տասը|tasə|ten; 10|Այստեղ տասը մարդ կա։|Aystegh tasə mard ka.|There are ten people here.
Սա|sa|this|Սա գիրք է։|Sa girkʼ e.|This is a book.
Դա|da|that|Դա իմ մեքենան է։|Da im mekʼenan e.|That is my car.
Ինչ|inchʼ|what|Ինչ է սա։|Inchʼ e sa?|What is this?
Ով|ov|who|Ով է նա։|Ov e na?|Who is he?
Որտեղ|vortegh|where|Որտեղ է տունը։|Vortegh e tunə?|Where is the house?
Ինչու|inchʼu|why|Ինչու ես ուշացել։|Inchʼu es ushatsʼel?|Why are you late?
Երբ|yerb|when|Երբ ես գալիս։|Yerb es galis?|When are you coming?
Գիտեմ|gitem|I know|Ես գիտեմ։|Yes gitem.|I know.
Չգիտեմ|chʼgitem|I don't know|Ներողություն, չգիտեմ։|Neroghutyun, chʼgitem.|Sorry, I don't know.
Հասկանում եմ|haskanum em|I understand|Այո, հասկանում եմ։|Ayo, haskanum em.|Yes, I understand.
Չեմ հասկանում|chʼem haskanum|I don't understand|Կներեք, չեմ հասկանում։|Knerekʼ, chʼem haskanum.|Sorry, I don't understand.
Բայց|bayts|but|Համեղ է, բայց թանկ։|Hamegh e, bayts tʼank.|It is tasty, but expensive.
կամ|kam|or|Թեյ կամ սուրճ։|Tʼey kam surch.|Tea or coffee.
"""
W['family'] = """
մայր|mayr|mother|Մայրս տանն է։|Mayrs tann e.|My mother is at home.
հայր|hayr|father|Հայրս բժիշկ է։|Hayrs bzhishk e.|My father is a doctor.
մամա|mama|mom; mama|Մամա, ես քաղցած եմ։|Mama, yes kʼaghtsʼats em.|Mom, I am hungry.
պապա|papa|dad; papa|Պապա, եկ այստեղ։|Papa, yek aystegh.|Dad, come here.
եղբայր|yeghbayr|brother|Իմ եղբայրը ուսանող է։|Im yeghbayrə usanogh e.|My brother is a student.
քույր|kʼuyr|sister|Քույրս երեխա ունի։|Kʼuyrs yerekha uni.|My sister has a child.
որդի|vordi|son|Նրա որդին դպրոցում է։|Nra vordin dprotsʼum e.|Her son is at school.
դուստր|dustr|daughter|Նրա դուստրը փոքր է։|Nra dustrə pʼokʼr e.|Her daughter is small.
տղա|tgha|boy; son|Այդ տղան իմ ընկերն է։|Ayd tghan im ənkern e.|That boy is my friend.
աղջիկ|aghjik|girl; daughter|Աղջիկը գիրք է կարդում։|Aghjikə girkʼ e kardum.|The girl is reading a book.
երեխա|yerekha|child|Երեխան քնած է։|Yerekhan kʼnats e.|The child is asleep.
ամուսին|amusin|husband; spouse|Ամուսինս աշխատում է։|Amusins ashkhatum e.|My husband is working.
կին|kin|woman; wife|Կինը խանութում է։|Kinə khanutʼum e.|The woman is in the shop.
տատիկ|tatik|grandmother|Տատիկս հաց է թխում։|Tatiks hatsʼ e tʼkhum.|My grandmother is baking bread.
պապիկ|papik|grandfather|Պապիկս այգում է։|Papiks aygum e.|My grandfather is in the garden.
ընտանիք|əntanikʼ|family|Իմ ընտանիքը մեծ է։|Im əntanikʼə mets e.|My family is big.
ընկեր|ənker|friend|Նա իմ լավ ընկերն է։|Na im lav ənkern e.|He is my good friend.
մարդ|mard|person; man|Այստեղ շատ մարդ կա։|Aystegh shat mard ka.|There are many people here.
տղամարդ|tghamard|man (male)|Տղամարդը խանութում է։|Tghamardə khanutʼum e.|The man is in the shop.
հարևան|harevan|neighbour|Հարևանս բարի մարդ է։|Harevans bari mard e.|My neighbour is a kind person.
անուն|anun|name|Քո անունն ինչ է։|Kʼo anunn inchʼ e?|What is your name?
թոռ|tʼorr|grandchild|Նա իմ թոռն է։|Na im tʼorrn e.|He is my grandchild.
քեռի|kʼerri|uncle (mother's brother)|Քեռիս Երևանում է ապրում։|Kʼerris Yerevanum e aprum.|My uncle lives in Yerevan.
հորեղբայր|horeghbayr|uncle (father's brother)|Հորեղբայրս Գյումրիում է ապրում։|Horeghbayrs Gyumrium e aprum.|My uncle lives in Gyumri.
ազգանուն|azganun|surname|Ինչ է քո ազգանունը։|Inchʼ e kʼo azganunə?|What is your surname?
"""
W['food'] = """
հաց|hatsʼ|bread|Ես հաց եմ ուտում։|Yes hatsʼ em utum.|I am eating bread.
ջուր|jur|water|Ես ջուր եմ խմում։|Yes jur em khmum.|I am drinking water.
կաթ|katʼ|milk|Երեխան կաթ է խմում։|Yerekhan katʼ e khmum.|The child is drinking milk.
թեյ|tʼey|tea|Թեյ կուզեմ։|Tʼey kuzem.|I would like tea.
սուրճ|surch|coffee|Ես սուրճ եմ սիրում։|Yes surch em sirum.|I like coffee.
գինի|gini|wine|Հայկական գինին համեղ է։|Haykakan gini-n hamegh e.|Armenian wine is tasty.
գարեջուր|garejur|beer|Մի գարեջուր, խնդրեմ։|Mi garejur, khndrem.|A beer, please.
հյութ|hyutʼ|juice|Նարնջի հյութ եմ խմում։|Narnji hyutʼ em khmum.|I am drinking orange juice.
միս|mis|meat|Ես միս չեմ ուտում։|Yes mis chʼem utum.|I don't eat meat.
ձուկ|dzuk|fish|Սևանի ձուկը համեղ է։|Sevani dzukə hamegh e.|Sevan fish is tasty.
հավ|hav|chicken; hen|Ես հավ եմ սիրում։|Yes hav em sirum.|I like chicken.
ձու|dzu|egg|Նախաճաշին ձու եմ ուտում։|Nakhachashin dzu em utum.|I eat eggs for breakfast.
պանիր|panir|cheese|Ես պանիր եմ սիրում։|Yes panir em sirum.|I like cheese.
կարագ|karag|butter|Հացի վրա կարագ կա։|Hatsʼi vra karag ka.|There is butter on the bread.
բրինձ|brindz|rice|Բրինձը համեղ է։|Brindzə hamegh e.|The rice is tasty.
աղ|agh|salt|Աղ, խնդրեմ։|Agh, khndrem.|Salt, please.
շաքար|shakʼar|sugar|Թեյին շաքար չեմ դնում։|Tʼeyin shakʼar chʼem dnum.|I don't put sugar in tea.
պտուղ|ptugh|fruit|Ես պտուղ եմ սիրում։|Yes ptugh em sirum.|I like fruit.
խնձոր|khndzor|apple|Այս խնձորը քաղցր է։|Ays khndzorə kʼaghtsʼr e.|This apple is sweet.
տանձ|tandz|pear|Տանձը համեղ է։|Tandzə hamegh e.|The pear is tasty.
խաղող|khaghogh|grapes|Խաղողը թարմ է։|Khaghoghə tʼarm e.|The grapes are fresh.
նարինջ|narinj|orange|Նարինջը նարնջագույն է։|Narinjə narnjaguyn e.|The orange is orange.
լիմոն|limon|lemon|Թեյի մեջ լիմոն կա։|Tʼeyi mej limon ka.|There is lemon in the tea.
ծիրան|tsiran|apricot|Հայկական ծիրանը համեղ է։|Haykakan tsiranə hamegh e.|Armenian apricots are tasty.
դեղձ|deghdz|peach|Դեղձը քաղցր է։|Deghdzə kʼaghtsʼr e.|The peach is sweet.
ելակ|yelak|strawberry|Ելակը կարմիր է։|Yelakə karmir e.|The strawberry is red.
ձմերուկ|dzmeruk|watermelon|Ամռանը ձմերուկ ենք ուտում։|Amrranə dzmeruk enkʼ utum.|In summer we eat watermelon.
ընկույզ|ənkuyz|walnut|Ընկույզը կարծր է։|Ənkuyzə kartsr e.|The walnut is hard.
բանջարեղեն|banjareghen|vegetables|Բանջարեղեն եմ գնում։|Banjareghen em gnum.|I am buying vegetables.
կարտոֆիլ|kartofil|potato|Կարտոֆիլ եմ եփում։|Kartofil em yepʼum.|I am boiling potatoes.
լոլիկ|lolik|tomato|Լոլիկը թարմ է։|Lolikə tʼarm e.|The tomato is fresh.
վարունգ|varung|cucumber|Աղցանում վարունգ կա։|Aghtsʼanum varung ka.|There is cucumber in the salad.
սոխ|sokh|onion|Սոխ եմ կտրում։|Sokh em ktrum.|I am cutting an onion.
սխտոր|skhtor|garlic|Սխտոր չեմ սիրում։|Skhtor chʼem sirum.|I don't like garlic.
կաղամբ|kaghamb|cabbage|Կաղամբը մեծ է։|Kaghambə mets e.|The cabbage is big.
գազար|gazar|carrot|Գազարը նարնջագույն է։|Gazarə narnjaguyn e.|The carrot is orange.
մեղր|meghr|honey|Թեյին մեղր եմ դնում։|Tʼeyin meghr em dnum.|I put honey in my tea.
շոկոլադ|shokolad|chocolate|Երեխան շոկոլադ է ուզում։|Yerekhan shokolad e uzum.|The child wants chocolate.
ապուր|apur|soup|Ապուրը տաք է։|Apurə takʼ e.|The soup is hot.
աղցան|aghtsʼan|salad|Աղցան եմ պատրաստում։|Aghtsʼan em patrastum.|I am making a salad.
նախաճաշ|nakhachash|breakfast|Նախաճաշը պատրաստ է։|Nakhachashə patrast e.|Breakfast is ready.
ճաշ|chash|lunch; meal|Ճաշի ժամանակն է։|Chashi zhamanaka e.|It is time for lunch.
ընթրիք|əntʼrikʼ|dinner|Ընթրիքը համեղ էր։|Əntʼrikʼə hamegh er.|Dinner was tasty.
համեղ|hamegh|tasty|Սա շատ համեղ է։|Sa shat hamegh e.|This is very tasty.
քաղցած|kʼaghtsʼats|hungry|Ես քաղցած եմ։|Yes kʼaghtsʼats em.|I am hungry.
ծարավ|tsarav|thirsty|Ես ծարավ եմ։|Yes tsarav em.|I am thirsty.
պաղպաղակ|paghpaghak|ice cream|Պաղպաղակ եմ ուզում։|Paghpaghak em uzum.|I want ice cream.
կոնյակ|konyak|brandy; cognac|Հայկական կոնյակը հայտնի է։|Haykakan konyakə haytni e.|Armenian cognac is famous.
"""
W['colours'] = """
կարմիր|karmir|red|Խնձորը կարմիր է։|Khndzorə karmir e.|The apple is red.
կապույտ|kapuyt|blue|Երկինքը կապույտ է։|Yerkinkʼə kapuyt e.|The sky is blue.
կանաչ|kanachʼ|green|Խոտը կանաչ է։|Khotə kanachʼ e.|The grass is green.
դեղին|deghin|yellow|Լիմոնը դեղին է։|Limonə deghin e.|The lemon is yellow.
սպիտակ|spitak|white|Ձյունը սպիտակ է։|Dzyunə spitak e.|The snow is white.
սև|sev|black|Իմ կատուն սև է։|Im katun sev e.|My cat is black.
մոխրագույն|mokhraguyn|grey|Երկինքն այսօր մոխրագույն է։|Yerkinkʼn aysor mokhraguyn e.|The sky is grey today.
նարնջագույն|narnjaguyn|orange (colour)|Գազարը նարնջագույն է։|Gazarə narnjaguyn e.|The carrot is orange.
վարդագույն|vardaguyn|pink|Վարդը վարդագույն է։|Vardə vardaguyn e.|The rose is pink.
մանուշակագույն|manushakaguyn|purple|Ծաղիկը մանուշակագույն է։|Tsaghikə manushakaguyn e.|The flower is purple.
գույն|guyn|colour|Քո սիրած գույնն ինչ է։|Kʼo sirats guynn inchʼ e?|What is your favourite colour?
"""
W['time'] = """
օր|or|day|Այսօր լավ օր է։|Aysor lav or e.|Today is a good day.
ժամ|zham|hour; o'clock|Ժամը քանի է։|Zhamə kʼani e?|What time is it?
րոպե|rope|minute|Մի րոպե սպասիր։|Mi rope spasir.|Wait a minute.
այսօր|aysor|today|Այսօր ցուրտ է։|Aysor tsʼurt e.|It is cold today.
վաղը|vaghə|tomorrow|Վաղը կգամ։|Vaghə kgam.|I will come tomorrow.
երեկ|yerek|yesterday|Երեկ տանն էի։|Yerek tann ei.|I was at home yesterday.
հիմա|hima|now|Հիմա գնում եմ։|Hima gnum em.|I am leaving now.
առավոտ|arravot|morning|Առավոտյան թեյ եմ խմում։|Arravotyan tʼey em khmum.|I drink tea in the morning.
շաբաթ|shabatʼ|week; Saturday|Շաբաթ օրը տանն եմ։|Shabatʼ orə tann em.|On Saturday I am at home.
ամիս|amis|month|Տարվա մեջ տասներկու ամիս կա։|Tarva mej tasnerku amis ka.|There are twelve months in a year.
տարի|tari|year|Ես քսան տարեկան եմ։|Yes kʼsan tarekan em.|I am twenty years old.
վայրկյան|vayrkyan|second|Մեկ րոպեում վաթսուն վայրկյան կա։|Mek ropeum vatʼsun vayrkyan ka.|There are sixty seconds in a minute.
կեսօր|kesor|noon; afternoon|Կեսօրին ճաշում եմ։|Kesorin chashum em.|I have lunch at noon.
երեկո|yereko|evening|Երեկոյան տանն եմ։|Yerekoyan tann em.|I am at home in the evening.
գիշեր|gisher|night|Գիշերը մութ է։|Gisherə mutʼ e.|The night is dark.
երկուշաբթի|yerkushabtʼi|Monday|Երկուշաբթի օրը աշխատում եմ։|Yerkushabtʼi orə ashkhatum em.|I work on Monday.
երեքշաբթի|yerekʼshabtʼi|Tuesday|
չորեքշաբթի|chʼorekʼshabtʼi|Wednesday|
հինգշաբթի|hingshabtʼi|Thursday|
ուրբաթ|urbatʼ|Friday|
կիրակի|kiraki|Sunday|
հունվար|hunvar|January|
փետրվար|pʼetrvar|February|
մարտ|mart|March|
ապրիլ|april|April|
մայիս|mayis|May|
հունիս|hunis|June|
հուլիս|hulis|July|
օգոստոս|ogostos|August|
սեպտեմբեր|september|September|
հոկտեմբեր|hoktember|October|
նոյեմբեր|noyember|November|
դեկտեմբեր|dektember|December|
գարուն|garun|spring|
ամառ|amarr|summer|
աշուն|ashun|autumn|
ձմեռ|dzmerr|winter|
ուշ|ush|late|
շուտ|shut|soon; early|
միշտ|misht|always|
երբեք|yerbekʼ|never|
արդեն|arden|already|
դեռ|derr|still; yet|
հետո|heto|then; after|
առաջ|arraj|before; ago|
"""
W['body'] = """
գլուխ|glukh|head
աչք|achʼkʼ|eye
ականջ|akanj|ear
քիթ|kʼitʼ|nose
բերան|beran|mouth
ատամ|atam|tooth
լեզու|lezu|tongue; language
մազ|maz|hair
դեմք|demkʼ|face
ձեռք|dzerrkʼ|hand; arm
մատ|mat|finger
ոտք|votkʼ|foot; leg
սիրտ|sirt|heart
մեջք|mejkʼ|back
փոր|pʼor|belly; stomach
ուս|us|shoulder
ծունկ|tsunk|knee
արյուն|aryun|blood
ոսկոր|voskor|bone
ուղեղ|ughegh|brain
առողջ|arroghj|healthy
հիվանդ|hivand|sick; ill
բժիշկ|bzhishk|doctor
ցավ|tsʼav|pain
դեղ|degh|medicine
հիվանդանոց|hivandanotsʼ|hospital
առողջություն|arroghjutyun|health; cheers
"""
W['home'] = """
տուն|tun|house; home
սենյակ|senyak|room
դուռ|durr|door
պատուհան|patuhan|window
սեղան|seghan|table
աթոռ|atʼorr|chair
մահճակալ|mahchakal|bed
խոհանոց|khohanotsʼ|kitchen
լոգարան|logaran|bathroom
պատ|pat|wall
հատակ|hatak|floor
տանիք|tanikʼ|roof
բանալի|banali|key
լամպ|lamp|lamp
հեռուստացույց|herrustatsʼuyts|television
հեռախոս|herrakhos|telephone
համակարգիչ|hamakargichʼ|computer
գիրք|girkʼ|book
պարտեզ|partez|garden
բնակարան|bnakaran|apartment
հարկ|hark|floor (storey)
պատշգամբ|patshgamb|balcony
բաժակ|bazhak|glass; cup
գդալ|gdal|spoon
դանակ|danak|knife
պատառաքաղ|patarrakʼagh|fork
ափսե|apse|plate
կաթսա|katʼsa|pot
սառնարան|sarrnaran|refrigerator
հայելի|hayeli|mirror
ժամացույց|zhamatsʼuyts|clock; watch
գորգ|gorg|carpet
"""
W['places'] = """
քաղաք|kʼaghakʼ|city
գյուղ|gyugh|village
փողոց|pʼoghotsʼ|street
հրապարակ|hraparak|square
խանութ|khanutʼ|shop
շուկա|shuka|market
դպրոց|dprotsʼ|school
համալսարան|hamalsaran|university
գրադարան|gradaran|library
եկեղեցի|yekeghetsʼi|church
թանգարան|tʼangaran|museum
այգի|aygi|garden; park
բանկ|bank|bank
հյուրանոց|hyuranotsʼ|hotel
ռեստորան|rrestoran|restaurant
սրճարան|srcharan|café
դեղատուն|deghatun|pharmacy
օդանավակայան|odanavakayan|airport
կայարան|kayaran|station
կամուրջ|kamurj|bridge
ճանապարհ|chanaparh|road; way
երկիր|yerkir|country; earth
աշխարհ|ashkharh|world
Հայաստան|Hayastan|Armenia
Երևան|Yerevan|Yerevan
հայ|hay|Armenian (person)
հայերեն|hayeren|Armenian (language)
անգլերեն|angleren|English (language)
ռուսերեն|rruseren|Russian (language)
գերմաներեն|germaneren|German (language)
"""
W['travel'] = """
ճանապարհորդություն|chanaparhordutyun|travel; journey
տոմս|toms|ticket
անձնագիր|andznagir|passport
ճամպրուկ|champruk|suitcase
ավտոբուս|avtobus|bus
գնացք|gnatsʼkʼ|train
մեքենա|mekʼena|car; machine
ինքնաթիռ|inkʼnatʼirr|aeroplane
տաքսի|takʼsi|taxi
հեծանիվ|hetsaniv|bicycle
մետրո|metro|metro
նավ|nav|ship; boat
քարտեզ|kʼartez|map
աջ|aj|right
ձախ|dzakh|left
ուղիղ|ughigh|straight
մոտ|mot|near; close
հեռու|herru|far
այստեղ|aystegh|here
այնտեղ|ayntegh|there
արագ|arag|fast; quickly
դանդաղ|dandagh|slow; slowly
Բարի ճանապարհ|bari chanaparh|have a good trip
"""
W['verbs'] = """
լինել|linel|to be
ունենալ|unenal|to have
գնալ|gnal|to go
գալ|gal|to come
անել|anel|to do; to make
ասել|asel|to say
տեսնել|tesnel|to see
լսել|lsel|to hear; to listen
խոսել|khosel|to speak
կարդալ|kardal|to read
գրել|grel|to write
սիրել|sirel|to love; to like
ուզենալ|uzenal|to want
կարողանալ|karoghanal|to be able; can
իմանալ|imanal|to know (a fact)
հասկանալ|haskanal|to understand
տալ|tal|to give
վերցնել|vertsʼnel|to take
գնել|gnel|to buy
վաճառել|vacharrel|to sell
բացել|batsʼel|to open
փակել|pʼakel|to close
սովորել|sovorel|to learn; to study
սպասել|spasel|to wait
քնել|kʼnel|to sleep
արթնանալ|artʼnanal|to wake up
նստել|nstel|to sit
կանգնել|kangnel|to stand
վազել|vazel|to run
քայլել|kʼaylel|to walk
խաղալ|khaghal|to play
աշխատել|ashkhatel|to work
օգնել|ognel|to help
հարցնել|hartsʼnel|to ask
պատասխանել|pataskhanel|to answer
մտածել|mtatsel|to think
ապրել|aprel|to live
լվանալ|lvanal|to wash
գտնել|gtnel|to find
կորցնել|kortsʼnel|to lose
ժպտալ|zhptal|to smile
ծիծաղել|tsitsaghel|to laugh
ճանաչել|chanachʼel|to know (a person)
հիշել|hishel|to remember
մոռանալ|morranal|to forget
սկսել|sksel|to begin
ավարտել|avartel|to finish
վճարել|vcharel|to pay
կանչել|kanchʼel|to call
ուղարկել|ugharkel|to send
ստանալ|stanal|to receive
բերել|berel|to bring
երգել|yergel|to sing
պարել|parel|to dance
լողալ|loghal|to swim
ուտել|utel|to eat
խմել|khmel|to drink
հանգստանալ|hangstanal|to rest
ծնվել|tsnvel|to be born
"""
W['adjectives'] = """
մեծ|mets|big; large
փոքր|pʼokʼr|small
նոր|nor|new
հին|hin|old (thing)
վատ|vat|bad
գեղեցիկ|geghetsʼik|beautiful
տաք|takʼ|hot; warm
սառը|sarrə|cold (thing)
ցուրտ|tsʼurt|cold (weather)
երկար|yerkar|long
կարճ|karch|short
բարձր|bardzr|high; tall; loud
ցածր|tsʼatsr|low
հեշտ|hesht|easy
դժվար|dzhvar|difficult
ճիշտ|chisht|correct; right
սխալ|skhal|wrong; mistake
երիտասարդ|yeritasard|young
ծեր|tser|old (person)
հարուստ|harust|rich
աղքատ|aghkʼat|poor
ուժեղ|uzhegh|strong
թույլ|tʼuyl|weak
թանկ|tʼank|expensive
էժան|ezhan|cheap
մաքուր|makʼur|clean
կեղտոտ|keghtot|dirty
լիքը|likʼə|full
դատարկ|datark|empty
ազատ|azat|free
զբաղված|zbaghvats|busy
ուրախ|urakh|happy
տխուր|tkhur|sad
հոգնած|hognats|tired
բարի|bari|kind; good
ծանր|tsanr|heavy
թեթև|tʼetʼev|light (weight)
լայն|layn|wide
նեղ|negh|narrow
հաստ|hast|thick
բարակ|barak|thin
խելացի|khelatsʼi|clever; smart
հետաքրքիր|hetakʼkʼir|interesting
կարևոր|karevor|important
նույն|nuyn|same
ուրիշ|urish|other; different
մութ|mutʼ|dark
քաղցր|kʼaghtsʼr|sweet
թթու|tʼtʼu|sour
դառը|darrə|bitter
աղի|aghi|salty
"""
W['questions'] = """
ինչպես|inchʼpes|how
քանի|kʼani|how many
ինչքան|inchʼkʼan|how much
որ|vor|which; that
ում|um|whom
այս|ays|this
այդ|ayd|that (near you)
այն|ayn|that (far)
բոլոր|bolor|all
ամեն|amen|every
ամեն ինչ|amen inchʼ|everything
ոչինչ|vochʼinchʼ|nothing
քիչ|kʼichʼ|few; a little
միայն|miayn|only
նաև|nayev|also
եթե|yetʼe|if
մեջ|mej|in; inside
վրա|vra|on
տակ|tak|under
հետ|het|with
համար|hamar|for
առանց|arrantsʼ|without
մինչև|minchev|until
առաջին|arrajin|first
երկրորդ|yerkrord|second
երրորդ|yerrord|third
կես|kes|half
"""
W['numbers'] = """
զրո|zro|zero
տասնմեկ|tasnmek|eleven
տասներկու|tasnerku|twelve
քսան|kʼsan|twenty
երեսուն|yeresun|thirty
քառասուն|kʼarrasun|forty
հիսուն|hisun|fifty
վաթսուն|vatʼsun|sixty
յոթանասուն|yotʼanasun|seventy
ութսուն|utʼsun|eighty
իննսուն|innsun|ninety
հարյուր|haryur|hundred
հազար|hazar|thousand
"""
W['animals'] = """
շուն|shun|dog
կատու|katu|cat
ձի|dzi|horse
կով|kov|cow
ոչխար|vochʼkhar|sheep
այծ|ayts|goat
խոզ|khoz|pig
թռչուն|tʼrrchʼun|bird
մեղու|meghu|bee
մուկ|muk|mouse
արջ|arj|bear
գայլ|gayl|wolf
աղվես|aghves|fox
առյուծ|arryuts|lion
փիղ|pʼigh|elephant
կապիկ|kapik|monkey
նապաստակ|napastak|rabbit
օձ|odz|snake
թիթեռ|tʼitʼerr|butterfly
ճանճ|chanch|fly
մրջյուն|mrjyun|ant
կենդանի|kendani|animal; alive
էշ|esh|donkey
արծիվ|artsiv|eagle
գառ|garr|lamb
սագ|sag|goose
բադ|bad|duck
"""
W['nature'] = """
արև|arev|sun
լուսին|lusin|moon
աստղ|astgh|star
երկինք|yerkinkʼ|sky
ամպ|amp|cloud
անձրև|andzrev|rain
ձյուն|dzyun|snow
քամի|kʼami|wind
կրակ|krak|fire
հող|hogh|soil; earth
քար|kʼar|stone
լեռ|lerr|mountain
գետ|get|river
լիճ|lich|lake
ծով|tsov|sea
անտառ|antarr|forest
ծառ|tsarr|tree
ծաղիկ|tsaghik|flower
վարդ|vard|rose
խոտ|khot|grass
տերև|terev|leaf
դաշտ|dasht|field
օդ|od|air
եղանակ|yeghanak|weather
ժայռ|zhayrr|rock; cliff
ավազ|avaz|sand
կայծակ|kaytsak|lightning
ամպրոպ|amprop|thunder
արևոտ|arevot|sunny
Արարատ|Ararat|Ararat
Սևան|Sevan|Sevan (lake)
"""
W['work'] = """
աշխատանք|ashkhatankʼ|work; job
դասարան|dasaran|classroom
դաս|das|lesson
ուսուցիչ|usutsʼichʼ|teacher
աշակերտ|ashakert|pupil
ուսանող|usanogh|student
գրիչ|grichʼ|pen
մատիտ|matit|pencil
տետր|tetr|notebook
թուղթ|tʼughtʼ|paper
հարց|hartsʼ|question
պատասխան|pataskhan|answer
բառ|barr|word
նախադասություն|nakhadasutyun|sentence
տառ|tarr|letter (of alphabet)
թիվ|tʼiv|number
պատմություն|patmutyun|story; history
մաթեմատիկա|matʼematika|mathematics
գիտություն|gitutyun|science
արվեստ|arvest|art
երաժշտություն|yerazhshtutyun|music
գրասենյակ|grasenyak|office
ընկերություն|ənkerutyun|company; friendship
գործ|gorts|work; business; deed
աշխատավարձ|ashkhatavardz|salary
փող|pʼogh|money
գին|gin|price
ինժեներ|inzhener|engineer
ծրագրավորող|tsragravorogh|programmer
նամակ|namak|letter; mail
հաշիվ|hashiv|bill; account
շնորհավոր|shnorhavor|congratulations
Բարի ախորժակ|bari akhorzhak|bon appétit
"""

cards = []
for ch, tr, hint, (ehy, etr, een) in LETTERS:
    cards.append({'id': ch, 't': 'l', 'g': 0, 'hy': ch.upper() + ' ' + ch, 'tr': tr, 'en': [hint], 'cat': 'alphabet',
                  'ex': [ehy, etr, een]})
words = []
for cat, block in W.items():
    for line in block.strip().splitlines():
        p = line.split('|')
        hy, tr, en = p[0], p[1], [x.strip() for x in p[2].split(';')]
        ex = p[3:6] if len(p) >= 6 and p[3] else None
        words.append({'id': hy, 't': 'w', 'g': 0, 'hy': hy, 'tr': tr, 'en': en, 'cat': cat, 'ex': ex})
for i, w in enumerate(words):
    w['g'] = i // 50 + 1
cards += words

# checks
ids = [c['id'] for c in cards]
assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
assert len([c for c in cards if c['t'] == 'l']) == 38   # 37 letters + և
assert 'ու' not in [c['id'] for c in cards if c['t'] == 'l']
ARM = re.compile(r'^[Ա-և ]+$')
for c in cards:
    assert ARM.match(c['hy']), c['hy']
    if c['ex']:
        assert len(c['ex']) == 3 and re.search(r'[Ա-և]', c['ex'][0]), c['id']
assert all(w['ex'] for w in words[:150]), [w['id'] for w in words[:150] if not w['ex']]

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(cards, f, ensure_ascii=False, separators=(',', ':'))
by_g = {}
for c in cards:
    by_g[c['g']] = by_g.get(c['g'], 0) + 1
print('cards', len(cards), 'letters', 38, 'words', len(words), 'with example', sum(1 for w in words if w['ex']))
print('per g', dict(sorted(by_g.items())))
for w in words[:12]:
    print(w['hy'], w['tr'], w['en'])
