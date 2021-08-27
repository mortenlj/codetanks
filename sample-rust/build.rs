extern crate prost_build;

fn main() {
    prost_build::compile_protos(&["target/proto/messages.proto"],
                                &["target/"]).unwrap();
}
