"""The English text of Puyo Puyo 2 (arcade), by address of the original Japanese text.

Kinds of page (tools/text.py builds the control codes):
  name  the first page of a character profile: the name in 『』, a short pause, then up
        to two lines (32 characters each)
  page  a further page of a profile: up to three lines (32 characters)
  tut   a page of the attract mode's tutorial (…のひみつ): up to seven lines of 18
        characters
'PAUSE' before a line keeps the original's dramatic pause there; 'IFTURN' marks where a
tutorial page ends when the TURN DIRECTION DIP switch is set (the original's ff1c).
The English names follow the Super Puyo Puyo 2 translation by J2e Translations.
"""

TEXT = [
    # --- character profiles (shown before each match) ---
    (0x1bf9e, 'name', ["Will-o'-Wisp", "A lively little fireball.", "One of the Eight Clan."]),
    (0x1bffe, 'page', ["It doesn't seem to think", "about things very much."]),
    (0x1c040, 'name', ["Momomo", "Both a member of the Eight Clan", "and a merchant. A hard worker."]),
    (0x1c096, 'name', ["Nohoho", "True to his name, he takes", "life nice and easy."]),
    (0x1c0e2, 'page', ["One of the Six Poets."]),
    (0x1c10a, 'name', ["Nomi", "Just a flea.", "A mere flea in the Eight Clan!"]),
    (0x1c162, 'name', ["Skeleton-T", "A guy who loves his tea.", "One of the Eight Clan."]),
    (0x1c1b8, 'page', ["He still hasn't figured out", "how to rotate his puyo."]),
    (0x1c1fe, 'name', ["Mini Zombie", "A little zombie.", "One of the Eight Clan."]),
    (0x1c252, 'page', ["Small as it is,", "it's rotten all the same,", "so it stinks just as much."]),
    (0x1c2a0, 'name', ["Nasu Grave", "As you can see, an eggplant."]),
    (0x1c2e4, 'page', ["Kids who hate eggplant", "will be eaten by this guy...", 'PAUSE', "...maybe."]),
    (0x1c34a, 'name', ["Sukiyapodes", "He's very touchy about people", "saying he has big feet."]),
    (0x1c3bc, 'name', ["Samurai Mole", "A SAMURAAI who lives by", "the code of BUSHIDOO."]),
    (0x1c408, 'page', ["The edge of his sword is", "second to none."]),
    (0x1c43c, 'name', ["Mummy", "A clumsy bandaged man.", "One of the Six Poets."]),
    (0x1c48e, 'page', ["He might be handsome", "under all those bandages."]),
    (0x1c4b8, 'name', ["Owlbear", "Half bear, half owl.", "Scary voice, scary face."]),
    (0x1c512, 'page', ["For some reason he's always", "the villain. Poor thing."]),
    (0x1c558, 'name', ["Barometz", "Something like a sheep.", "One of the Eight Clan."]),
    (0x1c5b4, 'name', ["Banshee Trio", "Three singing sisters", "who are a real nuisance."]),
    (0x1c600, 'page', ["Thanks to them, the Eight Clan", "became famous."]),
    (0x1c646, 'name', ["Fufufu", "A creepy goldfish-like", "merchant."]),
    (0x1c684, 'page', ["How he carries his safe", "around is a secret."]),
    (0x1c6be, 'name', ["Cait Sith Twins", "Apart from being twins,", "they're just cats."]),
    (0x1c726, 'name', ["Zombie", "A rotten man."]),
    (0x1c75c, 'page', ["He stinks so much that", "nobody seems to like him."]),
    (0x1c7a0, 'name', ["Panotty", "A little prankster imp", "who loves his flute."]),
    (0x1c7e4, 'page', ["But he's harmless."]),
    (0x1c80c, 'name', ["Sasoriman", "A mystery scorpion who talks", "Kansai style. Very friendly."]),
    (0x1c86e, 'page', ["One of the Five Musicians."]),
    (0x1c898, 'name', ["Suketoudara", "Crazy about dancing.", "A fish dancer proud of his legs."]),
    (0x1c900, 'name', ["Uroko Sakanabito", "Put simply, a mermaid.", "Rather shy."]),
    (0x1c964, 'name', ["Harpy", "Bewitches people with a voice", "that isn't exactly good."]),
    (0x1c9ca, 'name', ["Parara", "A merchant of few words.", "So he's bad at business."]),
    (0x1ca18, 'page', ["Also one of the Five Musicians."]),
    (0x1ca4a, 'name', ["Dragon", "Of everyone in the tower,", "he's by far the biggest."]),
    (0x1ca9a, 'page', ["How did he even get in?"]),
    (0x1cace, 'name', ["Witch", "A girl who uses magic."]),
    (0x1cb0c, 'page', ["Her personality is", "a little twisted."]),
    (0x1cb4a, 'name', ["Pakista", "One of the Four Kings."]),
    (0x1cb82, 'page', ["Does his business in a", "rather dubious French."]),
    (0x1cbc0, 'name', ["Draco Centaur", "A cute girl with horns,", "fangs and wings."]),
    (0x1cc20, 'page', ["Every now and then she gets", "mistaken for a boy."]),
    (0x1cc60, 'name', ["Rulue", "Her cold stare and voice make", "all who hear them tremble."]),
    (0x1ccbe, 'page', ["Her haughty laughter", "echoes across the field."]),
    (0x1cd06, 'name', ["Minotauros", "A master of the axe."]),
    (0x1cd42, 'page', ["Has the dangerous habit of", "swinging it around at times."]),
    (0x1cd8a, 'name', ["Zoh Daimaoh", "A big elephant with an", "exotic, ethnic flair."]),
    (0x1cdde, 'page', ["Slams puyo into the ground.", "His power play is still strong."]),
    (0x1ce32, 'name', ["Mamono", "One of the Four Kings."]),
    (0x1ce68, 'page', ["Its eerie growl just can't", "come from this world."]),
    (0x1ceb4, 'name', ["Shezo Wegey", "A sorcerer with a crystal sword.", "His name is hard to say."]),
    (0x1cf1c, 'page', ["Powered up, he's after Arle", "once again."]),
    (0x1cf64, 'page', ["But his name is still", "hard to say."]),
    (0x1cf94, 'name', ["Satan", "Has horns, fangs and wings,", "just like Draco."]),
    (0x1cfec, 'page', ["But it seems even he", "doesn't have a tail.", "The last foe of this tower."]),
    (0x1d046, 'name', ["Masked Satan", "Who he really is remains", "a mystery."]),

    # --- attract mode tutorial pages ---
    (0x1d0ae, 'tut', ["Move the falling", "puyo left and", "right with the", "stick.", "Push down to make", "them fall faster."]),
    (0x1d116, 'tut', ["Press a button", "to rotate.", 'IFTURN', "Right button:", "rotate right.", "Left button:", "rotate left."]),
    (0x1d176, 'tut', ["When 4 or more", "puyo touch up,", "down, left or", "right, they pop!"]),
    (0x1d1c0, 'tut', ["Pile puyo up to", "the top of the", "3rd column from", "the left and", "it's game over!"]),
    (0x1d206, 'tut', ["Pop puyo to drop", "nuisance puyo on", "your opponent.", "Make long chains", "to send lots and", "lots of nuisance", "puyo!"]),
    (0x1d28e, 'tut', ["Nuisance puyo", "vanish together", "with the normal", "puyo popping next", "to them."]),
    (0x1d2e0, 'tut', ["Hard puyo won't", "vanish in just", "one pop."]),
    (0x1d314, 'tut', ["But do it like", "this, and they all", "vanish at once!"]),
    (0x1d35a, 'tut', ["Point puyo vanish", "the usual way,", "but they also", "score you points!"]),
    (0x1d3a4, 'tut', ["You can cancel", "the nuisance puyo", "your opponent", "sends you with", "the nuisance puyo", "you send back!"]),
    (0x1d414, 'tut', ["Pop puyo while", "this is shown to", "send a whole lot", "of nuisance puyo!"]),
    (0x1d476, 'tut', ["Even in a spot", "like this, press", "the button twice", "to flip the pair."]),
    (0x1d4c8, 'tut', ["While this sign", "is shown, a new", "player can join", "the game from the", "empty side!"]),
    (0x1d532, 'tut', ["To play against", "a linked cabinet,", "choose YES when", "asked JOIN IN?"]),
    (0x1d5a4, 'tut', ["If you'd rather", "not be joined,", "press START to", "take the JOIN IN!", "sign away."]),
]
