#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    notty_lib::run();
}
