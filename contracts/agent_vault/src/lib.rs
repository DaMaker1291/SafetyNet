#![no_std]
#![no_main]

extern crate alloc;

use alloc::string::String;
use casper_contract::{
    contract_api::{runtime, storage},
    unwrap_or_revert::UnwrapOrRevert,
};
use casper_types::{
    ApiError, Key, URef, U256,
};

const ARG_METHOD: &str = "method";
const ARG_AGENT: &str = "agent_name";
const ARG_AGENT_DATA: &str = "agent_data";

const KEY_INIT: &str = "sv_init";
const KEY_AGENTS_DICT: &str = "sv_agents";
const KEY_COUNT: &str = "sv_count";


fn get_dict_seed(name: &str) -> URef {
    let key = runtime::get_key(name)
        .unwrap_or_revert_with(ApiError::MissingKey);
    match key {
        Key::URef(uref) => uref,
        _ => runtime::revert(ApiError::UnexpectedKeyVariant),
    }
}

#[no_mangle]
pub extern "C" fn call() {
    let method: String = runtime::get_named_arg(ARG_METHOD);

    match method.as_str() {

        "init" => {
            if runtime::get_key(KEY_INIT).is_some() {
                runtime::revert(ApiError::User(0));
            }

            let dict = storage::new_dictionary(KEY_AGENTS_DICT)
                .unwrap_or_revert();
            runtime::put_key(KEY_AGENTS_DICT, dict.into());

            let count = storage::new_uref(U256::zero());
            runtime::put_key(KEY_COUNT, count.into());

            let init = storage::new_uref(String::from("ok"));
            runtime::put_key(KEY_INIT, init.into());
        }

        "register_agent" => {
            let _init_check = runtime::get_key(KEY_INIT)
                .unwrap_or_revert_with(ApiError::MissingKey);

            let name: String = runtime::get_named_arg(ARG_AGENT);
            let data: String = runtime::get_named_arg(ARG_AGENT_DATA);

            let dict_seed = get_dict_seed(KEY_AGENTS_DICT);
            storage::dictionary_put(dict_seed, &name, data);

            let count_key = runtime::get_key(KEY_COUNT)
                .unwrap_or_revert_with(ApiError::MissingKey);
            let count_uref = match count_key {
                Key::URef(uref) => uref,
                _ => runtime::revert(ApiError::UnexpectedKeyVariant),
            };
            storage::add(count_uref, U256::one());
        }

        _ => runtime::revert(ApiError::InvalidArgument),
    }
}
