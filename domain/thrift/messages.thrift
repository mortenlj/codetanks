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
