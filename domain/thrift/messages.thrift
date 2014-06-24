namespace py ibidem.codetanks.domain

enum ClientType {
    VIEWER,
    BOT
}

enum BotStatus {
    ALIVE,
    DYING,
    DEAD,
    INACTIVE
}

struct Id {
    1: required string name;
    2: required i16 version;
}

struct Registration {
    1: required ClientType client_type;
    2: required Id id;
}

struct Arena {
    1: required i16 width;
    2: required i16 height;
}

struct GameInfo {
    1: required Arena arena;
}

struct RegistrationReply {
    1: required GameInfo game_info;
    2: required string event_url;
    3: optional string cmd_url;
}

struct Point {
    1: required double x;
    2: required double y;
}

struct Bullet {
    1: required i32 id;
    2: required Point position;
    3: required Point direction;
    4: required double speed;
}

struct Tank {
    1: required i32 id;
    2: required Id bot_id;
    3: required Point position;
    4: required Point direction;
    5: required Point aim;
    6: required double speed;
    7: required byte health;
    8: required BotStatus status;
}

struct GameData {
    1: required list<Bullet> bullets;
    2: required list<Tank> tanks;
}