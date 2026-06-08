#![no_std]
#![no_main]

extern crate alloc;

use alloc::{
    string::{String, ToString},
    vec::Vec,
};
use casper_contract::{
    contract_api::{runtime, storage, system},
    unwrap_or_revert::UnwrapOrRevert,
};
use casper_types::{
    contracts::NamedKeys,
    runtime_args,
    ApiError, CLType, CLTyped, CLValue, EntryPoint, EntryPointAccess, EntryPointType,
    EntryPoints, Group, Key, Parameter, URef, U256,
};

const KEY_AGENT_COUNT: &str = "agent_count";
const KEY_STRATEGY_COUNT: &str = "strategy_count";
const KEY_ACTION_COUNT: &str = "action_count";
const KEY_AGENTS_DICT: &str = "agents";
const KEY_STRATEGIES_DICT: &str = "strategies";
const KEY_ACTIONS_DICT: &str = "actions";
const KEY_OWNER: &str = "owner";
const KEY_AGENT_SEED: &str = "agent_seed_uref";

const ENTRY_POINT_INIT: &str = "init";
const ENTRY_POINT_REGISTER_AGENT: &str = "register_agent";
const ENTRY_POINT_SUBMIT_STRATEGY: &str = "submit_strategy";
const ENTRY_POINT_RECORD_ACTION: &str = "record_action";
const ENTRY_POINT_GET_AGENT: &str = "get_agent";
const ENTRY_POINT_GET_STRATEGY: &str = "get_strategy";
const ENTRY_POINT_GET_ACTION: &str = "get_action";
const ENTRY_POINT_GET_COUNTS: &str = "get_counts";

const ARG_NAME: &str = "name";
const ARG_AGENT_ID: &str = "agent_id";
const ARG_STRATEGY_ID: &str = "strategy_id";
const ARG_ACTION_ID: &str = "action_id";
const ARG_DESCRIPTION: &str = "description";
const ARG_METADATA: &str = "metadata";
const ARG_STRATEGY_TYPE: &str = "strategy_type";
const ARG_PARAMS: &str = "params_json";
const ARG_ACTION_TYPE: &str = "action_type";
const ARG_DATA: &str = "data_json";
const ARG_AGENT_IDS: &str = "agent_ids";
const ARG_TX_HASH: &str = "tx_hash";

#[derive(Debug, Clone, CLTyped)]
pub struct AgentInfo {
    pub id: U256,
    pub name: String,
    pub description: String,
    pub registered_at: U256,
    pub strategy_count: U256,
    pub action_count: U256,
    pub is_active: bool,
}

#[derive(Debug, Clone, CLTyped)]
pub struct StrategyInfo {
    pub id: U256,
    pub agent_id: U256,
    pub strategy_type: String,
    pub params_json: String,
    pub created_at: U256,
    pub executed: bool,
    pub tx_hash: String,
}

#[derive(Debug, Clone, CLTyped)]
pub struct ActionInfo {
    pub id: U256,
    pub agent_id: U256,
    pub action_type: String,
    pub data_json: String,
    pub performed_at: U256,
    pub tx_hash: String,
}

#[repr(u16)]
enum Error {
    UnknownError = 0,
    AlreadyInitialized = 1,
    NotInitialized = 2,
    OnlyOwner = 3,
    AgentNotFound = 4,
    StrategyNotFound = 5,
    ActionNotFound = 6,
    InvalidArgument = 7,
}

impl From<Error> for ApiError {
    fn from(e: Error) -> Self {
        ApiError::User(e as u16)
    }
}

fn get_dict_uref(name: &str) -> URef {
    let key = runtime::get_key(name)
        .unwrap_or_revert_with(Error::NotInitialized);
    key.into_uref()
        .unwrap_or_revert_with(Error::NotInitialized)
}

fn store_dict_entry<T: CLTyped + alloc::fmt::Debug>(
    dict_name: &str,
    key_str: &str,
    value: T,
) {
    let dict_uref = get_dict_uref(dict_name);
    storage::dictionary_put(dict_uref, key_str, value);
}

fn read_dict_entry<T: CLTyped + alloc::fmt::Debug>(
    dict_name: &str,
    key_str: &str,
) -> Option<T> {
    let dict_uref = get_dict_uref(dict_name);
    storage::dictionary_get(dict_uref, key_str)
        .unwrap_or_revert_with(Error::UnknownError)
}

fn get_owner() -> Key {
    runtime::get_key(KEY_OWNER)
        .unwrap_or_revert_with(Error::NotInitialized)
}

fn assert_owner() {
    let caller = runtime::get_caller();
    let owner = get_owner();
    if Key::Account(caller) != owner {
        runtime::revert(Error::OnlyOwner);
    }
}

fn current_timestamp() -> U256 {
    let blocktime = runtime::get_blocktime();
    U256::from(blocktime.into())
}

#[no_mangle]
pub extern "C" fn init() {
    let caller = runtime::get_caller();
    let owner_key = Key::Account(caller);

    if runtime::has_key(KEY_OWNER) {
        runtime::revert(Error::AlreadyInitialized);
    }

    runtime::put_key(KEY_OWNER, owner_key);

    let agent_seed = storage::new_uref(U256::from(0));
    runtime::put_key(KEY_AGENT_SEED, Key::URef(agent_seed));

    let agents_dict = storage::new_dictionary(KEY_AGENTS_DICT)
        .unwrap_or_revert_with(Error::UnknownError);
    runtime::put_key(KEY_AGENTS_DICT, Key::URef(agents_dict));

    let strategies_dict = storage::new_dictionary(KEY_STRATEGIES_DICT)
        .unwrap_or_revert_with(Error::UnknownError);
    runtime::put_key(KEY_STRATEGIES_DICT, Key::URef(strategies_dict));

    let actions_dict = storage::new_dictionary(KEY_ACTIONS_DICT)
        .unwrap_or_revert_with(Error::UnknownError);
    runtime::put_key(KEY_ACTIONS_DICT, Key::URef(actions_dict));

    runtime::put_key(KEY_AGENT_COUNT, storage::new_uref(U256::from(0)));
    runtime::put_key(KEY_STRATEGY_COUNT, storage::new_uref(U256::from(0)));
    runtime::put_key(KEY_ACTION_COUNT, storage::new_uref(U256::from(0)));
}

#[no_mangle]
pub extern "C" fn register_agent() {
    assert_owner();

    let name: String = runtime::get_named_arg(ARG_NAME);
    let description: String = runtime::get_named_arg(ARG_DESCRIPTION);

    let count_uref = runtime::get_key(KEY_AGENT_COUNT)
        .unwrap_or_revert_with(Error::NotInitialized)
        .into_uref()
        .unwrap_or_revert_with(Error::NotInitialized);
    let mut count: U256 = storage::read(count_uref)
        .unwrap_or_revert_with(Error::UnknownError)
        .unwrap_or_default();
    count += U256::from(1);
    storage::write(count_uref, count);

    let agent_id = count;
    let agent_key = agent_id.to_string();

    let agent = AgentInfo {
        id: agent_id,
        name,
        description,
        registered_at: current_timestamp(),
        strategy_count: U256::from(0),
        action_count: U256::from(0),
        is_active: true,
    };

    store_dict_entry(KEY_AGENTS_DICT, &agent_key, agent);

    runtime::ret(CLValue::from_t(agent_id).unwrap_or_revert());
}

#[no_mangle]
pub extern "C" fn submit_strategy() {
    assert_owner();

    let agent_id: U256 = runtime::get_named_arg(ARG_AGENT_ID);
    let strategy_type: String = runtime::get_named_arg(ARG_STRATEGY_TYPE);
    let params_json: String = runtime::get_named_arg(ARG_PARAMS);

    let agent_key = agent_id.to_string();
    let mut agent: AgentInfo = read_dict_entry(KEY_AGENTS_DICT, &agent_key)
        .unwrap_or_revert_with(Error::AgentNotFound);

    let count_uref = runtime::get_key(KEY_STRATEGY_COUNT)
        .unwrap_or_revert_with(Error::NotInitialized)
        .into_uref()
        .unwrap_or_revert_with(Error::NotInitialized);
    let mut count: U256 = storage::read(count_uref)
        .unwrap_or_revert_with(Error::UnknownError)
        .unwrap_or_default();
    count += U256::from(1);
    storage::write(count_uref, count);

    let strategy_id = count;
    let strategy_key = strategy_id.to_string();

    let strategy = StrategyInfo {
        id: strategy_id,
        agent_id,
        strategy_type,
        params_json,
        created_at: current_timestamp(),
        executed: false,
        tx_hash: String::new(),
    };

    store_dict_entry(KEY_STRATEGIES_DICT, &strategy_key, strategy);

    agent.strategy_count += U256::from(1);
    store_dict_entry(KEY_AGENTS_DICT, &agent_key, agent);

    runtime::ret(CLValue::from_t(strategy_id).unwrap_or_revert());
}

#[no_mangle]
pub extern "C" fn record_action() {
    assert_owner();

    let agent_id: U256 = runtime::get_named_arg(ARG_AGENT_ID);
    let action_type: String = runtime::get_named_arg(ARG_ACTION_TYPE);
    let data_json: String = runtime::get_named_arg(ARG_DATA);
    let tx_hash: String = runtime::get_named_arg(ARG_TX_HASH);

    let agent_key = agent_id.to_string();
    let mut agent: AgentInfo = read_dict_entry(KEY_AGENTS_DICT, &agent_key)
        .unwrap_or_revert_with(Error::AgentNotFound);

    let count_uref = runtime::get_key(KEY_ACTION_COUNT)
        .unwrap_or_revert_with(Error::NotInitialized)
        .into_uref()
        .unwrap_or_revert_with(Error::NotInitialized);
    let mut count: U256 = storage::read(count_uref)
        .unwrap_or_revert_with(Error::UnknownError)
        .unwrap_or_default();
    count += U256::from(1);
    storage::write(count_uref, count);

    let action_id = count;
    let action_key = action_id.to_string();

    let action = ActionInfo {
        id: action_id,
        agent_id,
        action_type,
        data_json,
        performed_at: current_timestamp(),
        tx_hash,
    };

    store_dict_entry(KEY_ACTIONS_DICT, &action_key, action);

    agent.action_count += U256::from(1);
    store_dict_entry(KEY_AGENTS_DICT, &agent_key, agent);

    runtime::ret(CLValue::from_t(action_id).unwrap_or_revert());
}

#[no_mangle]
pub extern "C" fn get_agent() {
    let agent_id: U256 = runtime::get_named_arg(ARG_AGENT_ID);
    let agent_key = agent_id.to_string();
    let agent: Option<AgentInfo> = read_dict_entry(KEY_AGENTS_DICT, &agent_key);
    match agent {
        Some(a) => runtime::ret(CLValue::from_t(a).unwrap_or_revert()),
        None => runtime::revert(Error::AgentNotFound),
    }
}

#[no_mangle]
pub extern "C" fn get_strategy() {
    let strategy_id: U256 = runtime::get_named_arg(ARG_STRATEGY_ID);
    let strategy_key = strategy_id.to_string();
    let strategy: Option<StrategyInfo> = read_dict_entry(KEY_STRATEGIES_DICT, &strategy_key);
    match strategy {
        Some(s) => runtime::ret(CLValue::from_t(s).unwrap_or_revert()),
        None => runtime::revert(Error::StrategyNotFound),
    }
}

#[no_mangle]
pub extern "C" fn get_action() {
    let action_id: U256 = runtime::get_named_arg(ARG_ACTION_ID);
    let action_key = action_id.to_string();
    let action: Option<ActionInfo> = read_dict_entry(KEY_ACTIONS_DICT, &action_key);
    match action {
        Some(a) => runtime::ret(CLValue::from_t(a).unwrap_or_revert()),
        None => runtime::revert(Error::ActionNotFound),
    }
}

#[no_mangle]
pub extern "C" fn get_counts() {
    let agent_count: U256 = {
        let uref = runtime::get_key(KEY_AGENT_COUNT)
            .unwrap_or_revert_with(Error::NotInitialized)
            .into_uref()
            .unwrap_or_revert_with(Error::NotInitialized);
        storage::read(uref)
            .unwrap_or_revert_with(Error::UnknownError)
            .unwrap_or_default()
    };

    let strategy_count: U256 = {
        let uref = runtime::get_key(KEY_STRATEGY_COUNT)
            .unwrap_or_revert_with(Error::NotInitialized)
            .into_uref()
            .unwrap_or_revert_with(Error::NotInitialized);
        storage::read(uref)
            .unwrap_or_revert_with(Error::UnknownError)
            .unwrap_or_default()
    };

    let action_count: U256 = {
        let uref = runtime::get_key(KEY_ACTION_COUNT)
            .unwrap_or_revert_with(Error::NotInitialized)
            .into_uref()
            .unwrap_or_revert_with(Error::NotInitialized);
        storage::read(uref)
            .unwrap_or_revert_with(Error::UnknownError)
            .unwrap_or_default()
    };

    let counts = (agent_count, strategy_count, action_count);
    runtime::ret(CLValue::from_t(counts).unwrap_or_revert());
}

#[no_mangle]
pub extern "C" fn call() {
    let entry_points = {
        let mut eps = EntryPoints::new();

        let init_entry = EntryPoint::new(
            ENTRY_POINT_INIT,
            Vec::new(),
            CLValue::from_t(()).unwrap_or_revert().cl_type(),
            EntryPointAccess::Public,
            EntryPointType::Session,
        );
        eps.add_entry_point(init_entry);

        let register_agent_entry = EntryPoint::new(
            ENTRY_POINT_REGISTER_AGENT,
            vec![
                Parameter::new(ARG_NAME, CLType::String),
                Parameter::new(ARG_DESCRIPTION, CLType::String),
            ],
            CLType::U256,
            EntryPointAccess::Public,
            EntryPointType::Session,
        );
        eps.add_entry_point(register_agent_entry);

        let submit_strategy_entry = EntryPoint::new(
            ENTRY_POINT_SUBMIT_STRATEGY,
            vec![
                Parameter::new(ARG_AGENT_ID, CLType::U256),
                Parameter::new(ARG_STRATEGY_TYPE, CLType::String),
                Parameter::new(ARG_PARAMS, CLType::String),
            ],
            CLType::U256,
            EntryPointAccess::Public,
            EntryPointType::Session,
        );
        eps.add_entry_point(submit_strategy_entry);

        let record_action_entry = EntryPoint::new(
            ENTRY_POINT_RECORD_ACTION,
            vec![
                Parameter::new(ARG_AGENT_ID, CLType::U256),
                Parameter::new(ARG_ACTION_TYPE, CLType::String),
                Parameter::new(ARG_DATA, CLType::String),
                Parameter::new(ARG_TX_HASH, CLType::String),
            ],
            CLType::U256,
            EntryPointAccess::Public,
            EntryPointType::Session,
        );
        eps.add_entry_point(record_action_entry);

        let get_agent_entry = EntryPoint::new(
            ENTRY_POINT_GET_AGENT,
            vec![Parameter::new(ARG_AGENT_ID, CLType::U256)],
            CLType::Any,
            EntryPointAccess::Public,
            EntryPointType::Session,
        );
        eps.add_entry_point(get_agent_entry);

        let get_strategy_entry = EntryPoint::new(
            ENTRY_POINT_GET_STRATEGY,
            vec![Parameter::new(ARG_STRATEGY_ID, CLType::U256)],
            CLType::Any,
            EntryPointAccess::Public,
            EntryPointType::Session,
        );
        eps.add_entry_point(get_strategy_entry);

        let get_action_entry = EntryPoint::new(
            ENTRY_POINT_GET_ACTION,
            vec![Parameter::new(ARG_ACTION_ID, CLType::U256)],
            CLType::Any,
            EntryPointAccess::Public,
            EntryPointType::Session,
        );
        eps.add_entry_point(get_action_entry);

        let get_counts_entry = EntryPoint::new(
            ENTRY_POINT_GET_COUNTS,
            Vec::new(),
            CLType::Tuple3(Box::new((CLType::U256, CLType::U256, CLType::U256))),
            EntryPointAccess::Public,
            EntryPointType::Session,
        );
        eps.add_entry_point(get_counts_entry);

        eps
    };

    let (contract_hash, _) = storage::new_locked_contract(
        entry_points,
        None,
        None,
        None,
    );

    let contract_package_hash = storage::create_contract_package_at_hash();
    let contract_version = storage::add_contract_version(
        contract_package_hash,
        entry_points,
        NamedKeys::new(),
    );

    runtime::put_key("agent_vault", contract_package_hash.into());
    runtime::put_key("agent_vault_contract", contract_hash.into());
}
