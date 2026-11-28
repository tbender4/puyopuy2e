"""Saturn skit and ending voice subtitles in English (saturn_cutscenes.apply_subtitles).

PUYOSHOW script entry: [(first frame, last frame, (x, y) for the SPEAKER placement, text)]. Frames
count from the script start (endings: the frames the interpreter runs, scene loads stall it); the AIF
starts 27 frames later (endings: 34 to 63). (x, y) is the caption's
bottom-centre. A \n breaks a line where it reads better. Each line's comment: who speaks and the
Japanese. Wording starts from Domino054's translated cutscene videos."""
SUBTITLES = {
    0: [  # AUL_N.AIF
        (284, 558, (223, 115), 'You came all the way here? Bad luck for you.'),  # opponent: ここへ来てしまうとは、運のない奴め。
        (617, 868, (95, 117), "Whoa, that's dangerous! How rude!"),  # Arle: うわっ、危ないよ!乱暴だな!
        (877, 1033, (223, 115), "Don't you mouth off to me!"),  # opponent: 生意気な口を叩きおって、
        (1039, 1304, (223, 115), 'My claws will make you fall like petals\nin the Puyo Underworld!'),  # opponent: 俺様の爪で、ぷよぷよ地獄の花と散れ!
    ],
    2: [  # AUL_T.AIF
        (243, 398, (223, 115), 'Ora-ora-ora-oraaa!'),  # opponent: オラオラー!
        (386, 465, (95, 117), 'Whoa!'),  # Arle: ワッ!
        (813, 1079, (223, 115), "Nicely dodged. But that's as far as you go."),  # opponent: よく避けたな。だが、そこまでよ。
        (1160, 1422, (223, 115), "You see, I can read other people's minds."),  # opponent: 俺様は、相手の心を読むことができるんだからな。
        (1429, 1532, (95, 117), "Th-that's cheating!"),  # Arle: ず、ずるい!
        (1542, 1823, (223, 115), 'Oho, I see. I get it! I see, I see!'),  # opponent: ほー、そうか。なるほど!そうかそうか!
        (1831, 2041, (223, 115), 'You want to battle me in the Puyo Underworld!'),  # opponent: お前は、ぷよぷよ地獄で勝負したいのか!
        (2071, 2240, (95, 117), "I wasn't thinking that at all!"),  # Arle: ぼく、そんなこと思ってないよ!
        (2243, 2401, (223, 115), 'Enough back-talk! Here I come!'),  # opponent: ええい!つべこべぬかすな!行くぞ!
    ],
    4: [  # BARO_N.AIF
        (346, 421, (200, 118), 'Meh!'),  # opponent: めー
        (397, 594, (72, 118), 'Oh, how cute!'),  # Arle: あ、かわいい!
        (607, 791, (200, 118), 'Meh, meh, meh-meh!'),  # opponent: めー、めー、めめー!
        (779, 883, (72, 118), 'Hm? What is it?'),  # Arle: ん?なに?
        (900, 1080, (200, 118), 'Meh-meh-meeh! Meh-meh-meh-meh-meeh!'),  # opponent: めめめー!めめめめめー!
        (1100, 1331, (72, 118), "Sorry, I can't tell what you're saying."),  # Arle: ごめーん、なんて言ってるのかわかんないよ
        (1313, 1447, (200, 118), 'No good, meeh!'),  # opponent: だめだめー!
    ],
    6: [  # BARO_T.AIF
        (320, 596, (95, 117), 'Whoa, a blatantly suspicious plant...'),  # Arle: やや、あからさまに、あやしい植物が
        (614, 692, (224, 56), 'Meeh~'),  # opponent: メー
        (716, 799, (95, 117), 'It made a sound!'),  # Arle: 鳴いた
        (817, 907, (224, 56), 'Moo~'),  # opponent: モー
        (931, 1153, (95, 117), 'A sheep... and it goes "moo"?!'),  # Arle: 羊、それもモーって鳴く
        (1171, 1320, (95, 117), 'Wh-what are you?!'),  # Arle: な、何者なの
        (1326, 1428, (224, 56), 'Moo~'),  # opponent: モー
    ],
    8: [  # COCKA_N.AIF
        (284, 464, (95, 117), 'Is that my last opponent?'),  # Arle: あれが、最後の相手かな?
        (698, 906, (95, 117), "If you're that fat, you can't fly."),  # Arle: そんなに太ってたら、飛べないよ。
        (998, 1081, (95, 117), 'Whoa!'),  # Arle: うわっ!
        (1087, 1193, (95, 117), 'S-sorry!'),  # Arle: ご、ごめんなさい!
    ],
    10: [  # COCKA_T.AIF
        (350, 470, (95, 117), 'Wh-what is this?!'),  # Arle: な、なにこれ
        (589, 823, (95, 117), 'Whoa! Attacking out of nowhere? No fair!'),  # Arle: うわぁ、いきなりなんて卑怯だよ
        (1087, 1179, (95, 117), 'STOP!'),  # Arle: ストップ!
        (1205, 1408, (95, 117), 'This calls for a Puyo Puyo battle, right? Right?'),  # Arle: やっぱりここは、ぷよぷよで勝負だよね、ね
        (1410, 1515, (95, 117), 'Puyo puyo puyo puyo...'),  # Arle: ぷよぷよぷよぷよ…
        (1517, 1599, (95, 117), 'Waaah!'),  # Arle: うえぇー
        (1601, 1821, (95, 117), 'Just start the Puyo Puyo already!'),  # Arle: もう、ぷよぷよ始めてー
    ],
    12: [  # DRACO_N.AIF
        (241, 645, (95, 117), 'Hey, you! If I win our battle,\nyou have to let me through.'),  # Arle: そこの君、勝負して僕が勝ったらここを通してもらうからね
        (644, 838, (229, 114), 'A battle? You mean a beauty contest?'),  # opponent: 勝負って、まさか美少女コンテスト?
        (838, 1131, (95, 117), 'Hmph, you think you can beat a cutie like me?'),  # Arle: ふふん、この可憐な僕に勝てるとでも?
        (1142, 1385, (95, 117), 'W-wait, no! The battle is in the Puyo Underworld!'),  # Arle: て、ちっがーう!勝負はぷよぷよ地獄だ!
    ],
    14: [  # DRACO_T.AIF
        (229, 409, (271, 110), 'Today is the day we settle this.'),  # opponent: 今日という今日こそ、決着をつけるわよ。
        (419, 604, (95, 117), "Huh? Haven't you learned your lesson?"),  # Arle: ええ?まだ懲りてないの?
        (608, 694, (271, 110), 'Of course not.'),  # opponent: 当たり前よ。
        (720, 833, (271, 110), 'Now, change into your swimsuit.'),  # opponent: さあ、水着に着替えて。
        (844, 1067, (95, 117), 'A swimsuit? Not the Puyo Underworld?'),  # Arle: 水着?ぷよぷよ地獄じゃないの?
        (1081, 1342, (271, 110), "I can't win at that, so we're having\na beauty contest instead!"),  # opponent: それじゃ敵わないから、美少女コンテストで勝負しようってんじゃない。
        (1487, 1562, (95, 117), 'Ah!'),  # Arle: ああ!
        (1572, 1820, (95, 117), 'Wait, wait! This really calls\nfor the Puyo Underworld.'),  # Arle: 待った待った。ここはやっぱりぷよぷよ地獄しかないって。
        (1822, 1959, (95, 117), 'No, really.'),  # Arle: いや、ほんとに。
    ],
    16: [  # DRAGO_N.AIF
        (343, 586, (127, 117), "That's dangerous! Stop it!"),  # Arle: あぶないじゃない!やめてよ!
        (720, 950, (127, 117), "If that's how you want it, take this!"),  # Arle: 君がそんなことするんなら、僕はこうだ!
    ],
    18: [  # DRAGO_T.AIF
        (280, 420, (95, 85), 'Wow! A dragon!'),  # Arle: わぁ!ドラゴンだ!
        (437, 512, (223, 114), 'Rawr!'),  # opponent: ガウ!
        (540, 686, (95, 85), 'I can turn into a dragon too!'),  # Arle: 僕もドラゴンになれるんだよ!
        (684, 759, (223, 114), 'Rawr?'),  # opponent: ガウ?
        (759, 883, (95, 85), 'Illusion!'),  # Arle: イリュージョン!
        (1011, 1086, (95, 85), 'See?'),  # Arle: ほらね!
        (1102, 1177, (223, 114), 'Rawr-rawr!'),  # opponent: ガウガウ!
        (1173, 1414, (95, 85), 'What? You want to fight? Fine!'),  # Arle: なに?やるって言うの?いいよ!
        (1437, 1516, (223, 114), 'Rawr!'),  # opponent: ガウ!
    ],
    20: [  # FUFUF_N.AIF
        (310, 547, (223, 115), 'Fufu... so you came.'),  # opponent: うふふ、来たのね。
        (573, 670, (95, 117), 'Y-yes, I came...?'),  # Arle: き、来たけど?
        (690, 784, (223, 115), 'Fufufu.'),  # opponent: うふふ。
        (803, 892, (95, 117), 'Wh-what?'),  # Arle: な、なに?
        (902, 1074, (223, 115), "Fufu... so you're going."),  # opponent: うふふ、行くのね。
        (1089, 1164, (95, 117), 'Going where?'),  # Arle: どこへ?
        (1184, 1265, (223, 115), 'Fufufu.'),  # opponent: うふふ。
    ],
    22: [  # FUFUF_T.AIF
        (512, 685, (223, 114), 'Fufu... are you buying?'),  # opponent: うふふ、買うのね?
        (706, 877, (95, 117), 'Nope, not buying.'),  # Arle: ううん、買わない
        (948, 1158, (223, 114), 'Fufu... then what are you selling?'),  # opponent: うふふ、何を売るのかな?
        (1197, 1354, (95, 117), 'Nope, not selling anything.'),  # Arle: ううん、何にも売らない
        (1336, 1566, (223, 114), 'Then what did you come here for?'),  # opponent: じゃあ、何しに来たのね?
        (1586, 1797, (95, 117), 'Fufufu... what did I come here for?'),  # Arle: ふふふ、何をしに来たんでしょう
        (1779, 1970, (223, 114), 'No copying me!'),  # opponent: マネは許さないのね
    ],
    24: [  # HARPY_N.AIF
        (330, 584, (223, 97), '~Harahore hirehare~'),  # opponent: あらほれひれはれ
        (566, 707, (95, 117), "Hey, I'm coming through."),  # Arle: ねぇ、ここ通るよ
        (689, 961, (223, 97), '~Harahore hirehare~'),  # opponent: あらほれひれはれ
        (943, 1040, (95, 117), 'Are you listening?'),  # Arle: 聞いてる?
        (1022, 1245, (223, 97), '~Harahore hirehare~'),  # opponent: あらほれひれはれ
        (1227, 1410, (95, 117), 'As good as ever...'),  # Arle: あいかわらずうまいな
        (1392, 1467, (223, 97), '~Harahore~'),  # opponent: あらほれひれはれ
        (1416, 1491, (95, 117), "I'm enchanted."),  # Arle: 聞き惚れるよ
        (1470, 1571, (223, 97), '~Hirehare~'),  # opponent: あらほれひれはれ
        (1553, 1663, (95, 117), 'So you CAN hear me!'),  # Arle: ちゃんと聞こえてんじゃない
    ],
    26: [  # HARPY_T.AIF
        (330, 579, (223, 97), '~Harahore hirehare~'),  # opponent: ハラホレヒレハレ
        (561, 637, (95, 117), 'Again?'),  # Arle: また?
        (619, 729, (223, 97), 'What is it?'),  # opponent: 何です?
        (731, 1086, (223, 97), 'I was singing so happily~'),  # opponent: 気持ちよく歌ってたのに
        (1068, 1302, (95, 117), 'It may feel good to you, but not to me!'),  # Arle: 君は良くても僕は良くないの
        (1317, 1424, (223, 97), 'B-but...'),  # opponent: そ、そんな
        (1426, 1809, (223, 97), "Then let's settle this\nin the Puyo Underworld~!"),  # opponent: では、ぷよぷよ地獄で勝負するです
    ],
    28: [  # INKYU_N.AIF
        (265, 376, (223, 115), 'Hi, honey.'),  # opponent: ハイ、ハニー
        (358, 449, (95, 117), 'Are you my third opponent?'),  # Arle: あなたが3番手?
        (471, 645, (223, 115), "That's right. The one who charms every woman,"),  # opponent: そう、どんな女性でもトリコにする
        (647, 817, (223, 115), 'Incubus, is me.'),  # opponent: インキュバスとは私のこと
        (819, 1062, (223, 115), 'Now you too will fall under my charm, miss.'),  # opponent: お嬢さんもこれで私のトリコになるのだ
        (1064, 1197, (223, 115), "Aren't you happy?"),  # opponent: 嬉しいだろう
        (1228, 1303, (95, 117), 'And?'),  # Arle: それで?
        (1283, 1514, (223, 115), "What? My good looks don't work on you?!"),  # opponent: なに、私の美形アタックが効かないというのか
        (1496, 1662, (95, 117), 'Well, looks like that...'),  # Arle: だって、その程度なら
        (1684, 1874, (95, 117), "I'm used to them from Satan and Shezo."),  # Arle: サタンやシェゾで見慣れてるもん
        (1856, 2105, (223, 115), 'Tch... then be charmed by Puyo Puyo instead!'),  # opponent: くっ、それではぷよぷよのトリコになるがいい
    ],
    30: [  # INKYU_T.AIF
        (255, 451, (95, 117), "Weren't you the one in Practice mode?"),  # Arle: あなた、練習モードにいた人ね?
        (547, 660, (223, 115), 'That was my little brother.'),  # opponent: あれは弟なのだよ。
        (662, 1003, (223, 115), "Normally, miss, I'd love to... your... and..."),  # opponent: 本来ならばお嬢さんの…を…したり、
        (985, 1060, (95, 117), 'Huh?'),  # Arle: え?
        (1083, 1279, (223, 115), '...while draining your life force, but...'),  # opponent: …しながら精気を吸いたいところだが。
        (1300, 1404, (95, 117), 'A-and if you did that?'),  # Arle: そ、そんなことしたら?
        (1403, 1677, (223, 115), 'Right. Then this would be adults only.'),  # opponent: そう。18歳未満お断りになってしまうのだ。
        (1688, 1763, (223, 115), 'So...'),  # opponent: だから。
        (1724, 1799, (95, 117), 'So?'),  # Arle: だから?
        (1805, 2037, (223, 115), "I'll drain your life force\nin the Puyo Underworld instead."),  # opponent: ぷよぷよ地獄で精気を吸うことにする。
        (2047, 2177, (95, 117), 'Phew, what a relief.'),  # Arle: ふぅ、よかった。
    ],
    32: [  # KETSY_N.AIF
        (264, 399, (202, 100), 'Nyanyanya! Nyanyanya!'),  # opponent: ニャニャニャン ニャニャニャン
        (381, 524, (72, 102), 'Wow, twins!'),  # Arle: わあ、双子だ
        (571, 764, (202, 100), "Let's battle, meow! Battle, meow!"),  # opponent: さあ、勝負ニャン、勝負ニャン
        (858, 1058, (72, 102), 'Sure, but with which of you?'),  # Arle: いいけど、どっちと?
        (1069, 1243, (202, 100), 'Me, meow! Me, meow!'),  # opponent: あたしだニャン、あたしだニャン
    ],
    34: [  # KETSY_T.AIF
        (271, 519, (191, 115), 'I hate the cold, meow. Hate it, meow.'),  # opponent: 寒いのは嫌いだニャン、嫌いだニャン
        (501, 735, (95, 117), "Yeah, I don't like the cold either."),  # Arle: うんうん、僕も寒いのは嫌だ
        (717, 1057, (191, 115), 'But I love sleeping, meow! Love it, meow!'),  # opponent: でも眠るのは大好きだニャン、大好きだニャン
        (1021, 1332, (95, 117), 'Right! Sleeping is pure bliss.'),  # Arle: そうそう、眠ってるときは幸せだよね
        (1314, 1558, (191, 115), 'We get along, meow! Get along, meow!'),  # opponent: あなたとは気が合うニャン、合うニャン
        (1560, 1763, (191, 115), "Let's play Puyo Puyo together, meow!"),  # opponent: 一緒にぷよぷよするニャン、するニャン
        (1765, 1962, (191, 115), 'Puyo Puyo with you, meow!'),  # opponent: あなたと一緒にぷよぷよするニャン
    ],
    36: [  # MAMON_N.AIF
        (348, 754, (95, 117), 'Whoa! An entrance this grand means\nthis has to be the final battle!'),  # Arle: はっ!このものものしい登場の仕方は、いよいよラストバトルってことね!
        (771, 846, (223, 115), 'Gobe!'),  # opponent: ゴベ!
        (835, 1037, (95, 117), "Huh? It isn't? That's weird..."),  # Arle: え?違うの?おかしいな、
        (1039, 1397, (95, 117), 'You have such an evil face,\nI was sure...'),  # Arle: そんな凶悪な顔してるんだもん、僕、てっきり…
        (1399, 1476, (95, 117), 'Ah!'),  # Arle: あっ!
    ],
    38: [  # MAMON_T.AIF
        (316, 534, (95, 117), "Wow, it's huge! A statue of a monster!"),  # Arle: うわあ、おっきい。魔物の像だわ。
        (536, 725, (95, 117), 'It looks just like the real thing.'),  # Arle: まるで本物みたい。
        (814, 899, (95, 117), 'Amazing!'),  # Arle: すっごいなあ。
        (901, 1127, (95, 117), 'Even the sharp claws and fur are there.'),  # Arle: 鋭い爪や毛まで再現してあるよ。
        (1129, 1403, (95, 117), 'A skilled craftsman made this for sure.'),  # Arle: これは腕のいい職人さんの手によるものだね。
        (1465, 1606, (95, 117), 'Whoa, its eyes moved!'),  # Arle: うわあ、目が動いた。
        (1608, 1726, (95, 117), 'It even has gimmicks like that!'),  # Arle: あんなギミックまであるとは。
        (1728, 1806, (95, 117), 'Wow, wow!'),  # Arle: すごいすごい
        (1808, 1942, (95, 117), 'It even roars!'),  # Arle: おまけに鳴くなんて。
        (1976, 2160, (95, 117), "Ah! It's real!"),  # Arle: あ!本物だった!
    ],
    40: [  # MASKD_N.AIF
        (257, 607, (223, 117), 'Hmph. Wandering into a place like this?\nYou must be quite the fool.'),  # opponent: …ふん。こんなところへ迷い込むとは、なかなかとぼけた奴だな。
        (598, 673, (95, 117), 'Ehehe...'),  # Arle: えへへへっ
        (635, 735, (223, 117), 'That was not a compliment.'),  # opponent: 褒めたわけではない。
        (829, 1136, (223, 117), '...Very well. As a reward for coming this far,\nI shall show you my strength.'),  # opponent: …まあよい。ここまで来た褒美にわたしの強さを見せてやる。
        (1160, 1433, (95, 117), "Whoa! C-could it be... you're..."),  # Arle: うわあ!!も、もしかして…あんた…
    ],
    42: [  # MASKD_P.AIF
        (280, 565, (223, 117), 'My name is Masked Satan,'),  # opponent: 我が名はマスク・ド・サタン
        (567, 881, (223, 117), 'the prince of darkness\nwho rules this world of magic!'),  # opponent: この魔導の世界を支配する、闇の貴公子なり
        (902, 1211, (95, 117), "Huh? Aren't you Satan?"),  # Arle: あれ?あんた、サタンじゃないの?
        (1238, 1602, (223, 117), 'N-no! I am Masked Satan!'),  # opponent: ち、ちがう!わたしはマスク・ド・サタンだ!
        (1740, 1961, (223, 117), "Stop looking at me like that. It's no use!"),  # opponent: やめろ、そんなまなざしで私を見ても無駄だぞ
        (2004, 2141, (95, 117), 'Then take off that mask.'),  # Arle: それじゃあ、その仮面取ってよ
        (2292, 2367, (223, 117), 'Eh? What?'),  # opponent: え、何?
        (2384, 2500, (95, 117), 'I said, take off the mask!'),  # Arle: 仮面、取ってってば
        (2570, 2781, (223, 117), 'Ha ha ha! You fell right into my trap!'),  # opponent: はっはっは、まんまと罠にかかりおって
        (2783, 2989, (223, 117), 'If you can beat me in the Puyo Underworld,'),  # opponent: この私にぷよぷよ地獄で勝つことができれば、
        (2991, 3176, (223, 117), "I'll take you on a scandalous date!"),  # opponent: お前とスキャンダラスなデートをしてやろうじゃないか
        (3158, 3296, (95, 117), 'Listen to me, would you?!'),  # Arle: 人の話を聞かんかい
    ],
    44: [  # MINIZ_N.AIF
        (292, 432, (223, 115), 'Ukeh? Ukeeh!'),  # opponent: うけー?うけー!
    ],
    46: [  # MINIZ_T.AIF
        (270, 365, (233, 115), 'Here I come!'),  # opponent: 行くぞ!
        (426, 523, (95, 117), 'All right, bring it!'),  # Arle: よーし、来い!
        (578, 675, (95, 117), 'Ah! Look out!'),  # Arle: あ!危ない!
        (864, 1243, (95, 117), "Oh, fine. I'll wait,\nso hurry and gather up your body."),  # Arle: しょうがないな。待っててあげるから、早く体を集めなよ。
        (1243, 1318, (233, 115), 'Ugeh.'),  # opponent: うげ。
    ],
    48: [  # MINO_N.AIF
        (249, 374, (188, 104), 'Mooo!'),  # opponent: ンモー
        (356, 567, (72, 102), "Y-you're really fired up..."),  # Arle: ず、ずいぶんと力が入ってるなぁ
        (590, 747, (188, 104), 'M-m-mooo!'),  # opponent: ン、ン、ンモー
        (729, 782, (72, 102), 'Waah!'),  # Arle: うわぁ
        (784, 883, (72, 102), "Th-that can't be good!"),  # Arle: ま、まずい!
    ],
    50: [  # MINO_T.AIF
        (293, 560, (223, 114), 'Hmm. Nothing beats a brand-new axe and nose ring.'),  # opponent: ふむ。やはりオノと鼻輪は新しいものに限るな。
        (584, 883, (95, 117), "A n-nose ring?! You're into wearing those?!"),  # Arle: は、鼻輪!?君、そんなの付ける趣味あったの!?
        (925, 1097, (223, 114), 'Wha?! When did you get behind me?!'),  # opponent: はっ!いつの間にわしの背後に、
        (1099, 1324, (223, 114), 'The secret I kept even from Lady Rulue...'),  # opponent: ルルー様にも内緒にしていた秘密を、
        (1326, 1548, (223, 114), "Now that you know it, you won't leave alive!"),  # opponent: 秘密を知られたからには、生かしておけん!
    ],
    52: [  # MOMOM_N.AIF
        (302, 554, (223, 121), "Mm, welcome~! What'll it be?"),  # opponent: んー、いらっしゃーい。なにー?
        (562, 749, (95, 117), "Oh, no, I'm not a customer..."),  # Arle: あっ、いや、僕はお客じゃ。
        (736, 843, (223, 121), 'No window-shopping.'),  # opponent: ひやかしはだめ。
        (877, 977, (223, 121), "You're bad for business."),  # opponent: 商売の邪魔。
        (992, 1100, (95, 117), "Who's in whose way?"),  # Arle: 邪魔はどっちだよ。
        (1118, 1267, (95, 117), 'Opening a shop in a place like this...'),  # Arle: こんなとこにお店を出すなんて。
        (1307, 1388, (223, 121), 'Mm, then...'),  # opponent: んー、じゃあ、
        (1422, 1616, (223, 121), 'By Momomo Clan law, we settle it with Puyo Puyo.'),  # opponent: モモモ族のおきて、ぷよぷよで勝負。
        (1656, 1759, (223, 121), 'If you win,'),  # opponent: あなたが勝てば、
        (1770, 1862, (223, 121), "I'll close up shop~."),  # opponent: 店、たたむよー。
    ],
    54: [  # MOMOM_T.AIF
        (286, 537, (223, 122), 'Nngh... nngh... nngh...'),  # opponent: んー、んー、んー。
        (522, 615, (95, 114), 'That looks heavy.'),  # Arle: 重そうだね。
        (643, 728, (95, 114), "I'll help you."),  # Arle: 手伝ってあげるよ。
        (752, 877, (223, 122), 'Oh, how kind!'),  # opponent: おお、なんて親切。
        (936, 1125, (223, 122), 'Please take this Puyo bun as thanks.'),  # opponent: お礼に、このぷよまんを。
        (1122, 1299, (95, 114), "No, no, that's not why I helped."),  # Arle: いいよ、いいよ。僕、そんなつもりじゃ。
        (1308, 1415, (223, 122), 'How modest!'),  # opponent: なんて奥ゆかしい。
        (1441, 1622, (223, 122), 'Then how about this Puyo Underworld?'),  # opponent: じゃあ、このぷよぷよ地獄は。
        (1841, 1967, (95, 114), 'P-Puyo Underworld?'),  # Arle: ぷ、ぷよぷよ地獄?
        (2005, 2148, (223, 122), "It's something special. Really amazing."),  # opponent: ひと味違う、すごいの。
        (2156, 2241, (223, 122), 'Go on, help yourself.'),  # opponent: さあ、どうぞ。
    ],
    56: [  # MUMMY_N.AIF
        (275, 491, (219, 109), 'Oh, you came at just the right time!'),  # opponent: おう、これはいいところに!
        (488, 563, (95, 117), "What's wrong?"),  # Arle: どうしたの?
        (565, 784, (219, 109), "I'm all tangled up in my bandages\nand I can't move!"),  # opponent: 包帯が絡まって、動けないんだわさ
        (766, 991, (95, 117), "Th-that's so lame..."),  # Arle: か、かっこ悪ぅ
        (973, 1048, (219, 109), 'Hm?'),  # opponent: ん?
        (1124, 1280, (219, 109), 'There, all better!'),  # opponent: これで、OKだわさ
    ],
    58: [  # MUMMY_T.AIF
        (290, 398, (223, 114), 'Haaaah!'),  # opponent: ハァー!
        (398, 650, (95, 117), "Wow! Such power,\nand you're not even fighting!"),  # Arle: 凄い!戦ってないのになんて気なの?
        (671, 823, (223, 114), 'This is only the beginning!'),  # opponent: こんなのまだまだ序の口だわさ!
        (877, 952, (223, 114), 'Hah!'),  # opponent: ハァ!
        (1031, 1237, (95, 117), 'Ah! Your energy fizzled out!'),  # Arle: あ!気がすっぽ抜けた!
        (1307, 1482, (223, 114), 'W-well, that happens all the time!'),  # opponent: まぁ…まぁよくあることだわさ!
        (1530, 1710, (223, 114), "I'll pull myself together. Now let's battle!"),  # opponent: 気を取り直して勝負だわさ!
        (1758, 1833, (223, 114), 'Haaah!'),  # opponent: ハァー!
    ],
    60: [  # NASU_N.AIF
        (258, 619, (95, 117), "Lucky! Nobody's here!\nThen I'll just go on through!"),  # Arle: ラッキー!誰もいないよ!じゃあ、ここは遠慮なく!
        (634, 719, (223, 115), 'Naaasu!'),  # opponent: なーす!
        (723, 917, (95, 117), 'Whoa! That goofy cry!'),  # Arle: わっ!このまぬけな叫び声は!
        (980, 1198, (95, 117), 'Ow, that hurts! What was that for?'),  # Arle: いったいなーもう!いきなり何すんの?
        (1209, 1340, (223, 115), 'No questions asked, naaasu!'),  # opponent: 問答無用なーす!
    ],
    62: [  # NASU_T.AIF
        (267, 416, (223, 115), 'Lame-brain, naaasu!'),  # opponent: おたんこなーっす
        (398, 651, (95, 117), 'There you are! I was looking for you.'),  # Arle: 現れたね、君を探してたんだよ
        (633, 708, (223, 115), 'Nasu?'),  # opponent: なす?
        (699, 1002, (95, 117), 'I powered up my Fire spell just for today.'),  # Arle: この日のためにファイヤーの呪文の火力を上げておいたんだ。
        (1008, 1238, (95, 117), 'You have to roast them nice and crispy.'),  # Arle: やっぱり強火でこんがりと焼かないとね。
        (1231, 1313, (223, 115), 'Nasu-nasu?'),  # opponent: ナスナス?
        (1322, 1562, (95, 117), 'Now, be a grilled eggplant for me!'),  # Arle: さあ、僕のために焼きナスになってよ。
        (1562, 1647, (223, 115), 'Dummy, naaasu!'),  # opponent: ボケナース!
    ],
    64: [  # NOHOH_N.AIF
        (334, 441, (223, 114), 'Nohoho.'),  # opponent: のほほ
        (423, 585, (95, 117), "What's that supposed to be?"),  # Arle: それ、何の真似?
        (652, 740, (223, 114), 'Nohoho.'),  # opponent: のほほ
        (722, 875, (95, 117), "Ew, that's gross!"),  # Arle: もう、ばっちいな
        (857, 956, (223, 114), 'Nohoho.'),  # opponent: のほほ
        (958, 1156, (223, 114), 'Leave me alone. I hate nosy people.'),  # opponent: ほっといて、うるさい人は嫌い
        (1138, 1279, (95, 117), 'Aaaah!'),  # Arle: ああああ
    ],
    66: [  # NOHOH_T.AIF
        (153, 228, (95, 117), 'Hm?'),  # Arle: ん?
        (407, 528, (251, 114), 'Nhohohohoho!'),  # opponent: んほほほほほ
        (510, 641, (95, 117), "Wh-what's with you all of a sudden?"),  # Arle: な、なにいきなり
        (623, 701, (251, 114), 'Nhoho?'),  # opponent: んほほ?
        (728, 880, (251, 114), "It's a se-cret."),  # opponent: ひ、み、つ
        (862, 987, (95, 117), "Ugh, now I'm curious."),  # Arle: うぅ、気になる
        (989, 1125, (95, 117), 'Why were you laughing?'),  # Arle: なんで笑ってたの?
        (1181, 1256, (95, 117), 'Tell me!'),  # Arle: 教えてよ
        (1235, 1320, (251, 114), 'Nope.'),  # opponent: だめ
        (1302, 1433, (95, 117), 'Meanie!'),  # Arle: ケチ
        (1508, 1582, (251, 114), 'Nhoho.'),  # opponent: んほほ
        (1584, 1688, (251, 114), 'Oh, all right.'),  # opponent: 仕方ないの
        (1690, 1840, (251, 114), "I'll tell you just a little."),  # opponent: ちょっとだけ教えちゃう
        (1822, 1940, (95, 117), 'What is it? What is it?'),  # Arle: なんなの?なんなの?
        (1966, 2058, (251, 114), 'Nhoho...'),  # opponent: んほほ
        (2078, 2207, (251, 114), '...the Puyo Underworld.'),  # opponent: ぷよぷよ地獄
        (2189, 2432, (95, 117), 'Wh-why laugh about the Puyo Underworld?!'),  # Arle: な、なぜぷよぷよ地獄で笑う
    ],
    68: [  # NOMI_N.AIF
        (261, 524, (95, 117), "Huh? Nobody's here."),  # Arle: あれ?誰もいないや。
        (640, 724, (95, 117), 'Hellooo?'),  # Arle: もしもーし。
        (850, 1020, (95, 117), "Then I'll slip through while I can."),  # Arle: だったら、今のうちに。
        (1044, 1132, (95, 117), 'Waaah!'),  # Arle: うわあああ!
    ],
    70: [  # NOMI_T.AIF
        (312, 447, (95, 117), 'Is anyone here?'),  # Arle: ここにいる?
        (526, 714, (95, 117), 'Oh! You really are there!'),  # Arle: おー!確かにそこにいる!
        (735, 829, (95, 117), 'Looks like it.'),  # Arle: みたいだね
        (959, 1029, (95, 117), 'Hm?'),  # Arle: ん?
        (1031, 1094, (95, 117), "You're there, you're there!"),  # Arle: いるいる
        (1096, 1256, (95, 117), "You're really there this time!"),  # Arle: これは本当にいるよ
    ],
    72: [  # OOKAM_N.AIF
        (226, 468, (223, 117), "I'm your first opponent, the wolfman!"),  # opponent: オイラが一番手のオオカミ男なんですよ。
        (470, 661, (223, 117), 'Scary, right? Garooo!'),  # opponent: 怖いでしょ?ガルー。
        (670, 764, (95, 117), 'Not at all.'),  # Arle: ぜーんぜん。
        (859, 1125, (223, 117), "Ah, it's fine. Nobody's ever scared of me."),  # opponent: ああ、いいんです。どうせオイラなんか。
        (1192, 1267, (223, 117), 'Sulk, sulk...'),  # opponent: いじいじ…
        (1239, 1408, (95, 117), "Never mind that. We're playing Puyo Puyo, right?"),  # Arle: そんなことより、ぷよぷよするんでしょ?
        (1435, 1761, (223, 117), 'Never mind that? How mean! Garooo!'),  # opponent: そんなこととはひどいじゃないですか。ガルー。
        (1743, 1924, (95, 117), "Acting tough doesn't scare me."),  # Arle: すごんでも怖くないよ。
        (1938, 2050, (223, 117), 'Sulk, sulk...'),  # opponent: いじいじ…
    ],
    74: [  # OOKAM_T.AIF
        (258, 447, (223, 116), 'Awoooo!'),  # opponent: ウォー!!
        (429, 675, (95, 117), 'Oh, a wolf is howling.'),  # Arle: あっ、オオカミが遠吠えしてる
        (657, 742, (223, 116), 'Awoo?'),  # opponent: わおー?
        (724, 891, (95, 117), 'Whoa!'),  # Arle: うわっ
        (873, 1240, (223, 116), "Now that you know who I really am,\nI can't let you live!"),  # opponent: オイラの正体を知ったからには、生かしては置けないですよ
        (1273, 1584, (95, 117), "Um... your face is still a wolf's."),  # Arle: あのー、顔がオオカミのままなんですけど
    ],
    76: [  # PAKIS_N.AIF
        (268, 669, (227, 114), "Welcome~! My first customer in ages!\nI'm so happy!"),  # opponent: いらっしゃいーの、久々のお客さん、嬉しいの。
        (671, 850, (95, 117), "Don't get too excited..."),  # Arle: 喜ばれても困るな。
        (876, 1077, (227, 114), 'Play Puyo Puyo with me!'),  # opponent: 一緒にぷよぷよしてほしいの。
        (1146, 1349, (95, 117), 'Oh, fine. Sure.'),  # Arle: もう、仕方ないな。いいよ。
        (1368, 1479, (227, 114), 'Thank you!'),  # opponent: ありがたいの。
    ],
    78: [  # PAKIS_T.AIF
        (328, 420, (223, 114), 'Ta-da!'),  # opponent: ジャーン
        (402, 459, (95, 117), 'Ooh!'),  # Arle: おお
        (461, 697, (95, 117), "Isn't that the legendary Uranos Staff?!"),  # Arle: それは伝説のウラノススタッフでは
        (699, 842, (95, 117), 'I-I want it!'),  # Arle: ほ、ほしい
        (844, 991, (95, 117), 'Hey, hey, how much is it?'),  # Arle: ね、ね、いくらなの?
        (1005, 1142, (223, 114), 'Lend me your ear.'),  # opponent: 耳貸すの
        (1124, 1214, (95, 117), 'Okay, okay. Like this?'),  # Arle: はいはい、これで
        (1216, 1303, (95, 117), 'Uh-huh, uh-huh...'),  # Arle: ふんふん
        (1305, 1377, (95, 117), 'Huh?'),  # Arle: は?
        (1379, 1475, (95, 117), 'The Puyo Underworld?'),  # Arle: ぷよぷよ地獄?
        (1499, 1571, (95, 117), 'Never heard of it.'),  # Arle: 聞いたことない
        (1573, 1718, (95, 117), 'Must be some kind of currency.'),  # Arle: お金の単位だな
        (1700, 1840, (223, 114), 'Quit playing dumb!'),  # opponent: ボケはやめんの
        (1822, 1906, (95, 117), 'Eek!'),  # Arle: ひゃっ
    ],
    80: [  # PANO_N.AIF
        (320, 363, (95, 117), "What's that?"),  # Arle: 何これ?
        (365, 570, (95, 117), 'How annoying!'),  # Arle: うっとうしいなー
        (552, 731, (223, 114), "H-how rude! That's my flute!"),  # opponent: し、失礼な、僕の笛の音だぞ
        (713, 788, (95, 117), 'That?'),  # Arle: これが?
        (805, 989, (95, 117), 'Sounds like flies buzzing to me.'),  # Arle: ハエが飛んでるようにしか聞こえないけど
        (971, 1073, (223, 114), 'Whaaat?'),  # opponent: なにー?
        (1075, 1243, (223, 114), "Someone who doesn't get art, like you..."),  # opponent: お前みたいな芸術のわからない奴なんか
        (1245, 1380, (223, 114), '...gets this!'),  # opponent: こうだー!
    ],
    82: [  # PANO_T.AIF
        (350, 515, (95, 117), "Wh-what's this melody...?"),  # Arle: こ、この旋律は…
        (522, 875, (223, 114), "Hear my magic flute,\nand you can't help doing a goofy dance!"),  # opponent: この魔法の笛の音を聴くと、マヌケな踊りをせずにはいられないだろう!
        (867, 1098, (95, 117), 'Nooo! Not this dance!'),  # Arle: いやだー!こんな踊りは!
        (1264, 1525, (223, 114), 'Ahahaha! H-how goofy!'),  # opponent: あはははは!な、なんてマヌケなんだ!
        (1543, 1714, (95, 117), 'Ah, the music stopped!'),  # Arle: あ、音が止んだ!
        (1743, 1980, (95, 117), "Now's my chance! On to the Puyo Underworld!"),  # Arle: 今のうちに、ぷよぷよ地獄に持ち込むしかない!
    ],
    84: [  # PARAR_N.AIF
        (296, 416, (95, 117), 'Are you the last one on this floor?'),  # Arle: 君がこの階の最後の人?
        (433, 508, (223, 114), 'Right.'),  # opponent: うん
        (506, 704, (95, 117), "You don't look very strong..."),  # Arle: あんまり強そうには見えないなぁ
        (687, 762, (223, 114), 'Right.'),  # opponent: うん
        (781, 961, (95, 117), "But maybe you're actually super strong!"),  # Arle: でも本当はとんでもなく強いとか!
        (944, 1019, (223, 114), 'Right.'),  # opponent: うん
        (1027, 1270, (95, 117), "Or that's a bluff, and you're weak after all?"),  # Arle: と思わせといて、実はやっぱり弱いとか
        (1254, 1398, (223, 114), 'Right, right, right, right, right.'),  # opponent: うんうんうんうんうん
    ],
    86: [  # PARAR_T.AIF
        (267, 377, (199, 115), 'Parara~'),  # opponent: ぱらら
        (359, 585, (95, 117), "You're always so cheerful."),  # Arle: いつも陽気だなあ、君は
        (567, 692, (199, 115), 'Want to be cheerful together?'),  # opponent: 一緒に陽気になる?
        (730, 805, (95, 117), 'How?'),  # Arle: どうやって?
        (840, 940, (199, 115), 'A battle, a battle!'),  # opponent: 勝負、勝負
        (942, 1166, (199, 115), "That'll cheer you right up!"),  # opponent: これで陽気になれるよ
        (1407, 1583, (95, 117), 'N-no way!'),  # Arle: う、うそでしょー
    ],
    88: [  # RULUE_N.AIF
        (281, 516, (95, 117), 'Huh, Rulue? What are you doing here?'),  # Arle: あれ、ルルーじゃない。どうしてこんなとこに?
        (542, 650, (223, 117), "That's my line."),  # opponent: それはこっちのセリフだわ。
        (668, 949, (223, 117), "To think someone besides me\nfound out the tower's secret!"),  # opponent: まさか私の他に、この塔の秘密に気づいたものがいるなんて。
        (949, 1140, (95, 117), "The tower's secret? What's that?"),  # Arle: 塔の秘密?何それ?
        (1187, 1398, (223, 117), 'Hmph. As good at playing dumb as ever.'),  # opponent: ふん、相変わらずとぼけるのがうまいわね。
        (1446, 1717, (223, 117), 'But how long can you keep that up\nagainst me?'),  # opponent: でもこの私を相手に、どこまでシラが切り通せるかしら?
    ],
    90: [  # RULUE_T.AIF
        (237, 458, (231, 114), 'I am one who has mastered the fist.'),  # opponent: 私は、拳を極めし者なの。
        (458, 542, (95, 114), 'Uh-huh, and?'),  # Arle: うんうん、それで?
        (560, 926, (231, 114), "If things were as they should be,\nI'd reign as the strongest fighting queen!"),  # opponent: 世が世なら、最強の格闘女王として、君臨しているはずなのよ。
        (935, 1015, (95, 114), 'Wh-wow!'),  # Arle: な、なんと、
        (1027, 1105, (95, 114), 'And then? And then?'),  # Arle: それからそれから?
        (1117, 1219, (231, 114), 'And yet...'),  # opponent: それなのに、
        (1237, 1462, (231, 114), 'why am I in the Puyo Underworld?!'),  # opponent: どうしてぷよぷよ地獄なの?
        (1744, 1889, (95, 114), "There's nothing anyone can do about that."),  # Arle: こればっかりはどうしようもないよ。
        (1925, 2000, (95, 114), "You'll just have to give up."),  # Arle: あきらめるしか。
        (2015, 2090, (231, 114), 'No way!'),  # opponent: やーだー!
    ],
    92: [  # SAMUR_N.AIF
        (258, 487, (223, 115), 'I am Samurai Mole, a warrior.'),  # opponent: 拙者はサムライモール、武士でござる
        (469, 659, (95, 117), 'Uh... I see.'),  # Arle: はあ、そうですか
        (670, 817, (223, 115), 'And what is your name?'),  # opponent: して、お主の名は?
        (829, 1016, (95, 117), "Me? I'm Arle."),  # Arle: 僕?僕はアルルだよ
        (998, 1183, (223, 115), 'Oh, so you are the one!'),  # opponent: おお、お主がそうでござったか
        (1204, 1402, (223, 115), 'I bear you no grudge, but duty calls.'),  # opponent: お主には恨みはござらぬが、これも浮世の義理
        (1404, 1634, (223, 115), 'Now, face me in a fair fight!'),  # opponent: いざ尋常に、勝負されよ
    ],
    94: [  # SAMUR_T.AIF
        (310, 499, (223, 117), 'Ugh... ugh...'),  # opponent: うぅ…うぅ…
        (481, 651, (95, 117), "Huh? What's wrong?"),  # Arle: あれ?どうしたの?
        (718, 965, (223, 117), 'I-I am starving...'),  # opponent: は、腹が減っているのでござる…
        (967, 1154, (223, 117), 'Sorry, but could you shout out loud for me?'),  # opponent: すまぬが、大声を出してはもらえぬか?
        (1167, 1253, (95, 117), 'Sure, I guess.'),  # Arle: 別にいいけど
        (1310, 1385, (95, 117), 'WAAAH!'),  # Arle: わあ!
        (1631, 1840, (223, 117), 'Mm, your voice is quite delicious.'),  # opponent: うむ、お主の声はなかなか美味でござるな
        (1946, 2179, (223, 117), "Now that I've had my meal,"),  # opponent: さあて、腹ごしらえもすんだでござるし
        (2186, 2299, (223, 117), 'let us battle at once!'),  # opponent: さっそく勝負と参ろうか!
    ],
    96: [  # SASOR_N.AIF
        (286, 432, (223, 114), 'Well, well, you made it this far.'),  # opponent: よー、ここまで来られましたな。
        (449, 674, (95, 117), "You're... Sasoriman, right?"),  # Arle: 君は確か、サソリマンだっけ?
        (692, 896, (223, 114), 'Oh, you remembered me? How nice!'),  # opponent: いやー、覚えておいてくれたんですか。うれしいな。
        (979, 1267, (223, 114), "Sorry to trouble you when you're tired,\nbut you'll have to fight me."),  # opponent: さて、お疲れのところ恐縮ですけど、わてと戦ってもらいます。
        (1290, 1457, (223, 114), 'Here I go!'),  # opponent: ほな、行きまっせー。
    ],
    98: [  # SASOR_T.AIF
        (281, 408, (95, 117), 'Oh, long time no see!'),  # Arle: あ、久しぶり!
        (408, 483, (223, 114), 'Well, hello there!'),  # opponent: こりゃどうも!
        (512, 691, (223, 114), 'Still raking it in, I see. Good for you!'),  # opponent: 相変わらず儲かってるようで結構ですな
        (673, 902, (95, 117), 'N-not really...'),  # Arle: そ、そうでもないんだけどな
        (884, 1081, (223, 114), 'I know full well how strong you are.'),  # opponent: あんさんがお強いのはほんまよう分かってます
        (1083, 1233, (223, 114), "I'm no match for you."),  # opponent: もうあんたにはかないまへんわ
        (1235, 1413, (223, 114), 'Please, go on ahead.'),  # opponent: ささ、お先にお進みください
        (1395, 1517, (95, 117), 'Huh? Really?'),  # Arle: え?いいの?
        (1586, 1840, (95, 117), "But it feels like something's missing..."),  # Arle: でも、なんだか物足りないなぁ
        (1869, 2135, (95, 117), 'I really have to battle!'),  # Arle: やっぱり、勝負しなくっちゃ
        (2117, 2304, (223, 114), "Aw, you're killing me over here!"),  # opponent: ええ、そんな殺生な
    ],
    100: [  # SATAN_N.AIF
        (264, 398, (95, 117), 'Eek! Satan!'),  # Arle: ゲゲ?サタン!
        (405, 671, (223, 119), 'I knew if I waited at the top of the tower,\nyou would come!'),  # opponent: 塔の最上階にいれば、必ずお前が来ると思っていたぞ!
        (700, 780, (95, 117), 'Wh-why?'),  # Arle: な、なんで?
        (801, 1026, (223, 119), 'Because smoke and... you know who\nalways rise to high places.'),  # opponent: なんとかと煙は、高いところに登るものだからな
        (1008, 1196, (95, 117), "Hey! What's that supposed to mean?!"),  # Arle: ちょっと!それどういう意味よ!
        (1202, 1362, (95, 117), 'Enough talk! Bring it on!'),  # Arle: ごたくはいいから、かかってきなさい!
        (1381, 1788, (223, 119), "Very well. If I win,\nit's a honeymoon under the stars for us!"),  # opponent: よかろう。私が勝利したならば、二人で、星空のハネムーンだ!
        (1840, 2044, (95, 117), 'I have a really bad feeling about this!'),  # Arle: すっごく嫌な予感!
        (2050, 2160, (223, 119), 'Here I come!'),  # opponent: さあ、行くぞ!
    ],
    102: [  # SATAN_T.AIF
        (240, 524, (223, 117), 'Impressive. So you finally reached the top floor.'),  # opponent: さすがだな。ついにこの最上階までやってきたか。
        (586, 780, (223, 117), 'Now I want to make you mine even more!'),  # opponent: ますます、お前を我がものにしたくなったぞ。
        (778, 974, (95, 117), 'C-could it be... Satan?'),  # Arle: ま、まさか、サタンなの?
        (1003, 1331, (223, 117), "No, you're wrong. I am... Santa!"),  # opponent: いや、違うな。私はサンタだ!
        (1578, 1762, (95, 117), 'Wh-what a lame joke.'),  # Arle: な、なんてしょうもない。
        (1791, 2152, (223, 117), 'And I even had this costume made\nfor my best gag...'),  # opponent: 特注の衣装まで使った、とっておきのギャグだったのだが。
        (2173, 2312, (95, 117), 'Yeah, yeah, I get it.'),  # Arle: はいはい、分かったって。
        (2314, 2615, (95, 117), "Take that thing off\nand let's get this battle going."),  # Arle: そんなのは脱いじゃって、早いとこ勝負しようじゃない。
        (2672, 3056, (223, 117), "Tch... The gag fell flat,\nbut my state-of-the-art Puyo Underworld won't!"),  # opponent: くっ、ギャグは不発に終わったが、この最新鋭のぷよぷよ地獄はそうはいかんぞ。
        (3081, 3156, (223, 117), 'Take this!'),  # opponent: くらえ!
    ],
    104: [  # SHEZO_N.AIF
        (359, 464, (231, 116), "Heh heh... I've been waiting for you."),  # opponent: フフ…待っていたぞ
        (479, 584, (95, 117), 'Y-you again?!'),  # Arle: ま、また来た…
        (567, 895, (231, 116), 'Coming all this way for me,\nthe great Shezo Wegey...'),  # opponent: このシェゾ・ウィグィ様のために、ここまでやってくるとは、
        (943, 1077, (231, 116), 'How adorable.'),  # opponent: かわいい奴よ。
        (1089, 1222, (95, 117), "Aren't you getting the wrong idea?"),  # Arle: 何か勘違いしてるんじゃない?
        (1241, 1431, (231, 116), 'Come now, no need to be shy.'),  # opponent: やれやれ、照れることはないぞ。
        (1463, 1761, (231, 116), "After all, it's just you and me here."),  # opponent: 今ここには、俺様と、お前しかいないのだからな。
        (1797, 1872, (231, 116), 'How adorable.'),  # opponent: かわいい奴よ。
        (1853, 2137, (95, 117), 'You pervert mage!\nWhat weird stuff are you thinking?!'),  # Arle: この、変態魔導師が、何、変なこと考えてんのよ。
        (2196, 2385, (231, 116), "Y-you don't know how terrifying I truly am."),  # opponent: お、お前は俺様の真の恐ろしさを知らぬようだな。
        (2413, 2572, (231, 116), "Very well. You'll learn the hard way:"),  # opponent: よかろう、思い知るがいい。
        (2590, 2773, (231, 116), "the Dark Mage's amazing Puyo skills!"),  # opponent: 闇の魔導師の、驚異のぷよさばきをな。
    ],
    106: [  # SHEZO_T.AIF
        (341, 675, (95, 117), "Eek! You're that pervert mage!"),  # Arle: ゲゲッ!君はいつかの変態魔導師!
        (701, 841, (223, 216), "Wh-who's the pervert here!?"),  # opponent: だ、だーれが変態だ!?
        (841, 1044, (95, 117), 'You are, you really are.'),  # Arle: キミ、キミ、キミだよ!
        (1093, 1332, (223, 216), 'I am a Dark Mage of proud lineage!'),  # opponent: 俺様は由緒正しい闇の魔導師だ。
        (1335, 1498, (223, 216), "Now that it's come to this,\nI'll drag you down too..."),  # opponent: こうなればお前も、ぷよぷよ地獄の暗黒面に、
        (1500, 1620, (223, 216), '...to the dark side of the Puyo Underworld!'),  # opponent: ひきずりこんでやる!
    ],
    108: [  # SKELT_N.AIF
        (334, 536, (95, 117), 'Quit lounging there and get out of my way!'),  # Arle: そんなところでくつろいでないで道をあけてよ
        (518, 798, (223, 119), 'Now, now, calm down.\nHave some of this drugged tea.'),  # opponent: まあまあ落ち着き、この一服盛った茶でも飲んでな
        (780, 1004, (95, 117), "Who'd drink tea that dangerous?"),  # Arle: 誰がそんな危ないお茶を飲むって言うのよ
        (986, 1287, (223, 119), "How did you know\nthere's paralysis powder in the tea?!"),  # opponent: どうしてわかったんだ、お茶の中にしびれ薬が入ってるってよ
        (1269, 1420, (95, 117), 'You just said so yourself!'),  # Arle: さっき自分で言ったくせに
        (1402, 1784, (223, 119), "Whoops, my mistake.\nThen I'll attack the usual way!"),  # opponent: ありゃ、俺としたことが。ならばいつものように攻めるまでよ
    ],
    110: [  # SKELT_T.AIF
        (314, 641, (223, 119), 'Spring, summer, fall, winter...\ngreen tea is the best!'),  # opponent: 春夏秋冬、やはり緑茶が一番よなあ!
        (623, 886, (95, 117), 'Really? I like black tea better!'),  # Arle: そうかなぁ、僕は紅茶のほうが好きだよ!
        (883, 1075, (223, 119), 'Fool! Drink green tea! Green tea!'),  # opponent: バカモノ!緑茶を飲めぇ!緑茶を!
        (1096, 1258, (95, 117), 'Everyone has their own taste!'),  # Arle: 人にはそれぞれ好みがあるの!
        (1389, 1760, (223, 119), "Bah! You just don't get it!\nThen through the Puyo Underworld..."),  # opponent: えぇい!分からんやつだな!ならばぷよぷよ地獄を通じて!
        (1817, 1995, (223, 119), "...I'll teach you the wonders of green tea!"),  # opponent: 緑茶の素晴らしさを教えてやろう!
    ],
    112: [  # SKIYA_N.AIF
        (295, 431, (223, 115), 'Wait right there!'),  # opponent: ちょっと待てー!
        (427, 543, (95, 117), 'Where? Where are you?'),  # Arle: どこ?どこにいるの?
        (567, 704, (223, 115), 'Behold! My ultimate technique!'),  # opponent: 見よ!究極奥義!
        (740, 949, (223, 115), 'Special Wonder Flying 30-Mon Kiiick!'),  # opponent: スペシャルワンダーフライング30文キーック!
    ],
    114: [  # SKIYA_T.AIF
        (336, 553, (223, 117), 'Hyuuu... hyuuu...'),  # opponent: ひゅー、ひゅー
        (578, 695, (95, 117), "Wh-what's this?"),  # Arle: な、なにかな
        (719, 891, (95, 117), "A monster I've never seen before."),  # Arle: 見たことないモンスターだな
        (873, 1033, (223, 117), "Mmm, you're noisy."),  # opponent: うーん、うるさいな
        (1035, 1160, (223, 117), "You're disturbing my nap."),  # opponent: 昼寝の邪魔だ
        (1261, 1336, (95, 117), 'A nap?'),  # Arle: 昼寝?
        (1366, 1519, (95, 117), 'But why standing on your head?'),  # Arle: でもどうして逆立ちしながら
        (1501, 1681, (223, 117), 'How I sleep is my own business!'),  # opponent: どんな格好で寝ようと僕の勝手だろ
        (1683, 1967, (223, 117), "I'll beat you so badly\nyou'll never disturb my nap again!"),  # opponent: 二度と昼寝の邪魔ができないよう、コテンパンにしてやる!
    ],
    116: [  # SKYUR_N.AIF
        (320, 548, (95, 117), "Oh, a girl's taking a hot spring bath."),  # Arle: あ、女の子が温泉に入ってる。
        (554, 728, (95, 117), 'I want to get in too~'),  # Arle: ぼくも入りたいなー。
        (764, 871, (223, 117), 'You can come in~'),  # opponent: 入ってもいいわよー。
        (859, 1016, (95, 117), 'Really? Yay!'),  # Arle: ほんとー?わーい!
        (1129, 1360, (95, 117), 'Ahh, this feels great.'),  # Arle: はぁ、いい気分。
        (1342, 1646, (223, 117), "You know, I'm your second opponent, Scylla."),  # opponent: あのね、私が二番手のスキュラなんだよ。
        (1649, 1774, (95, 117), 'Nice to meet you~'),  # Arle: よろしくー。
        (1772, 1934, (223, 117), "Let's soak for a while, then battle."),  # opponent: ゆっくり入ってから、勝負しようね。
        (1946, 2021, (95, 117), 'Okay.'),  # Arle: うん。
        (2546, 2621, (223, 117), 'Still in?'),  # opponent: まだー?
        (2674, 2895, (95, 117), "I... I can't take any more..."),  # Arle: もう、ダメだー。
        (2902, 3051, (223, 117), 'I was waiting for this moment!'),  # opponent: この時を待ってたのよ。
        (3081, 3201, (223, 117), 'Now the battle is mine.'),  # opponent: これで勝負は私のもの。
        (3231, 3389, (223, 117), "...But I'm dizzy from the heat too."),  # opponent: でも、私ものぼせたの。
    ],
    118: [  # SKYUR_T.AIF
        (269, 344, (223, 116), 'Woof!'),  # opponent: ワン!
        (344, 433, (95, 117), 'Oh! So cute!'),  # Arle: あ!かわいい!
        (474, 564, (223, 116), 'Sniff, sniff...'),  # opponent: クンクン
        (546, 735, (95, 117), 'There, there. Good doggy, good doggy.'),  # Arle: よしよし、いい子いい子
        (783, 892, (223, 116), "I'll take this~!"),  # opponent: もらっていくよー
        (874, 1061, (95, 117), 'Waah, my Puyo bun!'),  # Arle: うわー、僕のぷよまん!
        (1047, 1234, (223, 116), 'Munch, munch, munch... gulp!'),  # opponent: パクパクパク、ゴックン
        (1216, 1308, (95, 117), 'Unforgivable!'),  # Arle: 許せない!
        (1336, 1435, (95, 117), "If you're that hungry,"),  # Arle: そんなにお腹が減ってるなら
        (1437, 1634, (95, 117), 'then eat this Puyo Puyo too!'),  # Arle: このぷよぷよも食べさせてあげるよ!
    ],
    120: [  # SUKE_N.AIF
        (263, 416, (223, 113), 'Fiiish!'),  # opponent: フィーッシュ!
        (501, 761, (95, 117), 'Not pretty, no matter when I see him...'),  # Arle: いつ見ても美しくないな
        (743, 1123, (223, 113), "What?! What about these legs\nisn't beautiful?!"),  # opponent: なんだと?この足のどこが美しくないと?
        (1142, 1502, (95, 117), 'Oh, no, not the legs... I mean,\nin your case...'),  # Arle: あ、いや、足っていうより、その、つまり君の場合は
        (1484, 1760, (223, 113), 'Anyone who knocks my gorgeous legs...'),  # opponent: この自慢の脚線美にケチをつける奴は
        (1762, 1916, (223, 113), '...gets tripped up by Puyo Puyo!'),  # opponent: ぷよぷよで足をすくってやる
    ],
    122: [  # SUKE_T.AIF
        (398, 572, (223, 114), 'Fiiish!'),  # opponent: フィーッシュ
        (554, 877, (95, 117), 'Ooh, your dancing is even wilder\nand more passionate than before!'),  # Arle: おー、以前にも増して踊りが激しく、情熱的に!
        (876, 989, (223, 114), 'Heh heh heh!'),  # opponent: ふっふっふーんだ!
        (996, 1162, (223, 114), 'Ever since I lost to you last time,'),  # opponent: 前回お前に負けてからな!
        (1164, 1577, (223, 114), "I've trained at dancing\nuntil I sweated blood!"),  # opponent: 俺は血の滲むようなダンスの特訓をしたのだ!
        (1668, 1813, (95, 117), 'So, did you get better at Puyo Puyo?'),  # Arle: で、ぷよぷよは上手くなったの?
        (1831, 1906, (223, 114), 'Huh?'),  # opponent: 何が?
        (1956, 2177, (95, 117), 'I said, did you get better at Puyo Puyo?'),  # Arle: だから、ぷよぷよは上手くなったの?
        (2246, 2321, (223, 114), 'Huh?'),  # opponent: 何が?
    ],
    124: [  # TRIO_N.AIF
        (405, 689, (95, 117), 'Hey, no fair! Is three against one allowed?'),  # Arle: あ、ずるい。3対1なんてありなの?
        (843, 1111, (95, 117), "O-okay, okay. It's allowed."),  # Arle: わ、わかりました。ありでいいです。
    ],
    126: [  # TRIO_T.AIF
        (340, 407, (95, 117), 'Huh?'),  # Arle: ええ?
        (409, 576, (95, 117), 'What are you three talking about?'),  # Arle: 三人そろって、何の話してるの?
        (566, 742, (223, 113), 'Psst, psst, psst...'),  # opponent: ポソポソポソ…
        (724, 928, (95, 117), "Hey, don't ignore me!"),  # Arle: ちょっと、無視しないでよ!
        (997, 1168, (223, 113), 'Psst, psst, psst...'),  # opponent: ポソポソポソ…
        (1209, 1373, (95, 117), 'Say something, will you?!'),  # Arle: なんとか言ったらどうなの!?
        (1912, 2070, (223, 113), 'Kiii! Kiii!'),  # opponent: きぃー!きぃー!
        (2087, 2162, (95, 117), 'Grrr!'),  # Arle: ムッキー!
        (2164, 2297, (95, 117), 'Are you making fun of me?!'),  # Arle: 馬鹿にしてんの!?
        (2299, 2425, (95, 117), "That's it, let's battle!"),  # Arle: こうなったら勝負よ!
    ],
    128: [  # UROKO_N.AIF
        (257, 444, (192, 56), "You... you came to bully me, didn't you?"),  # opponent: あなた、私をいじめに来たのね。
        (450, 525, (95, 117), 'Huh?'),  # Arle: え?
        (500, 651, (192, 56), 'Yes, that must be it!'),  # opponent: そうよ、そうに決まってるわ。
        (662, 843, (192, 56), "How cruel! I haven't done anything!"),  # opponent: ひどいわ、私何もしてないのに。
        (835, 1037, (95, 117), 'Ugh, what a pain...'),  # Arle: うわぁ、まいった。
        (1039, 1292, (95, 117), "I didn't know she was this type..."),  # Arle: この子って、この手のタイプだったとは。
    ],
    130: [  # UROKO_T.AIF
        (331, 540, (223, 127), "You... you came to bully me, didn't you?"),  # opponent: あなた、私をいじめに来たのね。
        (554, 629, (95, 117), 'Huh?'),  # Arle: え?
        (593, 741, (223, 127), 'Yes, that must be it!'),  # opponent: そうよ、そうに決まってるわ。
        (728, 815, (95, 117), 'Now, now, calm down.'),  # Arle: まあまあ、落ち着いて。
        (798, 948, (223, 127), "Stay back! Come closer and I'll cry!"),  # opponent: 来ないで、来たら泣くわよ。
        (974, 1086, (95, 117), 'Then what am I supposed to do?'),  # Arle: じゃあどうしろっての?
        (1099, 1228, (223, 127), 'Battle me in the Puyo Underworld.'),  # opponent: ぷよぷよ地獄で勝負して。
        (1252, 1358, (95, 117), 'Wh-why?!'),  # Arle: な、何故?
    ],
    132: [  # WILLO_N.AIF
        (273, 461, (95, 117), 'You look awfully relaxed.'),  # Arle: ずいぶん気持ちよさそうね
        (443, 524, (231, 93), 'Booo...'),  # opponent: ぼー
        (710, 832, (95, 117), 'But what a funny face.'),  # Arle: でもおかしな顔
        (834, 1009, (95, 117), "Like you're not thinking about anything."),  # Arle: なんにも考えてないって感じ
        (991, 1075, (231, 93), 'Booo...'),  # opponent: ぼー
    ],
    134: [  # WILLO_T.AIF
        (276, 356, (223, 46), 'Booo!'),  # opponent: ぼー!
        (338, 584, (63, 117), 'Whoa! So bright!'),  # Arle: わっ!まぶしい!
        (638, 713, (223, 46), 'Boboo!'),  # opponent: ぼぼー!
        (684, 823, (63, 117), "I won't lose at being bright!"),  # Arle: まぶしいのだったら負けないぞ!
        (835, 926, (63, 117), 'Hah! Light!'),  # Arle: えい!ライト!
        (1276, 1486, (63, 117), 'Phew, I win that round!'),  # Arle: ふぅ、今のは僕の勝ちだね!
        (1493, 1668, (63, 117), 'But the real battle starts now!'),  # Arle: でも、本当の勝負はこれからだよ!
    ],
    136: [  # WITCH_N.AIF
        (271, 635, (231, 114), 'Ohohoho! First, I commend you\nfor making it this far.'),  # opponent: おーっほっほ、まずはここにたどり着けたこと、褒めて差し上げますわ
        (617, 941, (95, 117), 'Ugh, why does everyone keep getting in my way?'),  # Arle: うーん、なんでみんな僕の邪魔ばっかりするの
        (958, 1163, (231, 114), 'How brazen, still saying such things!'),  # opponent: まあしらじらしい、まだそんなことをおっしゃるなんて、
        (1165, 1413, (231, 114), 'Reflect on yourself a little\nin the Nuisance Puyo Underworld!'),  # opponent: おじゃまぷよ地獄で少しは反省なさい
    ],
    138: [  # WITCH_T.AIF
        (262, 492, (200, 114), "Isn't the view from here lovely?"),  # opponent: ここからの眺めって、素敵だと思いません?
        (520, 602, (95, 117), 'Let me see...'),  # Arle: どれどれ?
        (641, 716, (200, 114), 'Hah!'),  # opponent: えい!
        (785, 1065, (95, 117), 'That was dangerous!\nI almost fell!'),  # Arle: 危ないじゃないか!もう少しで落ちるとこだったよ!
        (1105, 1577, (200, 114), "Good reflexes.\nI suppose you're worthy of fighting me."),  # opponent: なかなかの反射神経ですわ。この私と戦う資格が、ある…ってことかしら。
        (1559, 1778, (95, 117), "Saying whatever you like... now I'm mad!"),  # Arle: 勝手なこと言っちゃって、頭に来たぞ!
    ],
    140: [  # ZOMBI_N.AIF
        (277, 465, (223, 113), 'My... my clothes...'),  # opponent: あ、ふ、服がー。
        (453, 528, (95, 117), 'Wh-what is it?'),  # Arle: な、なんなの?
        (544, 644, (223, 113), "They're in tatters..."),  # opponent: ぼろぼろだー。
        (710, 947, (95, 117), "In your case, it's not just your clothes\nthat are in tatters."),  # Arle: 君の場合、ぼろぼろなのは服だけじゃないでしょ?
        (993, 1296, (223, 113), "So if I win, I'm taking your clothes!"),  # opponent: てなわけで、俺が勝ったらその服をもらうぞー。
    ],
    142: [  # ZOMBI_T.AIF
        (189, 344, (223, 118), "I can't find it..."),  # opponent: 見つからなーい。
        (338, 498, (95, 114), 'What are you looking for?'),  # Arle: 何探してんの?
        (541, 764, (223, 118), 'I dropped my guts somewhere...'),  # opponent: 腹綿をどこかに落としてしまったー。
        (786, 922, (95, 114), 'Who drops those?'),  # Arle: 落とすかな、普通。
        (992, 1221, (223, 118), "Ohh, what's under your feet is..."),  # opponent: おー、お前の足の下にあるのは、
        (1233, 1396, (95, 114), 'Ew, this is definitely...'),  # Arle: うわ、これはまさしく、
        (1401, 1710, (223, 118), "Stepping on my guts?\nI'll never forgive you!"),  # opponent: 俺の腹綿を踏むなんて、絶対に許さーん。
    ],
    144: [  # ZOU_N.AIF
        (280, 736, (223, 116), "Climbing all the way up here?\nYou're really something, zoh!"),  # opponent: ここまで登ってくるとは、大した奴だぞー!
        (736, 811, (95, 117), 'Whoa, whoa, hey!'),  # Arle: わ、わ、ちょっと!
        (838, 1113, (223, 116), "How's that? My earthquake stomp!"),  # opponent: どうだ!俺様の震脚は!
        (1137, 1405, (95, 117), "P-pretty impressive.\nBut come on, let's battle already!"),  # Arle: な、なかなかだと思うよ。でもいいよ、早く勝負を!
    ],
    146: [  # ZOU_T.AIF
        (707, 1228, (223, 116), 'Coming to wreck my place of peace again?\nUnforgivable, zoh!'),  # opponent: また、俺様の安らぎの場を荒らしに来るなんて、許さないぞー!
        (1289, 1634, (95, 117), "What's that supposed to mean?\nYou make it sound like I'm the bad guy!"),  # Arle: それ、どういう意味?まるで、僕が悪者みたいな言い方じゃないか!
        (1616, 2039, (223, 116), 'Not "like"... you ARE, zoh!'),  # opponent: みたいじゃなくて、そうなんだぞー!
        (2039, 2182, (95, 117), 'Ah, how mean!'),  # Arle: ああ、ひどいな
        (2164, 2592, (223, 116), "You can't talk your way out of it, zoh!"),  # opponent: 言い逃れは、できないんだぞー!
        (2931, 3210, (95, 117), "Then let's settle who's right\nin the Puyo Underworld!"),  # Arle: じゃあ、ぷよぷよ地獄で白黒をはっきりさせようじゃないの!
    ],
    148: [  # ED_EASY.AIF
        (22, 174, (160, 218), 'I... I won...!'),  # Arle: か、勝った!
        (355, 570, (160, 218), 'I did it! I did it! I did iiit!'),  # Arle: やった!やった!やったー!
        (596, 666, (160, 218), "I've become a..."),  # Arle: これで僕が…
        (668, 833, (160, 218), '...Puyo Puyo Master!'),  # Arle: ぷよぷよマスターね!
        (987, 1146, (160, 190), "Heh heh... Don't make me laugh!"),  # opponent: フフフ…笑わせてくれるわ
        (1217, 1475, (160, 190), "I'll show you who\nthe real Puyo Master is!"),  # opponent: 本物のぷよマスターが誰なのか、私が教えてやろう
        (1538, 1673, (160, 190), 'Heh heh heh heh...'),  # opponent: フフフフ…
        (1714, 2062, (160, 190), 'Ha ha ha ha! Ha ha ha ha!'),  # opponent: ハッハッハッハ。ハッハッハッハ
        (2074, 2324, (160, 218), 'Ngh... Darn it!'),  # Arle: う、ううう!!くそ~!
    ],
    150: [  # ED_NORM.AIF
        (19, 242, (160, 218), "All right! I'm the winner!"),  # Arle: やったー!僕の勝ちだ!
        (259, 366, (160, 190), 'D-darn it!'),  # opponent: く、くっそー!
        (424, 499, (160, 218), 'Huh?'),  # Arle: あら?
        (623, 755, (160, 218), 'W-wait a minute!'),  # Arle: ちょ、ちょっと待ってよ
        (757, 908, (160, 218), 'The ground is moving!'),  # Arle: 地面が動いてるよ
        (890, 1061, (160, 190), 'I-I have no idea!'),  # opponent: わ、わたしは知らんぞ!
        (1043, 1164, (160, 218), "What's going on?"),  # Arle: どうなってるの?
    ],
    152: [  # ED_MASK.AIF
        (179, 368, (160, 218), 'Whaaat? No way!'),  # Arle: えぇー、うっそー!
        (370, 748, (160, 218), "I can't believe Masked Satan was\nthe handsome, long-legged Satan!"),  # Arle: マスク・ド・サタンが、あの美形で足の長いサタンと同じ人だったなんて!
        (902, 1025, (160, 190), "...Or so I'd like to hear."),  # opponent: なんてな…
        (1082, 1375, (160, 218), 'I knew it was Satan all this time...'),  # Arle: なーんだ、やっぱりサタンじゃん
        (1377, 1521, (160, 218), "Carby, let's go home."),  # Arle: カーくん、お家帰ろっか
        (1503, 1743, (160, 190), 'Wait! How did you know I was Satan?'),  # opponent: 待ってくれ、どうして私がサタンだと分かった?
        (1760, 1904, (160, 218), 'I already told you that before the battle.'),  # Arle: 僕は戦う前から言ってたじゃないか
        (1952, 2027, (160, 190), 'N-no!'),  # opponent: そ、そんな!
        (2000, 2180, (160, 218), "I'm starting to get tired now. Bye-bye!"),  # Arle: 僕、もう疲れたよ、バイバイ!
        (2186, 2302, (160, 190), "Don't just leave me behind!"),  # opponent: 置いてかないでー
        (2473, 2647, (160, 190), "Carby, you won't leave me, right?"),  # opponent: カーくん、行かないよな
        (3018, 3327, (160, 190), 'Carby!'),  # opponent: カーくーん
    ],
    154: [  # ED_TUU.AIF
        (491, 565, (160, 218), "All right! I'm number one!"),  # Arle: やっほー!ぼくがいっちばーん!
        (567, 716, (160, 218), 'Our long battle is finally over!'),  # Arle: やっと長かった戦いが終わるわ!
        (1048, 1353, (160, 218), 'Nobody can beat me now!'),  # Arle: もう誰も僕に勝てる人はいない!
        (1485, 1618, (160, 218), "But still, it's so cool..."),  # Arle: でも、すごいなぁ
        (1620, 1882, (160, 218), "There's so much in this world I don't know."),  # Arle: この世界には僕の知らないことがいっぱいある
        (1884, 2122, (160, 218), 'I bet there are lots more\nstrange people out there.'),  # Arle: きっとまだ変わった人たちがいっぱいいるに違いないよ
        (2403, 2519, (160, 218), 'Ah! Carby!'),  # Arle: あー!カーくん!
        (2627, 2702, (160, 190), 'Guu!'),  # opponent: ぐー!
        (2748, 2846, (160, 218), 'Carby, are you hungry?'),  # Arle: カーくん、お腹減ったの?
        (2888, 2963, (160, 218), 'Me too.'),  # Arle: そうだね
        (2985, 3178, (160, 218), "Let's go home and eat something."),  # Arle: お家に帰って何か食べよう
        (3160, 3256, (160, 190), 'Guguguu!'),  # opponent: ぐぐぐー!
        (3331, 3508, (160, 218), "Carby, you'll make me curry? Yay!"),  # Arle: カーくんがカレー作ってくれるの?やった!
        (3516, 3608, (160, 190), 'Guu!'),  # opponent: ぐー!
    ],
}
