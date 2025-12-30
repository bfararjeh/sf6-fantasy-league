PLAYER_POOL = [
    "Shine", "Xian", "JAK", "Bryan-D", "kingsvega",
    "NYChrisG", "Kilzyou", "KojiKOG", "Hope", "Kusanagi",
    "Fuudo", "Zhen", "SURINI", "Samurai", "Shuto",
    "Akira", "Chris Wong", "Hurricane", "Tachikawa", "MenaRD",
    "xiaohai", "MysticSmash", "pugera", "NL", "Beslem",

    "Latif", "broski", "Agxxs", "Micky", "Psycho",
    "EndingWalker", "Big Bird", "Mister Crimson", "NARIKUN", "Nyanpi",
    "FREESER", "Axela", "Armperor", "Ryukichi", "LUGABO",
    "Torimeshi", "tako", "Jojotaro", "Juicyjoe", "Oil King",
    "Kawano", "KEI.B", "joxero", "Cosa", "Kobayan",

    "Yanai", "Nephew", "AngryBird", "NotPedro", "PrinceGR",
    "Takamura", "NoahTheProdigy", "Booce_Lee", "Harumi", "Kyuki",
    "Roy", "Dogura", "GO1", "NuckleDu", "Tantanmen",
    "DCQ", "Zangief_bolado", "harms", "moke", "Vxbao",
    "Punk", "ACQUA", "KR_Wrestlingman", "Jr.", "Ryusei",

    "Higuchi", "Itabashi Zangief", "Sahara", "gachikun", "JuniorLeo",
    "Travis Styles", "Caba", "Mago", "iDom", "Nauman",
    "Phenom", "Kakeru", "Daigo", "Kintyo", "Machabo",
    "HotDog29", "IWILLKEEELYOU", "Yamaguchi", "Momochi", "Riddles",
    "Yujiro", "Bonchan", "vWsym", "Eguto", "John Takeuchi"
]

TEST_USERS = [
    {"email": "user1@gmail.com", "password": "G!7rP2vH#9qZ", "manager_name": "Alice"},
    {"email": "user2@gmail.com", "password": "H$8mK4sT*1xW", "manager_name": "Bobert"},
    {"email": "user3@gmail.com", "password": "J&5yL6wR^2pQ", "manager_name": "Charlie"},
    {"email": "user4@gmail.com", "password": "T%3bV9nE@7rY", "manager_name": "Dana"},
    {"email": "user5@gmail.com", "password": "F!6kH8zM$4jL", "manager_name": "Evan"},

    {"email": "user6@gmail.com", "password": "Q9!A#7xM4Kp$", "manager_name": "Frank"},
    {"email": "user7@gmail.com", "password": "R@8m6J!FZ5H2", "manager_name": "Grace"},
    {"email": "user8@gmail.com", "password": "P#2E9$K!7rVb", "manager_name": "Hannah"},
    {"email": "user9@gmail.com", "password": "M@5WZ8!3kP$J", "manager_name": "Ianeth"},
    {"email": "user10@gmail.com", "password": "7$F!L2xK@M9P", "manager_name": "Julia"},

    {"email": "user11@gmail.com", "password": "Z@4!K7$H5FJ2", "manager_name": "Kevin"},
    {"email": "user12@gmail.com", "password": "8!xM2P$QZ@H5", "manager_name": "Laura"},
    {"email": "user13@gmail.com", "password": "T@7$K2M!ZP8F", "manager_name": "Mike"},
    {"email": "user14@gmail.com", "password": "6H@Z$P!9F7M2", "manager_name": "Nina"},
    {"email": "user15@gmail.com", "password": "P$!8Z2@7MHF9", "manager_name": "Oscar"},

    {"email": "user16@gmail.com", "password": "4M!Z@K7$H9P2", "manager_name": "Paula"},
    {"email": "user17@gmail.com", "password": "Z!7H@P$2M8F9", "manager_name": "Quinn"},
    {"email": "user18@gmail.com", "password": "9P$Z!H@2M7F8", "manager_name": "Rachel"},
    {"email": "user19@gmail.com", "password": "M2$P@7Z!9HF8", "manager_name": "Samuel"},
    {"email": "user20@gmail.com", "password": "H@9!ZP$M27F8", "manager_name": "Tina"},
]

FALSE_USERS = [
    {"email": "user1gmail.com", "password": "G!7rP2vH#9qZ", "manager_name": "Alice"},  # invalid email
    {"email": "user2@gmail.com", "password": "short", "manager_name": "Bobert"},        # password too short
    {"email": "user3@gmail.com", "password": "J&5yL6wR^2pQ", "manager_name": "Ch"},     # manager name too short
    {"email": "user4@gmail.com", "password": "T%3bV9nE@7rY", "manager_name": "Dana_123456789012345"},  # name too long
    {"email": "user5@gmail.com", "password": "F!6kH8zM$4jL", "manager_name": "Evan!"},  # invalid char

    {"email": "user6gmail.com", "password": "Q9!A#7xM4Kp$", "manager_name": "Frank"},   # invalid email
    {"email": "user7@gmail.com", "password": "123", "manager_name": "Grace"},           # password too short
    {"email": "user8@gmail.com", "password": "P#2E9$K!7rVb", "manager_name": "H@nnah"}, # invalid char
    {"email": "user9gmail", "password": "M@5WZ8!3kP$J", "manager_name": "Ianeth"},     # invalid email
    {"email": "user10@gmail.com", "password": "7$F!L2xK@M9P", "manager_name": "J"},      # name too short

    {"email": "user11@gmail.com", "password": "Z@4!K7$H5FJ2", "manager_name": "Kevin!!"},# invalid char
    {"email": "user12@gmail.com", "password": "8!xM2", "manager_name": "Laura"},         # password too short
    {"email": "user13@gmail.com", "password": "T@7$K2M!ZP8F", "manager_name": "Mike_1234567890123"},  # name too long
    {"email": "user14@gmail.com", "password": "6H@Z$P!9F7M2", "manager_name": "Ni#na"}, # invalid char
    {"email": "user15gmail.com", "password": "P$!8Z2@7MHF9", "manager_name": "Oscar"},   # invalid email

    {"email": "user16@gmail.com", "password": "4M!Z@K7", "manager_name": "Paula"},       # password too short
    {"email": "user17@gmail.com", "password": "Z!7H@P$2M8F9", "manager_name": "Qu!nn"}, # invalid char
    {"email": "user18@gmail.com", "password": "9P$Z!H@2M7F8", "manager_name": "Ra"},     # name too short
    {"email": "user19@gmail.com", "password": "M2$P@7Z!9HF8", "manager_name": "Samuel_1234567890123"}, # name too long
    {"email": "user20@gmailcom", "password": "H@9!ZP$M27F8", "manager_name": "Tina!"}   # invalid email & char
]

TEAM_NAMES = [
    "CrimsonFists", "IronWolves", "Nova_Raiders", "PixelSquad", "BlitzCrew",
    "ShadowStrike", "MegaMasters", "UltraForceX", "PrimeHunters", "SilverClaws",
    "CyberKnights", "StormUnit_7", "BattleTigers", "WarpDriveX", "GalaxyRivals",
    "ThunderRaid", "NightEclipse", "FrostGuard", "ChaosChamps", "OmegaElite",
    "MysticRogue1", "SteelLegionX", "RoyalFalcons", "QuantumCrew", "ApexSquad"
]

DUMMY_LEAGUE_NAMES = [
    "Test League 1", "Test League 2", "Test League 3", "Test League 4", "Test League 5"
]