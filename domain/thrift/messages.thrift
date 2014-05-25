namespace py ibidem.codetanks.domain

enum ClientType {
    VIEWER,
    BOT
}

struct Registration {
    1: required ClientType client_type;
    2: required string id;
}

struct RegistrationReply {
    1: required string update_url;
}

struct Arena {
    1: required i16 width;
    2: required i16 height;
}

struct GameInfo {
    1: required Arena arena;
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
    2: required string bot_id;
    3: required Point position;
    4: required Point direction;
    5: required Point aim;
    6: required double speed;
    7: required double health;
}

struct GameData {
    1: required list<Bullet> bullets;
    2: required list<Tank> tanks;
}