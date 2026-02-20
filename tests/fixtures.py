PLAYER_POOL = [
    'Akira', 'Alphen', 'AngryBird', 'Armperor', 'Big Bird', 
    'Blaz', 'Bonchan', 'Booce_Lee', 'Broski', 'Caba', 
    'Chris Wong', 'Craime', 'Daigo', 'DCQ', 'Dogura', 
    'Dual Kevin', 'EndingWalker', 'FREESER', 'Fuudo', 'Gachikun', 
    'GO1', 'Higuchi', 'Hikaru', 'HotDog29', 'Hurricane', 
    'iDom', 'Itabashi Zangief', 'JAK', 'John Takeuchi', 'Juicyjoe', 
    'Kakeru', 'Kawano', 'Kilzyou', 'Kingsvega', 'Kobayan', ''
    'Kusanagi', 'Leshar', 'Lexx', 'Mago', 'MenaRD', 
    'Micky', 'Mister Crimson', 'Moke', 'Momochi', 'Nephew', 
    'NL', 'NoahTheProdigy', 'NotPedro', 'NuckleDu', 'Nyanpi', 
    'NYChrisG', 'Oil King', 'Phenom', 'Problem X', 'Psycho', 
    'Pugera', 'Punk', 'Riddles', 'Ryukichi', 'Ryusei', 
    'Sahara', 'Shine', 'Shuto', 'Tachikawa', 'Takamura', 
    'Tokido', 'Torimeshi', 'Valmaster', 'vWsym', 'Vxbao', 
    'Xian', 'Xiaohai', 'Yamaguchi', 'Zangief_bolado', 'Zhen'
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

ALICES_TEAM = [
    {"email": "user1@gmail.com", "password": "G!7rP2vH#9qZ", "manager_name": "Alice"},
    {"email": "user4@gmail.com", "password": "T%3bV9nE@7rY", "manager_name": "Dana"},
    {"email": "user5@gmail.com", "password": "F!6kH8zM$4jL", "manager_name": "Evan"},
    {"email": "user2@gmail.com", "password": "H$8mK4sT*1xW", "manager_name": "Bobert"},
    {"email": "user3@gmail.com", "password": "J&5yL6wR^2pQ", "manager_name": "Charlie"},
]

FALSE_USERS = [
    {"email": "user1gmail.com", "password": "G!7rP2vH#9qZ", "manager_name": "Alice"},  # invalid email
    {"email": "user2@gmail.com", "password": "short", "manager_name": "Bobert"},        # password too short
    {"email": "user3@gmail.com", "password": "J&5yL6wR^2pQ", "manager_name": "C"},     # manager name too short
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
    {"email": "user18@gmail.com", "password": "9P$Z!H@2M7F8", "manager_name": "R"},     # name too short
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
    "Test_League_1", "Test_League_2", "Test_League_3", "Test_League_4", "Test_League_5"
]