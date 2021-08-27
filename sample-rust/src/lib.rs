
// Include the `domain` module, which is generated from items.proto.
pub mod domain {
    include!(concat!(env!("OUT_DIR"), "/ibidem.codetanks.domain.rs"));
}
