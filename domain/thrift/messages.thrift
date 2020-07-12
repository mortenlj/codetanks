namespace py ibidem.codetanks.domain
namespace java ibidem.codetanks.domain

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
    2: required byte max_health;
    3: required byte bullet_damage;
    4: required byte player_count;
    5: required double tank_speed;
    6: required double rotation;
    7: required double bullet_speed;
    8: required double tank_radius;
    9: required double bullet_radius;
}

struct RegistrationReply {
    1: required RegistrationResult result;
    2: required GameInfo game_info;
    3: optional string event_url;
    4: optional string cmd_url;
    5: optional i32 id;
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
    6: required byte health;
    7: required BotStatus status;
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

union Event {
    1: ScanResult scan;
    2: Death death;
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
    2: optional ScanResult scan;
}

enum CommandType {
    MOVE,
    ROTATE,
    AIM,
    FIRE,
    SCAN
}

struct Command {
    1: required CommandType type;
    2: optional i16 value;
}
