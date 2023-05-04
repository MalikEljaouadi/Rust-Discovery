// This file was generated by `mfy_api_generator`
// ⚠️  HANDLE WITH CARE

use serde::{Deserialize, Serialize};

/// The [`AnimalType`]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum AnimalType {
    /// The `cat`
    #[serde(rename = "cat")]
    Cat,
    /// The `dog`
    #[serde(rename = "dog")]
    Dog,
    /// The `possum`
    #[serde(rename = "possum")]
    Possum,
}
