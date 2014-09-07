namespace py ibidem.codetanks.domain

const byte MAX_HEALTH = 100;
const byte BULLET_DAMAGE = 5;
const byte PLAYER_COUNT = 4;
const double TANK_SPEED = 0.1;
const double ROTATION = 0.005;
const double BULLET_SPEED = 0.2;
const double TANK_RADIUS = 16.0;
const double BULLET_RADIUS = 2.0

enum ClientType {
    VIEWER,
    BOT
}

enum BotStatus {
    IDLE,
    MOVING,
    ROTATING,
    AIMING,
    FIRING,
    SCANNING,
    DEAD
}

enum RegistrationResult {
    SUCCESS,
    FAILURE
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
    1: required RegistrationResult result;
    2: required GameInfo game_info;
    3: optional string event_url;
    4: optional string cmd_url;
}

struct Point {
    1: required double x;
    2: required double y;
}

struct Bullet {
    1: required i32 id;
    2: required Point position;
    3: required Point direction;
}

struct Tank {
    1: required i32 id;
    2: required Id bot_id;
    3: required Point position;
    4: required Point direction;
    5: required Point turret;
    6: required byte health = MAX_HEALTH;
    7: required BotStatus status = BotStatus.IDLE;
}

struct GameData {
    1: required list<Bullet> bullets = [];
    2: required list<Tank> tanks = [];
}

// ******
// Events
// ******

struct ScanResult {
    1: required list<Tank> tanks = [];
}

struct Death {
    1: required Tank victim;
    2: required Tank perpetrator;
}

// ********
// Commands
// ********

enum CommandResult {
    BUSY,
    OK
}

struct CommandReply {
    1: required CommandResult result;
}

struct Move {
    1: required i16 distance;
}

struct Rotate {
    1: required i16 angle;
}

struct Aim {
    1: required i16 angle;
}

struct Fire {
}

struct Scan {
    1: required i16 angle;
}
