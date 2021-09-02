extern crate prost_build;

use std::path::Path;

fn main() {
    let protobuf_dir = option_env!("PROTOBUF_SRC")
        .or(Some("../domain/protobuf/"))
        .map(|dir| Path::new(dir))
        .unwrap();
    prost_build::compile_protos(&[protobuf_dir.join("messages.proto")],
                                &[protobuf_dir]).unwrap();
}
